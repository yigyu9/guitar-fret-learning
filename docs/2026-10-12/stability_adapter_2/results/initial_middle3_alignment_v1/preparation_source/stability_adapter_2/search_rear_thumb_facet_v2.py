"""Rear-facing thumb source facet, bounded initial FK search, certified finite-patch distance interval."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASE = BASE / 'three_face_rear_facet_v2'
TRIALS = ROOT / 'stability_adapter_2/trials/three_face_rear_facet_v2'
REFERENCE = BASE / 'three_face_support_loss_v1/native/saved_finger_targets'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    PHASE.mkdir(exist_ok=True)
    if (PHASE / 'proposal.json').exists() or (PHASE / 'attempt.json').exists():
        raise FileExistsError('preserve consumed source search')
    TRIALS.mkdir(exist_ok=False)
    previous = read(BASE / 'three_face_contact_footprint_v2/proposal.json')
    hashes = dict(previous['input_sha256'])
    if not all(sha(p) == h for p, h in hashes.items()):
        raise AssertionError('sealed source inputs changed')
    for path in [Path(__file__).resolve(), ROOT / 'stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md',
                 BASE / 'three_face_native_feature_map_v1/analysis_v2.json',
                 BASE / 'three_face_native_feature_map_v1/artifact_inventory.json',
                 BASE / 'three_face_contact_footprint_v2/artifact_inventory.json',
                 BASE / 'three_face_contact_footprint_v2/proposal.json',
                 BASE / 'three_face_rear_facet_v1/previous_search_source.py',
                 BASE / 'three_face_rear_facet_v1/previous_search_source_preservation.json',
                 PHASE / 'source_failure_v1_snapshot/preservation.json',
                 ROOT / 'stability_adapter_2/THREE_FACE_REAR_DISTANCE_RECOVERY.md',
                 ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md',
                 ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_EXECUTION.md']:
        hashes[str(path)] = sha(path)
    save(PHASE / 'attempt.json', {'input_sha256': hashes, 'native_initializations': 0, 'physics_steps': 0})
    from .environment import np
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .search_multi_face_grip import left_fk
    from .build_fixed_lower_asset import pose, ASSET
    from .palm_side_source_checks import intersection
    from .warmstart_targets import compose
    from scipy.spatial import ConvexHull
    from scipy.optimize import least_squares, minimize, LinearConstraint
    from scipy.spatial.transform import Rotation
    import trimesh

    initial = read(REFERENCE / 'initial_values.json')
    old = read(BASE / 'three_face_initial_same_target_v1/proposal.json')
    grip = read(BASE / 'three_face_finger_target_hold_v1/proposal.json')
    names, bodies = initial['human_joint_names'], initial['human_body_names']
    state0 = initial['native_initial_state']
    q0 = np.array(initial['initial_PD_target_rad'], dtype=float)
    target = np.array(initial['preserved_absolute_targets_rad'], dtype=np.float32)
    native_lower, native_upper = np.array(initial['PD_properties']['lower']), np.array(initial['PD_properties']['upper'])
    left = [names.index(n) for n in initial['left33_names']]
    main_indices = [names.index(n) for n in initial['main_control_joint_names']]
    arm = [i for i in left if not names[i].startswith('LH:')]
    thumb = [i for i in left if names[i].startswith('LH:thumb')]
    indices = arm + thumb
    def bounds(thumb_radius):
        lower, upper = native_lower.copy(), native_upper.copy()
        lower[arm] = np.maximum(lower[arm], np.maximum(q0[arm] - .05, np.array(old['C02_angles_rad'])[arm] - .3))
        upper[arm] = np.minimum(upper[arm], np.minimum(q0[arm] + .05, np.array(old['C02_angles_rad'])[arm] + .3))
        lower[thumb], upper[thumb] = np.maximum(lower[thumb], q0[thumb] - thumb_radius), np.minimum(upper[thumb], q0[thumb] + thumb_radius)
        aug = {row['dof']: row for row in read(ROOT / 'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json')['rows']}
        for i in thumb:
            lower[i] = max(lower[i], aug[names[i]]['lower_rad'])
            upper[i] = min(upper[i], aug[names[i]]['upper_rad'])
        lower[indices] = np.maximum(lower[indices], target[indices].astype(float) - .3)
        upper[indices] = np.minimum(upper[indices], target[indices].astype(float) + .3)
        # Restrict the optimizer to representable angles inside the requested bounds.
        lo32, hi32 = lower[indices].astype(np.float32), upper[indices].astype(np.float32)
        lo32 = np.where(lo32.astype(float) < lower[indices], np.nextafter(lo32, np.float32(np.inf)), lo32)
        hi32 = np.where(hi32.astype(float) > upper[indices], np.nextafter(hi32, np.float32(-np.inf)), hi32)
        lower[indices], upper[indices] = lo32, hi32
        if len(indices) != 17 or np.any(lower[indices] >= upper[indices]) or np.any(q0[indices] < lower[indices]) or np.any(q0[indices] > upper[indices]):
            raise AssertionError('17-coordinate search bounds and starting point')
        return lower, upper
    lower, upper = bounds(.1)
    fk, parents = left_fk(names, bodies, state0, q0)
    gp, gq = pose(state0['guitar_body_states'][0])
    gr = Rotation.from_quat(gq)
    gn = [row['body'] for row in read(REFERENCE / 'shape_properties.json')['actors']['guitar']['body_ranges']]
    config = read(ROOT / 'stability_adapter_2/config.json')
    config['humanoid_asset'] = str(ASSET)
    scene = SimpleNamespace(config=config, human=0, guitar=1, env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env, actor: bodies if actor == 0 else gn),
        bodies=lambda actor: state0['human_body_states'] if actor == 0 else state0['guitar_body_states'])
    model, data, shapes = build_probe(scene)
    world_meshes = {s['geom_id']: face_geometry(model, data, s) for s in shapes}
    local_meshes = {}
    for shape in shapes:
        if shape['actor'] == 'human' and shape['body'] in fk(q0):
            p, r = fk(q0)[shape['body']]
            mesh = world_meshes[shape['geom_id']].copy()
            mesh.vertices = r.inv().apply(mesh.vertices - p)
            local_meshes[shape['geom_id']] = mesh
    contacts = [json.loads(line) for line in (REFERENCE / 'contacts.jsonl').read_text().splitlines()]
    anchors = {}
    for body, end in [('LH:thumb3', 24), ('LH:palm', 144)]:
        candidates = [(row['physics_step'], k, c) for row in contacts if row['physics_step'] <= end
                      for k, c in enumerate(row['contacts']) if 'human/' + body in (c['body0_name'], c['body1_name'])
                      and any(c[n].startswith('guitar/') for n in ('body0_name', 'body1_name')) and c['lambda'] > 0]
        if not candidates:
            raise AssertionError('no positive recorded feature for ' + body)
        native_points = [np.array([c['localPos' + str(0 if c['body0_name'] == 'human/' + body else 1)][k]
                                  for k in 'xyz']) for _, _, c in candidates]
        chosen = int(np.argmin(np.linalg.norm(native_points - np.median(native_points, axis=0), axis=1)))
        step, row_index, contact = candidates[chosen]
        geom = next(s['geom_id'] for s in shapes if s['actor'] == 'human' and s['body'] == body)
        mesh = local_meshes[geom]
        near = trimesh.triangles.closest_point(mesh.triangles, np.tile(native_points[chosen], (len(mesh.faces), 1)))
        triangle = int(np.argmin(np.linalg.norm(near - native_points[chosen], axis=1)))
        anchors[body] = {'source_point_local_m': near[triangle].tolist(),
            'source_triangle_local_m': mesh.triangles[triangle].tolist(),
            'source_normal_local': mesh.face_normals[triangle].tolist(), 'source_triangle_index': triangle,
            'native_feature_local_m': native_points[chosen].tolist(), 'physics_step': step, 'contact_row_index': row_index,
            'native_to_source_distance_mm': float(np.linalg.norm(near[triangle] - native_points[chosen]) * 1000),
            'scope': 'observed feature nearest active source hull triangle; not anatomical pad/cooked surface certification'}
    observed_thumb = copy.deepcopy(anchors['LH:thumb3'])
    geom = next(s['geom_id'] for s in shapes if s['actor'] == 'human' and s['body'] == 'LH:thumb3')
    thumb_mesh = local_meshes[geom]
    initial_directions = (gr.inv() * fk(q0)['LH:thumb3'][1]).apply(thumb_mesh.face_normals)
    eligible = np.flatnonzero(initial_directions[:, 2] > .75)
    if not len(eligible):
        raise AssertionError('no rear-facing active thumb3 source triangle')
    triangle = int(eligible[np.argmax(thumb_mesh.area_faces[eligible])])
    center = thumb_mesh.triangles[triangle].mean(axis=0)
    anchors['LH:thumb3'] = dict(observed_thumb,
        source_point_local_m=center.tolist(), source_triangle_local_m=thumb_mesh.triangles[triangle].tolist(),
        source_normal_local=thumb_mesh.face_normals[triangle].tolist(), source_triangle_index=triangle,
        native_to_source_distance_mm=float(np.linalg.norm(center - observed_thumb['native_feature_local_m']) * 1000),
        source_selection='largest area active source triangle with initial G+Z dot>.75; not anatomical pad',
        scope='selected rear-facing active source triangle centroid; recorded native feature retained separately; not anatomical/cooked certification',
        observed_feature_source_anchor=observed_thumb)
    save(PHASE / 'facet_selection.json', {'eligible_triangle_count': len(eligible),
        'triangle_index': triangle, 'area_mm2': float(thumb_mesh.area_faces[triangle] * 1e6),
        'initial_outward_G': initial_directions[triangle].tolist(), 'anchor': anchors['LH:thumb3']})
    proxy = np.array(read(BASE / 'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    def points(q):
        poses = fk(q)
        return {b: gr.inv().apply(poses[b][0] + poses[b][1].apply(a['source_point_local_m']) - gp) for b, a in anchors.items()}
    start_points = points(q0)
    jac = np.empty((6, len(indices)))
    for col, i in enumerate(indices):
        plus, minus = q0.copy(), q0.copy()
        plus[i] += .0001
        minus[i] -= .0001
        pp, pm = points(plus), points(minus)
        jac[:, col] = np.concatenate([pp[b] - pm[b] for b in anchors]) / .0002
    save(PHASE / 'sensitivity.json', {'anchors': anchors, 'body_order': list(anchors),
        'coordinate_names': [names[i] for i in indices], 'derivative_G_mm_per_rad': (jac * 1000).tolist(),
        'central_difference_rad': .0001, 'difference_is_source_FK_not_submitted_native_angles': True,
        'initial_anchor_G_m': {k: v.tolist() for k, v in start_points.items()},
        'lower_rad': lower[indices].tolist(), 'upper_rad': upper[indices].tolist()})
    def graph_distance(a, b):
        chain, current = [], a
        while current in parents:
            chain.append(current)
            current = parents[current]
        chain.append(current)
        steps, current = 0, b
        while current not in chain and current in parents:
            steps += 1
            current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    def meshes_at(q):
        poses = fk(q)
        meshes = dict(world_meshes)
        for shape in shapes:
            if shape['geom_id'] not in local_meshes:
                continue
            mesh = local_meshes[shape['geom_id']].copy()
            p, r = poses[shape['body']]
            mesh.vertices = p + r.apply(mesh.vertices)
            meshes[shape['geom_id']] = mesh
        return meshes, poses
    necks = [world_meshes[s['geom_id']].copy() for s in shapes if s['actor'] == 'guitar' and s['body'] == 'guitar']
    for mesh in necks:
        mesh.vertices = gr.inv().apply(mesh.vertices - gp)
    neck_planes = [ConvexHull(mesh.vertices).equations for mesh in necks]
    local_planes = {b: ConvexHull(local_meshes[next(s['geom_id'] for s in shapes if s['actor'] == 'human' and s['body'] == b)].vertices).equations for b in anchors}
    def separating_gap(va, pa, vb, pb):
        return max(float(np.min(vb @ pa[:, :3].T + pa[:, 3], axis=0).max()),
                   float(np.min(va @ pb[:, :3].T + pb[:, 3], axis=0).max()))
    def footprint(point, triangle, polygon, outward):
        normal = np.cross(polygon[1] - polygon[0], polygon[2] - polygon[0])
        normal /= np.linalg.norm(normal)
        if normal @ outward < 0:
            normal = -normal
        def projection(p):
            signed = float((p - polygon[0]) @ normal)
            proj = p - signed * normal
            edges = np.roll(polygon, -1, axis=0) - polygon
            signs = [float(np.cross(edge, proj - origin) @ normal) for origin, edge in zip(polygon, edges)]
            inside = all(s >= -1e-12 for s in signs) or all(s <= 1e-12 for s in signs)
            fractions = np.clip(np.sum((proj - polygon) * edges, axis=1) / np.sum(edges * edges, axis=1), 0, 1)
            boundary = float(np.linalg.norm(proj - polygon - fractions[:, None] * edges, axis=1).min())
            return {'inside': inside, 'signed_plane_distance_mm': signed * 1000,
                    'boundary_margin_mm': boundary * 1000 if inside else -boundary * 1000}
        return {'point': projection(point), 'triangle_vertices': [projection(p) for p in triangle],
                'triangle_G_m': triangle.tolist(), 'scope': 'point margin gated; neighboring facet extent observed, overhang permitted'}
    def certified_distance(mesh, polygon):
        # Centered millimetres resolve the sub-micrometre gate without changing source meshes.
        center = (mesh.vertices.mean(axis=0) + polygon.mean(axis=0)) / 2
        vertices = (mesh.vertices - center) * 1000
        patch = (polygon - center) * 1000
        planes = ConvexHull(vertices).equations
        _, unique = np.unique(np.round(planes, 10), axis=0, return_index=True)
        planes = planes[unique]
        matrix = np.column_stack((planes[:, :3], np.zeros((len(planes), 4))))
        sum_row = np.r_[np.zeros(3), np.ones(4)][None, :]
        def objective(x):
            delta = x[:3] - x[3:] @ patch
            return float(delta @ delta), np.r_[2 * delta, -2 * patch @ delta]
        result = minimize(objective, np.r_[vertices.mean(axis=0), np.full(4, .25)], jac=True,
            method='SLSQP', bounds=[(None, None)] * 3 + [(0, 1)] * 4,
            constraints=[LinearConstraint(matrix, -np.inf, -planes[:, 3]), LinearConstraint(sum_row, 1, 1)],
            options={'ftol': 1e-13, 'maxiter': 1000})
        x = result.x
        if not np.isfinite(x).all() or np.any(x[3:] < 0) or x[3:].sum() <= 0:
            raise RuntimeError('invalid source patch witness')
        raw_violation = float(np.maximum(matrix @ x + planes[:, 3], 0).max())
        raw_weight_sum_error = float(abs(x[3:].sum() - 1))
        # A primal/dual interval needs feasible witnesses, not a solver success flag.
        # Move any boundary violation toward an interior convex vertex mean.
        interior = vertices.mean(axis=0)
        initial_witness = x[:3].copy()
        at_point = planes[:, :3] @ x[:3] + planes[:, 3]
        at_interior = planes[:, :3] @ interior + planes[:, 3]
        active = at_point > -1e-8
        if active.any():
            fraction = float(np.min((-1e-8 - at_interior[active]) / (at_point[active] - at_interior[active])))
            x[:3] = interior + min(1., fraction) * (x[:3] - interior)
        x[3:] /= x[3:].sum()
        violation = float(np.maximum(matrix @ x + planes[:, 3], 0).max())
        weight_sum_error = float(abs(x[3:].sum() - 1))
        if violation > 1e-10 or weight_sum_error > 1e-10:
            raise RuntimeError('source distance witness feasibility failed')
        delta = x[:3] - x[3:] @ patch
        upper_mm = float(np.linalg.norm(delta))
        direction = delta / upper_mm if upper_mm else np.zeros(3)
        lower_mm = max(0., float((vertices @ direction).min() - (patch @ direction).max()))
        return {'distance_m': upper_mm / 1000, 'distance_lower_bound_m': lower_mm / 1000,
            'primal_dual_gap_m': (upper_mm - lower_mm) / 1000, 'feasibility_error_mm': violation,
            'optimizer_success': bool(result.success), 'optimizer_message': result.message,
            'unadjusted_plane_feasibility_error_mm': raw_violation,
            'unadjusted_weight_sum_error': raw_weight_sum_error, 'weight_sum_error': weight_sum_error,
            'feasible_witness_adjustment_mm': float(np.linalg.norm(x[:3] - initial_witness)),
            'palm_witness_world_m': (x[:3] / 1000 + center).tolist(),
            'target_witness_world_m': ((x[3:] @ patch) / 1000 + center).tolist(),
            'scope': 'source convex distance witness upper bound and support-plane lower bound; not cooked geometry'}
    front_points = {b: gr.inv().apply(fk(q0)[b][0] + fk(q0)[b][1].apply(grip['facets'][b]['point_local_m']) - gp)
                    for b in ('LH:index3', 'LH:middle3', 'LH:ring3', 'LH:pinky3')}
    rows, rejected = [], []
    for thumb_radius, clearance, label in [(radius, clear, 'thumb_' + str(radius) + '_clear_' + str(clear))
                                           for radius in (.1, .2) for clear in (.0003, .0007)]:
        if thumb_radius == .2 and any(row['thumb_radius_rad'] == .1 for row in rows):
            break
        lower, upper = bounds(thumb_radius)
        y = .045
        width = .027908 - .01631590413943356 * (y + .241803)
        palm_target = np.array([width + clearance, y, .0045])
        thumb_y = gr.inv().apply(fk(q0)['LH:thumb3'][0] + fk(q0)['LH:thumb3'][1].apply(observed_thumb['source_point_local_m']) - gp)[1] + .02
        thumb_width = .027908 - .01631590413943356 * (thumb_y + .241803)
        thumb_target = np.array([-thumb_width + .003, thumb_y, -.008 - clearance])
        goals = {'LH:thumb3': thumb_target, 'LH:palm': palm_target}
        def residual(values):
            q = q0.copy()
            q[indices] = values
            ps, poses = points(q), fk(q)
            result = list(np.concatenate([(ps[b] - goals[b]) * 1000 for b in anchors]))
            for body, initial_point in front_points.items():
                p, r = poses[body]
                point = gr.inv().apply(p + r.apply(grip['facets'][body]['point_local_m']) - gp)
                result.append((point[2] - initial_point[2]) * 1000)
            for body in anchors:
                p, r = poses[body]
                geom = next(s['geom_id'] for s in shapes if s['actor'] == 'human' and s['body'] == body)
                vertices = gr.inv().apply(p + r.apply(local_meshes[geom].vertices) - gp)
                rotation = gr.inv() * r
                normals = rotation.apply(local_planes[body][:, :3])
                origin = gr.inv().apply(p - gp)
                planes = np.column_stack((normals, local_planes[body][:, 3] - normals @ origin))
                gaps = [separating_gap(mesh.vertices, plane, vertices, planes) for mesh, plane in zip(necks, neck_planes)]
                result.extend(5000 * max(0., clearance - gap) for gap in gaps)
                desired = np.array([0., 0., 1.]) if body == 'LH:thumb3' else -np.array([1., .01631590413943356, 0.]) / np.linalg.norm([1., .01631590413943356, 0.])
                direction = rotation.apply(anchors[body]['source_normal_local'])
                result.extend(2 * (direction - desired))
            up = float(poses['LH:palm'][1].apply(proxy)[2])
            result.append(100 * max(0., -up))
            result.extend(2 * (values - q0[indices]))
            return np.array(result)
        opt = least_squares(residual, q0[indices], bounds=(lower[indices], upper[indices]),
                            max_nfev=150, ftol=1e-9, xtol=1e-9, gtol=1e-8)
        q = q0.astype(np.float32)
        q[indices] = opt.x.astype(np.float32)
        ps = points(q)
        meshes, poses = meshes_at(q)
        overlaps, cross_hands, self_cross = [], [], []
        humans = [s for s in shapes if s['actor'] == 'human']
        guitars = [s for s in shapes if s['actor'] == 'guitar']
        for h in humans:
            for g in guitars:
                radius = intersection(meshes[h['geom_id']], meshes[g['geom_id']])
                if radius > 1e-7:
                    overlaps.append({'human': h['body'], 'guitar': g['body'], 'common_radius_m': radius})
        for h in [s for s in humans if s['body'].startswith('LH:') or s['body'] == 'L_Wrist']:
            for g in [s for s in humans if s['body'].startswith('RH:') or s['body'] == 'R_Wrist']:
                radius = intersection(meshes[h['geom_id']], meshes[g['geom_id']])
                if radius > 1e-7:
                    cross_hands.append({'left': h['body'], 'right': g['body'], 'common_radius_m': radius})
        hand = [s for s in humans if s['body'].startswith('LH:') or s['body'] in ('L_Wrist', 'L_Elbow')]
        for k, h in enumerate(hand):
            for g in hand[k + 1:]:
                if graph_distance(h['body'], g['body']) <= 2:
                    continue
                radius = intersection(meshes[h['geom_id']], meshes[g['geom_id']])
                if radius > 1e-7:
                    self_cross.append({'a': h['body'], 'b': g['body'], 'common_radius_m': radius})
        offsets = {names[i]: float(target[i]) - float(q[i]) for i in left}
        reasons = []
        if np.any(q < native_lower) or np.any(q > native_upper):
            reasons.append('float32_native_initial_bounds')
        if np.any(q[indices] < lower[indices]) or np.any(q[indices] > upper[indices]):
            reasons.append('float32_search_Aug19_C02_offset_bounds')
        if any(abs(v) > .3 for v in offsets.values()):
            reasons.append('absolute_target_relative_offset_bounds')
        if overlaps:
            reasons.append('source_human_guitar_intersection')
        if cross_hands:
            reasons.append('source_cross_hands_intersection')
        if self_cross:
            reasons.append('source_nonadjacent_left_hand_intersection')
        up = float(poses['LH:palm'][1].apply(proxy)[2])
        if up <= 0:
            reasons.append('palm_up_proxy')
        anchor_error = {b: float(np.linalg.norm(ps[b] - goals[b]) * 1000) for b in anchors}
        if max(anchor_error.values()) > 3:
            reasons.append('source_anchor_goal_distance_over3mm')
        footprint_metrics, hull_patch_gaps = {}, {}
        for body in anchors:
            face = 'thumb' if body == 'LH:thumb3' else 'palm'
            polygon = np.array(grip['regions_G_m'][face])
            p, r = poses[body]
            triangle = gr.inv().apply(p + r.apply(anchors[body]['source_triangle_local_m']) - gp)
            footprint_metrics[body] = footprint(ps[body], triangle, polygon,
                                                [0, 0, -1] if face == 'thumb' else [1, 0, 0])
            geom = next(s['geom_id'] for s in shapes if s['actor'] == 'human' and s['body'] == body)
            hull_patch_gaps[body] = certified_distance(meshes[geom], gr.apply(polygon) + gp)
            m = footprint_metrics[body]['point']
            if not m['inside'] or m['boundary_margin_mm'] < (2 if face == 'thumb' else 3):
                reasons.append(body + '_point_patch_margin')
            if not (hull_patch_gaps[body]['distance_lower_bound_m'] >= .0003 - 1e-7
                    and hull_patch_gaps[body]['distance_m'] <= .001 + 1e-7):
                reasons.append(body + '_hull_finite_patch_gap')
        thumb_gap = hull_patch_gaps['LH:thumb3']
        witness_G = gr.inv().apply(np.array(thumb_gap['palm_witness_world_m']) - gp)
        target_G = gr.inv().apply(np.array(thumb_gap['target_witness_world_m']) - gp)
        toward = target_G - witness_G
        rear_direction_dot = float(toward[2] / np.linalg.norm(toward)) if np.linalg.norm(toward) else 0.
        rear_signed_mm = float((-.008 - witness_G[2]) * 1000)
        if rear_direction_dot <= .75 or rear_signed_mm < 0:
            reasons.append('thumb_hull_witness_not_rear_support')
        trial = copy.deepcopy(initial['input_trial'])
        trial['initial_settings']['joint_angles_rad'].update({names[i]: float(q[i]) for i in left})
        trial['main_target_offsets_rad'] = offsets
        state = copy.deepcopy(state0)
        for body, (p, r) in poses.items():
            state['human_body_states'][bodies.index(body)]['pose'] = {'p': dict(zip('xyz', p)), 'r': dict(zip('xyzw', r.as_quat()))}
        for i, value in enumerate(q):
            state['human_dof_states'][i]['pos'] = float(value)
        row = {'label': label, 'alpha': .5, 'target_clearance_m': clearance,
            'accepted_for_fresh_native': not reasons, 'reasons': reasons,
            'absolute_strap_rest_length_m': initial['absolute_strap_rest_length_m'],
            'thumb_radius_rad': thumb_radius, 'search_lower_rad': lower[indices].tolist(),
            'search_upper_rad': upper[indices].tolist(),
            'thumb_witness_toward_patch_GZ_dot': rear_direction_dot, 'thumb_witness_rear_signed_mm': rear_signed_mm,
            'expected_initial_angles_rad': q.astype(float).tolist(), 'expected_absolute_targets_rad': target.astype(float).tolist(),
            'source_state': state, 'anchor_goal_G_m': {b: p.tolist() for b, p in goals.items()},
            'anchor_G_m': {b: p.tolist() for b, p in ps.items()}, 'anchor_goal_error_mm': anchor_error,
            'palm_up_proxy_z': up, 'source_intersections': overlaps, 'cross_hand_intersections': cross_hands,
            'nonadjacent_left_hand_intersections': self_cross, 'optimizer_success': bool(opt.success),
            'source_footprint': footprint_metrics, 'source_hull_to_finite_patch': hull_patch_gaps,
            'optimizer_nfev': opt.nfev, 'actual_initial_coordinate_delta_rad': (q - q0).tolist()}
        if not reasons:
            composed = compose(q, main_indices, [offsets.get(names[i], 0.) for i in main_indices], native_lower, native_upper)
            if not np.array_equal(composed, target):
                raise AssertionError('absolute81 target float32 exactness')
            path = TRIALS / (label + '.json')
            save(path, trial)
            row.update(trial_path=str(path), trial_sha256=sha(path))
            rows.append(row)
        else:
            rejected.append(row)
        save(PHASE / 'partial_selection.json', {'rows': rows, 'rejected': rejected})
        print(json.dumps({'label': label, 'reasons': reasons, 'anchor_error_mm': anchor_error,
                          'source_overlaps': len(overlaps), 'self_cross': len(self_cross)}), flush=True)
    checks = {'source_search_bounds_native_Aug19_C02_and_offsets': True, 'source_queries_only': True,
              'accepted_candidates_no_source_intersections_and_same_targets': all(not r['reasons'] for r in rows),
              'sealed_inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()):
        raise AssertionError(checks)
    save(PHASE / 'proposal.json', {'checks': checks, 'input_sha256': hashes, 'rows': rows, 'rejected': rejected,
        'facets': dict(grip['facets'], **{b: {'point_local_m': a['source_point_local_m'],
            'normal_local': a['source_normal_local']} for b, a in anchors.items()}),
        'regions_G_m': grip['regions_G_m'],
        'front_outer_source_z_G_m': grip['front_outer_source_z_G_m'], 'left33_names': initial['left33_names'],
        'old_initial_angles_rad': q0.tolist(), 'saved_absolute_targets_rad': target.astype(float).tolist(),
        'anchors': anchors, 'native_initializations': 0, 'physics_steps': 0,
        'scope': 'rear-facing active source thumb triangle center; arm12 and thumb5 initial coordinates only; other64 held; finite patch distance interval and rear witness direction; no native physics/cooked/anatomical/stability certification; old81targets/gain/LA unchanged'})


if __name__ == '__main__':
    main()
