"""Verify all historical attempts against their actual source versions."""
import ast
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
PACKAGE = ROOT/'guitar_learning'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert load(PHASE/'verification.json')['completed']
baseline = load(ROOT/'docs/2026-10-21/guitar_learning_gpu_contact_fix_v1/source_manifest.json')['after']
old_python = {p: value for p, value in baseline.items() if p.endswith('.py')}
current_python = sorted(p for p in PACKAGE.rglob('*.py') if 'archive' not in p.relative_to(PACKAGE).parts)
assert {str(p) for p in current_python} == set(old_python)
changed = sorted(str(Path(p).relative_to(PACKAGE)) for p, value in old_python.items() if sha(Path(p)) != value)
assert changed == sorted(['training/gpu_runner.py', 'training/start.py', 'training/ppo.py',
                          'training/ppo_diagnostics.py', 'tests/test_gpu_training.py', 'tests/test_ppo_logging.py']), changed
for p in current_python:
    ast.parse(p.read_bytes(), filename=str(p))
protected = ['music_task.py', 'song/task.py', 'song/__init__.py']
assert all(sha(PACKAGE/rel) == old_python[str(PACKAGE/rel)] for rel in protected)
assert all(sha(p) == old_python[str(p)] for p in current_python if p.relative_to(PACKAGE).parts[0] == 'native')
archives = {}
for name in ['20261021_before_gpu_long_run_check_v1', '20261021_before_ppo_batched_diagnostics_v1']:
    archive = PACKAGE/'archive'/name
    manifest = load(archive/'manifest.json')['files']
    for original, value in manifest.items():
        assert sha(archive/Path(original).relative_to(PACKAGE)) == value
    archives[name] = len(manifest)

attempts = []
for name, snapshot in [
    ('train1024_large_70', 'source_before_cuda_cache_release'),
    ('train1024_large_64_cache_v2', 'source_before_optimizer_cache_release'),
    ('train1024_large_64_cache_v3', 'source_before_batched_ppo_evaluation'),
    ('train1024_large_64_batched_v4', None),
    ('train512_large_128_v5', None),
    ('resume512_after_inspection', None),
]:
    report = load(PHASE/name/'report.json')
    pins = load(PHASE/name/'inputs_before.json')
    for original, value in pins.items():
        actual = Path(original)
        if snapshot and ROOT in actual.parents:
            saved = PHASE/snapshot/actual.relative_to(ROOT)
            if saved.exists():
                actual = saved
        assert sha(actual) == value, (name, original)
    attempts.append(dict(run=name, completed=report['completed'], optimizer_updates=report['optimizer_updates'],
                         committed_transitions=report['transitions'], stopped=report['stopped'],
                         failure_type=report['failure']['type'] if report['failure'] else None,
                         source_snapshot=snapshot or 'source_final', input_pins_verified=len(pins)))
assert [a['completed'] for a in attempts] == [False, False, False, False, False, True]

files = current_python + [PACKAGE/'README.md', PACKAGE/'AGENTS.md', ROOT/'CURRENT_STATUS.md']
files += sorted((PACKAGE/'assets/gpu_rigid_guitar_v1').glob('*'))
for original in files:
    target = PHASE/'source_final'/original.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert sha(target) == sha(original)
    else:
        shutil.copyfile(original, target)
result = dict(completed=True, baseline='guitar_learning_gpu_contact_fix_v1/source_manifest.json',
              changed_python=changed, active_python_count=len(current_python),
              unchanged_existing_python_count=len(current_python)-len(changed),
              protected_unchanged=protected, archive_files_verified=archives, attempts=attempts,
              after={str(p): sha(p) for p in files})
(PHASE/'source_manifest.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print(json.dumps({k: v for k, v in result.items() if k != 'after'}, indent=2, ensure_ascii=False))
