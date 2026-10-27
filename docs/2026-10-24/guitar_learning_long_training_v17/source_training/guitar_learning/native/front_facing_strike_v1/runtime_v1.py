"""10초 전 원 정면 제어, 이후 근위 목표 유지와 distal6 타현."""
import numpy as np
from ..initial_pose_noise_v1 import pose
from ..grounded_guitar_support_v1.runtime_v18 import Controller as PreparedController
from ..seated_foot_support_v1.runtime_v6 import Scene as FootScene
from ..front_facing_pose_v1.runtime_v1 import Controller as FrontController, HEADING_BODIES, horizontal_forward, heading_error_rad
from .motion_v1 import Motion

PROTOCOL = 'front_prepare5_hold5_distalstrike4_v1'


class Scene(FootScene):
    def command(self, named):
        named = self.play_logic.apply(named)
        row = super().command(named)
        self.play_logic.record_final(row)
        return row


class Controller(PreparedController):
    apply = FrontController.apply

    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['seconds'] == 14 and scene.cfg['mode'] == 'static'
        assert scene.cfg['validation_protocol'] == PROTOCOL
        assert scene.cfg['play_case'] in ('baseline', 'strike')
        state = scene.native()
        poses = {n: pose(b) for n, b in zip(scene.human_bodies, state['human_body_states'])}
        self.front_reference_W = horizontal_forward(poses['Pelvis'][1])
        self.front_initial_heading = {n: float(np.rad2deg(heading_error_rad(poses[n][1], self.front_reference_W))) for n in HEADING_BODIES}
        target = self.fk(self.base_target)
        self.front_base_heading = {n: float(np.rad2deg(heading_error_rad(target[n][1], self.front_reference_W))) for n in HEADING_BODIES}
        assert all(abs(v) <= 2 for v in self.front_initial_heading.values())
        assert all(abs(v) <= 2 for v in self.front_base_heading.values())
        assert scene.foot_target_logic is self and scene.native() == state
        scene.play_logic = Motion(scene, self.fk)
        self.play_latch = None

    def targets(self):
        s = self.s
        if s.steps < 2400:
            return super().targets()
        if self.play_latch is None:
            assert s.steps == 2400 and self.target_rows[-1]['physics_step_before'] == 2396
            final = s.target.astype(float).copy()
            assert np.array_equal(final, self.target_rows[-1]['final105_rad'])
            assert np.array_equal(final[s.play_logic.proximal], s.play_logic.spec['proximal_latch']['final6_rad'])
            self.play_latch = dict(latch_step=2400, source_target_step=2396,
                indices105=self.right_arm.tolist(), joint_names=[s.names[j] for j in self.right_arm],
                final12_rad=final[self.right_arm].tolist(),
                mode='final_submitted_R12_latch_then_distal6_motion_v1',
                scope='유한 목표만 유지. 실제 상태는 동적이며 R12 world IK는10초부터 호출하지 않는다.')
        request = self.base_target.copy()
        bias = s.cfg['lower_target_bias_rad']
        assert bias == {'L_Hip_y': .01, 'L_Hip_z': -.01, 'R_Hip_y': -.01, 'R_Hip_x': -.08}
        for name, value in bias.items():
            request[s.names.index(name)] += value
        request[self.right_arm] = self.play_latch['final12_rad']
        row = s.command(dict(zip(s.names, request.tolist())))
        row.update(stage=s.play_logic.stage, right_control_mode='final_submitted_R12_latch_then_distal6_motion_v1',
            right_target_latch=self.play_latch, right_world_palm_IK_active=False,
            right_palm_anchor_W_m=self.palm_W.tolist(), right_palm_anchor_xyzw=self.palm_rotation_W.as_quat().tolist(),
            right_material_anchor_W_m=self.material_W.tolist(), right_task_anchor_W_m=self.task_goal_W.tolist(),
            right_reference_mode=s.cfg['right_arm_reference_mode'], finite_human_right_goal=self.goal_correction,
            right_source_IK_scope='10초부터 R12 IK 없음. Motion의 distal6 위치오차만 별도 계산. Human material effort 유지.')
        self.target_rows.append(row)
        return row
