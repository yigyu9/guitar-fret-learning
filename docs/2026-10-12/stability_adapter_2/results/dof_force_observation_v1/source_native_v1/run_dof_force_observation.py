"""Add read-only DOF force collection to the unchanged PALM_RATE runner."""
import argparse
import json
from pathlib import Path
import sys

from .environment import InitialEnvironment, ROOT, gymapi, np
from .run_physx_contacts import native_state
from . import run_palm_position_followup as runner


class ForceEnvironment(InitialEnvironment):
    instance = None

    def __init__(self, settings):
        ForceEnvironment.instance = self
        self.force_records = []
        self.force_reads_preserve = True
        super().__init__(settings)

    def _create_scene(self):
        super()._create_scene()
        self.force_supported = bool(self.gym.enable_actor_dof_force_sensors(self.env, self.human))
        if not self.force_supported:
            raise RuntimeError('native DOF force collection is not supported')
        asset = self.gym.get_actor_asset(self.env, self.human)
        if list(self.gym.get_asset_dof_names(asset)) != self.names:
            raise ValueError('asset/actor DOF force layout differs')
        self.force_types = [int(self.gym.get_asset_dof_type(asset, i)) for i in range(len(self.names))]
        self.force_units = [('Nm' if t==int(gymapi.DOF_ROTATION) else
                             'N' if t==int(gymapi.DOF_TRANSLATION) else 'unverified') for t in self.force_types]

    def step_physics(self):
        super().step_physics()
        before, target = native_state(self), self.target.copy()
        props = self.gym.get_actor_dof_properties(self.env, self.human).copy()
        forces = self.gym.get_actor_dof_forces(self.env, self.human).copy()
        if forces.shape != (len(self.names),) or forces.dtype != np.float32 or not np.isfinite(forces).all():
            raise ValueError('finite float32 actor DOF force vector required')
        self.force_records.append({'physics_step':self.steps, 'time_s':self.steps/240,
                                   'native_total_DOF_force':forces.astype(float).tolist()})
        self.force_reads_preserve &= bool(before==native_state(self) and np.array_equal(target, self.target)
            and np.array_equal(props, self.gym.get_actor_dof_properties(self.env, self.human)))
        if not self.force_reads_preserve:
            raise RuntimeError('force read changed native states/targets/PD')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out/n).exists() for n in ('force_report.json', 'sensors.json', 'failure.json')):
        raise FileExistsError('preserve previous sensor observation')
    previous = ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/PALM_RATE'
    response = previous.parent.parent/'palm_target_response_v1/response.json'
    baseline = ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on'
    frame = baseline.parent.parent/'palm_frame_audit_v1/measurements_validated'
    settings = ROOT/'stability_adapter_2/trials/quiescent_3s_v1/reference.json'
    inputs = dict(runner.read(response)['input_sha256'])
    if not all(runner.sha(p)==h for p,h in inputs.items()):
        raise ValueError('previous response sources differ')
    raw_names = ('states','trace','controls','contacts','hands','queries','leg_torques')
    paths = [Path(__file__).resolve(), response,
        ROOT/'isaacgym/docs/programming/forcesensors.html', ROOT/'isaacgym/docs/api/python/gym_py.html',
        ROOT/'isaacgym/docs/api/python/enum_py.html']
    paths += [previous/(n+'.json') for n in raw_names]
    inputs.update({str(p.resolve()):runner.sha(p) for p in paths})
    original_environment, original_argv = runner.InitialEnvironment, sys.argv
    runner.InitialEnvironment = ForceEnvironment
    sys.argv = [str(Path(__file__)), '--mode', 'PALM_RATE', '--settings', str(settings),
        '--reference-run', str(baseline), '--frame-dir', str(frame), '--out', str(args.out/'native')]
    try:
        runner.main()
        env = ForceEnvironment.instance
        report = runner.read(args.out/'native/report.json')
        prefix = {n:runner.read(args.out/'native'/(n+'.json'))==runner.read(previous/(n+'.json')) for n in raw_names}
        paths = [args.out/'native'/(n+'.json') for n in ('report',)+raw_names]
        inputs.update({str(p.resolve()):runner.sha(p) for p in paths})
        checks = {'original_thirteen_native_contracts':len(report['checks'])==13 and all(report['checks'].values()),
            'all_seven_previous_arrays_exact':all(prefix.values()), 'force_sensor_enable_supported':env.force_supported,
            '120_aligned_force_samples':len(env.force_records)==120 and
                [r['physics_step'] for r in env.force_records]==list(range(1,121)),
            'force_reads_preserve_states_targets_PD':env.force_reads_preserve,
            'observer_and_reference_sources_current':all(runner.sha(p)==h for p,h in inputs.items())}
        result = {'checks':checks, 'seven_array_equality_observations':prefix,
            'input_sha256':dict(inputs, **report['input_sha256']), 'human_joint_names':env.names,
            'native_DOF_type_codes':env.force_types, 'native_DOF_units':env.force_units,
            't0_force_measurement':None, 'samples':len(env.force_records),
            'nonzero_sample_count':sum(any(abs(v)>0 for v in s['native_total_DOF_force']) for s in env.force_records),
            'scope':'total DOF sensor forces at completed steps; not actuator-only torque, contact force, effort saturation, PD cause or guitar stability success',
            'max_guitar_position_error_mm':report['max_position_error_m']*1000,
            'max_guitar_rotation_error_deg':report['max_rotation_error_deg'],
            'max_left_palm_displacement_mm':report['max_left_palm_displacement_m']*1000}
        (args.out/'force_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if not all(checks.values()):
            raise AssertionError(checks)
        print(json.dumps({'checks':checks, 'nonzero_samples_observed':result['nonzero_sample_count']}, indent=2))
    except Exception as error:
        env = ForceEnvironment.instance
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__, 'error':str(error),
            'completed_physics_steps':getattr(env,'steps',0), 'supported_observation':getattr(env,'force_supported',None)},indent=2)+'\n')
        raise
    finally:
        runner.InitialEnvironment, sys.argv = original_environment, original_argv
        env = ForceEnvironment.instance
        if env is not None:
            (args.out/'sensors.json').write_text(json.dumps(env.force_records,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    main()
