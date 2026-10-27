"""Initial left-arm/hand FK proposals for three neck faces; no native dynamics."""
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v2'
TRIALS = ROOT / 'stability_adapter_2/trials/multi_face_grip_v2'
BASE = ROOT / 'stability_adapter_2/trials/recorded_trial_5s_v1/baseline.json'
INITIAL = PHASE.parent / 'palm_stiffness_only_v1/kp_1/initial_values.json'
REFERENCE = PHASE.parent / 'finger_grip_hold_v1/short/baseline'
PROPOSAL = ROOT / 'docs/2026-10-12/visualizations/grip_proposal/geometry.json'
DIGITS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def left_fk(names, bodies, initial, q0):
    from .environment import np
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    xml = ET.parse(ROOT / 'tab2body/assets/smpl_mpl_hands_body.xml').getroot()
    parents = {c: p for p in xml.iter('body') for c in p.findall('body')}
    tree = next(b for b in xml.iter('body') if b.get('name') == 'L_Thorax')
    relatives = {}
    for body in tree.iter('body'):
        name, parent = body.get('name'), parents[body].get('name')
        pp, pq = pose(initial['human_body_states'][bodies.index(parent)])
        bp, bq = pose(initial['human_body_states'][bodies.index(name)])
        rp = Rotation.from_quat(pq)
        joints = body.findall('joint')
        indices = [names.index(j.get('name')) for j in joints]
        basis = np.column_stack([np.fromstring(j.get('axis'), sep=' ') for j in joints]) if joints else np.zeros((3, 0))
        relatives[name] = (parent, rp.inv().apply(bp - pp), rp.inv() * Rotation.from_quat(bq), basis, indices)
    anchor = pose(initial['human_body_states'][bodies.index('Chest')])
    def fk(q):
        poses = {'Chest': (anchor[0], Rotation.from_quat(anchor[1]))}
        for name, (parent, position, relative0, basis, indices) in relatives.items():
            pp, rp = poses[parent]
            relative = Rotation.from_rotvec(basis @ q[indices]) * Rotation.from_rotvec(basis @ q0[indices]).inv() * relative0 if indices else relative0
            poses[name] = (pp + rp.apply(position), rp * relative)
        return poses
    return fk, {name: row[0] for name, row in relatives.items()}


def prepare_geometry(initial):
    from .environment import np
    from .replay_contact_geometry import recorded_probe
    from .render_best_run_video import set_saved_pose
    from .palm_side_source_checks import source_checks
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    import mujoco
    report = read(REFERENCE / 'report.json')
    if report['human_joint_names'] != initial['human_joint_names']:
        raise AssertionError('native name mapping')
    model, data, shapes = recorded_probe(REFERENCE, 0)
    set_saved_pose(model, mujoco, report, initial['native_initial_state'])
    mujoco.mj_forward(model, data)
    meshes, _, _ = source_checks((model, data, shapes))
    state = initial['native_initial_state']
    gp, gq = pose(state['guitar_body_states'][0])
    gr = Rotation.from_quat(gq)
    locals_ = {}
    facets = {}
    for shape in shapes:
        name = shape['body']
        if not (name.startswith('LH:') or name in ('L_Wrist', 'L_Elbow', 'L_Shoulder', 'L_Thorax')):
            continue
        p, q = pose(state['human_body_states'][report['human_body_names'].index(name)])
        mesh = meshes[shape['geom_id']].copy()
        mesh.vertices = Rotation.from_quat(q).inv().apply(mesh.vertices - p)
        locals_[shape['geom_id']] = (name, mesh)
        if name in ['LH:' + d + '3' for d in DIGITS]:
            ids = np.flatnonzero(mesh.face_normals @ np.array([0., 0., -1.]) > .75)
            if not len(ids):
                raise AssertionError('no palmar-side distal collision facet: ' + name)
            i = ids[np.argmax(mesh.area_faces[ids])]
            facets[name] = {'point_local_m': mesh.triangles_center[i].tolist(), 'normal_local': mesh.face_normals[i].tolist(),
                            'area_m2': float(mesh.area_faces[i]), 'scope': 'selected collision facet; anatomical pad identity unverified'}
    old = read(PHASE.parent / 'palm_neck_side_v1/facet_distal_search/search.json')
    facets['LH:palm'] = {'point_local_m': old['palmar_facet_point_local_m'], 'normal_local': old['palmar_facet_normal_local']}
    neck = next(s for s in shapes if s['actor'] == 'guitar' and s['body'] == 'guitar'
                and gr.inv().apply(meshes[s['geom_id']].vertices - gp)[:, 1].min() < 0)
    neck_mesh = meshes[neck['geom_id']].copy()
    neck_mesh.vertices = gr.inv().apply(neck_mesh.vertices - gp)
    proposal = read(PROPOSAL)
    front = np.array(proposal['regions_G_m']['front'])
    ylo, yhi = front[:, 1].min(), front[:, 1].max()
    front_z = .0093
    for s in shapes:
        if s['actor'] != 'guitar':
            continue
        v = gr.inv().apply(meshes[s['geom_id']].vertices - gp)
        near = v[(v[:, 1] >= ylo) & (v[:, 1] <= yhi) & (abs(v[:, 0]) <= .03)]
        if len(near):
            front_z = max(front_z, float(near[:, 2].max()))
    return report, (model, data, shapes), meshes, locals_, facets, gp, gr, neck_mesh, float(front_z)


