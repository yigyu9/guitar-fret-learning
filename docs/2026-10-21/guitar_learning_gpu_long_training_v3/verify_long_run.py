"""Strict CPU verification of the completed 2000-update v3 run, never a live gate."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path

UPDATES, HORIZON, ENVS = 2000, 32, 1024
TRANSITIONS = 65_536_000
ROOT = Path(__file__).resolve().parents[3]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def lines(path):
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            require(line.endswith('\n'), '%s:%d incomplete final line' % (path,number))
            yield json.loads(line)


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            result.update(chunk)
    return result.hexdigest()


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def finite(value, location='metrics'):
    if isinstance(value,float):
        require(math.isfinite(value),'nonfinite '+location)
    elif isinstance(value,dict):
        for key,item in value.items():
            if key=='nonfinite_count':
                require(item==0,'reported nonfinite samples at '+location)
            if key=='nonfinite_steps':
                require(not item,'reported nonfinite optimizer steps at '+location)
            finite(item,location+'.'+str(key))
    elif isinstance(value,(list,tuple)):
        for item in value:
            finite(item,location)


def journal(value, transitions, rows, closed=False):
    for name in ('sampled','logged','durable','committed'):
        require(value[name]==transitions,'journal '+name)
    for name in ('sampled_rows','logged_rows','durable_rows'):
        require(value[name]==rows,'journal '+name)
    for name in ('discarded','pending_rows','pending_transitions','unresolved_sampled','logged_not_committed'):
        require(value[name]==0,'journal '+name+' must be zero')
    require(value['failed'] is False and value['closed'] is closed,'journal lifecycle')


def episode(value,duration):
    finite(value,'episode')
    require(value['valid'] is True and value['reason'] in ('terminal_failure','timeline_complete'),'invalid episode')
    require(0<=value['env_id']<ENVS and value['env_id']==value['worker_id'],'episode environment ID')
    require(value['steps']>0 and math.isclose(value['steps']/60.,value['task_time_s'],abs_tol=1e-8),'episode clock')
    require(value['song']['target_count']==67 and value['song']['denominator']==67,'song note denominator')
    failed=value['reason']=='terminal_failure'
    require(bool(value['failure_reasons']) is failed,'episode failure reasons')
    require(value['song']['completed'] is (not failed),'episode completed flag')
    if not failed:
        require(value['steps']==1969 and value['left_curriculum']['full_safe'] is True,'whole-song endpoint')
    component=value['cost_components']
    expected=5.*max(duration-value['task_time_s'],0.) if failed else 0.
    require(component['failure_rate_cost_per_s']==5.,'failure cost rate')
    require(math.isclose(component['remaining_song_failure'],expected,rel_tol=2e-6,abs_tol=1e-4),'failure extra cost')
    require(math.isclose(sum(component[k] for k in ('remaining_song_failure','original_physics_and_terminal')),
                         value['cost'],rel_tol=2e-6,abs_tol=1e-4),'cost component sum')


def verify(run,phase):
    require((run/'report.json').is_file(),'Final report missing: training is incomplete; verification refused')
    report=read(run/'report.json')
    require(report.get('completed') is True,'Final report.completed is not true: training is incomplete or failed')
    require(report['failure'] is None and report['stopped']=='updates_complete','run did not finish all updates normally')
    require(not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'],'run integrity/lifecycle errors')
    settings=read(run/'settings.json')
    require(settings==report['settings'],'settings/report mismatch')
    require((settings['updates'],settings['horizon'],settings['num_envs'],settings['size'])==(UPDATES,HORIZON,ENVS,'large'),'expected fresh large1024 H32 x2000')
    require(report['transitions']==TRANSITIONS==UPDATES*HORIZON*ENVS and report['optimizer_updates']==UPDATES,'committed transitions or optimizer updates')
    journal(report['journal'],TRANSITIONS,UPDATES*HORIZON,closed=True)
    require(report['journal']['compressed_bytes']==(run/'transitions.jsonl.gz').stat().st_size,'raw gzip byte count')
    require(len(report['updates'])==UPDATES,'report update count')
    scene=read(run/'gpu_scene_final.json')
    require(scene==report['gpu_scene'] and report['lifecycle_verified'] is True,'scene lifecycle/report mismatch')
    require(scene['closed'] is True and scene['physx_use_gpu'] is True and scene['use_gpu_pipeline'] is True,'GPU physics/pipeline/close flags')
    require(scene['simulator_count']==1 and scene['environment_count']==ENVS and scene['num_envs']==ENVS,'native scene batch')
    require(scene['physics_steps']==UPDATES*HORIZON*4 and all(v=='cuda:0' for v in scene['tensor_devices'].values()),'native physics steps/devices')
    require(scene['environment_aggregate']['schema']=='guitar_learning.gpu_env_aggregate.v1','aggregate contract')
    require(scene['guitar_representation']['collision_shapes']==89,'guitar representation')
    pins=read(run/'inputs_before.json')
    require(len(pins)==568,'expected568 input pins')
    for name,expected in pins.items():
        require(digest(Path(name))==expected,'input SHA changed: '+name)
    manifest=read(phase/'training_source_manifest.json')
    source=manifest['source']
    require(manifest['active_python_count']==len(source)==423,'expected423 frozen Python sources')
    active={str(p.resolve()) for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    require(active==set(source),'active source file set changed')
    for name,expected in source.items():
        require(pins.get(name)==expected and digest(Path(name))==expected,'frozen source pin changed: '+name)
        require(digest(phase/'source_training'/Path(name).relative_to(ROOT))==expected,'source snapshot changed: '+name)
    require(len(list(run.glob('update_*.json')))==UPDATES,'expected exactly2000 update files')
    expected_rows=[]
    episode_counts=Counter()
    duration=settings['song_training']['episode_duration_s']
    for index in range(UPDATES):
        row=read(run/('update_%06d.json'%index))
        finite(row)
        require(row['update_index']==index and row['optimizer_updates']==index+1 and row['transitions']==HORIZON*ENVS,'update sequence')
        require(row['physics_steps']==(index+1)*HORIZON*4,'update physics clock')
        journal(row['journal'],(index+1)*HORIZON*ENVS,(index+1)*HORIZON)
        for key in ('update_index','optimizer_updates','transitions','collection_s','update_s'):
            require(report['updates'][index][key]==row[key],'report/update summary '+key)
        ep_hash=hashlib.sha256()
        for value in row['completed_episodes']:
            episode(value,duration)
            ep_hash.update(encoded(value)+b'\n')
            episode_counts['all']+=1
            episode_counts['physical_failure' if value['reason']=='terminal_failure' else 'timeline_complete']+=1
            episode_counts['stage_success']+=bool(value['song']['stage_success'])
        expected_rows.append(dict(hash=hashlib.sha256(encoded(row)).hexdigest(),episodes=ep_hash.hexdigest(),
            count=len(row['completed_episodes']),reward=row['mean_reward'],cost=row['mean_cost']))
    metric_count=0
    for index,row in enumerate(lines(run/'learning_metrics.jsonl')):
        require(index<UPDATES and row['update_index']==index,'metrics update order/count')
        require(hashlib.sha256(encoded(row)).hexdigest()==expected_rows[index]['hash'],'metrics/update file mismatch')
        metric_count+=1
    require(metric_count==UPDATES,'metrics missing updates')
    episode_hashes=[hashlib.sha256() for _ in range(UPDATES)]
    logged_counts=Counter()
    last_index=-1
    for row in lines(run/'episodes.jsonl'):
        index=row['update_index']
        require(last_index<=index<UPDATES,'episode log update order')
        last_index=index
        episode_hashes[index].update(encoded(row['episode'])+b'\n')
        logged_counts[index]+=1
    for index,value in enumerate(expected_rows):
        require(logged_counts[index]==value['count'] and episode_hashes[index].hexdigest()==value['episodes'],'episode log/update mismatch')
    raw_count=0
    # Reading concatenated gzip to EOF validates every member CRC/trailer.
    with gzip.open(run/'transitions.jsonl.gz','rt') as stream:
        for index in range(UPDATES):
            rewards=costs=0.
            raw_hash=hashlib.sha256()
            ended=0
            for tick in range(HORIZON):
                line=stream.readline()
                require(line.endswith('\n'),'raw gzip missing/incomplete transition row')
                row=json.loads(line)
                require(row['schema']=='guitar_learning.gpu_transition.v1' and row['update_index']==index and row['tick_in_update']==tick,'raw transition sequence')
                for name in ('reward','cost','terminated','truncated'):
                    require(len(row[name])==ENVS,'raw transition batch size '+name)
                require(all(isinstance(x,bool) for name in ('terminated','truncated') for x in row[name]),'raw done-mask types')
                require(not any(row['truncated']),'unexpected truncated GPU song')
                require(all(math.isfinite(x) for x in row['reward']) and all(math.isfinite(x) and x>=0 for x in row['cost']),'nonfinite/negative raw costs')
                ids=[e['env_id'] for e in row['episodes']]
                require(len(ids)==len(set(ids)) and set(ids)=={i for i,v in enumerate(row['terminated']) if v},'raw terminal/episode correspondence')
                for value in row['episodes']:
                    raw_hash.update(encoded(value)+b'\n')
                ended+=len(ids)
                rewards+=sum(row['reward'])
                costs+=sum(row['cost'])
                raw_count+=1
            expected=expected_rows[index]
            require(ended==expected['count'] and raw_hash.hexdigest()==expected['episodes'],'raw episode/update mismatch')
            require(math.isclose(rewards/(HORIZON*ENVS),expected['reward'],rel_tol=2e-5,abs_tol=2e-6),'raw reward/update mean')
            require(math.isclose(costs/(HORIZON*ENVS),expected['cost'],rel_tol=2e-5,abs_tol=2e-6),'raw cost/update mean')
            if (index+1)%100==0:
                print('Verified raw updates',index+1,flush=True)
        require(stream.read()=='','unexpected extra raw transition data')
    song=read(run/'song_report.json')
    require(song['completed'] is True and song['partial_trajectories_are_successes'] is False,'song report lifecycle')
    require(song['completed_episodes']==report['completed_episodes']==episode_counts['all'],'ended episode total')
    require(all(song['episode_counts'][k]==episode_counts[k] for k in ('physical_failure','timeline_complete','stage_success')),'song report episode counts')
    cache=[]
    cache_reasons=Counter()
    # Final verification accepts successful recovery; the first200 gate's
    # no-intervention requirement is a separate, stricter observation.
    for row in lines(run/'events.jsonl'):
        if row.get('event')=='cuda_cache_release':
            cache_reasons[row['reason']]+=1
            require(row['after']['free_bytes']>=1024**3,'CUDA floor after cache recovery')
            if row['reason']=='optimizer_boundary':
                cache.append(row)
    require([r['update_index'] for r in cache]==list(range(UPDATES)),'cache boundary sequence')
    free=[r['after']['free_bytes'] for r in cache]
    base=sum(cache[0]['after'][k] for k in ('free_bytes','reserved_bytes'))
    growth=[base-sum(r['after'][k] for k in ('free_bytes','reserved_bytes')) for r in cache]
    require(min(free)>=1024**3 and report['resources']['cuda_free_guard_sample_min_bytes']>=1024**3,'CUDA resource floor')
    ram_floor=int(settings['min_available_memory_gib']*1024**3)
    ram_min=None
    for row in lines(run/'resources.jsonl'):
        require(row['low_memory'] is None and row['available_memory_bytes']>=ram_floor,'RAM resource floor')
        ram_min=row['available_memory_bytes'] if ram_min is None else min(ram_min,row['available_memory_bytes'])
    require(ram_min is not None and report['resources']['min_available_memory_bytes']>=ram_floor,'missing RAM samples/floor')
    telemetry_count=0
    telemetry_free=None
    for row in lines(phase/'gpu_resources_long.jsonl'):
        finite(row,'GPU telemetry')
        telemetry_count+=1
        telemetry_free=row['free_mib'] if telemetry_free is None else min(telemetry_free,row['free_mib'])
    require(telemetry_count>0,'missing external GPU telemetry')
    native_errors=[line for line in (phase/'train1024_large_2000.log').read_text().splitlines()
        if ('[Error]' in line or '[Warning]' in line) and 'Could not load visual geom' not in line]
    require(not native_errors,'unexpected native warnings/errors: '+repr(native_errors[:5]))
    # No Isaac import, model construction, CUDA query, or optimizer execution.
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    torch.set_num_threads(1)
    payload=torch.load(run/'final.pt',map_location='cpu',weights_only=False)
    tensors=Counter()
    def tensor_finite(value,branch):
        if isinstance(value,torch.Tensor):
            require(value.device.type=='cpu' and bool(torch.isfinite(value).all()),'nonfinite/non-CPU checkpoint '+branch)
            tensors[branch]+=1
        elif isinstance(value,dict):
            for item in value.values():tensor_finite(item,branch)
        elif isinstance(value,(list,tuple)):
            for item in value:tensor_finite(item,branch)
        elif isinstance(value,float):
            require(math.isfinite(value),'nonfinite checkpoint scalar '+branch)
    require(payload['updates']==UPDATES,'checkpoint update count')
    require(payload['identity']['config']==settings['ppo'],'checkpoint PPO configuration')
    require(math.isfinite(payload['cost_weight']) and payload['cost_weight']>=0,'checkpoint cost weight')
    architecture=payload['identity']['architecture']
    require(architecture['size']=='large' and architecture['state_dim']==512 and architecture['role']=='left','checkpoint architecture')
    require(architecture['contract']==read(run/'training_contract.json'),'checkpoint training contract')
    for branch in ('model','actor_optimizer','value_optimizer'):
        tensor_finite(payload[branch],branch)
        require(tensors[branch]>0,'empty checkpoint tensors '+branch)
    require(payload['actor_optimizer']['state'] and payload['value_optimizer']['state'],'empty optimizer state')
    return dict(completed=True,scope='Completed execution/data/model verification; geometric contact candidates are not pressure or acoustic success',
        committed_updates=UPDATES,committed_transitions=TRANSITIONS,raw_rows=raw_count,
        raw_gzip_all_member_CRC_and_exact_episode_correspondence=True,no_discarded_transitions=True,
        ended_episode_counts=dict(episode_counts),input_SHA_verified=len(pins),frozen_python_verified=len(source),
        final_checkpoint_CPU_finite_tensor_counts=dict(tensors),gpu_lifecycle_verified=True,
        memory=dict(post_cache_free_min_GiB=min(free)/1024**3,post_cache_free_final_GiB=free[-1]/1024**3,
            cache_release_reason_counts=dict(cache_reasons),
            non_torch_growth_max_GiB=max(growth)/1024**3,non_torch_growth_final_GiB=growth[-1]/1024**3,
            non_torch_growth_last100_range_GiB=(max(growth[-100:])-min(growth[-100:]))/1024**3,
            ram_sample_min_GiB=ram_min/1024**3,external_GPU_samples=telemetry_count,
            external_GPU_free_min_MiB=telemetry_free,
            scope='Resource observations and configured floors; free+Torch-reserved residual does not establish an internal SDK allocation cause'),
        resume_and_evaluation='Not checked by this verifier; see separate resume/evaluation evidence')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',type=Path,default=Path(__file__).parent)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    result=verify(args.phase/'train1024_large_2000',args.phase)
    out=args.out or args.phase/'long_run_verification.json'
    with out.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
