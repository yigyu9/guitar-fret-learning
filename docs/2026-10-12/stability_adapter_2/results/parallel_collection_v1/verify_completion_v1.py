"""Verify completed parallel production, full movies and checkpoint identity."""
from datetime import datetime,timezone
import importlib.util,json
from pathlib import Path
import numpy as np
import torch
P=Path(__file__).resolve().parent;RUN=P/'long_v1'
helper_path=P.parent/'graphics_isolation_v1/verify_graphics_v1.py'
spec=importlib.util.spec_from_file_location('helper',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
sha=helper.sha;equal=helper.equal;inputs={str(Path(__file__).resolve()):sha(__file__),str(helper_path):sha(helper_path)}
def read(path):inputs[str(path)]=sha(path);return json.loads(path.read_text())
def checkpoint(path):inputs[str(path)]=sha(path);return torch.load(path,map_location='cpu',weights_only=True)
report=read(RUN/'report.json');exit_record=read(P/'long_v1.exit.json')
source=checkpoint(P/'smoke_v1/checkpoints/update_000316.pt');initial=checkpoint(RUN/'checkpoints/initial_000000.pt');final=checkpoint(Path(report['last_checkpoint']))
analysis=read(P/'production_analysis_v1.json')
checks={'completed_exit_zero':report['completed'] and report['inputs_unchanged'] and exit_record['returncode']==0,
    'initial_checkpoint_numerics_exact':all(equal(source[k],initial[k]) for k in set(source)-{'resume_scope'}),
    'four_production_updates':report['updates']==320 and report['transitions']==84992 and final['updates']==320 and final['transitions']==84992,
    'production_prefix_verified':analysis['passed'] and analysis['updates_in_prefix']==4,
    'final_RMS_exact':all(equal(v,final['model'][k]) for k,v in source['model'].items() if k.startswith('obs_rms.')),
    'same_ABI_config':equal(final['abi'],source['abi']) and equal(final['ppo_config'],source['ppo_config']),
    'archive_errors_none':not exit_record['archive_errors']}
summaries={}
for label in ('initial_000000','cutoff_000320'):
    base=RUN/'evaluations'/label;ev=read(base/'report.json');nr=ev['native_report'];rows=read(base/'native/episode_0001/controls.json');trace=read(base/'native/episode_0001/trace.json')
    checks[label+'_full_native']=ev['completed'] and ev['inputs_unchanged'] and nr['full_horizon_completed'] and nr['control_steps']==982 and nr['physics_steps']==3928 and nr['baseline_weights_unchanged'] and not nr['forbidden_calls'] and nr['safety_violation'] is None
    archive=P.parents[2]/'video/parallel_long_v1'/label/'manifest.json';manifest=read(archive)
    checks[label+'_auto_archive']=all(sha(v['source'])==sha(v['archive'])==v['sha256'] for v in manifest['videos'].values())
    for v in manifest['videos'].values():inputs[v['source']]=v['sha256'];inputs[v['archive']]=v['sha256']
    distance=np.linalg.norm([r['position_outside_m'] for r in rows],axis=1)
    q=np.array([r['quaternion_xyzw'] for r in trace]);q/=np.linalg.norm(q,axis=1)[:,None]
    angle=2*np.arccos(np.clip(np.abs(q@q[0]),0,1))
    summaries[label]={'joint_success_events':nr['joint_success_events'],'settled_events':nr['settled_events'],
        'outside_percent':float(np.mean(distance>0)*100),'maximum_outside_root_box_m':float(distance.max()),
        'mean_outside_root_box_m':float(distance.mean()),'maximum_SO3_from_initial_deg':float(np.degrees(angle.max())),
        'videos':nr['videos'],'physics_seconds':nr['physics_seconds'],'archive':str(archive)}
checks['all_new_source_pinned']=all(sha(path)==expected for path,expected in read(P/'source_before_native_v1.json').items())
checks['production_input_closure_still_pinned']=all(sha(path)==expected for path,expected in read(RUN/'attempt.json')['input_sha256'].items())
checks['audit_inputs_unchanged']=all(sha(path)==expected for path,expected in inputs.items())
result={'utc':datetime.now(timezone.utc).isoformat(),'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,
    'final_checkpoint':report['last_checkpoint'],'final_checkpoint_sha256':sha(report['last_checkpoint']),
    'updates':320,'transitions':84992,'new_production_updates':4,'new_production_transitions':4096,
    'recovery_records':len(report['recovery_checkpoints']),'production_analysis':analysis,'evaluations':summaries,
    'scope':'completed N4/T256 four-update deadline run; two full representative native evaluations; reset-noise zero; musical success not certified'}
with (P/'completion_verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'passed':result['passed'],'checks':checks,'summaries':{k:{n:v for n,v in d.items() if n not in ('videos','archive')} for k,d in summaries.items()}},indent=2))
assert result['passed']
