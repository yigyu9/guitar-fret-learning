"""Historical gates verify their exact internal bytes without legacy access."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from guitar_learning import historical_inputs as historical

ROOT = Path(__file__).resolve().parents[2]


class HistoricalInputTests(unittest.TestCase):
    def test_external_cas_index_and_objects_are_rejected_before_read(self):
        source = str(ROOT / 'tab2body/full/events.py')
        sha = historical._index()[source]['default_sha256']
        with tempfile.TemporaryDirectory(dir=ROOT) as inside, tempfile.TemporaryDirectory() as outside:
            store = Path(inside)
            external = Path(outside) / 'unreadable.data'
            # 링크 목적지는 존재하지 않아도 파일 열기보다 경로 거부가 먼저여야 한다.
            (store / 'objects').mkdir()
            (store / 'objects' / (sha + '.data')).symlink_to(external)
            with patch.object(historical, '_STORE', store):
                with self.assertRaisesRegex(ValueError, 'outside project'):
                    historical.fingerprint_paths({source: sha})
                (store / 'index.json').symlink_to(external)
                # 이미 캐시한 정상 index를 지우지 않고 실제 로더의 경로 검사를 실행한다.
                with self.assertRaisesRegex(ValueError, 'outside project'):
                    historical._index.__wrapped__()

    def test_sealed_removed_and_changed_versions_verify_without_archive_reads(self):
        # 외장 보관 manifest 대신 내부 CAS에 봉인된 동일 식별자의 모든 버전을 검증한다.
        entries = historical._index()
        removed = str(ROOT / 'guitar_learning/audit_musical_quality_v1.py')
        changed = str(ROOT / 'guitar_learning/train_parallel.py')
        current = ROOT / 'guitar_learning/training/runner.py'
        self.assertIn(removed, entries)
        self.assertIn(changed, entries)
        versions = [(source, sha) for source in (removed, changed)
                    for sha in entries[source]['versions']]
        self.assertFalse(Path(removed).exists())
        self.assertTrue(all(hashlib.sha256(current.read_bytes()).hexdigest() != sha
                            for source, sha in versions if source == changed))
        original = Path.open

        def deny_original(path, *args, **kwargs):
            if (str(path).startswith(str(ROOT / 'guitar_learning/archive') + '/')
                    or str(path) in (removed, changed)):
                raise AssertionError('historical verification read an archived or changed program')
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', deny_original):
            for source, sha in versions:
                expected = {source: sha}
                self.assertEqual(historical.fingerprint_paths(expected), expected)

    def test_all_sealed_legacy_versions_preserve_identifiers_with_roots_denied(self):
        # 외장 실험 목록 대신 내부 CAS의 모든 legacy 경로·버전 쌍을 검증한다.
        # 식별자와 예상 SHA는 index 원문 그대로 유지한다.
        legacy_prefixes = tuple(str(ROOT / name) + '/' for name in ('tab2body', 'stability_adapter_2'))
        manifests = [{source: sha} for source, entry in historical._index().items()
                     if source.startswith(legacy_prefixes) for sha in entry['versions']]
        self.assertTrue(manifests)
        forbidden = [str(ROOT / name) + '/' for name in (
            'tab2body', 'stability_adapter_2', 'guitar_learning/archive')]
        original_open, original_stat, original_lstat = Path.open, Path.stat, Path.lstat

        def guard(original):
            def checked(path, *args, **kwargs):
                if str(path).startswith(tuple(forbidden)):
                    raise AssertionError('historical verification accessed an external source: ' + str(path))
                return original(path, *args, **kwargs)
            return checked

        with patch.object(Path, 'open', guard(original_open)), \
                patch.object(Path, 'stat', guard(original_stat)), \
                patch.object(Path, 'lstat', guard(original_lstat)):
            for manifest in manifests:
                self.assertEqual(historical.fingerprint_paths(manifest), manifest)
            legacy = str(ROOT / 'tab2body/full/events.py')
            registered = historical._index()[legacy]['default_sha256']
            self.assertEqual(historical.fingerprint_paths([legacy]), {legacy: registered})

    def test_historical_guitar_learning_version_does_not_read_current_implementation(self):
        source = str(ROOT / 'guitar_learning/music_task.py')
        versions = historical._index()[source]['versions']
        current_sha = hashlib.sha256((ROOT / 'guitar_learning/song/task.py').read_bytes()).hexdigest()
        old_sha = next(sha for sha in versions if sha != current_sha)
        self.assertNotEqual(current_sha, old_sha)
        original = Path.open

        def deny_current(path, *args, **kwargs):
            if str(path) == source:
                raise AssertionError('read current source for a historical pin')
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', deny_current):
            self.assertEqual(historical.fingerprint_paths({source: old_sha}), {source: old_sha})

    def test_live_fingerprints_and_exact_mapping_verification(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            path = Path(folder) / 'live.txt'
            path.write_bytes(b'current program')
            expected = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()}
            self.assertEqual(historical.fingerprint_paths([path]), expected)
            self.assertEqual(historical.fingerprint_paths(expected), expected)
            path.write_bytes(b'changed current program')
            with self.assertRaisesRegex(RuntimeError, 'live input SHA mismatch'):
                historical.fingerprint_paths(expected)
            self.assertNotEqual(historical.fingerprint_paths([path]), expected)

    def test_unknown_legacy_and_unknown_version_never_read_original(self):
        source = str(ROOT / 'tab2body/full/events.py')
        original = Path.open

        def deny_legacy(path, *args, **kwargs):
            if str(path).startswith(str(ROOT / 'tab2body') + '/'):
                raise AssertionError('fell back to old source')
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', deny_legacy):
            for paths in ([str(ROOT / 'tab2body/unknown.py')], {source: '0' * 64}):
                with self.assertRaisesRegex(ValueError, 'unknown'):
                    historical.fingerprint_paths(paths)
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                historical.fingerprint_paths({source: 'invalid'})

    def test_evidence_paths_pin_consumed_data_without_replacing_current_code(self):
        source = str(ROOT / 'guitar_learning/music_task.py')
        sha = next(iter(historical._index()[source]['versions']))
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            live = Path(folder) / 'current.txt'
            live.write_bytes(b'current input')
            expected = {source: sha, str(live): hashlib.sha256(live.read_bytes()).hexdigest()}
            before = dict(expected)
            live_only = {str(live): expected[str(live)]}
            self.assertEqual(historical.evidence_input_paths(live_only), {live})
            self.assertEqual(historical.evidence_input_pins(live_only), live_only)
            required = historical.evidence_input_pins(expected)
            self.assertEqual(required, {
                str(live): expected[str(live)],
                str(historical._STORE / 'index.json'): hashlib.sha256(
                    (historical._STORE / 'index.json').read_bytes()).hexdigest(),
                str(historical._STORE / 'objects' / (sha + '.data')): sha})
            paths = historical.evidence_input_paths(expected)
            self.assertEqual(paths, {live, historical._STORE / 'index.json',
                                    historical._STORE / 'objects' / (sha + '.data')})
            self.assertNotIn(Path(source), paths)
            self.assertEqual(expected, before)
            live.write_bytes(b'changed current input')
            self.assertEqual(required[str(live)], expected[str(live)])
            with self.assertRaisesRegex(RuntimeError, 'live input SHA mismatch'):
                historical.fingerprint_paths(required)
            with self.assertRaisesRegex(RuntimeError, 'live input SHA mismatch'):
                historical.evidence_input_paths(expected)

    def test_preserved_bytes_are_rehashed_on_every_call_and_corruption_fails(self):
        source = str(ROOT / 'tab2body/full/events.py')
        sha = historical._index()[source]['default_sha256']
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            store = Path(folder); (store / 'objects').mkdir()
            target = store / 'objects' / (sha + '.data')
            original = historical._STORE / 'objects' / (sha + '.data')
            target.write_bytes(original.read_bytes())
            with patch.object(historical, '_STORE', store):
                self.assertEqual(historical.fingerprint_paths({source: sha}), {source: sha})
                target.write_bytes(b'tampered sealed source')
                with self.assertRaisesRegex(RuntimeError, 'historical input SHA mismatch'):
                    historical.fingerprint_paths({source: sha})
                target.unlink()
                with self.assertRaises(FileNotFoundError):
                    historical.fingerprint_paths({source: sha})


if __name__ == '__main__':
    unittest.main()
