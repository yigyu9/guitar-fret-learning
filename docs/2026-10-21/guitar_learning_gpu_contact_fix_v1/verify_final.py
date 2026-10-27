"""Verify final evidence and save an immutable-by-convention source snapshot."""
import ast
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
PACKAGE = ROOT / 'guitar_learning'
ARCHIVE = PACKAGE / 'archive/20261021_before_gpu_contact_fix_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(name, data):
    (PHASE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


before = load(PHASE / 'inputs_before.json')
assert load(ARCHIVE / 'manifest.json')['files'] == before
for original, sha in before.items():
    assert digest(ARCHIVE / Path(original).relative_to(PACKAGE)) == sha
changed = sorted(str(Path(p).relative_to(PACKAGE)) for p, sha in before.items()
                 if digest(Path(p)) != sha)
expected = sorted([
    'AGENTS.md', 'README.md', 'gpu/scene.py', 'gpu/control.py',
    'training/gpu_pool.py', 'training/gpu_runner.py', 'training/start.py',
    'tests/test_gpu_scene.py', 'tests/test_gpu_training.py',
])
assert changed == expected, changed
python_paths = sorted(p for p in PACKAGE.rglob('*.py')
                      if 'archive' not in p.relative_to(PACKAGE).parts)
new_python = sorted(str(p.relative_to(PACKAGE)) for p in python_paths
                    if str(p) not in before)
assert new_python == ['gpu/rigid_guitar.py', 'tests/test_gpu_rigid_guitar.py']
assert len(python_paths) == 423
for p in python_paths:
    ast.parse(p.read_bytes(), filename=str(p))
protected = ['music_task.py', 'song/task.py', 'song/__init__.py']
for rel in protected:
    assert digest(PACKAGE / rel) == before[str(PACKAGE / rel)]
native_paths = [p for p in python_paths if p.relative_to(PACKAGE).parts[0] == 'native']
assert all(digest(p) == before[str(p)] for p in native_paths)

runs = {}
for name in ['live_gpu128_zero_2s_final', 'live_gpu1024_zero_2s_final',
             'train128_final', 'resume128_final_v2']:
    folder = PHASE / name
    report = load(folder / 'report.json')
    pins = load(folder / 'inputs_before.json')
    mismatches = [p for p, sha in pins.items() if digest(Path(p)) != sha]
    assert not mismatches, mismatches
    assert report['completed'] and report['failure'] is None
    assert not report['changed_inputs']
    scene = report.get('scene', report.get('gpu_scene'))
    assert scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    assert scene['device'] == 'cuda:0' and scene['closed']
    assert scene['native_body_count'] == 68 and scene['logical_body_count'] == 106
    for value in scene['tensor_devices'].values():
        assert value == 'cuda:0'
    entry = {'completed': True, 'pinned_input_count': len(pins),
             'current_input_mismatches': mismatches, 'gpu_scene': scene}
    if 'journal' in report:
        assert not report['missing_import_pins'] and not report['cleanup_errors']
        assert report['lifecycle_verified']
        journal = report['journal']
        assert journal['closed'] and not journal['failed']
        assert journal['discarded'] == 0
        assert len({journal[k] for k in ['sampled', 'logged', 'durable', 'committed']}) == 1
        entry.update({k: report[k] for k in [
            'transitions', 'optimizer_updates', 'completed_episodes',
            'missing_import_pins', 'cleanup_errors', 'lifecycle_verified']})
    else:
        events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
        assert len(events) == report['failure_episodes']
        entry.update(failure_episodes=len(events),
                     distinct_failed_envs=len({e['env_id'] for e in events}),
                     failure_reasons=dict(Counter(r for e in events for r in e['failure_reasons'])))
    runs[name] = entry
assert runs['live_gpu128_zero_2s_final']['failure_episodes'] == 0
assert runs['live_gpu1024_zero_2s_final']['failure_episodes'] == 8
assert runs['train128_final']['transitions'] == 8192
assert runs['resume128_final_v2']['transitions'] == 4096
assert runs['resume128_final_v2']['optimizer_updates'] == 3
reset = load(PHASE / 'live_reset_final/report.json')
assert reset['completed'] and reset['native_bodies'] == 272
assert reset['logical_body_shape'] == [4, 106, 13]
assert all(reset[k] for k in [
    'selective_reset_unchanged_rows', 'duplicate_reset_noop',
    'same_step_split_reset_rejected', 'physical_root_COM_velocity_restored',
    'original_logical_COM_retained', 'aggregate_force_only_on_logical_root'])
checkpoint = load(PHASE / 'checkpoint_verification.json')
assert checkpoint['completed'] and all(checkpoint['restored_fields_equal'].values())
assert checkpoint['model_finite'] and checkpoint['final_updates'] == 3
assert checkpoint['old_same_architecture_backend_rejected']
tests = (PHASE / 'active_gpu_tests_final.log').read_text()
assert 'Ran 36 tests' in tests and '\nOK\n' in tests

assets = sorted((PACKAGE / 'assets/gpu_rigid_guitar_v1').glob('*'))
final_files = python_paths + [PACKAGE / 'README.md', PACKAGE / 'AGENTS.md',
                             ROOT / 'CURRENT_STATUS.md'] + assets
snapshot = PHASE / 'source_final'
for original in final_files:
    target = snapshot / original.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert digest(target) == digest(original)
    else:
        shutil.copyfile(original, target)
manifest = {'before': before, 'after': {str(p): digest(p) for p in final_files},
            'changed_existing_package_files': changed, 'new_python_files': new_python,
            'new_asset_files': [str(p.relative_to(ROOT)) for p in assets],
            'protected_files_unchanged': protected,
            'native_python_files_unchanged': len(native_paths)}
save('source_manifest.json', manifest)
save('verification.json', {
    'completed': True, 'scope': 'Contact regression mitigation; residual slow drift unresolved',
    'archive_files_verified': len(before), 'active_python_AST_checked': len(python_paths),
    'unchanged_existing_python_files': 414, 'related_CPU_tests_passed': 36,
    'full_CPU_suite_rerun': False, 'live_reset': reset, 'runs': runs,
    'checkpoint': checkpoint, 'long_term_stability_certified': False,
    'recommended_training_env_count_certified': False,
    'historical_failure_count': {'episodes': 1781, 'distinct_envs': 817},
    'historical_harness_failure_retained': 'resume128_final used nonexistent checkpoint.pt; corrected in resume128_final_v2',
})
print(json.dumps({'completed': True, 'archive_files': len(before),
                  'active_python_files': len(python_paths), 'final_source_files': len(final_files),
                  'runs': list(runs)}, indent=2))
