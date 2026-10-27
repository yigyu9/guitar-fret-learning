"""Bounded, snapshot-only geometric proposals, never native reachability proof.

FK is calibrated at measured native q0, independently of the codec's fixed qref.
Source distal mesh vertices approximate a contact surface; PhysX convex cooking,
contact force, joint-coordinate increments and dynamic tracking need native tests.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from guitar_learning.native.paths import ASSETS, resolve_input_path


DEFAULT_ASSET = ASSETS / 'tab2body/assets/smpl_mpl_hands_body.xml'
FINGERS = {1: 'index', 2: 'middle', 3: 'ring', 4: 'pinky'}


def input_paths(asset_path=None):
    """Exact static files read by this solver, available before native creation."""
    asset = resolve_input_path(asset_path or DEFAULT_ASSET)
    tree = ET.parse(asset)
    compiler = tree.find('compiler')
    folder = asset.parent / (compiler.get('meshdir', '') if compiler is not None else '')
    meshes = {m.get('name'): (folder / m.get('file')).resolve() for m in tree.findall('./asset/mesh')}
    paths = {asset, ASSETS / 'stability_adapter_2/assets/humanoid_fixed_lower.xml'}
    for body in tree.iter('body'):
        if body.get('name') in {'LH:' + f + str(n) for f in FINGERS.values() for n in (2, 3)}:
            paths.update(meshes[g.get('mesh')] for g in body.findall('geom') if g.get('type') == 'mesh')
    return sorted(str(p.resolve()) for p in paths)


def _surface_vertices(asset_path, segment=3):
    import numpy as np
    import trimesh
    tree = ET.parse(asset_path)
    compiler = tree.find('compiler')
    folder = Path(asset_path).parent / (compiler.get('meshdir', '') if compiler is not None else '')
    meshes = {m.get('name'): m for m in tree.findall('./asset/mesh')}
    result = {}
    for finger in FINGERS.values():
        body = next(b for b in tree.iter('body') if b.get('name') == 'LH:' + finger + str(segment))
        chunks = []
        for geom in body.findall('geom'):
            if geom.get('type') != 'mesh':
                continue
            if geom.get('quat') or geom.get('euler'):
                raise ValueError('rotated distal source geometry requires explicit transform support')
            mesh = meshes[geom.get('mesh')]
            vertices = np.asarray(trimesh.load(folder / mesh.get('file'), process=False).vertices)
            vertices = vertices * np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
            vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
            chunks.append(vertices)
        if not chunks:
            raise ValueError('distal source mesh required; body origin cannot replace contact surface')
        result[finger] = np.unique(np.vstack(chunks), axis=0)
    return result


def _check_fk_axes(asset_path):
    """The reused FK reads its original XML, so require matching upper axes."""
    fk_asset = ASSETS / 'stability_adapter_2/assets/humanoid_fixed_lower.xml'
    def joints(path):
        tree = ET.parse(path)
        torso = next(body for body in tree.iter('body') if body.get('name') == 'Torso')
        return {body.get('name'): [(joint.get('name'), joint.get('axis'))
                for joint in body.findall('joint')] for body in torso.iter('body')}
    if joints(asset_path) != joints(fk_asset):
        raise ValueError('source asset upper joint axes differ from the calibrated FK model')


def solve(sample, codec, targets, *, joint_names, human_names, seed=7,
          max_nfev=80, starts=2, asset_path=None, context_targets=()):
    """Return A, A+B preparation, B and release endpoint commands.

    Commands use the unmodified codec's effective endpoints. The requested81
    vector is an actuator target, not an actual-state write. No pose is adopted
    as successful here, even when the geometric optimizer converges.
    """
    import numpy as np
    from scipy.optimize import least_squares
    from guitar_learning.native.upper_arm_static_geometry_v1 import calibrated_upper_fk
    from guitar_learning.core.geometry_v1 import frame, fret_target
    from guitar_learning.tool.experiments.local_skills.controls import normalize_target

    if type(starts) is not int or starts < 1 or type(max_nfev) is not int or max_nfev < 1:
        raise ValueError('positive integer starts and max_nfev required')
    if len(targets) not in (1, 2) or any(t.finger not in FINGERS or not t.fret for t in targets):
        raise ValueError('one or two explicit fretted targets required')
    if any(t.finger not in FINGERS or not t.fret for t in context_targets):
        raise ValueError('explicit fretted context targets required')
    names, bodies = tuple(joint_names), tuple(human_names)
    state = sample['native']
    q0 = np.asarray([row['pos'] for row in state['human_dof_states']], dtype=float)
    if (len(names) != 105 or len(set(names)) != 105 or q0.shape != (105,)
            or not np.isfinite(q0).all() or len(bodies) != len(state['human_body_states'])
            or len(set(bodies)) != len(bodies)):
        raise ValueError('aligned finite native105 joint and unique body snapshot required')
    if sample['geometry']['physics_step'] != state['physics_step']:
        raise ValueError('same-step native and guitar geometry required')
    asset = resolve_input_path(asset_path or DEFAULT_ASSET)
    _check_fk_axes(asset)
    surfaces = _surface_vertices(asset)
    middle_surfaces = _surface_vertices(asset, segment=2)
    fk, _ = calibrated_upper_fk(names, bodies, state, q0)
    original = fk(q0)
    calibration = max(float(np.linalg.norm(original[name][0] - frame(body)[0]))
                      for name, body in zip(bodies, state['human_body_states']))
    rotation_error = max(float((original[name][1].inv() * frame(body)[1]).magnitude())
                         for name, body in zip(bodies, state['human_body_states']))
    if calibration > 1e-8 or rotation_error > 1e-8:
        raise ValueError('FK must reproduce the measured calibration snapshot')
    upper_indices = np.array([names.index(name) for name in codec.names])
    active_indices = codec.active_indices
    reference = np.asarray(codec.q_ref[active_indices])
    lower, upper = np.asarray(codec.action_lower), np.asarray(codec.action_upper)
    if (reference.shape != (39,) or np.any(lower > reference) or np.any(reference > upper)):
        raise ValueError('valid fixed codec39 reference and effective endpoints required')
    variable = np.flatnonzero(upper[:33] - lower[:33] > 1e-12)
    if not len(variable):
        raise ValueError('left-hand action range is empty')
    gp, gr = frame(state['guitar_body_states'][0])
    geometry = dict(sample['geometry'])
    for key in ('starts_G_m', 'ends_G_m', 'fret_markers_G_m'):
        geometry[key] = np.asarray(geometry[key], dtype=float)
    goal_targets = {FINGERS[t.finger]: t for t in targets}
    if len(goal_targets) != len(targets):
        raise ValueError('different fingers required for the two-target overlap proposal')
    context_blockers = []
    for target in context_targets:
        finger = FINGERS[target.finger]
        if (finger not in goal_targets and any(target.string == t.string and target.fret > t.fret
                                               for t in targets)):
            goal_targets[finger] = target
            context_blockers.append(dict(finger=finger, string=target.string, fret=target.fret,
                target_id=target.target_id, source='explicit source-score context',
                reason='higher fret on same string; lift proposal, not measured contact'))
    goals = {finger: np.asarray(fret_target(geometry, t.string + 1, t.fret))
             for finger, t in goal_targets.items()}
    target_frets = {finger: t.fret for finger, t in goal_targets.items()}
    z_plane = float(np.mean(np.asarray(sample['geometry']['starts_G_m'])[:, 2]))
    rng = np.random.RandomState(seed)

    def requested(x):
        target = np.asarray(codec.q_ref).copy()
        active = reference.copy()
        active[variable] = x
        target[active_indices] = active
        q = q0.copy()
        q[upper_indices] = target
        return target, q

    def points(q, *, lift=False):
        poses = fk(q)
        result = {}
        for finger, vertices in surfaces.items():
            p, rotation = poses['LH:' + finger + '3']
            chunks = [gr.inv().apply(p + rotation.apply(vertices) - gp)]
            if lift:
                p, rotation = poses['LH:' + finger + '2']
                chunks.append(gr.inv().apply(p + rotation.apply(middle_surfaces[finger]) - gp))
            result[finger] = np.vstack(chunks)
        return result

    def residual(x, required):
        _, q = requested(x)
        vertices = points(q)
        lift_vertices = points(q, lift=True)
        values = []
        for finger, goal in goals.items():
            if finger in required:
                desired = goal.copy()
                desired[2] -= .0005
                witness = vertices[finger][np.argmin(np.linalg.norm(vertices[finger] - desired, axis=1))]
                values.extend((witness - desired) / .004)
        # Lower-fret precontact is permitted while a higher fret sounds. Do not
        # demand an unrelated finger lift or turn other-string contact into error.
        # B needs the previous higher-fret ring lifted; release lifts both goals.
        for finger in goals:
            if finger not in required and (not required or
                    target_frets[finger] > max(target_frets[f] for f in required)):
                values.append(max(0., z_plane + .004 - float(lift_vertices[finger][:, 2].min())) / .006)
        values.extend(.015 * (x - reference[variable]) / np.maximum(.01, upper[variable] - lower[variable]))
        return np.asarray(values)

    first = FINGERS[targets[0].finger]
    second = FINGERS[targets[-1].finger]
    modes = [('single_a', {first}), ('overlap', {first, second}),
             ('single_b', {second}), ('release', set())]
    candidates = []
    anchor = np.clip(reference[variable], lower[variable], upper[variable])
    for name, required in modes:
        attempts = []
        best = None
        for start in range(starts):
            x = anchor if start == 0 else rng.uniform(lower[variable], upper[variable])
            result = least_squares(residual, x, args=(required,),
                bounds=(lower[variable], upper[variable]), max_nfev=max_nfev)
            cost = float(np.sum(result.fun ** 2))
            attempts.append(dict(start=start, cost=cost, nfev=int(result.nfev), converged=bool(result.success)))
            if best is None or cost < best[0]:
                best = cost, result.x.copy()
        target, q = requested(best[1])
        action = normalize_target(target[active_indices], reference, lower, upper)
        if any(action[i] != 0. for i in range(33, 39)):
            raise ValueError('right hand must remain at its fixed target')
        vertices = points(q)
        lift_vertices = points(q, lift=True)
        diagnostics = {finger: dict(target_G_m=goal.tolist(),
            nearest_source_surface_distance_m=float(np.min(np.linalg.norm(vertices[finger] - goal, axis=1))),
            minimum_source_surface_height_G_m=float(vertices[finger][:, 2].min()),
            minimum_lift_surface_height_G_m=float(lift_vertices[finger][:, 2].min()),
            lift_surface_scope='finger2+3',
            required=finger in required) for finger, goal in goals.items()}
        candidates.append(dict(name=name, action39=action, requested_target81_rad=target.tolist(),
            objective=best[0], optimization_attempts=attempts, geometry=diagnostics,
            native_success=False, adoption='proposal_only_native_contact_and_tracking_unverified'))
        anchor = best[1]
    return dict(schema='guitar_learning.transition_geometric_plan.v1', candidates=candidates,
        input_paths=input_paths(asset), measured_native105_rad=q0.tolist(),
        declared_context_blockers=context_blockers,
        codec_reference81_rad=np.asarray(codec.q_ref).tolist(),
        physics_step=int(state['physics_step']), seed=seed,
        calibration=dict(position_max_m=calibration, rotation_max_rad=rotation_error,
            scope='self-consistency at q0 only; incremental FK/native coordinates and dynamic tracking unverified'),
        goal_frame='single measured guitar snapshot; no fixed-guitar forces or pose writes',
        surface_scope='distal source mesh vertices including XML scale/geom translation; not PhysX cooked convex witnesses or calibrated pads',
        lift_surface_scope='finger2+3 source mesh vertices; contact objective remains finger3 only',
        native_validation_required=True, success=False)
