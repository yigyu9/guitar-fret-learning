"""Small radian residual around the current frozen-baseline nominal."""
import numpy as np

CAPS_RAD = {'body': .03, 'head': .10, 'arm': .30, 'finger': .20}


def bounded_target(action, nominal, lower, upper, groups):
    action, nominal, lower, upper = [np.asarray(v, dtype=float)
                                   for v in (action, nominal, lower, upper)]
    if any(v.shape != (81,) or not np.isfinite(v).all()
           for v in (action, nominal, lower, upper)):
        raise ValueError('finite81 codec inputs required')
    if (len(groups) != 81 or [groups.count(k) for k in CAPS_RAD] != [9, 6, 24, 42]
            or np.any(np.abs(action) > 1) or np.any(lower >= upper)
            or np.any(nominal < lower) or np.any(nominal > upper)):
        raise ValueError('ordered upper81 groups/bounds/action invalid')
    caps = np.array([CAPS_RAD[g] for g in groups])
    return np.clip(nominal + caps*action, lower, upper)