def nearest_face(point, face, front_z, clear, regions):
    from .environment import np
    region = regions[face]
    vertices = np.array(region)
    y = float(np.clip(point[1], vertices[:, 1].min(), vertices[:, 1].max()))
    width = .027908 - .01631590413943356 * (y + .241803)
    if face == 'palm':
        normal = np.array([1., .01631590413943356, 0.]); normal /= np.linalg.norm(normal)
        target = np.array([width, y, np.clip(point[2], -.008, .0093)]) + clear * normal
    else:
        normal = np.array([0., 0., -1. if face == 'thumb' else 1.])
        target = np.array([np.clip(point[0], -width, width), y, -.008 if face == 'thumb' else front_z]) + clear * normal
    return target, normal


def main():
    PHASE.mkdir(exist_ok=False); TRIALS.mkdir(exist_ok=False)
    source_path = PHASE.parent / 'palm_stiffness_only_v1/analysis.json'
    hashes = {str(source_path): sha(source_path)}; source = read(source_path)
    paths = [Path(p) for p in source['input_sha256']] + [INITIAL, BASE, PROPOSAL, Path(__file__).resolve(),
        ROOT / 'stability_adapter_2/MULTI_FACE_GRIP_PLAN.md', ROOT / 'docs/2026-08-19/정리.txt',
        ROOT / 'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json', REFERENCE / 'report.json', REFERENCE / 'states.json']
    paths += [Path(__file__).with_name(n) for n in ('palm_side_source_checks.py', 'face_referenced_geometry.py',
        'replay_contact_geometry.py', 'render_best_run_video.py', 'initial_overlap.py', 'search_palm_neck_side.py')]
    hashes.update({str(p): sha(p) for p in paths})
    if not all(source['checks'].values()) or any(sha(p) != h for p, h in source['input_sha256'].items()):
        raise AssertionError('prior source closure changed')
    from .environment import np
    from .build_fixed_lower_asset import pose
    from .palm_side_source_checks import source_checks, intersection
    from .render_best_run_video import set_saved_pose
    from scipy.spatial import ConvexHull
    from scipy.spatial.transform import Rotation
    from scipy.optimize import least_squares
    import mujoco
    initial = read(INITIAL); base = read(BASE)
    report, probe, _, locals_, facets, gp, gr, neck, front_z = prepare_geometry(initial)
    model, data, shapes = probe
    names, bodies = initial['human_joint_names'], report['human_body_names']
    q0 = np.array([d['pos'] for d in initial['native_initial_state']['human_dof_states']])
    indices = np.array([i for i, n in enumerate(names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:'))])
    arm = indices[:12]
    low, high = np.array(initial['PD_properties']['lower']), np.array(initial['PD_properties']['upper'])
    low[arm] = np.maximum(low[arm], q0[arm] - .15); high[arm] = np.minimum(high[arm], q0[arm] + .15)
    fk, parents = left_fk(names, bodies, initial['native_initial_state'], q0)
    proxy = np.array(read(PHASE.parent / 'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    planes = ConvexHull(neck.vertices).equations
    regions = read(PROPOSAL)['regions_G_m']
    local_planes = {i: ConvexHull(mesh.vertices).equations for i, (_, mesh) in locals_.items()}
    def graph_distance(a, b):
        chain = []; current = a
        while current in parents: chain.append(current); current = parents[current]
        chain.append(current); steps = 0; current = b
        while current not in chain and current in parents: steps += 1; current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    self_pairs = [(a, b) for k, a in enumerate(locals_) for b in list(locals_)[k + 1:]
                  if graph_distance(locals_[a][0], locals_[b][0]) > 2]
    def separating_gap(va, pa, vb, pb):
        return max(float(np.min(vb @ pa[:, :3].T + pa[:, 3], axis=0).max()),
                   float(np.min(va @ pb[:, :3].T + pb[:, 3], axis=0).max()))
    rows = []
    def evaluate(q, clear):
        poses = fk(q); res = []; metrics = {}
        for name, facet in facets.items():
            p, rotation = poses[name]
            point = gr.inv().apply(p + rotation.apply(facet['point_local_m']) - gp)
            face = 'palm' if name == 'LH:palm' else 'thumb' if name == 'LH:thumb3' else 'front'
            target, normal = nearest_face(point, face, front_z, clear, regions)
            direction = gr.inv().apply(rotation.apply(facet['normal_local']))
            res.extend(1000 * (point - target)); res.extend(1 * (direction + normal))
            metrics[name] = {'face': face, 'point_G_m': point.tolist(), 'distance_to_offset_patch_m': float(np.linalg.norm(point - target)),
                             'inward_alignment_dot': float(direction @ -normal)}
        up = float(poses['LH:palm'][1].apply(proxy)[2])
        res.extend([100 * max(0., -up), 2 * (1 - up)])
        transformed = {}
        for geom, (name, mesh) in locals_.items():
            p, r = poses[name]
            vertices = gr.inv().apply(p + r.apply(mesh.vertices) - gp)
            rotation = gr.inv() * r
            normals = rotation.apply(local_planes[geom][:, :3])
            origin = gr.inv().apply(p - gp)
            body_planes = np.column_stack((normals, local_planes[geom][:, 3] - normals @ origin))
            transformed[geom] = vertices, body_planes
            gap = separating_gap(neck.vertices, planes, vertices, body_planes)
            res.append(5000 * max(0., clear - gap))
        for a, b in self_pairs:
            va, pa = transformed[a]; vb, pb = transformed[b]
            gap = separating_gap(va, pa, vb, pb)
            res.append(5000 * max(0., .0001 - gap))
        res.extend(10 * (q[[names.index('LH:' + d + '1_z') for d in DIGITS[1:]]] - q0[[names.index('LH:' + d + '1_z') for d in DIGITS[1:]]]))
        res.extend(.02 * (q[indices] - q0[indices]))
        return np.array(res), metrics, up, poses
    for seed_id, amount in enumerate((.3, 1., 1.3)):
        q = q0.copy()
        for digit in DIGITS[1:]:
            for suffix, weight in (('1_x', .7), ('2', 1.), ('3', .6)):
                q[names.index('LH:' + digit + suffix)] += amount * weight
        thumb = ((.65, -.05, .05), (.35, -.9, .6), (.65, -1.4, 1.3))[seed_id]
        for axis, value in zip('xyz', thumb): q[names.index('LH:thumb1_' + axis)] = value
        clear = .0003 if seed_id < 2 else .001
        def residual(values):
            trial_q = q0.copy(); trial_q[indices] = values
            return evaluate(trial_q, clear)[0]
        fit = least_squares(residual, np.clip(q[indices], low[indices] + 1e-8, high[indices] - 1e-8),
                            bounds=(low[indices], high[indices]), max_nfev=300, ftol=1e-8, xtol=1e-8, gtol=1e-8)
        q = q0.copy(); q[indices] = fit.x
        _, metrics, up, poses = evaluate(q, clear)
        state = copy.deepcopy(initial['native_initial_state'])
        for name, (p, r) in poses.items():
            state['human_body_states'][bodies.index(name)]['pose'] = {'p': dict(zip('xyz', p)), 'r': dict(zip('xyzw', r.as_quat()))}
        for i, value in enumerate(q): state['human_dof_states'][i]['pos'] = float(value)
        set_saved_pose(model, mujoco, report, state); mujoco.mj_forward(model, data)
        meshes, overlaps, crosshands = source_checks(probe)
        hand_shapes = [s for s in shapes if s['body'].startswith('LH:') or s['body'] in ('L_Wrist', 'L_Elbow')]
        self_cross = []
        for i, a in enumerate(hand_shapes):
            for b in hand_shapes[i + 1:]:
                if graph_distance(a['body'], b['body']) <= 2: continue
                radius = intersection(meshes[a['geom_id']], meshes[b['geom_id']])
                if radius > 1e-7: self_cross.append({'a': a['body'], 'b': b['body'], 'common_radius_m': radius})
        accepted = up > 0 and not overlaps and not crosshands and not self_cross and max(m['distance_to_offset_patch_m'] for m in metrics.values()) <= .003
        label = 'seed_' + str(seed_id)
        settings = copy.deepcopy(base); settings['initial_settings']['joint_angles_rad'].update({names[i]: float(q[i]) for i in indices})
        path = TRIALS / (label + '.json'); path.write_text(json.dumps(settings, indent=2) + '\n')
        row = {'label': label, 'fit_success': bool(fit.success), 'nfev': fit.nfev, 'cost': float(fit.cost),
               'metrics': metrics, 'target_clearance_m': clear, 'palm_up_proxy_z': up, 'source_intersections': overlaps, 'cross_hand_intersections': crosshands,
               'nonadjacent_left_hand_intersections': self_cross, 'accepted_for_fresh_native': bool(accepted),
               'trial_path': str(path), 'trial_sha256': sha(path), 'source_state': state}
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != 'source_state'}), flush=True)
    checks = {'inputs_unchanged': all(sha(p) == h for p, h in hashes.items()), 'native_initializations_zero': True}
    result = {'checks': checks, 'input_sha256': hashes, 'rows': rows, 'facets': facets, 'front_outer_source_z_G_m': front_z,
              'native_initializations': 0, 'physics_steps': 0, 'scope': 'source-only expmap FK hypothesis; fresh native validation required; facets are collision proxies, not anatomical pad certification; self graph-distance<=2 pairs excluded'}
    (PHASE / 'search.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    if not all(checks.values()): raise AssertionError(checks)


if __name__ == '__main__':
    main()
