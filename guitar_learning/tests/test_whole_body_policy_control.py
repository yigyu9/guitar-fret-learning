"""전신37 잔차의 소유권·비누적·속도 제한을 GPU 없이 검사한다."""
from types import SimpleNamespace
import unittest

import torch

from guitar_learning.core.control import LEFT_ARM_NAMES, LEFT_HAND_NAMES, RIGHT_GRIP_NAMES, RIGHT_STRIKE_NAMES
from guitar_learning.gpu.whole_body_control import ACTION_NAMES, ZERO_NAMES, WholeBodyController


class FakeBaseline:
    """실제 발 IK처럼 이전 목표를 읽는 작은 제어기 대역."""

    def __init__(self):
        # native 순서를 정책 순서와 다르게 두어 이름 기반 배치를 검사한다.
        self.names = tuple(reversed(LEFT_ARM_NAMES + LEFT_HAND_NAMES + RIGHT_GRIP_NAMES +
                                    RIGHT_STRIKE_NAMES + ACTION_NAMES + ZERO_NAMES))
        self.device, self.dtype, self.num_envs = torch.device('cpu'), torch.float64, 2
        self.reference = torch.zeros(105, dtype=self.dtype)
        self.target = self.reference.expand(2, -1).clone()
        self.lower, self.upper = -torch.ones(105, dtype=self.dtype), torch.ones(105, dtype=self.dtype)
        self.zero = self.index([self.names.index(name) for name in ZERO_NAMES])
        self.lower[self.zero] = self.upper[self.zero] = 0.
        self.rate = torch.full((105,), 60., dtype=self.dtype)
        self.contract = dict(schema='test_baseline', physical_parameters='unchanged')
        self.foot = self.names.index('L_Ankle_x')
        self.nonowned = self.names.index(LEFT_HAND_NAMES[0])
        self.inputs = []
        self.effort_snapshot = None

    def index(self, value):
        return torch.as_tensor(value, device=self.device, dtype=torch.long)

    def targets(self, action, snapshot):
        self.inputs.append(action.clone())
        # 발의 기준 목표가 이전 값에 의존하는 상황을 재현한다.
        previous_foot = self.target[:, self.foot].clone()
        self.target.zero_()
        self.target[:, self.foot] = .5*previous_foot + .01
        self.target[:, self.nonowned] = .03
        return self.target

    def reset(self, indices, snapshot):
        self.target[indices] = self.reference

    def efforts(self, snapshot):
        self.effort_snapshot = snapshot
        return 2*self.target


