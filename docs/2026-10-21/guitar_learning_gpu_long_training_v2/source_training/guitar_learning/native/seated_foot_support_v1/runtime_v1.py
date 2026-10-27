"""Only initial root placement and chair dimensions extend the guarded scene."""
import numpy as np
from ..lower_body_release_v1.scene_v8 import Scene as PreviousScene


class Scene(PreviousScene):
    def _create_scene(self):
        delta=np.array(self.candidate['root_initial_translation_W_m'],dtype=float)
        half=np.array(self.candidate['chair_half_m'],dtype=float)
        assert delta.shape==(3,) and np.array_equal(delta[:2],[0.,0.]) and -.05<=delta[2]<=0
        previous=np.array(self.pose['params']['chair']['half'],dtype=float)
        assert np.array_equal(half[:2],previous[:2]) and abs(2*(half[2]-previous[2])-delta[2])<1e-12
        self.pose['root_qpos'][:3]=(np.array(self.pose['root_qpos'][:3])+delta).tolist()
        self.pose['params']['chair']['half']=half.tolist()
        super()._create_scene()
