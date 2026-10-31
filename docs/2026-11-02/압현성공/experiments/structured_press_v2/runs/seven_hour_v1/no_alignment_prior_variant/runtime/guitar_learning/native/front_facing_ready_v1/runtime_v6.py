"""원 Controller5 생성자에만 protocol3를 연결한다. 제어/모션 본문은 불변."""
from unittest.mock import patch
from . import runtime_v5 as previous_runtime
from .runtime_v5 import Controller as PreviousController,Scene
from .protocol_v3 import PROTOCOL,schedule,SETTLED_HOLD


class Controller(PreviousController):
    def __init__(self,scene):
        assert scene.cfg['validation_protocol']==PROTOCOL
        assert scene.cfg['ready_schedule']==schedule(scene.cfg['ready_case'])
        assert scene.cfg['seconds']==scene.cfg['ready_schedule']['seconds']
        assert scene.cfg['ready_settled_hold_s']==SETTLED_HOLD
        state=scene.native()
        originals=(previous_runtime.PROTOCOL,previous_runtime.schedule)
        try:
            with patch.object(previous_runtime,'PROTOCOL',PROTOCOL),patch.object(previous_runtime,'schedule',schedule):
                super().__init__(scene)
                assert scene.play_logic.plan==schedule(scene.cfg['ready_case'])
        finally:
            assert previous_runtime.PROTOCOL is originals[0] and previous_runtime.schedule is originals[1]
            assert scene.native()==state
