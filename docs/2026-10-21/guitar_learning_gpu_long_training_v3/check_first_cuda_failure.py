"""Verify the new cost on actual committed CUDA episodes, without GPU calls."""
import json
import math
from pathlib import Path
p=Path(__file__).resolve().parent
run=p/'train1024_large_2000'
def lines(path):
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):break
            yield json.loads(line)
committed={r['update_index'] for r in lines(run/'learning_metrics.jsonl')}
settings=json.loads((run/'settings.json').read_text())
contract=json.loads((run/'training_contract.json').read_text())
scene=json.loads((run/'gpu_scene_initial.json').read_text())
assert scene['physx_use_gpu'] and scene['use_gpu_pipeline']
assert scene['num_envs']==settings['num_envs']
rate=contract['termination']['failure_horizon_cost']['rate_cost_per_s']
duration=contract['task']['duration_s']
verified=[]
for row in lines(run/'episodes.jsonl'):
    if row['update_index'] not in committed:continue
    e=row['episode'];c=e['cost_components']
    assert c['failure_rate_cost_per_s']==rate
    assert math.isclose(c['original_physics_and_terminal']+c['remaining_song_failure'],e['cost'],abs_tol=1e-4)
    if e['reason']=='terminal_failure':
        expected=rate*max(duration-e['task_time_s'],0.)
        assert math.isclose(c['remaining_song_failure'],expected,rel_tol=1e-6,abs_tol=1e-4)
        assert c['original_physics_and_terminal']>=5.-1e-4
        verified.append(dict(update_index=row['update_index'],env_id=e['env_id'],
            task_time_s=e['task_time_s'],cost=e['cost'],components=c,expected_extra=expected))
        if len(verified)>=5:break
    else:
        assert e['reason']=='timeline_complete' and c['remaining_song_failure']==0
if verified:
    report=dict(completed=True,actual_gpu_physics=True,
        scope='First committed failed CUDA episodes; mathematical cost/clock check, not convergence',
        verified_failures=verified,num_envs=settings['num_envs'],size=settings['size'],
        rate_cost_per_s=rate,song_duration_s=duration)
    (p/'first_cuda_failure_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'completed':True,'verified_failures':len(verified),'first':verified[0]}))
else:print(json.dumps({'completed':False,'reason':'No committed physical failure yet'}))
