"""CPU tests for current-frame native feature attribution and observed timing."""
import copy
import json
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from ..fretting_v1 import FretTarget, FretContract, FrettingTracker, measure_sample


TARGET = FretTarget(1, 5, 'index')
CONTRACT = FretContract(minimum_dwell_s=.05)


def fixture(step=0, *, finger='index2', string=1, fret_body=5, y=.12, height=-.001,
            raw_lambda=1., translation=(0., 0., 0.), rotation=None):
    rotation = Rotation.identity() if rotation is None else rotation
    translation = np.array(translation)
    def body(position):
        return {'pose': {'p': dict(zip('xyz', (translation + rotation.apply(position)).tolist())),
                         'r': dict(zip('xyzw', rotation.as_quat().tolist()))},
                'vel': {'linear': dict.fromkeys('xyz', 0.), 'angular': dict.fromkeys('xyz', 0.)}}
    fraction = (y - .25) / (-.4 - .25)
    x = (3.5 - string) * (.007 + fraction * (.010 - .007))
    point = np.array([x, y, .01 + height])
    human_names = ['LH:' + name + '3' for name in ('thumb', 'index', 'middle', 'ring', 'pinky')]
    human_names += ['LH:index2', 'LH:middle2', 'LH:index_top', 'RH:pick']
    human_positions = {name: point.copy() for name in human_names}
    guitar_positions = {'guitar': np.zeros(3), 'G:body': np.array([0., -.4, -.02]), 'G:thumb_support_proxy': np.zeros(3)}
    for number in range(1, 7):
        guitar_positions['G:string' + str(number)] = np.array([(3.5 - number) * .007, .25, .01])
        guitar_positions['G:string' + str(number) + '_end'] = np.array([(3.5 - number) * .010, -.4, .01])
    guitar_positions['G:nut'] = np.array([0., .22, 0.])
    for fret in range(1, 23):
        guitar_positions['G:fret' + str(fret)] = np.array([0., .22 - fret * .02, 0.])
    guitar_names = list(guitar_positions)
    state = {'physics_step': step, 'human_body_states': [body(human_positions[name]) for name in human_names],
             'guitar_body_states': [body(guitar_positions[name]) for name in guitar_names],
             'human_dof_states': [{'pos': .123, 'vel': -.234}]}
    guitar_name = 'G:fret' + str(fret_body) if isinstance(fret_body, int) else fret_body
    human_name = 'LH:' + finger
    contact = {'body0_name': 'guitar/' + guitar_name, 'body1_name': 'human/' + human_name,
               'localPos0': dict(zip('xyz', (point - guitar_positions[guitar_name]).tolist())),
               'localPos1': dict(zip('xyz', (point - human_positions[human_name]).tolist())),
               'lambda': raw_lambda}
    row = {'physics_step': step, 'time_s': step / 240., 'contacts': [contact]}
    return state, human_names, guitar_names, row


def measurement(step=0, **kwargs):
    state, humans, guitars, row = fixture(step, **kwargs)
    return measure_sample(state, humans, guitars, row, TARGET, CONTRACT)