class WholeBodyPolicyControlTests(unittest.TestCase):
    def make_controller(self):
        base = FakeBaseline()
        return WholeBodyController(SimpleNamespace(hand='left'), base=base), base

    def test_all37_affect_only_owned_axes_and_keep_aliases(self):
        controller, base = self.make_controller()
        alias = base.target
        action = torch.linspace(-1, 1, 37, dtype=base.dtype).expand(2, -1).clone()
        action[:, 18] = .25
        target = controller.targets(action, {})
        self.assertIs(target, alias)
        torch.testing.assert_close(target[:, controller.active],
                                   controller.baseline_target[:, controller.active] + .1*action)
        other = torch.ones(105, dtype=torch.bool)
        other[controller.active] = False
        self.assertTrue(torch.equal(target[:, other], controller.baseline_target[:, other]))
        self.assertTrue((target[:, base.zero] == 0).all())
        self.assertTrue((base.inputs[0] == 0).all())
        self.assertEqual(base.inputs[0].shape, (2, 39))
        self.assertEqual(controller.contract['action_dim'], 37)
        self.assertEqual(controller.contract['baseline_control'], base.contract)

    def test_constant_residual_does_not_accumulate_in_foot_baseline(self):
        controller, base = self.make_controller()
        independent = FakeBaseline()
        action = torch.ones(2, 37, dtype=base.dtype)
        for _ in range(25):
            expected = independent.targets(torch.zeros(2, 39, dtype=base.dtype), {}).clone()
            actual = controller.targets(action, {})
            torch.testing.assert_close(controller.baseline_target, expected)
            torch.testing.assert_close(actual[:, controller.active], expected[:, controller.active] + .1)
        self.assertLess(float(actual[:, base.foot].max()), .12000001)

    def test_rate_limit_native_clamp_and_zero_action_return(self):
        controller, base = self.make_controller()
        index = controller.active[0]
        base.rate[index] = .6
        base.upper[index] = .035
        action = torch.ones(2, 37, dtype=base.dtype)
        for tick in range(6):
            previous = base.target.clone()
            actual = controller.targets(action, {})
            self.assertLessEqual(float((actual[:, index]-previous[:, index]).abs().max()), .010000001)
            self.assertLessEqual(float(actual[:, index].max()), .035)
        self.assertAlmostEqual(float(actual[0, index]), .035)
        for _ in range(6):
            actual = controller.targets(torch.zeros_like(action), {})
        torch.testing.assert_close(actual, controller.baseline_target)

    def test_reset_only_selected_rows_in_both_memories_and_effort_passthrough(self):
        controller, base = self.make_controller()
        controller.targets(torch.full((2, 37), .5, dtype=base.dtype), {})
        old_target, old_baseline = base.target.clone(), controller.baseline_target.clone()
        controller.reset([0], {})
        self.assertTrue(torch.equal(base.target[0], base.reference))
        self.assertTrue(torch.equal(controller.baseline_target[0], base.reference))
        self.assertTrue(torch.equal(base.target[1], old_target[1]))
        self.assertTrue(torch.equal(controller.baseline_target[1], old_baseline[1]))
        snapshot = {'tag': 'same snapshot'}
        effort = controller.efforts(snapshot)
        self.assertIs(base.effort_snapshot, snapshot)
        torch.testing.assert_close(effort, 2*base.target)

    def test_invalid_actions_and_partitions_rejected_before_target_change(self):
        controller, base = self.make_controller()
        before = base.target.clone()
        for action in (torch.zeros(2, 39), torch.ones(2, 37)*1.001,
                       torch.full((2, 37), float('nan')), torch.ones(2, 37, dtype=torch.long)):
            with self.assertRaises(ValueError):
                controller.targets(action, {})
            self.assertTrue(torch.equal(base.target, before))
        base.names = ('not_a_native_joint',) + base.names[1:]
        with self.assertRaises(ValueError):
            WholeBodyController(SimpleNamespace(hand='left'), base=base)
        base = FakeBaseline()
        base.upper[base.names.index('L_Knee_y')] = .1
        with self.assertRaises(ValueError):
            WholeBodyController(SimpleNamespace(hand='left'), base=base)

    def test_native_baseline_parity_and_unchanged_physical_parameters(self):
        from guitar_learning.gpu.control import BatchedController
        from guitar_learning.tests.test_gpu_control import fake_scene
        scene, snapshot = fake_scene()
        controller = WholeBodyController(scene)
        baseline = BatchedController(scene)
        saved = {name: getattr(controller, name).clone()
                 for name in ('kp', 'kd', 'caps', 'rate', 'lower', 'upper')}
        original_state = {name: value.clone() for name, value in snapshot.items()}
        action = torch.zeros(2, 37, dtype=scene.q.dtype)
        for _ in range(3):
            target = controller.targets(action, snapshot)
            expected = baseline.targets(torch.zeros(2, 39, dtype=scene.q.dtype), snapshot)
            torch.testing.assert_close(target, expected, rtol=0, atol=0)
            torch.testing.assert_close(controller.efforts(snapshot), baseline.efforts(snapshot),
                                       rtol=0, atol=0)
        controller.targets(torch.full_like(action, .5), snapshot)
        effort = controller.efforts(snapshot)
        self.assertTrue(torch.isfinite(effort).all())
        self.assertTrue((effort.abs() <= controller.caps).all())
        self.assertTrue((effort[:, controller.position] == 0).all())
        self.assertTrue((effort[:, controller.zero] == 0).all())
        for name, value in saved.items():
            self.assertTrue(torch.equal(getattr(controller, name), value), name)
        for name, value in original_state.items():
            self.assertTrue(torch.equal(snapshot[name], value), name)


if __name__ == '__main__':
    unittest.main()
