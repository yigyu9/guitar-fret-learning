"""오른손21축의 직접 명령·속도 제한·행별 초기화와 기존 팔 제어 보존을 검사한다."""
import unittest
import torch
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.gpu.control import BatchedController
from guitar_learning.tool.experiments.right27.control import Right27Controller


class Right27ControlTests(unittest.TestCase):
    def test_right_fingers_direct_limits_and_unchanged_other_targets(self):
        scene, snapshot = fake_scene(hand='right')
        controller = Right27Controller(scene)
        baseline = BatchedController(scene)
        action = torch.zeros(2, 39, dtype=scene.q.dtype)
        action[:, 12:33] = 1
        action[:, 33:] = .2
        original = action.clone()
        original[:, :33] = 0
        other = torch.ones(105, dtype=torch.bool)
        other[controller.finger_indices] = False
        for _ in range(60):
            previous = controller.target.clone()
            actual = controller.targets(action, snapshot)
            expected = baseline.targets(original, snapshot)
            self.assertTrue(torch.equal(actual[:, other], expected[:, other]))
            self.assertLessEqual(float((actual[:, controller.finger_indices]-
                previous[:, controller.finger_indices]).abs().max()), 4/60+1e-10)
        self.assertTrue(torch.allclose(actual[:, controller.finger_indices],
            controller.upper[controller.finger_indices].expand(2, -1)))
        # 행동0은 누적 정지가 아니라 준비 기준각의 요청이다.
        for _ in range(60):
            controller.targets(torch.zeros_like(action), snapshot)
        self.assertTrue(torch.allclose(controller.target[:, controller.finger_indices],
            controller.reference[controller.finger_indices].expand(2, -1)))

    def test_reset_is_per_environment_and_inert_actions_rejected(self):
        scene, snapshot = fake_scene(hand='right')
        controller = Right27Controller(scene)
        action = torch.zeros(2, 39, dtype=scene.q.dtype)
        action[:, 12:33] = .3
        controller.targets(action, snapshot)
        previous = controller.target.clone()
        controller.reset(torch.tensor([0]), snapshot)
        self.assertTrue(torch.equal(controller.target[1], previous[1]))
        self.assertTrue(torch.equal(controller.target[0], controller.reference))
        action[:, 0] = .1
        with self.assertRaises(ValueError):
            controller.targets(action, snapshot)


if __name__ == '__main__':
    unittest.main()
