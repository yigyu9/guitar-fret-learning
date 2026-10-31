"""Pure geometry for the live diagnostic; no simulator or controller imports."""
import itertools
import numpy as np
from scipy.spatial.transform import Rotation
from .body_center_coordinates import body_center_world, pelvis_rfu

BITS = np.array(list(itertools.product((0, 1), repeat=3)))
EDGES = [(i, j) for i in range(8) for j in range(i+1, 8) if np.sum(BITS[i] != BITS[j]) == 1]
FINGERS = ('index', 'middle', 'ring', 'pinky')


def pose(row):
    p = row['pose']
    return np.array([p['p'][k] for k in 'xyz']), Rotation.from_quat([p['r'][k] for k in 'xyzw'])


def position_geometry(guitar_row, pelvis_row, initial_rotation, initial_chest_z):
    gp, gr = pose(guitar_row); pp, pr = pose(pelvis_row)
    low, high = np.array([-.50, -.15, .65]), np.array([-.15, .15, initial_chest_z])
    offset = gr.apply([0., -.4, -.0217])
    center = body_center_world(gp, gr.as_quat())
    excess = np.maximum(np.maximum(low-gp, gp-high), 0.)
    neck, front = gr.apply([[0, 1, 0], [0, 0, 1]])
    forward = pr.apply([0, -1, 0])
    return dict(body_center_W_m=center.tolist(), body_center_pelvis_RFU_m=pelvis_rfu(center, pp, pr.as_quat()).tolist(),
        user_body_center_box_W_m=(low+BITS*(high-low)+offset).tolist(),
        user_position_excess_world_axes_m=excess.tolist(), user_position_box_distance_m=float(np.linalg.norm(excess)),
        user_position_inside=bool(np.all(excess == 0)), rotation_set_evaluated=False,
        rotation_change_deg=float(np.degrees((gr*initial_rotation.inv()).magnitude())),
        neck_elevation_deg=float(np.degrees(np.arcsin(np.clip(neck[2], -1, 1)))),
        front_to_pelvis_forward_deg=float(np.degrees(np.arccos(np.clip(front@forward, -1, 1)))))


def assigned_targets(goal, measurement, tip_positions):
    """Each active string retains its assigned finger; top-body origins are markers."""
    rows = []
    for string, active in enumerate(measurement['active'][0]):
        if not active: continue
        finger = int(goal['finger'][0][string])
        if finger not in (1, 2, 3, 4): raise ValueError('active string has invalid assigned finger')
        tip = np.asarray(tip_positions[finger-1]); target = np.asarray(measurement['target_world'][0][string])
        rows.append(dict(string_index_zero_based=string, fret=int(goal['fret'][0][string]), finger=FINGERS[finger-1],
            barre=bool(goal['barre'][0][string]), tip_marker_W_m=tip.tolist(), target_W_m=target.tolist(),
            tip_marker_distance_m=float(np.linalg.norm(target-tip)),
            one_sided_pad_approach_distance_m=float(measurement['approach_distance'][0][string]),
            source_ready_from_prior_tracker=bool(measurement['ready'][0][string])))
    return rows


def actual_guitar_contacts(contacts):
    """Exclude the pluck proxy; retain raw lambda and all actual counterpart bodies."""
    rows = []
    for contact in contacts:
        names = [contact['body0_name'], contact['body1_name']]
        if not any(n.startswith('guitar/') and 'pluck_range' not in n for n in names): continue
        if any('pluck_range' in n for n in names): continue
        rows.append(contact)
    return rows
