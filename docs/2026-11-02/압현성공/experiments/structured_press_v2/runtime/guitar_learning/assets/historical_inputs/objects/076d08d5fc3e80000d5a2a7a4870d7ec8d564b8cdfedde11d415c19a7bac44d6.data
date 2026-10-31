"""Pure action/codec checks; no native feasibility or musical-success claim."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from guitar_learning.control import ACTIVE_NAMES, JointTargetContract
from guitar_learning.local_skills.controls import Controller, candidate_configs, normalize_target, FLEX_NAMES


def action(role, value):
    return [value if (i < 33) == (role == 'left') else 0. for i in range(39)]


def context(role, tick, end=.05, accepted=False):
    return dict(time_s=tick/60., task_end_s=end,
        musical_quality_before=dict(strike=dict(accepted_crossing_ids=['original:1'] if accepted else [])),
        applied_normalized39=action(role, .2), reference39=[0.]*39,
        lower39=[-1.]*39, upper39=[1.]*39)


class LocalControlsTests(unittest.TestCase):
    def test_only_four_declared_role_specific_candidates(self):
        self.assertEqual(len(candidate_configs('left')+candidate_configs('right')), 4)
        for role in ('left', 'right'):
            config = candidate_configs(role)[0]
            Controller(role, config)
            changed = copy.deepcopy(config); changed['duration_s'] += .1
            with self.assertRaises(ValueError): Controller(role, changed)
            with self.assertRaises(ValueError): Controller(role, 'not_a_candidate')
            other = candidate_configs('right' if role == 'left' else 'left')[0]['name']
            with self.assertRaises(ValueError): Controller(role, other)
        with self.assertRaises(ValueError): candidate_configs('joint')

    def test_lh_prefix_then_damped_reference_return_and_reset(self):
        controller = Controller('left', 'left_return_reference')
        for tick in range(3):
            policy = action('left', .7-tick*.1); original = policy.copy()
            output, used = controller.action(policy, context('left', tick))
            self.assertEqual(output, original); self.assertFalse(used); self.assertEqual(policy, original)
        output, used = controller.action(action('left', -.6), context('left', 3))
        self.assertTrue(used)
        self.assertEqual(output, action('left', .2))  # Anchor is applied target, not new policy.
        for tick in range(4, 23):
            output, used = controller.action(action('left', .9), context('left', tick))
            self.assertTrue(used)
            self.assertTrue(all(-1. <= x <= 1. for x in output))
            self.assertEqual(output[33:], [0.]*6)
        np.testing.assert_allclose(output, np.zeros(39), atol=1e-12)
        self.assertEqual(controller.diagnostic['start_s'], .05)
        controller.reset()
        output, used = controller.action(action('left', .8), context('left', 0))
        self.assertEqual(output, action('left', .8)); self.assertFalse(used)

    def test_lh_open_flex_only_named_axes_and_safe_zero_spans(self):
        controller = Controller('left', 'left_return_reference_open_flex')
        original = context('left', 0)
        blocked = ACTIVE_NAMES.index('LH:ring3')
        zero = ACTIVE_NAMES.index('LH:thumb2')
        original['reference39'][blocked] = original['lower39'][blocked] = .2
        original['reference39'][zero] = original['lower39'][zero] = original['upper39'][zero] = .4
        before = copy.deepcopy(original)
        for tick in range(23):
            ctx = copy.deepcopy(original); ctx['time_s'] = tick/60.
            output, _ = controller.action(action('left', .5), ctx)
        self.assertEqual(original, before)
        for i, name in enumerate(ACTIVE_NAMES):
            expected = -1. if name in FLEX_NAMES and i not in (blocked, zero) else 0.
            self.assertAlmostEqual(output[i], expected)
        self.assertEqual(output[33:], [0.]*6)

    def test_rh_first_accepted_next_action_holds_last_command_or_applied_target(self):
        for name, expected in [('right_hold_last_command', .7), ('right_hold_applied_target', .2)]:
            controller = Controller('right', name)
            for tick, value in ((0, .5), (1, .7)):
                output, used = controller.action(action('right', value), context('right', tick))
                self.assertEqual(output, action('right', value)); self.assertFalse(used)
            output, used = controller.action(action('right', -.9), context('right', 2, accepted=True))
            self.assertTrue(used); self.assertEqual(output, action('right', expected))
            output, used = controller.action(action('right', -.8), context('right', 3))
            self.assertEqual(output, action('right', expected)); self.assertTrue(used)
            self.assertEqual(controller.diagnostic['start_s'], 2/60.)
            self.assertEqual(output[:33], [0.]*33)

    def test_invalid_actions_clock_and_prefix_cannot_be_silently_repaired(self):
        for invalid in ([0.]*38, [float('nan')]*39, [2.]*39, [1.]*39):
            with self.assertRaises(ValueError):
                Controller('right', 'right_hold_last_command').action(invalid, context('right', 0))
        for ctx in (context('right', 1), context('right', 0, accepted=True)):
            with self.assertRaises(ValueError):
                Controller('right', 'right_hold_last_command').action(action('right', .1), ctx)
        controller = Controller('left', 'left_return_reference')
        controller.action(action('left', .1), context('left', 0))
        with self.assertRaises(ValueError): controller.action(action('left', .1), context('left', 2))
        with self.assertRaises(ValueError): controller.action(action('left', .1), context('left', 1, end=.1))

    def test_inverse_matches_original_asymmetric_codec_and_applied_target_hold(self):
        root = Path(__file__).resolve().parents[2]
        source = root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/training_contract.json'
        metadata = json.loads(source.read_text())['action']['target_contract']
        codec = JointTargetContract(metadata['native_order'], metadata['q_ref_rad'],
            metadata['native_lower_rad'], metadata['native_upper_rad'], metadata['rates_rad_s'],
            half_range_rad=metadata['half_range_rad'], smoothing_alpha=metadata['smoothing_alpha'])
        reference = codec.q_ref[codec.active_indices]
        for requested in ([1.]*39, [-1.]*39, np.linspace(-1., 1., 39)):
            _, applied81 = codec.targets(requested, codec.q_ref)
            normalized = normalize_target(applied81[codec.active_indices], reference, codec.action_lower, codec.action_upper)
            _, held81 = codec.targets(normalized, applied81)
            np.testing.assert_allclose(held81, applied81, rtol=0, atol=1e-12)
        # A held last desired command still advances a lagging codec target.
        _, first = codec.targets([1.]*39, codec.q_ref)
        _, second = codec.targets([1.]*39, first)
        self.assertGreater(np.max(np.abs(second-first)), 0.)
        normalized = normalize_target([999.]*39, reference, codec.action_lower, codec.action_upper)
        self.assertTrue(all(-1. <= x <= 1. for x in normalized))
        self.assertEqual(normalize_target([9.]*39, [0.]*39, [0.]*39, [0.]*39), [0.]*39)
        with self.assertRaises(ValueError): normalize_target([0.]*39, [1.]*39, [0.]*39, [0.]*39)


if __name__ == '__main__': unittest.main()
