"""CPU verification for the predeclared live diagnostic; creates no scene."""
import unittest

import torch

from probe import protocol, release_mask, replace_selected, RELEASE_S
from guitar_learning.gpu.control import BatchedController
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.tool.validation.press_acquisition import trajectory_actions


class LiveReleaseCPUChecks(unittest.TestCase):
    def test_fixed_first_attempt_assignment_and_exact_endpoint_schedule(self):
        p = protocol()
        self.assertEqual(len(p['assignments']), 128)
        self.assertEqual([sum(a['condition'] == c for a in p['assignments']) for c in range(16)], [8]*16)
        expected = [None, 174, 176, 177, 178, 179, 180, 182, 183, 184, 185, 188, 189, 190, 191, 194]
        found = [None]*128
        previous = torch.zeros(128, dtype=torch.bool)
        for tick in range(1, 219):
            mask = release_mask(torch.full((128,), 4*(tick-1), dtype=torch.long), torch=torch)
            self.assertFalse(bool((previous & ~mask).any()))
            for i in (mask & ~previous).nonzero().flatten().tolist():
                found[i] = tick
            previous = mask
        self.assertEqual(found, expected*8)
        self.assertEqual(RELEASE_S[0], None)

    def test_partial_reset_clocks_do_not_shift_fixed_environment_assignment(self):
        clock = torch.full((128,), 760, dtype=torch.long)
        clock[17] = 0
        mask = release_mask(clock, torch=torch)
        self.assertTrue(bool(mask[1]))
        self.assertFalse(bool(mask[17]))
        self.assertFalse(bool(mask[0]))

    def test_only_four_actions_replaced_and_native_rate_and_state_preserved(self):
        scene, snapshot = fake_scene(num_envs=128)
        controller = BatchedController(scene, finger_action_mode='incremental')
        selected = [21, 22, 23, 24]
        native = controller.active[selected]
        reference = controller.reference[controller.active]
        incremental = torch.zeros(39, dtype=torch.bool)
        incremental[controller.incremental_actions] = True
        # First move away using actual unchanged controller; then invert back to035.
        initial = torch.zeros(128, 39, dtype=scene.q.dtype)
        initial[:, selected] = .9
        for _ in range(5):
            controller.targets(initial, snapshot)
        old = controller.target[:, controller.active].clone()
        untouched_state = {key: value.clone() for key, value in snapshot.items()}
        retract = trajectory_actions(reference.expand(128, -1), old, reference,
            controller.action_low, controller.action_high, incremental, max_speed=4.)
        mask = release_mask(torch.full((128,), 760, dtype=torch.long), torch=torch)
        action = torch.linspace(-.9, .9, 128*39, dtype=scene.q.dtype).reshape(128, 39)
        result = replace_selected(action, retract, mask, selected, torch=torch)
        other = [i for i in range(39) if i not in selected]
        self.assertTrue(torch.equal(result[:, other], action[:, other]))
        self.assertTrue(torch.equal(result[~mask], action[~mask]))
        self.assertTrue(torch.equal(result[mask][:, selected], retract[mask][:, selected]))
        target = controller.targets(result, snapshot)
        delta = target[:, native]-old[:, selected]
        self.assertLessEqual(float(delta.abs().max()), 4/60+1e-12)
        expected = old[:, selected]+result[:, selected]*4/60
        expected = expected.clamp(controller.action_low[selected], controller.action_high[selected])
        torch.testing.assert_close(target[:, native], expected, rtol=0, atol=1e-12)
        self.assertTrue(bool((target[:, native] >= controller.action_low[selected]).all()))
        self.assertTrue(bool((target[:, native] <= controller.action_high[selected]).all()))
        for key, value in snapshot.items():
            self.assertTrue(torch.equal(value, untouched_state[key]), key)


if __name__ == '__main__':
    unittest.main(verbosity=2)
