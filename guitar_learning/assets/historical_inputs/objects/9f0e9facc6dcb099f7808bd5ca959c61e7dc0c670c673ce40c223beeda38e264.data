"""Analyze saved free-guitar trials; step pulses are not complete-episode metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',type=Path,nargs='+',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    rows=[]
    for trial in args.trial:
        trial=trial.resolve();data=trial/'data';loaded={}
        for name in ('report','controls','trace','initial_values','checkpoint_connection'):
            p=data/(name+'.json');inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();loaded[name]=json.loads(p.read_text())
        p=trial/'inputs_after.json';inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();closure=json.loads(p.read_text())
        report=loaded['report'];controls=loaded['controls'];policy=[r for r in controls if r['actor_used']]
        def scalar(v):return float(np.array(v,dtype=float).sum())
        pulse={key:sum(scalar(r['info'].get(key,0)) for r in policy) for key in ('target_hit','physical_target_hit','physical_release','miss','wrong_crossing_count')}
        last=policy[-1]['info'] if policy else {}
        names=loaded['initial_values']['joint_names'];indices=[i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
        errors=[]
        for r in controls:
            sample=min(loaded['trace'],key=lambda s:abs(s['time_s']-r['time_s']))
            if abs(sample['time_s']-r['time_s'])>1e-6:continue
            actual=np.array([d['pos'] for d in sample['native_state']['human_dof_states']]);target=np.array(r['final_targets_rad'])
            errors.append({'time_s':r['time_s'],'max_right_arm_goal_actual_error_rad':float(np.max(abs(target[indices]-actual[indices])))})
        limited=[]
        for r in policy:
            if 'requested_targets_rad' in r:
                idx=[names.index(n) for n in names if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
                limited.append(int(np.count_nonzero(abs(np.array(r['requested_targets_rad'])[idx]-np.array(r['final_targets_rad'])[idx])>1e-7)))
        row={'trial':str(trial),'completed_5s':report['completed_5s'],'failure':report['failure'],'contract_checks':report['checks'],
             'closure':closure,'actor_steps':len(policy),'phase_end':report['phase_end'],'play_start_time_s':report['play_start_time_s'],
             'stop_reason':report['stop_reason'],'source_pulse_totals':pulse,
             'accepted_release_mask_total':sum(scalar(r['info'].get('accepted_release_mask',0)) for r in policy),
             'running_strike_f1_last':last.get('strike_f1'),'running_tip_ready_success_last':last.get('tip_ready_success_rate'),
             'source_action_motor_phases':sorted(set(int(v) for r in policy for v in np.array(r['info'].get('action_motor_phase',[])).flatten())),
             'region_true_control_samples':sum(r['guitar_in_playable_region'] for r in controls),
             'region_true_policy_samples':sum(r['guitar_in_playable_region'] for r in policy),
             'min_prepare_distance_m':min((r['readiness']['pick_to_ready_m'] for r in controls if not r['actor_used']),default=None),
             'min_policy_distance_m':min((r['readiness']['pick_to_ready_m'] for r in policy),default=None),
             'max_rotation_change_deg':max(s['rotation_change_deg'] for s in loaded['trace']),
             'max_position_change_mm':1000*max(s['position_change_m'] for s in loaded['trace']),
             'end_rotation_change_deg':loaded['trace'][-1]['rotation_change_deg'],
             'end_position_change_mm':1000*loaded['trace'][-1]['position_change_m'],
             'right_arm_error_at_sample':errors,'right_policy_clipped_joint_counts':limited,
             'checkpoint_connection':loaded['checkpoint_connection'],'video_paths':{k:v['path'] for k,v in report['videos'].items()},
             'interpretation':'5-second diagnostic. Pulses/running scores are not full-song certification; contact is measured, not mandatory.'}
        rows.append(row)
    (out/'inputs_before.json').write_text(json.dumps({'sha256':inputs},indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps({'trials':rows},indent=2)+'\n')
    changed=[p for p,h in inputs.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    (out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    if changed:raise RuntimeError(changed)
    for r in rows:print({k:r[k] for k in ('trial','actor_steps','source_pulse_totals','source_action_motor_phases','region_true_policy_samples','min_prepare_distance_m','min_policy_distance_m','max_rotation_change_deg')})


if __name__=='__main__':main()
