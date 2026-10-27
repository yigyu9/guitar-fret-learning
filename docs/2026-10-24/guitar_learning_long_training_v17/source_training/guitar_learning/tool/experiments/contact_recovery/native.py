"""Versioned native probe with explicit evaluation RNG and recovery sidecars.

Derived from transition/probe.py; the archived origin SHA is recorded in
archive/20261019_before_contact_recovery/manifest.json. Physical guards and
complete raw observations/actions/240Hz measurements remain unchanged.
"""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import random
import time


def run(settings,args,protocol):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.imitation.imitation_io import CONFIG, BUNDLE, pin_inputs_with_evidence, verify_inputs
    from guitar_learning.training.recording import write, digest, project_source_paths
    from guitar_learning.training.parallel import FIELDS
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.training.monitoring import available_memory_bytes, LowMemoryError
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.tool.experiments.transition.environment import build_environment
    from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy as TransitionPolicy
    from guitar_learning.tool.experiments.transition.transfer import initialize_actor
    from guitar_learning.tool.experiments.transition.train import initialization_evidence
    from guitar_learning.tool.experiments.transition.solver import solve, input_paths
    from guitar_learning.tool.experiments.contact_recovery.controller import Controller
    from guitar_learning.tool.experiments.transition.contact_teacher import input_paths as contact_inputs
    from guitar_learning.tool.experiments.contact_recovery.evaluation import evaluation_case, apply_evaluation_seed, initial_state_snapshot, compare_initial_states
    from guitar_learning.song.task import make_task as source_task
    import sys

    if args.controller not in ('zero','solver','policy') or type(args.episodes) is not int or not 1<=args.episodes<=20:
        raise ValueError('zero/solver/policy and1..20 episodes required')
    checkpoint=getattr(args,'checkpoint',None)
    if checkpoint is not None and args.controller!='policy':raise ValueError('strict checkpoint belongs to policy evaluation only')
    evidence=initialization_evidence(settings,require_gate=False)
    checkpoint=Path(checkpoint).resolve() if checkpoint is not None else Path(settings['initialization']['checkpoint'])
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    pins=pin_inputs_with_evidence([args.settings.resolve(),args.protocol.resolve(),checkpoint,*input_paths(),*contact_inputs()], evidence['source_pins'])
    write(out/'inputs_before.json',pins);write(out/'settings.json',settings)
    env=None;scene=None;primary=None;cleanup=None;flags=False;forbidden=[];started=time.monotonic();cases=[]
    def guard(start=False):
        if available_memory_bytes()<(8. if start else 6.)*1024**3:raise LowMemoryError('transition native memory guard')
        if time.monotonic()-started>1800.:raise TimeoutError('transition native1800s guard')
    write(out/'protocol.json',protocol)
    initial_states=[]
    def encode(value):
        if isinstance(value,np.ndarray):return value.tolist()
        if isinstance(value,np.generic):return value.item()
        raise TypeError(type(value).__name__)
    try:
        guard(True);random.seed(settings['seed']);np.random.seed(settings['seed']);torch.manual_seed(settings['seed']);torch.set_num_threads(1)
        env=build_environment(CONFIG,out/'environment',bundle=BUNDLE,transition=settings['transition'],session_factory=PersistentHeadlessPreparedSession)
        for index in range(args.episodes):
            guard(True);case=out/('case_%03d'%index);case.mkdir();observation,reset=env.reset()
            scene=env.control.session.scene
            write(case/'reset.json',reset);write(case/'contract.json',env.contract);write(case/'settings.json',settings);write(case/'inputs_before.json',pins)
            case_spec=protocol['cases'][args.case_indices[index]]
            seed_case=evaluation_case(case_spec['seed'], case_index=index,
                evaluation_mode=protocol['evaluation_mode'],process_mode=protocol['process_mode'])
            builder=env.builder
            write(case/'context.json',dict(names=builder.names,human_names=builder.human_names,guitar_names=builder.guitar_names,
                human_com=builder.human_com,guitar_com=builder.guitar_com,reference105=builder.reference))
            write(case/'initial.json',dict(sample=env.last_sample,measured=env.last_measured,safety=env.last_safety,target105=scene.target))
            model=None;controller=None;initialization=None
            if args.controller=='policy':
                model=TransitionPolicy(500,size=settings['size'],contract=env.contract).to(settings['device'])
                if getattr(args,'checkpoint',None) is not None:
                    trainer=PPOTrainer(model,PPOConfig(**settings['ppo']));trainer.load(checkpoint)
                    initialization=dict(mode='strict_PPO',optimizer_updates=trainer.updates)
                    seed_record=apply_evaluation_seed(seed_case,checkpoint_loaded=True,checkpoint_sha256=digest(checkpoint))
                    seed_record['protocol_case_index']=args.case_indices[index]
                    write(case/'evaluation_seed.json',seed_record)
                else:initialization=initialize_actor(model,settings)
                model.eval();write(case/'initialization.json',initialization)
            elif args.controller=='solver':
                plan=solve(env.last_sample,env.control.contract,env.task.targets,
                    joint_names=scene.names,human_names=scene.human_bodies,
                    seed=case_spec['seed'],max_nfev=getattr(args,'max_nfev',80),starts=getattr(args,'starts',2),
                    context_targets=source_task(BUNDLE).targets[:2])
                if any(str(Path(path).resolve()) not in pins for path in plan.get('input_paths',[])):
                    raise RuntimeError('solver consumed an unpinned asset')
                write(case/'plan.json',plan);controller=Controller(plan,env.task,
                    perturbation=case_spec['perturbation'],transition=settings['transition'])
            snapshot=initial_state_snapshot(env)
            initial_states.append(snapshot)
            write(case/'initial_state.json',snapshot)
            write(case/'case_spec.json',dict(case_spec,protocol_case_index=args.case_indices[index],
                process_mode=protocol['process_mode'],evaluation_mode=protocol['evaluation_mode']))
            arrays={k:[] for k in (*FIELDS,'action','task_time_s')};ticks=round(env.task.duration_s*60);episode=None
            record=dict(folder=case,steps=0,episode=None,failure=None,initialization=initialization,arrays=arrays,
                controller=controller,perturbation=case_spec['perturbation'])
            cases.append(record)
            with gzip.open(case/'trace.jsonl.gz','xt',compresslevel=1) as stream:
                for tick in range(ticks):
                    if tick%60==0:guard()
                    before={k:np.array(observation[k],copy=True) for k in FIELDS}
                    if model is not None:
                        inputs=[torch.as_tensor(before[k],device=settings['device']).unsqueeze(0) for k in FIELDS]
                        with torch.no_grad():action=model.act(*inputs,deterministic=protocol['evaluation_mode']=='deterministic')['action'][0].cpu().numpy()
                    elif controller is not None:action=controller.action(tick/60.,observation,env)
                    else:action=np.zeros(39)
                    action=np.asarray(action,dtype=np.float32)
                    if action.shape!=(39,) or not np.isfinite(action).all() or np.any(np.abs(action)>1):raise ValueError('bounded39 native action required')
                    for key in FIELDS:arrays[key].append(before[key])
                    arrays['action'].append(action.copy());arrays['task_time_s'].append(tick/60.)
                    observation,reward,terminated,truncated,info=env.step(action);record['steps']+=1
                    if controller is not None:
                        for sample in info['physics_measurements']:
                            controller.observe_physics(sample['music'],sample['stability'])
                    stream.write(json.dumps(dict(tick=tick,task_time_before_s=tick/60.,before_observation=before,
                        action=action,reward=reward,info=info,safety_after=env.last_safety,target105=scene.target,
                        teacher_diagnostic=controller.diagnostic if controller else None,
                        teacher_action39_float32=np.asarray(controller.diagnostic['teacher_action39'],dtype=np.float32).tolist() if controller else None),default=encode,allow_nan=False)+'\n')
                    if (tick+1)%60==0:print('[transition %s] case=%d tick=%d/%d hold=%s success=%s'%(args.controller,index,tick+1,ticks,
                        {k:round(v['clean_hold_fraction'],3) for k,v in info['transition']['per_target'].items()},info['transition']['successful']),flush=True)
                    if terminated or truncated:
                        episode=copy.deepcopy(info['episode']);record['episode']=episode;break
            np.savez_compressed(case/'demonstration.npz',**{k:np.asarray(v) for k,v in arrays.items()})
            write(case/'partial_result.json',dict(steps=record['steps'],episode=episode,publication='pending shared cleanup and input audit'))
    except BaseException as error:
        primary=error
        if cases:cases[-1]['failure']=dict(type=type(error).__name__,message=str(error))
    finally:
        if env is not None:
            try:
                if scene is not None:
                    forbidden=copy.deepcopy(scene.forbidden_calls)
                    flags=bool(scene.human_root_fixed and not scene.guitar_root_fixed and not scene.guitar_gravity_disabled
                        and np.array_equal(scene.pd_properties,env.control.original_properties))
            except BaseException as error:
                cleanup=dict(type=type(error).__name__,message=str(error))
                if primary is None:primary=error
            try:env.close()
            except BaseException as error:
                cleanup=dict(type=type(error).__name__,message=str(error))
                if primary is None:primary=error
    for record in cases:
        path=record['folder']/'demonstration.npz'
        if not path.exists():
            try:np.savez_compressed(path,**{k:np.asarray(v) for k,v in record['arrays'].items()})
            except BaseException as error:
                if primary is None:primary=error
    unchanged=False
    try:unchanged=verify_inputs(pins)
    except BaseException as error:
        if primary is None:primary=error
    missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    manifests={};results=[]
    for record in cases:
        case=record['folder'];episode=record['episode'];complete=bool(episode and episode['valid'] is True and episode['reason']=='timeline_complete'
            and record['steps']==round(episode['task_time_s']*60))
        controller=record['controller']
        if controller is not None and controller.ledger is not None:
            write(case/'recovery.json',controller.ledger.summary(completed=complete,
                musical_success=episode['transition']['successful'] if episode else None))
        result=dict(schema='guitar_learning.contact_recovery_capture.v1',action_source=args.controller,
            teacher_intervention=args.controller!='policy',mode=args.mode,perturbation=record['perturbation'],initialization_checkpoint_sha256=digest(checkpoint),
            source_checkpoint=str(checkpoint),parent_result_path=str(out/'result.json'),steps=record['steps'],
            completed=complete,episode=episode,success=bool(complete and episode['transition']['successful'] and flags
                and unchanged and not forbidden and primary is None and not cleanup and not missing),
            source_unchanged=unchanged,physical_flags_ok=flags,forbidden_calls=forbidden,
            missing_import_pins=missing,failure=record['failure'],cleanup_error=cleanup,
            scope='bounded native control; teacher replay is feasibility evidence, not learned policy success')
        artifacts={'trace_sha256':'trace.jsonl.gz','demonstration_sha256':'demonstration.npz','contract_sha256':'contract.json',
            'settings_sha256':'settings.json','inputs_before_sha256':'inputs_before.json','context_sha256':'context.json','initial_sha256':'initial.json',
            'initial_state_sha256':'initial_state.json','case_spec_sha256':'case_spec.json'}
        for key,name in artifacts.items():result[key]=digest(case/name) if (case/name).is_file() else None
        for key,name in [('plan_sha256','plan.json'),('recovery_sha256','recovery.json'),('evaluation_seed_sha256','evaluation_seed.json')]:
            result[key]=digest(case/name) if (case/name).is_file() else None
        write(case/'result.json',result);manifests[str(case)]=digest(case/'result.json');results.append(result)
    result=dict(schema='guitar_learning.contact_recovery_probe.v1',completed=bool(primary is None and len(cases)==args.episodes
        and all(x['completed'] for x in results) and flags and unchanged and not forbidden and not missing and cleanup is None),
        source_unchanged=unchanged,physical_flags_ok=flags,forbidden_calls=forbidden,missing_import_pins=missing,
        failure=dict(type=type(primary).__name__,message=str(primary)) if primary else None,cleanup_error=cleanup,
        case_manifests=manifests,successful_cases=[str(record['folder']) for record,res in zip(cases,results) if res['success']],
        elapsed_wall_s=time.monotonic()-started,scope='native reachability/transition or unassisted policy evaluation, no pressure/audio certification')
    comparisons=[compare_initial_states(initial_states[0],state) for state in initial_states]
    write(out/'reset_comparisons.json',dict(comparisons=comparisons,
        scope='observable initial states; not hidden solver cache restoration or a physical determinism guarantee'))
    result.update(mode=args.mode,process_mode=protocol['process_mode'],
        evaluation_mode=protocol['evaluation_mode'],reset_comparisons_sha256=digest(out/'reset_comparisons.json'))
    write(out/'result.json',result)
    if primary is not None:raise primary
    return result
