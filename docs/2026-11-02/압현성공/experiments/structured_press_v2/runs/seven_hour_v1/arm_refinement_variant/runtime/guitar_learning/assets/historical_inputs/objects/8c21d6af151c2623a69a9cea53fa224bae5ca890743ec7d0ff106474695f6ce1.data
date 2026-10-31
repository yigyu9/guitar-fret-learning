"""Readiness profile regression without creating a native scene."""
import unittest
from . import deadline_native_v5 as guarded
from .deadline_native_v7 import NativeDeadlineEnvironment, PROFILE


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.env = NativeDeadlineEnvironment.__new__(NativeDeadlineEnvironment)
        self.env._ready = True
        self.env._finished = False
        self.env.metadata = {'profile': PROFILE}

    def test_current_profile_ready_and_patch_restored(self):
        original = guarded.PROFILE
        self.env.require_training_ready()
        self.assertIs(guarded.PROFILE, original)

    def test_finished_unready_wrong_profile_rejected(self):
        for attribute in ('_finished', '_ready', 'metadata'):
            old = getattr(self.env, attribute)
            setattr(self.env, attribute, {'profile': {'name': 'wrong'}} if attribute == 'metadata'
                    else attribute == '_finished')
            with self.assertRaises(RuntimeError): self.env.require_training_ready()
            setattr(self.env, attribute, old)


if __name__ == '__main__': unittest.main()
