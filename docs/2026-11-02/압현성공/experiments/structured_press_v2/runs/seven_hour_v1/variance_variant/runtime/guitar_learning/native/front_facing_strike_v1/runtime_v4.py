"""원cap 안에서10초 후 human Chest 목표만0.5mm 더 깊게 요청한다."""
import numpy as np
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.controller_horizontal_v4 import skew
from .runtime_v2 import Controller as PreviousController, Scene, PROTOCOL

MODE = 'finite_human_Chest_0p5mm_v1'


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['chest_action_preload_mode'] == MODE
        assert scene.cfg['chest_action_preload_extra_m'] == .0005
        assert scene.cfg['chest_action_preload_ramp_s'] == [10.,10.5]

    def effort(self):
        effort, row = super().effort()
        s = self.s
        if s.steps < 2400:
            return effort, row
        state = s.native()
        ref = next(v for v in s.references if v['body'] == 'Chest')
        point = next(v for v in row['support_points'] if v['body'] == 'Chest')
        previous = dict(point)
        p, r = pose(state['human_body_states'][ref['index']])
        _, gr = pose(state['guitar_body_states'][0])
        normal = gr.apply(point['normal_G'])
        local = r.inv().apply(np.array(point['point_W_m'])-p)
        block = s.jacobian.detach().cpu().numpy()[0].astype(float)[ref['index']-1]
        com = s.hcom[ref['index']] if s.jacobian_mode == 'COM' else np.zeros(3)
        j = block[:3]-skew(r.apply(local-com))@block[3:]
        u = float(np.clip((s.steps/240-10.)/.5,0.,1.))
        ramp = u*u*(3-2*u)
        extra = .0005*ramp
        base_depth = point['human_virtual_goal_depth_m']
        assert abs(base_depth-.00925) < 1e-15
        raw = point['raw_normal_request_N']-2000.*extra
        force = normal*np.clip(raw,-ref['cap_N'],0.)
        ix = np.array(ref['indices'],dtype=int)
        assert [s.names[a] for a in ix] == [name+'_'+axis for name in ('Torso','Spine','Chest') for axis in 'xyz']
        assert ref['cap_N'] == 20. and not set(ix)&set(s.lower_indices) and not set(ix)&set(s.position_indices)
        delta = np.zeros(105)
        delta[ix] = (j.T@(force-np.array(point['virtual_force_request_W_N'])))[ix]
        old_raw = np.array(row['raw_requested105_Nm'])
        old_task = np.array(row['support_task105_Nm'])
        old_submitted = effort.copy()
        request = old_raw+delta
        effort[s.upper_effort_indices] = np.clip(request[s.upper_effort_indices],
            -s.pd_properties['effort'][s.upper_effort_indices],s.pd_properties['effort'][s.upper_effort_indices]).astype(np.float32)
        effort[s.zero_indices] = 0
        other = np.setdiff1d(np.arange(105),ix)
        assert np.array_equal(effort[other],old_submitted[other])
        assert np.array_equal(effort[s.lower_indices],old_submitted[s.lower_indices])
        assert np.array_equal(effort[s.position_indices],old_submitted[s.position_indices])
        assert np.array_equal(effort[s.zero_indices],old_submitted[s.zero_indices])
        point.update(goal_W_m=(np.array(point['goal_W_m'])-extra*normal).tolist(),
            raw_normal_request_N=float(raw),virtual_force_request_W_N=force.tolist(),
            human_virtual_goal_depth_m=base_depth+extra,action_extra_human_virtual_goal_depth_m=extra,
            action_final_extra_depth_m=.0005,depth_velocity_feedforward=False,
            mode='원K2000/D30/cap20을 유지한 human Chest 동작0.5mm 추가지지목표. 기타힘 없음.')
        row['chest_action_preload'] = dict(mode=MODE,extra_m=extra,final_extra_m=.0005,
            ramp_s=[10.,10.5],ramp_fraction=ramp,K_N_m=2000.,D_Ns_m=30.,cap_N=20.,
            normal_W=normal.tolist(),point_local_m=local.tolist(),Jacobian6x105=block.tolist(),
            jacobian_frame=s.jacobian_mode,indices=ix.tolist(),joint_names=[s.names[a] for a in ix],
            point_J9=j[:,ix].tolist(),delta105_Nm=delta.tolist(),previous_Chest=previous,
            previous_raw_requested105_Nm=old_raw.tolist(),previous_support_task105_Nm=old_task.tolist(),
            previous_submitted105_Nm=old_submitted.astype(float).tolist(),base_depth_m=base_depth,total_depth_m=base_depth+extra,
            lower_unchanged=True,position48_unchanged=True,zero8_unchanged=True,state_preserved=True,
            scope='원runtime18 지지항 이후 spring 목표깊이만 추가. 기존 actual-surface damping 유지, depth-rate feedforward 없음. Chest9 JTF만 더하고 원upper33 cap을 재적용. 하체/POS48/zero8 그대로, 실제상태 및 기타직접명령 없음.')
        row.update(support_task105_Nm=(old_task+delta).tolist(),raw_requested105_Nm=request.tolist(),
                   submitted105_Nm=effort.astype(float).tolist())
        assert np.isfinite(effort).all() and s.native() == state
        return effort, row
