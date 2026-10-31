"""Left-away native test with wrist tracking disabled from physics step zero."""
from unittest.mock import patch


def main():
    import isaacgym  # Initialize Gym bindings before the reused Torch scene imports.
    from . import run_right_body_approach_v1 as runner
    from . import right_block_body_effort_v5 as support
    from . import left_near_scene_v3 as scene_module
    from . import left_near_arm_effort_v3 as legacy_tracking
    from .left_wrist_tracking_off_v2 import EffortRecording as TrackingOff
    from .native_contacts import body_names, read_contacts
    from .run_joint_hold import native_state

    class ChestRecording(support.EffortRecording):
        def __init__(self, env, out):
            super().__init__(env, out)
            mapping = body_names(env.gym, env.env)
            previous = env.after_physics

            def observe(owner):
                previous(owner)
                state = native_state(owner)
                contacts = read_contacts(owner.gym, owner.env, mapping)
                self.endpoint_rows[-1]['chest_guitar_contacts'] = [
                    c for c in contacts if 'human/Chest' in (c['body0_name'], c['body1_name'])
                    and any(n.startswith('guitar/') for n in (c['body0_name'], c['body1_name']))]
                self.endpoint_rows[-1]['trunk_guitar_contacts'] = [
                    c for c in contacts if any(n in ('human/Torso', 'human/Spine', 'human/Chest')
                                              for n in (c['body0_name'], c['body1_name']))
                    and any(n.startswith('guitar/') for n in (c['body0_name'], c['body1_name']))]
                assert native_state(owner) == state

            env.after_physics = observe

    with patch.object(scene_module.support, 'factory', support.factory), \
         patch.object(scene_module.support, 'ArmEffortGuard', support.ArmEffortGuard), \
         patch.object(support.LearningScene, '_create_scene', support.create_effort), \
         patch.object(support.base.string_trial_recording_v1, 'StrapTrialRecording', support.base.GymTrialRecording), \
         patch.object(support, 'EffortRecording', ChestRecording), \
         patch.object(legacy_tracking.EffortRecording, '__init__', TrackingOff.__init__):
        runner.main()


if __name__ == '__main__':
    main()
