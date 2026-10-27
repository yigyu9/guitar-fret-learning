"""Audit this pose/strap batch from saved native states; no simulation or ranking score."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from .environment import np
from .control import control_indices
from .pose_strap_inputs import pose_metrics
from .replay_contact_geometry import recorded_probe
from .initial_overlap import query_pairs
from .trial_settings import source_hashes


def load(path):
    return json.loads(path.read_text())


def saved_hand(run, report, state):
    scene = SimpleNamespace(human=0, guitar=1,
        human_bodies=report['human_body_names'], guitar_bodies=report['guitar_body_names'],
        bodies=lambda actor: state['human_body_states'] if actor == 0 else state['guitar_body_states'])
    return pose_metrics(scene, recorded_probe(run, state['physics_step']))


def summarize(run, baseline, audits):
    report = load(run/'report.json')
    trace, states, contacts = [load(run/(name+'.json')) for name in ('trace', 'states', 'contacts')]
    main, torso = control_indices(report['human_joint_names'])
    q = np.array([[v['pos'] for v in s['human_dof_states']] for s in states])
    target = np.array(report['initial_joint_targets_rad'])
    lo, hi = np.array(report['native_joint_lower_rad']), np.array(report['native_joint_upper_rad'])
    legs = [report['human_joint_names'].index(n) for n in report['leg_torque_joint_names']]
    static = query_pairs(*recorded_probe(run, 0))
    initial_hand, final_hand = [saved_hand(run, report, s) for s in (states[0], states[-1])]
    matched = [a for a in audits if a['settings'] == report['initial_settings']]
    nonleg_contacts, lower_contacts = [], []
    for sample in contacts:
        for c in sample['contacts']:
            pair = [c['body0_name'], c['body1_name']]
            if not any(n.startswith('guitar/') for n in pair):
                continue
            human = next((n[6:] for n in pair if n.startswith('human/')), None)
            if human is None:
                continue
            rows = lower_contacts if human in {s+'_'+b for s in ('L','R') for b in ('Hip','Knee','Ankle','Toe')} else nonleg_contacts
            rows.append((sample['physics_step'], human))
    late = trace[len(trace)//2:]
    rms = lambda values: float(np.sqrt(np.mean(np.square(values))))
    checks = {'native_run_checks':all(report['checks'].values()),
        'saved_sample_counts':len(states)==len(trace)==report['physics_steps']+1 and len(contacts)==report['physics_steps'],
        'initial_settings_match_accepted_input':bool(matched) and all(a['accepted_for_diagnostic'] for a in matched),
        'initial_source_query_matches_input':bool(matched) and all(a['geometry']==static for a in matched),
        'initial_hand_metrics_match_input':bool(matched) and all(a['hand']==initial_hand for a in matched),
        'lower_initial_targets_unchanged':bool(np.array_equal(target[legs],np.array(baseline['initial_joint_targets_rad'])[legs])),
        'torso_initial_targets_unchanged':bool(np.array_equal(target[torso],np.array(baseline['initial_joint_targets_rad'])[torso])),
        'current_runtime_sources_match':report['source_sha256']==source_hashes()}
    for key in ('native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm',
                'native_joint_lower_rad','native_joint_upper_rad','physics_parameters',
                'guitar_goal_position_m','guitar_goal_quaternion_xyzw','source_sha256'):
        checks[key+'_unchanged'] = report[key]==baseline[key]
    row = {'run':str(run.resolve()), 'group':run.parent.name, 'name':run.name,
        'duration_s':trace[-1]['time_s'], 'settings':report['initial_settings'],
        'initial_route_length_m':report['initial_route_length_m'],
        'rest_length_m':report['absolute_rest_length_m'], 'initial_source_negative_pairs':static['negative_gap_pair_count'],
        'initial_hand':initial_hand, 'final_hand':final_hand,
        'max_position_error_m':max(s['position_error_m'] for s in trace),
        'max_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
        'rms_position_error_m':rms([s['position_error_m'] for s in trace]),
        'rms_rotation_error_deg':rms([s['rotation_error_deg'] for s in trace]),
        'late_rms_position_error_m':rms([s['position_error_m'] for s in late]),
        'late_rms_rotation_error_deg':rms([s['rotation_error_deg'] for s in late]),
        'end_position_error_m':trace[-1]['position_error_m'], 'end_rotation_error_deg':trace[-1]['rotation_error_deg'],
        'end_linear_speed_mps':trace[-1]['linear_speed_mps'], 'end_angular_speed_rad_s':trace[-1]['angular_speed_rad_s'],
        'first_applied_tension_n':trace[1]['last_applied_tension_n'],
        'max_applied_tension_n':max(s['last_applied_tension_n'] for s in trace[1:]),
        'tension_cap_sample_count':sum(s['last_applied_tension_n']>=300-1e-6 for s in trace[1:]),
        'max_main_raw_drift_deg':float(np.rad2deg(np.abs(q[:,main]-target[main])).max()),
        'max_main_scalar_limit_violation_deg':float(np.rad2deg(np.maximum(np.maximum(lo-q,q-hi)[:,main],0)).max()),
        'max_torso_raw_drift_deg':float(np.rad2deg(np.abs(q[:,torso]-target[torso])).max()),
        'max_leg_raw_drift_deg_observation_only':float(np.rad2deg(np.abs(q[:,legs]-target[legs])).max()),
        'nonleg_guitar_contact_row_count':len(nonleg_contacts),
        'nonleg_guitar_contact_bodies':sorted({body for _,body in nonleg_contacts}),
        'lower_guitar_contact_row_count_observation_only':len(lower_contacts),
        'checks':checks}
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,help='new comparison path; defaults to results-dir/comparison.json')
    args = parser.parse_args()
    out = args.out or args.results_dir/'comparison.json'
    if out.exists():
        raise FileExistsError('preserve existing comparison; use new batch')
    audit_paths = [args.results_dir/(phase+'_inputs.json') for phase in ('strap','pose')]
    audits = [load(path) for path in audit_paths]
    baseline = load(args.results_dir/'strap/legacy/report.json')
    rows = [summarize(run, baseline, [r for a in audits for r in a['records']])
        for group in ('strap','pose','hold_05s','hold_1s')
        for run in sorted((args.results_dir/group).iterdir()) if (run/'report.json').exists()]
    historical = args.results_dir.parent/'lower_initial_pose_v1/c02'
    checks = {'inputs_generated_without_source_changes':all(a['runtime_sources_unchanged'] for a in audits),
        'legacy_exactly_reproduces_c02':all(load(args.results_dir/'strap/legacy'/(n+'.json'))==load(historical/(n+'.json'))
            for n in ('states','contacts','trace','leg_torques')),
        'zero_preload_reference_exactly_reproduced':all(load(args.results_dir/'strap/load_00n'/(n+'.json'))==load(args.results_dir/'pose/reference'/(n+'.json'))
            for n in ('states','contacts','trace','leg_torques')),
        'long_trials_reproduce_short_prefix':all(load(Path(r['run'])/'states.json')[:25]==load(args.results_dir/('strap' if r['name'].startswith('load_') or r['name']=='legacy' else 'pose')/r['name']/'states.json')
            and load(Path(r['run'])/'trace.json')[:25]==load(args.results_dir/('strap' if r['name'].startswith('load_') or r['name']=='legacy' else 'pose')/r['name']/'trace.json') for r in rows if r['duration_s']>.1)}
    paths = list(args.results_dir.rglob('*.json'))+[Path(__file__).resolve(),Path(__file__).with_name('pose_strap_inputs.py'),Path(__file__).with_name('plot_neck_palm.py'),Path(__file__).with_name('replay_contact_geometry.py')]
    output = {'scope':'initial source/proxy gates and native hold diagnostics; lower quality excluded from ranking only; no feedback/stability/playing success',
        'late_window':'samples from index floor(N/2) through last sample',
        'contact_group_semantics':'nonleg includes Pelvis/Torso/Spine/Chest and arms/hands; counts are raw contact rows, not measured support force',
        'checks':checks,'rows':rows,
        'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'runs':len(rows),'checks':checks,'failed_row_checks':{r['run']:[k for k,v in r['checks'].items() if not v] for r in rows if not all(r['checks'].values())}},indent=2))
    if not all(checks.values()) or not all(all(r['checks'].values()) for r in rows):
        raise SystemExit(1)


if __name__=='__main__':
    main()
