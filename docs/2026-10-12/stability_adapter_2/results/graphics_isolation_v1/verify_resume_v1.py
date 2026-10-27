"""Finite resume/recovery/video snapshot; the ongoing training log remains live."""
from datetime import datetime,timezone
import hashlib,importlib.util,json
from pathlib import Path
import torch
G=Path(__file__).resolve().parent;RUN=G/'long_on_v1'
spec=importlib.util.spec_from_file_location('audit_helper',G/'verify_graphics_v1.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
equal=helper.equal;sha=helper.sha
inputs={str(Path(__file__).resolve()):sha(__file__),str(G/'verify_graphics_v1.py'):sha(G/'verify_graphics_v1.py')}
def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
def checkpoint(p):inputs[str(p)]=sha(p);return torch.load(p,map_location='cpu',weights_only=True)
source=checkpoint(G/'smoke_on_v1/checkpoints/update_000242.pt')
initial=checkpoint(RUN/'checkpoints/initial_000000.pt')
recovery_record=read(RUN/'recovery_records/record_0001.json')
recovery=checkpoint(Path(recovery_record['checkpoint']))
observed=(RUN/'training.jsonl').read_bytes()
raw=observed[:observed.rfind(b'\n')+1]
assert raw
with (G/'training_prefix_at_recovery_v1.jsonl').open('xb') as f:f.write(raw)
inputs[str(G/'training_prefix_at_recovery_v1.jsonl')]=sha(G/'training_prefix_at_recovery_v1.jsonl')
logs=[json.loads(line) for line in raw.splitlines()]
keys=set(source)-{'resume_scope'}
checks={'initial_full_checkpoint_exact':all(equal(source[k],initial[k]) for k in keys),
    'fresh_training_scene_minus1':read(RUN/'initial_values.json')['graphics_resource_policy']['creation_calls'][0]['forwarded_graphics_device_id']==-1,
    'actual_recovery_sha':sha(recovery_record['checkpoint'])==recovery_record['sha256'],
    'recovery_ABI_config_exact':equal(source['abi'],recovery['abi']) and source['abi_sha256']==recovery['abi_sha256'] and equal(source['ppo_config'],recovery['ppo_config']),
    'recovery_new_updates':recovery['updates']>242 and recovery['transitions']==recovery['updates']*256,
    'recovery_counter_record_exact':recovery['updates']==recovery_record['updates'] and recovery['transitions']==recovery_record['transitions'],
    'recovery_RMS_exact':all(equal(v,recovery['model'][k]) for k,v in source['model'].items() if k.startswith('obs_rms.')),
    'accepted_update_sequence':len(logs)>0 and [e['update'] for e in logs]==list(range(243,243+len(logs))) and all(e['ppo']['optimizer_steps']>0 and not e['ppo']['RMS_updated'] and 0<=e['ppo']['final_analytic_kl']<=.02 for e in logs),
    'recovery_in_log':any(e['update']==recovery['updates'] and e['transitions']==recovery['transitions'] for e in logs),
    'original_training_prefix_preserved':(RUN/'training.jsonl').read_bytes().startswith(raw)}
base=RUN/'evaluations/initial_000000';report=read(base/'report.json')
checks['resume_initial_full_evaluation']=report['completed'] and report['inputs_unchanged'] and report['native_report']['full_horizon_completed']
for name in ('trace.json','controls.json'):
    checks['resume_initial_'+name+'_exact']=read(base/'native/episode_0001'/name)==read(G/'smoke_on_v1/evaluations/update_000242/native/episode_0001'/name)
archive=G.parents[2]/'video/graphics_long_v1/initial_000000/manifest.json'
manifest=read(archive)
checks['actual_video_archive']=all(sha(v['source'])==sha(v['archive'])==v['sha256'] for v in manifest['videos'].values())
for v in manifest['videos'].values():inputs[v['source']]=v['sha256'];inputs[v['archive']]=v['sha256']
attempt=read(RUN/'attempt.json')
checks['live_input_closure_unchanged']=all(sha(p)==h for p,h in attempt['input_sha256'].items())
initial_record=read(RUN/'evaluation_records/record_0001.json')
evaluation_time=datetime.fromisoformat(read(base/'attempt.json')['started_utc'])
recovery_time=datetime.fromisoformat(recovery_record['utc'])
checks['recovery_interval_not_early']=(recovery_time-evaluation_time).total_seconds()>=300
checks['audit_inputs_unchanged']=all(sha(p)==h for p,h in inputs.items())
record={'utc':datetime.now(timezone.utc).isoformat(),'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,
    'first_recovery':recovery_record,'last_completed_logged_update_at_snapshot':logs[-1]['update'],
    'last_completed_logged_transitions_at_snapshot':logs[-1]['transitions'],
    'initial_video_archive':str(archive),'training_still_live':not RUN.with_suffix('.exit.json').exists(),
    'scope':'finite prefix and first recovery/video archive only; not final long-run completion or crash-free guarantee'}
with (G/'resume_verification_v1.json').open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps({k:record[k] for k in ('passed','checks','first_recovery','last_completed_logged_update_at_snapshot')},ensure_ascii=False,indent=2))
if not record['passed']:raise AssertionError('resume snapshot verification failed')
