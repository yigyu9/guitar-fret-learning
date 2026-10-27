"""Pure initial poses: horizontal-to-ground neck, front board facing world +Y."""
import numpy as np
from scipy.spatial.transform import Rotation

BODY_CENTER_LOCAL = np.array([0., -.4, -.0217])


def placement(body_center, elevation_deg):
    center = np.asarray(body_center, dtype=float)
    if center.shape != (3,) or not np.isfinite(center).all() or not np.isfinite(elevation_deg) or abs(elevation_deg) > 10:
        raise ValueError('finite body center and neck elevation within +/-10deg required')
    angle = np.radians(elevation_deg)
    neck = np.array([-np.cos(angle), 0., np.sin(angle)])
    front = np.array([0., 1., 0.])
    rotation = Rotation.from_matrix(np.column_stack((np.cross(neck, front), neck, front)))
    return center - rotation.apply(BODY_CENTER_LOCAL), rotation.as_quat()
