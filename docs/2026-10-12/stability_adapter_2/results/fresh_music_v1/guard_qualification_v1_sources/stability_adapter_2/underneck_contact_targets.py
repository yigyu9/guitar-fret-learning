"""Moving illustrative grip regions, not contact enforcement or a controller."""
import numpy as np
from scipy.spatial.transform import Rotation


NORMALS_G = {'palm': [1., 0., 0.], 'thumb': [0., 0., -1.],
             'front': [0., 0., 1.]}


def moving_regions(position, quaternion, regions_G):
    p, q = np.asarray(position, dtype=float), np.asarray(quaternion, dtype=float)
    if p.shape != (3,) or q.shape != (4,) or not np.isfinite(p).all() or not np.isfinite(q).all():
        raise ValueError('finite world xyz and xyzw quaternion required')
    if np.linalg.norm(q) < 1e-12:
        raise ValueError('zero quaternion')
    rotation = Rotation.from_quat(q)
    result = {}
    for role, normal in NORMALS_G.items():
        polygon = np.asarray(regions_G[role], dtype=float)
        if polygon.shape != (4, 3) or not np.isfinite(polygon).all():
            raise ValueError('finite 4x3 illustrative region required')
        local_normal = np.cross(polygon[1] - polygon[0], polygon[2] - polygon[0])
        length = np.linalg.norm(local_normal)
        if length < 1e-12:
            raise ValueError('nondegenerate illustrative region required')
        local_normal /= length
        if local_normal @ normal < 0:
            local_normal = -local_normal
        outward = rotation.apply(local_normal)
        result[role] = {'polygon_W_m': p + rotation.apply(polygon),
                        'outward_normal_W': outward,
                        'desired_hand_normal_W': -outward}
    return result
