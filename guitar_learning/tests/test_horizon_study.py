"""H 비교 준비 도구의 봉인·복사 경계·동일 경험 예산을 CPU에서 검사한다."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[2]
MODULE = PROJECT/'docs/2026-11-09/H실험/도구/study.py'
SPEC = importlib.util.spec_from_file_location('horizon_study', MODULE)
study_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study_tool)
DESIGN = json.loads((MODULE.parents[1]/'설계.json').read_text(encoding='utf-8'))


class HorizonStudyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)/'project'
        self.study = self.root/'docs/H'
        self.study.mkdir(parents=True)
        (self.study/'설계.json').write_text(json.dumps(DESIGN), encoding='utf-8')
        for relative in ('guitar_learning/train.py', 'guitar_learning/assets/input.json',
                         'data/song_bundles/press_sequence_c1_v1/manifest.json',
                         'scripts/tab2body.py', 'isaacgym/python/isaacgym/__init__.py',
                         'isaacgym/python/setup.py'):
            self.write(relative, '{}')

    def write(self, relative, value):
        target = self.root/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding='utf-8')
        return target

    def test_common_budget_and_commands_survive_project_move(self):
        study_tool.prepare(self.root, self.study)
        moved = self.root.parent/'moved'
        self.root.rename(moved)
        document = study_tool.commands(moved, moved/'docs/H')
        self.assertTrue(document['verification']['snapshot_valid'])
        for condition, expected_updates, expected_period in zip(document['conditions'], (512, 256, 128), (128, 64, 32)):
            argv = condition['train']
            self.assertEqual(int(argv[argv.index('--updates')+1]), expected_updates)
            self.assertEqual(int(argv[argv.index('--checkpoint-every')+1]), expected_period)
            self.assertEqual(condition['batch_transitions'] * expected_updates, DESIGN['total_transitions'])
            self.assertEqual([row['transitions'] for row in condition['evaluations']], DESIGN['evaluation_transitions'])
            self.assertTrue(condition['evaluations'][0]['checkpoint'].endswith('/J/initial.pt'))
            self.assertTrue(condition['evaluations'][-1]['checkpoint'].endswith('/J/final.pt'))
            self.assertNotIn(str(self.root), ' '.join(argv))

    def test_invalid_budget_and_inconsistent_curriculum_are_rejected(self):
        for key, value in (('total_transitions', 16777217), ('num_envs', 768),
                           ('full_song_after_transitions', 4194305),
                           ('evaluation_transitions', [0, 16777216])):
            with self.subTest(key=key):
                design = copy.deepcopy(DESIGN)
                design[key] = value
                with self.assertRaises(ValueError):
                    study_tool.validate_design(design)

    def test_external_file_and_directory_links_are_rejected(self):
        external = Path(self.temporary.name)/'outside'
        external.mkdir()
        (external/'payload').write_text('secret')
        for target in (external, external/'payload'):
            link = self.root/'guitar_learning/assets/escape'
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, '링크'):
                study_tool.prepare(self.root, self.study)
            link.unlink()
        self.assertFalse((self.study/'기준봉인.json').exists())

    def test_safe_vendor_link_is_preserved(self):
        self.write('isaacgym/python/isaacgym/lib.so.1', 'native')
        (self.root/'isaacgym/python/isaacgym/lib.so').symlink_to('lib.so.1')
        study_tool.prepare(self.root, self.study)
        frozen = self.study/'작업자료/source_snapshot/isaacgym/python/isaacgym/lib.so'
        self.assertTrue(frozen.is_symlink())
        self.assertEqual(frozen.read_text(), 'native')

    def test_concurrent_source_addition_aborts_copy(self):
        original = study_tool.copy_sources

        def changing_copy(root, destination, entries):
            original(root, destination, entries)
            self.write('guitar_learning/added.py', 'changed')

        with patch.object(study_tool, 'copy_sources', changing_copy):
            with self.assertRaisesRegex(ValueError, '복사 중'):
                study_tool.prepare(self.root, self.study)
        self.assertFalse((self.study/'기준봉인.json').exists())
        self.assertFalse((self.study/'작업자료/source_snapshot').exists())

    def test_active_changes_are_reported_but_frozen_changes_fail(self):
        study_tool.prepare(self.root, self.study)
        self.write('guitar_learning/train.py', 'new active version')
        self.write('guitar_learning/new.py', 'new active module')
        report = study_tool.check(self.root, self.study)
        self.assertTrue(report['snapshot_valid'])
        self.assertFalse(report['active_matches'])
        self.assertIn('guitar_learning/new.py', report['active_changes'])
        snapshot = self.study/'작업자료/source_snapshot'
        (snapshot/'guitar_learning/assets/extra.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, '봉인 사본 변경'):
            study_tool.check(self.root, self.study)

    def test_changed_design_or_seal_and_overwrite_are_rejected(self):
        study_tool.prepare(self.root, self.study)
        with self.assertRaisesRegex(ValueError, '덮어쓰지'):
            study_tool.prepare(self.root, self.study)
        path = self.study/'설계.json'
        original = path.read_bytes()
        design = json.loads(original)
        design['num_envs'] = 512
        path.write_text(json.dumps(design))
        with self.assertRaisesRegex(ValueError, '봉인 후 설계'):
            study_tool.check(self.root, self.study)
        path.write_bytes(original)
        seal = self.study/'기준봉인.json'
        payload = json.loads(seal.read_text())
        payload['files']['guitar_learning/train.py']['bytes'] = 100
        seal.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, '기준봉인 자체'):
            study_tool.check(self.root, self.study)

    def test_generated_outputs_bytecode_and_tests_are_not_sealed(self):
        self.write('guitar_learning/tests/test_old.py', 'not a runtime input')
        self.write('guitar_learning/__pycache__/train.pyc', 'bytecode')
        study_tool.prepare(self.root, self.study)
        snapshot = self.study/'작업자료/source_snapshot'
        for relative in ('study_outputs/학습/log.json', '.runtime/cache/generated.py',
                         'guitar_learning/__pycache__/generated.pyc'):
            path = snapshot/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('generated')
        self.assertTrue(study_tool.check(self.root, self.study)['snapshot_valid'])
        self.assertFalse((snapshot/'guitar_learning/tests').exists())


if __name__ == '__main__':
    unittest.main()
