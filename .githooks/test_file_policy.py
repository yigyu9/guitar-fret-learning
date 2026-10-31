#!/usr/bin/env python3
"""공유 ignore와 커밋 검사를 임시 저장소에서 검증한다. 실제 인덱스는 건드리지 않는다."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent.parent


class FilePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', self.temp.name], check=True)
        shutil.copy2(SOURCE / '.gitignore', self.root / '.gitignore')
        shutil.copytree(SOURCE / '.githooks', self.root / '.githooks',
                        ignore=shutil.ignore_patterns('__pycache__'))

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True)

    def ignored(self, name):
        return self.git('check-ignore', '--no-index', name).returncode == 0

    def check_staged(self):
        return subprocess.run(['python3', '.githooks/check-staged-files.py'],
                              cwd=self.root, capture_output=True, text=True)

    def write(self, name, content='{}'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_required_inputs_eligible(self):
        names = [
            'guitar_learning/assets/runtime_inputs/paper/initial_pose/archive/experiment_records/lower_body_release_v1/front_facing_pose_v1/source_v9/support_candidate.json',
            'guitar_learning/assets/historical_inputs/archive/objects/abc.data',
            'guitar_learning/assets/prepared_reset_v1/reset.npz',
            'guitar_learning/assets/native/body.xml',
            'guitar_learning/assets/native/mesh.stl',
            'data/song_bundles/test/events.jsonl',
            'isaacgym/python/isaacgym/_bindings/linux-x86_64/gym_38.so',
        ]
        for name in names:
            with self.subTest(name=name):
                self.write(name)
                self.assertFalse(self.ignored(name))
                self.assertEqual(self.git('add', name).returncode, 0)
        result = self.check_staged()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_generated_files_and_secrets_ignored(self):
        for name in [
            'docs/example/trace.npz', 'docs/example/raw.jsonl',
            'docs/example/raw.json.gz', 'docs/example/model.PTH',
            'docs/example/render.MP4', 'docs/example/pack.tar.xz',
            'docs/archived_research/report.json',
            'guitar_learning/archive/policy.py',
            'guitar_learning/assets/runtime_inputs/archive/run.log',
            'guitar_learning/assets/runtime_inputs/archive/__pycache__/a.pyc',
            'guitar_learning/assets/runtime_inputs/archive/.env',
            'guitar_learning/assets/checkpoints/model.json',
            'guitar_learning/AGENTS.md', '.env.production',
        ]:
            with self.subTest(name=name):
                self.assertTrue(self.ignored(name))

    def test_force_added_archive_rejected(self):
        name = 'guitar_learning/archive/old.py'
        self.write(name)
        self.assertEqual(self.git('add', '-f', name).returncode, 0)
        result = self.check_staged()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Archive directory:', result.stderr)

    def test_large_report_rejected(self):
        name = 'docs/example/report.json'
        self.write(name, ' ' * (10 * 1024 * 1024 + 1))
        self.assertEqual(self.git('add', name).returncode, 0)
        result = self.check_staged()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exceeds 10 MiB', result.stderr)

    def test_external_link_in_assets_rejected(self):
        path = self.root / 'guitar_learning/assets/runtime_inputs/archive/input.json'
        path.parent.mkdir(parents=True)
        path.symlink_to('/media/external/input.json')
        self.assertEqual(self.git('add', '-f', str(path.relative_to(self.root))).returncode, 0)
        result = self.check_staged()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('External-storage link:', result.stderr)


if __name__ == '__main__':
    unittest.main()
