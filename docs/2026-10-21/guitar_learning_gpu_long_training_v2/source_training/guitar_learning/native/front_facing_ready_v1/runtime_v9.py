"""Scene8 alias; Controller6 생성자에서만 Motion2 binding, effort/targets 불변."""
from unittest.mock import patch
from . import runtime_v1 as legacy_runtime
from .runtime_v8 import Scene
from .runtime_v6 import Controller as PreviousController
from .motion_v2 import Motion,HAND_MODE,THUMB_DELTA,HAND_RAMP


class Controller(PreviousController):
    def __init__(self,scene):
        assert scene.cfg['ready_hand_maintenance_mode']==HAND_MODE
        assert scene.cfg['ready_hand_maintenance_thumb_delta_rad']==THUMB_DELTA
        assert scene.cfg['ready_hand_maintenance_ramp_s']==HAND_RAMP
        state=scene.native();original=legacy_runtime.Motion
        try:
            with patch.object(legacy_runtime,'Motion',Motion):
                super().__init__(scene)
                assert isinstance(scene.play_logic,Motion)
        finally:
            assert legacy_runtime.Motion is original
            assert scene.native()==state
