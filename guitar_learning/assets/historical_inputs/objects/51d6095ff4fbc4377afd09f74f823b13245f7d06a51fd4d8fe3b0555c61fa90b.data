import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.control import JointTargetContract
from guitar_learning.music_task import ScoreTarget
from guitar_learning.transition.solver import input_paths, solve
from guitar_learning.training_environment import default_action_ranges


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'


def fixture():
    prepared = json.loads((SOURCE / 'prepared.json').read_text())
    initial = json.loads((SOURCE / 'initial_values.json').read_text())
    meta = prepared['metadata']['target_contract']
    codec = JointTargetContract(meta['native_order'], meta['q_ref_rad'],
        meta['native_lower_rad'], meta['native_upper_rad'], meta['rates_rad_s'],
        half_range_rad=default_action_ranges())
    targets = [ScoreTarget('a', 'a', 1, 7, 3, 1, 2., 3., 0., 0., 1.),
               ScoreTarget('b', 'b', 1, 5, 1, 1, 3., 3.5, 2.5, 1., 1.5)]
    return prepared['sample'], codec, targets, initial


class SolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sample, codec, targets, initial = fixture()
        cls.sample, cls.codec, cls.targets, cls.initial = sample, codec, targets, initial
        cls.plan = solve(sample, codec, targets, joint_names=initial['joint_names'],
            human_names=initial['human_body_names'], max_nfev=2, starts=1)

    def test_proposals_have_original_codec_endpoints_without_adoption(self):
        self.assertEqual([c['name'] for c in self.plan['candidates']],
                         ['single_a', 'overlap', 'single_b', 'release'])
        for candidate in self.plan['candidates']:
            action = np.asarray(candidate['action39'])
            self.assertEqual(action.shape, (39,))
            self.assertTrue(np.isfinite(action).all())
            self.assertTrue((np.abs(action) <= 1.).all())
            self.assertTrue((action[33:] == 0.).all())
            requested, smoothed = self.codec.targets(action, self.codec.reset_targets())
            np.testing.assert_allclose(requested, candidate['requested_target81_rad'], atol=1e-12)
            np.testing.assert_array_equal(requested[self.codec.held_indices],
                                          self.codec.q_ref[self.codec.held_indices])
            self.assertFalse(candidate['native_success'])
            self.assertTrue(np.any(np.abs(requested-smoothed) > 1e-8))
        self.assertFalse(self.plan['success'])
        self.assertTrue(self.plan['native_validation_required'])

    def test_measured_q_and_fixed_reference_are_distinct(self):
        np.testing.assert_array_equal(self.plan['measured_native105_rad'],
            [row['pos'] for row in self.sample['native']['human_dof_states']])
        np.testing.assert_array_equal(self.plan['codec_reference81_rad'], self.codec.q_ref)
        upper = [self.initial['joint_names'].index(name) for name in self.codec.names]
        self.assertTrue(np.any(np.abs(np.array(self.plan['measured_native105_rad'])[upper]-self.codec.q_ref) > 1e-5))
        self.assertLess(self.plan['calibration']['position_max_m'], 1e-8)
        self.assertIn('unverified', self.plan['calibration']['scope'])

    def test_inputs_are_static_explicit_and_mesh_surface_not_origin(self):
        self.assertEqual(self.plan['input_paths'], input_paths())
        self.assertTrue(all(Path(path).is_file() for path in input_paths()))
        self.assertTrue(any(path.endswith('index3_left.stl') for path in input_paths()))
        self.assertTrue(any(path.endswith('index2_left.stl') for path in input_paths()))
        self.assertIn('not PhysX', self.plan['surface_scope'])

    def test_bad_sample_and_empty_budget_fail_closed(self):
        sample = copy.deepcopy(self.sample)
        sample['geometry']['physics_step'] += 1
        with self.assertRaisesRegex(ValueError, 'same-step'):
            solve(sample, self.codec, self.targets, joint_names=self.initial['joint_names'],
                  human_names=self.initial['human_body_names'], max_nfev=1)
        with self.assertRaises(ValueError):
            solve(self.sample, self.codec, self.targets, joint_names=self.initial['joint_names'],
                  human_names=self.initial['human_body_names'], starts=0)

    def test_asymmetric_inverse_clips_and_zero_span_stays_zero(self):
        from guitar_learning.local_skills.controls import normalize_target
        reference = [0.] * 39
        lower, upper = [-.1] * 39, [.35] * 39
        lower[0] = upper[0] = 0.
        normalized = normalize_target([.5] * 39, reference, lower, upper)
        self.assertEqual(normalized[0], 0.)
        self.assertEqual(normalized[1:], [1.] * 38)

    def test_single_b_has_only_explicit_same_string_higher_blocker(self):
        without = solve(self.sample, self.codec, self.targets[1:],
            joint_names=self.initial['joint_names'], human_names=self.initial['human_body_names'],
            max_nfev=1, starts=1)
        with_context = solve(self.sample, self.codec, self.targets[1:], context_targets=self.targets,
            joint_names=self.initial['joint_names'], human_names=self.initial['human_body_names'],
            max_nfev=1, starts=1)
        self.assertEqual(without['declared_context_blockers'], [])
        self.assertNotIn('ring', without['candidates'][0]['geometry'])
        self.assertEqual([x['finger'] for x in with_context['declared_context_blockers']], ['ring'])
        geometry = with_context['candidates'][0]['geometry']
        self.assertEqual(set(geometry), {'index', 'ring'})
        self.assertTrue(geometry['index']['required'])
        self.assertFalse(geometry['ring']['required'])
        self.assertEqual(geometry['ring']['lift_surface_scope'], 'finger2+3')
        self.assertLessEqual(geometry['ring']['minimum_lift_surface_height_G_m'],
                             geometry['ring']['minimum_source_surface_height_G_m'])
        self.assertFalse(with_context['success'])

    def test_blocker_finger2_penetration_changes_clearance_objective(self):
        from guitar_learning.geometry_v1 import frame
        from guitar_learning.transition import solver
        original = solver._surface_vertices
        _, guitar_rotation = frame(self.sample['native']['guitar_body_states'][0])
        def lowered_middle(asset_path, segment=3):
            if segment == 3:
                return original(asset_path, segment)
            result = {}
            for finger in solver.FINGERS.values():
                body = self.sample['native']['human_body_states'][
                    self.initial['human_body_names'].index('LH:'+finger+'2')]
                _, rotation = frame(body)
                result[finger] = np.array([rotation.inv().apply(guitar_rotation.apply([0., 0., -.1]))])
            return result
        kwargs = dict(joint_names=self.initial['joint_names'], human_names=self.initial['human_body_names'],
            context_targets=self.targets, max_nfev=1, starts=1)
        ordinary = solve(self.sample, self.codec, self.targets[1:], **kwargs)
        with patch.object(solver, '_surface_vertices', lowered_middle):
            altered = solve(self.sample, self.codec, self.targets[1:], **kwargs)
        ring = altered['candidates'][0]['geometry']['ring']
        self.assertLess(ring['minimum_lift_surface_height_G_m'],
                        ring['minimum_source_surface_height_G_m'] - .05)
        self.assertGreater(altered['candidates'][0]['objective'], ordinary['candidates'][0]['objective'] + 1.)


if __name__ == '__main__':
    unittest.main()
