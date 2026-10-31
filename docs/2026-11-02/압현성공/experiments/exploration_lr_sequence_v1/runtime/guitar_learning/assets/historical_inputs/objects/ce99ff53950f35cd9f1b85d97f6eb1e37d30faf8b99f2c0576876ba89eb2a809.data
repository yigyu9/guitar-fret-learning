"""생성자에서만 새 절대일정을 연결하며 원 제어·모션 본문은 상속한다."""
from unittest.mock import patch
from . import runtime_v1 as legacy_runtime,motion_v1 as legacy_motion
from .runtime_v2 import Controller as PreviousController
from .runtime_v4 import Scene
from .protocol_v2 import PROTOCOL,schedule,SETTLED_HOLD


class Controller(PreviousController):
    def __init__(self,scene):
        assert scene.cfg['validation_protocol']==PROTOCOL
        assert scene.cfg['ready_schedule']==schedule(scene.cfg['ready_case'])
        assert scene.cfg['seconds']==scene.cfg['ready_schedule']['seconds']
        assert scene.cfg['ready_settled_hold_s']==SETTLED_HOLD
        state=scene.native()
        originals=(legacy_runtime.PROTOCOL,legacy_runtime.schedule,legacy_motion.schedule)
        try:
            with patch.object(legacy_runtime,'PROTOCOL',PROTOCOL),patch.object(legacy_runtime,'schedule',schedule),patch.object(legacy_motion,'schedule',schedule):
                super().__init__(scene)
                assert scene.play_logic.plan==schedule(scene.cfg['ready_case'])
        finally:
            assert legacy_runtime.PROTOCOL is originals[0] and legacy_runtime.schedule is originals[1] and legacy_motion.schedule is originals[2]
            assert scene.native()==state
