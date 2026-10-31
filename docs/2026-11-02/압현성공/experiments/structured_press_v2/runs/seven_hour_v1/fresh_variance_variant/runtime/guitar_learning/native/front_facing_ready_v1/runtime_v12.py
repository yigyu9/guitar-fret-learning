"""Protocol4 constructor binding, including both nested settled-hold checks."""
from unittest.mock import patch
from . import runtime_v6 as protocol_runtime,runtime_v5 as hold_runtime
from .runtime_v10 import Controller as PreviousController,Scene
from .protocol_v4 import PROTOCOL,schedule,SETTLED_HOLD


class Controller(PreviousController):
    def __init__(self,scene):
        assert scene.cfg['validation_protocol']==PROTOCOL
        assert scene.cfg['ready_schedule']==schedule(scene.cfg['ready_case'])
        assert scene.cfg['seconds']==scene.cfg['ready_schedule']['seconds']
        assert scene.cfg['ready_settled_hold_s']==SETTLED_HOLD
        state=scene.native()
        original=(protocol_runtime.PROTOCOL,protocol_runtime.schedule,protocol_runtime.SETTLED_HOLD,hold_runtime.SETTLED_HOLD)
        try:
            with patch.object(protocol_runtime,'PROTOCOL',PROTOCOL),patch.object(protocol_runtime,'schedule',schedule),patch.object(protocol_runtime,'SETTLED_HOLD',SETTLED_HOLD),patch.object(hold_runtime,'SETTLED_HOLD',SETTLED_HOLD):
                super().__init__(scene)
                assert scene.play_logic.plan==schedule(scene.cfg['ready_case'])
        finally:
            assert protocol_runtime.PROTOCOL is original[0] and protocol_runtime.schedule is original[1]
            assert protocol_runtime.SETTLED_HOLD is original[2] and hold_runtime.SETTLED_HOLD is original[3] and scene.native()==state
