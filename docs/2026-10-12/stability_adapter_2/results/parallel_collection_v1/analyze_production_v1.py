"""Finite production prefix and reference throughput; no additional simulation."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;RUN=P/'long_v1';inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):inputs[str(path)]=sha(path);return json.loads(path.read_text())
raw=(RUN/'training.jsonl').read_bytes();raw=raw[:raw.rfind(b'\n')+1]
with (P/'production_prefix_v1.jsonl').open('xb') as f:f.write(raw)
inputs[str(P/'production_prefix_v1.jsonl')]=sha(P/'production_prefix_v1.jsonl')
entries=[json.loads(line) for line in raw.splitlines()];assert entries
oldraw=(P/'previous_training_prefix_v1.jsonl').read_bytes();inputs[str(P/'previous_training_prefix_v1.jsonl')]=sha(P/'previous_training_prefix_v1.jsonl');old=json.loads(oldraw.splitlines()[0])
first=entries[0]
checks={'N4_T256_1024':all(e['collection']['shape_T_N']==[256,4] and e['collection']['policy_batch_size']==4 and e['ppo']['transitions']==1024 for e in entries),
    'accepted_KL_RMS':all(e['ppo']['optimizer_steps']>0 and not e['ppo']['RMS_updated'] and 0<=e['ppo']['final_analytic_kl']<=.02 for e in entries),
    'counter_contiguous':all(e['update']==317+i and e['transitions']==80896+(i+1)*1024 for i,e in enumerate(entries)),
    'live_prefix_preserved':(RUN/'training.jsonl').read_bytes().startswith(raw),
    'actual_input_closure_unchanged':all(sha(path)==expected for path,expected in read(RUN/'attempt.json')['input_sha256'].items())}
record={'utc':datetime.now(timezone.utc).isoformat(),'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,
    'updates_in_prefix':len(entries),'last_update':entries[-1]['update'],'last_transitions':entries[-1]['transitions'],
    'first_production_collection':first['collection'],'first_production_rollout_and_update_s':first['rollout_and_update_s'],
    'production_mean_combined_transitions_per_second':sum(e['ppo']['transitions'] for e in entries)/sum(e['rollout_and_update_s'] for e in entries),
    'reference_single_first_update':old['update'],'reference_single_combined_transitions_per_second':old['ppo']['transitions']/old['rollout_and_update_s'],
    'first_parallel_vs_reference_ratio':(first['ppo']['transitions']/first['rollout_and_update_s'])/(old['ppo']['transitions']/old['rollout_and_update_s']),
    'scope':'finite N4/T256 production prefix; throughput reference uses different checkpoint/data batch, not controlled benchmark; final native evaluation and full completion remain separate'}
assert all(sha(path)==expected for path,expected in inputs.items())
with (P/'production_analysis_v1.json').open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({k:record[k] for k in ('passed','updates_in_prefix','last_update','last_transitions','first_production_collection','production_mean_combined_transitions_per_second','reference_single_combined_transitions_per_second','first_parallel_vs_reference_ratio')},indent=2))
assert record['passed']
