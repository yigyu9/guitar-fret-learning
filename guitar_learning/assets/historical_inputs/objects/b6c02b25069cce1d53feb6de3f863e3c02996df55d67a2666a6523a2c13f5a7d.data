"""Unchanged support-nominal control with isolated graphics resource creation."""
import json
from unittest.mock import patch
from .deadline_native_v7 import NativeDeadlineEnvironment as PreviousEnvironment
from .deadline_graphics_v1 import graphics_wrapper


class NativeDeadlineEnvironment(PreviousEnvironment):
    def reset(self):
        from . import capture_isaac_gym_initial as cameras
        Wrapper = graphics_wrapper(cameras.GraphicsGym, self.recording)
        with patch.object(cameras, 'GraphicsGym', Wrapper):
            observation = super().reset()
        calls = self.scene.gym.graphics_creations
        expected = 0 if self.recording else -1
        if len(calls)!=1 or calls[0]['forwarded_graphics_device_id']!=expected or not calls[0]['sim_created']:
            raise AssertionError('unexpected graphics creation')
        if not self.recording and getattr(self.scene,'cameras',{}):
            raise AssertionError('training cameras unexpectedly created')
        record = {'mode':'recorded_evaluation' if self.recording else 'graphics_free_training',
                  'creation_calls':calls, 'render_lookup_counts':self.scene.gym.render_lookup_counts,
                  'scope':'forwarded native create_sim arguments, not an internal driver-resource measurement'}
        self.metadata['graphics_resource_policy'] = record
        if self.output:
            with (self.run_output/'graphics_context.json').open('x') as f:
                json.dump(record,f,indent=2)
        return observation
