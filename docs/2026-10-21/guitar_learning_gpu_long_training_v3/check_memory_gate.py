"""Check the first committed 200 updates of the live cost experiment."""
import hashlib
import json
import math
from pathlib import Path
p=Path(__file__).resolve().parent
run=p/'train1024_large_2000'
rows=[json.loads((run/('update_%06d.json'%i)).read_text()) for i in range(200)]
assert all(r['update_index']==i and r['transitions']==32768 and r['journal']['committed']==(i+1)*32768 for i,r in enumerate(rows))
cache=[];other=[]
for line in (run/'events.jsonl').read_text().splitlines(keepends=True):
    if not line.endswith('\n'):break
    r=json.loads(line)
    if r.get('event')=='cuda_cache_release' and r.get('update_index',200)<200:
        (cache if r['reason']=='optimizer_boundary' else other).append(r)
assert [r['update_index'] for r in cache]==list(range(200)) and not other
base=sum(cache[0]['after'][k] for k in ('free_bytes','reserved_bytes'))
growth=[base-sum(r['after'][k] for k in ('free_bytes','reserved_bytes')) for r in cache]
free=[r['after']['free_bytes'] for r in cache]
assert min(free)>4*1024**3 and max(growth)<512*1024**2
assert max(growth[100:])-min(growth[100:])<256*1024**2
errors=[s for s in (p/'train1024_large_2000.log').read_text().splitlines() if ('[Error]' in s or '[Warning]' in s) and 'Could not load visual geom' not in s]
assert not errors,errors
pins=json.loads((run/'inputs_before.json').read_text())
assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in pins.items())
for r in rows:
    assert all(math.isfinite(r[k]) for k in ('mean_reward','mean_cost','analytic_kl'))
    for c in r['diagnostics']['post_update']['critics'].values():
        assert math.isfinite(c['mse']) and c['target']['nonfinite_count']==0 and c['value']['nonfinite_count']==0
    for e in r['completed_episodes']:
        c=e['cost_components'];expected=5*max(32.81666666666667-e['task_time_s'],0) if e['reason']=='terminal_failure' else 0
        assert math.isclose(c['remaining_song_failure'],expected,rel_tol=1e-6,abs_tol=1e-4)
        assert math.isclose(c['remaining_song_failure']+c['original_physics_and_terminal'],e['cost'],abs_tol=1e-4)
result=dict(completed=True,scope='First 200 updates only; continue same process to2000; efficacy not established',
    committed_updates=200,committed_transitions=6553600,
    post_cache_free_min_GiB=min(free)/1024**3,post_cache_free_final_GiB=free[-1]/1024**3,
    non_torch_growth_max_GiB=max(growth)/1024**3,
    non_torch_growth_last100_range_GiB=(max(growth[100:])-min(growth[100:]))/1024**3,
    resource_limits=dict(post_cache_free_min_GiB=4,non_torch_growth_max_MiB=512,last100_range_MiB=256),
    low_memory_releases=0,unexpected_native_errors_or_warnings=errors,input_pins_verified=len(pins),
    completed_episodes=sum(len(r['completed_episodes']) for r in rows),
    curriculum_progress=rows[-1]['left_curriculum']['progress'],cost_components_and_critic_finiteness_verified=True)
(p/'memory_gate_200.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
