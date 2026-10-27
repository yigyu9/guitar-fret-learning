"""Two bounded proximal human point tasks follow the free guitar's current frame."""
import numpy as np
from . import left_near_arm_effort_v3 as parent
from .initial_pose_noise_v1 import pose, save
from .strap import point_kinematics
from .dual_shoulder_effort_v1 import skew, right_indices

LearningScene = parent.LearningScene
base = parent.base
create_effort = parent.create_effort


class EffortRecording(parent.EffortRecording):
    def __init__(self, env, out):
        assert env.contract.config.get('two_block_current_G') is True
        super().__init__(env, out)
        from isaacgym import gymtorch
        from .run_joint_hold import native_state
        initial = native_state(env); gp, gr = pose(initial['guitar_body_states'][0])
        tensor = gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim, 'human'))
        props = env.gym.get_actor_rigid_body_properties(env.env, env.human)
        references = []; self.two_block_rows = []; right = right_indices(env.names)
        for name, witness in [('R_Thorax',env.contract.candidate['right_block_cradle']['capsule_body']['R_Thorax']),
                              ('R_Shoulder',env.contract.candidate['right_block_cradle']['proximal_upper_arm30_witness'])]:
            i = env.human_bodies.index(name); p,r = pose(initial['human_body_states'][i])
            surface = np.array(witness['guitar_surface_G_m']); normal = np.array(witness['capsule_axis_G_m'])-surface
            normal /= np.linalg.norm(normal); point = gp+gr.apply(surface+normal*witness['gap_m'])
            owned = [j for j,n in enumerate(env.names) if n.startswith(('R_Thorax_',)) or (name == 'R_Shoulder' and n.startswith('R_Shoulder_'))]
            settings = env.contract.config.get('proximal_point_parameters', {}).get(name, {'cap_N':10.,'depth_m':.004})
            assert (settings['cap_N'],settings['depth_m']) in ((10.,.004),(20.,.008),(30.,.012))
            references.append({'body':name, 'index':i, 'local_m':r.inv().apply(point-p).tolist(),
                'goal_G_m':(surface+normal*(witness['gap_m']-settings['depth_m'])).tolist(), 'cap_N':settings['cap_N'], 'depth_m':settings['depth_m'], 'indices':owned,
                'COM_local_m':[props[i].com.x,props[i].com.y,props[i].com.z]})
        save(self.out/'two_block_configuration.json', {'references':references,'K_N_m':2000,'D_Ns_m':30,'caps_per_reference':True,
             'rule':'replace old fixed-world shoulder task; current guitar point velocity; human proximal3/6 only',
             'scope':'finite human task requests, not guitar force/contact force/attachment'})
        previous = env.right_effort_controller
        def control():
            before = previous().copy(); state = native_state(env); guitar = state['guitar_body_states'][0]; gp,gr = pose(guitar)
            vec = lambda body,field: np.array([body['vel'][field][k] for k in 'xyz'])
            qdot = np.array([s['vel'] for s in state['human_dof_states']]); jac = tensor.detach().cpu().numpy()[0].astype(float).copy()
            task = np.zeros(81); measures = []
            for reference in references:
                index = reference['index']; body = state['human_body_states'][index]; p,r = pose(body)
                local,com = np.array(reference['local_m']),np.array(reference['COM_local_m'])
                point,velocity = point_kinematics(p,r.as_quat(),vec(body,'linear'),vec(body,'angular'),local,com)
                goal,goal_velocity = point_kinematics(gp,gr.as_quat(),vec(guitar,'linear'),vec(guitar,'angular'),
                                                     np.array(reference['goal_G_m']),env.com[env.guitar_bodies[0]])
                block = jac[index-1]; j = block[:3]-skew(r.apply(local-(com if self.mode == 'COM' else 0)))@block[3:]
                error = float(np.linalg.norm(j@qdot-velocity)); child = [i for i,n in enumerate(env.names) if n.startswith(('R_Elbow_','R_Wrist_'))]
                if error > .01 or abs(j[:,child]).max() > 1e-10: raise RuntimeError('proximal task Jacobian velocity/child mismatch')
                force = 2000*(goal-point)+30*(goal_velocity-velocity); force *= min(1.,reference['cap_N']/max(float(np.linalg.norm(force)),1e-12))
                contribution = np.zeros(81); owned = reference['indices']; contribution[owned] = (j.T@force)[owned]; task += contribution
                measures.append({'body':reference['body'],'point_W_m':point.tolist(),'velocity_W_m_s':velocity.tolist(),
                    'goal_W_m':goal.tolist(),'goal_velocity_W_m_s':goal_velocity.tolist(),'jacobian_all':j.tolist(),
                    'jacobian_velocity_error_m_s':error,'virtual_force_request_W_N':force.tolist(),'task81_Nm':contribution.tolist()})
            row = self.effort_rows[-1]; old = np.array(row['axilla_point_task_right_Nm'])
            request = np.array(row['requested_efforts_Nm'])[right]-old+task[right]
            final = before.copy(); final[right] = np.clip(request,-env.pd_properties['effort'][right],env.pd_properties['effort'][right]).astype(np.float32)
            self.two_block_rows.append({'physics_step':env.steps,'points':measures,'superseded_fixed_shoulder_task_right_Nm':old.tolist(),
                'requested_right_Nm':request.tolist(),'before_efforts_Nm':before.astype(float).tolist(),'final_efforts_Nm':final.astype(float).tolist()})
            tracking = self.tracking_rows[-1]; tracking['before_two_block_efforts_Nm'] = tracking.pop('actual_combined_submitted_efforts_Nm')
            tracking['actual_combined_submitted_efforts_Nm'] = final.astype(float).tolist()
            assert native_state(env) == state
            return final
        env.right_effort_controller = control

    def encode(self):
        save(self.out/'two_block_rows.json', {'rows':self.two_block_rows,'scope':'actual final human81 command; old fixed shoulder task is removed, not summed'})
        return super().encode()
