"""Align one initial scalar hinge with its prior held goal; source checks only."""
from pathlib import Path
from types import SimpleNamespace
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from .warmstart_targets import compose
from .coupled_support_source import CoupledSnapshot
from .build_fixed_lower_asset import ASSET, pose
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'initial_middle3_alignment_v1'
OLD = B / 'fixed_strap_middle_relax_v2'
HELPERS = ['warmstart_targets.py', 'coupled_support_source.py', 'build_fixed_lower_asset.py',
           'initial_overlap.py', 'palm_side_source_checks.py', 'search_multi_face_grip.py',
           'environment.py', 'run_palm_witness_initial_diagnostic.py', 'run_small_wrist_recorded_diagnostic.py', 'near_contact_initial_audit.py']
POLICY = B / 'torso_hold_native_collision_v1/initial_collision/shape_properties.json'
PROXY = B / 'palm_neck_side_v1/initial_audit_v2/audit.json'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, v): Path(p).write_text(json.dumps(v, indent=2, allow_nan=False) + '\n')


def main():
    assert not (P / 'proposal.json').exists() and not (P / 'preparation.json').exists()
    old = read(OLD / 'proposal.json'); initial = read(OLD / 'native/initial_values.json')
    row = old['rows'][0]; original = read(row['trial_path'])
    assert all(old['checks'].values()) and sha(row['trial_path']) == row['trial_sha256']
    hashes = dict(old['input_sha256'])
    sources = [Path(__file__).resolve(), A / 'INITIAL_MIDDLE3_ALIGNMENT_PLAN.md', A / 'FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md',
               OLD / 'proposal.json', OLD / 'native/initial_values.json', OLD / 'artifact_inventory.json', OLD / 'final_verification.json',
               Path(row['trial_path']), POLICY, PROXY, A / 'config.json', ASSET] + [A / n for n in HELPERS]
    for f in sources:
        assert str(f) not in hashes or hashes[str(f)] == sha(f)
        hashes[str(f)] = sha(f)
    previous = read(OLD / 'artifact_inventory.json')
    for f, v in previous.items():
        assert Path(f).stat().st_size == v['size'] and sha(f) == v['sha256']
        assert f not in hashes or hashes[f] == v['sha256']
        hashes[f] = v['sha256']
    assert all(sha(f) == h for f, h in hashes.items())
    names, bodies = initial['human_joint_names'], initial['human_body_names']
    axis = names.index('LH:middle3'); other = [j for j in range(81) if j != axis]
    main_indices = [names.index(n) for n in initial['main_control_joint_names']]
    qold = np.array(initial['initial_PD_target_rad'], dtype=np.float32)
    targetold = np.array(initial['preserved_absolute_targets_rad'], dtype=np.float32)
    qnew = qold.copy(); qnew[axis] = targetold[axis]
    trial = copy.deepcopy(original)
    trial['initial_settings']['joint_angles_rad']['LH:middle3'] = float(qnew[axis])
    trial['main_target_offsets_rad']['LH:middle3'] = 0.
    offsets = np.array([trial['main_target_offsets_rad'].get(names[j], 0.) for j in main_indices])
    lower, upper = initial['PD_properties']['lower'], initial['PD_properties']['upper']
    target = compose(qnew, main_indices, offsets, lower, upper)
    desired = qnew.copy(); desired[main_indices] = (qnew[main_indices].astype(float) + offsets).astype(np.float32)
    restored = copy.deepcopy(trial)
    restored['initial_settings']['joint_angles_rad']['LH:middle3'] = original['initial_settings']['joint_angles_rad']['LH:middle3']
    restored['main_target_offsets_rad']['LH:middle3'] = original['main_target_offsets_rad']['LH:middle3']
    checks = dict(only_middle3_initial_and_offset_changed=restored == original and np.array_equal(qnew[other], qold[other]),
                  all81_absolute_targets_exact=np.array_equal(target, targetold),
                  initial_and_target_bounds=bool(np.all(qnew >= lower) and np.all(qnew <= upper) and np.all(target >= lower) and np.all(target <= upper)),
                  unclipped_float32_target=np.array_equal(target, desired) and bool(np.all(abs(offsets) <= .3)),
                  fixed_LA=trial['initial_settings']['strap_rest_length_m'] == 1.1018469719600776)
    for sign in [-1, 1]:
        moving = offsets.copy(); moving[main_indices.index(names.index('L_Wrist_x'))] += sign * .005
        command = compose(qnew, main_indices, moving, lower, upper)
        expected = qnew.copy(); expected[main_indices] = (qnew[main_indices].astype(float) + moving).astype(np.float32)
        checks['wrist_extreme_' + str(sign)] = np.array_equal(command, expected) and bool(np.all(command >= lower) and np.all(command <= upper) and np.all(abs(moving) <= .3))
    state0 = initial['native_initial_state']; expected_state = copy.deepcopy(state0)
    snapshot = CoupledSnapshot(names, bodies, state0, state0)
    zero = snapshot.poses(np.zeros(18))
    zero_p = max(float(np.linalg.norm(pose(state0['human_body_states'][bodies.index(n)])[0] - v[0])) for n, v in zero.items())
    zero_r = max(float((Rotation.from_quat(pose(state0['human_body_states'][bodies.index(n)])[1]) * v[1].inv()).magnitude()) for n, v in zero.items())
    checks['zero_delta_FK_identity'] = zero_p < 1e-6 and zero_r < 1e-6
    delta = np.zeros(18); delta[snapshot.selected.index('LH:middle3')] = float(qnew[axis]) - float(qold[axis])
    poses = snapshot.poses(delta)
    changed_bodies = ['LH:middle3', 'LH:middle_top']
    for n in changed_bodies:
        position, rotation = poses[n]; rec = expected_state['human_body_states'][bodies.index(n)]['pose']
        rec['p'] = dict(zip('xyz', map(float, position))); rec['r'] = dict(zip('xyzw', map(float, rotation.as_quat())))
    expected_state['human_dof_states'][axis]['pos'] = float(qnew[axis])
    checks['other_bodies_and_G_source_state_exact'] = expected_state['guitar_body_states'] == state0['guitar_body_states'] and all(expected_state['human_body_states'][j] == state0['human_body_states'][j] for j, n in enumerate(bodies) if n not in changed_bodies)
    assert all(checks.values()), checks
    policy = read(POLICY); config = read(A / 'config.json'); config['humanoid_asset'] = str(ASSET)
    guitar_names = [r['body'] for r in policy['actors']['guitar']['body_ranges']]
    scene = SimpleNamespace(config=config, human=0, guitar=1, env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env, actor: bodies if actor == 0 else guitar_names),
        bodies=lambda actor: expected_state['human_body_states'] if actor == 0 else expected_state['guitar_body_states'])
    probe = build_probe(scene); meshes, hg, cross = source_checks(probe)
    xml = ET.parse(ASSET).getroot()
    parents = {c.get('name'): p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a, b):
        chain = []; current = a
        while current in parents: chain.append(current); current = parents[current]
        chain.append(current); steps = 0; current = b
        while current not in chain and current in parents: steps += 1; current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    humans = [s for s in probe[2] if s['actor'] == 'human']; overlaps = []; count = 0
    filters = policy['mask_audit']['native_filters']
    for j, x in enumerate(humans):
        for y in humans[j + 1:]:
            if distance(x['body'], y['body']) <= 2: continue
            sameleft = all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist', 'L_Elbow') for s in (x, y))
            allowed = all(a & b == 0 for a in filters[x['body']] for b in filters[y['body']])
            if not (sameleft or allowed): continue
            count += 1; radius = intersection(meshes[x['geom_id']], meshes[y['geom_id']])
            if radius > 1e-7: overlaps.append(dict(a=x['body'], b=y['body'], common_radius_m=radius))
    proxy = np.array(read(PROXY)['palmar_normal_proxy_local'])
    up = float(Rotation.from_quat(pose(expected_state['human_body_states'][bodies.index('LH:palm')])[1]).apply(proxy)[2])
    checks.update(source_human_guitar_clear=not hg, source_cross_hands_clear=not cross,
                  source_self1188_clear=count == 1188 and not overlaps, palm_up_hemisphere=up > 0,
                  all_inputs_unchanged=all(sha(f) == h for f, h in hashes.items()))
    admitted = all(checks.values())
    folder = A / 'trials/initial_middle3_alignment_v1'; folder.mkdir(exist_ok=False)
    trial_path = folder / 'middle3_initial_at_goal.json'; save(trial_path, trial)
    newrow = copy.deepcopy(row)
    newrow.update(label='initial_aligned', trial_path=str(trial_path), trial_sha256=sha(trial_path),
                  expected_initial_angles_rad=qnew.astype(float).tolist(), expected_absolute_targets_rad=target.astype(float).tolist(),
                  source_state=expected_state, admitted_for_native_near_contact_diagnostic=admitted,
                  finger_target_policy='middle3 initial q equals prior held goal, offset0; all81 final targets preserved')
    proposal = copy.deepcopy(old); proposal.update(checks=checks, input_sha256=hashes, rows=[newrow], scope='one scalar initial hinge aligned; all81 final goals fixed; source admission, not native/cooked/playing certification')
    save(P / 'proposal.json', proposal)
    save(P / 'preparation.json', dict(checks=checks, admitted_for_native=admitted, input_sha256=hashes,
        trial_path=str(trial_path), trial_sha256=sha(trial_path), previous_initial_rad=float(qold[axis]), new_initial_rad=float(qnew[axis]),
        initial_delta_rad=float(qnew[axis]) - float(qold[axis]), changed_source_bodies=changed_bodies, zero_FK_position_error_m=zero_p, zero_FK_rotation_error_rad=zero_r,
        source_human_guitar_intersections=hg, source_cross_hand_intersections=cross, source_self_pair_count=count, source_self_intersections=overlaps,
        palm_up_proxy_z=up, native_initializations=0, physics_steps=0))
    print(json.dumps(dict(checks=checks, admitted_for_native=admitted, initial_deg=float(np.degrees(float(qnew[axis]))), source_self_pair_count=count)))


if __name__ == '__main__': main()
