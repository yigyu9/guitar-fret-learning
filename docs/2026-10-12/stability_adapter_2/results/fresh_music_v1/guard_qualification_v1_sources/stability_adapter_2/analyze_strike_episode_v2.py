"""Summarize a variable-length recorded Strike episode without changing raw inputs."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    trial=args.trial.resolve();out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    paths={name:trial/'data'/(name+'.json') for name in ('report','controls','trace','initial_values','checkpoint_connection')}
    paths['closure']=trial/'inputs_after.json'
    paths['capture']=trial/'data/images/capture.json'
    inputs={str(p):sha(p) for p in [Path(__file__).resolve()]+list(paths.values())}
    (out/'inputs_before.json').write_text(json.dumps({'sha256':inputs},indent=2)+'\n')
    data={name:json.loads(p.read_text()) for name,p in paths.items()}
    report,controls,trace=data['report'],data['controls'],data['trace']
    actor_rows=[r for r in controls if r['actor_used']]
    policy=[r for r in actor_rows if 'info' in r]
    summary={'trial':str(trial),'failure':report['failure'],'checks':report['checks'],
        'completed_recording':report['completed_recording'],'episode_outcome':report['episode_outcome'],
        'stop_reason':report['stop_reason'],'terminal_reasons':report['terminal_reasons'],
        'play_start_time_s':report['play_start_time_s'],'physics_duration_s':report['recorded_physics_duration_s'],
        'physics_steps':report['physics_steps'],'actor_steps':len(actor_rows),'completed_actor_steps':len(policy),'incomplete_actor_steps':len(actor_rows)-len(policy),
        'phase_control_counts':{p:sum(r['phase']==p for r in controls) for p in sorted(set(r['phase'] for r in controls))},
        'source_pulse_totals':{k:sum(sum(r['info'].get(k,[0])) for r in policy) for k in ('target_hit','physical_target_hit','physical_release','miss','wrong_crossing_count')},
        'right_contact_control_samples':sum(not r['readiness']['conditions']['right_noncontact'] for r in controls),
        'max_position_change_mm':1000*max(r['position_change_m'] for r in trace),
        'max_rotation_change_deg':max(r['rotation_change_deg'] for r in trace),
        'end_position_change_mm':1000*trace[-1]['position_change_m'],'end_rotation_change_deg':trace[-1]['rotation_change_deg'],
        'frame_count':len(data['capture']['frames']),'last_frame_physics_step':data['capture']['frames'][-1]['physics_step'],
        'videos':report['videos'],'input_closure':data['closure'],
        'interpretation':'Recording completion and source goal_finished do not certify all-note accuracy or checkpoint transfer success.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    changed=[p for p,h in inputs.items() if sha(Path(p))!=h]
    (out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    if changed:raise RuntimeError('analysis inputs changed: '+str(changed))
    print({k:summary[k] for k in ('episode_outcome','play_start_time_s','physics_duration_s','source_pulse_totals')})


if __name__=='__main__':main()
