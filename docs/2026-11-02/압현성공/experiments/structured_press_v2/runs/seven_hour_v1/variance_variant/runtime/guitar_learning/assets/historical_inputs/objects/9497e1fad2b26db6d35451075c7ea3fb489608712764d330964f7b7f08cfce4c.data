"""Observe native masses, drive properties and total forces without changing commands."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',choices=('baseline','full'),required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    path=PREVIOUS/'analysis.json';hashes={str(path):sha(path)};analysis=read(path)
    reference=PREVIOUS.parent/'palm_coupled_response_v1/baseline' if args.label=='baseline' else PREVIOUS/'full'
    hashes[str(reference/'report.json')]=sha(reference/'report.json');reference_report=read(reference/'report.json');candidate=Path(reference_report['candidate_path'])
    paths=[Path(p) for p in analysis['input_sha256']]+[Path(__file__).resolve(),candidate,PREVIOUS/'artifact_inventory.json',
        ROOT/'stability_adapter_2/PALM_HOLD_OBSERVATION_PLAN.md',ROOT/'stability_adapter_2/run_palm_finite_response.py']
    paths += [reference/(n+'.json') for n in ('report','states','trace','tasks','contacts','controls')]
    paths += [ROOT/'isaacgym/docs'/n for n in ('programming/forcesensors.html','api/python/gym_py.html','api/python/struct_py.html','api/python/enum_py.html')]
    hashes.update({str(p):sha(p) for p in paths})
    if not all(analysis['checks'].values()) or any(sha(p)!=h for p,h in analysis['input_sha256'].items()):raise AssertionError('source inputs')
    inventory=read(PREVIOUS/'artifact_inventory.json')
    if not all(sha(p)==v['sha256'] for p,v in inventory.items()):raise AssertionError('previous phase changed')
    from . import self_collision_environment as environment_module
    from . import run_palm_finite_response as runner
    from .run_joint_hold import native_state
    from .environment import gymapi,np
    original_environment=environment_module.SelfCollisionEnvironment
    class ObservedEnvironment(original_environment):
        instance=None
        def __init__(self,*params,**kwargs):
            ObservedEnvironment.instance=self;self.force_records=[];self.query_preserves=True;self.properties=None
            super().__init__(*params,**kwargs)
            try:
                before=native_state(self);target=self.target.copy();props=self.gym.get_actor_dof_properties(self.env,self.human).copy();asset=self.gym.get_actor_asset(self.env,self.human)
                if list(self.gym.get_asset_dof_names(asset))!=self.names:raise AssertionError('DOF layout')
                self.force_types=[int(self.gym.get_asset_dof_type(asset,i)) for i in range(len(self.names))]
                units=['Nm' if v==int(gymapi.DOF_ROTATION) else 'N' if v==int(gymapi.DOF_TRANSLATION) else 'unverified' for v in self.force_types]
                bodies=[]
                for name,prop in zip(self.human_bodies,self.gym.get_actor_rigid_body_properties(self.env,self.human)):
                    bodies.append({'name':name,'mass_kg':float(prop.mass),'com_body_m':[float(getattr(prop.com,a)) for a in 'xyz'],
                        'inertia_com_kg_m2':[[float(getattr(getattr(prop.inertia,a),b)) for b in 'xyz'] for a in 'xyz']})
                self.properties={'human_body_properties':bodies,'human_joint_names':self.names,'native_DOF_type_codes':self.force_types,'native_DOF_units':units,
                    'drive_properties':{name:props[name].astype(float if name!='driveMode' else int).tolist() for name in props.dtype.names}}
                self.query_preserves &= bool(before==native_state(self) and np.array_equal(target,self.target) and np.array_equal(props,self.gym.get_actor_dof_properties(self.env,self.human)))
                if not self.query_preserves:raise AssertionError('property read changed state/target/PD')
            except Exception:self.close();raise
        def _create_scene(self):
            super()._create_scene();self.sensor_supported=bool(self.gym.enable_actor_dof_force_sensors(self.env,self.human))
            if not self.sensor_supported:raise RuntimeError('native DOF force sensors unsupported')
        def step_physics(self):
            super().step_physics();before=native_state(self);target=self.target.copy();props=self.gym.get_actor_dof_properties(self.env,self.human).copy();forces=self.gym.get_actor_dof_forces(self.env,self.human).copy()
            if forces.shape!=(len(self.names),) or forces.dtype!=np.float32 or not np.isfinite(forces).all():raise AssertionError('force vector')
            self.force_records.append({'physics_step':self.steps,'time_s':self.steps/240,'native_total_DOF_force':forces.astype(float).tolist()})
            self.query_preserves &= bool(before==native_state(self) and np.array_equal(target,self.target) and np.array_equal(props,self.gym.get_actor_dof_properties(self.env,self.human)))
            if not self.query_preserves:raise AssertionError('force read changed state/target/PD')
    old_argv=sys.argv;environment_module.SelfCollisionEnvironment=ObservedEnvironment
    sys.argv=[str(Path(__file__)),'--candidate',str(candidate),'--out',str(args.out/'native')]
    try:
        runner.main();env=ObservedEnvironment.instance;report=read(args.out/'native/report.json')
        equality={n:read(args.out/'native'/(n+'.json'))==read(reference/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')}
        checks={'native_contracts':all(report['checks'].values()) and not report['failure'],'five_previous_arrays_exact':all(equality.values()),
            'sensor_enable_supported':env.sensor_supported,'queries_preserve_states_targets_PD':env.query_preserves,
            '24_aligned_force_samples':len(env.force_records)==24 and [v['physics_step'] for v in env.force_records]==list(range(1,25)),
            'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
        result={'checks':checks,'input_sha256':hashes,'label':args.label,'reference_run':str(reference),'candidate_path':str(candidate),
            'native_initializations':1,'physics_steps':report['physics_steps'],'five_array_equality':equality,'t0_force_measurement':None,
            'properties':env.properties,'samples':env.force_records,'nonzero_force_samples':sum(any(v!=0 for v in row['native_total_DOF_force']) for row in env.force_records),
            'scope':'unchanged commands and physics; total DOF force at completed steps, not drive-only torque/contact force or saturation; static body readbacks can differ from original source masses'}
        (args.out/'observation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'checks':checks,'nonzero_force_samples':result['nonzero_force_samples']}),flush=True)
    except Exception as error:
        env=ObservedEnvironment.instance;(args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),'physics_steps':getattr(env,'steps',0)},indent=2)+'\n');raise
    finally:
        environment_module.SelfCollisionEnvironment=original_environment;sys.argv=old_argv;env=ObservedEnvironment.instance
        if env is not None:(args.out/'partial_observation.json').write_text(json.dumps({'properties':env.properties,'samples':env.force_records},indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
