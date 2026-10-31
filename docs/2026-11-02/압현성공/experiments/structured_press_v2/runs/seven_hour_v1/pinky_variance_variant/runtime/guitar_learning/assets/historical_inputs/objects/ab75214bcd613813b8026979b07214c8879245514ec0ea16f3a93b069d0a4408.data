"""Noise-enabled warm start: bounded training smoke or full native evaluation."""
import argparse
from pathlib import Path
from .initial_pose_noise_v1 import read,save,sha


def warm_start(model,checkpoint,abi):
    import torch
    from .joint_policy_v1 import digest
    d=torch.load(checkpoint,map_location=next(model.parameters()).device,weights_only=False)
    if digest(d['abi'])!=d['abi_sha256']:raise ValueError('source ABI hash mismatch')
    if any(sha(path)!=expected for path,expected in d['abi']['source_sha256'].items()):raise ValueError('old checkpoint source changed')
    keys=('profile','observation','names','groups','lower','upper','rates','action_codec','horizon_s','control_hz','physics_hz','baseline_contract_sha256','residual_caps_rad','baseline_nominal_guard','policy_update','strap_enabled','strap','action_dimension')
    if any(d['abi'][k]!=abi[k] for k in keys):raise ValueError('physical/control/model contracts differ')
    model.load_state_dict(d['model'],strict=True)
    return {'source':str(checkpoint),'sha256':sha(checkpoint),'source_updates':d['updates'],'source_transitions':d['transitions'],'model_and_RMS':'exact copy','optimizer_and_counters':'fresh; changed initial-state distribution','scope':'explicit warm start, not exact physical/RNG resume'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bank',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--eval-index',type=int);p.add_argument('--num-envs',type=int,default=4);p.add_argument('--updates',type=int,default=1);p.add_argument('--rollout-steps',type=int,default=64);p.add_argument('--device',choices=('cuda','cpu'),default='cuda');a=p.parse_args()
    if a.num_envs<1 or a.updates<1 or a.rollout_steps<1:p.error('positive N/T/update counts required')
    from .dual_music_scene_v1 import DualMusicScene
    from .deadline_initial_noise_v1 import NativeInitialNoiseEnvironment
    from .parallel_initial_noise_v1 import ParallelInitialNoiseEnvironment
    from .parallel_collect_v1 import ParallelPPO
    from .joint_policy_v1 import JointActorCritic,digest
    from .joint_ppo_v1 import PPOConfig
    from .run_parallel_training_v1 import input_closure,learning_abi
    import torch
    import numpy as np
    torch.set_num_threads(1);torch.manual_seed(103);a.out.mkdir(parents=True,exist_ok=False)
    closure=input_closure();closure.update(read(a.bank)['input_sha256']);closure[str(a.bank.resolve())]=sha(a.bank);closure[str(a.checkpoint.resolve())]=sha(a.checkpoint)
    save(a.out/'attempt.json',{'input_sha256':closure,'initial_noise_bank':str(a.bank),'physical_initial_noise':True,'training_steps_per_worker':a.rollout_steps,'num_envs':a.num_envs,'requested_updates':a.updates,'evaluation_index':a.eval_index})
    env=None
    try:
        env=NativeInitialNoiseEnvironment(a.bank,bank_index=a.eval_index,recording=True,output=a.out/'native',strap_enabled=True,seed=103) if a.eval_index is not None else ParallelInitialNoiseEnvironment(a.num_envs,a.out/'workers',a.bank,103)
        obs=env.reset();env.require_training_ready();abi=learning_abi(env,closure);model=JointActorCritic(825,abi['groups']).to(a.device)
        transfer=warm_start(model,a.checkpoint,abi);save(a.out/'warm_start.json',transfer);save(a.out/'learning_abi.json',{'payload':abi,'sha256':digest(abi)})
        save(a.out/'initial_values.json',env.metadata)
        if a.eval_index is not None:
            steps=0;reward_total=0.;model.eval()
            while True:
                with torch.no_grad():action=model.sample(torch.as_tensor(obs,device=a.device,dtype=torch.float32)[None],deterministic=True)['action'][0].cpu().numpy()
                obs,reward,terminated,truncated,info=env.step(action);steps+=1;reward_total+=reward
                if terminated or truncated:break
            save(a.out/'report.json',{'completed':True,'controls':steps,'reward':reward_total,'terminated':terminated,'truncated':truncated,'checkpoint':transfer,'native_report':env.last_report,'deterministic':True,'scope':'full representative native evaluation; no noisy PPO update'})
        else:
            trainer=ParallelPPO(model,abi,PPOConfig(learning_rate=3e-5));trainer._collection_env=env;trainer._collection_obs=np.array(obs,copy=True)
            trainer.save(a.out/'initial.pt');initial=env.snapshots();metrics=[]
            for i in range(a.updates):
                batch=trainer.collect(env,a.rollout_steps);update=trainer.update(batch)
                if update['optimizer_steps']<=0:raise RuntimeError('no accepted optimizer step; smoke not completed')
                metrics.append({'update':i+1,'collection':trainer.last_collection_stats,'metrics':update})
                save(a.out/('update_%03d.json'%(i+1)),metrics[-1]);trainer.save(a.out/('checkpoint_%03d.pt'%(i+1)))
            save(a.out/'report.json',{'completed':True,'updates':trainer.updates,'transitions':trainer.transitions,'initial_native':initial,'final_native':env.snapshots(),'reset_records':env.reset_records,'metrics':metrics,'source_checkpoint':transfer,'scope':'new initial distribution CUDA/collector smoke; no success claim'})
    finally:
        if env is not None:env.close()
    if any(sha(path)!=digest for path,digest in closure.items()):raise AssertionError('consumed input changed')
    save(a.out/'inputs_verified.json',{'unchanged':True,'inputs':len(closure)})
if __name__=='__main__':main()
