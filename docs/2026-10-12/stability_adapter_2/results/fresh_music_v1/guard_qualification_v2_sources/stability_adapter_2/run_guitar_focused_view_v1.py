"""Use a tighter native camera, preserving the existing six-string trial physics."""
from unittest.mock import patch
from . import strap_trial_recording
from .string_trial_recording_v1 import StringTrialRecording
from .run_om_body_geometry_trial_v2 import main

class FocusedRecording(StringTrialRecording):
    def capture(self):
        if not self.frames:
            from .environment import gymapi
            from .run_joint_hold import native_state
            from .initial_pose_noise_v1 import pose
            env=self.env;state=native_state(env);p,r=pose(state['guitar_body_states'][0])
            target=p+r.apply([0,-.145,-.02]);eye=target+r.apply([.08,0,.66])
            env.gym.set_camera_location(env.cameras['OM_appearance'],env.env,gymapi.Vec3(*eye),gymapi.Vec3(*target))
            assert native_state(env)==state
        super().capture()

if __name__=='__main__':
    with patch.object(strap_trial_recording,'StrapTrialRecording',FocusedRecording):
        main()
