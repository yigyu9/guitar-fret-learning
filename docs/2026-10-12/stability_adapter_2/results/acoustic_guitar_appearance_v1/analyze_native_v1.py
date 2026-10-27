"""Verify the appearance runs against the preceding native physics reference."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

R = Path('/home/ajou/yigyu/3')
P = R/'docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1'
B = P.parent/'realistic_guitar_proportions_v1/native_realistic_v2'
inputs = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    inputs[str(path)] = sha(path)
    return json.loads(Path(path).read_text())


inputs[str(Path(__file__).resolve())] = sha(__file__)
prior = read(B/'report.json')
prior_init = read(B/'initial_values.json')
checks, metrics = {}, {}
for version in (2, 3):
    trial = P/f'native_v{version}'
    report = read(trial/'report.json')
    initial = read(trial/'initial_values.json')
    collision = read(trial/'collision_comparison.json')
    props = read(trial/'native_properties.json')
    closure = read(trial/'attempt.json')['input_sha256']
    checked = read(trial/'inputs_verified.json')
    prefix = f'v{version}_'
    checks[prefix+'completed_5sec'] = report['completed'] and report['physics_steps']==1200 and report['controls']==300 and len(report['rows'])==301
    checks[prefix+'no_policy_no_forbidden_calls'] = report['music_actors']==report['policy_calls']==report['checkpoint_loads']==0 and not report['forbidden_calls'] and report['property_setter_calls']==1 and report['property_setter_rejections']==0
    checks[prefix+'collision_API_exact'] = collision['exact'] and collision['new']==collision['reference']
    checks[prefix+'mass_COM_fullI_exact'] = props['applied']==prior['mass_properties']['applied']
    checks[prefix+'cache_checks'] = all(report['property_cache_checks'].values())
    checks[prefix+'same_targets_PD_strap'] = initial['q_ref_rad']==prior_init['q_ref_rad'] and initial['PD_properties']==prior_init['PD_properties'] and initial['strap_initial']==prior_init['strap_initial']
    checks[prefix+'source_FK'] = initial['source_audit']['source_clear'] and max(e['position_error_m'] for e in initial['native_FK_error'].values())<1e-5
    checks[prefix+'native_inputs_preserved'] = checked['unchanged'] and all(sha(path)==value for path,value in closure.items())
    inputs.update(closure)
    checks[prefix+'constant_targets'] = all(row['submitted_target_rad']==initial['q_ref_rad'] for row in report['rows'][1:])
    contacts = read(trial/'contacts.json')
    checks[prefix+'contact_queries_300'] = len(contacts)==300
    capture = read(trial/'media/capture.json')
    checks[prefix+'151_native_frames'] = len(capture['frames'])==151 and capture['fps']==30
    for frame in capture['frames']:
        for key in ['image_sha256', 'raw_image_sha256']:
            assert all(sha(path)==value for path,value in frame[key].items())
            inputs.update(frame[key])
    inputs[str(trial/'initial_guitar_appearance.png')] = sha(trial/'initial_guitar_appearance.png')
    p0 = np.array(report['rows'][0]['position_W_m'])
    pf = np.array(report['rows'][-1]['position_W_m'])
    q = Rotation.from_quat([row['quaternion_xyzw'] for row in report['rows']])
    prior_q = Rotation.from_quat([row['quaternion_xyzw'] for row in prior['rows']])
    pos_delta = np.array([row['position_W_m'] for row in report['rows']])-np.array([row['position_W_m'] for row in prior['rows']])
    metrics[f'v{version}'] = {'initial_to_5s_actor_root_m':float(np.linalg.norm(pf-p0)),
        'initial_to_5s_rotation_deg':float(np.rad2deg((q[0].inv()*q[-1]).magnitude())),
        'max_trajectory_position_difference_vs_prior_m':float(np.linalg.norm(pos_delta,axis=1).max()),
        'max_trajectory_rotation_difference_vs_prior_deg':float(np.rad2deg((prior_q.inv()*q).magnitude()).max()),
        'native_collision_shapes':len(collision['new']['shapes']), 'native_body_count':len(collision['new']['names'])}
checks['analysis_inputs_preserved'] = all(sha(path)==value for path,value in inputs.items())
assert all(checks.values()), checks
output = P/'verification_v1.json'
assert not output.exists()
output.write_text(json.dumps({'passed':True,'checks':checks,'metrics':metrics,'input_sha256':inputs,
    'scope':'native visual-only upgrade; not music, left-free stability, measured wood mass or a product scan'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(checks),'metrics':metrics}))