class FrettingMeasurements(unittest.TestCase):
    def test_valid_wire_boundary_contact_without_marker_or_pressure_claim(self):
        result = measurement()
        self.assertTrue(result['fretting_contact_candidate'])
        self.assertEqual(result['valid_contact_finger_bodies'], ['human/LH:index2'])
        self.assertIsNone(result['source_fingertip_shape_candidate'])
        self.assertLess(result['contact_evidence'][0]['body_pair_witness_gap_m'], 1e-12)
        json.dumps(result, allow_nan=False)

    def test_wrong_finger_string_fret_zero_lambda_and_proxy_fail(self):
        cases = [{'finger': 'middle2'}, {'finger': 'index_top'}, {'finger': 'thumb3'},
                 {'string': 2}, {'fret_body': 6}, {'raw_lambda': 0.},
                 {'fret_body': 'G:body'}, {'fret_body': 'G:thumb_support_proxy'},
                 {'y': .08}, {'height': .004}]
        for case in cases:
            with self.subTest(case=case):
                self.assertFalse(measurement(**case)['fretting_contact_candidate'])

    def test_normalized_moving_guitar_and_state_read_only(self):
        inputs = fixture(12, translation=(.3, -.5, .8), rotation=Rotation.from_euler('xyz', [.2, -.4, .7]))
        original = copy.deepcopy(inputs)
        transformed = measure_sample(*inputs, TARGET, CONTRACT)
        reference = measurement(12)
        self.assertTrue(transformed['fretting_contact_candidate'])
        np.testing.assert_allclose(transformed['contact_evidence'][0]['guitar_feature_G_m'], reference['contact_evidence'][0]['guitar_feature_G_m'], atol=1e-14)
        self.assertEqual(inputs, original)

    def test_wrong_contact_step_time_and_witness_rejected(self):
        inputs = fixture(10)
        inputs[3]['physics_step'] = 11
        with self.assertRaises(ValueError):
            measure_sample(*inputs, TARGET, CONTRACT)
        inputs = fixture(10)
        inputs[3]['time_s'] += .01
        with self.assertRaises(ValueError):
            measure_sample(*inputs, TARGET, CONTRACT)
        inputs = fixture()
        inputs[3]['contacts'][0]['localPos1']['x'] += .001
        result = measure_sample(*inputs, TARGET, CONTRACT)
        self.assertFalse(result['fretting_contact_candidate'])
        self.assertIn('body_pair_witness_mismatch', result['contact_evidence'][0]['reason_flags'])

    def test_distal3_is_separate_evidence_and_open_zero_never_synthetic_press(self):
        result = measurement(finger='index3')
        self.assertEqual(result['valid_contact_finger_bodies'], ['human/LH:index3'])
        result = measure_sample(*fixture(), FretTarget(1, 0), CONTRACT)
        self.assertFalse(result['press_required'])
        self.assertFalse(result['fretting_contact_candidate'])


class TimingMeasurements(unittest.TestCase):
    def test_dwell_uses_n_minus_one_samples_and_release_is_separate(self):
        tracker = FrettingTracker(CONTRACT, 0., 12.)
        for step in range(12):
            result = tracker.update(step, measurement(step))
        self.assertFalse(result['minimum_dwell_acquired'])
        result = tracker.update(12, measurement(12))
        self.assertTrue(result['minimum_dwell_acquired'])
        self.assertTrue(result['note_interval_hold_observed'])
        result = tracker.update(13, measurement(13, raw_lambda=0.))
        self.assertTrue(result['measured_contact_release'])
        self.assertTrue(result['acquired_hold_dropout'])
        self.assertTrue(result['note_interval_hold_observed'])
        self.assertIsNone(result['intentional_music_release'])

    def test_fractional_short_note_full_hold_without_fake_dwell(self):
        tracker = FrettingTracker(CONTRACT, .3, .3 + .0232 * 240.)
        for step in range(7):
            result = tracker.update(step, measurement(step))
        self.assertTrue(result['note_sample_coverage_complete'])
        self.assertAlmostEqual(result['note_contact_hold_fraction'], 1.)
        self.assertAlmostEqual(result['note_duration_s'], .0232)
        self.assertTrue(result['note_shorter_than_required_dwell'])
        self.assertFalse(result['minimum_dwell_acquired'])
        self.assertFalse(result['note_interval_meets_minimum_dwell'])

    def test_gap_cannot_create_hold_or_release_and_duplicates_rejected(self):
        tracker = FrettingTracker(CONTRACT, 0., 20.)
        tracker.update(0, measurement(0))
        result = tracker.update(10, measurement(10))
        self.assertTrue(result['physics_step_gap'])
        self.assertEqual(result['consecutive_valid_span_s'], 0.)
        self.assertFalse(result['measured_contact_release'])
        self.assertFalse(result['note_sample_coverage_complete'])
        with self.assertRaises(ValueError):
            tracker.update(10, measurement(10))
        with self.assertRaises(ValueError):
            tracker.update(9, measurement(9))

    def test_target_change_resets_acquisition_and_note_hold(self):
        tracker = FrettingTracker(CONTRACT, 0., 20.)
        for step in range(13):
            result = tracker.update(step, measurement(step))
        self.assertTrue(result['minimum_dwell_acquired'])
        value = measurement(13)
        value['target'] = {'string_number': 2, 'musical_fret': 5, 'finger': 'index'}
        result = tracker.update(13, value)
        self.assertTrue(result['target_changed'])
        self.assertFalse(result['minimum_dwell_acquired'])
        self.assertFalse(result['measured_contact_release'])


if __name__ == '__main__':
    unittest.main()
