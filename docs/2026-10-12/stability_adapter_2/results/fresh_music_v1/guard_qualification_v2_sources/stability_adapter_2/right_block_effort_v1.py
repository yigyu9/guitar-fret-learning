"""Optional bounded human Thorax point task; free guitar and existing arm control."""
import numpy as np
from . import left_near_arm_effort_v3 as parent
from .initial_pose_noise_v1 import pose, save
from .strap import point_kinematics
from .dual_shoulder_effort_v1 import skew

LearningScene = parent.LearningScene
base = parent.base
create_effort = parent.create_effort


class EffortRecording(parent.EffortRecording):
    def __init__(self, env, out):
        super().__init__(env, out)
        from isaacgym import gymtorch
        from .run_joint_hold import native_state
        state = native_state(env); gp, gr = pose(state['guitar_body_states'][0])
        index = env.human_bodies.index('R_Thorax'); p, rotation = pose(state['human_body_states'][index])
        witness = env.contract.candidate['right_block_cradle']['capsule_body']['R_Thorax']
        surface = np.array(witness['guitar_surface_G_m'])
        normal = np.array(witness['capsule_axis_G_m'])-surface; normal /= np.linalg.norm(normal)
        point = gp+gr.apply(surface+normal*witness['gap_m'])
        local = rotation.inv().apply(point-p); desired = point-.004*gr.apply(normal)
        cap = float(env.contract.config.get('thorax_point_cap_N', 0)); assert cap in (0., 10.)
        prop = env.gym.get_actor_rigid_body_properties(env.env, env.human)[index]
        com = np.array([prop.com.x, prop.com.y, prop.com.z])
        tensor = gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim, 'human'))
        own = np.array([i for i, n in enumerate(env.names) if n.startswith('R_Thorax_')])
        children = np.array([i for i, n in enumerate(env.names) if n.startswith(('R_Shoulder_', 'R_Elbow_', 'R_Wrist_'))])
        assert len(own) == 3
        save(self.out/'thorax_point_configuration.json', {'cap_N': cap, 'K_N_m': 2000, 'D_Ns_m': 30,
             'point_local_m': local.tolist(), 'desired_point_W_m': desired.tolist(), 'indices': own.tolist(),
             'source_normal_G': normal.tolist(), 'world_goal_fixed': True,
             'scope': 'virtual human task force request; only right Thorax3 effort; no guitar wrench/attachment'})
        previous = env.right_effort_controller; self.thorax_rows = []
        def control():
            before = previous().copy(); state = native_state(env)
            p, rotation = pose(state['human_body_states'][index]); body = state['human_body_states'][index]
            vec = lambda field: np.array([body['vel'][field][k] for k in 'xyz'])
            point, velocity = point_kinematics(p, rotation.as_quat(), vec('linear'), vec('angular'), local, com)
            block = tensor.detach().cpu().numpy()[0, index-1].astype(float).copy()
            j = block[:3]-skew(rotation.apply(local-(com if self.mode == 'COM' else 0)))@block[3:]
            qdot = np.array([s['vel'] for s in state['human_dof_states']])
            error = float(np.linalg.norm(j@qdot-velocity)); child = float(abs(j[:, children]).max())
            if error > .01 or child > 1e-10: raise RuntimeError('Thorax Jacobian scope/velocity mismatch')
            force = 2000*(desired-point)-30*velocity
            force *= min(1., cap/max(float(np.linalg.norm(force)), 1e-12))
            task = j.T@force
            requested = np.array(self.effort_rows[-1]['requested_efforts_Nm'])[own]+task[own]
            final = before.copy(); final[own] = np.clip(requested, -env.pd_properties['effort'][own], env.pd_properties['effort'][own]).astype(np.float32)
            self.thorax_rows.append({'physics_step': env.steps, 'point_W_m': point.tolist(), 'velocity_W_m_s': velocity.tolist(),
                'point_error_m': float(np.linalg.norm(desired-point)), 'jacobian_velocity_error_m_s': error,
                'child_jacobian_max_abs': child, 'jacobian_all': j.tolist(), 'virtual_force_request_W_N': force.tolist(),
                'task_Thorax3_Nm': task[own].tolist(), 'requested_Thorax3_Nm': requested.tolist(),
                'before_efforts_Nm': before.astype(float).tolist(), 'final_efforts_Nm': final.astype(float).tolist()})
            assert native_state(env) == state
            return final
        env.right_effort_controller = control

    def encode(self):
        save(self.out/'thorax_point_rows.json', {'rows': self.thorax_rows, 'scope': 'final combined human actuator vector'})
        return super().encode()
