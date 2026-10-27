"""Audit saved right-arm initial-pose trials without rerunning native physics."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter

from .compare_pose_strap import load, summarize, saved_hand
from .search_hand_support import palm_neck_gap
from .replay_contact_geometry import recorded_probe
from .environment import np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--reference-run',type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve prior comparison')
    search = load(args.results_dir/'search/search.json')
    baseline = load(args.results_dir/'short/reference/report.json')
    target = np.array(baseline['initial_joint_targets_rad'])
    right = [i for i,n in enumerate(baseline['human_joint_names']) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
    other = [i for i in range(len(target)) if i not in right]
    rows = []
    for group in ('short','hold_05s','hold_1s'):
        for run in sorted((args.results_dir/group).glob('*')):
            if not (run/'report.json').exists():
                continue
            row = summarize(run,baseline,search['evaluations'])
            report,states,contacts = [load(run/(n+'.json')) for n in ('report','states','contacts')]
            q0 = np.array(report['initial_joint_targets_rad'])
            row['checks']['only_right_arm_initial_targets_changed'] = bool(np.array_equal(q0[other],target[other]) and (np.abs(q0[right]-target[right])<=.3+2e-7).all())
            row['checks']['absolute_length_unchanged'] = report['absolute_rest_length_m']==baseline['absolute_rest_length_m']
            row['checks']['initial_route_length_unchanged'] = report['initial_route_length_m']==baseline['initial_route_length_m']
            initial_gap = palm_neck_gap(recorded_probe(run,0),'RH:palm','G:body')
            matched = [r for r in search['evaluations'] if r['settings']==report['initial_settings']]
            row['checks']['initial_right_hull_matches_search'] = bool(matched) and all(r['palm_neck']==initial_gap for r in matched)
            row['initial_right_palm_body_hulls'] = initial_gap
            row['final_right_palm_body_hulls'] = palm_neck_gap(recorded_probe(run,states[-1]['physics_step']),'RH:palm','G:body')
            counts = Counter()
            for sample in contacts:
                for c in sample['contacts']:
                    pair = (c['body0_name'],c['body1_name'])
                    if any(n.startswith('guitar/') for n in pair):
                        for n in pair:
                            if n.startswith('human/'):
                                counts[n] += 1
            row['guitar_contact_rows_by_human_body'] = dict(counts)
            row['min_left_palm_up_dot_all_physics_samples'] = min(saved_hand(run,report,s)['palm_up_dot'] for s in states)
            rows.append(row)
    historical = args.reference_run or args.results_dir.parent/'joint_hold_v1/short/off'
    checks = {'search_contracts':all(search['checks'].values()),
        'reference_exactly_reproduces_previous_off':all(load(args.results_dir/'short/reference'/(n+'.json'))==load(historical/(n+'.json')) for n in ('states','trace','contacts','leg_torques'))}
    long_rows = [r for r in rows if r['duration_s']>.1]
    if long_rows:
        checks['long_trials_reproduce_short_prefix'] = all(load(Path(r['run'])/'states.json')[:25]==load(args.results_dir/'short'/r['name']/'states.json') and load(Path(r['run'])/'trace.json')[:25]==load(args.results_dir/'short'/r['name']/'trace.json') for r in long_rows)
    paths = sorted(args.results_dir.rglob('*.json'))+[Path(__file__).resolve(),Path(__file__).with_name('search_hand_support.py'),Path(__file__).with_name('compare_pose_strap.py')]
    output = {'scope':'right-arm initial pose, held native PD, fixed strap; no feedback or stability success',
        'search_count':len(search['evaluations']),'checks':checks,'rows':rows,
        'long_trial_count':len(long_rows),'long_prefix_status':'checked' if long_rows else 'not_applicable_no_long_runs',
        'geometry_semantics':'RH:palm/G:body unsigned source hull; palm_neck search key retained for compatibility. Upward gate/tie-break uses LH proxy only. Contact counts are not support force.',
        'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    args.out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'failed_rows':{r['run']:[k for k,v in r['checks'].items() if not v] for r in rows if not all(r['checks'].values())},
        'rows':[{k:r[k] for k in ('name','duration_s','max_position_error_m','max_rotation_error_deg','max_main_raw_drift_deg','guitar_contact_rows_by_human_body')} for r in rows]},indent=2))
    if not all(checks.values()) or not all(all(r['checks'].values()) for r in rows):
        raise SystemExit(1)


if __name__=='__main__':
    main()
