"""Explicitly disabled wrist task from initialization; left arm keeps original gravity/scalar PD."""
import numpy as np
from . import left_near_arm_effort_v2 as parent
from .initial_pose_noise_v1 import pose, save
from .strap import point_kinematics

LearningScene = parent.LearningScene
base = parent.base
factory = parent.factory
create_effort = parent.create_effort
ArmEffortGuard = parent.ArmEffortGuard
left_arm_indices = parent.left_arm_indices


class EffortRecording(parent.EffortRecording):
    def __init__(self, env, out):
        assert env.contract.config.get('left_wrist_tracking_off') is True
        parent.EffortRecording.__init__(self, env, out)
        from isaacgym import gymtorch
        from .run_joint_hold import native_state
        initial = native_state(env); gp, gr = pose(initial['guitar_body_states'][0])
        index = env.human_bodies.index('L_Wrist'); wp, wr = pose(initial['human_body_states'][index])
        goal_g = gr.inv().apply(wp-gp); left = left_arm_indices(env.names)
        props = env.gym.get_actor_rigid_body_properties(env.env, env.human)
        com = np.array([props[index].com.x, props[index].com.y, props[index].com.z])
        tensor = gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim, 'human'))
        assert tuple(tensor.shape) == (1, len(env.human_bodies)-1, 6, 81)
        previous = env.right_effort_controller; self.tracking_rows = []
        hold = False
        save(self.out/'left_wrist_tracking_configuration.json', {'goal_wrist_G_m': goal_g.tolist(),
             'K_N_m': 1000, 'D_Ns_m': 30, 'force_cap_N': 30, 'hold_for_entire_static_trial': hold,
             'pair_enabled_until_physics_s': None, 'disabled_from_initialization': True, 'unused_point_jacobian_diagnostic_only': True, 'human_body': 'L_Wrist', 'point_local_m': [0, 0, 0],
             'scope': 'human joint task torque only; virtual force request, not applied/measured guitar or contact force'})
        def control():
            before = previous().copy(); state = native_state(env)
            wrist = state['human_body_states'][index]; guitar = state['guitar_body_states'][0]
            p, rotation = pose(wrist); gp, gr = pose(guitar)
            vec = lambda body, field: np.array([body['vel'][field][k] for k in 'xyz'])
            point, velocity = point_kinematics(p, rotation.as_quat(), vec(wrist, 'linear'), vec(wrist, 'angular'), np.zeros(3), com)
            desired, desired_velocity = point_kinematics(gp, gr.as_quat(), vec(guitar, 'linear'), vec(guitar, 'angular'),
                                                         goal_g, env.com[env.guitar_bodies[0]])
            block = tensor.detach().cpu().numpy()[0, index-1].astype(float).copy()
            offset = -com if self.mode == 'COM' else np.zeros(3)
            jpoint = block[:3]-parent.right.skew(rotation.apply(offset))@block[3:]
            qdot = np.array([r['vel'] for r in state['human_dof_states']])
            error = float(np.linalg.norm(jpoint@qdot-velocity))
            # Tracking is OFF: this unused point-Jacobian error is diagnostic, not an actuator validity gate.
            enabled = False
            force = 1000*(desired-point)+30*(desired_velocity-velocity) if enabled else np.zeros(3)
            force *= min(1., 30/max(float(np.linalg.norm(force)), 1e-12))
            task = np.zeros(len(env.names))  # Explicit OFF: independent of the unused point Jacobian.
            requested = np.array(self.left_rows[-1]['requested_left_Nm'])+task[left]
            submitted = before.copy()
            submitted[left] = np.clip(requested, -env.pd_properties['effort'][left], env.pd_properties['effort'][left]).astype(np.float32)
            row = self.left_rows[-1]
            row['combined_before_tracking_efforts_Nm'] = row.pop('combined_submitted_efforts_Nm')
            self.tracking_rows.append({'physics_step': env.steps, 'enabled': enabled, 'wrist_point_W_m': point.tolist(),
                'desired_wrist_W_m': desired.tolist(), 'wrist_velocity_W_m_s': velocity.tolist(),
                'desired_velocity_W_m_s': desired_velocity.tolist(), 'point_error_m': float(np.linalg.norm(desired-point)),
                'jacobian_frame': self.mode, 'jacobian_velocity_error_m_s': error,
                'point_jacobian_all': jpoint.tolist(), 'virtual_force_request_W_N': force.tolist(),
                'task_left_Nm': task[left].tolist(), 'requested_left_Nm': requested.tolist(),
                'actual_combined_submitted_efforts_Nm': submitted.astype(float).tolist()})
            assert native_state(env) == state
            return submitted
        env.right_effort_controller = control

    def encode(self):
        save(self.out/'left_wrist_tracking_rows.json', {'rows': self.tracking_rows,
             'scope': 'final finite actuator vector after human preparation task; no native state writes'})
        save(self.out/'left_arm_effort_rows.json', {'rows': self.left_rows, 'scope': 'left gravity/scalar PD contribution before preparation task; final vector in left_wrist_tracking_rows'})
        save(self.out/'axilla_effort_rows.json', {'scope': 'unchanged right human upper-arm point command, not contact force', 'rows': self.axilla_rows})
        save(self.out/'position_command_rows.json', {'scope': 'POSITION57 readback; bilateral24 EFFORT readback ignored', 'rows': self.env.position_command_rows})
        save(self.out/'effort_control_rows.json', {'scope': 'right12 contribution before left merge; final combined vector in left_wrist_tracking_rows',
             'rows': self.effort_rows, 'right_effort_calls': self.env.right_effort_calls,
             'right_effort_window_closed': not self.env.right_effort_window})
        return parent.right.EffortRecording.__bases__[0].encode(self)
