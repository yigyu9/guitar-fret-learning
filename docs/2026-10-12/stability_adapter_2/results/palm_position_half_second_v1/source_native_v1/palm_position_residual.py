"""Approved bounded arm target calculation; never writes simulation state."""
import numpy as np
from scipy.optimize import lsq_linear

from .compare_palm_fk_coordinates import left_expmap_tangent
from .joint_hold_residual import JointHoldResidual


def source_position_jacobian(native, actual_left, point_minus_com):
    """Native COM velocity columns -> expmap position columns at source center."""
    native = np.asarray(native, dtype=float)
    actual_left = np.asarray(actual_left, dtype=float)
    r = np.asarray(point_minus_com, dtype=float)
    if native.shape != (6, 12) or actual_left.shape != (12,) or r.shape != (3,):
        raise ValueError('expected 6x12 Jacobian, 12 left coordinates, 3-vector offset')
    if not all(np.isfinite(v).all() for v in (native, actual_left, r)):
        raise ValueError('finite position Jacobian inputs required')
    corrected = native.copy()
    for k in range(0, 12, 3):
        corrected[:, k:k+3] = native[:, k:k+3] @ left_expmap_tangent(actual_left[k:k+3])
    x, y, z = r
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return corrected[:3] - skew @ corrected[3:]


def bounded_delta(matrix, desired, lower, upper):
    """Dense bounded least squares, including axes fixed by intersected bounds."""
    if (lower > upper).any():
        raise ValueError('empty target bound intersection')
    free = upper > lower
    delta = lower.copy()
    if free.any():
        rhs = desired - matrix[:, ~free] @ delta[~free]
        result = lsq_linear(matrix[:, free], rhs, bounds=(lower[free], upper[free]),
                            method='bvls', tol=1e-12, max_iter=100)
        if not result.success or not np.isfinite(result.x).all():
            raise RuntimeError('bounded position solve failed: ' + result.message)
        delta[free] = result.x
    return delta


class RatePalmResidual:
    def __init__(self, reference, lower, upper, palm_task=False):
        validated = JointHoldResidual(reference, lower, upper)
        self.reference = validated.reference
        self.lower, self.upper = validated.lower.copy(), validated.upper.copy()
        self.integral = np.zeros(24)
        self.previous = self.reference.copy()
        self.palm_task = palm_task

    def update(self, actual, dt, matrix=None, palm_error=None):
        actual = np.asarray(actual, dtype=float)
        if actual.shape != (24,) or not np.isfinite(actual).all() or not np.isfinite(dt) or dt <= 0:
            raise ValueError('finite actual 24-vector and positive dt required')
        if self.palm_task:
            matrix, palm_error = np.asarray(matrix, dtype=float), np.asarray(palm_error, dtype=float)
            if matrix.shape != (3, 12) or palm_error.shape != (3,) or not np.isfinite(matrix).all() or not np.isfinite(palm_error).all():
                raise ValueError('finite 3x12 position map and 3-vector palm error required')
        ref = self.reference
        low = np.maximum.reduce([np.full(24, -.15), self.lower-ref, self.previous-ref-.02])
        high = np.minimum.reduce([np.full(24, .15), self.upper-ref, self.previous-ref+.02])
        if (low > high).any():
            raise ValueError('empty target bound intersection')
        error = ref-actual
        proposed = self.integral+error*dt
        blocked = np.zeros(24, dtype=bool)
        solves = []
        for iteration in range(25):
            integral = np.where(blocked, self.integral, proposed)
            raw = error+2*integral
            pi = np.clip(np.clip(raw, -.15, .15), self.lower-ref, self.upper-ref)
            delta = np.clip(raw, low, high)
            if self.palm_task:
                augmented = np.vstack([matrix, .05*np.eye(12)])
                desired = np.concatenate([2*palm_error-matrix @ (ref[:12]-actual[:12]), .05*pi[:12]])
                delta[:12] = bounded_delta(augmented, desired, low[:12], high[:12])
            solves.append({'iteration': iteration, 'blocked_before': blocked.tolist(),
                           'raw_delta_rad': raw.tolist(), 'delta_rad': delta.tolist()})
            next_blocked = blocked | (error*(raw-delta) > 1e-12)
            if np.array_equal(blocked, next_blocked):
                break
            blocked = next_blocked
        else:
            raise RuntimeError('anti-windup did not terminate in 25 calculations')
        target = ref+delta
        if not np.isfinite(target).all():
            raise FloatingPointError('nonfinite final target')
        self.integral = integral
        self.previous = target.copy()
        record = {'error_at_update_rad': error.tolist(), 'integral_rad_s': integral.tolist(),
            'raw_delta_rad': raw.tolist(), 'applied_delta_rad': delta.tolist(),
            'integral_blocked': blocked.tolist(), 'saturated': (np.abs(raw-delta)>1e-10).tolist(),
            'delta_lower_rad': low.tolist(), 'delta_upper_rad': high.tolist(),
            'delta_PI_rad': pi.tolist(), 'anti_windup_iterations': solves,
            'calculated_arm_targets_rad': target.tolist()}
        if self.palm_task:
            predicted = matrix @ (target[:12]-actual[:12])
            record.update(position_J_m_per_rad=matrix.tolist(), palm_error_world_m=palm_error.tolist(),
                predicted_position_change_world_m=predicted.tolist(),
                position_task_residual_m=(predicted-2*palm_error).tolist(),
                objective=float(np.linalg.norm(predicted-2*palm_error)**2+.05**2*np.linalg.norm(delta[:12]-pi[:12])**2))
        return target, record
