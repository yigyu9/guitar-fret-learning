"""Support-nominal v1 with readiness checked against its own profile."""
from unittest.mock import patch
from . import deadline_native_v5 as guarded
from .deadline_native_v6 import NativeDeadlineEnvironment as PreviousEnvironment, PROFILE


class NativeDeadlineEnvironment(PreviousEnvironment):
    def require_training_ready(self):
        with patch.object(guarded, 'PROFILE', PROFILE):
            return super().require_training_ready()
