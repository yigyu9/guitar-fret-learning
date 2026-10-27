"""Prepare one five-hinge candidate, without guessing finger1 multi-axis FK."""
from pathlib import Path
import copy
import hashlib
import json
import numpy as np
from .warmstart_targets import compose

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'fixed_strap_source_hand_initial_v1'
OLD = B / 'initial_middle3_alignment_v1'
CHANGED = ('LH:thumb1_x', 'LH:thumb1_y', 'LH:thumb3', 'LH:index1_x', 'LH:ring1_x')


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, d): Path(p).write_text(json.dumps(d, indent=2, allow_nan=False) + '\n')


def main():
    assert not (P / 'proposal.json').exists()
    old = read(OLD / 'proposal.json')
    assert all(old['checks'].values())
    initial = read(OLD / 'native/initial_values.json')
    ranges_path = B / 'fixed_strap_source_compatibility_v1/joint_ranges.jsonl'
    inventory_path = ranges_path.parent / 'artifact_inventory.json'
    assert sha(ranges_path) == read(inventory_path)[str(ranges_path)]['sha256']
    ranges = [json.loads(s) for s in ranges_path.read_text().splitlines()]
    selected = {(d['kind'], d['name']):d for d in ranges if d['label'] == 'initial_aligned'}
    paths = [Path(__file__).resolve(), A / 'SOURCE_HAND_INITIAL_EXECUTION.md',
             A / 'FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md', OLD / 'proposal.json',
             OLD / 'native/initial_values.json', ranges_path, inventory_path, A / 'warmstart_targets.py',
             A / 'environment.py']
    hashes = dict(old['input_sha256'])
    for p in paths:
        assert str(p) not in hashes or hashes[str(p)] == sha(p)
        hashes[str(p)] = sha(p)
    assert all(sha(p) == h for p,h in hashes.items())
    row = old['rows'][0]
    original = read(row['trial_path'])
    assert sha(row['trial_path']) == row['trial_sha256']
    hashes[row['trial_path']] = row['trial_sha256']
    trial = copy.deepcopy(original)
    names = initial['human_joint_names']
    qold = np.array(initial['initial_PD_target_rad'], dtype=np.float32)
    told = np.array(initial['preserved_absolute_targets_rad'], dtype=np.float32)
    qnew, tnew = qold.copy(), told.copy()
    changes = []
    for name in CHANGED:
        i = names.index(name)
        values = []
        for kind, previous in [('actual_initial', qold[i]), ('held', told[i])]:
            d = selected[kind, name]
            assert float(previous) == d['current_rad'] and d['outside_effective_range']
            boundary = d['nearest_reference_rad']
            inward = d['effective_upper_rad'] if previous < d['effective_lower_rad'] else d['effective_lower_rad']
            value = np.nextafter(np.float32(boundary), np.float32(inward))
            assert d['effective_lower_rad'] < value < d['effective_upper_rad']
            values.append(value)
        qnew[i], tnew[i] = values
        trial['initial_settings']['joint_angles_rad'][name] = float(qnew[i])
        trial['main_target_offsets_rad'][name] = float(tnew[i]) - float(qnew[i])
        changes.append(dict(name=name, old_initial_rad=float(qold[i]), initial_rad=float(qnew[i]),
            old_held_rad=float(told[i]), held_rad=float(tnew[i]),
            initial_delta_rad=float(qnew[i]) - float(qold[i]), held_delta_rad=float(tnew[i]) - float(told[i])))
    main_indices = [names.index(n) for n in initial['main_control_joint_names']]
    offsets = np.array([trial['main_target_offsets_rad'].get(names[i], 0.) for i in main_indices])
    props = initial['PD_properties']
    target = compose(qnew, main_indices, offsets, props['lower'], props['upper'])
    other = [i for i,n in enumerate(names) if n not in CHANGED]
    restored = copy.deepcopy(trial)
    for name in CHANGED:
        restored['initial_settings']['joint_angles_rad'][name] = original['initial_settings']['joint_angles_rad'][name]
        restored['main_target_offsets_rad'][name] = original['main_target_offsets_rad'][name]
    checks = dict(only_five_settings_and_offsets_changed=restored == original,
        other76_initial_and_held_exact=bool(np.array_equal(qnew[other], qold[other]) and np.array_equal(tnew[other], told[other])),
        exact_unclipped_composed81_target=bool(np.array_equal(target, tnew)),
        fixed_LA=trial['initial_settings']['strap_rest_length_m'] == 1.1018469719600776)
    for kind, value in [('actual_initial', qnew), ('held', target)]:
        checks[kind + '_all81_effective_ranges'] = all(selected[kind,n]['effective_lower_rad'] <= float(value[i]) <= selected[kind,n]['effective_upper_rad'] for i,n in enumerate(names))
    for sign in [-1,1]:
        moving = offsets.copy(); moving[main_indices.index(names.index('L_Wrist_x'))] += sign * .005
        command = compose(qnew, main_indices, moving, props['lower'], props['upper'])
        checks['wrist_extreme_effective_ranges_' + str(sign)] = all(selected['held',n]['effective_lower_rad'] <= float(command[i]) <= selected['held',n]['effective_upper_rad'] for i,n in enumerate(names))
    checks['inputs_preserved'] = all(sha(p) == h for p,h in hashes.items())
    assert all(checks.values()), checks
    folder = A / 'trials/fixed_strap_source_hand_initial_v1'
    folder.mkdir(exist_ok=False)
    trial_path = folder / 'source_hand5_nearest.json'
    save(trial_path, trial)
    newrow = copy.deepcopy(row)
    newrow.pop('source_state', None)
    newrow.update(label='source_hand5_nearest', alpha=None, trial_path=str(trial_path), trial_sha256=sha(trial_path),
        expected_initial_angles_rad=qnew.astype(float).tolist(), expected_absolute_targets_rad=target.astype(float).tolist(),
        admitted_for_native_near_contact_diagnostic=True,
        admission_scope='Numeric candidate preparation only; fresh direct native source geometry gate still required before integration',
        finger_target_policy='Five initial/held hinges at nearest effective source boundary one float32 ULP inward; other76 preserved')
    proposal = copy.deepcopy(old)
    proposal.update(checks=checks, input_sha256=hashes, rows=[newrow],
        scope='Numeric preparation; no multi-axis FK prediction or geometry admission; fresh native direct gate required')
    save(P / 'proposal.json', proposal)
    save(P / 'preparation.json', dict(checks=checks, changes=changes, trial_path=str(trial_path),
        trial_sha256=sha(trial_path), input_sha256=hashes, native_initializations=0, physics_steps=0,
        scope='Numeric effective-range condition only; no geometry/support/stability success'))
    print(json.dumps(dict(checks=checks, changes=changes), indent=2))


if __name__ == '__main__': main()
