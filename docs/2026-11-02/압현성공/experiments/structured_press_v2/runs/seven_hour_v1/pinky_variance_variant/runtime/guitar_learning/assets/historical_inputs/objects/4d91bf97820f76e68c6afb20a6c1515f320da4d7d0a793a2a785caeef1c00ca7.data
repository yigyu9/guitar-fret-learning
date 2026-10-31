"""Independent music-task training and full-timeline native evaluation."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

from ..fresh_learning_v1.run_v5 import sha, save

MUSIC_CHECKPOINT_SCHEMA = 'fresh54_music_ppo_v1'
INITIALIZATION_PROFILE = {'version': 'fresh_music_exploration_v4', 'initial_log_std': -3.0,
                          'action_authority': 'full tanh54', 'learned_log_std': True}


def initialize_policy(policy):
    import torch
    with torch.no_grad():
        policy.log_std.fill_(INITIALIZATION_PROFILE['initial_log_std'])
    return policy


def emit(stream, value):
    stream.write(json.dumps(value, allow_nan=False)+'\n')
    stream.flush()


def validate_resume(payload, trainer, contract):
    """Reject Stage-A/legacy models and changed music/physics before loading."""
    import torch
    if not isinstance(payload, dict) or payload.get('identity') != trainer._identity():
        raise ValueError('music checkpoint schema, architecture, or PPO config mismatch')
    metadata = payload.get('metadata')
    if not isinstance(metadata, dict) or metadata.get('contract') != contract:
        raise ValueError('music checkpoint timeline, physics, asset, or observation contract mismatch')
    if not all(torch.isfinite(value).all() for value in payload['model'].values()):
        raise ValueError('nonfinite music model')
    if not isinstance(payload.get('updates'), int) or payload['updates'] < 0:
        raise ValueError('invalid completed-update count')
    counts = metadata.get('cumulative')
    if metadata.get('optimizer_update_in_progress'):
        raise ValueError('interrupted optimizer update is not resumable')
    if not isinstance(counts, dict) or counts.get('completed_updates') != payload['updates']:
        raise ValueError('music checkpoint cumulative counters mismatch')
    return metadata


def collect_rollout(env, policy, obs, steps, device, state, command_sink, transition_sink, episode_sink):
    """No fault recovery: partial buffers never reach the optimizer."""
    import torch
    buffer = {}
    state['pending_valid_controls'] = 0
    for index in range(steps):
        observation = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            output = policy.act(observation)
        action = output['action'][0].cpu().numpy()
        state['attempted_controls'] += 1
        command = dict(rollout_id=state['rollout_id'], rollout_index=index,
            process_control_attempt=state['attempted_controls'], episode_seed=env.seed,
            physics_step_before=env.scene.steps, action54=action.tolist())
        state['last_attempt'] = command
        command_sink(command)
        try:
            next_obs, reward, cost, terminated, truncated, info = env.step(action)
        finally:
            command['physics_step_after'] = env.scene.steps
        state['valid_controls'] += 1
        state['pending_valid_controls'] += 1
        with torch.no_grad():
            nxt = policy.act(torch.as_tensor(next_obs, dtype=torch.float32, device=device).unsqueeze(0), deterministic=True)
        row = dict(obs=observation, latent=output['latent'], logp=output['logp'],
            reward_value=output['reward_value'], cost_value=output['cost_value'],
            next_reward_value=nxt['reward_value'], next_cost_value=nxt['cost_value'])
        row.update({k:torch.tensor([v],device=device) for k,v in dict(reward=float(reward),cost=float(cost),
            terminated=bool(terminated),truncated=bool(truncated)).items()})
        for key,value in row.items():
            buffer.setdefault(key,[]).append(value)
        transition_sink(dict(rollout_id=state['rollout_id'], process_control_attempt=state['attempted_controls'],
            episode_seed=env.seed,reward=float(reward),cost=float(cost),terminated=bool(terminated),truncated=bool(truncated),info=info))
        obs = next_obs
        if terminated or truncated:
            episode_sink(dict(kind='episode_end',episode_seed=env.seed,metadata=env.metadata,info=info,
                terminated=bool(terminated),truncated=bool(truncated)))
            state['forbidden_calls'].extend(env.scene.forbidden_calls)
            state['finished_episodes'] += 1
            state['next_seed'] += 1
            obs = env.reset(seed=state['next_seed'])
            episode_sink(dict(kind='episode_start',episode_seed=env.seed,metadata=env.metadata))
    return {key:torch.stack(value) for key,value in buffer.items()},obs


def cumulative_counts(prior, state, updates, training=True):
    if not training:
        return dict(completed_updates=prior.get('completed_updates',0),
            attempted_controls=prior.get('attempted_controls',0),
            valid_controls=prior.get('valid_controls',0),
            accepted_ppo_steps=prior.get('accepted_ppo_steps',0),
            excluded_valid_controls=prior.get('excluded_valid_controls',0))
    return dict(completed_updates=updates,
        attempted_controls=prior.get('attempted_controls',0)+state['attempted_controls'],
        valid_controls=prior.get('valid_controls',0)+state['valid_controls'],
        accepted_ppo_steps=prior.get('accepted_ppo_steps',0)+state['accepted_ppo_steps'],
        excluded_valid_controls=prior.get('excluded_valid_controls',0)+state['pending_valid_controls'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--mode',choices=('train','baseline','eval'),required=True)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--stage',choices=('B','C','D'),required=True)
    parser.add_argument('--event-limit',type=int)
    parser.add_argument('--phrase-events',type=int,default=8)
    parser.add_argument('--tempo-scale',type=float,default=1.)
    parser.add_argument('--preroll-s',type=float,default=1.)
    parser.add_argument('--updates',type=int,default=16,help='cumulative target for train')
    parser.add_argument('--rollout-steps',type=int,default=256)
    parser.add_argument('--save-every',type=int,default=4)
    parser.add_argument('--seed',type=int,default=101)
    parser.add_argument('--device',choices=('cpu','cuda'),default='cuda')
    parser.add_argument('--checkpoint',type=Path)
    args=parser.parse_args()
    if not 0 < args.tempo_scale < float('inf') or not 0 <= args.preroll_s < float('inf'):
        parser.error('finite positive tempo scale and nonnegative preroll required')
    if min(args.updates,args.rollout_steps,args.save_every,args.phrase_events)<1 or (args.event_limit is not None and args.event_limit<1):
        parser.error('positive budgets required')
    if args.mode=='eval' and args.checkpoint is None or args.mode=='baseline' and args.checkpoint is not None:
        parser.error('eval requires checkpoint; baseline forbids checkpoint')
    args.out=args.out.resolve()
    args.bundle=args.bundle.resolve()
    if args.checkpoint:
        args.checkpoint=args.checkpoint.resolve()
    args.out.mkdir(parents=True,exist_ok=False)
    import isaacgym  # noqa: F401: must load before torch
    from .environment_v3 import MusicGuitarEnvironment, collect_inputs
    from ..fresh_learning_v1.policy import Policy
    from ..fresh_learning_v1.ppo import PPOConfig,PPOTrainer
    from ..gym_trial_recording import GymTrialRecording
    from ..run_joint_hold import native_state
    import random
    import numpy as np
    import torch
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)
    inputs=collect_inputs(args.bundle)
    hashes=inputs if isinstance(inputs,dict) else {str(Path(p).resolve()):sha(p) for p in inputs}
    contract_inputs=dict(hashes)
    for path in (Path(__file__).resolve(),Path(__file__).with_name('launch_v4.sh')):
        hashes[str(path)]=sha(path)
    if args.checkpoint:
        hashes[str(args.checkpoint)]=sha(args.checkpoint)
    project=Path(__file__).resolve().parents[2]
    for name in hashes:
        path=Path(name)
        if path.suffix in ('.py','.sh','.json') and project in path.parents:
            target=args.out/'source_before'/path.relative_to(project)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
    save(args.out/'attempt.json',dict(arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
        input_sha256=hashes,started_unix=time.time(),old_policy_loaded=False,
        initialization='explicit own music resume' if args.checkpoint else 'new random weights',
        initialization_profile=INITIALIZATION_PROFILE,recovery='all errors fatal; no selective recovery'))
    env=trainer=recorder=None
    failure=None
    latest=fault_checkpoint=None
    contract=None
    prior={}
    original_seed=args.seed
    initial_updates=0
    initial_parameters=None
    videos={}
    start=time.monotonic()
    state=dict(rollout_id=0,attempted_controls=0,valid_controls=0,accepted_ppo_steps=0,pending_valid_controls=0,
        finished_episodes=0,next_seed=args.seed,forbidden_calls=[],last_attempt=None,optimizer_update_in_progress=False)
    def metadata():
        return dict(contract=contract,initial_seed=original_seed,current_process_seed=args.seed,
            resume_source=str(args.checkpoint) if args.checkpoint else None,
            cumulative=cumulative_counts(prior,state,trainer.updates),physical_resume='fresh episode required',
            optimizer_update_in_progress=state['optimizer_update_in_progress'])
    try:
        env=MusicGuitarEnvironment(bundle=args.bundle,stage=args.stage,event_limit=args.event_limit,phrase_events=args.phrase_events,tempo_scale=args.tempo_scale,preroll_s=args.preroll_s,recording=args.mode!='train',seed=args.seed)
        obs=env.reset(seed=args.seed)
        policy=initialize_policy(Policy(env.observation_dim).to(args.device))
        trainer=PPOTrainer(policy,PPOConfig())
        trainer.schema=MUSIC_CHECKPOINT_SCHEMA
        contract=dict(environment=env.abi,observation_slices=env.observation_slices,
            music_task=env.task.content_document(),initialization_profile=INITIALIZATION_PROFILE,stage=args.stage,event_limit=args.event_limit,input_sha256=contract_inputs)
        if args.checkpoint:
            payload=torch.load(args.checkpoint,map_location='cpu',weights_only=False)
            stored=validate_resume(payload,trainer,contract)
            trainer.load(args.checkpoint)
            prior=stored['cumulative']
            original_seed=stored['initial_seed']
        initial_updates=trainer.updates
        if args.mode=='train' and initial_updates>=args.updates:
            raise ValueError('cumulative target must exceed completed updates')
        save(args.out/'config.json',dict(contract=contract,ppo=asdict(trainer.config),episode_initialization=env.metadata,
            initial_updates=initial_updates,initial_seed=original_seed,current_process_seed=args.seed))
        save(args.out/'initial_state.json',native_state(env.scene))
        properties=env.scene.gym.get_actor_dof_properties(env.scene.env,env.scene.human)
        save(args.out/'native_properties.json',dict(guitar=env.scene.mass_properties,joint_names=env.scene.names,
            PD_properties=[{key:row[key].item() for key in properties.dtype.names} for row in properties],
            scalar_PD_kp=env.controller.kp.tolist(),scalar_PD_kd=env.controller.kd.tolist()))
        initial_parameters={k:v.detach().clone() for k,v in policy.state_dict().items()}
        if args.mode=='train':
            candidate=args.out/('checkpoint_%04d.pt'%trainer.updates)
            trainer.save(candidate,metadata=metadata())
            latest=candidate
        else:
            recorder=GymTrialRecording(env.scene,args.out)
            recorder.capture()
        with (args.out/'commands.jsonl').open('x') as commands,(args.out/'transitions.jsonl').open('x') as transitions,(args.out/'episodes.jsonl').open('x') as episodes,(args.out/'metrics.jsonl').open('x') as metrics:
            emit(episodes,dict(kind='episode_start',episode_seed=env.seed,metadata=env.metadata))
            if args.mode=='train':
                while trainer.updates<args.updates:
                    state['rollout_id']+=1
                    buffer,obs=collect_rollout(env,policy,obs,args.rollout_steps,args.device,state,
                        lambda row:emit(commands,row),lambda row:emit(transitions,row),lambda row:emit(episodes,row))
                    state['optimizer_update_in_progress']=True
                    result=trainer.update(buffer)
                    state['optimizer_update_in_progress']=False
                    state['accepted_ppo_steps']+=args.rollout_steps
                    state['pending_valid_controls']=0
                    record=dict(kind='update',rollout_id=state['rollout_id'],update=trainer.updates,
                        process_updates=trainer.updates-initial_updates,process_counters=state,losses=result,
                        elapsed_seconds=time.monotonic()-start)
                    emit(metrics,record)
                    print(json.dumps(record,allow_nan=False),flush=True)
                    if trainer.updates%args.save_every==0 or trainer.updates==args.updates:
                        candidate=args.out/('checkpoint_%04d.pt'%trainer.updates)
                        trainer.save(candidate,metadata=metadata())
                        latest=candidate
            else:
                # One episode through its declared timeline; no evaluation retry.
                for index in range(1000000):
                    observation=torch.as_tensor(obs,dtype=torch.float32,device=args.device).unsqueeze(0)
                    with torch.no_grad():
                        output=policy.act(observation,deterministic=True)
                    action=np.zeros(54,dtype=np.float32) if args.mode=='baseline' else output['action'][0].cpu().numpy()
                    state['attempted_controls']+=1
                    command=dict(process_control_attempt=state['attempted_controls'],episode_seed=env.seed,
                        physics_step_before=env.scene.steps,action54=action.tolist())
                    state['last_attempt']=command
                    emit(commands,command)
                    try:
                        obs,reward,cost,terminated,truncated,info=env.step(action)
                    finally:
                        command['physics_step_after']=env.scene.steps
                    state['valid_controls']+=1
                    emit(transitions,dict(step=state['valid_controls'],reward=float(reward),cost=float(cost),
                        terminated=bool(terminated),truncated=bool(truncated),info=info))
                    if env.scene.steps%recorder.interval==0 or terminated or truncated:
                        recorder.capture()
                    if terminated or truncated:
                        state['finished_episodes']=1
                        emit(episodes,dict(kind='episode_end',episode_seed=env.seed,metadata=env.metadata,
                            terminated=bool(terminated),truncated=bool(truncated),info=info))
                        break
                else:
                    raise RuntimeError('music episode control protection budget exceeded')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),
            diagnostic=getattr(error,'diagnostic',None),last_attempt=state['last_attempt'])
        if trainer is not None and contract is not None and args.mode=='train':
            try:
                candidate=args.out/('fault_checkpoint_%04d.pt'%trainer.updates)
                trainer.save(candidate,metadata=dict(metadata(),fault=failure,unfinished_rollout=dict(state)))
                fault_checkpoint=candidate
            except BaseException as save_error:
                failure['checkpoint_save_error']=str(save_error)
    finally:
        if env and env.scene:
            try:
                save(args.out/'final_state.json',native_state(env.scene))
                state['forbidden_calls'].extend(env.scene.forbidden_calls)
                if recorder and recorder.frames[-1]['physics_step']!=env.scene.steps:
                    recorder.capture()
            except BaseException as error:
                failure=failure or dict(type=type(error).__name__,message=str(error))
            env.close()
        if recorder:
            try:
                videos=recorder.encode()
            except BaseException as error:
                failure=failure or dict(type=type(error).__name__,message=str(error))
        changed=[name for name,digest in hashes.items() if not Path(name).is_file() or sha(name)!=digest]
        updates=trainer.updates if trainer else initial_updates
        delta=max(float((trainer.policy.state_dict()[k]-v).abs().max()) for k,v in initial_parameters.items()) if initial_parameters else None
        save(args.out/'report.json',dict(completed=failure is None and not changed and not state['forbidden_calls'],
            failure=failure,changed_inputs=changed,mode=args.mode,process_counters=state,
            cumulative=cumulative_counts(prior,state,updates,training=args.mode=='train'),initial_updates=initial_updates,
            performed_updates=updates-initial_updates,final_updates=updates,parameter_max_abs_change=delta,
            latest_regular_checkpoint=str(latest) if latest else None,fault_checkpoint=str(fault_checkpoint) if fault_checkpoint else None,
            videos=videos,elapsed_seconds=time.monotonic()-start,old_policy_loaded=False,
            loaded_project_python_modules={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
                if getattr(module,'__file__',None) and str(module.__file__).endswith('.py') and project in Path(module.__file__).resolve().parents}))
    if failure or changed or state['forbidden_calls']:
        raise RuntimeError(failure or dict(changed_inputs=changed,forbidden_calls=state['forbidden_calls']))


if __name__=='__main__':
    main()
