"""CPU reward-order checks, independent of native physics and policy learning."""
import math
import unittest

import torch

from guitar_learning.gpu.finger_reward import (FINGER_TARGET_CONTRACT, finger_target_indices, FINGER_REWARD_CONTRACT,
    FINGER_COORDINATION_CONTRACT, finger_tracking_reward, finger_posture_reward,
    source_finger_frame_contract, _verify_source_frames)
from guitar_learning.gpu.control import multiply


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

    def test_distance_and_candidate_effect_remain_analytic(self):
        x = self.inputs(n=4)
        x['delta'][:, 0] = torch.tensor([[0., 0., 0.], [.001, 0., 0.], [.03, .04, 0.], [.1, 0., 0.]])
        before = finger_tracking_reward(**x)['rate']
        expected = 2/(1+torch.tensor([0., .001, .05, .1])/.04).square()
        torch.testing.assert_close(before, expected, rtol=1e-6, atol=0)
        self.assertTrue((before[:-1] > before[1:]).all())
        x['candidate'].fill_(True)
        torch.testing.assert_close(finger_tracking_reward(**x)['rate'], 2*before, rtol=0, atol=0)

    def test_all21_axes_mixed_requests_and_surface_velocities_never_change_reward(self):
        # Zero, every individual positive/negative axis, and two mixed21-axis commands.
        commands = torch.cat((torch.zeros(1, 21), torch.eye(21), -torch.eye(21),
                              torch.linspace(-1, 1, 21)[None], torch.ones(1, 21)), 0).double()
        velocities = torch.tensor([[0., 0., 0.], [-.1, 0., 0.], [.1, 0., 0.],
                                   [.3, -.2, .1], [-2., 3., -4.]], dtype=torch.float64)
        n = len(commands)
        for distance in (0., .001, .01, .05, .1, .2):
            for candidate in (False, True):
                x = self.inputs(n=n)
                for k in ('now', 'onset', 'end', 'press', 'delta', 'velocity', 'actions'):
                    x[k] = x[k].double()
                x['delta'].zero_(); x['delta'][:, 0, 0] = distance
                x['candidate'].fill_(candidate)
                x['actions'] = commands.clone()
                reference = finger_tracking_reward(**x)
                for velocity in velocities:
                    x['velocity'][:] = velocity
                    actual = finger_tracking_reward(**x)
                    for key in reference:
                        torch.testing.assert_close(actual[key], reference[key], rtol=0, atol=0)
                expected = 2*(1+distance/.04)**-2*(1+candidate)
                torch.testing.assert_close(reference['rate'], torch.full((n,), expected, dtype=torch.float64), rtol=0, atol=1e-15)
        self.assertEqual(FINGER_REWARD_CONTRACT['schema'], 'guitar_learning.gpu_finger_tracking_rate.v5')
        self.assertEqual(FINGER_REWARD_CONTRACT['quality'], '(1+distance/0.04)^-2*(1+candidate)')
        self.assertIn('none', FINGER_REWARD_CONTRACT['motion_cost'])

    def test_far_target_tail_stays_positive_and_matches_analytic_distance(self):
        x = self.inputs(n=3)
        x['delta'][:, 0, 0] = torch.tensor([.1, .2, 1.])
        rate = finger_tracking_reward(**x)['rate']
        torch.testing.assert_close(rate, torch.tensor([2/3.5**2, 2/6**2, 2/26**2]))
        self.assertTrue(torch.isfinite(rate).all())
        self.assertTrue((rate > 0).all())
        self.assertAlmostEqual(FINGER_REWARD_CONTRACT['distance_scale_m'], .04)

    def test_all_fingers_have_equal_motion_free_quality(self):
        x = self.inputs(n=4)
        for k in ('onset', 'end', 'press'):
            x[k] = x[k].expand(4)
        x.update(finger=torch.arange(1, 5), delta=torch.zeros(4, 4, 3),
                 velocity=torch.randn(4, 4, 3), candidate=torch.ones(4, 4, dtype=torch.bool),
                 actions=torch.linspace(-1, 1, 84).reshape(4, 21))
        result = finger_tracking_reward(**x)
        torch.testing.assert_close(result['quality'], torch.full((4, 4), 2.), rtol=0, atol=0)
        torch.testing.assert_close(result['rate'], torch.full((4,), 4.), rtol=0, atol=0)

    def test_next_opposite_target_selection_has_no_velocity_preference(self):
        x = self.inputs(); x.update(onset=torch.tensor([0., 1.]), end=torch.tensor([1., 2.]),
            press=torch.tensor([0., .9]), finger=torch.tensor([1, 1]),
            delta=torch.tensor([[[.01, 0., 0.], [-.01, 0., 0.]]]),
            velocity=torch.zeros(1, 2, 3), candidate=torch.zeros(1, 2, dtype=torch.bool))
        before = finger_tracking_reward(**x)
        self.assertEqual(before['indices'].tolist(), [[1, -1, -1, -1]])
        for speed in (-.04, .04):
            x['velocity'][0, 1, 0] = speed
            torch.testing.assert_close(before['rate'], finger_tracking_reward(**x)['rate'], rtol=0, atol=0)
        x['delta'][0, 1, 0] = .01
        torch.testing.assert_close(before['rate'], finger_tracking_reward(**x)['rate'], rtol=0, atol=0)

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

    def test_legacy_velocity_and_action_shapes_still_rejected(self):
        x = self.inputs(); x['velocity'] = torch.zeros(1, 1, 2)
        with self.assertRaises(ValueError): finger_tracking_reward(**x)
        x = self.inputs(); x['actions'] = torch.zeros(1, 21, 1)
        with self.assertRaises(ValueError): finger_tracking_reward(**x)


class FingerTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_overlap_current_end_priority_and_next_future_excluding_current(self):
        x = dict(now=torch.tensor([1.5, 0., 2., 5.], dtype=torch.float64),
                 onset=torch.tensor([4., 1., 1.2, 1.2, 2., 2., 1., 4., 4.], dtype=torch.float64),
                 end=torch.tensor([5., 3., 2., 2., 3., 3., 2., 5., 5.], dtype=torch.float64),
                 press=torch.tensor([3.9, .9, 1.1, 1.1, 1.9, 1.9, .9, 3.9, 3.9], dtype=torch.float64),
                 finger=torch.tensor([1, 1, 1, 1, 1, 1, 2, 3, 3]))
        saved = {key:value.clone() for key, value in x.items()}
        result = finger_target_indices(**x)
        expected = [[[2, 4], [6, -1], [-1, -1], [-1, -1]],
                    [[1, 2], [6, -1], [-1, -1], [-1, -1]],
                    [[1, 0], [-1, -1], [7, 8], [-1, -1]],
                    [[-1, -1]]*4]
        self.assertEqual(result['indices'].tolist(), expected)
        self.assertTrue(torch.equal(result['valid'], result['indices'] >= 0))
        for key in saved:
            torch.testing.assert_close(x[key], saved[key], rtol=0, atol=0)

    def test_preparation_inclusive_end_exclusive_and_future_strict_onset(self):
        x = dict(now=torch.tensor([.499999, .5, 2.999999, 3., 3.999999, 4.], dtype=torch.float64),
                 onset=torch.tensor([3., 3.], dtype=torch.float64),
                 end=torch.tensor([4., 4.], dtype=torch.float64),
                 press=torch.tensor([2.5, 2.5], dtype=torch.float64), finger=torch.tensor([3, 3]))
        slots = finger_target_indices(**x)['indices'][:, 2]
        self.assertEqual(slots.tolist(), [[-1, -1], [0, 1], [0, 1], [0, -1], [0, -1], [-1, -1]])

    def test_scalar_reference_and_tracking_slot0_remain_identical(self):
        generator = torch.Generator().manual_seed(37)
        onset = torch.rand(29, generator=generator, dtype=torch.float64)*5
        end = onset+.1+torch.rand(29, generator=generator, dtype=torch.float64)*2
        press = onset-.2
        finger = torch.randint(1, 5, (29,), generator=generator)
        now = torch.tensor([-2., 0., .5, 1., 2., 4., 8.], dtype=torch.float64)
        result = finger_target_indices(now, onset, end, press, finger)
        expected = []
        for at in now.tolist():
            row = []
            for f in range(1, 5):
                audible = [i for i in range(29) if finger[i] == f and onset[i] <= at < end[i]]
                preparing = [i for i in range(29) if finger[i] == f and press[i]-2 <= at < end[i]]
                first = min(audible, key=lambda i: (float(end[i]), i)) if audible else (
                    min(preparing, key=lambda i: (float(onset[i]), i)) if preparing else -1)
                future = [i for i in preparing if i != first and onset[i] > at]
                second = min(future, key=lambda i: (float(onset[i]), i)) if future else -1
                row.append([first, second])
            expected.append(row)
        self.assertEqual(result['indices'].tolist(), expected)
        tracking = finger_tracking_reward(now, onset, end, press, finger,
            torch.zeros(7, 29, 3, dtype=torch.float64), torch.zeros(7, 29, 3, dtype=torch.float64),
            torch.zeros(7, 29, dtype=torch.bool), torch.zeros(7, 21, dtype=torch.float64))
        self.assertTrue(torch.equal(tracking['indices'], result['indices'][..., 0]))
        self.assertTrue(torch.equal(tracking['valid'], result['valid'][..., 0]))

    def test_empty_score_and_contract_slot_order(self):
        result = finger_target_indices(torch.tensor([0., 1.]), torch.empty(0), torch.empty(0),
                                       torch.empty(0), torch.empty(0, dtype=torch.long))
        self.assertEqual(result['indices'].shape, (2, 4, 2))
        self.assertEqual(result['indices'].dtype, torch.long)
        self.assertEqual(result['indices'].unique().tolist(), [-1])
        self.assertFalse(result['valid'].any())
        self.assertEqual(FINGER_TARGET_CONTRACT['schema'], 'guitar_learning.left_finger_targets.v1')
        self.assertEqual(FINGER_TARGET_CONTRACT['slots'], [f+'_'+slot
            for f in ('index', 'middle', 'ring', 'pinky') for slot in ('tracking', 'next')])


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
        other = finger_posture_reward(**self.inputs((60., 75., 40.)))
        self.assertAlmostEqual(float(balanced['coordination_rate']), .05, places=14)
        self.assertAlmostEqual(float(balanced['standby_rate']), .05, places=14)
        self.assertAlmostEqual(float(other['standby_rate']), .05, places=14)
        bad = finger_posture_reward(**self.inputs((-40., 0., 90.)))
        # Violations70/70/20 degrees; standby distances25/15/45 degrees.
        self.assertAlmostEqual(float(bad['coordination_rate']), .05*math.exp(-(70**2+70**2+20**2)/30**2), places=14)
        self.assertAlmostEqual(float(bad['standby_rate']), .05*math.exp(-(25**2+15**2+45**2)/30**2), places=14)

    def test_double90_flexion_is_softly_distinguished_from_shared_bending(self):
        balanced = finger_posture_reward(**self.inputs((40., 55., 35.)))
        curled = finger_posture_reward(**self.inputs((60., 90., 90.)))
        self.assertAlmostEqual(float(balanced['coordination_rate']), .05, places=14)
        # Existing three violations are zero; only min(PIP,DIP)-60=30deg applies.
        self.assertAlmostEqual(float(curled['coordination_rate']), .05*math.exp(-1), places=14)
        self.assertGreater(float(curled['coordination_rate']), 0.)
        self.assertEqual(FINGER_COORDINATION_CONTRACT['schema'], 'guitar_learning.gpu_finger_posture_rate.v2')
        self.assertEqual(FINGER_COORDINATION_CONTRACT['coordination_violations_degrees'][-1],
                         'relu(min(PIP,DIP)-60)')

    def test_standby_retains_wide_bands_with_pip75_upper_boundary(self):
        for mcp in (-15., 110.):
            for pip in (15., 75.):
                for dip in (-10., 45.):
                    result = finger_posture_reward(**self.inputs((mcp, pip, dip)))
                    self.assertAlmostEqual(float(result['standby_rate']), .05, places=14)
        outside = finger_posture_reward(**self.inputs((40., 90., 30.)))
        self.assertAlmostEqual(float(outside['standby_rate']), .05*math.exp(-15**2/30**2), places=14)
        self.assertEqual(FINGER_COORDINATION_CONTRACT['standby_bands_degrees'],
                         [[-15., 110.], [15., 75.], [-10., 45.]])

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
