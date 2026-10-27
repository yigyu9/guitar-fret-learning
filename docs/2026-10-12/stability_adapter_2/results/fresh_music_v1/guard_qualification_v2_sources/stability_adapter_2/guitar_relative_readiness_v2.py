"""Current-guitar preparation predicate; raw contacts are evidence, not forces in N."""
import numpy as np
from scipy.spatial.transform import Rotation


def body_pose(row):
    return (np.array([row['pose']['p'][k] for k in 'xyz']),
            Rotation.from_quat([row['pose']['r'][k] for k in 'xyzw']))


def world_target(position, quaternion, ready_g):
    p, q, target = np.asarray(position), np.asarray(quaternion), np.asarray(ready_g)
    if p.shape != (3,) or q.shape != (4,) or target.shape != (3,) or not np.isfinite(np.r_[p,q,target]).all() or np.linalg.norm(q)<1e-12:
        raise ValueError('finite guitar pose and ready point required')
    return p + Rotation.from_quat(q).apply(target + [0., 0., .03])


def evaluate_readiness(state, human_names, guitar_names, contacts, ready_g, center_g, palm_normal_local, grip_success):
    gp, gr = body_pose(state['guitar_body_states'][0])
    human = dict(zip(human_names, state['human_body_states']))
    guitar = dict(zip(guitar_names, state['guitar_body_states']))
    pick_w, _ = body_pose(human['RH:pick'])
    pick_g = gr.inv().apply(pick_w-gp)
    _, palm_r = body_pose(human['LH:palm'])
    palm_up = float(palm_r.apply(palm_normal_local)[2])
    evidence, palm_rows, finger_rows, right_rows = [], [], [], []
    for contact in contacts:
        a, b = contact['body0_name'], contact['body1_name']
        if a.startswith('guitar/') and b.startswith('human/'):
            gn, hn, local = a[7:], b[6:], contact['localPos0']
        elif b.startswith('guitar/') and a.startswith('human/'):
            gn, hn, local = b[7:], a[6:], contact['localPos1']
        else:
            continue
        if hn.startswith('RH:') or hn == 'R_Wrist':
            right_rows.append(contact)
        if not np.isfinite(contact['lambda']) or contact['lambda']<=0:
            continue
        if not hn.startswith('LH:') or gn not in guitar:
            continue
        p, r = body_pose(guitar[gn])
        point = gr.inv().apply(p+r.apply([local[k] for k in 'xyz'])-gp)
        width = .027908-.01631590413943356*(point[1]+.241803)
        neck = (gn=='guitar' or gn=='G:nut' or gn.startswith('G:fret')) and \
            -.241803-.003 <= point[1] <= .219455+.003 and \
            abs(point[0]) <= width+.003 and -.011 <= point[2] <= .0143
        underside = bool(neck and abs(point[0]-width)<=.003)
        row = {'hand_body':hn, 'guitar_body':gn, 'point_G_m':point.tolist(),
               'neck_region':bool(neck), 'under_neck_face':underside, 'positive_raw_lambda':float(contact['lambda'])}
        evidence.append(row)
        if hn=='LH:palm' and underside:
            palm_rows.append(row)
        elif hn.startswith(('LH:thumb','LH:index','LH:middle','LH:ring','LH:pinky')) and neck:
            finger_rows.append(row)
    distance = float(np.linalg.norm(pick_g-ready_g))
    front = float(pick_g[2]-center_g[2])
    finite = bool(np.isfinite(np.r_[pick_g,ready_g,center_g,palm_up]).all())
    conditions = {'finite':finite, 'left_palm_under_neck_contact':bool(palm_rows),
        'left_finger_neck_contact':bool(finger_rows), 'left_palm_up':bool(palm_up>=0),
        'right_near_strike':bool(distance<=.05), 'right_front_side':bool(front>=.003),
        'right_grip':bool(grip_success), 'right_noncontact':not right_rows}
    return {'ready_now':all(conditions.values()), 'conditions':conditions,
        'pick_G_m':pick_g.tolist(), 'ready_G_m':np.asarray(ready_g).tolist(),
        'ready_W_m':(gp+gr.apply(ready_g)).tolist(), 'prep_target_W_m':world_target(gp,gr.as_quat(),ready_g).tolist(),
        'pick_to_ready_m':distance, 'pick_front_clearance_m':front, 'palm_up_dot':palm_up,
        'left_contact_evidence':evidence, 'right_contact_rows':len(right_rows)}


class PreparationGate:
    def __init__(self):
        self.streak = 0

    def update(self, readiness):
        self.streak = self.streak+1 if readiness['ready_now'] else 0
        return self.streak>=6


def pick_behind_body(state, guitar_names, pick_g, body_half_thickness):
    """Current physical body rear plane, separate from preparation's front stand-off."""
    gp, gr = body_pose(state['guitar_body_states'][0])
    bp, br = body_pose(state['guitar_body_states'][guitar_names.index('G:body')])
    rear_world = bp + br.apply([0.,0.,-body_half_thickness])
    rear_z_g = float(gr.inv().apply(rear_world-gp)[2])
    return bool(pick_g[2] < rear_z_g-.003), rear_z_g
