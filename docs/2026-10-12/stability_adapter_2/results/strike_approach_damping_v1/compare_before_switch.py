"""Compare preserved baseline and candidate before first APPROACH PD change."""
import hashlib
import json
from pathlib import Path
phase=Path(__file__).resolve().parent
baseline=phase.parent/'strike_timed_exit_v1/native/data'
candidate=phase/'native/data'
paths=[Path(__file__).resolve(),candidate/'report.json']+[p/n for p in (baseline,candidate) for n in ('controls.json','trace.json')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in paths}
read=lambda p:json.loads(p.read_text())
switch=read(candidate/'report.json')['PD_switch_time_s']
keys=('time_s','phase','actor_used','requested_targets_rad','final_targets_rad','observation','action','source_history','song_time_s')
controls=[[{k:r.get(k) for k in keys} for r in read(p/'controls.json') if r['time_s']<switch] for p in (baseline,candidate)]
traces=[[r for r in read(p/'trace.json') if r['time_s']<=switch] for p in (baseline,candidate)]
assert controls[0]==controls[1] and traces[0]==traces[1]
assert len(controls[0])==76 and len(traces[0])==39
assert all(sha(Path(p))==h for p,h in hashes.items())
(phase/'pre_switch_comparison.json').write_text(json.dumps({'switch_time_s':switch,'exact_control_samples_before_switch':len(controls[0]),'exact_complete_native_trace_samples_through_switch':len(traces[0]),'compared_control_keys':keys,'input_sha256':hashes,'inputs_unchanged':True,'scope':'exact preserved native sampled states and command/history/action/observation prefix; not all1200steps state equality'},indent=2)+'\n')
print('exact pre-switch controls76/states39')
