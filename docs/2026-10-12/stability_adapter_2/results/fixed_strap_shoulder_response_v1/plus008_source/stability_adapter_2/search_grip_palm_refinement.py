"""Small seed2 initial-pose fits; saved source geometry only, no dynamics."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3'
PHASE = OLD.parent / 'grip_palm_refinement_v1'
TRIALS = ROOT / 'stability_adapter_2/trials/grip_palm_refinement_v1'


def main():
    PHASE.mkdir(exist_ok=False); TRIALS.mkdir(exist_ok=False)
    from .search_multi_face_grip import sha, read
    path = OLD / 'analysis.json'; hashes = {str(path): sha(path)}; prior = read(path)
    paths = [Path(p) for p in prior['input_sha256']] + [Path(__file__).resolve(),
        ROOT / 'stability_adapter_2/MULTI_FACE_GRIP_PALM_REFINEMENT_PLAN.md', ROOT / 'stability_adapter_2/GRIP_PALM_REFINEMENT_EXECUTION.md',
        OLD / 'search.json', OLD / 'native/seed_2/initial_grip_audit.json',
        OLD / 'native/seed_2/initial_values.json', ROOT / 'stability_adapter_2/audit_palm_side_target.py']
    hashes.update({str(p): sha(p) for p in paths})
    def save(name, value):
        (PHASE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    save('attempt.json', {'input_sha256': hashes, 'native_initializations': 0, 'physics_steps': 0})
    if not all(prior['checks'].values()) or any(sha(p) != h for p, h in prior['input_sha256'].items()):
        raise AssertionError('previous closure changed')
    from .environment import np
    from .search_multi_face_grip import prepare_geometry, left_fk, nearest_face
    from .build_fixed_lower_asset import pose
    from .render_best_run_video import set_saved_pose
    from .palm_side_source_checks import source_checks, intersection
    from .audit_palm_side_target import closest_polygon
    from scipy.spatial.transform import Rotation
    from scipy.optimize import least_squares
    import mujoco
    initial = read(OLD / 'native/seed_2/initial_values.json'); old = read(OLD / 'search.json')
    audit = read(OLD / 'native/seed_2/initial_grip_audit.json')
    report, probe, _, _, _, gp, gr, _, z = prepare_geometry(initial)
    model, data, shapes = probe; names = initial['human_joint_names']; bodies = report['human_body_names']
    state0 = initial['native_initial_state']; q0 = np.array([d['pos'] for d in state0['human_dof_states']])
    base0 = np.array([d['pos'] for d in read(OLD / 'native/baseline/initial_values.json')['native_initial_state']['human_dof_states']])
    indices = np.array([i for i, n in enumerate(names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:'))])
    widths = np.r_[np.full(12, .03), np.full(21, .10)]
    low = np.maximum(np.array(initial['PD_properties']['lower'])[indices], q0[indices] - widths)
    high = np.minimum(np.array(initial['PD_properties']['upper'])[indices], q0[indices] + widths)
    low[:12] = np.maximum(low[:12], base0[indices[:12]] - .3)
    high[:12] = np.minimum(high[:12], base0[indices[:12]] + .3)
    fk, parents = left_fk(names, bodies, state0, q0)
    proxy = np.array(read(OLD.parent / 'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    points = {}
    for name, gap in audit['source_hull_to_faces'].items():
        p, r = pose(state0['human_body_states'][bodies.index(name)])
        points[name] = Rotation.from_quat(r).inv().apply(np.array(gap['palm_witness_world_m']) - p)
    def residual(values, palm_weight):
        q = q0.copy(); q[indices] = values; poses = fk(q); result = []
        for name, point in points.items():
            p, r = poses[name]; face = audit['source_hull_to_faces'][name]['face']
            point_G = gr.inv().apply(p + r.apply(point) - gp)
            target, normal = nearest_face(point_G, face, z, .0003, old['regions_G_m'])
            result.extend((palm_weight if face == 'palm' else 1) * 1000 * (point_G - target))
            if face == 'palm':
                result.extend(.2 * (gr.inv().apply(r.apply(old['facets'][name]['normal_local'])) + normal))
        up = poses['LH:palm'][1].apply(proxy)[2]
        result.extend([100 * max(0., -up), 2 * (1 - up)])
        result.extend(.5 * (values - q0[indices]))
        return np.array(result)
    def distance(a, b):
        chain = []; current = a
        while current in parents: chain.append(current); current = parents[current]
        chain.append(current); steps = 0; current = b
        while current not in chain and current in parents: steps += 1; current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    rows = []; baseline_max = max(g['distance_m'] for g in audit['source_hull_to_faces'].values())
    for weight in (1., 2.):
        fit = least_squares(lambda v: residual(v, weight), np.clip(q0[indices], low + 1e-9, high - 1e-9), bounds=(low, high), max_nfev=60)
        for alpha in (1., .5, .25, .125):
            q = q0.copy(); q[indices] += alpha * (fit.x - q0[indices]); poses = fk(q)
            state = copy.deepcopy(state0)
            for name, (p, r) in poses.items():
                state['human_body_states'][bodies.index(name)]['pose'] = {'p': dict(zip('xyz', p)), 'r': dict(zip('xyzw', r.as_quat()))}
            for i, value in enumerate(q): state['human_dof_states'][i]['pos'] = float(value)
            set_saved_pose(model, mujoco, report, state); mujoco.mj_forward(model, data)
            meshes, overlaps, crosshands = source_checks(probe)
            hand = [s for s in shapes if s['body'].startswith('LH:') or s['body'] in ('L_Wrist', 'L_Elbow')]
            self_cross = [{'a': a['body'], 'b': b['body'], 'common_radius_m': radius}
                for i, a in enumerate(hand) for b in hand[i + 1:] if distance(a['body'], b['body']) > 2
                for radius in [intersection(meshes[a['geom_id']], meshes[b['geom_id']])] if radius > 1e-7]
            gaps = {}
            for name, original in audit['source_hull_to_faces'].items():
                poly = np.array(old['regions_G_m'][original['face']])
                if original['face'] == 'front': poly[:, 2] = z
                mesh = meshes[next(s['geom_id'] for s in shapes if s['body'] == name)]
                gaps[name] = dict(closest_polygon(mesh, gr.apply(poly) + gp), face=original['face'])
            up = float(poses['LH:palm'][1].apply(proxy)[2]); clear = not overlaps and not crosshands and not self_cross and up > 0
            accepted = clear and max(g['distance_m'] for g in gaps.values()) < baseline_max and gaps['LH:palm']['distance_m'] < audit['source_hull_to_faces']['LH:palm']['distance_m']
            label = f'w{int(weight)}_a{str(alpha).replace(".", "p")}'
            trial = copy.deepcopy(initial['input_trial']); trial['initial_settings']['joint_angles_rad'].update({names[i]: float(q[i]) for i in indices})
            path = TRIALS / (label + '.json'); path.write_text(json.dumps(trial, indent=2) + '\n')
            row = {'label': label, 'fit_success': bool(fit.success), 'alpha': alpha, 'weight': weight,
                'target_clearance_m': .0003, 'palm_up_proxy_z': up, 'source_clear': clear,
                'source_intersections': overlaps, 'cross_hand_intersections': crosshands, 'nonadjacent_left_hand_intersections': self_cross,
                'source_hull_to_faces': gaps, 'accepted_for_fresh_native': bool(accepted),
                'trial_path': str(path), 'trial_sha256': sha(path), 'source_state': state}
            rows.append(row); save('partial_rows.json', rows)
            print(json.dumps({'label': label, 'accepted': bool(accepted), 'gaps_mm': {n: v['distance_m'] * 1000 for n, v in gaps.items()}, 'overlaps': len(overlaps), 'self_cross': len(self_cross)}), flush=True)
    checks = {'inputs_unchanged': all(sha(p) == h for p, h in hashes.items()), 'native_initializations_zero': True}
    save('search.json', {'checks': checks, 'input_sha256': hashes, 'rows': rows, 'facets': old['facets'],
        'regions_G_m': old['regions_G_m'], 'front_outer_source_z_G_m': z, 'native_initializations': 0, 'physics_steps': 0,
        'seed2_angles_rad': q0.tolist(), 'baseline_angles_rad': base0.tolist(),
        'scope': 'fixed closest-hull witnesses are local fit proxies; full hull/LP safety rechecked at each saved candidate; no native dynamics or cooked clearance certification'})
    if not all(checks.values()): raise AssertionError(checks)


if __name__ == '__main__': main()
