"""Fixed-profile ownership and codec tests; recorded sessions are not native PD evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from guitar_learning.core.control import (
    ACTIVE_NAMES, HELD_NAMES, LEFT_HAND_NAMES, JointTargetContract)
from guitar_learning.core.environment_v4 import FreeGuitarEnvironment
from guitar_learning.core.control import (
    default_profile, validate_profile, profile_control_settings)
from guitar_learning.core.control import target_rates
from guitar_learning.tests.test_environment_v4 import FakeSession


def inputs():
    # Reverse native order to make semantic-vs-native indexing errors visible.
    names = tuple(reversed(ACTIVE_NAMES+HELD_NAMES))
    reference = np.linspace(-.4, .4, len(names))
    lower, upper = np.full(len(names), -1.2), np.full(len(names), 1.8)
    half = np.full(39, .5)
    return names, reference, lower, upper, half, target_rates(names)


def codec(smoothing=.2):
    names, reference, lower, upper, half, rates = inputs()
    half, rates, alpha = profile_control_settings(names, reference, lower, upper,
                                                 half, rates, smoothing)
    return JointTargetContract(names, reference, lower, upper, rates,
                               half_range_rad=half, smoothing_alpha=alpha)


class ProfileRecordedSession(FakeSession):
    """Explicit contract fixture only; FakeSession has no native actuator backend."""
    def __init__(self, config, out):
        super().__init__(config, out)
        self.finger_control_description = dict(profile=default_profile(), applied=True,
                                               evidence='recorded interface fixture')


class FingerControlTests(unittest.TestCase):
    def test_profile_is_exact_json_contract_and_returns_private_copy(self):
        profile = default_profile()
        self.assertEqual(profile['scope'], 'left21_native_joint_limits')
        self.assertEqual(json.loads(json.dumps(profile)), profile)
        validated = validate_profile(profile)
        profile['finger_rate_rad_s'] = 99.
        self.assertEqual(validated['finger_rate_rad_s'], 4.)
        for change in (dict(unrequested=True), dict(finger_rate_rad_s=3.),
                       dict(finger_stiffness=float('nan')), dict(finger_rate_rad_s=4)):
            altered = dict(default_profile(), **change)
            with self.assertRaises(ValueError):
                validate_profile(altered)
        missing = default_profile()
        missing.pop('scope')
        with self.assertRaises(ValueError):
            validate_profile(missing)

    def test_signed_endpoint_requests_are_full_native_only_on_left21(self):
        c = codec()
        fingers = [c.names.index(name) for name in LEFT_HAND_NAMES]
        others = [c.names.index(name) for name in ACTIVE_NAMES if name not in LEFT_HAND_NAMES]
        for sign in (-1., 0., 1.):
            requested, final = c.targets(np.full(39, sign), c.reset_targets())
            expected = c.lower if sign < 0 else c.upper if sign > 0 else c.q_ref
            np.testing.assert_allclose(requested[fingers], expected[fingers], rtol=0., atol=1e-14)
            np.testing.assert_allclose(requested[others], c.q_ref[others]+sign*.5)
            np.testing.assert_array_equal(requested[c.held_indices], c.q_ref[c.held_indices])
            np.testing.assert_array_equal(final[c.held_indices], c.q_ref[c.held_indices])

    def test_rate_changes_only_left21_and_inactive_right_stays_at_reference(self):
        c = codec()
        action = np.r_[np.ones(33), np.zeros(6)]
        requested, final = c.targets(action, c.reset_targets())
        fingers = [c.names.index(name) for name in LEFT_HAND_NAMES]
        arm = [c.names.index(name) for name in ACTIVE_NAMES[:12]]
        right = [c.names.index(name) for name in ACTIVE_NAMES[33:]]
        np.testing.assert_allclose(final[fingers]-c.q_ref[fingers], 4./60.)
        np.testing.assert_allclose(final[arm]-c.q_ref[arm], 3./60.)
        np.testing.assert_array_equal(final[right], c.q_ref[right])
        np.testing.assert_array_equal(final[c.held_indices], c.q_ref[c.held_indices])
        self.assertTrue(np.all(requested[fingers] > final[fingers]))

    def test_vector_smoothing_is_semantic_readonly_and_json_safe(self):
        names, reference, lower, upper, half, rates = inputs()
        alpha = np.full(39, .2)
        alpha[12:33] = .45
        c = JointTargetContract(names, reference, lower, upper, np.full(81, 1000.),
                               half_range_rad=half, smoothing_alpha=alpha)
        alpha[:] = .9
        requested, final = c.targets(np.ones(39), c.reset_targets())
        expected_alpha = np.r_[np.full(12, .2), np.full(21, .45), np.full(6, .2)]
        np.testing.assert_allclose(final[c.active_indices]-c.q_ref[c.active_indices],
                                   expected_alpha*.5)
        np.testing.assert_allclose(c.alpha, expected_alpha)
        self.assertFalse(c.alpha.flags.writeable)
        with self.assertRaises(ValueError):
            c.alpha[0] = 1.
        self.assertEqual(json.loads(json.dumps(c.metadata))['smoothing_alpha'],
                         expected_alpha.tolist())
        scalar = JointTargetContract(names, reference, lower, upper, rates,
                                    half_range_rad=half, smoothing_alpha=.2)
        self.assertIsInstance(scalar.alpha, float)
        self.assertEqual(scalar.metadata['smoothing_alpha'], .2)

    def test_profile_settings_do_not_alias_or_change_other_channel_controls(self):
        names, reference, lower, upper, half, rates = inputs()
        originals = [value.copy() for value in (reference, lower, upper, half, rates)]
        base_alpha = np.linspace(.1, .9, 39)
        half_new, rates_new, alpha = profile_control_settings(names, reference, lower,
                                        upper, half, rates, base_alpha)
        untouched = [i for i, name in enumerate(names) if name not in LEFT_HAND_NAMES]
        np.testing.assert_array_equal(rates_new[untouched], rates[untouched])
        np.testing.assert_array_equal(half_new[:12], half[:12])
        np.testing.assert_array_equal(half_new[33:], half[33:])
        np.testing.assert_array_equal(alpha[:12], base_alpha[:12])
        np.testing.assert_array_equal(alpha[33:], base_alpha[33:])
        for actual, before in zip((reference, lower, upper, half, rates), originals):
            np.testing.assert_array_equal(actual, before)
        half[:] = 9.
        rates[:] = 99.
        base_alpha[:] = .01
        np.testing.assert_array_equal(half_new[:12], originals[3][:12])
        np.testing.assert_array_equal(rates_new[untouched], originals[4][untouched])
        self.assertTrue(np.all(alpha[12:33] == .45))

    def test_invalid_alpha_and_native_profile_inputs_are_rejected(self):
        names, reference, lower, upper, half, rates = inputs()
        for bad in (np.zeros(39), np.full(39, 1.01), np.full(39, np.nan),
                    np.ones(38), np.ones((1, 39))):
            with self.assertRaises(ValueError):
                JointTargetContract(names, reference, lower, upper, rates,
                                    half_range_rad=half, smoothing_alpha=bad)
            with self.assertRaises(ValueError):
                profile_control_settings(names, reference, lower, upper, half, rates, bad)
        changed = lower.copy()
        changed[names.index(LEFT_HAND_NAMES[0])] = upper[names.index(LEFT_HAND_NAMES[0])]
        with self.assertRaises(ValueError):
            profile_control_settings(names, reference, changed, upper, half, rates, .2)

    def test_v4_profile_contract_and_four_samples_with_recorded_applied_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            env = FreeGuitarEnvironment({}, folder, action_half_range_rad=.5,
                finger_profile=default_profile(), session_factory=ProfileRecordedSession,
                geometry_fn=lambda state, h, g: dict(physics_step=state['physics_step']))
            try:
                _, info = env.reset()
                c = env.contract
                fingers = [c.names.index(name) for name in LEFT_HAND_NAMES]
                np.testing.assert_array_equal(c.action_lower[12:33], c.lower[fingers])
                np.testing.assert_array_equal(c.action_upper[12:33], c.upper[fingers])
                np.testing.assert_array_equal(c.alpha[12:33], .45)
                self.assertEqual(info['target_contract']['finger_control']['profile'], default_profile())
                self.assertIsInstance(env.alpha, list)
                json.dumps(info['target_contract'])
                before = env.session.scene.target.copy()
                _, info = env.step(np.r_[np.ones(33), np.zeros(6)])
                self.assertEqual(len(info['physics_samples240']), 4)
                finger105 = [env.session.scene.names.index(name) for name in LEFT_HAND_NAMES]
                np.testing.assert_allclose(env.session.scene.target[finger105]-before[finger105],
                                           4./60., atol=1e-7)
                expected = copy.deepcopy(c.metadata)
                env.reset()
                self.assertEqual(env.contract.metadata, expected)
            finally:
                env.close()

    def test_profile_without_matching_applied_native_evidence_fails_closed(self):
        for description in (None, dict(profile=default_profile(), applied=False),
                            dict(profile=dict(default_profile(), finger_rate_rad_s=3.), applied=True)):
            sessions = []
            def factory(config, out):
                session = FakeSession(config, out)
                session.finger_control_description = description
                sessions.append(session)
                return session
            with tempfile.TemporaryDirectory() as folder:
                env = FreeGuitarEnvironment({}, folder, action_half_range_rad=.5,
                    finger_profile=default_profile(), session_factory=factory,
                    geometry_fn=lambda state, h, g: {})
                with self.assertRaisesRegex(ValueError, 'matching applied native'):
                    env.reset()
                self.assertFalse(env.ready)
                self.assertTrue(sessions[0].closed)
                self.assertEqual(sessions[0].policy_calls, 0)


if __name__ == '__main__':
    unittest.main()
