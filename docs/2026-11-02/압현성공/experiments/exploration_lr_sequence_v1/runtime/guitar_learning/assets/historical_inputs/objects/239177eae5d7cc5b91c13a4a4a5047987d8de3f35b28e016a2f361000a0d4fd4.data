"""Audit finger-only native Fret and compare identical preparation with the baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    n=a.native.resolve();d=n/'data';b=a.baseline.resolve()/'data';out=a.out.resolve();out.mkdir(exist_ok=False)
    paths=[d/p for p in ('report.json','initial_values.json','terminal_info.json','controls.json','trace.json','images/capture.json','handoff_values.json')]+[n/'inputs_before.json',n/'inputs_after.json']+[b/p for p in ('report.json','controls.json','trace.json','images/capture.json')]+[Path(__file__).resolve()]
    hashes={str(p):sha(p) for p in paths};load=lambda p:json.loads(Path(p).read_text())
    report,initial,terminal,rows,trace,capture,handoff,inputs,after,old_report,old_rows,old_trace,old_capture=[load(p) for p in paths[:-1]]
    play=[r for r in rows if r['actor_used']];prep=[r for r in rows if not r['actor_used']]
    owners=initial['control_owners'];names=initial['joint_names'];indices=lambda key:[names.index(n) for n in owners[key]]
    left=indices('prepared_left9');fingers=indices('Fret21');policy=sorted(left+fingers);slots=[policy.index(i) for i in fingers]
    target=np.array(handoff['prepared_left_targets_rad']);checks={
        'runtime_checks':all(report['checks'].values()),'runtime_ok':report['failure'] is None,
        'input_closure':after['inputs_unchanged'] and all(sha(p)==h for p,h in inputs['sha256'].items()),
        'two_second_handoff':len(prep)==120 and play[0]['time_s']==handoff['time_s']==report['play_start_time_s']==2.,
        'ownership_partition':len(sum(owners.values(),[]))==len(set(sum(owners.values(),[])))==81,
        'prepared_left_targets_held':all(np.array_equal(np.array(r['submitted_targets_rad'])[left],target) for r in play),
        'source_finger_requests_exact':all(np.array_equal(np.array(r['requested_targets_rad'])[fingers],np.array(r['source_requested_policy_targets_rad'])[slots]) for r in play),
        'arm_requests_logged':all(len(r['source_requested_policy_targets_rad'])==30 for r in play),
        'one_transaction_per_control':report['physics_steps']==len(rows)*4,
        'source_frame_sequence':[r['source_frame_before'] for r in play]==[[i] for i in range(len(play))],
        'last_done_only':sum(r.get('source_done')==[True] for r in play)==1 and play[-1]['source_done']==[True],
        'terminal_info_exact':play[-1]['source_info']==terminal,
        'terminal_classification':terminal['failure_termination']==[True] or (terminal['goal_finished']==[True] and terminal['normal_termination']==[True]),
        'prepare_targets_exact':all(r['submitted_targets_rad']==old_rows[i]['submitted_targets_rad'] for i,r in enumerate(prep)),
        'prepare_native_states_exact':trace[:61]==old_trace[:61],
        'prepare_camera_bytes_exact':all(sorted(f['image_sha256'].values())==sorted(old_capture['frames'][i]['image_sha256'].values()) for i,f in enumerate(capture['frames'][:61])),
        'terminal_capture':capture['frames'][-1]['physics_step']==report['physics_steps'],
        'trace_camera_steps':[r['physics_step'] for r in trace]==[f['physics_step'] for f in capture['frames']],
        'render_readonly':all(f['render_preserves_states'] for f in capture['frames']),
        'png_sha':all(sha(p)==h for f in capture['frames'] for p,h in f['image_sha256'].items()),
        'video_sha':all(sha(v['path'])==v['sha256'] for v in report['videos'].values()),
        'video_frames_time':all(int(v['stream']['nb_read_frames'])==len(capture['frames']) and abs(float(v['stream']['duration'])-len(capture['frames'])/30)<.002 for v in report['videos'].values()),
        'no_learning_or_strike':report['learning_updates']==0 and report['Strike_actor_enabled'] is False}
    by_step={r['physics_step']:r for r in trace};old_by_step={r['physics_step']:r for r in old_trace};common=sorted(set(by_step)&set(old_by_step));last=common[-1]
    comparison={'last_common_time_s':last/240,'baseline_end_s':old_report['recorded_physics_duration_s'],
        'new_position_at_common_end_m':by_step[last]['position_change_m'],'old_position_at_common_end_m':old_by_step[last]['position_change_m'],
        'new_rotation_at_common_end_deg':by_step[last]['rotation_change_deg'],'old_rotation_at_common_end_deg':old_by_step[last]['rotation_change_deg'],
        'new_max_common_position_m':max(by_step[i]['position_change_m'] for i in common),
        'old_max_common_position_m':max(old_by_step[i]['position_change_m'] for i in common),
        'new_max_common_rotation_deg':max(by_step[i]['rotation_change_deg'] for i in common),
        'old_max_common_rotation_deg':max(old_by_step[i]['rotation_change_deg'] for i in common)}
    summary={'checks':checks,'input_count':after['input_count'],'actor_controls':len(play),'physics_duration_s':report['recorded_physics_duration_s'],
        'video_duration_s':float(report['videos']['whole_body']['stream']['duration']),'frame_count':len(capture['frames']),
        'source_goal_finished':terminal['goal_finished'],'source_failure':terminal['failure_termination'],
        'termination_true_fields':{k:v for k,v in terminal.items() if 'termination' in k and v==[True]},
        'press_success_rate':terminal['press_success_rate'],'sustain_success':terminal['sustain_event_success_count'],'sustain_count':terminal['sustain_event_count'],
        'max_position_change_m':max(r['position_change_m'] for r in trace),'max_rotation_change_deg':max(r['rotation_change_deg'] for r in trace),
        'final_position_change_m':trace[-1]['position_change_m'],'final_rotation_change_deg':trace[-1]['rotation_change_deg'],
        'same_time_comparison':comparison,'reference':'all guitar deltas from actual t=0; common sample comparison without interpolation',
        'recording_verified':all(checks.values()),'music_success_claimed':False,'stability_success_claimed':False}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    assert all(sha(p)==h for p,h in hashes.items())
    (out/'inputs.json').write_text(json.dumps({'sha256':hashes,'inputs_unchanged':True},indent=2)+'\n')
    assert all(checks.values()),checks
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
