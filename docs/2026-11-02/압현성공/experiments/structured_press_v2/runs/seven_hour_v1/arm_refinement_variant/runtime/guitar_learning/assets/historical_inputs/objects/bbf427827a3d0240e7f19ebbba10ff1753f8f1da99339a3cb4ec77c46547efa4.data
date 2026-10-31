"""Single native physics scene with one 81-DOF target owner; no reward API."""
from .environment import gymapi, np, vector, quaternion
from .capture_isaac_gym_initial import CameraEnvironment
from .environment_contract_v1 import EnvironmentContract, MARKERS
from .strap import point_kinematics
from .run_joint_hold import native_state
from scipy.spatial.transform import Rotation

from .environment_guard_v2 import InitializationGuard

class LearningScene(CameraEnvironment):
    def __init__(self, contract=None):
        self.contract = contract or EnvironmentContract()
        self.initialization_complete = False
        self.target_submission_allowed = False
        self.integrating_control = False
        self.forbidden_calls, self.initial_state_write_calls = [], []
        acquire = gymapi.acquire_gym
        gymapi.acquire_gym = lambda: InitializationGuard(acquire(), self)
        try:
            super().__init__({}, [0., 0., 0.])
        finally:
            gymapi.acquire_gym = acquire
        try:
            if any(self.config[k] != self.contract.config[k] for k in ('control_hz', 'physics_hz')):
                raise AssertionError('native/contract clock mismatch')
            params = self.gym.get_sim_params(self.sim)
            if abs(params.dt-1/240) > 1e-9 or params.use_gpu_pipeline or params.physx.use_gpu:
                raise AssertionError('unexpected physics dt/backend')
            if self.names != self.contract.names or not np.array_equal(self.initial_q, self.contract.q_ref.astype(np.float32)):
                raise AssertionError('native initialization/action order mismatch')
            if not np.array_equal(self.lower, self.contract.lower) or not np.array_equal(self.upper, self.contract.upper):
                raise AssertionError('native limits changed')
            self.pd_properties = self.gym.get_actor_dof_properties(self.env, self.human).copy()
            for field in ('driveMode', 'lower', 'upper', 'stiffness', 'damping', 'effort'):
                expected = np.array([p[field] for p in self.contract.reference['PD_properties']], dtype=self.pd_properties[field].dtype)
                if not np.array_equal(self.pd_properties[field], expected):
                    raise AssertionError('reference PD mismatch: '+field)
            self.com = {self.names_for(actor)[i]: np.array([p.com.x, p.com.y, p.com.z])
                for actor in (self.human, self.guitar)
                for i, p in enumerate(self.gym.get_actor_rigid_body_properties(self.env, actor))}
            missing = set(MARKERS + ['Pelvis', 'Chest']) - set(self.human_bodies)
            if missing: raise ValueError('missing native marker bodies: '+str(missing))
            bodies = self.bodies(self.human)
            self.z_chest = vector(bodies[self.human_bodies.index('Chest')]['pose']['p'])[2]
            self.chest_ref = self.chest_in_pelvis(bodies)
            self.initialization_complete = True
            self.initial_state = native_state(self)
            self.observe()
        except BaseException:
            self.close()
            raise

    def names_for(self, actor):
        return self.human_bodies if actor == self.human else self.guitar_bodies

    def set_main_offsets(self, offsets):
        raise RuntimeError('legacy 66-offset control disabled; use step(action81)')

    def _create_scene(self):
        candidate = self.contract.candidate
        self.goal_position = np.array(candidate['position_W_m'])
        x, y, z, w = candidate['quaternion_xyzw']
        self.pose['params']['guitar_quat_wxyz_computed'] = [w, x, y, z]
        super()._create_scene()
        # Set construction-time coordinates before InitialEnvironment's one
        # prepare/reset submission; never change state during control steps.
        self.initial_q = self.contract.q_ref.astype(np.float32)
        props = self.gym.get_actor_dof_properties(self.env, self.human)
        props['stiffness'][self.torso_indices] *= self.contract.config['body_kp_scale']
        props['damping'][self.torso_indices] *= self.contract.config['body_kd_scale']
        if not self.gym.set_actor_dof_properties(self.env, self.human, props):
            raise RuntimeError('native POSITION PD properties rejected')
        center = self.goal_position + Rotation.from_quat([x,y,z,w]).apply([0., .064, 0.])
        for view in ('hands', 'hands_collision'):
            self.gym.set_camera_location(self.cameras[view], self.env,
                gymapi.Vec3(*(center+[.05,.42,.12])), gymapi.Vec3(*center))

    def chest_in_pelvis(self, bodies):
        chest = Rotation.from_quat(quaternion(bodies[self.human_bodies.index('Chest')]['pose']['r']))
        pelvis = Rotation.from_quat(quaternion(bodies[self.human_bodies.index('Pelvis')]['pose']['r']))
        return pelvis.inv()*chest

    def origin_motion(self, state, name):
        q = quaternion(state['pose']['r'])
        p, v = point_kinematics(vector(state['pose']['p']), q,
            vector(state['vel']['linear']), vector(state['vel']['angular']), np.zeros(3), self.com[name])
        return p, Rotation.from_quat(q).as_matrix(), v, vector(state['vel']['angular'])

    def observe(self):
        human, guitar = self.bodies(self.human), self.bodies(self.guitar)[0]
        dof = self.gym.get_actor_dof_states(self.env, self.human, gymapi.STATE_ALL)
        markers = [self.origin_motion(human[self.human_bodies.index(n)], n) for n in MARKERS]
        palms = [self.origin_motion(human[self.human_bodies.index(n)], n)[1] for n in ('LH:palm', 'RH:palm')]
        gp, gr, gv, gw = self.origin_motion(guitar, self.guitar_bodies[0])
        delta = (self.chest_in_pelvis(human)*self.chest_ref.inv()).as_matrix()
        observation, manifest = self.contract.encode(
            {'q': dof['pos'], 'qdot': dof['vel']}, self.target, delta, (gp, gr, gv, gw),
            [(p, v) for p, rot, v, omega in markers], palms, self.z_chest, self.steps)
        self.observation_manifest = manifest
        return observation

    def step(self, action):
        if self.contract.clock(self.steps)['diagnostic_time_limit']:
            raise RuntimeError('diagnostic time limit reached; reset required')
        before = native_state(self)
        requested, final = self.contract.targets(action, self.target)
        self.target = final
        self.target_submission_allowed = True
        try: self._submit_targets()
        finally: self.target_submission_allowed = False
        actual = self.gym.get_actor_dof_position_targets(self.env, self.human)
        if not np.array_equal(actual, final) or native_state(self) != before:
            raise AssertionError('target readback mismatch or command changed state')
        self.integrating_control = True
        try:
            for _ in range(self.contract.physics_per_control): self.step_physics()
        finally:
            self.integrating_control = False
        observation = self.observe()
        return observation, {'clock': self.contract.clock(self.steps),
            'requested_rad': requested.tolist(), 'final_rad': final.astype(float).tolist(),
            'rate_limited_count': int(np.count_nonzero(np.abs(final-requested)>2e-7)),
            'training_ready': False}

    def step_physics(self):
        # Deliberately bypass the legacy cable force/66-offset/PI update paths.
        if not self.integrating_control: raise RuntimeError('physics integration must belong to step(action81)')
        self.tension = 0.
        self.gym.simulate(self.sim)
        self.gym.fetch_results(self.sim, True)
        self.steps += 1


class PhysicsEnvironment:
    """Fresh-scene reset for diagnostics; GPU/vector reset is a later backend."""
    def __init__(self): self.scene = None

    def reset(self):
        self.close()
        self.scene = LearningScene()
        return self.scene.observe()

    def step(self, action):
        if self.scene is None: raise RuntimeError('reset before step')
        return self.scene.step(action)

    def close(self):
        if self.scene is not None:
            self.scene.close()
            self.scene = None
