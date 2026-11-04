"""CPU-only validation of the original compiled single right strike task."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from guitar_learning.tool.experiments.right_strike.prepare import (
    INPUT_ROOT, TARGET_SPEC, prepare, sha, validate_inputs)
from guitar_learning.tool.experiments.right_strike.settings import build_settings


class RightStrikeInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='right_strike_test_', dir=str(INPUT_ROOT))
        cls.bundle = Path(cls.temp.name)/'single_down'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.report = prepare(cls.bundle)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate_and_rehash(self, name, change):
        """Return restoration data after changing one inventoried JSON input."""
        path = self.bundle/name
        manifest_path = self.bundle/'manifest.json'
        original, manifest_original = path.read_bytes(), manifest_path.read_bytes()
        document = json.loads(original)
        change(document)
        path.write_text(json.dumps(document))
        manifest = json.loads(manifest_original)
        manifest['files'][name].update(sha256=sha(path), bytes=path.stat().st_size)
        manifest_path.write_text(json.dumps(manifest))
        return path, original, manifest_path, manifest_original

    def restore(self, data):
        path, original, manifest, manifest_original = data
        path.write_bytes(original); manifest.write_bytes(manifest_original)

    def test_actual_canonical_identity_onset_and_down_direction(self):
        task = validate_inputs(self.bundle)
        self.assertEqual(len(task.targets), 1)
        target = task.targets[0]
        self.assertEqual((target.target_id, target.string, target.fret, target.finger, target.direction),
                         ('event-000000/string-3/note-0', 2, 6, 1, 1))
        self.assertEqual((target.onset_s, target.end_s), (3., 4.2))
        self.assertEqual(task.duration_s, 5.)
        self.assertEqual(task.provenance['song']['control_ticks'], 300)
        self.assertTrue(self.report['completed'])
        self.assertFalse(self.report['code_sealed'])
        spec = json.loads((self.bundle/'right_strike_input.json').read_text())
        self.assertEqual(spec, TARGET_SPEC)
        self.assertFalse(spec['left_clean_required'])

    def test_manifest_covers_all_data_files_and_original_schemas(self):
        manifest = json.loads((self.bundle/'manifest.json').read_text())
        actual = {p.relative_to(self.bundle).as_posix() for p in self.bundle.rglob('*')
                  if p.is_file() and p.name != 'manifest.json'}
        self.assertEqual(set(manifest['files']), actual)
        self.assertEqual(len(actual), 8)
        for name, schema in [('training/fret_training.json', 'tab2body.fret_training.v1'),
                             ('training/strike_training.json', 'tab2body.strike_training.v3'),
                             ('training/strike_plan.json', 'tab2body.strike_plan.v4')]:
            self.assertEqual(json.loads((self.bundle/name).read_text())['schema'], schema)

    def test_sha_contamination_and_unlisted_file_are_rejected(self):
        path = self.bundle/'mapping/fingering.json'
        original = path.read_bytes()
        try:
            path.write_bytes(original+b' ')
            with self.assertRaisesRegex(ValueError, 'SHA/size'):
                validate_inputs(self.bundle)
        finally:
            path.write_bytes(original)
        extra = self.bundle/'unexpected.json'
        try:
            extra.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Unlisted'):
                validate_inputs(self.bundle)
        finally:
            extra.unlink()

    def test_rehashed_upstroke_and_wrong_spec_are_rejected(self):
        changes = [('training/strike_plan.json', lambda value: value['events'][0].update(direction='up')),
                   ('right_strike_input.json', lambda value: value.update(runtime_string=3)),
                   ('right_strike_input.json', lambda value: value.update(left_clean_required=True))]
        for name, change in changes:
            saved = self.mutate_and_rehash(name, change)
            try:
                with self.assertRaises(ValueError):
                    validate_inputs(self.bundle)
            finally:
                self.restore(saved)

    def test_manifest_path_escape_and_wrong_identity_are_rejected(self):
        path = self.bundle/'manifest.json'
        original = path.read_bytes()
        for change in (lambda value: value.update(song_id='other'),
                       lambda value: value['files'].update({'../escape': dict(bytes=0, sha256='0'*64)})):
            try:
                document = json.loads(original); change(document)
                path.write_text(json.dumps(document))
                with self.assertRaises(ValueError):
                    validate_inputs(self.bundle)
            finally:
                path.write_bytes(original)

    def test_existing_and_outside_output_are_refused(self):
        with self.assertRaises(FileExistsError):
            prepare(self.bundle)
        with self.assertRaises(ValueError):
            prepare(INPUT_ROOT.parent/'escaped_right_strike')

    def test_settings_keep_legacy_right_ppo_control_and_policy_contract(self):
        import torch
        from guitar_learning.training.launch import build_settings as original_settings
        settings = build_settings(self.bundle, updates=20, num_envs=4, seed=9)
        baseline = original_settings('right', learning_family='song',
            song='virtual_finger_v9_middle_s3_f6', updates=20, num_envs=4, horizon=32,
            seed=9, size='medium', device='cuda:0', physics='gpu')
        for key in set(baseline)-{'phrase_events', 'song_training'}:
            self.assertEqual(settings[key], baseline[key], key)
        self.assertEqual(settings['song_training']['bundle'], str(self.bundle.resolve()))
        self.assertEqual(settings['song_training']['target_count'], 1)
        self.assertEqual(settings['song_training']['control_ticks'], 300)
        self.assertEqual(settings['song_training']['observation_dimension'], 500)
        self.assertTrue(settings['right_strike']['reward_original'])
        self.assertFalse(settings['right_strike']['left_clean_required'])
        self.assertNotIn('finger_skill', settings)
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    unittest.main()
