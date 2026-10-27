import unittest

import torch
from run_native import GraphicsGym, blend, finish_encoders, target_action


class NativeBControlTests(unittest.TestCase):
    def test_hold_move_hold_is_continuous_and_bounded(self):
        self.assertEqual([blend(t) for t in (0, 1, 5, 8)], [0, 0, 1, 1])
        values = [blend(t/60.) for t in range(481)]
        self.assertTrue(all(a <= b for a, b in zip(values, values[1:])))
        # Even a two-radian joint excursion remains below the unchanged
        # production 4rad/s target rate over this four-second motion.
        self.assertLess(max(b-a for a, b in zip(values, values[1:]))*2, 4/60.)

    def test_incremental_codec_reaches_each_scheduled_target(self):
        start = torch.tensor([[.7, .4, 1.5, -.087], [1.57, -.2, .4, -.087]])
        goal = torch.tensor([[.44, -.24, .61, .21], [.59, .17, .77, .31]])
        current = start.clone()
        for tick in range(1, 481):
            desired = start+(goal-start)*blend(tick/60.)
            action = target_action(current, desired)
            self.assertLessEqual(float(action.abs().max()), 1.)
            current = current+action*4/60.
            torch.testing.assert_close(current, desired, atol=2e-7, rtol=0)
        torch.testing.assert_close(current, goal, atol=2e-7, rtol=0)
        self.assertEqual(float(target_action(goal, goal).abs().max()), 0.)
        self.assertEqual(float(target_action(torch.tensor(0.), torch.tensor(10.))), 1.)

    def test_graphics_adapter_preserves_physics_objects(self):
        class FakeGym:
            sentinel = 'delegated'

            def create_sim(self, *args):
                self.args = args
                return 'sim'
        native, params, engine = FakeGym(), object(), object()
        proxy = GraphicsGym(native)
        self.assertEqual(proxy.create_sim(0, -1, engine, params), 'sim')
        self.assertEqual(native.args[:2], (0, 0))
        self.assertIs(native.args[2], engine)
        self.assertIs(native.args[3], params)
        self.assertEqual(proxy.sentinel, 'delegated')

    def test_broken_video_pipe_does_not_skip_other_encoder_cleanup(self):
        class Process:
            def __init__(self, broken):
                self.stdin, self.broken, self.waited = self, broken, False

            def close(self):
                if self.broken:
                    raise BrokenPipeError('encoder failed')

            def wait(self):
                self.waited = True
                return 1 if self.broken else 0
        bad, good = Process(True), Process(False)
        codes, errors = finish_encoders(dict(front=bad, oblique=good))
        self.assertEqual(codes, dict(front=1, oblique=0))
        self.assertEqual(set(errors), {'front'})
        self.assertTrue(bad.waited and good.waited)


if __name__ == '__main__':
    unittest.main()
