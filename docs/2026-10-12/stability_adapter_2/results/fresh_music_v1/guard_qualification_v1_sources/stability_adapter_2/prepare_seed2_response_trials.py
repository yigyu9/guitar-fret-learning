"""Prepare six single-axis target probes with the saved native seed2 initial state."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1'
PHASE = OLD.parent / 'seed2_guitar_response_v1'
TRIALS = ROOT / 'stability_adapter_2/trials/seed2_guitar_response_v1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def main():
    PHASE.mkdir(exist_ok=False); TRIALS.mkdir(exist_ok=False)
    path = OLD / 'analysis.json'; hashes = {str(path): sha(path)}; prior = read(path)
    paths = [Path(p) for p in prior['input_sha256']] + [Path(__file__).resolve(),
        ROOT / 'stability_adapter_2/SEED2_GUITAR_RESPONSE_PLAN.md', OLD / 'proposal.json',
        OLD / 'native/full/initial_values.json', OLD / 'native/full/initial_grip_audit.json',
        ROOT / 'stability_adapter_2/trials/seed2_startup_target_v1/full.json']
    hashes.update({str(p): sha(p) for p in paths})
    (PHASE / 'attempt.json').write_text(json.dumps({'input_sha256': hashes, 'native_initializations': 0, 'physics_steps': 0}, indent=2) + '\n')
    if not all(prior['checks'].values()) or any(sha(p) != h for p, h in prior['input_sha256'].items()):
        raise AssertionError('prior closure changed')
    initial = read(OLD / 'native/full/initial_values.json'); audit = read(OLD / 'native/full/initial_grip_audit.json')
    if not all(audit['checks'].values()): raise AssertionError('saved initial pose not admitted')
    grip = read(OLD / 'proposal.json'); base = initial['input_trial']; bias = base['main_target_offsets_rad']
    names = {f'L_{joint}_{axis}' for joint in ('Thorax', 'Shoulder', 'Elbow', 'Wrist') for axis in 'xyz'}
    if set(bias) != names: raise AssertionError('exact left arm12 startup offsets required')
    axes = [f'L_{joint}_{axis}' for joint in ('Shoulder','Wrist') for axis in 'xyz']
    rows = []
    for label, residual in [('base', {})] + [(n[2:].lower(), {n:.002}) for n in axes]:
        trial = copy.deepcopy(base)
        for n,v in residual.items(): trial['main_target_offsets_rad'][n] += v
        if any(abs(v)>.3 for v in trial['main_target_offsets_rad'].values()): raise AssertionError('diagnostic offset bound')
        for n,v in trial['main_target_offsets_rad'].items():
            k=initial['human_joint_names'].index(n); target=initial['initial_PD_target_rad'][k]+v
            if not initial['PD_properties']['lower'][k] <= target <= initial['PD_properties']['upper'][k]: raise AssertionError('native target bound')
        path = TRIALS / (label + '.json'); path.write_text(json.dumps(trial, indent=2, allow_nan=False) + '\n')
        rows.append({'label': label, 'target_residual_rad': residual, 'trial_path': str(path), 'trial_sha256': sha(path),
            'accepted_for_fresh_native': True, 'target_clearance_m': .001,
            'absolute_strap_rest_length_m': initial['absolute_strap_rest_length_m'], 'source_state': initial['native_initial_state']})
    checks = {'saved_seed2_pose_admitted': True, 'only_declared_sixaxis_target_residual_changes': all(
        {**read(r['trial_path']), 'main_target_offsets_rad': bias} == base
        and read(r['trial_path'])['main_target_offsets_rad'] == {n: v+r['target_residual_rad'].get(n,0.) for n,v in bias.items()} for r in rows),
        'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()): raise AssertionError(checks)
    (PHASE / 'proposal.json').write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'rows': rows,
        'facets': grip['facets'], 'regions_G_m': grip['regions_G_m'], 'front_outer_source_z_G_m': grip['front_outer_source_z_G_m'],
        'seed2_angles_rad': initial['initial_PD_target_rad'], 'support_bias_rad': bias, 'probe_axes': axes, 'initial_route_length_m': initial['initial_route_length_m'],
        'native_initializations': 0, 'physics_steps': 0,
        'scope': 'same saved native initial q/LA/PD/G state; six individual target residual probes only; fresh native admission required'}, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'target_residuals': {r['label']: r['target_residual_rad'] for r in rows}}, indent=2))


if __name__ == '__main__': main()
