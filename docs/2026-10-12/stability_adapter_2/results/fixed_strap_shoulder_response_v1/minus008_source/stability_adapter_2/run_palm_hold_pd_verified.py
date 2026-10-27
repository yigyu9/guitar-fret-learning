"""Compare left-arm native stiffness/damping at unchanged initial pose and commands."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OBSERVATION=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--trial',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    source=OBSERVATION/'analysis.json';hashes={str(source):sha(source)};analysis=read(source)
    trial_path=args.trial.resolve();hashes[str(trial_path)]=sha(trial_path);trial=read(trial_path)
    candidate=Path(trial['candidate_path']);reference=OBSERVATION/'full/native';scale=trial['left_arm_PD_scale']
    if scale not in (1.,1.5,2.):raise ValueError('three planned scales only')
    paths=[Path(p) for p in analysis['input_sha256']]+[Path(__file__).resolve(),candidate,
        ROOT/'stability_adapter_2/PALM_HOLD_PD_PLAN.md',ROOT/'stability_adapter_2/PALM_HOLD_PD_VERIFICATION.md',ROOT/'isaacgym/docs/programming/physics.html']
    paths += [reference/(n+'.json') for n in ('report','states','trace','tasks','contacts','controls')]
    hashes.update({str(p):sha(p) for p in paths})
    if not all(analysis['checks'].values()) or any(sha(p)!=h for p,h in analysis['input_sha256'].items()):raise AssertionError('observation inputs')
    reference_report=read(reference/'report.json')
    if reference_report['candidate_path']!=str(candidate):raise AssertionError('same full candidate required')
    from . import self_collision_environment as environment_module
    from . import run_palm_finite_response as runner
    from .run_joint_hold import native_state
    from .environment import np
    original_environment=environment_module.SelfCollisionEnvironment
    class GainEnvironment(original_environment):
        instance=None
        def __init__(self,*params,**kwargs):
            GainEnvironment.instance=self;self.pd_observation=None
            super().__init__(*params,**kwargs)
            try:
                arm=reference_report['arm_indices']
                if [self.names[i] for i in arm]!=[reference_report['human_joint_names'][i] for i in arm] or len(arm)!=12:raise AssertionError('left arm layout')
                before=native_state(self);target=self.target.copy();props=self.gym.get_actor_dof_properties(self.env,self.human).copy();expected=props.copy()
                for name in ('stiffness','damping'):expected[name][arm]=props[name][arm]*scale
                if not self.gym.set_actor_dof_properties(self.env,self.human,expected):raise RuntimeError('native PD setter rejected properties')
                actual=self.gym.get_actor_dof_properties(self.env,self.human).copy()
                checks={'setter_preserves_state_and_Python_target':before==native_state(self) and np.array_equal(target,self.target),
                    'exact_expected_property_readback':bool(np.array_equal(expected,actual))}
                self.pd_observation={'checks':checks,'left_arm_indices':arm,'left_arm_names':[self.names[i] for i in arm],
                    'before':{n:props[n].astype(int if n=='driveMode' else float).tolist() for n in props.dtype.names},
                    'after':{n:actual[n].astype(int if n=='driveMode' else float).tolist() for n in actual.dtype.names}}
                if not all(checks.values()):raise AssertionError(checks)
            except Exception:self.close();raise
    old_argv=sys.argv;environment_module.SelfCollisionEnvironment=GainEnvironment
    sys.argv=[str(Path(__file__)),'--candidate',str(candidate),'--out',str(args.out/'native')]
    try:
        runner.main();env=GainEnvironment.instance;report=read(args.out/'native/report.json')
        equality={n:read(args.out/'native'/(n+'.json'))==read(reference/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')}
        checks={'native_contracts':all(report['checks'].values()) and not report['failure'],
            'PD_setter_contracts':all(env.pd_observation['checks'].values()),'baseline_five_arrays_exact':scale!=1 or all(equality.values()),
            'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
        # controls also include task-error metadata, which can change despite identical target commands.
        new_controls=read(args.out/'native/controls.json');old_controls=read(reference/'controls.json')
        checks['same_submitted_targets']=all(a['final_target_rad']==b['final_target_rad'] for a,b in zip(new_controls,old_controls)) and len(new_controls)==len(old_controls)==24
        result={'checks':checks,'input_sha256':hashes,'trial':trial,'native_initializations':1,'physics_steps':report['physics_steps'],
            'properties':env.pd_observation,'reference_five_array_equality':equality,'scope':'left-arm kp/kd only; constant Python targets, free guitar; no stability success or torque saturation certification'}
        (args.out/'PD.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'scale':scale,'checks':checks}),flush=True)
    except Exception as error:
        env=GainEnvironment.instance;(args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),'physics_steps':getattr(env,'steps',0)},indent=2)+'\n');raise
    finally:
        environment_module.SelfCollisionEnvironment=original_environment;sys.argv=old_argv;env=GainEnvironment.instance
        if env is not None:(args.out/'partial_PD.json').write_text(json.dumps(env.pd_observation,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
