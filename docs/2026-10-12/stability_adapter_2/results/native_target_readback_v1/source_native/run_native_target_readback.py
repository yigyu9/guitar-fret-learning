"""Read native stored targets in the unchanged 0.1-second PALM_RATE run."""
import argparse
import json
from pathlib import Path
import sys

from .environment import InitialEnvironment, ROOT, np
from .run_physx_contacts import native_state
from . import run_palm_position_compare as runner


class TargetEnvironment(InitialEnvironment):
    instance = None

    def __init__(self, settings):
        TargetEnvironment.instance = self
        self.readbacks = []
        self.reads_preserve = True
        super().__init__(settings)

    def read_targets(self, phase):
        state, target = native_state(self), self.target.copy()
        props = self.gym.get_actor_dof_properties(self.env, self.human).copy()
        stored = self.gym.get_actor_dof_position_targets(self.env, self.human).copy()
        if stored.shape!=(len(self.names),) or stored.dtype!=np.float32 or not np.isfinite(stored).all():
            raise ValueError('finite float32 native target vector required')
        self.reads_preserve &= bool(state==native_state(self) and np.array_equal(target,self.target)
            and np.array_equal(props,self.gym.get_actor_dof_properties(self.env,self.human)))
        self.readbacks.append({'physics_step':self.steps,'phase':phase,
            'submitted_targets_rad':target.astype(float).tolist(),
            'native_stored_targets_rad':stored.astype(float).tolist()})
        if not self.reads_preserve:
            raise RuntimeError('native target read changed states/targets/PD')

    def step_physics(self):
        self.read_targets('before_step')
        super().step_physics()
        self.read_targets('after_step')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if any((args.out/n).exists() for n in ('readbacks.json','report.json','failure.json')):
        raise FileExistsError('preserve previous readback observation')
    previous = ROOT/'docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1'
    native = previous/'attempt_v2/native'
    reference = ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on'
    frame = reference.parent.parent/'palm_frame_audit_v1/measurements_validated'
    raw = ('states','trace','controls','contacts','hands','queries','leg_torques')
    inputs = dict(runner.read(previous/'summary.json')['input_sha256'])
    paths = [Path(__file__).resolve(),Path(runner.__file__).resolve(),previous/'summary.json']
    paths += [ROOT/'isaacgym/docs/api/python/gym_py.html']
    paths += [native/(n+'.json') for n in raw]
    inputs.update({str(p.resolve()):runner.sha(p) for p in paths})
    if not all(runner.sha(p)==h for p,h in inputs.items()):
        raise ValueError('previous sources differ')
    original, argv = runner.InitialEnvironment, sys.argv
    runner.InitialEnvironment = TargetEnvironment
    sys.argv = [__file__,'--mode','PALM_RATE','--settings',str(ROOT/'stability_adapter_2/trials/quiescent_3s_v1/reference.json'),
        '--reference-run',str(reference),'--frame-dir',str(frame),'--out',str(args.out/'native')]
    try:
        runner.main()
        env = TargetEnvironment.instance
        count = {n:(25 if n in ('states','trace','hands','queries','leg_torques') else 24) for n in raw}
        prefix = {n:runner.read(args.out/'native'/(n+'.json'))==runner.read(native/(n+'.json'))[:count[n]] for n in raw}
        native_report = runner.read(args.out/'native/report.json')
        paths = [args.out/'native'/(n+'.json') for n in raw+('report',)]
        inputs.update({str(p.resolve()):runner.sha(p) for p in paths})
        values = np.array([r['native_stored_targets_rad'] for r in env.readbacks])
        submitted = np.array([r['submitted_targets_rad'] for r in env.readbacks])
        checks = {'original_native_contracts_pass':all(native_report['checks'].values()),
            'seven_prefix_arrays_exact':all(prefix.values()),'48_aligned_reads':
                [(r['physics_step'],r['phase']) for r in env.readbacks]==
                [(k,p) for n in range(24) for k,p in ((n,'before_step'),(n+1,'after_step'))],
            'reads_preserve_states_targets_PD':env.reads_preserve,
            'sources_current':all(runner.sha(p)==h for p,h in inputs.items())}
        report = {'checks':checks,'input_sha256':inputs,'seven_prefix_observations':prefix,
            'human_joint_names':env.names,'max_stored_submitted_difference_rad':float(np.abs(values-submitted).max()),
            'all_reads_exact_observation':bool(np.array_equal(values,submitted)),
            'scope':'native stored targets, not actuator torque, PD cause or guitar stability success',
            'native_physics_steps':env.steps}
        (args.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if not all(checks.values()):
            raise AssertionError(checks)
        print(json.dumps({'checks':checks,'max_target_difference_rad':report['max_stored_submitted_difference_rad']},indent=2))
    except Exception as error:
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'error':str(error),
            'completed_physics_steps':getattr(TargetEnvironment.instance,'steps',0)},indent=2)+'\n')
        raise
    finally:
        runner.InitialEnvironment,sys.argv = original,argv
        if TargetEnvironment.instance is not None:
            (args.out/'readbacks.json').write_text(json.dumps(TargetEnvironment.instance.readbacks,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    main()
