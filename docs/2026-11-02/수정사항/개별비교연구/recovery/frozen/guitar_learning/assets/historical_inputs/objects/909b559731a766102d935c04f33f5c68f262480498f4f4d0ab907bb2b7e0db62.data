"""Display reference point, not mass CoM; quaternions are world xyzw."""
import numpy as np
from scipy.spatial.transform import Rotation
from .validate_team_pose_envelope import BODY_CENTER_G


def body_center_world(root_position, quaternion):
    """Convert one root or root-box corners with a single fixed rotation."""
    return np.asarray(root_position) + Rotation.from_quat(quaternion).apply(BODY_CENTER_G)


def actor_root_world(center_position, quaternion):
    """Convert a desired display center to the actor-root position at this q."""
    return np.asarray(center_position) - Rotation.from_quat(quaternion).apply(BODY_CENTER_G)


def pelvis_rfu(world_points, pelvis_position, pelvis_quaternion):
    """Pelvis right/forward/up meters: local -X/-Y/+Z, respectively."""
    basis = Rotation.from_quat(pelvis_quaternion).apply([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    return (np.asarray(world_points) - np.asarray(pelvis_position)) @ basis.T
