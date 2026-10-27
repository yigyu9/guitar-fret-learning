"""Record real CPU/GPU physical states for a failure comparison, without training."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)

def body_rows(native):
    return [[*[r['pose']['p'][a] for a in 'xyz'], *[r['pose']['r'][a] for a in 'xyzw'],
             *[r['vel']['linear'][a] for a in 'xyz'], *[r['vel']['angular'][a] for a in 'xyz']]
            for kind in ('human','guitar','chair') for r in native[kind+'_body_states']]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case', choices=('cpu_zero','gpu2_zero','gpu1024_zero','gpu1024_policy'), required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--controls',type=int,default=120)
    args=parser.parse_args()
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract, prepared_input_paths
    from guitar_learning.training.start import settings_document
    args.out.mkdir(parents=True,exist_ok=False)
    paths=set(p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    paths.update(prepared_input_paths());paths.add(Path(__file__).resolve())
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    write(args.out/'inputs_before.json',pins)
    contract=load_prepared_reset_contract(); initial=contract['initial']
    count=1 if args.case=='cpu_zero' else 2 if args.case=='gpu2_zero' else 1024
    ids=[0] if count==1 else [0,1] if count==2 else [0,1,33,64,512,1023]
    metadata=dict(case=args.case,num_envs=count,mode='initial_stochastic_policy_no_PPO' if args.case.endswith('policy') else 'zero_action',
        env_ids=ids,human_body_names=initial['human_body_names'],guitar_body_names=initial['guitar_body_names'],
        loaded_assets=initial['loaded_assets'],chair_initial_placement=initial['chair_initial_placement'],
        physics_hz=240,control_hz=60,source='New native reproduction; original benchmark did not record body trajectories',
        initial_body_source='Pinned035/v14 prepared snapshot; actual fetched native states from physics step1 onward')
    body=[];qd=[];episode=[];global_steps=[];roots=[];events=[]
    pool=session=None;failure=None;started=time.monotonic()
    try:
        if args.case=='cpu_zero':
            from guitar_learning.runtime.finger_session import FlexibleLeftFingerSession
            from guitar_learning.core.safety import StabilityMonitor
            (args.out/'native').mkdir()
            session=FlexibleLeftFingerSession(contract['config'],args.out/'native',physics_threads=1)
            scene=session.scene
            from guitar_learning.native.native_contacts import body_names,read_contacts
            contact_names=body_names(scene.gym,scene.env)
            safety=StabilityMonitor(scene.human_bodies,scene.guitar_bodies)
            def record_cpu():
                native=scene.native()
                body.append(np.asarray(body_rows(native),dtype=np.float32)[None])
                qd.append(np.asarray([r['vel'] for r in native['human_dof_states']],dtype=np.float32)[None])
                episode.append(np.array([int(scene.steps)]));global_steps.append(int(scene.steps))
                return dict(native=native,native_contacts=dict(contacts=read_contacts(scene.gym,scene.env,contact_names)))
            first=record_cpu();safety.reset(first)
            for tick in range(args.controls):
                session.submit_policy_target(np.asarray(contract['target105']))
                for substep in range(4):
                    session.integrate();sample=record_cpu();value=safety.update(sample)
                    if value['failure_reasons']:
                        events.append(dict(control_tick=tick+1,global_step=int(scene.steps),env_id=0,failure_reasons=value['failure_reasons']))
                        break
                if events:break
                if (tick+1)%30==0:print(args.case,tick+1,flush=True)
        else:
            from guitar_learning.training.gpu_pool import GpuPool,FIELDS
            settings=settings_document('left',num_envs=count,device='cuda:0',physics='gpu',size='large')
            torch.set_num_threads(1);torch.manual_seed(7)
            pool=GpuPool(settings,args.out/'scene')
            scene=pool.scene; selected=torch.tensor(ids,device=scene.device)
            metadata['env_origins']=scene.origins[selected].tolist()
            metadata['training_contract']=pool.contract
            policy=None
            if args.case.endswith('policy'):
                from guitar_learning.skills.specialist_policy import SpecialistPolicy
                from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
                from guitar_learning.training.ppo import PPOTrainer,PPOConfig
                policy=SpecialistPolicy(512,size='large',contract=pool.contract,role='left',frozen_partner=False).to(scene.device)
                coordinator=CurriculumCoordinator(policy,pool)
                trainer=PPOTrainer(policy,PPOConfig(**settings['ppo']))
                checkpoint=ROOT/'docs/2026-10-20/guitar_learning_gpu_batch_v1/n1024_large_v4/initial.pt'
                trainer.load(checkpoint);pool.observation=coordinator.restore()
                metadata['policy_checkpoint']=str(checkpoint)
                metadata['policy_checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            def record_gpu(sample):
                body.append(sample['body_state'][selected].cpu().numpy())
                qd.append(sample['qd'][selected].cpu().numpy())
                episode.append(sample['physics_step'][selected].cpu().numpy())
                roots.append(scene._roots[selected].cpu().numpy())
                global_steps.append(scene.physics_steps)
            record_gpu(scene.snapshot())
            step=scene.step
            def recording_step(target,efforts):
                sample=step(target,efforts);record_gpu(sample);return sample
            scene.step=recording_step
            zero=torch.zeros(count,39,device=scene.device)
            for tick in range(args.controls):
                with torch.no_grad():
                    action=zero if policy is None else policy.act(*(pool.observation[k] for k in FIELDS))['action']
                    obs,reward,cost,terminated,truncated,completed=pool.step(action)
                for e in completed:
                    events.append(dict(control_tick=tick+1,global_step=scene.physics_steps,env_id=e['worker_id'],failure_reasons=e['failure_reasons']))
                done=(terminated|truncated).nonzero().flatten()
                if done.numel():pool.reset(done)
                if torch.cuda.mem_get_info()[0]<1024**3:raise MemoryError('CUDA free below1GiB')
                if (tick+1)%30==0:print(args.case,tick+1,'failure episodes',len(events),flush=True)
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
        raise
    finally:
        if pool is not None:pool.close()
        if session is not None:session.close()
        if body:
            arrays=dict(body=np.stack(body),qd=np.stack(qd),episode_step=np.stack(episode),global_step=np.asarray(global_steps))
            if roots:arrays['roots']=np.stack(roots)
            np.savez_compressed(args.out/'recording.npz',**arrays)
        write(args.out/'metadata.json',metadata)
        with (args.out/'events.jsonl').open('x') as stream:
            for event in events:stream.write(json.dumps(event)+'\n')
        changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
        report=dict(completed=failure is None,failure=failure,case=args.case,frames=len(body),global_physics_steps=global_steps[-1] if global_steps else 0,
            duration_s=global_steps[-1]/240. if global_steps else 0.,elapsed_s=time.monotonic()-started,changed_inputs=changed,
            failure_episodes=len(events),selected_failure_events=[e for e in events if e['env_id'] in ids],
            scene=pool.scene.diagnostics if pool is not None else None,physics_hz=240,optimizer_updates=0)
        write(args.out/'report.json',report)
        print(json.dumps(report),flush=True)

if __name__=='__main__':main()
