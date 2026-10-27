"""Move two unopened orphan Git temporaries to verified RAM backups; preserve valid packs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

PHASE = Path(__file__).resolve().parent
PACK = PHASE.parents[2]/'.git/objects/pack'
BACKUP = Path('/dev/shm/guitar_learning_orphan_git_backup_20261022_snapshot2')
NAMES = ('tmp_pack_TPNfCE',)


def signature(path):
    value = path.stat()
    assert value.st_nlink == 1 and path.is_file() and not path.is_symlink()
    return value.st_ino, value.st_size, value.st_mtime_ns


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


def unopened(path):
    result = subprocess.run(['lsof', '-t', '--', str(path)], capture_output=True, text=True)
    assert result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip(), 'Open/unknown file use'


def main():
    total = sum(signature(PACK/name)[1] for name in NAMES)
    available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                         if line.startswith('MemAvailable:')))*1024
    assert available >= total+8*1024**3, 'Retain8GiB available host memory before training'
    assert shutil.disk_usage('/dev/shm').free >= total+1024**3, 'RAM filesystem capacity'
    BACKUP.mkdir(exist_ok=False)
    rows = []
    for name in NAMES:
        source, backup = PACK/name, BACKUP/name
        unopened(source)
        before = signature(source)
        with source.open('rb') as reader, backup.open('xb') as writer:
            value = hashlib.sha256()
            for block in iter(lambda: reader.read(1024**2), b''):
                writer.write(block)
                value.update(block)
            writer.flush()
            os.fsync(writer.fileno())
        sha = value.hexdigest()
        assert digest(source) == sha == digest(backup), 'Source/backup full SHA mismatch'
        unopened(source)
        assert signature(source) == before, 'Source changed during backup'
        row = dict(source=str(source), backup=str(backup), bytes=before[1], sha256=sha,
                   source_signature=before, storage='volatile tmpfs; survives only until reboot/removal')
        rows.append(row)
        with (PHASE/('ram_backup_before_unlink_'+name+'.json')).open('x') as stream:
            json.dump(row, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        source.unlink()
        print('Verified RAM backup and removed orphan temporary: '+name, flush=True)
    result = dict(files=rows, bytes=sum(row['bytes'] for row in rows),
                  scope='Only two unopened tmp_pack files; named packs/idx/keep/refs/index untouched',
                  memory_available_before_bytes=available,
                  local_free_after_bytes=shutil.disk_usage(PHASE).free)
    with (PHASE/'ram_git_backup_snapshot2_manifest.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
