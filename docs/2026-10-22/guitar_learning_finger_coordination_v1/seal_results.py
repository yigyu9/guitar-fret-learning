"""Seal current results after review; original results and sources are read-only."""
from pathlib import Path
import hashlib
import json

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            value.update(block)
    return value.hexdigest()


def main():
    target=PHASE/'result_manifest.json'
    assert not target.exists()
    source=json.loads((PHASE/'tested_source_manifest.json').read_text())['source']
    assert all(sha(Path(p))==h for p,h in source.items())
    before=json.loads((PHASE/'before_manifest.json').read_text())
    assert sha(Path(before['baseline_seal']))==before['baseline_seal_sha256']
    integrity_path=PHASE/'integrity_after.json'
    integrity=json.loads(integrity_path.read_text())
    integrity['current_documents']={str(ROOT/p):sha(ROOT/p) for p in (
        'CURRENT_STATUS.md','guitar_learning/README.md','guitar_learning/AGENTS.md',
        'docs/2026-10-26/learning_flow/README.md')}
    integrity_path.write_text(json.dumps(integrity,indent=2)+'\n')
    files={str(p.relative_to(PHASE)):dict(sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(PHASE.rglob('*')) if p.is_file() and p!=target}
    result=dict(schema='guitar_learning.finger_coordination_v1.result_manifest.v1',
        scope='All phase files excluding this manifest itself. Current active source is separately pinned; source_tested is its frozen copy. Original v4 phase remains sealed and unchanged.',
        file_count=len(files),bytes=sum(v['bytes'] for v in files.values()),files=files)
    target.write_text(json.dumps(result,indent=2)+'\n')
    assert {str(p.relative_to(PHASE)) for p in PHASE.rglob('*') if p.is_file() and p!=target}==set(files)
    assert all(sha(PHASE/p)==v['sha256'] and (PHASE/p).stat().st_size==v['bytes'] for p,v in files.items())
    print('SEALED',len(files),result['bytes'],sha(target))


if __name__=='__main__':
    main()
