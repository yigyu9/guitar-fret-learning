"""Reuse the frozen OM trial, selecting only a new video recording wrapper."""
from unittest.mock import patch
from . import strap_trial_recording
from .string_trial_recording_v1 import StringTrialRecording
from .run_om_body_geometry_trial_v2 import main

if __name__=='__main__':
    with patch.object(strap_trial_recording,'StrapTrialRecording',StringTrialRecording):
        main()
