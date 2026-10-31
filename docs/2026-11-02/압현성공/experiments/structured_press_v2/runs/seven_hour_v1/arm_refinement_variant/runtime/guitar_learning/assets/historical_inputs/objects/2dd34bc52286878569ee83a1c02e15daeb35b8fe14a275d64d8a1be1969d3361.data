"""Original routed tension-only cable law, evaluated with NumPy."""
import numpy as np


def rotate(q, vector):
    xyz = np.asarray(q[:3])
    cross = 2 * np.cross(xyz, vector)
    return vector + q[3] * cross + np.cross(xyz, cross)


def point_kinematics(position, q, linear_com, angular, local_point, local_com):
    """Native Gym reports body-origin pose and COM linear velocity."""
    point = position + rotate(q, local_point)
    velocity = linear_com + np.cross(angular, rotate(q, local_point - local_com))
    return point, velocity


def cable_forces(points, velocities, rest_length, stiffness, damping, max_tension):
    delta = np.diff(points, axis=0)
    lengths = np.linalg.norm(delta, axis=1)
    directions = delta / np.maximum(lengths[:, None], 1e-8)
    length = float(lengths.sum())
    length_rate = float((directions * np.diff(velocities, axis=0)).sum())
    tension = (float(np.clip(stiffness * (length - rest_length) + damping * length_rate,
                             0, max_tension)) if length > rest_length else 0.0)
    segment_forces = tension * directions
    forces = np.zeros_like(points)
    forces[:-1] += segment_forces
    forces[1:] -= segment_forces
    return forces, tension, length, length_rate
