import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare


class PrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='prepare_test_', dir=str(prepare.STUDY))
        cls.out = Path(cls.temp.name) / 'bundles'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.report = prepare.build(cls.out)
        cls.cases = prepare.load_cases()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_matrix_and_complete_shared_window(self):
        self.assertEqual(len(self.report['rows']), 6)
        for case in self.cases:
            task = prepare.task_for_case(case, self.out / case['case_id'])
            self.assertEqual(len(task.targets), 2)
            self.assertEqual(len({t.string for t in task.targets}), 2)
            self.assertEqual(len({t.finger for t in task.targets}), 2)
            self.assertEqual(task.provenance['song']['source_note_count'], 2)
            self.assertTrue(task.provenance['song']['coverage']['complete'])
            self.assertLessEqual(max(t.onset_s for t in task.targets), 3.3)
            self.assertGreaterEqual(min(t.end_s for t in task.targets), 4.8)
            self.assertEqual(task.duration_s, 5.5)

    def test_settings_use_actual_bundle_and_keep_current_defaults(self):
        import torch
        from guitar_learning.training.launch import settings_document
        case = self.cases[0]
        settings = prepare.make_settings(case, self.out / case['case_id'])
        baseline = settings_document('left', song='virtual_finger_v9_middle_s3_f6',
            updates=100, num_envs=64, horizon=32, size='medium', seed=7,
            device='cuda:0', physics='gpu')
        for key in ('ppo', 'song', 'initial_std', 'finger_skill', 'physics_backend'):
            self.assertEqual(settings[key], baseline[key])
        self.assertEqual(settings['ppo']['actor_lr'], 3e-5)
        self.assertEqual(settings['song_training']['target_count'], 2)
        self.assertEqual(settings['song_training']['control_ticks'], 330)
        self.assertEqual(settings['song_training']['bundle'],
                         str((self.out / case['case_id']).resolve()))
        self.assertEqual(settings['song_training']['observation_dimension'], 557)
        self.assertFalse(torch.cuda.is_initialized())

    def test_existing_output_refused(self):
        with self.assertRaises(FileExistsError):
            prepare.build(self.out)

    def test_output_outside_study_refused(self):
        with self.assertRaises(ValueError):
            prepare.build(Path(self.temp.name).parent.parent / 'escaped_bundles')

    def test_wrong_case_identity_refused(self):
        with self.assertRaises(ValueError):
            prepare.task_for_case(self.cases[1], self.out / self.cases[0]['case_id'])

    def test_same_string_and_nonadjacent_fingers_refused(self):
        for key, value in (('string', 2), ('finger_id', 4)):
            case = copy.deepcopy(self.cases[0])
            case['targets'][1][key] = value
            with self.assertRaises(ValueError):
                prepare.validate_case(case)

    def test_manifest_audio_tamper_refused(self):
        case = self.cases[0]
        path = self.out / case['case_id'] / 'source/audio.wav'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'changed')
            with self.assertRaises(ValueError):
                prepare.task_for_case(case, path.parents[1])
        finally:
            path.write_bytes(original)

    def test_manifest_mapping_tamper_refused(self):
        case = self.cases[0]
        path = self.out / case['case_id'] / 'mapping/fingering.json'
        original = path.read_bytes()
        try:
            document = json.loads(original)
            document['notes'][0]['fret'] = 9
            path.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                prepare.task_for_case(case, path.parents[1])
        finally:
            path.write_bytes(original)

    def test_all_pins_match_and_tamper_is_rejected(self):
        prepare.verify_pins(self.report['source_sha256'])
        prepare.verify_pins(self.report['output_sha256'])
        path = Path(self.temp.name) / 'pin_test.txt'
        path.write_text('original')
        pins = {str(path): prepare.sha(path)}
        path.write_text('changed')
        with self.assertRaises(ValueError):
            prepare.verify_pins(pins)


if __name__ == '__main__':
    unittest.main()
