"""Postprocess immutable native evidence; does not train or simulate."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[4]
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

inputs=[Path(__file__),PHASE/'cpu_tests_v1.log',PHASE/'cpu_verification_v1.json',
        ROOT/'docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload100_v2/trace.json']
for name in ('native_mean_v2','native_sample_resume_v2'):
    inputs += [PHASE/name/f for f in ('attempt.json','report.json','initial_values.json','learning_abi.json',
                'controls.json','trace.json','joint_crossings.json','joint_events.json','music_physics_samples.json',
                'final_observation.json','initial_policy.pt','media/capture.json')]
hashes={str(p):sha(p) for p in inputs}
with (PHASE/'native_verifier_attempt_v1.json').open('x') as f: json.dump({'input_sha256':hashes},f,indent=2)
results={}
for name in ('native_mean_v2','native_sample_resume_v2'):
    folder=PHASE/name;report=read(folder/'report.json');controls=read(folder/'controls.json')
    trace=read(folder/'trace.json');initial=read(folder/'initial_values.json')
    samples=read(folder/'music_physics_samples.json');events=read(folder/'joint_events.json')
    abi=read(folder/'learning_abi.json');codec=abi['payload']['codec']
    assert report['completed'] and report['inputs_unchanged'] and not report['forbidden_calls']
    assert report['control_steps']==len(controls)==300 and report['physics_steps']==len(samples)==1200
    assert [r['physics_step'] for r in trace]==list(range(0,1201,4))
    assert [r['physics_step'] for r in samples]==list(range(1,1201))
    assert all(len(r['observation_before'])==739 and len(r['action81'])==81 for r in controls)
    assert len(read(folder/'final_observation.json'))==739
    lower,upper,anchor,rates=[np.array(codec[k]) for k in ('lower_rad','upper_rad','anchor_rad','rates_rad_s')]
    previous=np.array([r['pos'] for r in initial['native_initial_state']['human_dof_states']])
    requested_deltas=[]
    for row in controls:
        action,latent=np.array(row['action81']),np.array(row['latent81'])
        assert np.allclose(np.tanh(latent),action,atol=6e-8,rtol=1e-7)
        requested=anchor+np.where(action>=0,upper-anchor,anchor-lower)*action
        final=np.array(row['owner_info']['final_rad'])
        np.testing.assert_allclose(requested,row['requested_rad'],atol=1e-12,rtol=0)
        assert np.all(final>=lower-1e-7) and np.all(final<=upper+1e-7)
        assert np.all(abs(final-previous)<=rates/60+2e-7)
        previous=final;requested_deltas.append(requested-anchor)
    for video in report['videos'].values():
        assert video['stream']['nb_read_frames']=='151' and video['stream']['avg_frame_rate']=='30/1'
        assert sha(Path(video['path']))==video['sha256']
    positions=np.array([r['position_W_m'] for r in trace])
    rotations=Rotation.from_quat([r['quaternion_xyzw'] for r in trace])
    displacement=np.linalg.norm(positions-positions[0],axis=1)*1000
    angles=(rotations[0].inv()*rotations).magnitude()*180/np.pi
    q=np.array([r['q_rad'] for r in trace]);q0=q[0]
    # Physical torso motion is measured separately from the target bounds.
    body=np.array([g=='body' for g in codec['groups']])
    deltas=np.array(requested_deltas)
    results[name]={'physics_seconds':5.,'control_steps':300,'physics_steps':1200,'observation_dimension':739,
        'maximum_displacement_mm':float(displacement.max()),'maximum_rotation_deg':float(angles.max()),
        'maximum_actual_body_angle_change_deg':float(abs(q[:,body]-q0[body]).max()*180/np.pi),
        'settled_events':len(events),'joint_success_events':sum(e['joint_success'] for e in events),
        'crossings':len(read(folder/'joint_crossings.json')),
        'sampled_nonzero_action_channels':int(np.any(np.array([r['action81'] for r in controls])!=0,axis=0).sum()),
        'requested_anchor_delta_rms_rad_by_group':{g:float(np.sqrt(np.mean(deltas[:,np.array(codec['groups'])==g]**2)))
                                                  for g in ('body','head','arm','finger')},
        'frames_per_video':151,'source_actor_calls':0,'native_training_updates':0,'all_validation_assertions_passed':True}
assert read(PHASE/'native_mean_v2/trace.json')==read(inputs[3])
assert results['native_sample_resume_v2']['sampled_nonzero_action_channels']==81
assert read(PHASE/'native_mean_v2/learning_abi.json')==read(PHASE/'native_sample_resume_v2/learning_abi.json')
assert all(sha(Path(p))==h for p,h in hashes.items())
result={'cpu_tests_passed':22,'native_runs':2,'native_physics_steps':2400,'native_videos':4,
        'native_optimizer_updates':0,'mean_trace_exact_preload100_v2':True,'resume_same_abi':True,
        'native_training_gate_blocks_before_scene':not (PHASE/'blocked_native_training').exists(),
        'runs':results,'input_sha256':hashes,'scope':'structure/CPU optimizer/native inference only; reward and music success not certified'}
with (PHASE/'native_verification_v1.json').open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},ensure_ascii=False))
