"""Finite world poses and incremental rotation about the guitar actor origin."""
import numpy as np
from scipy.spatial.transform import Rotation


def checked_pose(position, quaternion):
    p, q = np.asarray(position, dtype=float), np.asarray(quaternion, dtype=float)
    if p.shape != (3,) or q.shape != (4,) or not np.isfinite(p).all() or not np.isfinite(q).all():
        raise ValueError('finite position xyz and quaternion xyzw required')
    if np.linalg.norm(q) < 1e-12:
        raise ValueError('zero quaternion')
    return p.copy(), q / np.linalg.norm(q)


def nudge(position, quaternion, axis, amount, rotation=False, local=False):
    p, q = checked_pose(position, quaternion)
    if axis not in (0, 1, 2) or not np.isfinite(amount):
        raise ValueError('axis 0/1/2 and finite increment required')
    direction = np.eye(3)[axis] * amount
    current = Rotation.from_quat(q)
    if rotation:
        delta = Rotation.from_rotvec(direction)
        q = (current * delta if local else delta * current).as_quat()
    else:
        p += current.apply(direction) if local else direction
    return p, q


def pose_delta(position, quaternion, reference):
    p, q = checked_pose(position, quaternion)
    rp, rq = checked_pose(*reference)
    delta = Rotation.from_quat(q) * Rotation.from_quat(rq).inv()
    return {'translation_W_m': (p-rp).tolist(),
            'rotation_vector_W_deg': np.degrees(delta.as_rotvec()).tolist(),
            'rotation_angle_deg': float(np.degrees(delta.magnitude()))}
