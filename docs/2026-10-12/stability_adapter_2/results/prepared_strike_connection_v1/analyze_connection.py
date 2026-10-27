"""Analyze saved prepared-pose policy connection; no simulation or actor calls."""
from pathlib import Path
import hashlib
import json
import numpy as np

P=Path(__file__).resolve().parent
BASE=P.parent/'guitar_relative_ready_v1/native_v4/data'
def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    output=P/'analysis';output.mkdir(exist_ok=False)
    native=P/'native/data'
    paths=[Path(__file__).resolve(),*[native/n for n in ('controls.json','trace.json','report.json','initial_values.json','checkpoint_connection.json')],
           P/'native/inputs_after.json',BASE/'trace.json',BASE/'controls.json',BASE/'initial_values.json']
    before={str(p):sha(p) for p in paths}
    (output/'inputs_before.json').write_text(json.dumps(before,indent=2)+'\n')
    r,t,report,initial,connection=[load(native/n) for n in ('controls.json','trace.json','report.json','initial_values.json','checkpoint_connection.json')]
    baseline=load(BASE/'trace.json');baseline_controls=load(BASE/'controls.json')
    policy=[c for c in r if c['actor_used']];hold=[c for c in r if c['phase']=='HOLD']
    start=next((c for c in r if c.get('handoff')),None)
    previous=next((c for c in reversed(r) if c['phase']=='PREPARE'),None)
    terminal=next((c for c in policy if c.get('done')),None)
    names=initial['joint_names'];indices=[i for i,n in enumerate(names) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
    lower,upper=[np.array(initial[k],dtype=np.float32)[indices] for k in ('native_lower_rad','native_upper_rad')]
    mid=np.float32(.5)*(lower+upper);half=np.float32(.5)*(upper-lower)
    history_error=max(float(np.max(np.abs(np.clip((np.array(c['final_targets_rad'],dtype=np.float32)[indices]-mid)/half,-1,1)-np.array(c['source_history'][0],dtype=np.float32)))) for c in r)
    summary={'report':report,'checkpoint_connection':connection,'policy_control_steps':len(policy),
        'policy_physics_duration_s':len(policy)/60,
        'policy_first_time_s':policy[0]['time_s'] if policy else None,
        'policy_last_end_time_s':policy[-1]['after_physics_step']/240 if policy else None,
        'terminal_physics_step':terminal['after_physics_step'] if terminal else None,
        'terminal_episode_info':{k:v for k,v in terminal['info'].items() if k in ('strike_episode_f1','strike_true_positive_count','strike_false_positive_count','strike_false_negative_count')} if terminal else None,
        'handoff_readiness':start['readiness'] if start else None,
        'handoff_region_ok':start['guitar_in_playable_region'] if start else None,
        'handoff_targets_continuous':bool(start and previous and all(abs(a-b)<=.8/60+2e-7 for a,b in zip(start['final_targets_rad'],previous['final_targets_rad']))),
        'initial_native_PD_exact_baseline':initial['native_initial_state']==load(BASE/'initial_values.json')['native_initial_state'] and initial['PD_properties']==load(BASE/'initial_values.json')['PD_properties'],
        'preparation_native_prefix_exact':len([c for c in t if c['time_s']<=2])==61 and len([c for c in baseline if c['time_s']<=2])==61 and all(a==b for a,b in zip([c for c in t if c['time_s']<=2], [c for c in baseline if c['time_s']<=2])),
        'preparation_goal_prefix_exact':all(c['final_targets_rad']==baseline_controls[i]['final_targets_rad'] for i,c in enumerate(r) if c['phase']=='PREPARE'),
        'history_inverse_max_error':history_error,
        'guitar_change_mm_deg':{'max':[max(c['position_change_m'] for c in t)*1000,max(c['rotation_change_deg'] for c in t)],'end':[t[-1]['position_change_m']*1000,t[-1]['rotation_change_deg']]},
        'region_true_control_samples':sum(c['guitar_in_playable_region'] for c in r),
        'region_true_policy_samples':sum(c['guitar_in_playable_region'] for c in policy),
        'strict_preparation_true_policy_samples':sum(c['strict_preparation_met'] for c in policy),
        'left_palm_contact_policy_samples':sum(c['readiness']['conditions']['left_palm_under_neck_contact'] for c in policy),
        'left_finger_contact_policy_samples':sum(c['readiness']['conditions']['left_finger_neck_contact'] for c in policy),
        'hold_samples':len(hold),'hold_clock_values':sorted(set(c['song_time_s'] for c in hold)),
        'hold_final_goal_history_exact':bool(not hold or all(c['final_targets_rad']==hold[0]['final_targets_rad'] and c['source_history']==hold[0]['source_history'] for c in hold)),
        'controls':len(r),'physics_steps':report['physics_steps'],'learning_updates':0,
        'interpretation':'Actual frozen Strike connection diagnostic. Strict palm support was not certified; HOLD is physics-only recording after policy stop.'}
    assert policy and start and report['completed_5s'] and summary['initial_native_PD_exact_baseline']
    assert summary['preparation_native_prefix_exact'] and summary['preparation_goal_prefix_exact']
    assert history_error==0 and summary['handoff_targets_continuous'] and summary['hold_final_goal_history_exact']
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    changed=[p for p,h in before.items() if sha(Path(p))!=h]
    (output/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    assert not changed

if __name__=='__main__':main()
