"""Check the completed 200-update prefix without stopping the live run."""
import hashlib
import json
from pathlib import Path
p=Path(__file__).resolve().parent
run=p/'train1024_large_2000'
rows=[json.loads((run/('update_%06d.json'%i)).read_text()) for i in range(200)]
assert all(r['update_index']==i and r['transitions']==32768 for i,r in enumerate(rows))
events=[]
for line in (run/'events.jsonl').read_text().splitlines(keepends=True):
    if not line.endswith('\n'):break
    r=json.loads(line)
    if r.get('event')=='cuda_cache_release' and r.get('update_index',200)<200:events.append(r)
cache=[r for r in events if r['reason']=='optimizer_boundary']
assert [r['update_index'] for r in cache]==list(range(200))
base=sum(cache[0]['after'][k] for k in ('free_bytes','reserved_bytes'))
growth=[base-sum(r['after'][k] for k in ('free_bytes','reserved_bytes')) for r in cache]
free=[r['after']['free_bytes'] for r in cache]
assert min(free)>1024**3 and max(growth)<128*1024**2
assert max(growth[100:])-min(growth[100:])<128*1024**2
assert not [r for r in events if r['reason']!='optimizer_boundary']
log=(p/'train1024_large_2000.log').read_text()
errors=[line for line in log.splitlines() if ('[Error]' in line or '[Warning]' in line) and 'Could not load visual geom' not in line]
assert not errors,errors
pins=json.loads((run/'inputs_before.json').read_text())
for path,value in pins.items():
    original=Path(path)
    try:saved=p/'source_training'/original.relative_to(p.parents[2])
    except ValueError:saved=original
    actual=saved if saved.is_file() else original
    assert hashlib.sha256(actual.read_bytes()).hexdigest()==value
assert rows[-1]['journal']['committed']==200*32768
result=dict(completed=True,scope='First 200 updates only; same live process continues toward 2000',
    committed_updates=200,committed_transitions=6553600,
    last_physics_steps=rows[-1]['physics_steps'],
    post_cache_free_min_GiB=min(free)/1024**3,post_cache_free_final_GiB=free[-1]/1024**3,
    non_torch_growth_max_GiB=max(growth)/1024**3,
    non_torch_growth_last_100_range_GiB=(max(growth[100:])-min(growth[100:]))/1024**3,
    low_memory_cache_releases=0,unexpected_native_errors_or_warnings=errors,
    input_pins_verified=len(pins),completed_episodes=sum(len(r['completed_episodes']) for r in rows),
    curriculum_progress=rows[-1]['left_curriculum']['progress'],
    decision='Continue the same run; no input/source/physics changes.')
(p/'memory_gate_200.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
