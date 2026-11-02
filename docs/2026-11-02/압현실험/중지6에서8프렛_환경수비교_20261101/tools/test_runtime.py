"""새 6→8 과제의 시간표·입력 봉인·기존 제어 유지 계약을 CPU에서 검사한다."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('middle_f68_runtime', HERE/'runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
spec = importlib.util.spec_from_file_location('middle_f68_prepare', HERE/'prepare_targets.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class RuntimeContractTests(unittest.TestCase):
    def setUp(self):
        self.settings = runtime.build_settings()

    def test_distinct_goals_and_timing(self):
        sequence = runtime.validate(self.settings)
        self.assertEqual([(r['string_index'], r['fret'], r['finger'], r['onset_s'], r['end_s'])
                          for r in sequence['schedule']], [(2, 6, 2, 3., 4.5), (2, 8, 2, 5.25, 6.75)])
        self.assertEqual(sequence['duration_s'], 7.25)
        self.assertEqual(prepare.SONG, runtime.SONG)
        self.assertEqual([n['fret'] for n in prepare.fingering(.75)['notes']], [6, 8])
        self.assertNotEqual(runtime.SCHEMA, 'guitar_learning.transition_diagnosis.v3')
        self.assertNotEqual(runtime.TransitionPolicy.schema, 'guitar_learning.transition_diagnosis_policy.v3')

    def test_training_environment_counts_preserve_algorithm(self):
        for count in (256, 512, 1024):
            current = runtime.build_settings(num_envs=count)
            self.assertEqual(current['num_envs'], count)
            self.assertEqual(current['ppo'], self.settings['ppo'])
            self.assertEqual(current['natural_press'], self.settings['natural_press'])
            self.assertEqual(current['horizon'], 32)
            self.assertEqual(current['size'], 'large')
            runtime.validate(current)

    def test_geometry_and_bundle_hashes_are_actual_bytes(self):
        for name, expected in self.settings['transition']['bundle_files'].items():
            self.assertEqual(hashlib.sha256((runtime.ROOT/name).read_bytes()).hexdigest(), expected)
        bias = self.settings['natural_press']
        self.assertEqual(runtime.natural.digest(bias['geometry']), bias['geometry_sha256'])
        self.assertEqual(runtime.natural.digest(runtime.BASE/'geometry/initial_provenance.json'), bias['provenance_sha256'])
        self.assertEqual(len(bias['active_axes']), 16)
        self.assertFalse(self.settings['transition']['thumb_active'])

    def test_old_target_or_schema_is_rejected(self):
        for change in ('fret', 'schema'):
            settings = copy.deepcopy(self.settings)
            if change == 'fret':
                settings['transition']['schedule'][1]['fret'] = 7
            else:
                settings['transition']['schema'] = 'guitar_learning.transition_diagnosis.v3'
            with self.assertRaisesRegex(ValueError, '시간표/입력 SHA'):
                runtime.validate(settings)

    def test_modified_bundle_pin_is_rejected(self):
        settings = copy.deepcopy(self.settings)
        name = next(iter(settings['transition']['bundle_files']))
        settings['transition']['bundle_files'][name] = '0'*64
        with self.assertRaises(ValueError):
            runtime.validate(settings)

    def test_modified_initial_contract_is_rejected(self):
        settings = copy.deepcopy(self.settings)
        settings['natural_press']['finger_initial_std'] = .2
        with self.assertRaisesRegex(ValueError, '초기 bias'):
            runtime.validate(settings)

    def test_wrong_actual_training_bundle_is_rejected(self):
        settings = copy.deepcopy(self.settings)
        settings['song_training']['bundle'] = str(runtime.ROOT/'data/song_bundles/virtual_middle_s3_f6_f7_AB_v2')
        with self.assertRaisesRegex(ValueError, '실제 학습 음열'):
            runtime.validate(settings)

    def test_current_source_and_runtime_are_pinned(self):
        from guitar_learning.training import finger_skill_runner as runner
        with tempfile.TemporaryDirectory(prefix='f68_cpu_pins_', dir=runtime.ROOT/'.runtime/cache') as directory:
            out = Path(directory)
            (out/'settings.json').write_text(json.dumps(self.settings))
            original = runner._pins
            with runtime.transition_runtime(self.settings):
                pins = runner._pins(self.settings, out)
            self.assertIs(runner._pins, original)
            for path in (HERE/'runtime.py', runtime.ROOT/'guitar_learning/training/ppo.py',
                         runtime.ROOT/'guitar_learning/gpu/finger_skill_environment.py',
                         runtime.BASE/'geometry/initial_catalog.json'):
                self.assertEqual(pins[str(path.resolve())], runtime.natural.digest(path))


if __name__ == '__main__':
    unittest.main()
