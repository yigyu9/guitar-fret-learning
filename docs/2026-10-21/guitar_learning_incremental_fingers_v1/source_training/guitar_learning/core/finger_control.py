"""Fixed left finger exploration profile; native joint limits stay authoritative."""
import numpy as np

from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES


def default_profile():
    return dict(schema='guitar_learning.flexible_left_fingers.v1',
                finger_rate_rad_s=4., finger_smoothing_alpha=.45,
                finger_stiffness=12., finger_damping=1.5,
                thumb_stiffness=8., thumb_damping=1.25,
                scope='left21_native_joint_limits')


def validate_profile(value):
    """Accept only the recorded fixed profile; return a private JSON safe copy."""
    expected = default_profile()
    if (not isinstance(value, dict) or set(value) != set(expected) or
            any(type(value[key]) is not type(item) or value[key] != item
                for key, item in expected.items())):
        raise ValueError('exact flexible left finger profile required')
    return expected


def profile_control_settings(names, q_ref, lower, upper, half_ranges, rates, smoothing):
    """Copy controls and expand only LH21 to both asymmetric native endpoints.

    Half ranges remain reference centred inputs to the existing signed codec.
    Choosing the larger native distance lets its clipping recover both native
    endpoints, with normalized zero still equal to the prepared reference.
    """
    names = tuple(names)
    if len(set(names)) != len(names) or not set(LEFT_HAND_NAMES) <= set(names):
        raise ValueError('unique native names including all left21 required')
    arrays = [np.array(value, dtype=float, copy=True)
              for value in (q_ref, lower, upper, rates)]
    if any(value.shape != (len(names),) or not np.isfinite(value).all()
           for value in arrays):
        raise ValueError('finite aligned native reference, bounds and rates required')
    reference, low, high, rate = arrays
    half = np.array(half_ranges, dtype=float, copy=True)
    alpha = np.array(smoothing, dtype=float, copy=True)
    if alpha.ndim == 0:
        alpha = np.full(39, float(alpha))
    if (half.shape != (39,) or not np.isfinite(half).all() or np.any(half <= 0.) or
            alpha.shape != (39,) or not np.isfinite(alpha).all() or
            np.any(alpha <= 0.) or np.any(alpha > 1.) or
            np.any(low > high) or np.any(reference < low) or
            np.any(reference > high) or np.any(rate < 0.)):
        raise ValueError('valid native bounds and39 channel controls required')
    profile = default_profile()
    for name in LEFT_HAND_NAMES:
        native, action = names.index(name), ACTIVE_NAMES.index(name)
        if low[native] >= high[native]:
            raise ValueError('left finger native joint must have positive range')
        half[action] = max(reference[native]-low[native], high[native]-reference[native])
        rate[native] = profile['finger_rate_rad_s']
        alpha[action] = profile['finger_smoothing_alpha']
    return half, rate, alpha
