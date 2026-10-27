"""Explicit-budget parallel native training and measured resource comparison."""
import argparse
import gzip
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from dataclasses import asdict
from .recording import write,digest,project_source_paths
from .train import training_dependency
from .monitoring import Monitor,available_memory_bytes,stopped_reason,save_failure_checkpoint


def settings_document(value):
    from .ppo import PPOConfig
    settings=dict(num_envs=8,horizon=256,updates=1,device='cpu',seed=7,size='medium',
                  initial_std=math.exp(-3),stage='B',checkpoint_every=5,max_wall_seconds=None,
                  min_available_memory_gib=4.,heartbeat_seconds=10.,resource_interval_seconds=5.,worker_timeout_seconds=300.,
                  music=dict(reward_mode='legacy',goal_event_indices=None),
                  start_event_index=0,phrase_events=8,tempo_scale=1.,ppo=asdict(PPOConfig()))
    unknown=set(value)-set(settings)
    if unknown: raise ValueError('unknown run settings: '+str(sorted(unknown)))
    settings.update(value)
    for key in ('num_envs','horizon','updates','seed','checkpoint_every','start_event_index','phrase_events'):
        if isinstance(settings[key],bool) or not isinstance(settings[key],int): raise ValueError('integer '+key+' required')
    if settings['num_envs'] not in (1,2,4,8,16) or min(settings[k] for k in ('horizon','updates','checkpoint_every','phrase_events'))<1:
        raise ValueError('supported worker count and positive budgets required')
    if settings['horizon']*settings['num_envs']<2 or settings['start_event_index']<0:
        raise ValueError('at least two samples and nonnegative event index required')
    if settings['stage'] not in ('B','C','D') or settings['size'] not in ('small','medium','large'):
        raise ValueError('explicit supported stage/size required')
    if not isinstance(settings['device'],str) or settings['device'] not in ('cpu','cuda:0'):
        raise ValueError('device must be cpu or cuda:0')
    if not math.isfinite(settings['initial_std']) or not math.exp(-5)<=settings['initial_std']<=math.exp(2):
        raise ValueError('initial_std must fit the policy log_std clamp')
    if not math.isfinite(settings['tempo_scale']) or settings['tempo_scale']<=0:
        raise ValueError('positive tempo_scale required')
    wall=settings['max_wall_seconds']
    if wall is not None and (not math.isfinite(wall) or wall<=0): raise ValueError('positive optional wall budget required')
    for key in ('min_available_memory_gib','heartbeat_seconds','resource_interval_seconds','worker_timeout_seconds'):
        value=settings[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError('positive finite '+key+' required')
    music=settings['music']
    if not isinstance(music,dict) or set(music)-{'reward_mode','goal_event_indices'}:
        raise ValueError('explicit supported music settings required')
    music=dict(dict(reward_mode='legacy',goal_event_indices=None),**music)
    if music['reward_mode'] not in ('legacy','dense_v2'):
        raise ValueError('supported reward_mode required')
    indices=music['goal_event_indices']
    if indices is not None and (not isinstance(indices,list) or not indices or
        any(isinstance(i,bool) or not isinstance(i,int) or i<0 for i in indices) or len(set(indices))!=len(indices)):
        raise ValueError('unique nonnegative goal_event_indices required')
    if indices is not None and settings['stage']!='B':raise ValueError('goal sampling currently requires stage B')
    settings['music']=music
    settings['ppo']=asdict(PPOConfig(**settings['ppo']))
    return settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[1]
    parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--resume',type=Path)
    args=parser.parse_args()
    # All spawned imports see the same limits; this is not a claim that the OS
    # creates just one total thread per simulator process.
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    import isaacgym
    import numpy as np
    import random
    import torch
    from .parallel import Pool,Collector
    from .policy import Policy
    from .ppo import PPOTrainer,PPOConfig
    from . import prepared_reset_v1
    from stability_adapter_2.lower_body_release_v1.common import pin
    settings=settings_document(json.loads(args.settings.read_text()))
    # Constructing the trainer validates the remaining numerical PPO settings.
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32=False
    random.seed(settings['seed']);np.random.seed(settings['seed']);torch.manual_seed(settings['seed'])
    if settings['device'].startswith('cuda') and not torch.cuda.is_available(): raise RuntimeError('requested CUDA policy unavailable')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    config=(root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json').resolve()
    bundle=root/'data/song_bundles/05_BN2-131-B_solo'
    cfg=json.loads(config.read_text())
    sources={Path(__file__).resolve(),args.settings.resolve(),config,root/'tab2body/full/events.py'}
    sources.update((root/'stability_adapter_2').rglob('*.py'))
    sources.update(p for p in (root/'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    sources.update(p for p in bundle.rglob('*') if p.is_file())
    sources.update(prepared_reset_v1.prepared_input_paths())
    if args.resume: sources.add(args.resume.resolve())
    for value in cfg.values():
        if isinstance(value,str) and value.startswith('/') and Path(value).is_file(): sources.add(Path(value).resolve())
    sources.add(Path(json.loads(Path(cfg['candidate']).read_text())['support_candidate']).resolve())
    expected={}
    original=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_baseline_v14'
    for name in ('attempt.json','support_wrapper.json'):
        path=original/name;sources.add(path)
        for filename,value in json.loads(path.read_text())['input_sha256'].items():
            path=str(Path(filename).resolve())
            if path in expected and expected[path]!=value: raise RuntimeError('conflicting original SHA')
            expected[path]=value
    pins=pin(config,extra=sources)
    write(out/'inputs_before.json',pins);write(out/'settings.json',settings)
    # Check original model inputs before any child constructs a scene.
    model=[p for p in pins if Path(p).suffix.lower() in ('.xml','.obj','.stl','.ply','.dae')]+[str(config)]
    if any(expected.get(p)!=pins[p] for p in model): raise RuntimeError('original model/config parity failed')
    specs=[dict(config=str(config),bundle=str(bundle),out=str(out/('worker_%03d'%i)),stage=settings['stage'],
                start_event_index=settings['start_event_index'],phrase_events=settings['phrase_events'],
                tempo_scale=settings['tempo_scale'],seed=settings['seed'],headless=True,raw_samples=False,music=settings['music'])
           for i in range(settings['num_envs'])]
    def encode(value):
        if isinstance(value,np.ndarray):return value.tolist()
        if isinstance(value,np.generic):return value.item()
        raise TypeError(type(value).__name__)
    start=time.perf_counter();updates=[];failure=None;pool=None;trainer=None;stopped='updates_complete'
    recovery_checkpoint=None;partial_collection=None;collector=None;pool_failure_diagnostics=None
    monitor=Monitor(out,min_available_memory_gib=settings['min_available_memory_gib'],
                    heartbeat_seconds=settings['heartbeat_seconds'],resource_interval_seconds=settings['resource_interval_seconds'])
    timers=dict(startup_s=0.,reset_s=0.,step_s=0.,collection_s=0.,update_s=0.)
    resources=dict(min_available_memory_bytes=available_memory_bytes(),worker_rss_peak_sum_kib=0,parent_rss_peak_kib=0,
                   torch_cuda_allocated_peak_bytes=0,torch_cuda_reserved_peak_bytes=0)
    transition_file=gzip.open(out/'transitions.jsonl.gz','xt')
    class MeasuredPool(Pool):
        def reset(self,indices=None):
            begin=time.perf_counter()
            result=super().reset(indices)
            timers['reset_s']+=time.perf_counter()-begin
            return result

        def step(self,actions):
            begin=time.perf_counter();result=super().step(actions);timers['step_s']+=time.perf_counter()-begin
            observation,reward,terminated,truncated,infos=result
            resources['worker_rss_peak_sum_kib']=max(resources['worker_rss_peak_sum_kib'],sum(i['resource']['rss_peak_kib'] for i in infos))
            resources['parent_rss_peak_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            resources['min_available_memory_bytes']=min(resources['min_available_memory_bytes'],available_memory_bytes())
            transition_file.write(json.dumps(dict(reward=reward,terminated=terminated,truncated=truncated,infos=infos),default=encode,allow_nan=False)+'\n')
            return result
    try:
        monitor.start()
        monitor.set_phase('worker_startup')
        begin=time.perf_counter();pool=MeasuredPool(specs,timeout_s=settings['worker_timeout_seconds'],wait_callback=monitor.wait);timers['startup_s']=time.perf_counter()-begin
        monitor.set_phase('initial_preparation')
        observation,infos=pool.reset();write(out/'reset_initial.json',infos);write(out/'training_contract.json',pool.contract)
        monitor.set_phase('policy_initialization')
        policy=Policy(observation['state'].shape[-1],size=settings['size'],contract=pool.contract).to(settings['device'])
        with torch.no_grad():policy.log_std.fill_(math.log(settings['initial_std']))
        trainer=PPOTrainer(policy,PPOConfig(**settings['ppo']))
        if args.resume:trainer.load(args.resume.resolve())
        trainer.save(out/'initial.pt',metadata=dict(settings=settings,resume_scope='optimizer_RNG_new_native_episodes'))
        collector=Collector(policy,pool,device=settings['device']);collector.observation=observation
        for index in range(settings['updates']):
            if settings['max_wall_seconds'] is not None and time.perf_counter()-start>=settings['max_wall_seconds']:
                stopped='wall_budget';break
            monitor.set_phase('collecting',update_index=index,ticks=0,horizon=settings['horizon'])
            partial_collection=dict(update_index=index,complete=False,ticks=0,horizon=settings['horizon'])
            begin=time.perf_counter();buffer,completed=collector.collect(settings['horizon'],progress_callback=monitor.progress)
            partial_collection.update(complete=True,ticks=settings['horizon'])
            if settings['device'].startswith('cuda'):torch.cuda.synchronize()
            collection=time.perf_counter()-begin;timers['collection_s']+=collection
            if index==0:torch.save({k:v.cpu() for k,v in buffer.items()},out/'rollout_first.pt')
            if settings['device'].startswith('cuda'):torch.cuda.synchronize()
            monitor.set_phase('optimizing')
            begin=time.perf_counter();metrics=trainer.update(buffer,completed)
            if settings['device'].startswith('cuda'):torch.cuda.synchronize()
            elapsed=time.perf_counter()-begin;timers['update_s']+=elapsed
            if torch.cuda.is_initialized():
                resources['torch_cuda_allocated_peak_bytes']=torch.cuda.max_memory_allocated()
                resources['torch_cuda_reserved_peak_bytes']=torch.cuda.max_memory_reserved()
            metrics.update(update_index=index,collection_s=collection,update_s=elapsed,
                           transitions=settings['horizon']*settings['num_envs'],completed_episodes=completed)
            updates.append(metrics);write(out/('update_%06d.json'%index),metrics)
            if (index+1)%settings['checkpoint_every']==0 or index+1==settings['updates']:
                trainer.save(out/('checkpoint_%06d.pt'%index),metadata=dict(settings=settings,update_in_run=index+1))
            print(json.dumps(metrics),flush=True)
            monitor.set_phase('update_complete')
        monitor.set_phase('saving_final')
        trainer.save(out/'final.pt',metadata=dict(settings=settings,updates_in_run=len(updates),stopped=stopped))
    except BaseException as error:
        stopped=stopped_reason(error)
        pool_failure_diagnostics=getattr(error,'pool_close_diagnostics',None)
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if partial_collection is not None and not partial_collection['complete']:
            partial_collection['ticks']=monitor.context['ticks']
            partial_collection['discarded_transitions']=monitor.context['ticks']*settings['num_envs']
        recovery_checkpoint=save_failure_checkpoint(trainer,out,dict(settings=settings,updates_in_run=len(updates),
            stopped=stopped,failed_phase=monitor.context['phase'],partial_collection=partial_collection,
            recovery_scope='valid_PPO_optimizer_only_new_native_episodes_partial_rollout_discarded'))
        try:monitor.event('failure',failure=failure,recovery_checkpoint=recovery_checkpoint)
        except BaseException as log_error:
            failure['logging_error']=dict(type=type(log_error).__name__,message=str(log_error))
        print('[training] stopped=%s recovery=%s'%(stopped,recovery_checkpoint),flush=True)
        raise
    finally:
        cleanup_errors=[]
        for label,cleanup in (('transitions',transition_file.close),('pool',pool.close if pool is not None else lambda:None)):
            try:cleanup()
            except BaseException as error:cleanup_errors.append(dict(component=label,type=type(error).__name__,message=str(error)))
        if cleanup_errors and failure is None:stopped='error'
        audits=[];missing_audits=[];audit_read_errors=[]
        for spec in specs:
            path=Path(spec['out'])/'worker_final_audit.json'
            if path.exists():
                try:audits.append(json.loads(path.read_text()))
                except (OSError,ValueError) as error:
                    audit_read_errors.append(dict(path=str(path),type=type(error).__name__,message=str(error)))
            else:missing_audits.append(str(path))
        imported=project_source_paths(list(sys.modules.items()))
        for audit in audits:imported.update(audit.get('actual_imported_sources',[]))
        missing=sorted(imported-set(pins))
        parity=sorted(p for p in imported if not training_dependency(p) and expected.get(p)!=pins.get(p))
        changed=[p for p,h in pins.items() if digest(p)!=h]
        guards=[a for a in audits if a.get('forbidden_calls')]
        worker_failures=[a for a in audits if a.get('failure')]
        physical_flags_errors=[a['worker_id'] for a in audits if
            a.get('human_root_fixed') is not True or a.get('guitar_root_fixed') is not False or
            a.get('guitar_gravity_disabled') is not False or
            (a.get('headless_description') or {}).get('camera_count')!=0]
        checks=not(changed or missing or parity or missing_audits or guards or worker_failures or physical_flags_errors or cleanup_errors or audit_read_errors)
        if failure is None and not checks:stopped='error'
        try:monitor.close(stopped)
        except BaseException as error:
            cleanup_errors.append(dict(component='monitor',type=type(error).__name__,message=str(error)))
            checks=False
            if failure is None:stopped='error'
        if monitor.minimum_available is not None:
            resources['min_available_memory_bytes']=min(resources['min_available_memory_bytes'],monitor.minimum_available)
        total=sum(u['transitions'] for u in updates)
        complete=failure is None and checks and (len(updates)==settings['updates'] or stopped=='wall_budget')
        report=dict(completed=complete,failure=failure,stopped=stopped,recovery_checkpoint=recovery_checkpoint,
                    partial_collection=partial_collection,resource_monitor=monitor.status,cleanup_errors=cleanup_errors,
                    pool_close_diagnostics=getattr(pool,'close_diagnostics',None) if pool is not None else pool_failure_diagnostics,
                    settings=settings,updates=updates,
                    transitions=total,timers=timers,wall_s=time.perf_counter()-start,resources=resources,
                    collection_transitions_per_s=total/timers['collection_s'] if timers['collection_s'] else None,
                    actual_imported_sources=sorted(imported),missing_import_pins=missing,original_source_parity_errors=parity,
                    changed_inputs=changed,missing_worker_audits=missing_audits,worker_audit_read_errors=audit_read_errors,guard_violations=guards,
                    worker_failures=worker_failures,physical_flags_errors=physical_flags_errors,
                    worker_audits=audits,scope='CPU independent simulators, one batched policy; not GPU PhysX vectorization or learned performance certification')
        write(out/'report.json',report)
        if failure is None and not complete:raise RuntimeError('parallel run source/worker checks failed; see report')


if __name__=='__main__':main()
