"""Current-model pad reachability candidates and bounded fixed/free replay.

Geometry is a source-FK search, not a reachability proof. Replay uses only the
existing 39-action controller after prepared reset. Its static-goal contact
metrics are separate from song achievement, pressure and acoustic success.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BUNDLE = ROOT/'data/song_bundles/05_BN2-131-B_solo'
SCHEMA = 'guitar_learning.press_acquisition.v1'
REPRESENTATIVE_ROWS = (0, 4, 8, 12)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    from guitar_learning.training.recording import write as write_json
    write_json(path, value)


def select_targets(task):
    """Four unique goals/finger: most frequent, low, high, then next frequent."""
    from collections import Counter
    frequencies = Counter((t.string, t.fret, t.finger) for t in task.targets)
    rows = []
    for finger in range(1, 5):
        keys = [key for key in frequencies if key[2] == finger]
        if len(keys) < 4:
            raise ValueError('Four distinct source goals per finger required')
        ranked = sorted(keys, key=lambda key: (-frequencies[key], key[1], key[0]))
        chosen = []
        for key in [ranked[0], min(keys, key=lambda k: (k[1], k[0])),
                    max(keys, key=lambda k: (k[1], k[0]))]+ranked:
            if key not in chosen:
                chosen.append(key)
            if len(chosen) == 4:
                break
        for string, fret, finger_id in chosen:
            note_index = next(i for i, t in enumerate(task.targets)
                              if (t.string, t.fret, t.finger) == (string, fret, finger_id))
            rows.append(dict(row=len(rows), string=string, physical_string=string+1,
                fret=fret, finger=finger_id, frequency=frequencies[(string, fret, finger_id)],
                source_note_index=note_index, target_id=task.targets[note_index].target_id))
    return rows


def action_bounds(contract):
    """Same left-hand action bounds as BatchedController, without a simulator."""
    import numpy as np
    from guitar_learning.core.control import ACTIVE_NAMES
    initial = contract['initial']
    names = initial['joint_names']
    active = np.array([names.index(n) for n in ACTIVE_NAMES])
    reference = np.asarray(contract['target105'])[active]
    low = np.asarray(initial['native_PD_properties']['lower'])[active]
    high = np.asarray(initial['native_PD_properties']['upper'])[active]
    half = np.array([.5 if n.startswith('LH:') else .35 if n.startswith('L_') else .25
                     for n in ACTIVE_NAMES])
    fingers = np.array([n.startswith('LH:') for n in ACTIVE_NAMES])
    half[fingers] = np.maximum(reference-low, high-reference)[fingers]
    return active, np.maximum(low, reference-half), np.minimum(high, reference+half)


def trajectory_actions(desired, current, reference, low, high, incremental, max_speed=1.):
    """Invert the existing codec; never assign targets or actual joint state."""
    import torch
    if (desired.ndim != 2 or desired.shape[-1] != 39 or current.shape != desired.shape or
            reference.shape != low.shape or low.shape != high.shape or low.shape != (39,) or
            incremental.shape != (39,) or incremental.dtype != torch.bool or
            not 0 < max_speed <= 4):
        raise ValueError('Aligned action39 trajectories and speed in(0,4] required')
    if not all(bool(torch.isfinite(x).all()) for x in (desired, current, reference, low, high)):
        raise ValueError('Finite inverse-codec inputs required')
    if bool(((desired < low-1e-6) | (desired > high+1e-6)).any()):
        raise ValueError('Trajectory exceeds current controller action bounds')
    delta = desired-reference
    span = torch.where(delta >= 0, high-reference, reference-low)
    actions = torch.where(span > 0, delta/span.clamp_min(1e-30), torch.zeros_like(delta))
    actions[:, incremental] = ((desired-current)*15).clamp(-max_speed/4, max_speed/4)[:, incremental]
    return actions.clamp(-1, 1)


def diagnostic_streak(previous, current, streak, best, dt=1/240.):
    """Both real endpoints required; repeated short runs do not accumulate."""
    import numpy as np
    streak = np.where(previous & current, streak+dt, 0.)
    return streak, np.maximum(best, streak)


def pad_axis_flags(points, starts, ends, strings, low, high, plane):
    """Independent any-sample axes, on the same press plane as pad candidates."""
    import torch
    from guitar_learning.gpu.press_surface import project_press_strings
    projected_starts, projected_ends = project_press_strings(starts, ends, plane)
    rows = torch.arange(points.shape[0], device=points.device)
    start = projected_starts[rows, strings]
    line = projected_ends[rows, strings]-start
    unit = plane[:3]/torch.linalg.vector_norm(plane[:3])
    height = (points*unit).sum(-1)+plane[3]/torch.linalg.vector_norm(plane[:3])
    projected = points-height[..., None]*unit
    fraction = ((projected-start[:, None])*line[:, None]).sum(-1)/line.square().sum(-1)[:, None]
    lateral = torch.linalg.vector_norm(projected-start[:, None]-fraction[..., None]*line[:, None], dim=-1)
    return dict(cell=((points[..., 1] >= low[:, None]) & (points[..., 1] <= high[:, None])).any(-1),
        lateral=(lateral <= .003).any(-1), height=((height >= -.001) & (height <= .003)).any(-1))


def goal_measurement(goal, **metrics):
    """Keep source search distance distinct from physical replay distance."""
    result = dict(goal)
    result['source_geometry_minimum_distance_m'] = result.pop('minimum_distance_m')
    result.update(metrics)
    return result


def integral_tracking_offset(offset, nominal, actual, low, high, mask, *,
                             gain_per_s=1.5, max_offset_rad=.1, dt_s=1/60.):
    """Diagnostic outer feedback with clamped integrator-state antiwindup.

    Returned values remain action-space target offsets. They are never written
    into the native target/DOF tensors; the caller uses trajectory_actions.
    """
    import torch
    if (offset.ndim != 2 or offset.shape[-1] != 39 or
            nominal.shape != offset.shape or actual.shape != offset.shape or mask.shape != offset.shape or
            mask.dtype != torch.bool or low.shape != (39,) or high.shape != (39,) or
            not 0 < gain_per_s <= 2 or not 0 < max_offset_rad <= .1 or not 0 < dt_s <= 1/60.+1e-12):
        raise ValueError('Bounded diagnostic integral feedback requires aligned action39 arrays')
    if not all(bool(torch.isfinite(x).all()) for x in (offset, nominal, actual, low, high)):
        raise ValueError('Finite diagnostic integral feedback required')
    updated = (offset+gain_per_s*dt_s*(nominal-actual)).clamp(-max_offset_rad, max_offset_rad)
    # Store only the offset that survives actual action-range saturation.
    bounded = torch.maximum(torch.minimum(nominal+updated, high), low)-nominal
    return torch.where(mask, bounded, torch.zeros_like(bounded))


def source_geometry(contract, goals):
    import numpy as np
    from guitar_learning.gpu.press_surface import load_press_surface
    from guitar_learning.gpu.rigid_guitar import _ASSET_DIR
    surface = load_press_surface([r['string'] for r in goals], [r['fret'] for r in goals])
    manifest = json.loads((_ASSET_DIR/'manifest.json').read_text())
    markers = dict(zip(manifest['logical_body_names'], np.array(manifest['logical_position_root_m'])))
    starts = np.array([markers['G:string%d'%i] for i in range(1, 7)])
    ends = np.array([markers['G:string%d_end'%i] for i in range(1, 7)])
    plane = np.array(surface['plane_G'])
    for points in (starts, ends):
        points[:, 2] = -(points[:, :2]@plane[:2]+plane[3])/plane[2]
    frets = np.array([markers['G:nut'][1]]+[markers['G:fret%d'%i][1] for i in range(1, 23)])
    low = np.array([min(frets[r['fret']-1:r['fret']+1]) for r in goals])
    high = np.array([max(frets[r['fret']-1:r['fret']+1]) for r in goals])
    return starts, ends, low, high, plane, surface


def search_geometry(bundle, out, max_nfev=160):
    """Optimize actual patch position/direction within current action bounds."""
    import numpy as np
    from scipy.optimize import least_squares
    from scipy.spatial.transform import Rotation
    from types import SimpleNamespace
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    from guitar_learning.song.task import make_task
    out.mkdir(parents=True, exist_ok=False)
    contract = load_prepared_reset_contract()
    task = make_task(bundle)
    goals = select_targets(task)
    # Commit the selection and capture row IDs before any search/replay result.
    write(out/'targets.json', dict(schema=SCHEMA, goals=goals,
        representative_rows=list(REPRESENTATIVE_ROWS), selection='frequency plus fret extremes; deterministic source order'))
    state = contract['state']
    names, bodies = contract['initial']['joint_names'], contract['initial']['human_body_names']
    q0 = np.array([r['pos'] for r in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=bodies, q_ref=q0), state)
    pad = load_fingertip_pad()
    starts, ends, low, high, plane, surface = source_geometry(contract, goals)
    guitar = state['guitar_body_states'][0]['pose']
    gp = np.array([guitar['p'][a] for a in 'xyz'])
    gr = Rotation.from_quat([guitar['r'][a] for a in 'xyzw'])
    active, lower, upper = action_bounds(contract)
    ref = np.asarray(contract['target105'])
    rows = []
    pins = dict(contract['source_sha256'])
    pins.update(pad['contract']['source_sha256']); pins.update(surface['source_sha256'])
    pins.update({p['path']: p['sha256'] for p in task.provenance['provenance']})
    pins[str(Path(__file__).resolve())] = sha(__file__)
    write(out/'inputs_before.json', pins)
    for index, goal in enumerate(goals):
        finger = goal['finger']-1
        finger_name = ('index', 'middle', 'ring', 'pinky')[finger]
        local = pad['points_local'][finger].astype(float)
        normals = pad['normals_local'][finger].astype(float)
        # All arm12 channels plus the assigned finger4; other fingers stay at reference.
        channels = [i for i, name in enumerate(ACTIVE_NAMES)
                    if name.startswith('L_') or name.startswith('LH:'+finger_name)]
        native = active[channels]
        lo, hi = lower[channels], upper[channels]
        start, line = starts[goal['string']], ends[goal['string']]-starts[goal['string']]
        y = (low[index]+high[index])/2
        center = start+(y-start[1])/line[1]*line
        # A floating pad can satisfy the geometric band without acquiring load.
        # Request a small nominal inward overlap inside the existing[-1,3]mm
        # band; real contact/deflection remains entirely the physics engine's.
        desired_point = center-plane[:3]*.0005

        def evaluate(values):
            trial = ref.copy(); trial[native] = values
            p, r = fk(trial)['LH:'+finger_name+'3']
            points = gr.inv().apply(p+r.apply(local)-gp)
            facing = -gr.inv().apply(r.apply(normals))@plane[:3]
            closest = np.argmin(np.linalg.norm(points-desired_point, axis=-1))
            return trial, points, facing, closest

        def residual(values):
            _, points, facing, selected = evaluate(values)
            return np.r_[1000*(points[selected]-desired_point),
                         10*max(.3-facing[selected], 0), .03*(values-ref[native])]

        seed = np.clip(ref[native], lo+1e-9, hi-1e-9)
        guesses = [seed, .75*seed+.25*(lo+hi)/2]
        fits = [least_squares(residual, guess, bounds=(lo, hi), max_nfev=max_nfev,
                             ftol=1e-9, xtol=1e-9, gtol=1e-9) for guess in guesses]
        fit = min(fits, key=lambda result: np.linalg.norm(residual(result.x)))
        q, points, facing, selected = evaluate(fit.x)
        fraction = np.clip((points-start)@line/(line@line),
                          min((low[index]+.002-start[1])/line[1], (high[index]-.002-start[1])/line[1]),
                          max((low[index]+.002-start[1])/line[1], (high[index]-.002-start[1])/line[1]))
        closest = start+fraction[:, None]*line
        distance = np.linalg.norm(closest-points, axis=-1)
        height = points@plane[:3]+plane[3]
        projected = points-height[:, None]*plane[:3]
        infinite = start+((projected-start)@line/(line@line))[:, None]*line
        lateral = np.linalg.norm(projected-infinite, axis=-1)
        position = ((points[:, 1] >= low[index]+.002) & (points[:, 1] <= high[index]-.002) &
                    (lateral <= .003) & (height >= -.001) & (height <= .003))
        facing_ok = position & (facing >= .1)
        nearest = int(distance.argmin())
        rows.append(dict(**goal, q_target105=q.tolist(),
            geometry_candidate=bool(facing_ok.any()), minimum_distance_m=float(distance[nearest]),
            nearest_normal_cos=float(facing[nearest]), nearest_signed_height_m=float(height[nearest]),
            nearest_lateral_m=float(lateral[nearest]), position_geometry=bool(position.any()),
            facing_geometry=bool(facing_ok.any()), nearest_sample=nearest,
            optimizer_converged=bool(fit.success), optimizer_nfev=int(fit.nfev),
            limitation='Source FK candidate only; no physical collision/load/wrong certification; search failure is not impossibility'))
        print('geometry', index, finger_name, goal['physical_string'], goal['fret'],
              rows[-1]['minimum_distance_m'], rows[-1]['geometry_candidate'], flush=True)
    write(out/'candidates.json', dict(schema=SCHEMA, bundle=str(bundle.resolve()),
        goals=rows, reference105=ref.tolist(), action_indices=active.tolist(),
        action_lower=lower.tolist(), action_upper=upper.tolist(),
        source_geometry=surface, pad_contract=pad['contract'],
        fk='current source exponential joints calibrated to prepared actual poses/q; no simulator',
        search=dict(max_nfev=max_nfev, seeds=2, objective='nearest actual distal patch to cell midpoint plus weak near-facing/pose prior',
                    requested_signed_pad_height_m=-.0005,
                    contact_request='0.5mm nominal inward source-plane overlap; no state/collision/PD override and no pressure guarantee',
                    limitation='Finite local optimization does not prove reachability or infeasibility')))
    changed = [p for p, expected in pins.items() if sha(p) != expected]
    if changed:
        raise RuntimeError('Geometry input changed: '+str(changed))


def replay_geometry(geometry, mode, out, device='cuda:0', ramp_s=6., hold_s=2., feedback='none'):
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.environment import TensorSongEnvironment, FAILURE_REASONS
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from scipy.spatial.transform import Rotation
    from types import SimpleNamespace
    candidates_path = geometry/'candidates.json'
    candidates = json.loads(candidates_path.read_text())
    selected = json.loads((geometry/'targets.json').read_text())
    goals = candidates['goals']
    if (candidates['schema'] != SCHEMA or len(goals) != 16 or
            selected['representative_rows'] != list(REPRESENTATIVE_ROWS) or
            any({k: row[k] for k in original} != original for row, original in zip(goals, selected['goals']))):
        raise ValueError('Original deterministic16-goal selection/capture rows required')
    pins = json.loads((geometry/'inputs_before.json').read_text())
    if any(sha(p) != expected for p, expected in pins.items()):
        raise ValueError('Pinned geometry source changed; rebuild geometry before replay')
    pins.update({str(p.resolve()): sha(p) for p in (candidates_path, geometry/'targets.json')})
    out.mkdir(parents=True, exist_ok=False)
    scene = None
    fast, slow, fk_checks = [], [], []
    report = None
    if feedback not in ('none', 'joint_error_integral'):
        raise ValueError('Explicit none/joint_error_integral diagnostic feedback required')
    settings = dict(schema=SCHEMA, diagnostic_only=True, training_contract=False,
        guitar_mode=mode, ramp_s=ramp_s, hold_s=hold_s, initial_hold_s=.5,
        representative_rows=list(REPRESENTATIVE_ROWS), max_finger_command_speed_rad_s=1.,
        open_loop=feedback == 'none', feedback=dict(mode=feedback,
            gain_per_s=1.5, offset_limit_rad=.1, integration_hz=60,
            onset='only after nominal ramp completes; no feedback during initial hold/ramp',
            channels='left arm12 plus assigned finger4 only; other fingers and partner unchanged',
            antiwindup='store only offset surviving both0.1rad cap and existing action target bounds',
            application='bounded39 action inverse only; no controller target/DOF overwrite; native control/PD unchanged'),
        interpretation=('Same finite prepared-frame q trajectory; free failure alone does not prove a policy/controller defect'
            if feedback == 'none' else 'Diagnostic closed-loop joint-error correction; fixed/free actual trajectories differ with their measured errors; not an identical-trajectory comparison'),
        after_failure='Row outcomes/captures censored at first safety failure; no reset or state injection; bounded hold while other isolated rows finish',
        contact_scope='Current assigned distal pad geometry + net distal body load + original wrong veto; no contact pair/pressure/acoustic success')
    write(out/'settings.json', settings)
    try:
        scene = GpuScene(16, 'left', device=device, out=out, diagnostic_guitar_mode=mode)
        control = BatchedController(scene, finger_action_mode='incremental')
        metadata = copy.deepcopy(scene.metadata)
        metadata['action_contract'] = copy.deepcopy(control.contract)
        env = TensorSongEnvironment(metadata, bundle=candidates['bundle'],
            song=dict(pre_roll_s=3., tail_s=.5, left_fraction=.4, window_s=.1), hand='left', device=device)
        sample = scene.snapshot()
        ids = torch.arange(16, device=device)
        control.reset(ids, sample); env.reset(ids, sample)
        pins.update({p: sha(p) for p in project_source_paths(sys.modules.items())})
        write(out/'inputs_before.json', pins)
        write(out/'metadata.json', metadata)
        indices = torch.tensor([r['source_note_index'] for r in goals], device=device)
        trace_ids = torch.tensor(REPRESENTATIVE_ROWS, device=device)
        reference = control.reference[control.active]
        requested = torch.tensor([r['q_target105'] for r in goals], device=device)[:, control.active]
        if (not torch.allclose(control.action_low.cpu(), torch.tensor(candidates['action_lower']), atol=1e-6, rtol=0) or
                not torch.allclose(control.action_high.cpu(), torch.tensor(candidates['action_upper']), atol=1e-6, rtol=0)):
            raise ValueError('CPU/GPU action bounds differ')
        incremental = torch.tensor([n.startswith('LH:') for n in ACTIVE_NAMES], device=device)
        alive = np.ones(16, dtype=bool)
        previous = env.candidate[ids, indices].cpu().numpy()
        streak = np.zeros(16); best = np.zeros(16); samples = np.zeros(16, dtype=int)
        counts = {key: np.zeros(16, dtype=int) for key in ('position', 'facing', 'loaded', 'wrong', 'candidate', 'cell', 'lateral', 'height')}
        distance = np.full(16, np.inf)
        max_error = np.zeros(16); limits = np.zeros(16, dtype=int)
        max_guitar_distance = np.zeros(16); max_guitar_rotation = np.zeros(16)
        failures = [None]*16
        env.tick_failure = torch.zeros(16, len(FAILURE_REASONS), dtype=torch.bool, device=device)
        env.tick_cost = torch.zeros(16, device=device)
        last_valid = scene.efforts.clone()
        initial_target = control.target[:, control.active].clone()
        nominal = initial_target.clone()
        offset = torch.zeros_like(nominal)
        max_offset = torch.zeros(16, device=device)
        feedback_mask = torch.tensor([[name.startswith('L_') or
            name.startswith('LH:'+('index', 'middle', 'ring', 'pinky')[goal['finger']-1])
            for name in ACTIVE_NAMES] for goal in goals], device=device)
        initial_q = scene.q[0].cpu().numpy().copy()
        fk = full_fk(SimpleNamespace(names=scene.names, human_bodies=scene.human_bodies,
                                    q_ref=initial_q), scene.contract['state'])
        from guitar_learning.gpu.geometry import apply, conjugate

        def pose_frame(tick, action):
            slow.append(dict(tick=tick, body_state=scene.body_state[trace_ids].cpu().numpy().copy(),
                q=scene.q[trace_ids].cpu().numpy().copy(), qd=scene.qd[trace_ids].cpu().numpy().copy(),
                target=scene.target[trace_ids].cpu().numpy().copy(), action=action[trace_ids].cpu().numpy().copy(),
                nominal_target39=nominal[trace_ids].cpu().numpy().copy(),
                outer_feedback_offset39=offset[trace_ids].cpu().numpy().copy(),
                valid=alive[list(REPRESENTATIVE_ROWS)].copy()))
            if tick <= 2 or tick % 30 == 0:
                for slot, row in enumerate(REPRESENTATIVE_ROWS):
                    if not alive[row]:
                        continue
                    q = slow[-1]['q'][slot].astype(float)
                    predicted = fk(q)
                    for body_name in ('L_Wrist', 'LH:'+('index', 'middle', 'ring', 'pinky')[goals[row]['finger']-1]+'3'):
                        actual = slow[-1]['body_state'][slot, metadata['body_names'].index('human/'+body_name)]
                        p, r = predicted[body_name]
                        angle = (r.inv()*Rotation.from_quat(actual[3:7])).magnitude()
                        fk_checks.append(dict(tick=tick, row=row, body=body_name,
                            q_change_from_prepared_rad=float(np.linalg.norm(q-initial_q)),
                            position_error_m=float(np.linalg.norm(p-actual[:3])),
                            rotation_error_rad=float(angle),
                            scope='Actual physically evolved q/body readback versus prepared-calibrated source FK; no q injection'))

        pose_frame(0, torch.zeros(16, 39, device=device))
        ticks = round((.5+ramp_s+hold_s)*60)
        for tick in range(ticks):
            fraction = min(max(((tick+1)/60.-.5)/ramp_s, 0.), 1.)
            nominal = initial_target+(requested-initial_target)*fraction
            # Failed rows retain bounded LH targets, with no physical-state writes.
            live = torch.tensor(alive, device=device)
            if feedback == 'joint_error_integral' and (tick+1)/60. > .5+ramp_s:
                offset = integral_tracking_offset(offset, nominal, scene.q[:, control.active],
                    control.action_low, control.action_high, feedback_mask & live[:, None])
                max_offset = torch.maximum(max_offset, offset.abs().amax(-1))
            desired = nominal+offset
            desired = torch.where(live[:, None], desired, control.target[:, control.active])
            actions = trajectory_actions(desired, control.target[:, control.active], reference,
                control.action_low, control.action_high, incremental)
            actions[:, 33:] = 0  # frozen partner retains its original residual reference.
            target = control.targets(actions, sample)
            for _ in range(4):
                efforts = control.efforts(sample)
                checks = control.diagnostics
                certified = checks['finite'] & checks['chest_witness_certified']
                if not bool(certified.all()):
                    raise RuntimeError('Nonfinite or uncertified native support controller; remaining rows censored')
                undefined = ~checks['chest_normal_defined']
                efforts = torch.where(undefined[:, None], last_valid, efforts)
                last_valid.copy_(efforts)
                sample = scene.step(target, efforts)
                # Reuse measurement and safety predicates, without reward/score clocks.
                env._snapshot(sample)
                env._safety()
                env.tick_failure[:, -1] |= undefined
                current = env.candidate[ids, indices].cpu().numpy()
                flags = dict(position=env.contact_geometry[ids, indices], facing=env.contact_facing[ids, indices],
                    loaded=env.surface_body_loaded[ids, indices], wrong=env.wrong[ids, indices],
                    candidate=env.candidate[ids, indices])
                # Separate any-sample cell/lateral/height diagnostics from combined geometry.
                distal = env.body[ids, env.pad_indices[env.finger[indices]-1]]
                local = env.pad_local[env.finger[indices]-1]
                points = apply(conjugate(env.guitar_q[:, None]),
                    distal[:, None, :3]+apply(distal[:, None, 3:7], local)-env.guitar_body[:, None, :3])
                low = torch.minimum(env.frets[ids, env.fret[indices]-1, 1], env.frets[ids, env.fret[indices], 1])+.002
                high = torch.maximum(env.frets[ids, env.fret[indices]-1, 1], env.frets[ids, env.fret[indices], 1])-.002
                flags.update(pad_axis_flags(points, env.starts, env.ends, env.string[indices], low, high, env.press_plane))
                flag_values = {key: value.cpu().numpy() for key, value in flags.items()}
                failure = env.tick_failure.cpu().numpy()
                just_failed = alive & failure.any(-1)
                accepted = alive & ~just_failed
                current &= accepted
                streak, best = diagnostic_streak(previous, current, streak, best)
                previous = current.copy()
                d = env.surface_distance[ids, indices].cpu().numpy()
                distance = np.where(accepted, np.minimum(distance, d), distance)
                q_error = (scene.q[:, control.active]-target[:, control.active]).abs().amax(-1).cpu().numpy()
                limit_mask = ((scene.q[:, control.active] <= scene.lower[control.active]+1e-3) |
                              (scene.q[:, control.active] >= scene.upper[control.active]-1e-3))
                at_limit = limit_mask.any(-1).cpu().numpy()
                gd = torch.linalg.vector_norm(env.guitar_delta, dim=-1).cpu().numpy()
                ga = torch.linalg.vector_norm(env.guitar_rotation, dim=-1).cpu().numpy()
                max_error = np.where(accepted, np.maximum(max_error, q_error), max_error)
                limits += accepted & at_limit
                max_guitar_distance = np.where(alive, np.maximum(max_guitar_distance, gd), max_guitar_distance)
                max_guitar_rotation = np.where(alive, np.maximum(max_guitar_rotation, ga), max_guitar_rotation)
                for key in counts:
                    counts[key] += accepted & flag_values[key]
                samples += accepted
                for row in np.flatnonzero(just_failed):
                    failures[row] = dict(physics_step=scene.physics_steps,
                        reasons=[name for i, name in enumerate(FAILURE_REASONS) if failure[row, i]])
                alive &= ~just_failed
                selected_rows = list(REPRESENTATIVE_ROWS)
                fast.append(dict(physics_step=scene.physics_steps, valid=accepted[selected_rows],
                    q=scene.q[trace_ids].cpu().numpy().copy(), qd=scene.qd[trace_ids].cpu().numpy().copy(),
                    target=target[trace_ids].cpu().numpy().copy(),
                    active_native_limit_mask=limit_mask[trace_ids].cpu().numpy(),
                    distance=d[selected_rows], delta=env.surface_delta[ids, indices][trace_ids].cpu().numpy(),
                    nearest_normal_cos=env.surface_alignment[ids, indices][trace_ids].cpu().numpy(),
                    nearest_signed_height=env.surface_height[ids, indices][trace_ids].cpu().numpy(),
                    body_load_n=torch.linalg.vector_norm(sample['contact_force'][ids, env.pad_indices[env.finger[indices]-1]], dim=-1)[trace_ids].cpu().numpy(),
                    streak=streak[selected_rows].copy(),
                    **{key: value[selected_rows] for key, value in flag_values.items()}))
            pose_frame(tick+1, actions)
            if tick % 60 == 0:
                print(mode, 'tick', tick+1, 'active', int(alive.sum()), 'best_contact_s', best.tolist(), flush=True)
            if not alive.any():
                break
        report = dict(schema=SCHEMA, settings=settings, scene=scene.diagnostics,
            completed_control_ticks=tick+1, actual_physics_steps=scene.physics_steps,
            initial_reset_calls=scene.reset_calls, source_unchanged=all(sha(p) == expected for p, expected in pins.items()),
            source_fk_readback=dict(samples=len(fk_checks),
                maximum_position_error_m=max(r['position_error_m'] for r in fk_checks),
                maximum_rotation_error_rad=max(r['rotation_error_rad'] for r in fk_checks),
                limitation='Source candidate interpretation must account for actual native/source FK discrepancies; calibration alone is not a perturbation proof'),
            interpretation='Static diagnostics outside song windows; overlapping causes are not additive;100ms hold is not song achievement',
            goals=[goal_measurement(goal, accepted_physics_samples=int(samples[i]), observed_s=float(samples[i]/240.),
                minimum_distance_m=float(distance[i]) if np.isfinite(distance[i]) else None,
                seconds={key: float(counts[key][i]/240.) for key in counts}, best_contact_streak_s=float(best[i]),
                first_contact_50ms=bool(best[i]+1e-12 >= .05), diagnostic_hold_100ms=bool(best[i]+1e-12 >= .1),
                maximum_target_error_rad=float(max_error[i]), any_active_joint_limit_s=float(limits[i]/240.),
                maximum_outer_feedback_offset_rad=float(max_offset[i].cpu()),
                maximum_guitar_displacement_m=float(max_guitar_distance[i]), maximum_guitar_rotation_rad=float(max_guitar_rotation[i]),
                failure=failures[i]) for i, goal in enumerate(goals)])
    except BaseException as error:
        write(out/'failure.json', dict(error=repr(error), samples240=len(fast), frames60=len(slow)))
        raise
    finally:
        for filename, rows in (('trace240.npz', fast), ('poses60.npz', slow)):
            if rows:
                np.savez_compressed(out/filename, **{key: np.stack([r[key] for r in rows]) for key in rows[0]})
        if scene is not None:
            scene.close()
            if report is not None:
                report['scene'] = scene.diagnostics
        if fk_checks:
            write(out/'source_fk_readback.json', fk_checks)
    write(out/'report.json', report)


def render_replay(source, out, row=0):
    """Render exact saved poses using the existing source renderer; no physics."""
    import numpy as np
    import mujoco
    from PIL import Image, ImageDraw
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses, add_strings
    from guitar_learning.tool._rendering import encoder, probe
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    if row not in REPRESENTATIVE_ROWS:
        raise ValueError('Only predeclared representative row poses are recorded')
    trace = np.load(source/'poses60.npz', allow_pickle=False)
    slot = REPRESENTATIVE_ROWS.index(row)
    valid = trace['valid'][:, slot]
    frame_count = int(valid.sum())
    if frame_count < 1 or valid[:frame_count].sum() != frame_count:
        raise ValueError('Contiguous valid pose frames required')
    metadata = json.loads((source/'metadata.json').read_text())
    out.mkdir(parents=True, exist_ok=False)
    contract = load_prepared_reset_contract()
    model, data, mapping, _ = build_model(contract['initial'])
    renderer = mujoco.Renderer(model, height=720, width=1280)
    hand_camera = dict(distance_m=.5, azimuth_deg=270., elevation_deg=-10.,
                       lookat='current recorded human/L_Wrist world origin',
                       side='front/string side of guitar neck')
    media = []
    try:
        for view in ('full', 'hand'):
            stream = encoder(out/(view+'.mp4'))
            try:
                for frame in range(frame_count):
                    bodies = trace['body_state'][frame, slot]
                    state = {kind+'_body_states': [] for kind in ('human', 'guitar', 'chair')}
                    for name, body in zip(metadata['body_names'], bodies):
                        kind = name.split('/')[0]
                        state[kind+'_body_states'].append(dict(pose=dict(
                            p=dict(zip('xyz', body[:3].tolist())), r=dict(zip('xyzw', body[3:7].tolist())))))
                    set_body_poses(model, data, mapping, state)
                    if view == 'hand':
                        camera = mujoco.MjvCamera()
                        mujoco.mjv_defaultCamera(camera)
                        wrist = metadata['body_names'].index('human/L_Wrist')
                        camera.lookat[:] = bodies[wrist, :3]
                        camera.distance = hand_camera['distance_m']
                        camera.azimuth = hand_camera['azimuth_deg']
                        camera.elevation = hand_camera['elevation_deg']
                    else:
                        camera = 'front'
                    renderer.update_scene(data, camera=camera)
                    endpoints = np.array([[bodies[metadata['body_names'].index('guitar/'+name), :3]
                        for name in ('G:string%d'%s, 'G:string%d_end'%s)] for s in range(1, 7)])
                    add_strings(renderer.scene, endpoints)
                    image = Image.fromarray(renderer.render())
                    ImageDraw.Draw(image).text((15, 15), 'Diagnostic row %d | %s | %.3fs'%(row, view, frame/60), fill='white')
                    if frame in (0, frame_count-1):
                        image.save(out/('%s_%04d.png'%(view, frame)))
                    stream.stdin.write(image.tobytes())
            finally:
                stream.stdin.close()
                if stream.wait() != 0:
                    raise RuntimeError('Diagnostic video encoding failed')
            media.append(probe(out/(view+'.mp4'), frame_count))
    finally:
        renderer.close()
    write(out/'render.json', dict(schema=SCHEMA, source=str(source.resolve()), row=row,
        source_sha256={str((source/name).resolve()): sha(source/name) for name in ('poses60.npz', 'metadata.json')},
        frames=frame_count, videos=media, new_physics_steps=0,
        cameras=dict(full=dict(name='front', source='existing source-visual renderer camera'),
                     hand=hand_camera),
        scope='exact recorded body poses, valid prefix through the last safe60Hz endpoint'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    geometry = commands.add_parser('geometry')
    geometry.add_argument('--bundle', type=Path, default=DEFAULT_BUNDLE)
    geometry.add_argument('--out', type=Path, required=True)
    geometry.add_argument('--max-nfev', type=int, default=160)
    replay = commands.add_parser('replay')
    replay.add_argument('--geometry', type=Path, required=True)
    replay.add_argument('--mode', choices=('fixed', 'free'), required=True)
    replay.add_argument('--out', type=Path, required=True)
    replay.add_argument('--device', default='cuda:0')
    replay.add_argument('--ramp-s', type=float, default=6.)
    replay.add_argument('--hold-s', type=float, default=2.)
    replay.add_argument('--feedback', choices=('none', 'joint_error_integral'), default='none')
    render = commands.add_parser('render')
    render.add_argument('--source', type=Path, required=True)
    render.add_argument('--out', type=Path, required=True)
    render.add_argument('--row', type=int, default=0)
    args = parser.parse_args()
    if args.command == 'replay':
        if args.ramp_s <= 0 or args.hold_s <= 0:
            parser.error('Positive ramp/hold durations required')
        # Isaac Gym must initialize before any module imports Torch.
        import isaacgym
        replay_geometry(args.geometry.resolve(), args.mode, args.out.resolve(), args.device,
                        args.ramp_s, args.hold_s, args.feedback)
    elif args.command == 'geometry':
        if args.max_nfev < 1:
            parser.error('Positive search budget required')
        search_geometry(args.bundle.resolve(), args.out.resolve(), args.max_nfev)
    else:
        render_replay(args.source.resolve(), args.out.resolve(), args.row)


if __name__ == '__main__':
    main()
