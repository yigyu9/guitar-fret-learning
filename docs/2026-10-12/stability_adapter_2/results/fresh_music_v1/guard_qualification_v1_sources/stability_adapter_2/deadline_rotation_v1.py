"""CPU pilot SO(3) envelope: numerical membership, conservative distance interval.

Extrinsic xyz degrees: X=[45,90], Y=[50,100], Z=[135,180].
Membership checks both nonsingular Euler branches and the full +90 degree
gimbal family. Boundaries use 64 machine eps radians of numerical tolerance.
Outside distances are NOT certified exact nearest distances: the feasible
local fit supplies an upper bound; a complete grid and its Euler-cell covering
radius supply a global lower bound. This does not close the production gate.
"""

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


BOUNDS_DEG = np.array([[45., 90.], [50., 100.], [135., 180.]])
_TOL_RAD = 64 * np.finfo(float).eps


class RotationEnvelope:
    exact_distance_certified = False
    production_gate_complete = False

    def __init__(self, grid_step_deg=5.):
        if not 2. <= grid_step_deg <= 5.:
            raise ValueError('pilot grid step must be in [2, 5] degrees')
        self.bounds_rad = np.radians(BOUNDS_DEG)
        axes = [np.linspace(lo, hi, int(np.ceil((hi-lo)/grid_step_deg))+1)
                for lo, hi in BOUNDS_DEG]
        self.grid_euler_deg = np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1).reshape(-1, 3)
        self.grid_quaternion = Rotation.from_euler('xyz', self.grid_euler_deg, degrees=True).as_quat()
        # d(R(a),R(b)) <= |dx|+|dy|+|dz| by composition invariance and
        # the triangle inequality. Every box point has a grid node within
        # half an actual grid spacing along each axis, including endpoints.
        self.covering_radius_rad = float(np.radians(sum((a[1]-a[0])/2 for a in axes)))
        self._previous_fit_rad = None

    def _inside_euler(self, rotation):
        matrix = rotation.as_matrix()
        cos_y = np.hypot(matrix[0, 0], matrix[1, 0])
        if cos_y <= _TOL_RAD:
            if matrix[2, 0] >= 0.:  # -90 degrees has no allowed Y representation.
                return None
            delta = np.arctan2(matrix[0, 1], matrix[0, 2])  # X-Z at Y=+90.
            x_lo, x_hi = self.bounds_rad[0]
            z_lo, z_hi = self.bounds_rad[2]
            lo, hi = max(x_lo, z_lo+delta), min(x_hi, z_hi+delta)
            if lo <= hi+_TOL_RAD:
                x = np.clip((lo+hi)/2, x_lo, x_hi)
                return np.array([x, np.pi/2, np.clip(x-delta, z_lo, z_hi)])
            return None
        x = np.arctan2(matrix[2, 1], matrix[2, 2])
        y = np.arctan2(-matrix[2, 0], cos_y)
        z = np.arctan2(matrix[1, 0], matrix[0, 0])
        for candidate in (np.array([x, y, z]), np.array([x+np.pi, np.pi-y, z+np.pi])):
            candidate = np.mod(candidate, 2*np.pi)
            if np.all(candidate >= self.bounds_rad[:, 0]-_TOL_RAD) and np.all(
                    candidate <= self.bounds_rad[:, 1]+_TOL_RAD):
                return np.clip(candidate, self.bounds_rad[:, 0], self.bounds_rad[:, 1])
        return None

    def distance(self, quaternion_xyzw):
        quaternion = np.asarray(quaternion_xyzw, dtype=float)
        if quaternion.shape != (4,) or not np.isfinite(quaternion).all():
            raise ValueError('expected four finite xyzw quaternion components')
        norm = np.linalg.norm(quaternion)
        if not np.isfinite(norm) or norm == 0.:
            raise ValueError('quaternion must have a finite nonzero norm')
        quaternion = quaternion/norm
        rotation = Rotation.from_quat(quaternion)
        inside_euler = self._inside_euler(rotation)
        if inside_euler is not None:
            self._previous_fit_rad = inside_euler.copy()
            return {'inside': True, 'upper_rad': 0., 'lower_rad': 0.,
                    'nearest_euler_deg': np.degrees(inside_euler).tolist(),
                    'nearest_quaternion_xyzw': quaternion.tolist(), 'uncertainty_rad': 0.}

        # Absolute dot identifies q and -q. atan2 retains precision near zero.
        dots = np.clip(np.abs(np.einsum('ij,j->i', self.grid_quaternion, quaternion)), 0., 1.)
        grid_distance = 2*np.arctan2(np.sqrt(np.maximum(0., 1.-dots*dots)), dots)
        index = int(np.argmin(grid_distance))
        lower = max(0., float(grid_distance[index])-self.covering_radius_rad-1e-12)
        best_euler = np.radians(self.grid_euler_deg[index])
        inverse = rotation.inv()

        def residual(euler):
            return (inverse*Rotation.from_euler('xyz', euler)).as_rotvec()

        upper = float(np.linalg.norm(residual(best_euler)))
        seeds = [best_euler]
        if self._previous_fit_rad is not None:
            seeds.append(self._previous_fit_rad)
        for seed in seeds:
            fit = least_squares(residual, seed, bounds=self.bounds_rad.T,
                                max_nfev=24, ftol=1e-9, xtol=1e-9, gtol=1e-9)
            feasible = np.clip(fit.x, self.bounds_rad[:, 0], self.bounds_rad[:, 1])
            distance = float(np.linalg.norm(residual(feasible)))
            if distance < upper:
                upper, best_euler = distance, feasible
        self._previous_fit_rad = best_euler.copy()
        return {'inside': False, 'upper_rad': upper, 'lower_rad': lower,
                'nearest_euler_deg': np.degrees(best_euler).tolist(),
                'nearest_quaternion_xyzw': Rotation.from_euler('xyz', best_euler).as_quat().tolist(),
                'uncertainty_rad': max(0., upper-lower)}
