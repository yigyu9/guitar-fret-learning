"""Prepare one middle3 PD-goal relaxation at the unchanged fixed-LA initial pose."""
from pathlib import Path
import copy
import hashlib
import json
import numpy as np
from .warmstart_targets import compose

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'fixed_strap_middle_relax_v2'
OLD = B / 'joint_only_fixed_strap_v1'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, data):
    Path(p).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def main():
    assert not (P / 'proposal.json').exists()
    old = read(OLD / 'proposal.json')
    row = old['rows'][0]
    initial = read(OLD / 'native/initial_values.json')
    original = read(row['trial_path'])
    assert all(old['checks'].values()) and all(sha(p) == h for p, h in old['input_sha256'].items())
    assert sha(row['trial_path']) == row['trial_sha256']
    hashes = dict(old['input_sha256'])
    for p in [OLD / 'proposal.json', OLD / 'native/initial_values.json', Path(row['trial_path']), Path(__file__).resolve(), A / 'FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md', A / 'warmstart_targets.py', B / 'fixed_strap_middle_relax_v1/artifact_inventory.json', B / 'fixed_strap_middle_relax_v1/final_verification.json', A / 'FIXED_STRAP_MIDDLE_RELAX_DECISION.md']:
        assert str(p) not in hashes or hashes[str(p)] == sha(p)
        hashes[str(p)] = sha(p)
    previous = read(B / 'fixed_strap_middle_relax_v1/artifact_inventory.json')
    assert all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p, v in previous.items())
    for p, v in previous.items():
        assert p not in hashes or hashes[p] == v['sha256']
        hashes[p] = v['sha256']
    names = initial['human_joint_names']
    main_indices = [names.index(n) for n in initial['main_control_joint_names']]
    axis, wrist = names.index('LH:middle3'), names.index('L_Wrist_x')
    q = np.array(initial['initial_PD_target_rad'], dtype=np.float32)
    lo, hi = np.array(initial['PD_properties']['lower']), np.array(initial['PD_properties']['upper'])
    baseline = np.array(initial['preserved_absolute_targets_rad'], dtype=np.float32)
    trial = copy.deepcopy(original)
    trial['main_target_offsets_rad']['LH:middle3'] -= .15
    offsets = np.array([trial['main_target_offsets_rad'].get(names[j], 0.) for j in main_indices])
    target = compose(q, main_indices, offsets, lo, hi)
    restored = copy.deepcopy(trial)
    restored['main_target_offsets_rad']['LH:middle3'] = original['main_target_offsets_rad']['LH:middle3']
    other = [j for j in range(81) if j != axis]
    desired = q.copy()
    desired[main_indices] = (q[main_indices].astype(float) + offsets).astype(np.float32)
    checks = dict(only_middle3_offset_changed=restored == original and np.array_equal(target[other], baseline[other]), initial_settings_and_G_unchanged=trial['initial_settings'] == original['initial_settings'] and trial['guitar_initial_translation_m'] == original['guitar_initial_translation_m'], fixed_LA=trial['initial_settings']['strap_rest_length_m'] == 1.1018469719600776, unclipped_float32_target=np.array_equal(target, desired) and bool(np.all(target >= lo) and np.all(target <= hi) and np.all(abs(offsets) <= .3)))
    for sign in [-1, 1]:
        moving = offsets.copy()
        moving[main_indices.index(wrist)] += sign * .005
        command = compose(q, main_indices, moving, lo, hi)
        desired = q.copy()
        desired[main_indices] = (q[main_indices].astype(float) + moving).astype(np.float32)
        checks['wrist_extreme_' + str(sign)] = np.array_equal(command, desired) and bool(np.all(abs(moving) <= .3))
    checks['all_inputs_unchanged'] = all(sha(p) == h for p, h in hashes.items())
    assert all(checks.values()), checks
    folder = A / 'trials/fixed_strap_middle_relax_v2'
    folder.mkdir(exist_ok=False)
    path = folder / 'middle3_minus015.json'
    save(path, trial)
    newrow = copy.deepcopy(row)
    newrow.update(label='middle3_minus015', trial_path=str(path), trial_sha256=sha(path), expected_absolute_targets_rad=target.astype(float).tolist(), finger_target_policy='only middle3 held goal reduced total .15rad from baseline; unchanged initial81/other80 goals/LA')
    proposal = copy.deepcopy(old)
    proposal.update(checks=checks, input_sha256=hashes, rows=[newrow], scope='unchanged initial81 and guitar p/q; middle3 PD goal -.15rad only; same fixed LA/wrist motion; physical effect unverified')
    save(P / 'proposal.json', proposal)
    save(P / 'preparation.json', dict(checks=checks, input_sha256=hashes, axis='LH:middle3', trial_path=str(path), trial_sha256=sha(path), requested_delta_rad=-.15, actual_float32_target_delta_rad=float(target[axis] - baseline[axis]), target_rad=float(target[axis]), baseline_target_rad=float(baseline[axis]), native_initializations=0, physics_steps=0))
    print(json.dumps(dict(checks=checks, target_deg=float(np.degrees(target[axis])), baseline_target_deg=float(np.degrees(baseline[axis])))))


if __name__ == '__main__':
    main()
