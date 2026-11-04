"""C 번들 변환·원본 시계·factory 격리의 CPU 검사. 물리 압현 성공 검사가 아니다."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tool import prepare_press_targets as targets
from guitar_learning.song import task as task_module
from guitar_learning.gpu import environment as environment_module
from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
from guitar_learning.gpu.press_coordination import audible_sections
from guitar_learning.tool.experiments import compact_press_v5
from guitar_learning.tests.test_gpu_environment import fixture


class PressTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def clone(self, directory):
        root = Path(directory)/targets.CASES['C1']
        shutil.copytree(targets.BUNDLES/targets.CASES['C1'], root)
        return root

    def test_catalog_includes_unregistered_cases_and_rejects_unknown(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(targets, 'BUNDLES', Path(directory)):
            rows = targets.catalog()
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(not row['ready'] for row in rows))
        for value in ('C7', '../C1', '05_BN2-131-B_solo'):
            with self.assertRaises(ValueError):
                targets.check_target(value)

    def test_all_six_canonical_identity_and_source_times_preserved(self):
        for case, bundle_id in targets.CASES.items():
            root = targets.BUNDLES/bundle_id
            original = json.loads((targets.ORIGINALS/f'{case}.fingering.json').read_text())
            canonical = targets.BASE_TASK_FACTORY(root)
            adapted = targets.source_clock_task(root)
            report = targets.check_target(case)
            self.assertEqual(report['target_count'], 20)
            self.assertEqual(report['canonical_event_count'], 15)
            self.assertEqual(report['adjusted_note_count'], 10)
            self.assertEqual(report['policy_duration_s'], 47.25)
            self.assertEqual(report['control_ticks'], 2835)
            self.assertTrue(report['p7_preserved'] and report['p9_unmerged'])
            self.assertEqual([t.target_id for t in adapted.targets], [t.target_id for t in canonical.targets])
            for before, after, row in zip(canonical.targets, adapted.targets, adapted.provenance['song']['schedule']):
                note = original['notes'][row['mapping_note_index']]
                self.assertEqual(after.onset_s, note['t_on']+3.)
                self.assertEqual(after.source_onset_s, note['t_on'])
                self.assertEqual((after.string,after.fret,after.finger), (5-note['string'],note['fret'],note['finger']))
                self.assertEqual((before.press_s,before.end_s,before.event_id,before.direction),
                                 (after.press_s,after.end_s,after.event_id,after.direction))
            for suffix in ('fingering.json', 'notes.csv', 'chords.json'):
                name = case+'.'+suffix
                self.assertEqual((root/'source/original'/name).read_bytes(), (targets.ORIGINALS/name).read_bytes())

    def test_self_contained_copy_checks_without_original_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            self.clone(directory)
            with patch.object(targets, 'BUNDLES', Path(directory)), patch.object(targets, 'ORIGINALS', Path(directory)/'missing'):
                self.assertTrue(targets.check_target('C1')['completed'])

    def test_prepare_uses_official_builders_and_never_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(targets, 'BUNDLES', Path(directory)):
            report = targets.prepare_target('C1')
            self.assertTrue(report['completed'])
            root = Path(report['bundle'])
            before = {path.relative_to(root):path.read_bytes() for path in root.rglob('*') if path.is_file()}
            with self.assertRaises(FileExistsError):
                targets.prepare_target('C1')
            self.assertEqual(before, {path.relative_to(root):path.read_bytes() for path in root.rglob('*') if path.is_file()})

    def test_tampered_preserved_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.clone(directory)
            with (root/'source/original/C1.notes.csv').open('ab') as stream:
                stream.write(b'changed')
            with patch.object(targets, 'BUNDLES', Path(directory)), self.assertRaisesRegex(ValueError, 'SHA'):
                targets.check_target('C1')

    def test_missing_original_key_rejected_even_with_updated_clock_manifest_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.clone(directory)
            clock_path = root/'left_press_clock.json'
            clock = json.loads(clock_path.read_text())
            clock['original_sha256'] = {}
            clock_path.write_text(json.dumps(clock))
            manifest_path = root/'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['files']['left_press_clock.json'] = dict(bytes=clock_path.stat().st_size,
                sha256=hashlib.sha256(clock_path.read_bytes()).hexdigest())
            manifest_path.write_text(json.dumps(manifest))
            with patch.object(targets, 'BUNDLES', Path(directory)), self.assertRaisesRegex(ValueError, '3개'):
                targets.check_target('C1')

    def test_runtime_patches_both_aliases_and_restores_on_success_exception_and_nested_error(self):
        before = (task_module.make_task, environment_module.make_task)
        with targets.source_clock_runtime():
            self.assertIs(task_module.make_task, targets.source_clock_task)
            self.assertIs(environment_module.make_task, targets.source_clock_task)
            with self.assertRaises(RuntimeError):
                with targets.source_clock_runtime():
                    pass
        self.assertEqual((task_module.make_task,environment_module.make_task),before)
        with self.assertRaisesRegex(ValueError, 'test exception'):
            with targets.source_clock_runtime():
                raise ValueError('test exception')
        self.assertEqual((task_module.make_task,environment_module.make_task),before)
        with patch.object(task_module, 'make_task', lambda *args,**kwargs: None):
            with self.assertRaises(RuntimeError):
                with targets.source_clock_runtime():
                    pass
        self.assertEqual((task_module.make_task,environment_module.make_task),before)

    def test_settings_environment_catalog_coordination_and_provenance_use_adapted_task(self):
        root = targets.BUNDLES/targets.CASES['C1']
        with targets.source_clock_runtime():
            settings = compact_press_v5.build_settings(song=root.name, num_envs=2, updates=1,
                device='cuda:0', physics='gpu')
            compact_press_v5.validate_settings(settings)
            metadata, snapshot = fixture(2)
            env = CompactPressV5Environment(metadata, bundle=root, song=settings['song'],
                skill=settings['finger_skill'], device='cpu')
            env.set_evaluation(True, full_song=True)
            observation = env.reset(range(2), snapshot)
        self.assertEqual(observation['state'].shape, (2,464))
        self.assertEqual(observation['priority_events'].shape, (2,8,26))
        clock = env.contract['task']['provenance']['left_press_clock']
        report = targets.check_target('C1')
        for key in ('bundle_id','clock_contract_sha256','onset_mapping_sha256'):
            self.assertEqual(clock[key],report[key])
        self.assertEqual(clock['schema'], targets.SCHEMA)
        expected = audible_sections(env.task.targets,[True]*20)
        self.assertEqual(env.coordination_groups[0],expected)
        self.assertEqual(len(env.catalog.source_targets),20)
        self.assertEqual(settings['song_training']['control_ticks'],2835)
        self.assertEqual(settings['song_training']['episode_duration_s'],47.25)
        compact_press_v5.validate_contract(settings,env.contract)
        self.assertTrue(any(group['start_s']==7.25 for group in env.coordination_groups[0]))


if __name__=='__main__':
    unittest.main()
