"""Verify the negative long-training finding and actual model recovery."""
import json
import math
from collections import Counter
from pathlib import Path
import numpy as np
import torch

P = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def equal(a,b):
    if isinstance(a,torch.Tensor):return torch.equal(a,b)
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):
        return type(a) is type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


def finite(value):
    if isinstance(value,torch.Tensor):return bool(torch.isfinite(value).all())
    if isinstance(value,dict):return all(finite(v) for v in value.values())
    if isinstance(value,(tuple,list)):return all(finite(v) for v in value)
    if isinstance(value,float):return math.isfinite(value)
    return True


attempts=[]
for name,updates,transitions,failure_type in [
    ('train1024_large_70',26,851968,'MemoryError'),
    ('train1024_large_64_cache_v2',48,720896,'RuntimeError'),
    ('train1024_large_64_cache_v3',28,917504,'OutOfMemoryError'),
    ('train1024_large_64_batched_v4',39,1277952,'RuntimeError'),
    ('train512_large_128_v5',94,1540096,'KeyboardInterrupt'),
]:
    r=load(P/name/'report.json')
    assert not r['completed'] and r['optimizer_updates']==updates and r['transitions']==transitions
    assert r['failure']['type']==failure_type
    assert not r['changed_inputs'] and not r['missing_import_pins']
    assert not r['cleanup_errors']
    assert r['gpu_scene']['physx_use_gpu'] and r['gpu_scene']['use_gpu_pipeline']
    assert r['journal']['closed'] and r['journal']['unresolved_sampled']==0
    attempts.append(dict(run=name,num_envs=r['settings']['num_envs'],optimizer_updates=updates,
        committed_transitions=transitions,stopped=r['stopped'],failure_type=failure_type,
        recovery_checkpoint=r['recovery_checkpoint'],resources=r['resources']))

run=P/'train512_large_128_v5'
r=load(run/'report.json')
assert r['stopped']=='interrupted' and (P/'intentional_stop.json').is_file()
assert r['journal']['discarded']>0 and r['recovery_checkpoint']['error'] is None
assert r['lifecycle_verified']
raw=rows(run/'episodes.jsonl')
committed=[x['episode'] for x in raw if x['update_index']<94]
song=load(run/'song_report.json')
counts=dict(timeline_complete=sum(e['reason']=='timeline_complete' for e in committed),
    physical_failure=sum(e['reason']=='terminal_failure' for e in committed),
    stage_success=sum(bool(e['song']['stage_success']) for e in committed))
assert r['completed_episodes']==song['completed_episodes']==len(committed)
assert song['episode_counts']==counts and song['episodes_path']=='episodes.jsonl'
assert song['schema']=='guitar_learning.gpu_song_run.v2' and 'episodes' not in song
assert counts['timeline_complete']>0
cache=[e for e in rows(run/'events.jsonl') if e.get('event')=='cuda_cache_release']
assert len(cache)==r['resources']['cuda_cache_releases']==94
assert all(e['before']['allocated_bytes']==e['after']['allocated_bytes'] for e in cache)
assert r['resources']['cuda_free_guard_sample_min_bytes']>=1024**3
non_torch_base=cache[0]['after']['free_bytes']+cache[0]['after']['reserved_bytes']
curve=[dict(update_index=e['update_index'],free_after_bytes=e['after']['free_bytes'],
            non_torch_increase_bytes=non_torch_base-e['after']['free_bytes']-e['after']['reserved_bytes']) for e in cache]

source=torch.load(run/'failure_last_valid.pt',map_location='cpu',weights_only=False)
resume=P/'resume512_after_inspection'
initial=torch.load(resume/'initial.pt',map_location='cpu',weights_only=False)
final=torch.load(resume/'final.pt',map_location='cpu',weights_only=False)
keys=['identity','model','actor_optimizer','value_optimizer','cost_weight','updates',
      'torch_rng','numpy_rng','python_rng','cuda_rng']
restored={k:equal(source[k],initial[k]) for k in keys}
assert all(restored.values()),restored
assert source['updates']==94 and final['updates']==95
assert all(finite(final[k]) for k in ['model','actor_optimizer','value_optimizer'])
assert any(not torch.equal(initial['model'][k],v) for k,v in final['model'].items()
           if k.startswith(('actor_','reward_critic','cost_critic')))
rr=load(resume/'report.json')
assert rr['completed'] and rr['failure'] is None and rr['transitions']==16384 and rr['optimizer_updates']==95
assert not rr['changed_inputs'] and not rr['missing_import_pins'] and not rr['cleanup_errors']
assert rr['lifecycle_verified'] and rr['journal']['discarded']==0 and rr['journal']['closed']
assert 'Ran 48 tests' in (P/'tests_batched_v4.log').read_text()
assert 'Ran 12 tests' in (P/'tests_shared_ppo_dependents.log').read_text()
assert '\nOK\n' in (P/'tests_batched_v4.log').read_text()
assert '\nOK\n' in (P/'tests_shared_ppo_dependents.log').read_text()
result=dict(completed=True,scope='Completed inspection; long training readiness NOT established',
    long_training_ready=False,recommended_num_envs=None,related_cpu_tests_passed=60,full_cpu_suite_rerun=False,
    attempts=attempts,controlled_stop=dict(optimizer_updates=94,committed_transitions=1540096,
        discarded_transitions=r['journal']['discarded'],committed_episodes=len(committed),episode_counts=counts,
        raw_uncommitted_episodes=len(raw)-len(committed),
        failure_reasons=dict(Counter(reason for e in committed for reason in e['failure_reasons'])),
        cache_releases=len(cache),post_optimizer_free_curve=curve,
        late_memory_growth_unresolved=True,final_curriculum=load(run/'update_000093.json')['left_curriculum']),
    actual_recovery=dict(completed=True,source_updates=94,final_updates=95,additional_transitions=16384,
                         restored_fields_equal=restored,finite_final_model_and_optimizers=True,
                         physical_scope='new prepared episodes'),
    no_long_run_command_published=True)
(P/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['attempts','controlled_stop']},indent=2))
print(json.dumps(dict(committed_episodes=len(committed),counts=counts,discarded=r['journal']['discarded'],
                      first_post_free_GiB=curve[0]['free_after_bytes']/1024**3,
                      last_post_free_GiB=curve[-1]['free_after_bytes']/1024**3)))
