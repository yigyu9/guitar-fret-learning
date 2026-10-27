"""CPU-only provenance/selection/capture checks; no simulator or policy rollout."""
import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(PHASE))
sys.path.insert(0, str(ROOT))
import evaluate_checkpoints as evaluation
import render_video
from guitar_learning.tests import test_gpu_environment as fixtures


def episode(index, *, safe=False, achieved=0, duration=1.):
    return dict(env_id=index, reason='timeline_complete' if safe else 'terminal_failure',
        task_time_s=duration, song=dict(left_success_count=achieved),
        left_curriculum=dict(full_safe=safe))


class EvaluationHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(1)
        cls.env, _, _ = fixtures.TensorSongTests().environment()

    def test_current_contract_and_actual_posture_metadata(self):
        evaluation.validate_input_contract(self.env.contract)
        result = evaluation.posture_metadata(self.env.contract, self.env.body_names)
        self.assertEqual(result['contract']['schema'], 'guitar_learning.gpu_finger_preparation_rate.v1')
        self.assertEqual(len(result['segment_body_indices']), 4)
        self.assertTrue(all(len(row)==3 for row in result['segment_body_indices']))
        self.assertIn('cannot be reconstructed', result['scope'])
        for group, field, old in (('reward', 'schema', 'guitar_learning.gpu_tensor_song_reward.v15'),
                                 ('observation', 'dimension', 512)):
            changed = copy.deepcopy(self.env.contract)
            changed[group][field] = old
            with self.assertRaises(ValueError):
                evaluation.validate_input_contract(changed)
        for group, key, old in (('reward', 'surface_learning', 'guitar_learning.surface_fretting.v6'),
                               ('reward', 'finger_tracking', 'guitar_learning.gpu_finger_tracking_rate.v5'),
                               ('observation', 'surface_geometry', 'guitar_learning.left_surface_events.v3')):
            changed = copy.deepcopy(self.env.contract)
            changed[group][key]['schema'] = old
            with self.assertRaises(ValueError):
                evaluation.validate_input_contract(changed)

    def test_frozen_v16_451_source_pins_match_and_missing_pin_fails(self):
        pins = json.loads((PHASE/'training_source_manifest.json').read_text())['source']
        seal, source = evaluation.validate_source_pins(pins)
        self.assertEqual(seal.name, 'delivery_manifest.json')
        self.assertEqual(source.name, 'final_source_manifest.json')
        missing = dict(pins)
        missing.pop(next(iter(missing)))
        with self.assertRaises(ValueError):
            evaluation.validate_source_pins(missing)

    def test_video_subject_selection_is_predeclared_and_not_score_based(self):
        rows = [episode(i, duration=i+1., achieved=67-i) for i in range(8)]
        self.assertEqual(evaluation.select_video_env(rows), 7)
        rows[1] = episode(1, safe=True, achieved=0)
        rows[6] = episode(6, safe=True, achieved=67)
        self.assertEqual(evaluation.select_video_env(rows), 1)
        with self.assertRaises(ValueError):
            evaluation.select_video_env(rows[:-1])

    def test_checkpoint_selection_uses_score_then_safety_then_latest_and_excludes_initial(self):
        def report(updates, score, safe):
            return dict(completed=True, source_optimizer_updates=updates, num_envs=1024,
                checkpoint='checkpoint-%d'%updates, evaluation_directory='evaluation-%d'%updates,
                episodes=[episode(i, achieved=score, safe=i<safe) for i in range(1024)])
        rows = [report(0, 67, 1024), report(500, 2, 100), report(1000, 3, 1),
                report(1500, 3, 2), report(2000, 3, 2)]
        selected = evaluation.checkpoint_selection(rows)
        self.assertEqual(selected['best']['updates'], 2000)
        self.assertFalse(selected['mean_achieved_improved_over_initial'])
        rows[-1]['episodes'][0]['song']['left_success_count'] = 2
        self.assertEqual(evaluation.checkpoint_selection(rows)['best']['updates'], 1500)
        rows[-1]['episodes'][0]['env_id'] = 1
        with self.assertRaises(ValueError):
            evaluation.checkpoint_selection(rows)

    def test_checkpoint_paths_follow_actual_100_update_save_indices(self):
        run = Path('/example/train2000')
        self.assertEqual(evaluation.checkpoint_path(run, 0), run/'initial.pt')
        self.assertEqual(evaluation.checkpoint_path(run, 500), run/'checkpoint_000499.pt')
        self.assertEqual(evaluation.checkpoint_path(run, 2000), run/'final.pt')
        with self.assertRaises(ValueError):
            evaluation.checkpoint_path(run, 100)

    def test_per_note_summary_retains_best_run_and_v16_wrong_diagnostics(self):
        rows = []
        fields = ('left', 'near_done', 'contact_done', 'clean', 'best_clean_streak', 'wrong',
                  'missing', 'contact_time', 'near_time', 'wrong_supported_time',
                  'wrong_ambiguous_time', 'wrong_next_preparation_time')
        for safe, best in ((False, .2), (True, .4)):
            values = {field:[0.] for field in fields}
            values['best_clean_streak'] = [best]
            rows.append(dict(left_curriculum=dict(full_safe=safe),
                             left_note_ledger=dict(values=values)))
        summary = evaluation.per_note_summary(rows, [dict(target_id='a', required_clean_s=.4)])[0]
        self.assertAlmostEqual(summary['all_first']['mean_best_clean_streak_s'], .3)
        self.assertAlmostEqual(summary['all_first']['mean_best_required_fraction'], .75)
        self.assertEqual(summary['full_safe_first']['mean_best_required_fraction'], 1.)
        self.assertIn('mean_wrong_next_preparation_time_s', summary['all_first'])

    def test_capture_requires_continuous_clock_unit_quaternions_and_matching_final_count(self):
        row = dict(steps=2, task_time_s=8/240., song=dict(left_success_count=1))
        arrays = dict(body_state=np.zeros((3, 2, 13)), q=np.zeros((3, 105)),
            qd=np.zeros((3, 105)), target=np.zeros((3, 105)), action=np.zeros((3, 39)),
            clock=np.array([0, 4, 8]), left_count=np.array([0, 0, 1]),
            near_count=np.zeros(3), contact_count=np.zeros(3), candidate_count=np.zeros(3))
        arrays['body_state'][..., 6] = 1.
        evaluation.validate_capture(arrays, 2, row)
        for key in ('clock', 'left_count', 'body_state'):
            broken = {name:value.copy() for name,value in arrays.items()}
            broken[key].flat[-1] = np.nan if key=='body_state' else 9
            with self.assertRaises(ValueError):
                evaluation.validate_capture(broken, 2, row)

    def test_pose_conversion_preserves_actual_world_position_and_xyzw_quaternion(self):
        initial = dict(human_body_names=['palm'], guitar_body_names=['box'])
        names = ['human/palm', 'guitar/box', 'chair/box']
        bodies = np.arange(39, dtype=float).reshape(3, 13)
        state = render_video.pose_state(names, bodies, initial)
        for index, actor in enumerate(('human', 'guitar', 'chair')):
            pose = state[actor+'_body_states'][0]['pose']
            self.assertEqual(list(pose['p'].values()), bodies[index, :3].tolist())
            self.assertEqual(list(pose['r'].values()), bodies[index, 3:7].tolist())
        with self.assertRaises(ValueError):
            render_video.pose_state(names[::-1], bodies, initial)


if __name__ == '__main__':
    unittest.main()
