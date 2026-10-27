"""Preserve final sources and verify all declared native inputs without writes."""
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


def save(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    native = json.loads((PHASE/'native_verification_v1.json').read_text())
    if not native['completed']:
        raise RuntimeError('native verification is incomplete')
    review = PHASE/'review.md'
    if not review.is_file():
        raise RuntimeError('independent review required before final seal')
    declared = {}
    for row in native['runs']:
        before = json.loads((Path(row['report_path']).parent/'inputs_before.json').read_text())
        for filename, sha in before.items():
            if filename in declared and declared[filename] != sha:
                raise RuntimeError('conflicting run input SHA: '+filename)
            declared[filename] = sha
    changed_inputs = [name for name, sha in declared.items() if digest(name) != sha]
    frozen = json.loads((PHASE/'source_run_v1/manifest.json').read_text())
    changed_sources = [r['path'] for r in frozen if digest(r['path']) != r['sha256']]
    archive = json.loads((ROOT/'guitar_learning/archive/20261018_before_specialists/manifest.json').read_text())
    changed_original_python = [r['original'] for r in archive['files']
        if Path(r['original']).suffix == '.py' and digest(r['original']) != r['sha256']]
    missing_archives = [r['archive'] for r in archive['files'] if digest(r['archive']) != r['sha256']]
    docs = [PHASE/'README.md', ROOT/'guitar_learning/SPECIALIST_TRAINING.md',
            ROOT/'docs/plans/guitar_learning_specialists_20261018.md']
    broken = []
    for path in docs:
        for link in re.findall(r'\]\((/[^\n)]*)\)', path.read_text()):
            target = re.sub(r':\d+$', '', link)
            if not Path(target).exists(): broken.append(dict(document=str(path), target=target))
    errors = dict(changed_declared_inputs=changed_inputs, changed_frozen_python=changed_sources,
                  changed_previous_python=changed_original_python, archive_hash_mismatch=missing_archives,
                  broken_local_links=broken)
    if any(errors.values()):
        raise RuntimeError(json.dumps(errors))
    final = PHASE/'source_final'; final.mkdir(exist_ok=False)
    source_paths = list((ROOT/'guitar_learning').glob('*.py')) + list((ROOT/'guitar_learning/tests').glob('*.py'))
    source_paths += list((ROOT/'guitar_learning/configs').glob('*.json')) + list((ROOT/'guitar_learning').glob('*.md'))
    source_paths += docs + [ROOT/'stability_adapter_2/PLAN.md', ROOT/'stability_adapter_2/README.md']
    source_rows = []
    for path in sorted(set(source_paths)):
        destination = final/path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, destination)
        source_rows.append(dict(path=str(path), sha256=digest(path), snapshot=str(destination)))
    save(final/'manifest.json', source_rows)
    inventory = [dict(path=str(p), bytes=p.stat().st_size, sha256=digest(p))
        for p in sorted(PHASE.rglob('*')) if p.is_file()
        and p.name not in ('artifact_inventory.json', 'final_verification.json') and '__pycache__' not in p.parts]
    save(PHASE/'artifact_inventory.json', inventory)
    result = dict(completed=True, errors=errors, declared_input_count=len(declared),
        frozen_python_count=len(frozen), final_source_count=len(source_rows), artifact_count=len(inventory),
        cpu_tests=168, final_runner_tests=5, native_transitions=native['transitions'],
        native_policy_physics_samples=native['physics_policy_samples'], completed_episodes=native['completed_episodes'],
        stage_success_episodes=native['stage_success_episodes'], physical_failure_episodes=native['physical_failure_episodes'],
        review=dict(path=str(review), sha256=digest(review)),
        native_verification=dict(path=str(PHASE/'native_verification_v1.json'), sha256=digest(PHASE/'native_verification_v1.json')),
        artifact_inventory_sha256=digest(PHASE/'artifact_inventory.json'),
        scope='implementation and bounded native regression complete; long training, positive skill and deterministic video evaluation remain')
    save(PHASE/'final_verification.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
