"""Measured geometry in the live guitar-root frame; no simulator writes.

Physical string numbers are 1=high E through 6=low E. Musical fret 0
means an open string here, not the legacy Fret task's DONT_CARE sentinel.
"""
import numpy as np
from scipy.spatial.transform import Rotation


def frame(body_state):
    pose = body_state['pose']
    p = np.array([pose['p'][axis] for axis in 'xyz'], dtype=float)
    q = np.array([pose['r'][axis] for axis in 'xyzw'], dtype=float)
    if not np.isfinite(np.r_[p, q]).all() or np.linalg.norm(q) == 0:
        raise ValueError('finite pose and nonzero quaternion required')
    return p, Rotation.from_quat(q)


def world_to_guitar(points_W, guitar_state):
    p, rotation = frame(guitar_state)
    return rotation.inv().apply(np.asarray(points_W, dtype=float) - p)


def guitar_to_world(points_G, guitar_state):
    p, rotation = frame(guitar_state)
    return p + rotation.apply(np.asarray(points_G, dtype=float))


def body_point_motion(body_state, local_point, com_local):
    """Body-origin pose, native COM linear velocity, world angular velocity."""
    p, rotation = frame(body_state)
    point = np.asarray(local_point, dtype=float)
    com = np.asarray(com_local, dtype=float)
    if point.shape != (3,) or com.shape != (3,) or not np.isfinite(np.r_[point, com]).all():
        raise ValueError('finite body-local point and COM vectors required')
    linear = np.array([body_state['vel']['linear'][a] for a in 'xyz'])
    angular = np.array([body_state['vel']['angular'][a] for a in 'xyz'])
    return p + rotation.apply(point), linear + np.cross(angular, rotation.apply(point - com))


def relative_point_motion(point_W, velocity_W, guitar_state, guitar_com_local):
    """Differentiate R_GW (point_W - origin_W), including guitar rotation."""
    origin, origin_velocity = body_point_motion(guitar_state, np.zeros(3), guitar_com_local)
    _, rotation = frame(guitar_state)
    omega = np.array([guitar_state['vel']['angular'][a] for a in 'xyz'])
    point = np.asarray(point_W, dtype=float)
    return (rotation.inv().apply(point - origin),
            rotation.inv().apply(np.asarray(velocity_W) - origin_velocity - np.cross(omega, point - origin)))


def geometry_snapshot(state, human_names, guitar_names):
    """Read marker origins from this physics sample, never reset-time targets.

    Distal finger body origins are identified as proxies, not calibrated pads.
    This function does not decide native contact, pressure, or musical success.
    """
    if len(set(human_names)) != len(human_names) or len(set(guitar_names)) != len(guitar_names):
        raise ValueError('unique body names required')
    if len(human_names) != len(state['human_body_states']) or len(guitar_names) != len(state['guitar_body_states']):
        raise ValueError('body names and states must align')
    humans = dict(zip(human_names, state['human_body_states']))
    guitars = dict(zip(guitar_names, state['guitar_body_states']))
    guitar = guitars['guitar']
    local = {name: world_to_guitar(frame(body)[0], guitar) for name, body in guitars.items()}
    tips = {finger: world_to_guitar(frame(humans['LH:' + finger + '3'])[0], guitar)
            for finger in ('thumb', 'index', 'middle', 'ring', 'pinky')}
    pick = world_to_guitar(frame(humans['RH:pick'])[0], guitar)
    return dict(schema='free_guitar_geometry_v1', physics_step=int(state['physics_step']),
                frame='current guitar root body origin; +x string6 to string1, +y bridge to nut',
                string_numbers=list(range(1, 7)),
                starts_G_m=np.array([local['G:string%d' % n] for n in range(1, 7)]),
                ends_G_m=np.array([local['G:string%d_end' % n] for n in range(1, 7)]),
                fret_markers_G_m=np.array([local['G:nut']] + [local['G:fret%d' % n] for n in range(1, 23)]),
                pick_G_m=pick, finger_distal_origins_G_m=tips,
                measurement_scope='saved/live body origins; distal proxies, no pad or pressure measurement')


def fret_target(snapshot, string_number, musical_fret):
    """Interval midpoint on the measured string; open string has no press goal."""
    if type(string_number) is not int or not 1 <= string_number <= 6:
        raise ValueError('physical string number must be 1..6')
    if type(musical_fret) is not int or not 0 <= musical_fret <= 22:
        raise ValueError('musical fret must be 0..22; legacy sentinels need an adapter')
    if musical_fret == 0:
        return None
    markers = snapshot['fret_markers_G_m']
    y = (markers[musical_fret - 1, 1] + markers[musical_fret, 1]) / 2
    start, end = snapshot['starts_G_m'][string_number - 1], snapshot['ends_G_m'][string_number - 1]
    if abs(end[1] - start[1]) < 1e-12:
        raise ValueError('string must span the measured fret direction')
    fraction = (y - start[1]) / (end[1] - start[1])
    if not 0 <= fraction <= 1:
        raise ValueError('fret interval outside measured finite string')
    return start + fraction * (end - start)


def relative_sweep_inputs(previous, current, physics_hz=240.):
    """Inputs for the legacy local swept detector, using each sample's frame.

    The endpoint-linear relative sweep is an approximation over one physics
    interval. A six-string rigid guitar must retain its local endpoints.
    """
    elapsed = current['physics_step'] - previous['physics_step']
    if elapsed != 1 or not np.isfinite(physics_hz) or physics_hz <= 0:
        raise ValueError('consecutive physics samples and positive frequency required')
    for key in ('starts_G_m', 'ends_G_m'):
        if not np.allclose(previous[key], current[key], atol=1e-5, rtol=0):
            raise ValueError('local string geometry changed; rigid-guitar sweep is invalid')
    return dict(previous_tip_g=previous['pick_G_m'].copy(), current_tip_g=current['pick_G_m'].copy(),
                string_start_g=current['starts_G_m'].copy(), string_end_g=current['ends_G_m'].copy(),
                dt=1. / physics_hz)
