"""Audit completed isolated Fret recording, without touching native outputs."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    n=a.native.resolve();d=n/'data';out=a.out.resolve();out.mkdir(exist_ok=False)
    paths=[d/p for p in ('report.json','initial_values.json','terminal_info.json','controls.json','trace.json','images/capture.json')]+[n/'inputs_before.json',n/'inputs_after.json',Path(__file__).resolve()]
    before={str(p):sha(p) for p in paths}
    load=lambda p:json.loads(Path(p).read_text())
    report,initial,terminal,rows,trace,capture=[load(p) for p in paths[:6]]
    prior=load(paths[6]);after=load(paths[7]);play=[r for r in rows if r['actor_used']];prep=[r for r in rows if not r['actor_used']]
    true=lambda k:terminal[k]==[True]
    false=lambda k:terminal[k]==[False]
    pngs={p:h for f in capture['frames'] for p,h in f['image_sha256'].items()}
    checks={'runtime_checks':all(report['checks'].values()),'no_runtime_failure':report['failure'] is None,
        'input_closure':after['inputs_unchanged'] and all(Path(p).is_file() and sha(p)==h for p,h in prior['sha256'].items()),
        'two_second_handoff':len(prep)==120 and play[0]['time_s']==2. and report['play_start_time_s']==2.,
        'source_frame_zero':play[0]['source_frame_before']==[0],
        'one_transaction_per_control':report['physics_steps']==len(rows)*4,
        'only_last_done':sum(r.get('source_done')==[True] for r in play)==1 and play[-1]['source_done']==[True],
        'consecutive_source_frames':[r['source_frame_before'] for r in play]==[[i] for i in range(len(play))],
        'failure_classified':true('failure_termination') and true('finger_back_termination') and false('goal_finished'),
        'no_press_success':all(r['source_info']['press_success_rate']==[0.] for r in play),
        'terminal_frame':[f['physics_step'] for f in capture['frames']]==list(range(0,report['physics_steps']+1,8)),
        'trace_camera_steps':[r['physics_step'] for r in trace]==[f['physics_step'] for f in capture['frames']],
        'render_readonly':all(f['render_preserves_states'] for f in capture['frames']),
        'png_hashes':all(sha(p)==h for p,h in pngs.items()),
        'video_hashes':all(sha(v['path'])==v['sha256'] for v in report['videos'].values()),
        'video_frames_time':all(int(v['stream']['nb_read_frames'])==len(capture['frames']) and abs(float(v['stream']['duration'])-len(capture['frames'])/30)<.002 for v in report['videos'].values()),
        'no_learning_or_strike':report['learning_updates']==0 and report['Strike_actor_enabled'] is False}
    handoff=next(r for r in trace if r['time_s']==2.)
    contacts=[]
    for r in rows:
        for c in r['native_contacts']:
            names=[c['body0_name'],c['body1_name']]
            if any('/LH:' in s for s in names) and any('/G:' in s for s in names):
                contacts.append({'time_s':r['time_s'],'phase':r['phase'],'body0':names[0],'body1':names[1],'raw_lambda':c.get('lambda')})
    summary={'scope':'isolated free-guitar native Fret transfer; not original fixed-guitar evaluation',
        'checks':checks,'input_count':after['input_count'],'preparation_controls':len(prep),'actor_controls':len(play),
        'physics_duration_s':report['recorded_physics_duration_s'],'video_duration_s':float(report['videos']['whole_body']['stream']['duration']),
        'frame_count':len(capture['frames']),'handoff_position_change_m':handoff['position_change_m'],
        'handoff_rotation_change_deg':handoff['rotation_change_deg'],'final_position_change_m':trace[-1]['position_change_m'],
        'final_rotation_change_deg':trace[-1]['rotation_change_deg'],
        'max_position_change_m':max(r['position_change_m'] for r in trace),'max_rotation_change_deg':max(r['rotation_change_deg'] for r in trace),
        'handoff_max_actual_profile_excess_rad':max(play[0]['actual_profile_excess_rad']),
        'source_finger_back_termination_by_finger':terminal['finger_back_termination_by_finger'],
        'press_success_rate':terminal['press_success_rate'],'sustain_event_success_count':terminal['sustain_event_success_count'],
        'sustain_event_count':terminal['sustain_event_count'],'terminal_mean_target_distance_m':terminal['mean_target_distance'],
        'LH_guitar_contact_samples':contacts,'contact_scope':'60Hz native candidate rows; raw lambda not converted to N; not continuous contact certificate',
        'checkpoint_asset_changes':initial['checkpoint_asset_changes'],'checkpoint_implementation_changes':initial['checkpoint_implementation_changes'],
        'recording_verified':all(checks.values()),'music_success':False,'stability_success':False}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    unchanged=all(sha(p)==h for p,h in before.items());assert unchanged
    (out/'inputs.json').write_text(json.dumps({'sha256':before,'inputs_unchanged':unchanged},indent=2)+'\n')
    assert all(checks.values()),checks
    print(json.dumps({k:v for k,v in summary.items() if k not in ('LH_guitar_contact_samples','checkpoint_implementation_changes')},indent=2))


if __name__=='__main__':main()
