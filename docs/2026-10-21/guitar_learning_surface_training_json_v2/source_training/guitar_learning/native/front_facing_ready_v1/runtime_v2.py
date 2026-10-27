"""미검증 margin후보: 기존제어후 Chest virtual목표만0.25mm 추가한다."""
import numpy as np
from ..initial_pose_noise_v1 import pose
from .runtime_v1 import Controller as PreviousController,Scene

MODE='finite_human_Chest_extra0p25mm_v1'


class Controller(PreviousController):
    def __init__(self,scene):
        super().__init__(scene)
        assert scene.cfg['ready_chest_margin_mode']==MODE
        assert scene.cfg['ready_chest_margin_extra_m']==.00025 and scene.cfg['ready_chest_margin_ramp_s']==[10,10.5]

    def effort(self):
        effort,row=super().effort();s=self.s
        if s.steps<2400:return effort,row
        state=s.native();target=s.target.astype(float).copy()
        point=next(p for p in row['support_points'] if p['body']=='Chest');previous=dict(point);parent=row['chest_action_preload']
        _,gr=pose(state['guitar_body_states'][0]);normal=gr.apply(point['normal_G']);normal/=np.linalg.norm(normal)
        ix=np.array(parent['indices'],dtype=int);J=np.array(parent['point_J9'])
        assert len(ix)==9 and [s.names[j] for j in ix]==[n+'_'+a for n in ('Torso','Spine','Chest') for a in 'xyz']
        assert not set(ix)&set(s.lower_indices) and not set(ix)&set(s.position_indices) and not set(ix)&set(s.zero_indices)
        u=float(np.clip((s.steps/240-10)/.5,0,1));ramp=u*u*(3-2*u);extra=.00025*ramp
        depth=point['human_virtual_goal_depth_m'];assert abs(depth-(.00925+.0005*ramp))<1e-15
        raw=point['raw_normal_request_N']-2000*extra;force=normal*np.clip(raw,-20,0)
        delta=np.zeros(105);delta[ix]=J.T@(force-np.array(point['virtual_force_request_W_N']))
        old_raw=np.array(row['raw_requested105_Nm']);old_task=np.array(row['support_task105_Nm']);old_submitted=effort.copy();request=old_raw+delta
        effort[s.upper_effort_indices]=np.clip(request[s.upper_effort_indices],-s.pd_properties['effort'][s.upper_effort_indices],s.pd_properties['effort'][s.upper_effort_indices]).astype(np.float32)
        effort[s.zero_indices]=0
        outside=np.setdiff1d(np.arange(105),ix)
        assert np.array_equal(effort[outside],old_submitted[outside])
        for ids in (s.lower_indices,s.position_indices,s.zero_indices):assert np.array_equal(effort[ids],old_submitted[ids])
        goal=np.array(point['goal_W_m'])-extra*normal
        point.update(goal_W_m=goal.tolist(),raw_normal_request_N=float(raw),virtual_force_request_W_N=force.tolist(),human_virtual_goal_depth_m=depth+extra,
            ready_margin_extra_depth_m=extra,ready_margin_final_extra_depth_m=.00025,mode='가설후보humanChest virtual0.25mm추가.원K/D/cap유지;실제침투목표/상태주입/기타힘아님.')
        row['ready_chest_margin']=dict(mode=MODE,extra_m=extra,final_extra_m=.00025,ramp_s=[10.,10.5],ramp_fraction=ramp,K_N_m=2000.,D_Ns_m=30.,cap_N=20.,
            base_depth_m=depth,total_depth_m=depth+extra,normal_W=normal.tolist(),normal_G=point['normal_G'],point_local_m=parent['point_local_m'],Jacobian6x105=parent['Jacobian6x105'],jacobian_frame=parent['jacobian_frame'],
            point_J9=J.tolist(),indices=ix.tolist(),joint_names=[s.names[j] for j in ix],source_gap_m=point['nearest_source_gap_m'],goal_W_m=goal.tolist(),previous_Chest=previous,
            previous_raw_requested105_Nm=old_raw.tolist(),previous_support_task105_Nm=old_task.tolist(),previous_submitted105_Nm=old_submitted.astype(float).tolist(),delta105_Nm=delta.tolist(),
            target_preserved=True,state_preserved=True,outside9_unchanged=True,lower_unchanged=True,position48_unchanged=True,zero8_unchanged=True,
            scope='원SO3/.5mm부모effort완료후 Chest9만JTF차분.원부모metadata보존/관절목표·하체·POSITION48·zero8·실제상태불변.성공미채택margin가설.')
        row.update(raw_requested105_Nm=request.tolist(),support_task105_Nm=(old_task+delta).tolist(),submitted105_Nm=effort.astype(float).tolist())
        assert np.isfinite(effort).all() and np.array_equal(s.target.astype(float),target) and s.native()==state
        return effort,row
