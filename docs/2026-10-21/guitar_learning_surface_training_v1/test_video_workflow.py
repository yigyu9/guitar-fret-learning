"""CPU structure/pose checks only: no Isaac, CUDA, Renderer or GL context."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np


PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, PHASE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluation = load('evaluate_checkpoints')
video = load('render_video')


class VideoWorkflowTests(unittest.TestCase):
    def test_predeclared_selection_is_safe_then_id_else_duration_then_id(self):
        rows = [dict(env_id=i, task_time_s=10.+i, reason='terminal_failure',
                     left_curriculum=dict(full_safe=False)) for i in range(8)]
        self.assertEqual(evaluation.select_video_env(rows), 7)
        rows[6]['task_time_s'] = 17.
        self.assertEqual(evaluation.select_video_env(rows), 6)
        for i in (3, 5):
            rows[i].update(reason='timeline_complete', left_curriculum=dict(full_safe=True))
        self.assertEqual(evaluation.select_video_env(list(reversed(rows))), 3)
        with self.assertRaises(ValueError):
            evaluation.select_video_env(rows[:-1])

    def test_capture_requires_continuous_first_episode_and_actual_counts(self):
        arrays = dict(body_state=np.zeros((3, 106, 13)), q=np.zeros((3, 105)), qd=np.zeros((3, 105)),
            target=np.zeros((3, 105)), action=np.zeros((3, 39)), clock=np.array([0, 4, 8]),
            left_count=np.array([0, 0, 1]), near_count=np.zeros(3), contact_count=np.zeros(3), candidate_count=np.zeros(3))
        arrays['body_state'][..., 6] = 1.
        episode = dict(steps=2, task_time_s=8/240., song=dict(left_success_count=1))
        evaluation.validate_capture(arrays, 106, episode)
        for key, index, value in (('clock', 1, 8), ('left_count', -1, 0), ('action', (1, 0), np.nan),
                                   ('body_state', (1, 0, 6), 0)):
            damaged = copy.deepcopy(arrays)
            damaged[key][index] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                evaluation.validate_capture(damaged, 106, episode)

    def test_source_body_mapping_and_cpu_model_readback_without_renderer(self):
        import mujoco
        from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses
        probe = ROOT/'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'
        initial = json.loads((probe/'initial_values.json').read_text())
        source = json.loads((probe/'prepared.json').read_text())['sample']['native']
        names = ['human/'+n for n in initial['human_body_names']] + ['guitar/'+n for n in initial['guitar_body_names']] + ['chair/box']
        rows = [r for actor in ('human', 'guitar', 'chair') for r in source[actor+'_body_states']]
        frame = np.asarray([[*[r['pose']['p'][a] for a in 'xyz'], *[r['pose']['r'][a] for a in 'xyzw'],
                             *[r['vel']['linear'][a] for a in 'xyz'], *[r['vel']['angular'][a] for a in 'xyz']] for r in rows])
        state = video.pose_state(names, frame, initial)
        for actor in ('human', 'guitar', 'chair'):
            self.assertEqual([r['pose'] for r in state[actor+'_body_states']], [r['pose'] for r in source[actor+'_body_states']])
        with self.assertRaises(ValueError):
            video.pose_state(list(reversed(names)), frame, initial)
        with patch.object(mujoco, 'Renderer', side_effect=AssertionError('No renderer/context in CPU check')):
            model, data, mapping, _ = build_model(initial)
            audit = set_body_poses(model, data, mapping, state)
            self.assertEqual((model.nq, model.nv, data.time), (0, 0, 0.))
            self.assertEqual(audit['body_count'], len(names))
            self.assertLess(audit['max_position_error_m'], 1e-9)
            self.assertLess(audit['max_rotation_error_rad'], 1e-9)
            ids = np.flatnonzero(model.geom_bodyid > 0)
            radius = model.geom_rbound[ids, None]
            low, high = (data.geom_xpos[ids]-radius).min(0), (data.geom_xpos[ids]+radius).max(0)
            video.fit_camera(model, data, low, high)
            bounds = video.projection_bounds(model, data)
            self.assertLessEqual(bounds['max_abs_ndc_x'], .900001)
            self.assertLessEqual(bounds['max_abs_ndc_y'], .750001)
        endpoints = np.asarray(video.string_endpoints(names, frame))
        self.assertEqual(endpoints.shape, (6, 2, 3))
        self.assertTrue(np.isfinite(endpoints).all())
        self.assertTrue((np.linalg.norm(endpoints[:, 1]-endpoints[:, 0], axis=-1) > .1).all())


if __name__ == '__main__':
    unittest.main()
