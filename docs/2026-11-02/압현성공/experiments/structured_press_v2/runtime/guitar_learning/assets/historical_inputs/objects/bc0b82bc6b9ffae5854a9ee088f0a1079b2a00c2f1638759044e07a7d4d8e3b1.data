"""Read-only evidence analysis of current-G response and terminated native transfer."""
from pathlib import Path
import json
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1'


def main():
    out = PHASE/'analysis'; out.mkdir(exist_ok=False)
    trial = PHASE/'native_v2/trial'
    paths = [trial/n for n in ('report.json', 'trace.json', 'controls.json', 'initial_values.json', 'counterfactual.json', 'attempt.json', 'images/capture.json', 'images/videos.json')]
    paths += [PHASE/'native_v1/controls.json', PHASE/'native_v1/trace.json', PHASE/'native_v1/report.json',
              PHASE/'native_v2/inputs_before.json', PHASE/'native_v2/inputs_after.json', Path(__file__).resolve()]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    def read(p): return json.loads(p.read_text())
    report, trace, controls, initial, probe = [read(trial/n) for n in ('report.json','trace.json','controls.json','initial_values.json','counterfactual.json')]
    old_controls = read(PHASE/'native_v1/controls.json')
    old_trace = read(PHASE/'native_v1/trace.json')
    # Exactly compare actor input/output/final goal/history through policy termination.
    prefix = len(controls) == len(old_controls) and all(a == b for a,b in zip(controls, old_controls))
    native_prefix = all(all(r[k] == s[k] for k in ('position_W_m','quaternion_xyzw','position_change_m','rotation_change_deg'))
        for r in trace if r['physics_step'] < report['policy_end_physics_step']
        for s in old_trace if s['physics_step'] == r['physics_step'])
    names = initial['joint_names']; indices = [i for i,n in enumerate(names) if n.startswith(('R_Shoulder','R_Elbow','R_Wrist','RH:'))]
    lower = np.array(initial['native_lower_rad'])[indices]; upper = np.array(initial['native_upper_rad'])[indices]
    mid, half = (lower+upper)/2, (upper-lower)/2
    inverse_error = max(np.max(abs(np.array(r['history'])[0] - (np.array(r['final_targets_rad'])[indices]-mid)/half)) for r in controls)
    history_error = max(np.max(abs(np.array(r['observation'])[0,-30:] - np.array(prev['history'])[0])) for prev,r in zip(controls,controls[1:]))
    tip = [r['info']['tip_target_distance'][0] for r in controls]
    end = controls[-1]['info']
    last_window = [s for s in trace if s['time_s']>=2]
    data = {'physics_steps': report['physics_steps'], 'policy_steps': len(controls),
        'policy_end_time_s': report['policy_end_time_s'], 'post_termination_passive_only': report['post_termination_passive_only'],
        'completed_5s_physics_recording': report['completed_requested_5s'], 'checks': report['checks'],
        'preservation_wrapper': read(PHASE/'native_v2/inputs_after.json'),
        'policy_prefix_exact_reproduction': prefix, 'sampled_native_prefix_exact_reproduction': native_prefix,
        'actual_goal_history_inverse_max_error': float(inverse_error), 'next_observation_history_max_error': float(history_error),
        'max_RH_target_step_rad': max(r['max_RH_target_step_rad'] for r in controls),
        'tip_target_distance_first_post_step_m': tip[0], 'tip_target_distance_terminal_m': tip[-1],
        'tip_target_distance_min_post_step_m': min(tip),
        'terminal_metrics': {k: end[k][0] for k in ('strike_f1','strike_true_positive_count','strike_false_positive_count','strike_false_negative_count','grip_quality','entry_distance_m')},
        'terminal_reasons': report['terminal_reasons'],
        'max_position_change_m_all_5s': max(s['position_change_m'] for s in trace),
        'max_rotation_change_deg_all_5s': max(s['rotation_change_deg'] for s in trace),
        'final_position_change_m': trace[-1]['position_change_m'], 'final_rotation_change_deg': trace[-1]['rotation_change_deg'],
        'final_position_W_m': trace[-1]['position_W_m'],
        '2s_reference_max_translation_m': float(max(np.linalg.norm(np.array(s['position_W_m'])-last_window[0]['position_W_m']) for s in last_window)),
        'counterfactual': [{k:v for k,v in c.items() if k not in ('observation','actor_action')} for c in probe['cases']],
        'scope': 'single fixed checkpoint, current horizontal no-strap pose, changed native PD/rate cap; no learning; current-G update verified but playing failed',
        'passive_monitor_limits': 'after termination: q/qd/G state finite, qd<50, root/lower fixed, constant targets; no continued source geometry penetration/irrecoverable monitor or upper-body pose-finite gate',
        'input_sha256': hashes}
    assert prefix and native_prefix and history_error == 0 and inverse_error < 2e-6
    assert report['failure'] is None and all(report['checks'].values())
    assert data['preservation_wrapper']['inputs_unchanged'] and data['completed_5s_physics_recording']
    assert data['max_RH_target_step_rad'] <= .8/60+1e-7
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (out/'summary.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ('input_sha256','terminal_reasons','checks')}))


if __name__ == '__main__': main()
