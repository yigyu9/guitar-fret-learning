"""Read-only compact progress for the current long run."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent/'train1024_large_2000'
s=json.loads((p/'status.json').read_text())
cache=[]
for line in (p/'events.jsonl').read_text().splitlines():
    try:e=json.loads(line)
    except json.JSONDecodeError:continue
    if e.get('event')=='cuda_cache_release':cache.append(e)
updates=sorted(p.glob('update_*.json'))
a=json.loads(updates[-1].read_text()) if updates else {}
print(json.dumps(dict(status={k:s.get(k) for k in ('phase','update_index','ticks','elapsed_s')},
    committed_updates=len(updates),report_exists=(p/'report.json').exists(),
    latest_post_free_GiB=round(cache[-1]['after']['free_bytes']/1024**3,3) if cache else None,
    post_free_min_GiB=round(min(e['after']['free_bytes'] for e in cache)/1024**3,3) if cache else None,
    recent_post_free_GiB=[[e['update_index'],round(e['after']['free_bytes']/1024**3,3)] for e in cache[-4:]],
    non_torch_growth_GiB=round((sum(cache[0]['after'][k] for k in ('free_bytes','reserved_bytes'))-sum(cache[-1]['after'][k] for k in ('free_bytes','reserved_bytes')))/1024**3,3) if cache else None,
    mean_reward=a.get('mean_reward'),mean_cost=a.get('mean_cost'),
    curriculum_progress=a.get('left_curriculum',{}).get('progress'),
    completed_episodes_latest=len(a.get('completed_episodes',[]))),ensure_ascii=False))
