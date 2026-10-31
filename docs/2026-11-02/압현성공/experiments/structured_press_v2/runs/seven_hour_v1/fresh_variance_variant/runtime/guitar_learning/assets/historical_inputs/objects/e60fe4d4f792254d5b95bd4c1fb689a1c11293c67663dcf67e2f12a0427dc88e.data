"""Same underneck scene with the inherited, passive tension-only strap enabled."""
from .underneck_pose_trial_v5 import UnderneckEnvironment, NoStrapGym
from .capture_isaac_gym_initial import GraphicsGym
from .environment import gymapi, np
from .strap import cable_forces


class UnderneckStrapEnvironment(UnderneckEnvironment):
    def __init__(self, candidate):
        super().__init__(candidate)
        # Keep the existing guard for every other force/effort/state API.
        assert isinstance(self.gym, GraphicsGym) and isinstance(self.gym.gym, NoStrapGym)
        self._submit_strap_force = self.gym.gym.gym.apply_body_force_at_pos
        self.strap_records = []
        self.strap_checks = {'finite': True, 'internal_force_balance': True,
                             'tension_bounds': True, 'constant_rest_length': True}
        self.fixed_rest_length = self.rest_length

    def step_physics(self):
        if self.steps % 4 == 0:
            if self.hold_enabled: self.update_hold()
            elif self.follow: self.update_follow()
        self.started = True
        points, velocities = self.route()
        strap = self.config['strap']
        forces, self.tension, length, rate = cable_forces(
            points, velocities, self.rest_length, strap['stiffness_n_per_m'],
            strap['damping_n_s_per_m'], strap['max_tension_n'])
        self.strap_checks['finite'] &= bool(np.isfinite(np.r_[points.ravel(), velocities.ravel(), forces.ravel(), self.tension]).all())
        self.strap_checks['internal_force_balance'] &= bool(np.allclose(forces.sum(axis=0), 0., rtol=0., atol=1e-9))
        self.strap_checks['tension_bounds'] &= bool(0. <= self.tension <= strap['max_tension_n'])
        self.strap_checks['constant_rest_length'] &= self.rest_length == self.fixed_rest_length
        if not all(self.strap_checks.values()): raise AssertionError(self.strap_checks)
        self.strap_records.append({'physics_step_before': self.steps, 'time_s': self.steps / 240,
            'points_W_m': points.tolist(), 'point_velocities_W_m_s': velocities.tolist(),
            'forces_W_n': forces.tolist(), 'tension_n': self.tension,
            'route_length_m': length, 'route_length_rate_m_s': rate,
            'rest_length_m': self.rest_length})
        for handle, point, force in zip(self.route_handles, points, forces):
            self._submit_strap_force(self.env, handle, gymapi.Vec3(*force),
                                    gymapi.Vec3(*point), gymapi.ENV_SPACE)
        self.gym.simulate(self.sim)
        self.gym.fetch_results(self.sim, True)
        self.steps += 1
