"""Audit the approved source proximity and explicitly coupled initial-length trials."""
import argparse
import hashlib
import json
from pathlib import Path

from .compare_pose_strap import load, summarize
from .search_hand_support import palm_neck_gap
from .replay_contact_geometry import recorded_probe
from .environment import np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    args = parser.parse_args()
    out = args.results_dir/'comparison.json'
    if out.exists():
        raise FileExistsError('preserve existing comparison')
    search = load(args.results_dir/'search_v2/search.json')
    coupling = load(args.results_dir/'coupling_inputs.json')
    audit = search['evaluations']+coupling['records']
    baseline = load(args.results_dir/'short/reference/report.json')
    target = np.array(baseline['initial_joint_targets_rad'])
    indices = [i for i,n in enumerate(baseline['human_joint_names']) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]
    rows = []
    for group in ('short','coupled_short','coupled_hold_05s'):
        for run in sorted((args.results_dir/group).iterdir()):
            row = summarize(run,baseline,audit)
            report,states,contacts = [load(run/(name+'.json')) for name in ('report','states','contacts')]
            initial = np.array(report['initial_joint_targets_rad'])
            changed = set(np.flatnonzero(initial!=target))
            row['checks']['initial_changes_within_approved_left_arm'] = changed<=set(indices) and bool(np.abs(initial-target).max()<=.3+2e-7)
            initial_gap = palm_neck_gap(recorded_probe(run,0))
            matches = [a for a in audit if a['settings']==row['settings']]
            row['checks']['initial_hull_query_matches_input'] = all(a['palm_neck']==initial_gap for a in matches)
            row['initial_palm_neck_hulls'] = initial_gap
            row['final_palm_neck_hulls'] = palm_neck_gap(recorded_probe(run,states[-1]['physics_step']))
            lh = [dict(physics_step=s['physics_step'],time_s=s['time_s'],body_pair=[c['body0_name'],c['body1_name']],raw_signed_feature_gap_m=c['initialOverlap'])
                for s in contacts for c in s['contacts'] if any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name']))
                and any(n.startswith('human/LH:') for n in (c['body0_name'],c['body1_name']))]
            row['left_hand_guitar_contact_row_count'] = len(lh)
            row['first_left_hand_contact'] = lh[0] if lh else None
            row['initial_arm_offsets_rad'] = {report['human_joint_names'][i]:float(initial[i]-target[i]) for i in indices}
            rows.append(row)
    historical = args.results_dir.parent/'pose_strap_v1/pose/reference'
    checks = {'search_contracts':all(search['checks'].values()),
        'reference_exactly_reproduces_previous':all(load(args.results_dir/'short/reference'/(name+'.json'))==load(historical/(name+'.json')) for name in ('states','contacts','trace','leg_torques')),
        'coupled_hold_short_prefix':all(load(Path(r['run'])/'states.json')[:25]==load(args.results_dir/'coupled_short'/r['name']/'states.json') and load(Path(r['run'])/'trace.json')[:25]==load(args.results_dir/'coupled_short'/r['name']/'trace.json') for r in rows if r['duration_s']>.1),
        'coupling_input_search_hash':coupling['source_search_sha256']==hashlib.sha256((args.results_dir/'search_v2/search.json').read_bytes()).hexdigest()}
    paths = list(args.results_dir.rglob('*.json'))+[Path(__file__).resolve(),Path(__file__).with_name('compare_pose_strap.py'),Path(__file__).with_name('search_hand_support.py'),Path(__file__).with_name('pose_strap_inputs.py'),Path(__file__).with_name('plot_neck_palm.py'),Path(__file__).with_name('replay_contact_geometry.py')]
    output = {'scope':'native hold diagnostics; left-arm source proximity only, no force support or stability success',
        'search_v1_status':'invalid wide-cutoff backend gap metric; preserved with original script/settings, never executed as native candidate',
        'search_v2_count':len(search['evaluations']),'checks':checks,'rows':rows,
        'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'runs':len(rows),'checks':checks,'failed_row_checks':{r['run']:[k for k,v in r['checks'].items() if not v] for r in rows if not all(r['checks'].values())}},indent=2))
    if not all(checks.values()) or not all(all(r['checks'].values()) for r in rows):
        raise SystemExit(1)


if __name__=='__main__':
    main()
