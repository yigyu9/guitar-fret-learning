from types import SimpleNamespace
import unittest

from guitar_learning.tool.experiments.transition.teacher import Controller


def plan():
    return dict(candidates=[dict(name=name, action39=[value]*33 + [0.]*6)
        for name, value in [('single_a', .2), ('overlap', .4), ('single_b', -.2), ('release', -.4)]])


def task():
    return SimpleNamespace(targets=[SimpleNamespace(press_s=0., onset_s=2., end_s=3.),
        SimpleNamespace(press_s=2.5, onset_s=3., end_s=3.5)], duration_s=4.)


class TeacherTests(unittest.TestCase):
    def test_consecutive_smooth_commands_and_no_reset(self):
        controller = Controller(plan(), task())
        values = [controller.action(tick/60.) for tick in range(240)]
        self.assertEqual(values[0], [0.]*39)
        self.assertEqual(values[84], [.2]*33+[0.]*6)
        self.assertEqual(values[120], [.4]*33+[0.]*6)
        self.assertEqual(values[180], [.4]*33+[0.]*6)
        self.assertTrue(all(len(a) == 39 and all(abs(v) <= 1 for v in a) and a[33:] == [0.]*6 for a in values))
        self.assertTrue(all(abs(values[i][0]-values[i-1][0]) < .2 for i in range(1, len(values))))
        self.assertFalse(controller.diagnostic['live_guitar_tracking'])
        with self.assertRaises(ValueError):
            controller.action(0.)

    def test_invalid_time_skip_and_right_hand_rejected(self):
        controller = Controller(plan(), task())
        with self.assertRaises(ValueError):
            controller.action(.1)
        controller.action(0.)
        with self.assertRaises(ValueError):
            controller.action(2/60.)
        bad = plan()
        bad['candidates'][0]['action39'][-1] = .1
        with self.assertRaises(ValueError):
            Controller(bad, task())

    def test_single_b_uses_selected_single_goal_and_release(self):
        one = SimpleNamespace(targets=[SimpleNamespace(press_s=0., onset_s=2., end_s=2.5)], duration_s=4.)
        controller = Controller(plan(), one)
        values = [controller.action(tick/60.) for tick in range(241)]
        self.assertEqual(values[120], [.2]*33+[0.]*6)
        self.assertEqual(values[240], [-.4]*33+[0.]*6)


if __name__ == '__main__':
    unittest.main()
