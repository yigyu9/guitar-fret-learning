"""Compare rear-facing source centroids and bounded linear FK motion; no simulation."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PREVIOUS = BASE / 'three_face_rear_facet_v2'
PHASE = BASE / 'three_face_rear_facet_catalog_v1'
REFERENCE = BASE / 'three_face_support_loss_v1/native/saved_finger_targets'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    PHASE.mkdir(exist_ok=True)
    if (PHASE / 'catalog.json').exists() or (PHASE / 'attempt.json').exists():
        raise FileExistsError('preserve consumed catalog')
    previous = read(PREVIOUS / 'proposal.json')
    hashes = dict(previous['input_sha256'])
    for path in [Path(__file__).resolve(), PREVIOUS / 'proposal.json', PREVIOUS / 'sensitivity.json',
                 PREVIOUS / 'facet_selection.json', PREVIOUS / 'artifact_inventory.json',
                 PREVIOUS / 'analysis.json',
                 ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_PLAN.md',
                 ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_EXECUTION.md']:
        hashes[str(path)] = sha(path)
    if not all(sha(p) == h for p, h in hashes.items()):
        raise AssertionError('sealed source inputs changed')
    save(PHASE / 'attempt.json', {'input_sha256': hashes, 'native_initializations': 0, 'physics_steps': 0})
    from .environment import np
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .search_multi_face_grip import left_fk
    from .build_fixed_lower_asset import ASSET, pose
    from scipy.spatial.transform import Rotation
    from scipy.optimize import lsq_linear
    import trimesh

    initial = read(REFERENCE / 'initial_values.json')
    state = initial['native_initial_state']
    names, bodies = initial['human_joint_names'], initial['human_body_names']
    q0 = np.array(previous['old_initial_angles_rad'])
    sensitivity = read(PREVIOUS / 'sensitivity.json')
    indices = [names.index(n) for n in sensitivity['coordinate_names']]
    expanded = [r for r in previous['rejected'] if r['thumb_radius_rad'] == .2]
    lower, upper = np.array(expanded[0]['search_lower_rad']), np.array(expanded[0]['search_upper_rad'])
    if any(r['search_lower_rad'] != lower.tolist() or r['search_upper_rad'] != upper.tolist() for r in expanded):
        raise AssertionError('expanded search bounds differ')
    actual = np.array([initial['actual_initial_angles_rad'][n] for n in names])
    if not np.array_equal(q0, actual) or len(indices) != 17:
        raise AssertionError('saved actual initial81 and coordinate17 schema')
    fk, _ = left_fk(names, bodies, state, q0)
    gp, gq = pose(state['guitar_body_states'][0])
    gr = Rotation.from_quat(gq)
    guitar_names = [r['body'] for r in read(REFERENCE / 'shape_properties.json')['actors']['guitar']['body_ranges']]
    config = read(ROOT / 'stability_adapter_2/config.json')
    config['humanoid_asset'] = str(ASSET)
    scene = SimpleNamespace(config=config, human=0, guitar=1, env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env, actor: bodies if actor == 0 else guitar_names),
        bodies=lambda actor: state['human_body_states'] if actor == 0 else state['guitar_body_states'])
    model, data, shapes = build_probe(scene)
    shape = next(s for s in shapes if s['actor'] == 'human' and s['body'] == 'LH:thumb3')
    mesh = face_geometry(model, data, shape)
    p0, r0 = fk(q0)['LH:thumb3']
    local_centers = r0.inv().apply(mesh.triangles_center - p0)
    local_normals = r0.inv().apply(mesh.face_normals)
    centers_G = gr.inv().apply(mesh.triangles_center - gp)
    normals_G = gr.inv().apply(mesh.face_normals)
    eligible = np.flatnonzero(normals_G[:, 2] > .75)
    old_facet = read(PREVIOUS / 'facet_selection.json')
    largest = old_facet['triangle_index']
    if len(eligible) != old_facet['eligible_triangle_count'] or not np.allclose(
            local_centers[largest], old_facet['anchor']['source_point_local_m'], atol=1e-12, rtol=0):
        raise AssertionError('active source hull differs from previous selection')

    # True perpendicular edge inset, with intersections of adjacent shifted lines.
    polygon = np.array(previous['regions_G_m']['thumb'])
    center = polygon[:, :2].mean(axis=0)
    edges = np.roll(polygon[:, :2], -1, axis=0) - polygon[:, :2]
    normals = np.column_stack((-edges[:, 1], edges[:, 0])) / np.linalg.norm(edges, axis=1)[:, None]
    normals *= np.where(np.sum(normals * (center - polygon[:, :2]), axis=1) > 0, 1., -1.)[:, None]
    levels = np.sum(normals * polygon[:, :2], axis=1) + .002
    inset = np.array([np.linalg.solve(normals[[i - 1, i]], levels[[i - 1, i]]) for i in range(4)])
    inset = np.column_stack((inset, polygon[:, 2]))
    triangles = np.array([inset[[0, 1, 2]], inset[[0, 2, 3]]])
    goals, distances = [], []
    for point in centers_G:
        near = trimesh.triangles.closest_point(triangles, np.tile(point, (2, 1)))
        nearest = near[np.argmin(np.linalg.norm(near - point, axis=1))]
        distances.append(float(np.linalg.norm(nearest - point)))
        goal = nearest.copy()
        goal[2] -= .0007
        goals.append(goal)
    goals = np.array(goals)

    # One pair of body-pose FK evaluations per coordinate yields every point derivative.
    jac = np.empty((len(local_centers), 3, 17))
    for j, i in enumerate(indices):
        plus, minus = q0.copy(), q0.copy()
        plus[i] += .0001
        minus[i] -= .0001
        pp, rp = fk(plus)['LH:thumb3']
        pm, rm = fk(minus)['LH:thumb3']
        jac[:, :, j] = gr.inv().apply(pp + rp.apply(local_centers) - pm - rm.apply(local_centers)) / .0002
    rows = []
    observed = old_facet['anchor']['observed_feature_source_anchor']
    for k in sorted(set(eligible.tolist() + [largest, observed['source_triangle_index']])):
        delta = goals[k] - centers_G[k]
        fit = lsq_linear(jac[k], delta, bounds=(lower - q0[indices], upper - q0[indices]), tol=1e-10)
        if not fit.success or not np.isfinite(fit.x).all():
            raise RuntimeError('bounded source linear fit failed')
        axis_min = np.sum(np.minimum(jac[k] * (lower - q0[indices]), jac[k] * (upper - q0[indices])), axis=1)
        axis_max = np.sum(np.maximum(jac[k] * (lower - q0[indices]), jac[k] * (upper - q0[indices])), axis=1)
        rows.append({'triangle_index': k, 'rear_facing_qualified': bool(k in eligible),
            'centroid_local_m': local_centers[k].tolist(), 'normal_local': local_normals[k].tolist(),
            'centroid_G_m': centers_G[k].tolist(), 'normal_G': normals_G[k].tolist(),
            'area_mm2': float(mesh.area_faces[k] * 1e6), 'distance_to_2mm_inset_patch_mm': distances[k] * 1000,
            'diagnostic_goal_G_m': goals[k].tolist(), 'required_motion_G_mm': (delta * 1000).tolist(),
            'required_motion_norm_mm': float(np.linalg.norm(delta) * 1000),
            'source_J_G_mm_per_rad': (jac[k] * 1000).tolist(),
            'linear_fit_residual_mm': float(np.linalg.norm(jac[k] @ fit.x - delta) * 1000),
            'linear_fit_coordinate_delta_rad': fit.x.tolist(),
            'axis_independent_min_G_mm': (axis_min * 1000).tolist(),
            'axis_independent_max_G_mm': (axis_max * 1000).tolist()})
    ranked = sorted([r for r in rows if r['rear_facing_qualified']], key=lambda r: (r['required_motion_norm_mm'], r['triangle_index']))
    selected = []
    for row in ranked:
        if all(np.linalg.norm(np.array(row['centroid_G_m']) - r['centroid_G_m']) >= .002 for r in selected):
            selected.append(row)
        if len(selected) == 2:
            break
    checks = {'same_saved_actual_initial81_and_bounds17': True,
              'previous_largest_active_source_anchor_exact': True,
              'all_qualified_points_and_reference_recorded': len(ranked) == len(eligible),
              'selected_qualified_distance_order_and_2mm_separation': len(selected) == 2,
              'sealed_inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()):
        raise AssertionError(checks)
    save(PHASE / 'catalog.json', {'checks': checks, 'input_sha256': hashes, 'rows': rows, 'selected': selected,
        'qualified_count': len(eligible), 'reference_largest_triangle': largest,
        'reference_observed_triangle': observed['source_triangle_index'],
        'observed_feature_source_anchor': observed, 'original_patch_G_m': polygon.tolist(),
        'inset_patch_G_m': inset.tolist(), 'diagnostic_clearance_m': .0007,
        'coordinate_names': sensitivity['coordinate_names'], 'lower_rad': lower.tolist(), 'upper_rad': upper.tolist(),
        'initial81_angles_rad': q0.tolist(), 'saved_absolute_targets_rad': previous['saved_absolute_targets_rad'],
        'absolute_strap_rest_length_m': initial['absolute_strap_rest_length_m'],
        'native_initializations': 0, 'physics_steps': 0,
        'scope': 'source centroid selection and finite-difference FK/linear box prediction only; no nonlinear feasibility, cooked/anatomical/physical support/control authority or stability certification'})
    print(json.dumps({'checks': checks, 'qualified': len(eligible), 'selected': [
        {k: row[k] for k in ('triangle_index', 'centroid_G_m', 'required_motion_norm_mm', 'linear_fit_residual_mm')}
        for row in selected], 'native_initializations': 0, 'physics_steps': 0}), flush=True)


if __name__ == '__main__':
    main()
