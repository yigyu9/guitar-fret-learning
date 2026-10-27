"""Release this run's verified volatile Git cache and restore its two temporary keys."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
BACKUP = Path('/dev/shm/guitar_learning_orphan_git_backup_20261022_snapshot2')


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


def save(name, value):
    with (PHASE/name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    manifest_path = PHASE/'ram_git_backup_snapshot2_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    rows = manifest['files']
    assert len(rows) == 1 and rows[0]['backup'] == str(BACKUP/'tmp_pack_TPNfCE')
    assert rows[0]['bytes'] == 3644790537
    assert rows[0]['sha256'] == '6c547e2c6fd00336517cde4440a93880900004a39c9d3ff6bdb8aff8d07cb153'
    assert not BACKUP.is_symlink() and sorted(p.name for p in BACKUP.iterdir()) == ['tmp_pack_TPNfCE']
    backup = Path(rows[0]['backup'])
    assert backup.is_file() and not backup.is_symlink() and backup.stat().st_nlink == 1
    signature = (backup.stat().st_ino, backup.stat().st_size, backup.stat().st_mtime_ns)
    assert signature[1] == rows[0]['bytes'] and sha(backup) == rows[0]['sha256']
    opened = subprocess.run(['lsof', '-t', '--', str(backup)], capture_output=True, text=True)
    assert opened.returncode == 1 and not opened.stdout.strip() and not opened.stderr.strip()
    log = PHASE/'git_connectivity_final.log'
    with log.open('x') as stream:
        result = subprocess.run(['git', 'fsck', '--connectivity-only'], cwd=ROOT,
                                stdout=stream, stderr=subprocess.STDOUT)
    assert result.returncode == 0, 'Keep the cache if reachable Git objects do not verify'
    save('temporary_cache_release_before.json', dict(files=rows,
         manifest_sha256=sha(manifest_path), connectivity_exit_code=result.returncode,
         connectivity_log_sha256=sha(log), scope='Only this run-created volatile orphan cache; no training data or Git objects'))
    assert signature == (backup.stat().st_ino, backup.stat().st_size, backup.stat().st_mtime_ns)
    backup.unlink()
    BACKUP.rmdir()
    restored = []
    original = json.loads((PHASE/'git_maintenance_before.json').read_text())
    assert [(r['key'], r['previous'], r['temporary']) for r in original['keys']] == [
        ('gc.auto', None, '0'), ('maintenance.auto', None, 'false')]
    for row in original['keys']:
        command = ['git', 'config', '--local', '--get-all', row['key']]
        current = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert current.returncode in (0, 1), 'Cannot read local Git key'
        values = current.stdout.splitlines()
        changed = values == [row['temporary']]
        removed = False
        if changed:
            deletion = subprocess.run(['git', 'config', '--local', '--unset-all',
                                       row['key'], '^'+row['temporary']+'$'], cwd=ROOT)
            assert deletion.returncode in (0, 5), 'Cannot remove the expected temporary value'
            removed = deletion.returncode == 0
        after = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert after.returncode in (0, 1)
        restored.append(dict(key=row['key'], before=values, expected_value_removed=removed,
                             restored_to_absent=removed and not after.stdout.splitlines(),
                             after=after.stdout.splitlines(),
                             scope='Deletion matches only the expected temporary value; other values are preserved'))
    save('temporary_storage_final.json', dict(completed=True,
         released_volatile_cache_bytes=rows[0]['bytes'], backup_absent=not BACKUP.exists(),
         git_keys=restored, connectivity_exit_code=0,
         scope='Reachable Git connectivity only; valid packs/refs/index and training data untouched. Scoped training-output ignores retained.'))
    print('Temporary cache released; Git keys restored or later user changes preserved.')


if __name__ == '__main__':
    main()
