"""Scene8 alias; constructor-only Motion3 binding atop Controller9."""
from unittest.mock import patch
from . import runtime_v9 as previous_runtime
from .runtime_v9 import Controller as PreviousController
from .runtime_v8 import Scene
from .motion_v3 import Motion,BIAS_BOUNDS_MODE


class Controller(PreviousController):
    def __init__(self,scene):
        assert scene.cfg['ready_hand_bias_bounds_mode']==BIAS_BOUNDS_MODE
        state=scene.native();original=previous_runtime.Motion
        try:
            with patch.object(previous_runtime,'Motion',Motion):
                super().__init__(scene)
                assert isinstance(scene.play_logic,Motion)
        finally:
            assert previous_runtime.Motion is original
            assert scene.native()==state
