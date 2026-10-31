"""PhysX 없이 실제 캐시 저장·복원 메서드의 메타데이터 계약 검사."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch


class CacheMetadataTests(unittest.TestCase):
    def test_roundtrip_legacy_and_independent_snapshot(self):
        source = Path(__file__).resolve().parents[1] / 'env/tasks/task_fret.py'
        tree = ast.parse(source.read_text())
        methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                   and node.name in ('curriculum_state_dict', 'load_curriculum_state_dict')]
        scope = dict(torch=torch, deepcopy=deepcopy)
        for method in methods:
            exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
        env = SimpleNamespace(device='cpu', goals=SimpleNamespace(
            curriculum_sampler_state_dict=lambda: {},
            load_curriculum_sampler_state_dict=lambda state: None))
        for method in methods:
            for node in ast.walk(method):
                if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id == 'self' and node.attr.startswith('_')):
                    setattr(env, node.attr, torch.zeros(1))
        env._success_pose_source_metadata = {'0': {'source_frame': 499}}
        env._success_pose_diagnostic_probes = {}
        saved = scope['curriculum_state_dict'](env)
        env._success_pose_source_metadata['0']['source_frame'] = 1
        self.assertEqual(saved['success_rsi']['source_metadata']['0']['source_frame'], 499)
        scope['load_curriculum_state_dict'](env, saved)
        saved['success_rsi']['source_metadata']['0']['source_frame'] = 2
        self.assertEqual(env._success_pose_source_metadata['0']['source_frame'], 499)
        del saved['success_rsi']['source_metadata']
        scope['load_curriculum_state_dict'](env, saved)
        self.assertEqual(env._success_pose_source_metadata, {})


if __name__ == '__main__':
    unittest.main()
