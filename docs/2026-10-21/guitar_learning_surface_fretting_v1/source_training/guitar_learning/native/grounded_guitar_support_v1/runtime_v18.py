"""Add only0.25mm scheduled human Chest preload; original finite caps and Hip bias."""
import numpy as np
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.controller_horizontal_v4 import skew
from .runtime_v17 import Controller as PreviousController


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['chest_extra_goal_depth_m'] == .00025
        assert scene.cfg['chest_normal_goal_depth_m'] == .009
        assert scene.cfg['chest_initial_goal_depth_m'] == .007 and scene.cfg['chest_goal_ramp_s'] == [.75,1.25]

    def effort(self):
        effort, row = super().effort()
        s = self.s
        state = s.native()
        ref = next(v for v in s.references if v['body'] == 'Chest')
        old = next(v for v in row['support_points'] if v['body'] == 'Chest')
        before_point = dict(old)
        p, r = pose(state['human_body_states'][ref['index']])
        _, gr = pose(state['guitar_body_states'][0])
        normal = gr.apply(old['normal_G'])
        local = r.inv().apply(np.array(old['point_W_m'])-p)
        block = s.jacobian.detach().cpu().numpy()[0].astype(float)[ref['index']-1]
        com = s.hcom[ref['index']] if s.jacobian_mode == 'COM' else np.zeros(3)
        j = block[:3]-skew(r.apply(local-com))@block[3:]
        u = float(np.clip((s.steps/240-.75)/.5, 0., 1.))
        ramp = u*u*(3-2*u)
        extra = .00025*ramp
        base_depth = .007+.002*ramp
        assert abs(old['human_virtual_goal_depth_m']-base_depth) <= 1e-15
        raw = old['raw_normal_request_N']-2000*extra
        force = normal*np.clip(raw,-ref['cap_N'],0.)
        delta = np.zeros(105)
        ix = np.array(ref['indices'],dtype=int)
        assert len(ix)==9 and not set(ix)&set(s.lower_indices) and ref['cap_N']==20.
        delta[ix] = (j.T@(force-np.array(old['virtual_force_request_W_N'])))[ix]
        old_raw = np.array(row['raw_requested105_Nm'])
        old_task = np.array(row['support_task105_Nm'])
        old_submitted = effort.copy()
        request = old_raw+delta
        effort[s.upper_effort_indices] = np.clip(request[s.upper_effort_indices],
            -s.pd_properties['effort'][s.upper_effort_indices],s.pd_properties['effort'][s.upper_effort_indices]).astype(np.float32)
        effort[s.zero_indices] = 0
        assert np.array_equal(effort[s.lower_indices],old_submitted[s.lower_indices])
        old.update(goal_W_m=(np.array(old['goal_W_m'])-extra*normal).tolist(),
            raw_normal_request_N=float(raw),virtual_force_request_W_N=force.tolist(),
            human_virtual_goal_depth_m=base_depth+extra,legacy_human_virtual_goal_depth_m=base_depth,
            extra_human_virtual_goal_depth_m=extra,extra_final_goal_depth_m=.00025,
            depth_velocity_feedforward=False,
            mode='Original nearest-normal Chest human task plus scheduled0.25mm spring preload; same K2000/D30/cap20; no guitar force.')
        row['chest_extra_depth'] = dict(final_extra_depth_m=.00025,legacy_final_depth_m=.009,
            final_total_depth_m=.00925,ramp_fraction=ramp,ramp_s=[.75,1.25],extra_depth_m=extra,
            base_depth_m=base_depth,total_depth_m=base_depth+extra,K_N_m=2000.,D_Ns_m=30.,cap_N=20.,
            normal_W=normal.tolist(),point_local_m=local.tolist(),Jacobian6x105=block.tolist(),jacobian_frame=s.jacobian_mode,
            indices=ix.tolist(),joint_names=[s.names[a] for a in ix],point_J9=j[:,ix].tolist(),delta105_Nm=delta.tolist(),
            previous_Chest=before_point,previous_raw_requested105_Nm=old_raw.tolist(),previous_support_task105_Nm=old_task.tolist(),
            previous_submitted105_Nm=old_submitted.astype(float).tolist(),lower_unchanged=True,state_preserved=True,
            scope='Spring preload only; original actual-surface damping is retained without depth-rate feedforward. Human effort before original joint cap, finite Hip bias unchanged.')
        row.update(support_task105_Nm=(old_task+delta).tolist(),raw_requested105_Nm=request.tolist(),submitted105_Nm=effort.astype(float).tolist())
        assert np.isfinite(effort).all() and s.native()==state
        return effort,row
