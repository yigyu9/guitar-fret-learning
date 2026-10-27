"""Bounded world-palm feedback composed with joint PD targets, never body states."""
from .environment import np, vector, quaternion
from scipy.spatial.transform import Rotation


def palm_poses(env):
    bodies = env.bodies(env.human)
    return [(vector(bodies[env.human_bodies.index(name)]['pose']['p']),
             quaternion(bodies[env.human_bodies.index(name)]['pose']['r']))
            for name in ('LH:palm', 'RH:palm')]


class PalmGripFeedback:
    def __init__(self, matrix, initial_poses):
        self.matrix = np.asarray(matrix, dtype=float)
        if self.matrix.shape != (12, 24) or not np.isfinite(self.matrix).all():
            raise ValueError('finite 12 by 24 palm Jacobian required')
        self.inverse = self.matrix.T @ np.linalg.inv(self.matrix @ self.matrix.T + .01**2*np.eye(12))
        self.initial = initial_poses
        self.integral = np.zeros(24)
        self.delta = np.zeros(24)

    def update(self, env, dt):
        self.previous_integral = self.integral.copy()
        guitar = env.bodies(env.guitar)[0]
        gp = vector(guitar['pose']['p'])
        gr = Rotation.from_quat(quaternion(guitar['pose']['r']))
        guitar_rotation_error = (Rotation.from_quat(env.goal_quaternion)*gr.inv()).as_rotvec()
        rotation_offset = np.clip(guitar_rotation_error, -.05, .05)
        error = []
        desired_positions = []
        for (p0, q0), (p, q) in zip(self.initial, palm_poses(env)):
            offset = np.clip(env.goal_position-gp + np.cross(guitar_rotation_error, p0-env.goal_position), -.01, .01)
            desired_positions.append((p0+offset).tolist())
            orientation_error = (Rotation.from_rotvec(rotation_offset)*Rotation.from_quat(q0)*Rotation.from_quat(q).inv()).as_rotvec()
            error.extend(np.r_[p0+offset-p, .08*orientation_error])
        joint_error = self.inverse @ np.array(error)
        self.joint_error = joint_error
        proposed = self.integral + joint_error*dt
        raw = 2*joint_error+4*proposed
        clipped = np.clip(raw, -.15, .15)
        bounded = self.delta + np.clip(clipped-self.delta, -dt, dt)
        blocked = joint_error*(raw-bounded)>1e-12
        self.integral = np.where(blocked, self.integral, proposed)
        raw = 2*joint_error+4*self.integral
        self.delta += np.clip(np.clip(raw, -.15, .15)-self.delta, -dt, dt)
        return self.delta.copy(), {'task_error_m_and_scaled_rad':list(error),
            'desired_palm_positions_m':desired_positions, 'guitar_rotation_error_rad':guitar_rotation_error.tolist(),
            'applied_delta_rad':self.delta.tolist(), 'integral_rad_s':self.integral.tolist(),
            'integral_blocked':blocked.tolist(), 'cap_rad':.15, 'rate_rad_s':1.}

    def accept_final_target(self, requested, delivered, record):
        blocked = self.joint_error*(requested-delivered)>1e-12
        self.integral = np.where(blocked, self.previous_integral, self.integral)
        record['final_target_integral_blocked'] = blocked.tolist()
        record['integral_rad_s'] = self.integral.tolist()
