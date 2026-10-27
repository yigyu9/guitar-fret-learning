"""Same right support plus finite left-arm scalar PD and gravity compensation."""
import numpy as np
from . import dual_shoulder_effort_v1 as right
from .initial_pose_noise_v1 import save, pose

LearningScene = right.LearningScene
base = right.base


def left_arm_indices(names):
    indices = np.array([i for i, n in enumerate(names)
                        if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist'))])
    assert len(indices) == 12
    return indices


class ArmEffortGuard(right.ArmEffortGuard):
    def __getattr__(self, name):
        if name != 'apply_actor_dof_efforts': return super().__getattr__(name)
        def controlled(env, actor, efforts):
            owner = self.owner; value = np.asarray(efforts)
            owned = np.r_[right.right_indices(owner.names), left_arm_indices(owner.names)]
            other = np.ones(81, dtype=bool); other[owned] = False
            if not (owner.integrating_control and owner.right_effort_window and
                    env == owner.env and actor == owner.human and value.shape == (81,) and
                    np.isfinite(value).all() and np.all(value[other] == 0) and
                    np.all(abs(value) <= owner.pd_properties['effort']+1e-6)):
                owner.forbidden_calls.append(name); raise RuntimeError('human effort outside bilateral24 owner/caps')
            result = self.gym.apply_actor_dof_efforts(env, actor, value)
            if result is False: raise RuntimeError('bilateral human actuator effort rejected')
            owner.right_effort_calls += 1
            return result
        return controlled


def create_effort(owner):
    right.create_effort(owner)
    from .environment import gymapi
    indices = left_arm_indices(owner.names)
    before = owner.gym.get_actor_dof_properties(owner.env, owner.human).copy()
    owner.left_arm_kp = before['stiffness'][indices].astype(float).copy()
    owner.left_arm_kd = before['damping'][indices].astype(float).copy()
    requested = before.copy()
    requested['driveMode'][indices] = gymapi.DOF_MODE_EFFORT
    requested['stiffness'][indices] = 0; requested['damping'][indices] = 0
    if not owner.gym.set_actor_dof_properties(owner.env, owner.human, requested):
        raise RuntimeError('left EFFORT construction rejected')
    actual = owner.gym.get_actor_dof_properties(owner.env, owner.human).copy()
    assert np.array_equal(actual, requested)
    owner.left_arm_mode = {'before': {n: before[n].tolist() for n in before.dtype.names},
                           'applied': {n: actual[n].tolist() for n in actual.dtype.names},
                           'indices': indices.tolist(), 'scope': 'bilateral24 EFFORT, remaining57 POSITION; finite model caps'}


def factory(recording, enabled):
    Parent = right.factory(recording, enabled)
    class Scene(Parent):
        def step(self, action):
            from .run_joint_hold import native_state
            if self.contract.clock(self.steps)['diagnostic_time_limit']: raise RuntimeError('time limit reached')
            before = native_state(self); requested, final = self.contract.targets(action, self.target)
            self.target = final; self.target_submission_allowed = True
            try: self._submit_targets()
            finally: self.target_submission_allowed = False
            actual = self.gym.get_actor_dof_position_targets(self.env, self.human)
            owned = np.r_[right.right_indices(self.names), left_arm_indices(self.names)]
            mask = np.ones(81, dtype=bool); mask[owned] = False
            preserved = native_state(self) == before
            if not (np.isfinite(actual).all() and np.array_equal(actual[mask], final[mask]) and preserved):
                raise AssertionError('POSITION57 targets/state changed')
            self.position_command_rows.append({'physics_step': self.steps, 'requested_target_rad': requested.tolist(),
                'logical_final_target_rad': final.astype(float).tolist(), 'native_position_target_readback_rad': actual.astype(float).tolist(),
                'position57_exact': True, 'state_preserved': preserved,
                'effort_scope': 'right12/left12 ignore POSITION readback and consume final targets through one finite effort command'})
            self.integrating_control = True
            try:
                for _ in range(self.contract.physics_per_control): self.step_physics()
            finally: self.integrating_control = False
            return self.observe(), {'clock': self.contract.clock(self.steps), 'requested_rad': requested.tolist(),
                                   'final_rad': final.astype(float).tolist(), 'training_ready': False}
    return Scene


class EffortRecording(right.EffortRecording):
    def __init__(self, env, out):
        super().__init__(env, out)
        from isaacgym import gymtorch
        from .run_joint_hold import native_state
        indices = left_arm_indices(env.names)
        props = env.gym.get_actor_rigid_body_properties(env.env, env.human)
        com = np.array([[v.com.x, v.com.y, v.com.z] for v in props]); mass = np.array([v.mass for v in props])
        tensor = gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim, 'human'))
        assert tuple(tensor.shape) == (1, len(env.human_bodies)-1, 6, 81)
        old_control = env.right_effort_controller; self.left_rows = []
        save(self.out/'left_arm_effort_configuration.json', {'left_indices': indices.tolist(),
             'K_posture_Nm_rad': env.left_arm_kp.tolist(), 'D_posture_Nms_rad': env.left_arm_kd.tolist(),
             'joint_effort_caps_Nm': env.pd_properties['effort'][indices].tolist(),
             'human_mass_kg': mass.tolist(), 'human_COM_local_m': com.tolist(), 'mode_properties': env.left_arm_mode,
             'scope': 'same initial pose; native original left scalar K/D, human gravity feedforward; no hand task force or guitar force'})
        def control():
            submitted = old_control().copy(); state = native_state(env)
            jac = tensor.detach().cpu().numpy()[0].astype(float).copy(); gravity = np.zeros(81)
            for body in range(1, len(env.human_bodies)):
                _, rotation = pose(state['human_body_states'][body]); block = jac[body-1]
                jcom = block[:3] if self.mode == 'COM' else block[:3]-right.skew(rotation.apply(com[body]))@block[3:]
                gravity -= jcom.T@(mass[body]*np.array([0., 0., -9.81]))
            q = np.array([r['pos'] for r in state['human_dof_states']]); velocity = np.array([r['vel'] for r in state['human_dof_states']])
            target = env.target.astype(float).copy()
            posture = env.left_arm_kp*(target[indices]-q[indices])-env.left_arm_kd*velocity[indices]
            requested = gravity[indices]+posture
            submitted[indices] = np.clip(requested, -env.pd_properties['effort'][indices], env.pd_properties['effort'][indices]).astype(np.float32)
            if not np.isfinite(submitted).all(): raise ValueError('nonfinite left actuator')
            self.left_rows.append({'physics_step': env.steps, 'left_indices': indices.tolist(), 'q_left_rad': q[indices].tolist(),
                'qdot_left_rad_s': velocity[indices].tolist(), 'target_left_rad': target[indices].tolist(),
                'jacobian_frame': self.mode, 'gravity_left_Nm': gravity[indices].tolist(), 'posture_left_Nm': posture.tolist(),
                'requested_left_Nm': requested.tolist(), 'submitted_left_Nm': submitted[indices].astype(float).tolist(),
                'combined_submitted_efforts_Nm': submitted.astype(float).tolist()})
            assert native_state(env) == state
            return submitted
        env.right_effort_controller = control

    def encode(self):
        save(self.out/'left_arm_effort_rows.json', {'rows': self.left_rows, 'scope': 'one bilateral command per physics step; right rows separately preserved'})
        save(self.out/'axilla_effort_rows.json', {'scope': 'unchanged right human upper-arm point command, not contact force', 'rows': self.axilla_rows})
        save(self.out/'position_command_rows.json', {'scope': 'POSITION57 readback; bilateral24 EFFORT position readback ignored', 'rows': self.env.position_command_rows})
        save(self.out/'effort_control_rows.json', {'scope': 'right12 contribution before left12 merge; actual combined actuator vector in left_arm_effort_rows',
             'rows': self.effort_rows, 'right_effort_calls': self.env.right_effort_calls,
             'right_effort_window_closed': not self.env.right_effort_window})
        return right.EffortRecording.__bases__[0].encode(self)
