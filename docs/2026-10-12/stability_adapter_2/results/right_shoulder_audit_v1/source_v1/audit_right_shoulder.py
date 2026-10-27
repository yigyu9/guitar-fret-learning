"""Read-only source-hull audit of existing native shoulder-contact records."""
import argparse
import hashlib
import json
from pathlib import Path

from .search_hand_support import palm_neck_gap
from .replay_contact_geometry import recorded_probe
from .trial_settings import source_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve existing audit')
    comparison = json.loads((args.results_dir/'comparison_v2.json').read_text())
    paths = [args.results_dir/'comparison_v2.json',Path(__file__).resolve(),
        Path(__file__).with_name('search_hand_support.py'),Path(__file__).with_name('replay_contact_geometry.py'),
        Path(__file__).with_name('plot_neck_palm.py')]
    for name in ('reference','candidate_01'):
        paths += list((args.results_dir/'short'/name).glob('*.json'))
    hashes = source_hashes()
    hashes.update({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    rows = []
    checks = {'complete_body_pairs':True,'initial_rh_matches_previous':True,'solver_feasible':True}
    for name in ('reference','candidate_01'):
        run = args.results_dir/'short'/name
        archived = next(r for r in comparison['rows'] if r['name']==name)
        for step in (0,3,4,24):
            model,data,shapes = recorded_probe(run,step)
            for human in ('R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:palm'):
                human_shapes = [s for s in shapes if s['actor']=='human' and s['body']==human]
                for guitar in ('G:body','guitar'):
                    guitar_shapes = [s for s in shapes if s['actor']=='guitar' and s['body']==guitar]
                    if not human_shapes or not guitar_shapes:
                        raise AssertionError('missing active source shape: '+human+'/'+guitar)
                    pairs = []
                    for shape in human_shapes:
                        selected = [s for s in shapes if not (s['actor']=='human' and s['body']==human)] + [shape]
                        pairs.append(palm_neck_gap((model,data,selected),human,guitar))
                    closest = min(pairs,key=lambda r:r['source_hull_distance_m'])
                    row = {'run':str(run.resolve()),'name':name,'physics_step':step,'time_s':step/240,
                        'human_body':human,'guitar_body':guitar,'human_geom_count':len(human_shapes),
                        'guitar_geom_count':len(guitar_shapes),'closest':closest,'per_human_geom_queries':pairs}
                    rows.append(row)
                    checks['solver_feasible'] &= all(r['solver_feasibility_error_m']<=1e-7 for r in pairs)
                    if step==0 and human=='RH:palm' and guitar=='G:body':
                        checks['initial_rh_matches_previous'] &= closest==archived['initial_right_palm_body_hulls']
    checks['complete_body_pairs'] = len(rows)==80
    checks['inputs_and_sources_unchanged'] = all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in hashes.items())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'scope':'stored source-shape diagnostic only; no native rollout or contact/clearance certification',
        'checks':checks,'source_sha256':hashes,'rows':rows},indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'body_pairs':len(rows)},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
