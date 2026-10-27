"""Deadline gate must exclude an interrupted transition, not fabricate done."""
import unittest
from unittest.mock import patch
from .run_deadline_training_v3 import DeadlineBoundedEnvironment, TrainingDeadline


class Scene:
    def __init__(self): self.calls=[]
    def require_training_ready(self): self.calls.append('ready')
    def reset(self): self.calls.append('reset'); return 'real_observation'
    def step(self, action): self.calls.append(action); return 'real_transition'


class DeadlineTests(unittest.TestCase):
    def test_before_deadline_passes_actual_transition(self):
        scene=Scene(); gate=DeadlineBoundedEnvironment(scene, 10.)
        with patch('stability_adapter_2.run_deadline_training_v3.time.time',return_value=9.):
            self.assertEqual(gate.reset(),'real_observation')
            self.assertEqual(gate.step('action'),'real_transition')
        self.assertEqual(scene.calls,['reset','action'])

    def test_at_deadline_no_reset_or_step(self):
        scene=Scene(); gate=DeadlineBoundedEnvironment(scene, 10.)
        with patch('stability_adapter_2.run_deadline_training_v3.time.time',return_value=10.):
            with self.assertRaises(TrainingDeadline): gate.reset()
            with self.assertRaises(TrainingDeadline): gate.step('action')
        self.assertEqual(scene.calls,[])

    def test_training_ready_is_real_environment_contract(self):
        scene=Scene(); gate=DeadlineBoundedEnvironment(scene, 10.)
        gate.require_training_ready()
        self.assertEqual(scene.calls,['ready'])


if __name__=='__main__': unittest.main(verbosity=2)
