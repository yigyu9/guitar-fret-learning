"""Change finite human right-arm world goals; the free guitar is untouched."""
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.native.paths import read, sha
from .runtime_v11 import Controller as PreviousController


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        cfg = scene.cfg
        assert cfg['finite_right_goal_mode'] == 'constant_world_affine_human_anchors_v1'
        assert sha(cfg['finite_right_goal_spec']) == cfg['finite_right_goal_spec_sha256']
        spec = read(cfg['finite_right_goal_spec'])
        assert spec['initial_candidate_sha256'] == cfg['candidate_sha256']
        quat = np.array(spec['R_delta_xyzw'], dtype=float)
        translation = np.array(spec['translation_W_m'], dtype=float)
        assert quat.shape == (4,) and translation.shape == (3,)
        assert np.isfinite(quat).all() and np.isfinite(translation).all()
        assert abs(np.linalg.norm(quat)-1.) < 1e-12
        rotation = Rotation.from_quat(quat)
        state = scene.native()
        before = dict(palm_W_m=self.palm_W.tolist(), material_W_m=self.material_W.tolist(),
                      task_goal_W_m=self.task_goal_W.tolist(), palm_xyzw=self.palm_rotation_W.as_quat().tolist())
        self.palm_W = rotation.apply(self.palm_W)+translation
        self.material_W = rotation.apply(self.material_W)+translation
        self.task_goal_W = rotation.apply(self.task_goal_W)+translation
        self.palm_rotation_W = rotation*self.palm_rotation_W
        after = dict(palm_W_m=self.palm_W.tolist(), material_W_m=self.material_W.tolist(),
                     task_goal_W_m=self.task_goal_W.tolist(), palm_xyzw=self.palm_rotation_W.as_quat().tolist())
        self.goal_correction = dict(spec_sha256=cfg['finite_right_goal_spec_sha256'],
            R_delta_xyzw=quat.tolist(), translation_W_m=translation.tolist(), before=before, after=after,
            scope='Constant finite human IK/task goals only. No guitar pose, force, attachment or state command.')
        assert scene.native() == state

    def targets(self):
        row = super().targets()
        row['finite_human_right_goal'] = self.goal_correction
        return row

    def effort(self):
        effort, row = super().effort()
        right = next(point for point in row['support_points'] if point['body'] == 'R_Shoulder')
        right['mode'] = 'Finite human effort to corrected constant world goal; original preload/gains/caps retained.'
        row['finite_human_right_goal_spec_sha256'] = self.goal_correction['spec_sha256']
        return effort, row
