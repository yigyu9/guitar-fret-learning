"""원 정면·근위목표·유한effort를 유지하고 새 distal6 모션만 연결한다."""
from .runtime_v1 import Controller as OriginalController, Scene, PROTOCOL
from .motion_v2 import Motion


class Controller(OriginalController):
    def __init__(self, scene):
        super().__init__(scene)
        scene.play_logic = Motion(scene, self.fk)
