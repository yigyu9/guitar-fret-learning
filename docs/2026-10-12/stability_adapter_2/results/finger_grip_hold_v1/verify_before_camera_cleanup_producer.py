"""Read-only raw/provenance verification of the bounded finger-grip experiments."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1'


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def controls_with_defaults(rows):
    return [dict(row,arm_static_bias_rad=row.get('arm_static_bias_rad',[0.]*24),
                 palm_control=row.get('palm_control',{})) for row in rows]


def raw_prefix(folder,short):
    for name in ('states','trace','contacts','controls','leg_torques'):
        before=read(PHASE/(short+'/'+name+'.json'))
        after=read(PHASE/(folder+'/'+name+'.json'))[:len(before)]
        if name=='controls':before,after=controls_with_defaults(before),controls_with_defaults(after)
        if before!=after:return False
    return True


def main():
    output=PHASE/'verification.json'
    if output.exists():raise FileExistsError('preserve verification')
    producers={sha(p):str(p.resolve()) for p in PHASE.rglob('*.py')}
    reports=sorted(PHASE.glob('**/report.json'))
    provenance=[]
    checks={'all_run_checks':all(all(read(p)['checks'].values()) for p in reports)}
    for path in reports:
        for name,digest in read(path)['source_sha256'].items():
            current=Path(name)
            preserved=str(current) if sha(current)==digest else producers.get(digest)
            provenance.append({'run':str(path.resolve()),'original_path':name,'sha256':digest,'verified_copy':preserved})
    checks['all_runtime_inputs_current_or_saved_producer']=all(p['verified_copy'] for p in provenance)
    a=PHASE/'native_video/run';b=PHASE/'hold_1s/seed120_palm_feedback_v2'
    checks['native_capture_five_raw_exact']=all(read(a/(n+'.json'))==read(b/(n+'.json')) for n in ('states','trace','contacts','controls','leg_torques'))
    capture=read(PHASE/'native_video/frames/capture.json')
    checks['capture_61_frames_0_to_1s']=[f['physics_step'] for f in capture['frames']]==list(range(0,241,4))
    checks['render_preserves_all_states']=all(f['render_preserves_states'] for f in capture['frames'])
    checks['native_images_match_saved_sha']=all(sha(Path(p))==h for f in capture['frames'] for p,h in f['image_sha256'].items())
    checks['capture_inputs_unchanged']=all(sha(Path(p))==h for p,h in capture['input_sha256'].items())
    checks['baseline_short_exact_to_previous']=read(PHASE/'short/baseline/report.json')['checks']['baseline_raw_exact']
    checks['v2_fix_preserves_three_raw']=all(read(PHASE/('hold_05s/seed120_palm_feedback/'+n+'.json'))==read(PHASE/('hold_05s/seed120_palm_feedback_v2/'+n+'.json')) for n in ('states','trace','contacts'))
    checks['cap030_half_second_three_raw_exact']=all(read(PHASE/('hold_05s/seed120_palm_cap030/'+n+'.json'))==read(PHASE/('hold_05s/seed120_palm_feedback_v2/'+n+'.json')) for n in ('states','trace','contacts'))
    for folder,short in (('hold_05s/baseline','short/baseline'),('hold_05s/seed120_preload050_hold','short/seed120_preload050_hold'),('hold_05s/seed120_palm_feedback','short/seed120_palm_feedback')):
        checks[folder+'_short_raw_and_normalized_controls_prefix']=raw_prefix(folder,short)
    for folder,short in (('hold_1s/baseline','hold_05s/baseline'),('hold_1s/seed120_palm_feedback_v2','hold_05s/seed120_palm_feedback_v2'),('hold_1s/seed120_palm_cap030','hold_05s/seed120_palm_cap030')):
        checks[folder+'_half_second_raw_and_normalized_controls_prefix']=raw_prefix(folder,short)
    metrics={}
    for name in ('baseline','seed120_palm_feedback_v2','seed120_palm_cap030'):
        folder=PHASE/'hold_1s'/name;report=read(folder/'report.json');states=read(folder/'states.json')
        poses=[];up=[]
        for state in states:
            points={n:np.array([body['pose']['p'][axis] for axis in 'xyz']) for n,body in zip(report['human_body_names'],state['human_body_states'])}
            poses.append(points['LH:palm'])
            normal=np.cross(points['LH:middle1']-points['L_Wrist'],points['LH:index1']-points['LH:pinky1'])
            up.append(float(normal[2]/np.linalg.norm(normal)))
        positive=[r['physics_step'] for r in read(folder/'lh_contacts.json') if r['contact']['lambda']>0]
        trace=read(folder/'trace.json')
        metrics[name]={'left_palm_end_world_displacement_mm':((poses[-1]-poses[0])*1000).tolist(),
            'left_palm_max_displacement_mm':float(max(np.linalg.norm(p-poses[0]) for p in poses)*1000),
            'palm_up_proxy_min_world_z':min(up),'palm_up_proxy_sign_anatomically_verified':False,
            'last_positive_lh_contact_step':max(positive) if positive else None,
            'max_torso_drift_deg':max(abs(a) for t in trace for a in t['torso_drift_deg']),
            'end_position_error_mm':trace[-1]['position_error_m']*1000,'end_rotation_error_deg':trace[-1]['rotation_error_deg']}
    before=read(Path('/tmp/stability2_environment_protected_before.json'))
    checks['original_87_files_size_mtime_unchanged']=all([Path(p).stat().st_size,Path(p).stat().st_mtime_ns]==v for p,v in before.items())
    aug=read(Path('/tmp/stability2_aug19_before.json'))
    checks['aug19_49_sha_unchanged']=all(sha(Path(p))==v for p,v in aug.items())
    frozen=[]
    for phase in ('best_run_video_v1','lower_body_fixed_v1','hand_hand_collision_audit_v1','thigh_palm_support_v1','self_collision_v1','isaac_gym_camera_v1'):
        manifest=read(PHASE.parent/phase/'source_final_manifest.json')
        frozen.extend(sha(Path(v['copy_path']))==v['sha256'] for v in manifest.values())
    checks['previous_frozen_sources_unchanged']=all(frozen)
    for phase in ('self_collision_v1','isaac_gym_camera_v1'):
        inventory=read(PHASE.parent/phase/'artifact_inventory.json')
        checks[phase+'_inventory_unchanged']=all(sha(Path(p))==v['sha256'] and Path(p).stat().st_size==v['size_bytes'] for p,v in inventory.items())
    init=10+24+24+len(reports)
    steps=24+sum(read(p)['physics_steps'] for p in reports)
    checks['native_accounting_79_init_1872_steps']=init==79 and steps==1872
    output.write_text(json.dumps({'checks':checks,'runtime_source_provenance':provenance,'one_second_motion_metrics':metrics,
        'native_initializations':init,'physics_steps':steps,'successful_stability_claim':False,
        'control_prefix_normalization':'old records lacked zero arm_static_bias_rad and empty palm_control; raw files untouched',
        'scope':'raw prefix, native render, source preservation and motion measurements; no cooked clearance certification'},indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'metrics':metrics,'native_initializations':init,'physics_steps':steps},indent=2))
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
