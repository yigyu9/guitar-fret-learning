"""Exact float64 codec-history regression; native submission remains float32."""
import copy
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.tool.experiments.contact_recovery import audit as original_audit
from guitar_learning.tool.experiments.contact_recovery import audit_v2
from guitar_learning.tests.test_transition_contact_teacher import environment


class RecoveryAuditV2Tests(unittest.TestCase):
    def test_float64_codec_history_survives_rounded_native_submission(self):
        env, _, _ = environment()
        codec = env.control.contract
        previous = codec.reset_targets()
        action = np.asarray([.137]*33+[0.]*6, dtype=np.float32)
        requested, final = codec.targets(action, previous)
        submitted = final.astype(np.float32).astype(float)
        self.assertFalse(np.array_equal(final, submitted))
        control = dict(requested_upper81_rad=requested.tolist(), codec_target_upper81_rad=final.tolist())
        replayed = audit_v2._replay_codec_step(codec, action.tolist(), previous, control)
        np.testing.assert_array_equal(replayed, final)
        requested2, final2 = codec.targets(action, final)
        control2 = dict(requested_upper81_rad=requested2.tolist(), codec_target_upper81_rad=final2.tolist())
        np.testing.assert_array_equal(audit_v2._replay_codec_step(codec, action, replayed, control2), final2)
        with self.assertRaisesRegex(ValueError, 'codec target did not reproduce exactly'):
            audit_v2._replay_codec_step(codec, action, submitted, control2)

    def test_requested_and_final_target_mutation_rejected_without_tolerance(self):
        env, _, _ = environment()
        codec = env.control.contract
        previous = codec.reset_targets()
        action = np.asarray([.137]*33+[0.]*6, dtype=np.float32)
        requested, final = codec.targets(action, previous)
        control = dict(requested_upper81_rad=requested.tolist(), codec_target_upper81_rad=final.tolist())
        for key in control:
            changed = copy.deepcopy(control)
            changed[key][0] = float(np.nextafter(changed[key][0], np.inf))
            with self.assertRaisesRegex(ValueError, 'did not reproduce exactly'):
                audit_v2._replay_codec_step(codec, action, previous, changed)

    def test_initial_codec_is_original_reset_not_native_submission(self):
        env, _, _ = environment()
        codec = env.control.contract
        initial = dict(codec_target81=codec.reset_targets().tolist())
        np.testing.assert_array_equal(audit_v2._initial_codec_state(codec, initial), codec.q_ref)
        initial['codec_target81'][0] = float(np.nextafter(initial['codec_target81'][0], np.inf))
        with self.assertRaisesRegex(ValueError, 'original reset targets exactly'):
            audit_v2._initial_codec_state(codec, initial)

    def test_scoped_callback_restores_original_and_pins_both_v2_sources(self):
        original = original_audit._audit_recovery
        def completed_capture(folder):
            self.assertIs(original_audit._audit_recovery, audit_v2._audit_recovery)
            return dict(source_pins={})
        with patch.object(audit_v2, '_ORIGINAL_CAPTURE', completed_capture):
            evidence = audit_v2.audit_capture('/synthetic-capture')
        self.assertIs(original_audit._audit_recovery, original)
        self.assertTrue(evidence['codec_history_replayed'])
        self.assertEqual(set(evidence['source_pins']), {str(path) for path in audit_v2.source_paths()})
        with patch.object(audit_v2, '_ORIGINAL_CAPTURE', side_effect=ValueError('native gate rejected')):
            with self.assertRaisesRegex(ValueError, 'native gate rejected'):
                audit_v2.audit_capture('/synthetic-capture')
        self.assertIs(original_audit._audit_recovery, original)


if __name__ == '__main__': unittest.main()
