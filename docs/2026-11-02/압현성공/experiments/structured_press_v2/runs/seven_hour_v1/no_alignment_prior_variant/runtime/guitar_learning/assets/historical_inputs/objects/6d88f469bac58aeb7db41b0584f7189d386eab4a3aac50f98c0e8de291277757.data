"""COLOR-only native camera capture, without depth/goal callbacks."""
from .gym_trial_recording import GymTrialRecording
from .live_fret_recording_v2 import NativePixelRecording


class FretRawRecording(NativePixelRecording):
    def __init__(self, env, out):
        super().__init__(GymTrialRecording(env, out))
