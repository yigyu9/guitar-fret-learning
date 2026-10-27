"""Independent saved-source consistency checks; no GPU execution."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

PHASE = Path(__file__).resolve().parents[1]


class ExistingAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((PHASE/'existing_analysis.json').read_text())
        cls.evaluation = PHASE.parent/'guitar_learning_long_training_v19_3000/evaluation_video1_final_1024'
        cls.meta = json.loads((cls.evaluation/'capture_metadata.json').read_text())
        with (cls.evaluation/'first_episodes.jsonl').open() as stream:
            cls.rows = [json.loads(line) for line in stream]

    def test_pins(self):
        for path, expected in self.result['inputs_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected, path)

    def test_cohort_and_aggregate_reward_identity(self):
        self.assertEqual(self.result['all']['episodes'], 1024)
        self.assertEqual(self.result['safe']['episodes'], 887)
        self.assertEqual(len({r['env_id'] for r in self.rows}), 1024)
        for finger in ('index', 'middle', 'ring', 'pinky'):
            s = self.result['all']['fingers'][finger]['standby']
            self.assertAlmostEqual(.0025*s['gate_weighted_s']*s['eligible_mean_quality'], s['raw_standby_reward'], places=8)
            self.assertLessEqual(s['gate_weighted_s'], s['eligible_s']+1e-7)
            self.assertLessEqual(s['eligible_s'], self.result['all']['total_episode_seconds']+1e-7)

    def test_geometry_and_pattern_independent_scipy(self):
        pm = self.meta['posture_reconstruction']
        for capture in self.meta['captures']:
            with np.load(self.evaluation/capture['path']) as z:
                q = z['body_state'][1:, :, 3:7]
                for f, name in enumerate(('index', 'middle', 'ring', 'pinky')):
                    child = q[:, pm['segment_body_indices'][f]]
                    parent = np.concatenate([q[:, pm['palm_body_index'], None], child[:, :2]], axis=1)
                    direction = (Rotation.from_quat(parent.reshape(-1, 4)).inv()*
                                 Rotation.from_quat(child.reshape(-1, 4))).apply(np.tile([0., -1., 0.], (len(q)*3, 1)))
                    direction = direction.reshape(-1, 3, 3)
                    angle = np.degrees(np.arctan2(-direction[..., 2], -direction[..., 1]))
                    expected = self.result['captures'][str(capture['env_id'])]['fingers'][name]
                    np.testing.assert_allclose(angle.mean(0), expected['conditions']['all']['mean_angles_degrees'], atol=2e-5)
                    pattern = (angle[:, 1] <= 10) & (angle[:, 2] >= 60)
                    self.assertAlmostEqual(pattern.mean(), expected['conditions']['all']['pip_le10_dip_ge60_fraction'])
                    np.testing.assert_allclose(angle[-1], expected['final_angles_degrees'], atol=2e-5)

    def test_full_tail_cannot_have_relevant_target_veto(self):
        targets = json.loads((self.evaluation/'targets.json').read_text())
        for f, name in enumerate(('index', 'middle', 'ring', 'pinky')):
            tail = self.result['schedule'][name]['full_b_tail_start_s']
            self.assertTrue(all(t['end_s'] < tail for t in targets if t['finger'] == f+1))
            self.assertAlmostEqual(tail-max(t['end_s'] for t in targets if t['finger'] == f+1), .15)


if __name__ == '__main__':
    unittest.main()
