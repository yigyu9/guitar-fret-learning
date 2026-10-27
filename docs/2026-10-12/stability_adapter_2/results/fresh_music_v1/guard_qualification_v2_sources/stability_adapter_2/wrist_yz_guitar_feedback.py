"""Bounded wrist target correction from current world-frame guitar error."""
import numpy as np
from scipy.spatial.transform import Rotation

JOINTS = ('L_Wrist_y', 'L_Wrist_z')
SCALE = np.r_[np.full(3, .03), np.full(3, np.deg2rad(5.))]
KAPPA = .00242502989755426  # rad^2 / s
RATE_LIMIT = .002  # rad / s
ANGLE_LIMIT = .005  # rad
CONTROL_DT = 1. / 60.


def update(response, goal_p, goal_q, current_p, current_q, delta, enabled, command_time):
    """Return two offsets and the exact observation used before submitting PD."""
    response = np.asarray(response, dtype=np.float64)
    delta = np.asarray(delta, dtype=np.float64)
    if response.shape != (6, 2) or not np.isfinite(response).all():
        raise ValueError('finite world 6x2 response required')
    if delta.shape != (2,) or not np.isfinite(delta).all() or np.any(abs(delta) > ANGLE_LIMIT):
        raise ValueError('two finite bounded correction angles required')
    error = np.r_[np.asarray(goal_p) - np.asarray(current_p),
                  (Rotation.from_quat(goal_q) * Rotation.from_quat(current_q).inv()).as_rotvec()]
    gradient = (response / SCALE[:, None]).T @ (error / SCALE)
    if not np.isfinite(gradient).all():
        raise ValueError('finite current guitar error required')
    active = bool(enabled and command_time > 2.)
    requested_rate = np.clip(KAPPA * gradient, -RATE_LIMIT, RATE_LIMIT) if active else np.zeros(2)
    following = np.clip(delta + requested_rate * CONTROL_DT, -ANGLE_LIMIT, ANGLE_LIMIT) if active else np.zeros(2)
    return following, dict(
        feedback_active=active, guitar_position_at_update_W_m=np.asarray(current_p).tolist(),
        guitar_quaternion_at_update_xyzw=np.asarray(current_q).tolist(),
        guitar_error_at_update_world_m_rad=error.tolist(), gradient_per_rad=gradient.tolist(),
        delta_before_rad=delta.tolist(), requested_rate_rad_s=requested_rate.tolist(),
        effective_rate_rad_s=((following - delta) / CONTROL_DT).tolist(), delta_after_rad=following.tolist())
