"""Prepare three absolute strap lengths at the saved native seed2 pose."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3'
PHASE = OLD.parent / 'seed2_strap_initial_v1'
TRIALS = ROOT / 'stability_adapter_2/trials/seed2_strap_initial_v1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def main():
    PHASE.mkdir(exist_ok=False); TRIALS.mkdir(exist_ok=False)
    path = OLD / 'analysis.json'; hashes = {str(path): sha(path)}; prior = read(path)
    paths = [Path(p) for p in prior['input_sha256']] + [Path(__file__).resolve(),
        ROOT / 'stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md', OLD / 'search.json',
        OLD / 'native/seed_2/initial_values.json', OLD / 'native/seed_2/initial_grip_audit.json',
        ROOT / 'stability_adapter_2/trials/multi_face_grip_v3/seed_2.json']
    hashes.update({str(p): sha(p) for p in paths})
    (PHASE / 'attempt.json').write_text(json.dumps({'input_sha256': hashes, 'native_initializations': 0, 'physics_steps': 0}, indent=2) + '\n')
    if not all(prior['checks'].values()) or any(sha(p) != h for p, h in prior['input_sha256'].items()):
        raise AssertionError('prior closure changed')
    initial = read(OLD / 'native/seed_2/initial_values.json'); audit = read(OLD / 'native/seed_2/initial_grip_audit.json')
    if not all(audit['checks'].values()): raise AssertionError('saved initial pose not admitted')
    grip = read(OLD / 'search.json'); route = initial['initial_route_length_m']
    base = initial['input_trial']; rows = []
    for label, length in (('current', initial['absolute_strap_rest_length_m']), ('taut', route), ('preload5n', route - 5 / 6000)):
        trial = copy.deepcopy(base); trial['initial_settings']['strap_rest_length_m'] = length
        path = TRIALS / (label + '.json'); path.write_text(json.dumps(trial, indent=2, allow_nan=False) + '\n')
        rows.append({'label': label, 'trial_path': str(path), 'trial_sha256': sha(path),
            'accepted_for_fresh_native': True, 'target_clearance_m': .001,
            'absolute_strap_rest_length_m': length, 'source_state': initial['native_initial_state']})
    checks = {'saved_seed2_pose_admitted': True, 'only_absolute_LA_changes': all(
        {**read(r['trial_path'])['initial_settings'], 'strap_rest_length_m': base['initial_settings']['strap_rest_length_m']} == base['initial_settings']
        and all(read(r['trial_path'])[k] == base[k] for k in base if k != 'initial_settings') for r in rows),
        'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()): raise AssertionError(checks)
    (PHASE / 'proposal.json').write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'rows': rows,
        'facets': grip['facets'], 'regions_G_m': grip['regions_G_m'], 'front_outer_source_z_G_m': grip['front_outer_source_z_G_m'],
        'seed2_angles_rad': initial['initial_PD_target_rad'], 'initial_route_length_m': route,
        'native_initializations': 0, 'physics_steps': 0,
        'scope': 'saved native pose reused to prepare LA-only candidates; fresh native geometry/q/route admission still required'}, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'lengths_m': {r['label']: r['absolute_strap_rest_length_m'] for r in rows}}, indent=2))


if __name__ == '__main__': main()
