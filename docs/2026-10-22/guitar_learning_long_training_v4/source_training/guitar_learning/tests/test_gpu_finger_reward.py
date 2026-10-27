"""CPU reward-order checks, independent of native physics and policy learning."""
import math
import unittest

import torch

from guitar_learning.gpu.finger_reward import FINGER_REWARD_CONTRACT, finger_tracking_reward


class FingerRewardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def inputs(n=1):
        return dict(now=torch.full((n,), 1.), onset=torch.tensor([.5]), end=torch.tensor([2.]),
                    press=torch.tensor([.4]), finger=torch.tensor([1]),
                    delta=torch.tensor([[[.01, 0., 0.]]]).expand(n, -1, -1).clone(),
                    velocity=torch.zeros(n, 1, 3), candidate=torch.zeros(n, 1, dtype=torch.bool),
                    actions=torch.zeros(n, 21))

    def test_approach_beats_equal_speed_departure_without_load(self):
        x = self.inputs(); x['velocity'][0, 0, 0] = -.04
        toward = finger_tracking_reward(**x)['rate']
        x['velocity'][0, 0, 0] = .04
        away = finger_tracking_reward(**x)['rate']
        self.assertGreater(float(toward), float(away))
        self.assertAlmostEqual(float(toward), 2*math.exp(-.5), places=6)

    def test_near_goal_deceleration_beats_overshoot(self):
        x = self.inputs(); x['delta'][0, 0, 0] = .001
        x['velocity'][0, 0, 0] = -.004
        slow = finger_tracking_reward(**x)['rate']
        x['velocity'][0, 0, 0] = -.1
        self.assertGreater(float(slow), float(finger_tracking_reward(**x)['rate']))

    def test_desired_speed_clips_vector_norm_without_rotating_direction(self):
        x = self.inputs(); x['delta'][0, 0] = torch.tensor([.03, .04, 0.])
        x['velocity'][0, 0] = torch.tensor([-.06, -.08, 0.])
        self.assertAlmostEqual(float(finger_tracking_reward(**x)['rate']), 2*math.exp(-2.5), places=6)

    def test_contact_stillness_and_zero_request_beat_motion_or_constant_thumb_request(self):
        x = self.inputs(); x['candidate'][:] = True; x['delta'].zero_()
        self.assertEqual(float(finger_tracking_reward(**x)['rate']), 4.)
        x['velocity'][0, 0, 0] = -.04
        self.assertLess(float(finger_tracking_reward(**x)['rate']), 4.)
        x['velocity'].zero_(); x['actions'][0, 0] = .05
        # One thumb request has squared normalized requested speed1;21 axes mean.
        expected = 4/(1+1/21)
        for _ in range(3):
            self.assertAlmostEqual(float(finger_tracking_reward(**x)['rate']), expected, places=6)

    def test_next_opposite_target_prefers_reversal_but_same_target_does_not(self):
        x = self.inputs(); x.update(onset=torch.tensor([0., 1.]), end=torch.tensor([1., 2.]),
            press=torch.tensor([0., .9]), finger=torch.tensor([1, 1]),
            delta=torch.tensor([[[.01, 0., 0.], [-.01, 0., 0.]]]),
            velocity=torch.zeros(1, 2, 3), candidate=torch.zeros(1, 2, dtype=torch.bool))
        x['velocity'][0, 1, 0] = .04
        reverse = finger_tracking_reward(**x)
        self.assertEqual(reverse['indices'].tolist(), [[1, -1, -1, -1]])
        x['velocity'][0, 1, 0] = -.04
        self.assertGreater(float(reverse['rate']), float(finger_tracking_reward(**x)['rate']))
        x['delta'][0, 1, 0] = .01
        same_direction = finger_tracking_reward(**x)['rate']
        x['velocity'][0, 1, 0] = .04
        self.assertGreater(float(same_direction), float(finger_tracking_reward(**x)['rate']))

    def test_current_priority_earliest_end_then_original_order_and_next_onset(self):
        x = self.inputs(); x.update(onset=torch.tensor([2., .3, .4, .4]),
            end=torch.tensor([3., 1.8, 1.5, 1.5]), press=torch.tensor([1.9, .2, .3, .3]),
            finger=torch.ones(4, dtype=torch.long), delta=torch.zeros(1, 4, 3),
            velocity=torch.zeros(1, 4, 3), candidate=torch.zeros(1, 4, dtype=torch.bool))
        self.assertEqual(finger_tracking_reward(**x)['indices'].tolist(), [[2, -1, -1, -1]])
        x['now'][:] = .1
        self.assertEqual(finger_tracking_reward(**x)['indices'].tolist(), [[1, -1, -1, -1]])

    def test_window_start_end_absence_and_song_finger_denominator(self):
        x = self.inputs(); x.update(onset=torch.tensor([3., 8.]), end=torch.tensor([4., 9.]),
            press=torch.tensor([2.5, 7.5]), finger=torch.tensor([1, 3]),
            delta=torch.zeros(1, 2, 3), velocity=torch.zeros(1, 2, 3),
            candidate=torch.zeros(1, 2, dtype=torch.bool))
        x['now'][:] = .5
        self.assertEqual(float(finger_tracking_reward(**x)['rate']), 1.)  #2/s divided by2 present fingers.
        x['now'][:] = .49
        self.assertEqual(float(finger_tracking_reward(**x)['rate']), 0.)
        x['now'][:] = 4.
        self.assertFalse(bool(finger_tracking_reward(**x)['valid'].any()))
        self.assertEqual(float(finger_tracking_reward(**x)['rate']), 0.)

    def test_batch_rows_and_rate_bounds_inputs_unchanged(self):
        x = self.inputs(n=3); x['candidate'][1] = True; x['now'][2] = 3.
        saved = {k:v.clone() for k, v in x.items()}
        result = finger_tracking_reward(**x)
        self.assertEqual(result['valid'][:, 0].tolist(), [True, True, False])
        self.assertEqual(float(result['rate'][2]), 0.)
        self.assertTrue(bool(((result['rate'] >= 0) & (result['rate'] <= 4)).all()))
        for k in saved:
            torch.testing.assert_close(x[k], saved[k], rtol=0, atol=0)

    def test_empty_song_returns_zero_without_nan_or_fake_selection(self):
        x = self.inputs(n=2)
        for k in ('onset', 'end', 'press', 'finger'):
            x[k] = x[k][:0]
        for k in ('delta', 'velocity', 'candidate'):
            x[k] = x[k][:, :0]
        result = finger_tracking_reward(**x)
        self.assertEqual(result['rate'].tolist(), [0., 0.])
        self.assertEqual(result['indices'].tolist(), [[-1]*4]*2)
        self.assertEqual(FINGER_REWARD_CONTRACT['rate_bounds_per_s'], [0., 4.])

    def test_all_present_fingers_share_maximum_rate_and_bad_action_shape_rejected(self):
        x = self.inputs(n=2)
        for k in ('onset', 'end', 'press'):
            x[k] = x[k].expand(4)
        x.update(finger=torch.arange(1, 5), delta=torch.zeros(2, 4, 3),
                 velocity=torch.zeros(2, 4, 3), candidate=torch.ones(2, 4, dtype=torch.bool))
        self.assertEqual(finger_tracking_reward(**x)['rate'].tolist(), [4., 4.])
        x['actions'] = torch.zeros(2, 20)
        with self.assertRaises(ValueError):
            finger_tracking_reward(**x)


if __name__ == '__main__':
    unittest.main()
