"""Completed initial-noise bank/warm-start/native-motion evidence audit."""
import json,hashlib
from pathlib import Path
import numpy as np
import torch
P=Path(__file__).resolve().parent
inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
def load(p):inputs[str(p)]=sha(p);return torch.load(p,map_location='cpu',weights_only=False)
def equal(a,b):
    if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
    if isinstance(a,(list,tuple)):return isinstance(b,type(a)) and len(a)==len(b) and all(equal(v,w) for v,w in zip(a,b))
    return a==b
inputs[str(Path(__file__))]=sha(__file__)
analysis=read(P/'analysis_v1.json');smoke=read(P/'smoke_v1/report.json');source=load(Path(smoke['source_checkpoint']['source']));initial=load(P/'smoke_v1/initial.pt');trained=load(P/'smoke_v1/checkpoint_001.pt')
checks={'initial_bank_and_collector':analysis['passed'],'source_model_RMS_warm_exact':equal(source['model'],initial['model']),'fresh_optimizer_counters':not initial['optimizer']['state'] and initial['updates']==0 and initial['transitions']==0,'actual_actor_critic_changed':any(not equal(v,trained['model'][k]) for k,v in initial['model'].items() if k.startswith('actor.')) and any(not equal(v,trained['model'][k]) for k,v in initial['model'].items() if k.startswith('critic.')),'RMS_fixed':all(equal(v,trained['model'][k]) for k,v in initial['model'].items() if k.startswith('obs_rms.')),'same_training_ABI':equal(initial['abi'],trained['abi'])}
summaries={}
for index in (1,4):
    label='eval_noise_%d_v1'%index;base=P/label;d=read(base/'report.json');nr=d['native_report'];media=base/'native/episode_0001/media';capture=read(media/'capture.json');rows=read(base/'native/episode_0001/controls.json');trace=read(base/'native/episode_0001/trace.json');selection=read(base/'native/episode_0001/initial_noise_selection.json')
    checks[label+'_full']=d['completed'] and nr['full_horizon_completed'] and nr['control_steps']==982 and nr['physics_steps']==3928 and nr['baseline_weights_unchanged'] and nr['safety_violation'] is None and not nr['forbidden_calls'] and nr['strap_force_calls']==13*3928
    checks[label+'_fixed_index']=selection['selection']['index']==index and read(base/'attempt.json')['evaluation_index']==index
    checks[label+'_capture_complete']=len(capture['frames'])==492 and capture['frames'][0]['time_s']==0 and capture['frames'][-1]['physics_step']==3928 and all(f['render_preserves_states'] for f in capture['frames'])
    checks[label+'_videos_exact']=all(sha(v['path'])==v['sha256'] and int(v['stream']['nb_read_frames'])==492 and abs(float(v['stream']['duration'])-16.4)<.002 for v in nr['videos'].values())
    for v in nr['videos'].values():inputs[v['path']]=sha(v['path'])
    checks[label+'_inputs_unchanged']=read(base/'inputs_verified.json')['unchanged'] and all(sha(path)==h for path,h in read(base/'attempt.json')['input_sha256'].items())
    distance=np.linalg.norm([r['position_outside_m'] for r in rows],axis=1);q=np.array([r['quaternion_xyzw'] for r in trace]);q/=np.linalg.norm(q,axis=1)[:,None];angles=2*np.arccos(np.clip(abs(q@q[0]),0,1))
    summaries[label]={'forced_bank_index':index,'physics_seconds':nr['physics_seconds'],'music_success':nr['joint_success_events'],'music_events':nr['settled_events'],'actor_root_box_outside_percent':float(np.mean(distance>0)*100),'max_actor_root_box_outside_m':float(distance.max()),'mean_actor_root_box_outside_m':float(distance.mean()),'maximum_SO3_from_own_initial_deg':float(np.rad2deg(angles).max()),'native_videos':nr['videos'],'sampling_metadata_note':'selection.sampling is the declared general bank mode; evaluation actually forces index as recorded in attempt.evaluation_index'}
checks['smoke_input_closure_unchanged']=all(sha(path)==h for path,h in read(P/'smoke_v1/attempt.json')['input_sha256'].items())
checks['audit_inputs_exact']=all(sha(path)==h for path,h in inputs.items())
result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'evaluations':summaries,'scope':'validated discrete coupled initial noise and real CUDA update/full evaluations; no continuous-uniform noise or stabilization/music success claim; explicit eval indices fixed, general selection sampling string is documented metadata limitation'}
with (P/'verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'passed':result['passed'],'checks':checks,'evaluations':{k:{n:v for n,v in d.items() if n!='native_videos'} for k,d in summaries.items()}},ensure_ascii=False,indent=2));assert result['passed']
