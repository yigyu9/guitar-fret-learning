"""Bound teacher arm/thumb nominal around the reset's fixed preload."""
import numpy as np

ARM_CAP_RAD, LEFT_THUMB_CAP_RAD = .15, .10


def support_nominal(teacher, preload, lower, upper, groups, names):
    teacher, preload, lower, upper = [np.asarray(v, dtype=float)
                                    for v in (teacher, preload, lower, upper)]
    if any(v.shape != (81,) or not np.isfinite(v).all() for v in (teacher, preload, lower, upper)):
        raise ValueError('finite81 support inputs required')
    arm = np.array([g == 'arm' for g in groups])
    thumb = np.array([n.startswith('LH:thumb') for n in names])
    if (len(groups)!=81 or len(names)!=81 or arm.sum()!=24 or thumb.sum()!=5
            or any(groups[i]!='finger' for i in np.flatnonzero(thumb))
            or np.any(lower>=upper) or np.any(preload<lower) or np.any(preload>upper)
            or np.any(teacher<lower) or np.any(teacher>upper)):
        raise ValueError('native upper81 arm/left-thumb mapping or bounds invalid')
    caps = np.where(arm, ARM_CAP_RAD, np.where(thumb, LEFT_THUMB_CAP_RAD, np.inf))
    return np.clip(teacher, np.maximum(lower, preload-caps), np.minimum(upper, preload+caps))
