"""Root-owned final preservation checks; run once after independent review."""
import hashlib
import json
import re
import shutil
from pathlib import Path

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[4]
GUITAR = ROOT/'guitar_learning'
CASES = ('fresh_reference_v1', 'reuse_repeat_v1', 'reuse_resume_v1', 'reuse_pool_v1')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    assert (PHASE/'final_review.md').is_file()
    assert read(PHASE/'analysis_verification.json')['completed']
    assert 'Ran 146 tests' in (PHASE/'cpu_tests_v2.log').read_text()
    assert (PHASE/'cpu_tests_v2.log').read_text().rstrip().endswith('OK')
    manifests = list(PHASE.glob('*/manifest.json'))
    manifests.append(GUITAR/'archive/20261018_before_persistent_reset/archive_manifest.json')
    archive_count = 0
    for manifest in manifests:
        data = read(manifest)
        rows = data.get('files', [data]) if isinstance(data, dict) else data
        for row in rows:
            path = Path(row.get('snapshot_path', row.get('archived_path', '')))
            assert path.is_file() and sha(path) == row['sha256'], str(manifest)
            archive_count += 1
    source = read(PHASE/'source_run_v1/manifest.json')
    consumed_python = [r for r in source if r['original_path'].endswith('.py')]
    assert all(sha(Path(r['original_path'])) == r['sha256'] for r in consumed_python)
    pins = {}
    for case in CASES:
        report = read(PHASE/case/'report.json')
        assert report['completed'], case
        if case != 'fresh_reference_v1':
            assert read(PHASE/case/'persistent_audit.json')['completed']
        for filename, value in read(PHASE/case/'inputs_before.json').items():
            assert filename not in pins or pins[filename] == value, filename
            pins[filename] = value
    old_run = Path(read(PHASE/'running_job_before.json')['run'])
    old_pins = read(old_run/'inputs_before.json')
    pins.update(old_pins)
    changed = [name for name, value in pins.items() if not Path(name).is_file() or sha(Path(name)) != value]
    assert not changed, changed
    write(PHASE/'running_job_after.json', dict(run=str(old_run),status=read(old_run/'status.json'),
        changed_original_inputs=[], scope='Read only; no signal or source/input mutation of the existing training job'))
    write(PHASE/'inputs_union.json', pins)
    link_errors = []
    docs = [GUITAR/'README.md', GUITAR/'PARALLEL_TRAINING.md', PHASE/'README.md', PHASE/'final_review.md']
    for doc in docs:
        for filename in re.findall(r'\]\((/[^)]+)\)', doc.read_text()):
            target = re.sub(r':\d+$', '', filename.split('#', 1)[0])
            if not Path(target).exists():
                link_errors.append(dict(document=str(doc),target=target))
    assert not link_errors, link_errors
    final = PHASE/'source_final'
    final.mkdir()
    files = sorted(set([p for p in GUITAR.rglob('*') if p.is_file() and
        not any(x in p.relative_to(GUITAR).parts for x in ('archive','__pycache__'))] +
        [PHASE/'analyze_results.py', Path(__file__).resolve(), PHASE/'README.md',
         ROOT/'stability_adapter_2/PLAN.md', ROOT/'stability_adapter_2/README.md']))
    rows = []
    for original in files:
        destination = final/original.relative_to(ROOT)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,destination)
        rows.append(dict(original_path=str(original),snapshot_path=str(destination),sha256=sha(original)))
    write(final/'manifest.json', rows)
    inventory = {str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(PHASE.rglob('*')) if p.is_file()}
    write(PHASE/'artifact_inventory.json', inventory)
    write(PHASE/'final_verification.json', dict(completed=True,cases=list(CASES),cpu_tests=146,
        preserved_snapshot_files=archive_count,consumed_python_unchanged=len(consumed_python),
        input_union_count=len(pins),changed_inputs=changed,source_final_count=len(rows),
        artifact_count=len(inventory),broken_links=link_errors,
        final_review_sha256=sha(PHASE/'final_review.md'),
        scope='Artifact inventory excludes itself and this final verification; existing live training outputs are outside the sealed phase'))


if __name__ == '__main__':
    main()
