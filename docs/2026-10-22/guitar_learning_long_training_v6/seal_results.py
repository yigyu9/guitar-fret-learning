"""Seal the completed local phase and explicitly pin its separately sealed copy target."""
import hashlib
import json
import os
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


def main():
    source = json.loads((PHASE/'training_source_manifest.json').read_text())
    assert len(source['source']) == 436
    assert all(sha(Path(p)) == h for p, h in source['source'].items())
    proof = json.loads((PHASE/'recovery_verification.json').read_text())
    assert proof['completed'] and proof['committed_updates'] == 2000
    evaluations = json.loads((PHASE/'recovery_checkpoint_evaluation.json').read_text())
    assert evaluations['completed'] and evaluations['requested_evaluations_completed']
    assert json.loads((PHASE/'media_qa.json').read_text())['completed']
    assert json.loads((PHASE/'temporary_storage_final.json').read_text())['completed']
    documents = json.loads((PHASE/'current_documents.json').read_text())
    assert all(sha(Path(p)) == h for p, h in documents['current_sha256'].items())
    assert (PHASE/'independent_final_document_review.md').is_file()
    external = json.loads((PHASE/'external_copy_seal.json').read_text())
    assert sha(Path(external['manifest'])) == external['manifest_sha256']
    alias = PHASE/'recovered_train2000_restart1'
    assert alias.is_symlink() and str(alias.resolve()) == external['directory']
    manifest_path = PHASE/'result_manifest.json'
    assert not manifest_path.exists(), 'Never overwrite a previous seal'
    entries = sorted(PHASE.rglob('*'))
    assert [p for p in entries if p.is_symlink()] == [alias], 'Unexpected symbolic link'
    paths = [p for p in entries if p.is_file() and not p.is_symlink()]
    files = {}
    for path in paths:
        before = path.stat()
        digest = sha(path)
        after = path.stat()
        assert (before.st_ino, before.st_size, before.st_mtime_ns) == (
            after.st_ino, after.st_size, after.st_mtime_ns), 'File changed while sealing'
        files[str(path.relative_to(PHASE))] = dict(bytes=after.st_size, sha256=digest)
    assert set(PHASE.rglob('*')) == set(entries), 'Phase file set changed while sealing'
    result = dict(schema='guitar_learning.long_training_v6.result_manifest.v1',
        scope='Every regular local phase file except this manifest. Directory alias is recorded separately; its target data are covered only by the separately pinned external manifest. Original external interrupted attempts are historical provenance, not recursively sealed here.',
        file_count=len(files), bytes=sum(r['bytes'] for r in files.values()), files=files,
        symlinks={alias.name: dict(target=os.readlink(alias), resolved=str(alias.resolve()),
            external_manifest=external['manifest'], external_manifest_sha256=external['manifest_sha256'])})
    with manifest_path.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(dict(completed=True, files=len(files), bytes=result['bytes'],
                         manifest_sha256=sha(manifest_path))))


if __name__ == '__main__':
    main()
