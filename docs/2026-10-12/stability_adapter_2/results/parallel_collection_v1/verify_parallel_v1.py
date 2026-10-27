"""Audit real workers, checkpoint preservation and one batched CUDA update."""
import hashlib,importlib.util,json
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;SMOKE=P/'smoke_v1'
helper_path=P.parent/'graphics_isolation_v1/verify_graphics_v1.py'
spec=importlib.util.spec_from_file_location('helper',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
equal=helper.equal;sha=helper.sha
inputs={str(Path(__file__).resolve()):sha(__file__),str(helper_path):sha(helper_path)}
def read(path):inputs[str(path)]=sha(path);return json.loads(path.read_text())
def checkpoint(path):inputs[str(path)]=sha(path);return torch.load(path,map_location='cpu',weights_only=True)
source_record=read(P/'previous_stop_snapshot_v1.json')['checkpoint_record'];source=checkpoint(Path(source_record['checkpoint']))
adopted=checkpoint(SMOKE/'adopted_checkpoint.pt');initial=checkpoint(SMOKE/'checkpoints/initial_000000.pt');updated=checkpoint(SMOKE/'checkpoints/update_000316.pt')
fields=set(source)-{'abi','abi_sha256','resume_scope'}
metadata=read(SMOKE/'initial_values.json')['parallel_collection']
probe=read(P/'probe_v1/report.json');report=read(SMOKE/'report.json')
lines=(SMOKE/'training.jsonl').read_text().splitlines();assert len(lines)==1
inputs[str(SMOKE/'training.jsonl')]=sha(SMOKE/'training.jsonl');entry=json.loads(lines[0])
checks={'source_numeric_adoption_exact':all(equal(source[k],adopted[k]) for k in fields),
    'source_numeric_initial_exact':all(equal(source[k],initial[k]) for k in fields),
    'probe_success':probe['completed'] and probe['inputs_unchanged'] and read(P/'probe_v1.exit.json')['returncode']==0,
    'two_native_initials_exact':probe['initial_native_states_exact'],
    'two_real_q_states_distinct':probe['maximum_actual_q_difference_rad']>0,
    'four_spawn_workers':metadata['workers']==4 and len(set(metadata['processes']))==4 and metadata['start_method']=='spawn',
    'all_training_graphics_minus1':all(v['creation_calls'][0]['forwarded_graphics_device_id']==-1 and not v['render_lookup_counts'] for v in metadata['graphics_resource_policy_by_worker']),
    'physical_initial_noise_zero':not metadata['reset_randomization'],
    'actual_batched_collection':entry['collection']['shape_T_N']==[64,4] and entry['collection']['policy_batch_size']==4 and entry['ppo']['transitions']==256,
    'one_actual_CUDA_update':updated['updates']==source['updates']+1 and updated['transitions']==source['transitions']+256 and entry['ppo']['optimizer_steps']>0,
    'KL_and_RMS':0<=entry['ppo']['final_analytic_kl']<=.02 and not entry['ppo']['RMS_updated'] and all(equal(v,updated['model'][k]) for k,v in source['model'].items() if k.startswith('obs_rms.')),
    'actor_critic_changed':all(any(not equal(v,updated['model'][k]) for k,v in source['model'].items() if k.startswith(prefix)) for prefix in ('actor.','critic.')),
    'smoke_completed':report['completed'] and report['inputs_unchanged'] and read(P/'smoke_v1.exit.json')['returncode']==0}
video_summaries=[]
for label in ('initial_000000','update_000316'):
    base=SMOKE/'evaluations'/label;ev=read(base/'report.json');native=ev['native_report'];capture=read(base/'native/episode_0001/media/capture.json')
    checks[label+'_native_full_and_frozen']=ev['completed'] and ev['inputs_unchanged'] and native['full_horizon_completed'] and native['baseline_weights_unchanged'] and not native['forbidden_calls'] and native['safety_violation'] is None
    checks[label+'_frames_and_strap']=len(capture['frames'])==492 and capture['frames'][0]['physics_step']==0 and capture['frames'][-1]['physics_step']==3928 and native['strap_force_calls']==3928*13
    checks[label+'_video_SHA']=all(sha(v['path'])==v['sha256'] and v['stream']['nb_read_frames']=='492' for v in native['videos'].values())
    for v in native['videos'].values():inputs[v['path']]=v['sha256']
    video_summaries.append({'label':label,'native_report':native})
checks['new_source_unchanged']=all(sha(path)==expected for path,expected in read(P/'source_before_native_v1.json').items())
checks['actual_input_closure_unchanged']=all(sha(path)==expected for path,expected in read(SMOKE/'attempt.json')['input_sha256'].items())
checks['audit_input_unchanged']=all(sha(path)==expected for path,expected in inputs.items())
result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'actual_update':entry,'evaluations':video_summaries,
    'physical_noise':read(P/'initial_noise_analysis_v1.json'),
    'scope':'N2 five-second independent native test plus N4/T64 batched CUDA one-update/full movies; production N4/T256 speed and musical success evaluated separately'}
with (P/'verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps({'passed':result['passed'],'checks':checks,'collection':entry['collection'],'KL':entry['ppo']['final_analytic_kl']},indent=2))
assert result['passed']
