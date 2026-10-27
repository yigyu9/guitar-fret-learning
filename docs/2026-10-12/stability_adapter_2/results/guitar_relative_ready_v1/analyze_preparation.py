"""Saved native preparation records only; never runs physics or policy."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parent
def load(path):
    return json.loads(path.read_text())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def streak(values):
    maximum = current = 0
    for value in values:
        current = current + 1 if value else 0
        maximum = max(maximum, current)
    return maximum

def main():
    output = ROOT/'analysis'
    output.mkdir(exist_ok=False)
    paths = [Path(__file__).resolve()]
    for version in ('native_v1','native_v2','native_v3','native_v4'):
        paths += [ROOT/version/'data'/name for name in ('report.json','controls.json','trace.json','initial_values.json','initial_audit.json')]
        paths += [ROOT/version/'inputs_after.json']
    paths += [ROOT/'search_v1/data/candidate_1.json',ROOT/'search_v1/data/report.json']
    before = {str(p):digest(p) for p in paths}
    (output/'inputs_before.json').write_text(json.dumps(before,indent=2)+'\n')
    summary = {}
    initial = []
    for version in ('native_v1','native_v2','native_v3','native_v4'):
        folder = ROOT/version/'data'
        controls,trace = load(folder/'controls.json'),load(folder/'trace.json')
        values,audit,report = [load(folder/name) for name in ('initial_values.json','initial_audit.json','report.json')]
        initial.append(values)
        conditions = {k:sum(r['readiness']['conditions'][k] for r in controls) for k in controls[0]['readiness']['conditions']}
        distances = [r['readiness']['pick_to_ready_m']*1000 for r in controls]
        target_errors = [np.linalg.norm(np.array(r['readiness']['pick_G_m'])-(np.array(r['readiness']['ready_G_m'])+[0,0,.03]))*1000 for r in controls]
        q0=np.array(values['initial_angles_rad'],dtype=np.float32)
        goals=np.array([r['final_targets_rad'] for r in controls],dtype=np.float32)
        lower,upper = [np.array(values[k],dtype=np.float32) for k in ('native_lower_rad','native_upper_rad')]
        names=values['joint_names']; right=[i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
        controlled=[i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))]
        other=np.setdiff1d(np.arange(81),controlled)
        computed_targets=[]
        for r in controls:
            t=trace[r['before_physics_step']//8] if r['before_physics_step']%8==0 else None
            if t:
                expected=np.array(t['position_W_m'])+Rotation.from_quat(t['quaternion_xyzw']).apply(np.array(r['readiness']['ready_G_m'])+[0,0,.03])
                computed_targets.append(np.linalg.norm(expected-r['readiness']['prep_target_W_m']))
        summary[version]={'report':report,'control_samples':len(controls),'condition_true_counts':conditions,
            'ready_frames':sum(r['readiness']['ready_now'] for r in controls),
            'longest_ready_streak':streak([r['readiness']['ready_now'] for r in controls]),
            'longest_palm_finger_streak':streak([all(r['readiness']['conditions'][k] for k in ('left_palm_under_neck_contact','left_finger_neck_contact')) for r in controls]),
            'palm_and_finger_frames':sum(all(r['readiness']['conditions'][k] for k in ('left_palm_under_neck_contact','left_finger_neck_contact')) for r in controls),
            'ready_distance_mm':{'min':min(distances),'max':max(distances),'last_control':distances[-1]},
            'stand_off_target_error_mm':{'initial':target_errors[0],'last_control':target_errors[-1],'max':max(target_errors)},
            'control_last_time_s':controls[-1]['time_s'],'physical_end_time_s':trace[-1]['time_s'],
            'guitar_change_mm_deg':{'end':[trace[-1]['position_change_m']*1000,trace[-1]['rotation_change_deg']],
                'max':[max(t['position_change_m'] for t in trace)*1000,max(t['rotation_change_deg'] for t in trace)]},
            'right_source_gap_mm':audit['right_hand_conservative_source_gap_m']*1000,
            'independent_checks':{'all_final_goals_within_native_bounds':bool(((goals>=lower)&(goals<=upper)).all()),
                'held_other36_exact':bool((goals[:,other]==q0[other]).all()),
                'max_goal_delta_rad':float(np.max(np.abs(np.diff(np.vstack([q0,goals]),axis=0)))),
                'right_goal_max_initial_delta_rad':float(np.max(np.abs(goals[:,right]-q0[right]))),
                'prepare_song_times':sorted(set(r['song_time_s'] for r in controls if r['phase']=='PREPARE')),
                'current_G_target_max_error_m':max(computed_targets),
                'closure':load(ROOT/version/'inputs_after.json')}}
    summary['identical_initial_native_state_PD'] = all(v['native_initial_state']==initial[0]['native_initial_state'] and v['PD_properties']==initial[0]['PD_properties'] for v in initial)
    candidate=load(ROOT/'search_v1/data/candidate_1.json')
    summary['search_target_error_mm']=candidate['preparation']['pick_target_error_m']*1000
    summary['search_ready_G_m']=candidate['preparation']['ready_G_m']
    summary['native_initial_ready_G_m']=load(ROOT/'native_v4/data/controls.json')[0]['readiness']['ready_G_m']
    summary['interpretation']='Search error uses search-selected lane; native uses its initial task-selected lane. The simultaneous preparation gate is not acquired; actual policy handoff or playing is not certified. Extra right joint PI is diagnostic only and rejected if worse than baseline.'
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    changed=[p for p,h in before.items() if digest(Path(p))!=h]
    (output/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    assert not changed

if __name__=='__main__':main()
