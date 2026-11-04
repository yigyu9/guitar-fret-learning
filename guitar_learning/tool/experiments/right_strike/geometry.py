"""Finite CPU pick-path proposals within unchanged right6 action bounds."""
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit_path(contract, starts, ends, string_index=2, direction=1):
    """Propose pre/post/lift q targets from one actual common body snapshot.

    This function never creates a simulator, changes state, or changes bounds.
    Full source-FK candidates do not certify tracking, collision or real hits.
    """
    import numpy as np
    from scipy.optimize import least_squares
    from scipy.spatial.transform import Rotation
    from guitar_learning.core.control import RIGHT_STRIKE_NAMES
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.paths import resolve_input_path
    import guitar_learning.core.control as control_module
    import guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 as fk_module
    started = time.monotonic()
    if type(string_index) is not int or not 0 <= string_index < 6 or type(direction) is not int or direction not in (-1, 1):
        raise ValueError('Runtime string0..5 and direction+1/-1 required')
    canonical = load_gpu_prepared_reset_contract('right')
    initial, expected = contract['initial'], canonical['initial']
    for key in ('joint_names', 'human_body_names', 'guitar_body_names'):
        if initial[key] != expected[key]:
            raise ValueError('Original ordered right-hand prepared identities required')
    for key in ('lower', 'upper'):
        if initial['native_PD_properties'][key] != expected['native_PD_properties'][key]:
            raise ValueError('Native joint ranges may not be changed')
    reference = np.asarray(contract['target105'], dtype=float)
    if reference.shape != (105,) or not np.array_equal(reference, canonical['target105']):
        raise ValueError('Unchanged reset-reference target105 required; actual arrival is a separate state')
    state = contract['state']
    if len(state['human_dof_states']) != 105:
        raise ValueError('Every ordered actual human DOF required')
    qbase = np.array([row['pos'] for row in state['human_dof_states']], dtype=float)
    qd = np.array([row['vel'] for row in state['human_dof_states']], dtype=float)
    if not np.isfinite(np.r_[qbase, qd]).all():
        raise ValueError('Finite actual joint position and velocity required')
    names = initial['joint_names']
    for kind, body_names in (('human', initial['human_body_names']),
                             ('guitar', initial['guitar_body_names']), ('chair', ['box'])):
        rows = state[kind+'_body_states']
        if len(rows) != len(body_names):
            raise ValueError('Complete ordered actual body states required')
        for name, row in zip(body_names, rows):
            if row.get('body_name', name) != name:
                raise ValueError('Actual body row identity mismatch')
            values = [row['pose']['p'][key] for key in 'xyz']+[row['pose']['r'][key] for key in 'xyzw']
            values += [row['vel'][field][key] for field in ('linear', 'angular') for key in 'xyz']
            if not np.isfinite(values).all() or abs(np.linalg.norm(values[3:7])-1.) > 1e-5:
                raise ValueError('Finite actual body pose/velocity and unit quaternion required')
    starts, ends = np.asarray(starts, dtype=float), np.asarray(ends, dtype=float)
    if starts.shape != (6, 3) or ends.shape != (6, 3) or not np.isfinite(np.r_[starts, ends]).all():
        raise ValueError('Finite guitar-local measured starts/ends[6,3] required')
    guitar = state['guitar_body_states'][0]['pose']
    gp = np.array([guitar['p'][key] for key in 'xyz'])
    gr = Rotation.from_quat([guitar['r'][key] for key in 'xyzw'])
    measured = []
    for suffix in ('', '_end'):
        points = [state['guitar_body_states'][initial['guitar_body_names'].index('G:string%d%s' % (i, suffix))]['pose']['p']
                  for i in range(1, 7)]
        measured.append(gr.inv().apply(np.array([[p[key] for key in 'xyz'] for p in points])-gp))
    if not np.allclose(starts, measured[0], atol=1e-5, rtol=0) or not np.allclose(ends, measured[1], atol=1e-5, rtol=0):
        raise ValueError('String geometry must match the same actual ordered guitar state')
    line = ends[string_index]-starts[string_index]
    length = float(np.linalg.norm(line[:2]))
    if length <= 1e-12 or abs(line[1]) <= 1e-12:
        raise ValueError('Nondegenerate finite string spanning the strike y axis required')
    normal = np.array([-line[1], line[0]])/length
    if normal[0] < 0:
        normal = -normal
    indices = [names.index(name) for name in RIGHT_STRIKE_NAMES]
    native_low = np.asarray(initial['native_PD_properties']['lower'], dtype=float)
    native_high = np.asarray(initial['native_PD_properties']['upper'], dtype=float)
    low = np.maximum(native_low[indices], reference[indices]-.25)
    high = np.minimum(native_high[indices], reference[indices]+.25)
    if not np.isfinite(np.r_[low, high]).all() or np.any(low >= high):
        raise ValueError('Unchanged finite right6 action bounds required')
    fk = full_fk(SimpleNamespace(names=names, human_bodies=initial['human_body_names'], q_ref=qbase), state)
    reproduced = fk(qbase)
    position_errors, rotation_errors = [], []
    for name, row in zip(initial['human_body_names'], state['human_body_states']):
        position, rotation = reproduced[name]
        actual_position = np.array([row['pose']['p'][key] for key in 'xyz'])
        actual_rotation = Rotation.from_quat([row['pose']['r'][key] for key in 'xyzw'])
        position_errors.append(float(np.linalg.norm(position-actual_position)))
        rotation_errors.append(float((actual_rotation.inv()*rotation).magnitude()))
    if max(position_errors) > 1e-8 or max(rotation_errors) > 1e-8:
        raise ValueError('Actual-state calibrated source FK reproduction failed')
    source_pins = dict(canonical['source_sha256'])
    for path, value in contract['source_sha256'].items():
        if path in source_pins and source_pins[path] != value:
            raise ValueError('Original source SHA expectation changed')
        source_pins[path] = value
    for path in (Path(__file__).resolve(), Path(fk_module.__file__).resolve(), Path(control_module.__file__).resolve()):
        name, current = str(path), _sha(path)
        if name in source_pins and source_pins[name] != current:
            raise ValueError('Existing source SHA expectation changed: '+name)
        source_pins.setdefault(name, current)
    for path, value in source_pins.items():
        if _sha(resolve_input_path(path)) != value:
            raise ValueError('Source geometry input SHA mismatch: '+str(path))
    fixed = sorted(set(range(105))-set(indices))
    attempts = []
    # This finite source-only comparison is declared before any native replay.
    strike_y_values = (-.35, -.32, -.29)
    for strike_y in strike_y_values:
        fraction = (strike_y-starts[string_index, 1])/line[1]
        if not 0 <= fraction <= 1:
            raise ValueError('Strike center outside the actual finite string')
        center = starts[string_index]+fraction*line
        center[2] -= .004
        pre = center.copy(); pre[:2] -= direction*.004*normal
        post = center.copy(); post[:2] += direction*.004*normal
        lift = post+np.array([0., 0., .008])
        seed = np.clip(qbase[indices], low+1e-10, high-1e-10)
        waypoints, errors = [], []
        for label, goal_G in zip(('pre', 'post', 'lift'), (pre, post, lift)):
            goal_W = gp+gr.apply(goal_G)
            origin = seed.copy()
            def residual(values):
                trial = qbase.copy(); trial[indices] = values
                return np.r_[1000*(fk(trial)['RH:pick'][0]-goal_W), .1*(values-origin)]
            fitted = least_squares(residual, seed, bounds=(low, high), max_nfev=60,
                                   ftol=1e-8, xtol=1e-8, gtol=1e-8)
            candidate = qbase.copy(); candidate[indices] = fitted.x
            if not np.array_equal(candidate[fixed], qbase[fixed]) or np.any(candidate[indices] < low) or np.any(candidate[indices] > high):
                raise ValueError('Candidate changed non-right6 axes or exceeded original action bounds')
            achieved_G = gr.inv().apply(fk(candidate)['RH:pick'][0]-gp)
            error = float(np.linalg.norm(achieved_G-goal_G))
            waypoints.append(candidate.tolist())
            errors.append(dict(waypoint=label, target_G_m=goal_G.tolist(), achieved_G_m=achieved_G.tolist(),
                position_error_m=error, geometry_candidate=error <= .001,
                optimizer_converged=bool(fitted.success), nfev=int(fitted.nfev)))
            seed = fitted.x.copy()
        attempts.append(dict(strike_y_m=strike_y, waypoints_q105=waypoints, errors=errors,
            geometry_candidate=all(row['geometry_candidate'] for row in errors),
            maximum_position_error_m=max(row['position_error_m'] for row in errors)))
    for path, value in source_pins.items():
        if _sha(resolve_input_path(path)) != value:
            raise ValueError('Source geometry input changed during search')
    best_index = min(range(len(attempts)), key=lambda index: attempts[index]['maximum_position_error_m'])
    best = attempts[best_index]
    found = best['geometry_candidate']
    snapshot = dict(q105=qbase.tolist(), body_state=state, starts_G_m=starts.tolist(), ends_G_m=ends.tolist())
    snapshot_sha = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode('utf-8')).hexdigest()
    return dict(schema='guitar_learning.right_strike_source_path.v1',
        outcome='geometry_candidate' if found else 'finite_search_unresolved',
        string_index=string_index, standard_string_1based=string_index+1, direction=direction,
        waypoint_labels=['pre', 'post', 'lift'], waypoints_q105=best['waypoints_q105'], errors=best['errors'],
        strike_y_m=best['strike_y_m'], selected_attempt=best_index, attempts=attempts,
        declared_strike_y_m=list(strike_y_values), selection='lowest maximum3waypoint position residual; fixed declaration order breaks ties',
        both_geometry_candidate_only=found, geometry_candidate=found, native_verified=False,
        physics_steps_executed=0, max_nfev_per_waypoint=60,
        right_indices=indices, right_joint_names=list(RIGHT_STRIKE_NAMES),
        action_reference_rad=reference[indices].tolist(), action_lower_rad=low.tolist(), action_upper_rad=high.tolist(),
        non_right6_preserved=True, source_snapshot_sha256=snapshot_sha,
        reproduction=dict(max_position_error_m=max(position_errors), max_rotation_error_rad=max(rotation_errors),
            pick_position_error_m=position_errors[initial['human_body_names'].index('RH:pick')]),
        actual_pick_G_m=gr.inv().apply(reproduced['RH:pick'][0]-gp).tolist(),
        pins=source_pins, elapsed_s=time.monotonic()-started,
        limitation='Finite source-FK proposals at one actual guitar pose only. No candidate is not impossibility. '
                   'No collision/load/tracking/strike/speed or recovery-return certification; no state injection.')
