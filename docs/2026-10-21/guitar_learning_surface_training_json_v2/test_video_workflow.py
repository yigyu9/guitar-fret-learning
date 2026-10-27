"""CPU structure/pose checks only: no Isaac, CUDA, Renderer or GL context."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
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
    def test_four_selected_segments_and_only_json_helper_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original, recovery, logging, run = [root/name for name in ('failed', 'resume1700', 'resume1550', 'resume1200')]
            for path in (original, recovery, logging, run):
                path.mkdir()
            def put(path, value):
                path.write_text(json.dumps(value))
            settings = dict(num_envs=1024, horizon=32, size='large', seed=7, initial_std=.05,
                specialist=dict(role='left'), song={}, song_training={}, ppo={}, physics_backend={}, updates=1200)
            for path, count in ((original, 2000), (recovery, 1700), (logging, 1550), (run, 1200)):
                put(path/'settings.json', dict(settings, updates=count))
            first = original/'checkpoint_000299.pt'
            second = recovery/'checkpoint_000149.pt'
            selected = logging/'checkpoint_000349.pt'
            for path in (first, second, selected):
                path.write_bytes(b'CPU JSON/hash fixture; not a real policy checkpoint')
            asset = root/'asset'; asset.write_text('fixed-source')
            old_pins = {str(asset): evaluation.sha(asset), str(original/'settings.json'): evaluation.sha(original/'settings.json')}
            old_pins.update({str(evaluation.ROOT/path): 'old-logging-SHA' for path in evaluation.LOGGING_PATHS})
            mid_pins = {key: value for key, value in old_pins.items() if key != str(original/'settings.json')}
            mid_pins.update({str(recovery/'settings.json'): evaluation.sha(recovery/'settings.json'), str(first): evaluation.sha(first)})
            logging_pins = {key: value for key, value in mid_pins.items() if key not in (str(recovery/'settings.json'), str(first))}
            logging_pins.update({str(evaluation.ROOT/path): 'new-logging-SHA' for path in evaluation.LOGGING_PATHS})
            logging_pins.update({str(evaluation.ROOT/path): 'added-logging-SHA' for path in evaluation.NEW_LOGGING_PATHS})
            logging_pins.update({str(logging/'settings.json'): evaluation.sha(logging/'settings.json'), str(second): evaluation.sha(second)})
            pins = {key: value for key, value in logging_pins.items() if key not in (str(logging/'settings.json'), str(second))}
            pins.update({str(evaluation.ROOT/path): 'Dragon4-SHA' for path in evaluation.NEW_LOGGING_PATHS})
            pins.update({str(run/'settings.json'): evaluation.sha(run/'settings.json'), str(selected): evaluation.sha(selected)})
            for path, values in ((original, old_pins), (recovery, mid_pins), (logging, logging_pins), (run, pins)):
                put(path/'inputs_before.json', values)
            put(original/'update_000299.json', dict(update_index=299, optimizer_updates=300, journal=dict(committed=9_830_400)))
            put(recovery/'update_000149.json', dict(update_index=149, optimizer_updates=450, journal=dict(committed=4_915_200)))
            put(logging/'update_000349.json', dict(update_index=349, optimizer_updates=800, journal=dict(committed=11_468_800)))
            for path, indices in ((original, range(300, 308)), (recovery, range(150, 185)), (logging, range(350, 370))):
                for index in indices:
                    put(path/('update_%06d.json' % index), {})
            report = dict(completed=True, optimizer_updates=2000, transitions=39_321_600,
                updates=[dict(update_index=i, optimizer_updates=801+i, transitions=32768) for i in range(1200)])
            put(run/'report.json', report)
            _, _, chain = evaluation.recovery_contract(run, original, recovery, logging)
            self.assertFalse(chain['original_attempt_completed'])
            self.assertFalse(chain['first_recovery_attempt_completed'])
            self.assertFalse(chain['logging_fix_attempt_completed'])
            self.assertEqual(chain['effective_chain_transitions'], 65_536_000)
            self.assertEqual(chain['selected_prefix_updates']+chain['selected_recovery_updates']+chain['selected_logging_fix_updates']+chain['resumed_updates'], 2000)
            self.assertEqual(len(chain['source_changes']), 4)
            self.assertEqual(len(chain['json_v2_source_changes']), 2)
            self.assertEqual(len(chain['excluded_original_update_files']), 8)
            self.assertEqual(len(chain['excluded_first_recovery_update_files']), 35)
            self.assertEqual(len(chain['excluded_logging_fix_update_files']), 20)
            for field, value in (('completed', False), ('optimizer_updates', 1999),
                                 ('transitions', 65_536_000), ('updates', report['updates'][:-1])):
                put(run/'report.json', dict(report, **{field: value}))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    evaluation.recovery_contract(run, original, recovery, logging)
            put(run/'report.json', report)
            for path in (original, recovery, logging):
                put(path/'report.json', dict(completed=True))
                with self.subTest(completed=path.name), self.assertRaises(ValueError):
                    evaluation.recovery_contract(run, original, recovery, logging)
                (path/'report.json').unlink()
            for bad_pins in (dict(pins, **{str(selected): 'wrong-SHA'}),
                             dict(pins, **{str(asset): 'changed-nonlogging-SHA'}),
                             dict(pins, **{str(evaluation.ROOT/evaluation.LOGGING_PATHS[0]): 'changed-existing-writer'}),
                             dict(pins, **{str(root/'extra-source.py'): 'unapproved'}),
                             {key: value for key, value in pins.items() if key != str(evaluation.ROOT/evaluation.NEW_LOGGING_PATHS[0])}):
                put(run/'inputs_before.json', bad_pins)
                with self.subTest(keys=len(bad_pins)), self.assertRaises(ValueError):
                    evaluation.recovery_contract(run, original, recovery, logging)
            put(run/'inputs_before.json', pins)
            put(recovery/'inputs_before.json', dict(mid_pins, **{str(asset): 'wrong-old-source'}))
            with self.assertRaises(ValueError):
                evaluation.recovery_contract(run, original, recovery, logging)
        import torch
        state = dict(model=torch.tensor([1., 2.]), rng=(np.array([1, 2]), None), groups=[dict(lr=.1)])
        self.assertTrue(evaluation.same_tree(state, copy.deepcopy(state)))
        damaged = copy.deepcopy(state); damaged['model'][0] = 3.
        self.assertFalse(evaluation.same_tree(state, damaged))

    def test_json_writes_use_public_encoder(self):
        for name in ('evaluate_checkpoints', 'render_video'):
            tree = ast.parse((PHASE/(name+'.py')).read_text())
            writes = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call) and
                      isinstance(node.func, ast.Attribute) and node.func.attr in ('dump', 'dumps')]
            self.assertTrue(writes)
            self.assertTrue(all(isinstance(func.value, ast.Name) and func.value.id == 'json_io' for func in writes))

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
