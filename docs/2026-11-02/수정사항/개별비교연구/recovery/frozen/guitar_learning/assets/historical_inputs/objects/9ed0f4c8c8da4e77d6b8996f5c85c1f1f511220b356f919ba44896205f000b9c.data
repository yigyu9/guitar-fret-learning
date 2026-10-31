"""긴ready protocol의 명시 초기화; 성공한Chest/SO3 effort는 그대로 상속한다."""
import xml.etree.ElementTree as ET
import numpy as np
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.common import HUMAN
from ..grounded_guitar_support_v1.runtime_v18 import Controller as PreparedController
from ..seated_foot_support_v1.runtime_v6 import Scene as FootScene
from ..front_facing_pose_v1.runtime_v1 import HEADING_BODIES,horizontal_forward,heading_error_rad
from ..front_facing_strike_v1.runtime_v5 import Controller as StrikeController
from .protocol_v1 import PROTOCOL,schedule
from .motion_v1 import Motion


class Scene(FootScene):
    def command(self,named):
        named=self.play_logic.apply(named)
        row=super().command(named)
        self.play_logic.record_final(row)
        return row


class Controller(StrikeController):
    def __init__(self,scene):
        PreparedController.__init__(self,scene)
        assert scene.cfg['validation_protocol']==PROTOCOL and scene.cfg['mode']=='static'
        assert scene.cfg['ready_schedule']==schedule(scene.cfg['ready_case'])
        assert scene.cfg['seconds']==scene.cfg['ready_schedule']['seconds']
        assert scene.cfg['chest_action_preload_mode']=='finite_human_Chest_0p5mm_v1'
        assert scene.cfg['chest_action_preload_extra_m']==.0005 and scene.cfg['chest_action_preload_ramp_s']==[10.,10.5]
        assert scene.cfg['distal_rotational_feedback_mode']=='finite_distal6_SO3_child_PD_v1' and scene.cfg['distal_rotational_feedback_start_s']==10.
        state=scene.native();poses={n:pose(b) for n,b in zip(scene.human_bodies,state['human_body_states'])}
        self.front_reference_W=horizontal_forward(poses['Pelvis'][1])
        self.front_initial_heading={n:float(np.rad2deg(heading_error_rad(poses[n][1],self.front_reference_W))) for n in HEADING_BODIES}
        target=self.fk(self.base_target)
        self.front_base_heading={n:float(np.rad2deg(heading_error_rad(target[n][1],self.front_reference_W))) for n in HEADING_BODIES}
        assert all(abs(v)<=2 for v in self.front_initial_heading.values()) and all(abs(v)<=2 for v in self.front_base_heading.values())
        assert scene.foot_target_logic is self and scene.native()==state
        self.rotational_groups=[];xml=ET.parse(HUMAN)
        for body,parent,K,D,cap in (('R_Elbow','R_Shoulder',60.,3.,100.),('R_Wrist','R_Elbow',20.,1.,60.)):
            joints=xml.find(".//body[@name='"+body+"']").findall('joint');ix=np.array([scene.names.index(j.get('name')) for j in joints]);basis=np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints])
            assert [scene.names[j] for j in ix]==[body+'_'+a for a in 'xyz'] and np.array_equal(basis.T@basis,np.eye(3))
            assert np.array_equal(scene.control_kp[ix],np.full(3,K)) and np.array_equal(scene.control_kd[ix],np.full(3,D)) and np.array_equal(scene.pd_properties['effort'][ix],np.full(3,cap))
            assert set(ix)<=set(scene.upper_effort_indices) and not set(ix)&set(scene.zero_indices)
            self.rotational_groups.append((body,parent,ix,basis))
        scene.play_logic=Motion(scene,self.fk);self.play_latch=None

    def targets(self):
        s=self.s
        if s.steps<2400:return PreparedController.targets(self)
        if self.play_latch is None:
            assert s.steps==2400 and self.target_rows[-1]['physics_step_before']==2396
            final=s.target.astype(float).copy();assert np.array_equal(final,self.target_rows[-1]['final105_rad'])
            assert np.array_equal(final[s.play_logic.proximal],s.play_logic.right_spec['proximal_latch']['final6_rad'])
            self.play_latch=dict(latch_step=2400,source_target_step=2396,indices105=self.right_arm.tolist(),joint_names=[s.names[j] for j in self.right_arm],final12_rad=final[self.right_arm].tolist(),mode='final_submitted_R12_latch_then_distal6_motion_v1',scope='유한목표latch이며실제상태고정아님.10초이후R12worldIK없음.')
        request=self.base_target.copy();bias=s.cfg['lower_target_bias_rad']
        assert bias=={'L_Hip_y':.01,'L_Hip_z':-.01,'R_Hip_y':-.01,'R_Hip_x':-.08}
        for name,value in bias.items():request[s.names.index(name)]+=value
        request[self.right_arm]=self.play_latch['final12_rad']
        row=s.command(dict(zip(s.names,request.tolist())))
        row.update(stage=s.play_logic.stage,right_control_mode='final_submitted_R12_latch_then_distal6_motion_v1',right_target_latch=self.play_latch,right_world_palm_IK_active=False,
            right_palm_anchor_W_m=self.palm_W.tolist(),right_palm_anchor_xyzw=self.palm_rotation_W.as_quat().tolist(),right_material_anchor_W_m=self.material_W.tolist(),right_task_anchor_W_m=self.task_goal_W.tolist(),right_reference_mode=s.cfg['right_arm_reference_mode'],finite_human_right_goal=self.goal_correction,
            right_source_IK_scope='ready 단일스케줄러의LH26/Rdistal6만목표변경.원R12worldIK는10초이후호출안함.')
        self.target_rows.append(row);return row
