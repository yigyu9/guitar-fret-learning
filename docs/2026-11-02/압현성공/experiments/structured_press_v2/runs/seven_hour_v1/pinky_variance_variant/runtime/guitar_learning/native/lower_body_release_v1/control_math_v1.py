"""Finite rotational stable-PD in native child-angular generalized coordinates."""
import numpy as np
from scipy.spatial.transform import Rotation


def rotation_error(q, target, basis):
    current = Rotation.from_rotvec(basis @ q)
    desired = Rotation.from_rotvec(basis @ target)
    return basis.T @ (current.inv() * desired).as_rotvec()


def stable_pd(mass, error, velocity, kp, kd, gravity, dt):
    """Predict backward-Euler feedback velocity, with gravity feed-forward.

    M(v_next-v)/dt = K e - (D+dt K)v_next after cancelling gravity.
    This is a finite, capped-by-caller effort, not a pose/state update.
    """
    mass = (mass + mass.T) / 2
    assert np.isfinite(mass).all() and np.linalg.eigvalsh(mass).min() > 0
    next_velocity = np.linalg.solve(mass + np.diag(dt*kd + dt*dt*kp),
                                    mass @ velocity + dt*kp*error)
    feedback = kp*error - (kd + dt*kp)*next_velocity
    return gravity + feedback, next_velocity, feedback
