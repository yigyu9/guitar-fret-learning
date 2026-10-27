"""Copy the stopped run to ext4, preserving original bytes and recording relocation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

PHASE = Path(__file__).resolve().parent
SOURCE = Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long/train2000_restart1')
DESTINATION = PHASE/'recovered_train2000_restart1'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


def signature(path):
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns


def main():
    DESTINATION.mkdir(exist_ok=False)
    names = sorted(os.listdir(str(SOURCE)))
    priority = {'checkpoint_001299.pt': 0, 'settings.json': 1, 'inputs_before.json': 2,
                'training_contract.json': 3, 'initial.pt': 4}
    names.sort(key=lambda name: (priority.get(name, 5), name))
    result = dict(schema='guitar_learning.relocated_run_copy.v1', source=str(SOURCE),
                  destination=str(DESTINATION), completed=False, files={}, errors=[],
                  scope='Byte copy only; original run/files/pins unchanged; no claim of final training completion')
    with (PHASE/'recovery_copy_records.jsonl').open('x') as records:
        for number, name in enumerate(names, 1):
            source, destination = SOURCE/name, DESTINATION/name
            temporary = DESTINATION/(name+'.copying')
            for attempt in range(1, 5):
                try:
                    assert not source.is_symlink() and source.is_file(), 'Expected regular run file'
                    before = signature(source)
                    free = shutil.disk_usage(DESTINATION).free
                    if free < before[1]+2*1024**3:
                        raise RuntimeError('Local disk would fall below2GiB')
                    with source.open('rb') as reader, temporary.open('xb') as writer:
                        value = hashlib.sha256()
                        for block in iter(lambda: reader.read(1024**2), b''):
                            writer.write(block)
                            value.update(block)
                        writer.flush()
                        os.fsync(writer.fileno())
                    checksum = value.hexdigest()
                    assert signature(source) == before, 'Source metadata changed during copy'
                    assert digest(source) == checksum == digest(temporary), 'Full byte SHA mismatch'
                    assert signature(source) == before, 'Source metadata changed during verification'
                    os.link(str(temporary), str(destination))
                    temporary.unlink()
                    row = dict(source=str(source), copy=str(destination), sha256=checksum,
                               bytes=before[1], source_signature=before, attempts=attempt)
                    result['files'][name] = row
                    records.write(json.dumps(dict(file=name, **row))+'\n')
                    records.flush()
                    os.fsync(records.fileno())
                    break
                except OSError as error:
                    result['errors'].append(dict(file=name, attempt=attempt, error=str(error)))
                    if temporary.exists():
                        temporary.unlink()
                    if attempt == 4:
                        print('UNREADABLE '+name+': '+str(error), flush=True)
                    else:
                        time.sleep(.25)
            if number % 100 == 0 or number <= 5:
                print('Copied %d/%d; verified bytes %d' %
                      (len(result['files']), len(names), sum(v['bytes'] for v in result['files'].values())), flush=True)
        result['completed'] = set(result['files']) == set(names) == set(os.listdir(str(SOURCE)))
        result['bytes'] = sum(v['bytes'] for v in result['files'].values())
        output = PHASE/('recovery_copy_manifest.json' if result['completed'] else 'recovery_copy_failed_manifest.json')
        with output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    print(json.dumps(dict(completed=result['completed'], files=len(result['files']),
                          bytes=result['bytes'], errors=len(result['errors']))), flush=True)
    return 0 if result['completed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
