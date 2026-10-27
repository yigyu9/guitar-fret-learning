"""Final source/raw preservation audit after both specialist runs and review."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    reports = {hand: json.loads((PHASE/(hand+'_run_v1')/'report.json').read_text()) for hand in ('left', 'right')}
    if not all(row['completed'] and row['persistent_audit']['completed'] for row in reports.values()):
        raise RuntimeError('both canonical training and persistent audits must pass')
    verification_paths = [PHASE/'learning_verification_v1.json', PHASE/'runtime_verification_v1.json']
    if not all(json.loads(p.read_text())['completed'] for p in verification_paths):
        raise RuntimeError('completed analysis checks required')
    review = PHASE/'review.md'
    if not review.is_file():
        raise RuntimeError('independent review required')
    declared = {}
    for hand in ('left', 'right'):
        for filename, sha in json.loads((PHASE/(hand+'_run_v1')/'inputs_before.json').read_text()).items():
            if filename in declared and declared[filename] != sha:
                raise RuntimeError('conflicting input SHA: '+filename)
            declared[filename] = sha
    changed_inputs = [p for p, sha in declared.items() if digest(p) != sha]
    frozen = json.loads((PHASE/'source_run_v1/manifest.json').read_text())
    changed_sources = [row['path'] for row in frozen if digest(row['path']) != row['sha256']]
    bad_snapshots = [row['snapshot'] for row in frozen if digest(row['snapshot']) != row['sha256']]
    docs = [PHASE/'README.md', PHASE/'WORK_STATE.md']
    broken = []
    for path in docs:
        for target in re.findall(r'\]\((/[^\n)]*)\)', path.read_text()):
            if not Path(re.sub(r':\d+$', '', target)).exists():
                broken.append(dict(document=str(path), target=target))
    errors = dict(changed_declared_inputs=changed_inputs, changed_frozen_sources=changed_sources,
                  bad_source_snapshots=bad_snapshots, broken_local_links=broken)
    if any(errors.values()):
        raise RuntimeError(json.dumps(errors))
    destination = PHASE/'source_final'; destination.mkdir(exist_ok=False)
    paths = {Path(row['path']) for row in frozen}
    paths.update(PHASE.glob('*.py')); paths.update(docs)
    paths.update(ROOT/'stability_adapter_2'/name for name in ('PLAN.md', 'README.md'))
    paths.update(ROOT/'guitar_learning'/name for name in ('README.md', 'SPECIALIST_TRAINING.md', 'AGENTS.md'))
    snapshots = []
    for path in sorted(paths):
        target = destination/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
        snapshots.append(dict(path=str(path), sha256=digest(path), snapshot=str(target)))
    write(destination/'manifest.json', snapshots)
    inventory = [dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))
        for path in sorted(PHASE.rglob('*')) if path.is_file() and '__pycache__' not in path.parts
        and path.name not in ('final_verification.json', 'artifact_inventory.json')]
    write(PHASE/'artifact_inventory.json', inventory)
    result = dict(completed=True, errors=errors, declared_input_count=len(declared),
        frozen_source_count=len(frozen), final_source_count=len(snapshots), artifact_count=len(inventory),
        runs={hand: dict(completed=row['completed'], updates=len(row['updates']), transitions=row['transitions'],
                        stopped=row['stopped'], wall_s=row['wall_s'], final_checkpoint_sha256=digest(PHASE/(hand+'_run_v1')/'final.pt'))
              for hand, row in reports.items()},
        review_sha256=digest(review), analysis_verification_sha256={p.name:digest(p) for p in verification_paths},
        artifact_inventory_sha256=digest(PHASE/'artifact_inventory.json'),
        scope='bounded actual specialist training and observation; not proof of architecture superiority, generalization or acoustic performance')
    write(PHASE/'final_verification.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
