"""Native graphics-free lifecycle test and frozen-policy physical comparison."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--reference-episode',type=Path,required=True)
    p.add_argument('--resets',type=int,default=60)
    a=p.parse_args()
    if a.resets<=0:p.error('positive reset count required')
    a.out.mkdir(parents=True,exist_ok=False)
    # Native Isaac must be imported before Torch.
    from .dual_music_scene_v1 import DualMusicScene
    from .deadline_native_v8 import NativeDeadlineEnvironment
    from .run_deadline_training_v9 import input_closure,learning_abi
    from .deadline_graphics_migration_v1 import adopt_checkpoint
    from .deadline_guarded_ppo_v3 import GuardedPPO
    from .joint_ppo_v1 import PPOConfig
    from .joint_policy_v1 import JointActorCritic
    from .run_joint_hold import native_state
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(103);np.random.seed(103)
    reference={name:json.loads((a.reference_episode/name).read_text()) for name in ('trace.json','controls.json','initial_values.json')}
    closure=input_closure()
    closure.update({str(a.checkpoint.resolve()):sha(a.checkpoint),**{str((a.reference_episode/n).resolve()):sha(a.reference_episode/n) for n in reference}})
    save(a.out/'attempt.json',{'inputs':closure,'resets':a.resets,'reference_episode':str(a.reference_episode.resolve()),'policy_device':'cuda','scope':'finite lifecycle stress; deterministic physical comparison; no video or PPO update'})
    env=NativeDeadlineEnvironment(recording=False,strap_enabled=True,seed=103)
    records=[];failure=None;exact=False
    try:
        reference_initial=reference['initial_values.json']
        for n in range(a.resets):
            obs=env.reset();env.require_training_ready()
            assert env.initial==reference_initial['native_initial_state']
            assert env.scene.names==reference_initial['joint_names']
            for k,v in reference_initial['PD_properties'].items():assert np.array_equal(env.scene.pd_properties[k],np.array(v,dtype=env.scene.pd_properties[k].dtype))
            record=copy.deepcopy(env.metadata['graphics_resource_policy'])
            assert record['creation_calls'][0]['forwarded_graphics_device_id']==-1
            assert record['render_lookup_counts']=={}
            records.append(dict(reset=n+1,**record))
            save(a.out/('reset_%04d.json'%(n+1)),records[-1])
            print('reset',n+1,'graphics_device -1 exact_initial_and_PD',flush=True)
        model=JointActorCritic(env.obs_dim,env.scene.contract.groups).to('cuda')
        trainer=GuardedPPO(model,learning_abi(env,closure),PPOConfig(learning_rate=3e-5))
        adoption=adopt_checkpoint(a.checkpoint,trainer,a.out/'adopted_checkpoint.pt')
        trainer.load(a.out/'adopted_checkpoint.pt',restore_rng=False)
        save(a.out/'adoption.json',adoption)
        model.eval();trace=[];controls=[]
        def capture():
            state=native_state(env.scene);pose=state['guitar_body_states'][0]['pose']
            trace.append({'physics_step':env.scene.steps,'position_W_m':[pose['p'][k] for k in 'xyz'],
                'quaternion_xyzw':[pose['r'][k] for k in 'xyzw'],
                'q_rad':[v['pos'] for v in state['human_dof_states']],
                'qdot_rad_s':[v['vel'] for v in state['human_dof_states']],
                'strap':env.scene.strap_state(),'safety_violation':env.safety_violation})
        capture()
        while True:
            sample=model.sample(torch.as_tensor(obs,device='cuda',dtype=torch.float32)[None],deterministic=True)
            teacher=env.current_teacher_nominal.tolist()
            source_actions=copy.deepcopy(env.last_source_actions)
            obs,reward,terminated,truncated,info=env.step(sample['action'][0].cpu().numpy())
            row=copy.deepcopy(env.last_step)
            row.update(teacher_nominal81_rad=teacher,baseline_source_actions=source_actions,
                nominal_guard_delta81_rad=[n-t for n,t in zip(row['nominal81_rad'],teacher)])
            controls.append(row);capture()
            if env.tick%120==0:print('comparison_tick',env.tick,flush=True)
            if terminated or truncated:break
        save(a.out/'trace.json',trace);save(a.out/'controls.json',controls)
        exact=trace==reference['trace.json'] and controls==reference['controls.json']
        deltas={}
        for field in ('position_W_m','quaternion_xyzw','q_rad','qdot_rad_s'):
            if len(trace)==len(reference['trace.json']):
                deltas[field]=float(np.max(np.abs(np.array([r[field] for r in trace])-np.array([r[field] for r in reference['trace.json']]))))
        save(a.out/'comparison.json',{'trace_exact':trace==reference['trace.json'],'controls_exact':controls==reference['controls.json'],
            'trace_lengths':[len(trace),len(reference['trace.json'])],'controls_lengths':[len(controls),len(reference['controls.json'])],
            'max_absolute_difference':deltas,'native_report':env.last_report})
        if not exact:raise AssertionError('graphics-free deterministic trajectory differs from recorded reference; preserved for diagnosis')
    except BaseException as error:
        failure={'type':type(error).__name__,'message':str(error)}
        raise
    finally:
        env.close()
        unchanged=all(sha(path)==expected for path,expected in closure.items())
        save(a.out/'report.json',{'completed':failure is None and unchanged and exact,'failure':failure,'resets_completed':len(records),
            'inputs_unchanged':unchanged,'deterministic_trajectory_exact':exact,'scope':'60 creations and one full episode; not a universal no-crash guarantee'})
        if not unchanged:raise AssertionError('probe input changed')

if __name__=='__main__':main()
