"""CPU reward-order checks, independent of native physics and policy learning."""
import math
import unittest

import torch

from guitar_learning.gpu.finger_reward import (FINGER_REWARD_CONTRACT,
    FINGER_COORDINATION_CONTRACT, finger_tracking_reward, finger_posture_reward,
    source_finger_frame_contract, _verify_source_frames)
from guitar_learning.gpu.geometry import multiply


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

    def test_contact_stillness_and_zero_request_beat_motion_or_own_request(self):
        x = self.inputs(); x['candidate'][:] = True; x['delta'].zero_()
        self.assertEqual(float(finger_tracking_reward(**x)['rate']), 4.)
        x['velocity'][0, 0, 0] = -.04
        self.assertLess(float(finger_tracking_reward(**x)['rate']), 4.)
        x['velocity'].zero_(); x['actions'][0, 5] = .05
        # One own-finger request retains its original1/21 coefficient.
        expected = 4/(1+1/21)
        for _ in range(3):
            self.assertAlmostEqual(float(finger_tracking_reward(**x)['rate']), expected, places=6)

    def test_thumb_and_other_finger_requests_do_not_change_selected_quality(self):
        x = self.inputs(); before = finger_tracking_reward(**x)
        x['actions'][:, :5] = 1.
        x['actions'][:, 9:] = -.7
        after = finger_tracking_reward(**x)
        torch.testing.assert_close(before['quality'], after['quality'], rtol=0, atol=0)
        self.assertEqual(FINGER_REWARD_CONTRACT['schema'], 'guitar_learning.gpu_finger_tracking_rate.v2')

    def test_each_finger_own_four_axes_keep_sum_over21_not_mean_over4(self):
        x = self.inputs(n=4)
        for k in ('onset', 'end', 'press'):
            x[k] = x[k].expand(4)
        x.update(finger=torch.arange(1, 5), delta=torch.zeros(4, 4, 3),
                 velocity=torch.zeros(4, 4, 3), candidate=torch.ones(4, 4, dtype=torch.bool))
        for row in range(4):
            x['actions'][row, 5+4*row:9+4*row] = torch.tensor([.05, -.1, .15, -.2])
        result = finger_tracking_reward(**x)
        expected = 2/(1+(1+4+9+16)/21)
        for row in range(4):
            for finger in range(4):
                self.assertAlmostEqual(float(result['quality'][row, finger]), expected if row == finger else 2., places=6)

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


class FingerPostureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def rotation(axis, angle):
        q = torch.zeros((*angle.shape, 4), dtype=angle.dtype)
        q[..., axis] = torch.sin(angle/2)
        q[..., 3] = torch.cos(angle/2)
        return q

    def inputs(self, degrees=(30., 40., 20.), times=(1.,)):
        n = len(times)
        angle = torch.tensor(degrees, dtype=torch.float64)*math.pi/180
        relative = self.rotation(0, angle).expand(n, 4, 3, 4).clone()
        segment = relative.clone()
        segment[:, :, 1] = multiply(segment[:, :, 0], relative[:, :, 1])
        segment[:, :, 2] = multiply(segment[:, :, 1], relative[:, :, 2])
        return dict(now=torch.tensor(times, dtype=torch.float64), onset=torch.empty(0, dtype=torch.float64),
                    end=torch.empty(0, dtype=torch.float64), press=torch.empty(0, dtype=torch.float64),
                    finger=torch.empty(0, dtype=torch.long),
                    palm_quaternion=torch.tensor([0., 0., 0., 1.], dtype=torch.float64).expand(n, -1).clone(),
                    segment_quaternion=segment)

    def test_signed_actual_angles_and_source_axis_sign(self):
        x = self.inputs((-25., 0., 75.))
        result = finger_posture_reward(**x)
        expected = torch.tensor([-25., 0., 75.], dtype=torch.float64)*math.pi/180
        torch.testing.assert_close(result['angles'], expected.expand(1, 4, 3), rtol=0, atol=1e-14)
        self.assertTrue(result['valid'].all())
        self.assertLess(float(result['coordination_rate']), .05)

    def test_full_extra_y_rotation_changes_actual_bend_not_only_xz(self):
        x = self.inputs((45., 0., 0.))
        original = finger_posture_reward(**x)['angles'].clone()
        # Ry*Rx: projecting the actual forward vector gives atan2(sin45*cos60,cos45).
        y = self.rotation(1, torch.full((1, 4), math.pi/3, dtype=torch.float64))
        x['segment_quaternion'] = multiply(y[:, :, None], x['segment_quaternion'])
        result = finger_posture_reward(**x)
        expected = math.atan2(math.sin(math.pi/4)*math.cos(math.pi/3), math.cos(math.pi/4))
        self.assertAlmostEqual(float(result['angles'][0, 0, 0]), expected, places=13)
        self.assertFalse(torch.allclose(original, result['angles']))
        torch.testing.assert_close(result['angles'][..., 1:], torch.zeros(1, 4, 2, dtype=torch.float64), atol=1e-14, rtol=0)

    def test_common_world_rotation_and_quaternion_sign_preserve_reward(self):
        x = self.inputs(times=(1., 2.)); before = finger_posture_reward(**x)
        turn = self.rotation(2, torch.tensor([.7, -1.2], dtype=torch.float64))
        x['palm_quaternion'] = multiply(turn, x['palm_quaternion'])
        x['segment_quaternion'] = -multiply(turn[:, None, None], x['segment_quaternion'])
        after = finger_posture_reward(**x)
        for key in before:
            torch.testing.assert_close(before[key], after[key], rtol=0, atol=1e-14)

    def test_projection_degeneracy_and_zero_quaternion_zero_whole_finger_credit(self):
        x = self.inputs()
        sideways = self.rotation(2, torch.tensor(math.pi/2, dtype=torch.float64))
        x['segment_quaternion'][:, 0, 0] = sideways
        x['segment_quaternion'][:, 1, 2] = 0.
        result = finger_posture_reward(**x)
        self.assertFalse(result['valid'][0, 0, 0])
        self.assertFalse(result['valid'][0, 1, 2])
        for key in ('coordination_quality', 'standby_quality'):
            self.assertEqual(result[key][0, :2].tolist(), [0., 0.])
        for value in result.values():
            self.assertTrue(torch.isfinite(value).all())

    def test_coordination_formula_corner_and_broad_standby_region(self):
        balanced = finger_posture_reward(**self.inputs())
        other = finger_posture_reward(**self.inputs((60., 80., 40.)))
        self.assertAlmostEqual(float(balanced['coordination_rate']), .05, places=14)
        self.assertAlmostEqual(float(balanced['standby_rate']), .05, places=14)
        self.assertAlmostEqual(float(other['standby_rate']), .05, places=14)
        bad = finger_posture_reward(**self.inputs((-40., 0., 90.)))
        # Violations70/70/20 degrees; standby distances25/15/45 degrees.
        self.assertAlmostEqual(float(bad['coordination_rate']), .05*math.exp(-(70**2+70**2+20**2)/30**2), places=14)
        self.assertAlmostEqual(float(bad['standby_rate']), .05*math.exp(-(25**2+15**2+45**2)/30**2), places=14)

    def test_soft_terms_continuous_and_full_extension_is_not_forbidden(self):
        left = finger_posture_reward(**self.inputs((0., 0., 20.-1e-5)))
        right = finger_posture_reward(**self.inputs((0., 0., 20.+1e-5)))
        self.assertLess(abs(float(left['coordination_rate']-right['coordination_rate'])), 1e-12)
        x = self.inputs((-40., 0., -5.)); saved = {k:v.clone() for k, v in x.items()}
        result = finger_posture_reward(**x)
        self.assertGreater(float(result['standby_rate']), 0.)
        self.assertAlmostEqual(float(result['coordination_rate']), .05, places=14)
        for key in saved:
            torch.testing.assert_close(x[key], saved[key], rtol=0, atol=0)

    def test_idle_fades_overlap_absent_fingers_and_empty_score(self):
        x = self.inputs(times=(.74, .75, .875, 1., 4., 4.125, 4.25, 4.26))
        x.update(onset=torch.tensor([3.5], dtype=torch.float64), end=torch.tensor([4.], dtype=torch.float64),
                 press=torch.tensor([3.], dtype=torch.float64), finger=torch.tensor([1]))
        result = finger_posture_reward(**x)
        expected = torch.tensor([1., 1., .5, 0., 0., .5, 1., 1.], dtype=torch.float64)
        torch.testing.assert_close(result['idle_weight'][:, 0], expected, rtol=0, atol=1e-14)
        self.assertTrue((result['idle_weight'][:, 1:] == 1).all())
        x = self.inputs(times=(4.125,))
        x.update(onset=torch.tensor([3.5, 6.], dtype=torch.float64), end=torch.tensor([4., 6.5], dtype=torch.float64),
                 press=torch.tensor([3., 6.], dtype=torch.float64), finger=torch.tensor([1, 1]))
        self.assertEqual(float(finger_posture_reward(**x)['idle_weight'][0, 0]), 0.)
        empty = finger_posture_reward(**self.inputs())
        self.assertTrue((empty['idle_weight'] == 1).all())

    def test_rates_bounds_and_inputs_unchanged_with_active_notes(self):
        x = self.inputs((110., 105., 90.), times=(0., 1., 4., 8.))
        x.update(onset=torch.tensor([1., 6.], dtype=torch.float64), end=torch.tensor([2., 7.], dtype=torch.float64),
                 press=torch.tensor([.9, 5.9], dtype=torch.float64), finger=torch.tensor([2, 4]))
        saved = {key:value.clone() for key, value in x.items()}
        result = finger_posture_reward(**x)
        for key in ('coordination_rate', 'standby_rate'):
            self.assertTrue(((result[key] >= 0) & (result[key] <= .05)).all())
        for key in saved:
            torch.testing.assert_close(x[key], saved[key], rtol=0, atol=0)
        self.assertEqual(FINGER_COORDINATION_CONTRACT['each_rate_bounds_per_s'], [0., .05])

    def test_actual_pinned_source_frames_and_reject_changed_direction_rotation_axis(self):
        import hashlib
        import xml.etree.ElementTree as ET
        from pathlib import Path
        contract = source_finger_frame_contract()
        path = Path(contract['source_xml'])
        self.assertTrue(path.is_absolute())
        self.assertEqual(contract['source_sha256'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        for tag, key, value in (("body[@name='LH:ring2']", 'pos', '0 .04 0'),
                                ("body[@name='LH:pinky1']", 'quat', '.7 .7 0 0'),
                                ("joint[@name='LH:index3']", 'axis', '0 1 0')):
            xml = ET.parse(path).getroot()
            xml.find('.//'+tag).set(key, value)
            with self.assertRaises(ValueError):
                _verify_source_frames(xml)


if __name__ == '__main__':
    unittest.main()
