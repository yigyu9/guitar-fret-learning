"""Compare approved Shoulder stiffness only, using unchanged PALM_RATE runners."""
import argparse
import json
from pathlib import Path
import sys

from .environment import ROOT, np
from .run_physx_contacts import native_state
from .run_dof_force_observation import ForceEnvironment
from . import run_palm_position_compare as short_runner
from . import run_palm_position_followup as hold_runner

RAW = ('states', 'trace', 'controls', 'contacts', 'hands', 'queries', 'leg_torques')


def properties(values):
    return {name: values[name].tolist() for name in values.dtype.names}


def native_targets(env):
    value = env.gym.get_actor_dof_position_targets(env.env, env.human).copy()
    if value.shape != (len(env.names),) or value.dtype != np.float32 or not np.isfinite(value).all():
        raise ValueError('finite float32 native target vector required')
    return value


class ShoulderEnvironment(ForceEnvironment):
    instance = None

    def __init__(self, settings, stiffness):
        ShoulderEnvironment.instance = self
        super().__init__(settings)
        try:
            indices = [self.names.index(side+'_Shoulder_'+axis)
                       for side in ('L', 'R') for axis in ('x', 'y', 'z')]
            baseline = short_runner.read(ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on/report.json')
            before = self.gym.get_actor_dof_properties(self.env, self.human).copy()
            for field, key in (('stiffness', 'native_pd_kp'), ('damping', 'native_pd_kd'),
                               ('effort', 'native_effort_caps_nm'), ('driveMode', 'native_drive_modes')):
                if before[field].tolist() != baseline[key]:
                    raise ValueError('baseline native PD differs: '+field)
            if not (np.all(before['stiffness'][indices] == 200) and
                    np.all(before['damping'][indices] == 50) and np.all(before['effort'][indices] == 150)):
                raise ValueError('approved Shoulder baseline differs')
            state, target = native_state(self), self.target.copy()
            stored_target = native_targets(self)
            expected = before.copy()
            expected['stiffness'][indices] = stiffness
            if not self.gym.set_actor_dof_properties(self.env, self.human, expected):
                raise RuntimeError('Shoulder PD submission failed')
            actual = self.gym.get_actor_dof_properties(self.env, self.human).copy()
            self.pd_checks = {'exact_requested_properties': bool(np.array_equal(expected, actual)),
                'PD_submission_preserves_initial_states_targets': state == native_state(self) and
                    bool(np.array_equal(target, self.target)) and
                    bool(np.array_equal(stored_target, native_targets(self))),
                'no_physics_steps_at_PD_submission': self.steps == 0}
            if not all(self.pd_checks.values()):
                raise ValueError(self.pd_checks)
            self.kp[indices] = stiffness
            self.pd_before, self.pd_after = properties(before), properties(actual)
            self.shoulder_indices = indices
        except Exception:
            self.close()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stiffness', type=int, choices=(200, 300), required=True)
    parser.add_argument('--steps', type=int, choices=(24, 120), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError('preserve previous comparison')
    args.out.mkdir(parents=True, exist_ok=True)
    runner = short_runner if args.steps == 24 else hold_runner
    baseline = ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on'
    previous = baseline.parent.parent/'dof_force_observation_v1/attempt_v2/native'
    frame = baseline.parent.parent/'palm_frame_audit_v1/measurements_validated'
    settings = ROOT/'stability_adapter_2/trials/quiescent_3s_v1/reference.json'
    inputs = {str(p.resolve()):runner.sha(p) for p in
              (Path(__file__), Path(__file__).with_name('run_dof_force_observation.py'))}
    reference_paths = [previous/(n+'.json') for n in RAW] if args.stiffness == 200 else [previous/'states.json']
    inputs.update({str(p.resolve()):runner.sha(p) for p in reference_paths})
    old_environment, old_argv = runner.InitialEnvironment, sys.argv
    runner.InitialEnvironment = lambda value: ShoulderEnvironment(value, args.stiffness)
    sys.argv = [str(Path(__file__)), '--mode', 'PALM_RATE', '--settings', str(settings),
        '--reference-run', str(baseline), '--frame-dir', str(frame), '--out', str(args.out/'native')]
    try:
        runner.main()
        env = ShoulderEnvironment.instance
        report = runner.read(args.out/'native/report.json')
        count = args.steps
        prefix = {n:runner.read(args.out/'native'/(n+'.json')) ==
                  runner.read(previous/(n+'.json'))[:count if n in ('controls', 'contacts') else count+1]
                  for n in RAW} if args.stiffness == 200 else None
        checks = dict(env.pd_checks,
            thirteen_native_contracts_pass=len(report['checks']) == 13 and all(report['checks'].values()),
            same_full_initial_state=runner.read(args.out/'native/states.json')[0] ==
                runner.read(previous/'states.json')[0],
            aligned_total_force_samples=len(env.force_records) == count and
                [r['physics_step'] for r in env.force_records] == list(range(1, count+1)),
            total_force_reads_preserve_states_targets_PD=env.force_reads_preserve,
            force_types_and_units_verified=all(t == 1 and u == 'Nm' for t, u in zip(env.force_types, env.force_units)),
            completed_expected_steps=env.steps == count)
        if prefix is not None:
            checks['seven_original_baseline_arrays_exact'] = all(prefix.values())
        paths = [args.out/'native'/(n+'.json') for n in RAW+('report', 'initial_source')]
        if any(inputs[p] != h for p, h in report['input_sha256'].items() if p in inputs):
            raise ValueError('native/wrapper source SHA conflict')
        inputs.update(report['input_sha256'])
        inputs.update({str(p.resolve()):runner.sha(p) for p in paths})
        checks['sources_current'] = all(runner.sha(p) == h for p, h in inputs.items())
        result = {'checks': checks, 'stiffness': args.stiffness, 'physics_steps': count,
            'human_joint_names': env.names, 'shoulder_indices': env.shoulder_indices,
            'PD_before': env.pd_before, 'PD_after': env.pd_after, 'input_sha256': inputs,
            'initial_PD_submission': 'after fresh prepare/initial reset, before any physics step; no runtime changes',
            'previous_baseline_seven_array_equality': prefix,
            'native_DOF_type_codes': env.force_types, 'native_DOF_units': env.force_units,
            'scope': 'approved Shoulder stiffness comparison, total DOF force is not actuator-only torque or PD cause; no guitar stability/playing success'}
        (args.out/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        if not all(checks.values()):
            raise AssertionError(checks)
        print(json.dumps({'stiffness':args.stiffness, 'steps':count, 'checks':checks}, indent=2))
    except Exception as error:
        env = ShoulderEnvironment.instance
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__, 'error':str(error),
            'completed_physics_steps':getattr(env, 'steps', 0)}, indent=2)+'\n')
        raise
    finally:
        runner.InitialEnvironment, sys.argv = old_environment, old_argv
        env = ShoulderEnvironment.instance
        if env is not None:
            (args.out/'sensors.json').write_text(json.dumps(env.force_records, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
