"""Relocate the inactive byte-verified copy outside Git; retain the original path alias."""
import copy
import hashlib
import json
import os
from pathlib import Path

PHASE = Path(__file__).resolve().parent
SOURCE = PHASE/'recovered_train2000_restart1'
DESTINATION = Path('/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    manifest = PHASE/'recovery_copy_manifest.json'
    previous = json.loads(manifest.read_text())
    assert previous['completed'] and Path(previous['destination']) == SOURCE
    assert SOURCE.is_dir() and not SOURCE.is_symlink() and not DESTINATION.exists()
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    assert SOURCE.stat().st_dev == DESTINATION.parent.stat().st_dev, 'Same-filesystem rename only'
    record = dict(source=str(SOURCE), destination=str(DESTINATION), source_inode=SOURCE.stat().st_ino,
                  parent_copy_manifest=str(manifest), parent_copy_manifest_sha256=digest(manifest),
                  scope='Inactive copied historical run only; active training directory unchanged')
    write(PHASE/'recovery_storage_move_before.json', record)
    os.rename(str(SOURCE), str(DESTINATION))
    try:
        SOURCE.symlink_to(DESTINATION, target_is_directory=True)
    except BaseException:
        os.rename(str(DESTINATION), str(SOURCE))
        raise
    assert SOURCE.resolve() == DESTINATION and DESTINATION.stat().st_ino == record['source_inode']
    current = copy.deepcopy(previous)
    current.update(destination=str(DESTINATION), parent_copy_manifest=str(manifest),
                   parent_copy_manifest_sha256=digest(manifest), original_alias=str(SOURCE),
                   relocation_scope='Same SSD atomic rename; original absolute alias retained by directory symlink')
    assert {p.name for p in DESTINATION.iterdir()} == set(current['files'])
    for name, row in current['files'].items():
        target = DESTINATION/name
        assert target.stat().st_size == row['bytes'] and digest(target) == row['sha256'], 'Relocated bytes differ'
        row['copy'] = str(target)
    write(PHASE/'recovery_copy_relocated_manifest.json', current)
    record.update(completed=True, files=len(current['files']), bytes=current['bytes'],
                  relocated_manifest_sha256=digest(PHASE/'recovery_copy_relocated_manifest.json'))
    write(PHASE/'recovery_storage_relocation.json', record)
    print(json.dumps(record), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
