"""Explicit deterministic native probes and strict checkpoint evaluation; no training."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import copy
import json
import math
import random
import traceback
from guitar_learning.training.recording import write, digest, project_source_paths
from guitar_learning.training.recording import bridge_dependency as training_dependency
from guitar_learning.core.dependency_inputs import parity_errors

MODES = ('zero','right','left_arm','fingers','all','policy')


def probe_action(mode, step):
    import numpy as np
    if mode not in MODES[:-1] or isinstance(step,bool) or not isinstance(step,int) or step < 0:
        raise ValueError('known probe mode and nonnegative integer control step required')
    action=np.zeros(39,dtype=np.float32)
    roles={'zero':slice(0,0),'left_arm':slice(0,12),'fingers':slice(12,33),
           'right':slice(33,39),'all':slice(0,39)}
    action[roles[mode]]=math.sin(2*math.pi*step/120.)
    return action


def evaluate_episode(env, action_fn, seconds, *, on_reset=None, on_step=None):
    """Return preserved final input and budget termination without changing task."""
    import numpy as np
    if not np.isfinite(seconds) or seconds <= 0 or abs(seconds*60-round(seconds*60)) > 1e-8:
        raise ValueError('positive seconds aligned to 60Hz required')
    observation,info=env.reset()
    contract=copy.deepcopy(env.contract)
    if on_reset: on_reset(observation,info)
    summary=dict(reward=0.,cost=0.,control_steps=0,terminated=False,truncated=False,
                 reason=None,failures=[],contact_flags_last=None,target_distance_last_m={},
                 fret_candidates_last={},music=None)
    for step in range(round(seconds*60)):
        action=action_fn(observation,step)
        observation,reward,terminated,truncated,info=env.step(action)
        if env.contract != contract:
            raise ValueError('environment contract changed within episode')
        budget=step+1==round(seconds*60) and not (terminated or truncated)
        truncated=bool(truncated or budget)
        reason='validation_budget' if budget else info['termination_reason']
        summary['reward']+=float(reward)
        summary['cost']+=float(info['cost'])
        summary.update(control_steps=step+1,terminated=bool(terminated),truncated=truncated,reason=reason,
                       contact_flags_last=env.last_safety['flags'].tolist(),music=info['music'])
        summary['failures'].extend(x for x in info['failure_reasons'] if x not in summary['failures'])
        summary['target_distance_last_m']={key:float(np.linalg.norm(row['delta'])) for key,row in env.last_measured['geometry'].items()}
        summary['fret_candidates_last']={key:bool(row['candidate']) for key,row in env.last_measured['targets'].items()}
        if on_step: on_step(step,dict(action=action,observation=observation,reward=reward,
                                     terminated=bool(terminated),truncated=truncated,
                                     termination_reason=reason,info=info))
        if terminated or truncated: break
    return summary



def load_policy(checkpoint_path, observation, contract, device='cpu'):
    import torch
    from guitar_learning.training.policy import Policy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    payload=torch.load(checkpoint_path,map_location='cpu',weights_only=False)
    identity=payload['identity']
    if identity['schema']!=PPOTrainer.schema:
        raise ValueError('own checkpoint schema required')
    policy=Policy(len(observation['state']),size=identity['architecture']['size'],contract=contract).to(device)
    PPOTrainer(policy,PPOConfig(**identity['config'])).load(checkpoint_path)
    policy.eval()
    return policy


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[2]
    parser.add_argument('--config',type=Path,default=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json')
    parser.add_argument('--bundle',type=Path,default=root/'data/song_bundles/05_BN2-131-B_solo')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--stage',choices=('B','C','D'),required=True)
    parser.add_argument('--seconds',type=float,default=3.)
    parser.add_argument('--episodes',type=int,default=1)
    parser.add_argument('--mode',choices=MODES,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--start-event-index',type=int,default=0)
    parser.add_argument('--phrase-events',type=int,default=8)
    parser.add_argument('--tempo-scale',type=float,default=1.)
    parser.add_argument('--device',default='cpu')
    parser.add_argument('--seed',type=int,default=7)
    args=parser.parse_args()
    if args.episodes < 1 or not math.isfinite(args.seconds) or args.seconds<=0 or abs(args.seconds*60-round(args.seconds*60))>1e-8:
        parser.error('episodes>=1 and positive seconds aligned to 60Hz required')
    if (args.mode=='policy') != bool(args.checkpoint):
        parser.error('checkpoint is required exactly for policy mode')
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.music_task import ScoreTask
    from guitar_learning.core.training_environment import TrainingEnvironment
    from guitar_learning.training.policy import Policy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.native.paths import resolve_input_path, rebase_paths
    from guitar_learning.native.front_facing_ready_v1.runtime_v15 import Scene
    from guitar_learning.native.front_facing_ready_v1.runtime_v12 import Controller
    from guitar_learning.native.native_contacts import body_names,read_contacts
    from guitar_learning.native.lower_body_release_v1.common import pin
    from guitar_learning.native.gym_trial_recording import GymTrialRecording
    torch.set_num_threads(1)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    task=ScoreTask.from_bundle(args.bundle,stage=args.stage,start_event_index=args.start_event_index,
                             phrase_events=args.phrase_events,tempo_scale=args.tempo_scale)
    checkpoint=None
    if args.checkpoint:
        checkpoint=torch.load(args.checkpoint.resolve(),map_location='cpu',weights_only=False)
        identity=checkpoint['identity']
        if identity['schema']!=PPOTrainer.schema:
            raise ValueError('own checkpoint schema required')
    config,out=resolve_input_path(args.config),args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    cfg=rebase_paths(json.loads(config.read_text()))
    sources={config,Path(__file__).resolve(),root/'guitar_learning/score/canonical.py'}
    sources.update((root/'guitar_learning/native').rglob('*.py'))
    sources.update(p for p in (root/'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    sources.update(p for p in args.bundle.resolve().rglob('*') if p.is_file())
    sources.update(prepared_reset_v1.prepared_input_paths())
    if args.checkpoint: sources.add(args.checkpoint.resolve())
    for value in cfg.values():
        if isinstance(value,str) and value.startswith('/') and Path(value).is_file(): sources.add(Path(value).resolve())
    sources.add(Path(rebase_paths(json.loads(Path(cfg['candidate']).read_text()))['support_candidate']).resolve())
    expected={}
    original_run=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_baseline_v14'
    for name in ('attempt.json','support_wrapper.json'):
        path=original_run/name
        sources.add(path)
        for filename,value in json.loads(path.read_text())['input_sha256'].items():
            canonical=str(Path(filename).resolve())
            if canonical in expected and expected[canonical]!=value: raise RuntimeError('conflicting source SHA')
            expected[canonical]=value
    pins=pin(config,extra=sources)
    write(out/'inputs_before.json',pins)
    original={p for p in project_source_paths(list(sys.modules.items())) if not training_dependency(p)}
    original.update(p for p in pins if Path(p).suffix.lower() in ('.xml','.obj','.stl','.ply','.dae'))
    original.add(str(config))
    if parity_errors(original, expected): raise RuntimeError('original source/model parity failed')
    write(out/'arguments.json',{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()})
    recorder=[]
    media=[]
    encoding_errors=[]
    summaries=[]
    failure=None
    policy=None
    full_contract=None
    episode_folder=None
    last_capture=[None]
    initial_written=[False]
    def capture(scene,phase):
        if not initial_written[0]:
            write(episode_folder/'initial_values.json',dict(native_state=scene.native(),joint_names=scene.names,
                  human_body_names=scene.human_bodies,guitar_body_names=scene.guitar_bodies,
                  target105_rad=scene.target,human_properties=scene.human_properties,guitar_properties=scene.guitar_properties,
                  loaded_assets=scene.loaded_assets,human_root_fixed=scene.human_root_fixed,
                  guitar_root_fixed=scene.guitar_root_fixed,guitar_gravity_disabled=scene.guitar_gravity_disabled))
            initial_written[0]=True
        if args.mode!='policy': return
        if not recorder:
            recorder.append(GymTrialRecording(scene,episode_folder/'media'))
            recorder[0].fps,recorder[0].interval=30,8
        if scene.steps%8==0:
            recorder[0].capture()
            last_capture[0]=scene.steps
    env_options={}
    if checkpoint:
        saved=checkpoint['identity']['architecture']['contract']
        env_options=dict(action_half_range_rad=saved['action']['offset_half_range_rad'],
                         smoothing_alpha=saved['action']['smoothing_alpha'],
                         preparation_seconds=saved['termination']['preparation_seconds'],
                         time_limit_s=saved['termination']['time_limit_s'])
    env=TrainingEnvironment(config,out/'environment',task=task,sample_callback=capture,**env_options)
    try:
        for episode in range(args.episodes):
            episode_folder=out/('episode_%04d'%episode)
            episode_folder.mkdir()
            recorder.clear()
            last_capture[0]=None
            initial_written[0]=False
            def reset(observation,info):
                nonlocal policy,full_contract
                if full_contract is None:
                    full_contract=copy.deepcopy(env.contract)
                    write(out/'training_contract.json',full_contract)
                elif env.contract!=full_contract:
                    raise ValueError('episode contract changed')
                if checkpoint and policy is None:
                    policy=load_policy(args.checkpoint.resolve(),observation,env.contract,args.device)
                write(episode_folder/'prepared.json',dict(observation=observation,info=info,sample=env.last_sample,
                                                          music=env.last_measured,stability=env.last_safety))
            def action(observation,step):
                if policy is None: return probe_action(args.mode,step)
                inputs=[torch.as_tensor(observation[k],device=args.device).unsqueeze(0) for k in ('state','events','mask','priority_events','priority_mask')]
                with torch.no_grad(): return policy.act(*inputs,deterministic=True)['action'][0].cpu().numpy()
            def transition(step,row):
                write(episode_folder/('transition_%06d.json.gz'%step),row,compressed=True)
            try:
                summary=evaluate_episode(env,action,args.seconds,on_reset=reset,on_step=transition)
                summary.update(episode=episode,mode=args.mode,scope='Measured native interface probe; not learned music success, sound or V3 pose certification')
                summaries.append(summary)
                write(episode_folder/'summary.json',summary)
            finally:
                if recorder and env.control.session is not None and last_capture[0]!=env.control.session.scene.steps:
                    try: recorder[0].capture()
                    except BaseException as error: encoding_errors.append(dict(episode=episode,stage='final_capture',message=str(error)))
                env.close()
                if recorder:
                    try: media.append(recorder[0].encode())
                    except BaseException as error: encoding_errors.append(dict(episode=episode,message=str(error)))
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        raise
    finally:
        env.close()
        changed=[p for p,h in pins.items() if digest(p)!=h]
        imported=project_source_paths(list(sys.modules.items()))
        missing=sorted(imported-set(pins))
        parity=parity_errors((p for p in imported if not training_dependency(p)), expected)
        write(out/'inputs_after.json',{p:digest(p) for p in pins})
        completed=failure is None and len(summaries)==args.episodes and not(changed or missing or parity)
        write(out/'report.json',dict(completed=completed,physics_failure=failure,episodes=summaries,
              encoding_errors=encoding_errors,videos=media,media_complete=not encoding_errors,
              inputs_unchanged=not changed,changed_inputs=changed,actual_imported_sources=sorted(imported),
              missing_import_pins=missing,original_source_parity_errors=parity,new_training_updates=0,
              budget_scope='seconds limits evaluation only; checkpoint environment contract is unchanged',
              scope='Deterministic probes/evaluation only; no PPO update, acoustic or long-run performance certification'))
        if failure is None and not completed: raise RuntimeError('validation source/output checks failed')


if __name__=='__main__':
    main()
