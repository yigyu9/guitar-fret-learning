"""Finite human right-arm goals in the initial world frame; real guitar unchanged."""
import numpy as np
from scipy.optimize import least_squares
from ..initial_pose_noise_v1 import pose
from ..strap import point_kinematics
from ..lower_body_release_v1.controller_horizontal_v4 import skew, vec
from ..seated_foot_support_v1.runtime_v6 import Controller as FootController


class Controller(FootController):
    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['right_arm_reference_mode'] == 'initial_world_finite_human_v2'
        state = scene.native()
        gp, gr = pose(state['guitar_body_states'][0])
        self.palm_W, self.palm_rotation_W = pose(state['human_body_states'][scene.human_bodies.index('RH:palm')])
        ref = self.right_reference
        p, r = pose(state['human_body_states'][ref['index']])
        self.material_W = p+r.apply(ref['local_m'])
        self.task_goal_W = gp+gr.apply(ref['goal_G_m'])

    def targets(self):
        s = self.s
        request = self.base_target.copy()
        assert s.cfg['mode'] == 'static'
        bias = s.cfg['lower_target_bias_rad']
        assert bias == {'L_Hip_y': .01, 'L_Hip_z': -.01, 'R_Hip_y': -.01, 'R_Hip_x': -.08}
        for n, value in bias.items():
            request[s.names.index(n)] += value
        if s.steps % 24 == 0:
            q = np.array([v['pos'] for v in s.native()['human_dof_states']])
            ix = self.right_arm
            lo = np.maximum(s.lower[ix]+1e-6, s.q_ref[ix]-.8)
            hi = np.minimum(s.upper[ix]-1e-6, s.q_ref[ix]+.8)
            def residual(v):
                trial = q.copy()
                trial[ix] = v
                ps = self.fk(trial)
                p, r = ps['RH:palm']
                sp, sr = ps['R_Shoulder']
                return np.r_[1000*(p-self.palm_W), 80*(self.palm_rotation_W.inv()*r).as_rotvec(),
                    1000*(sp+sr.apply(self.right_reference['local_m'])-self.material_W), .1*(v-s.q_ref[ix])]
            fit = least_squares(residual, np.clip(self.right_target, lo+1e-8, hi-1e-8),
                bounds=(lo, hi), max_nfev=30, ftol=1e-7, xtol=1e-7)
            self.right_target = fit.x
            errors = residual(fit.x)
            perr, rerr, serr = np.linalg.norm(errors[:3])/1000, np.linalg.norm(errors[3:6])/80, np.linalg.norm(errors[6:9])/1000
            assert np.isfinite(fit.x).all() and perr <= .01 and rerr <= .05 and serr <= .01
            self.right_info = dict(right_source_IK_position_error_m=float(perr), right_source_IK_rotation_error_rad=float(rerr),
                right_source_IK_support_point_error_m=float(serr), right_source_IK_step=s.steps, right_neck_correction_deg=0.)
        request[self.right_arm] = self.right_target
        row = s.command(dict(zip(s.names, request.tolist())))
        row.update(self.right_info)
        row.update(stage='static', right_palm_anchor_W_m=self.palm_W.tolist(),
            right_palm_anchor_xyzw=self.palm_rotation_W.as_quat().tolist(), right_material_anchor_W_m=self.material_W.tolist(),
            right_task_anchor_W_m=self.task_goal_W.tolist(), right_reference_mode=s.cfg['right_arm_reference_mode'])
        self.target_rows.append(row)
        return row

    def effort(self):
        effort, row = super().effort()
        s = self.s
        state = s.native()
        ref = self.right_reference
        body = state['human_body_states'][ref['index']]
        p, r = pose(body)
        point, velocity = point_kinematics(p, r.as_quat(), vec(body, 'linear'), vec(body, 'angular'),
            np.array(ref['local_m']), s.hcom[ref['index']])
        jac = s.jacobian.detach().cpu().numpy()[0].astype(float)[ref['index']-1]
        j = jac[:3]-skew(r.apply(np.array(ref['local_m'])-(s.hcom[ref['index']] if s.jacobian_mode == 'COM' else np.zeros(3))))@jac[3:]
        raw = 2000*(self.task_goal_W-point)-30*velocity
        force = raw*min(1., ref['cap_N']/max(np.linalg.norm(raw), 1e-12))
        old = next(v for v in row['support_points'] if v['body'] == 'R_Shoulder')
        delta = np.zeros(105)
        ix = ref['indices']
        delta[ix] = (j.T@(force-np.array(old['virtual_force_request_W_N'])))[ix]
        request = np.array(row['raw_requested105_Nm'])+delta
        effort[s.upper_effort_indices] = np.clip(request[s.upper_effort_indices],
            -s.pd_properties['effort'][s.upper_effort_indices], s.pd_properties['effort'][s.upper_effort_indices]).astype(np.float32)
        effort[s.zero_indices] = 0
        palm, palm_r = pose(state['human_body_states'][s.human_bodies.index('RH:palm')])
        row['replaced_current_G_right_task'] = dict(old)
        old.update(goal_W_m=self.task_goal_W.tolist(), goal_velocity_W_m_s=[0., 0., 0.],
            virtual_force_request_W_N=force.tolist(), point_world_error_m=float(np.linalg.norm(point-self.material_W)),
            point_world_velocity_m_s=velocity.tolist(), palm_world_error_m=float(np.linalg.norm(palm-self.palm_W)),
            palm_world_rotation_error_rad=float((self.palm_rotation_W.inv()*palm_r).magnitude()),
            mode='Finite human effort toward initial world task goal; original preload retained; no guitar force or constraint.')
        row.update(support_task105_Nm=(np.array(row['support_task105_Nm'])+delta).tolist(),
            raw_requested105_Nm=request.tolist(), submitted105_Nm=effort.astype(float).tolist())
        assert np.isfinite(effort).all() and s.native() == state
        return effort, row
