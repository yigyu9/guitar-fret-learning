"""Read-only comparison of diagnostic native point/wrist teacher variants."""
import json
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parents[1]

def main():
    comparisons={}
    for name in ('teacher_fixed_B','teacher_fixed_B_wrist','teacher_fixed_B_wrist_normal_guard'):
        folder=BASE/name
        report=json.loads((folder/'report.json').read_text())
        data=np.load(folder/'teacher_trace60.npz')
        entry=dict(completed=report['completed'],wall_s=report['wall_s'],
            changed_inputs=report['changed_inputs'],scene_closed=report['scene']['closed'],
            physical_failures=sum(g['failure'] is not None for g in report['goals']),
            trace_finite=all(bool(np.isfinite(data[k]).all()) for k in data.files),
            max_requested_step_deg=float(np.rad2deg(np.abs(data['requested_delta16_rad']).max())),goals=[])
        for row,goal in enumerate(report['goals']):
            item=dict(row=row,finger=goal['finger'],string=goal['physical_string'],fret=goal['fret'],
                hold_candidate_s=goal['best_hold_contact_streak_s'],any_phase_candidate_s=goal['best_static_contact_streak_s'],
                wrist_shadow_first_s=goal['wrist_shadow_failure_time_s'],
                correction_active_fraction=float(data['active'][:,row].mean()),
                max_body_resultant_n=float(data['body_force_n'][:,row].max()),
                last_point_error_mm=float(np.linalg.norm(data['point_error_world_m'][-1,row])*1000))
            if 'wrist_error_world_m' in data:
                item.update(last_wrist_target_error_mm=float(np.linalg.norm(data['wrist_error_world_m'][-1,row])*1000),
                    last_wrist_guide_excess_max_mm=float(np.abs(data['wrist_guide_excess_G_m'][-1,row]).max()*1000))
            if 'high_force' in data:
                selected=data['high_force'][:,row]
                guarded=data['predicted_normal_target_step_after_m'][selected,row]
                item.update(high_force_fraction=float(selected.mean()),
                    fallback_fraction=float(data['normal_guard_fallback'][:,row].mean()),
                    min_high_force_predicted_outward_step_m=float(guarded.min()) if len(guarded) else None,
                    largest_removed_inward_error_mm=float(-data['removed_inward_error_m'][:,row].min()*1000))
            entry['goals'].append(item)
        if 'high_force' in data:
            guarded=data['predicted_normal_target_step_after_m'][data['high_force']]
            entry['high_force_linearized_target_guard_passed']=bool((guarded>=-1.01e-9).all())
            entry['guarded_step_min_m']=float(guarded.min()) if len(guarded) else None
        comparisons[name]=entry
    output=dict(scope='Static diagnostic only; not song ledger or learned success. High-force normal guard constrains instantaneous linearized smoothed target motion, not actual dynamic penetration.',comparisons=comparisons)
    (BASE/'support/normal_guard_comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    for name,entry in comparisons.items():
        print(name,entry['completed'],entry['physical_failures'],entry.get('high_force_linearized_target_guard_passed'))
        for goal in entry['goals']:
            if goal['hold_candidate_s']>=.05 or goal['row'] in (6,12):print(goal)

if __name__=='__main__':main()
