"""Root final preservation audit; no simulation or learning."""
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
BASE = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def save(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

manifests = [
    'selection_v1/inputs_before.json',
    'implementation/cpu_inputs_before_v1.json',
    'cpu_adapter_v2/inputs_before.json',
    'replay_v1/inputs_before.json',
    'native_probe_v1/inputs_before.json',
    'native_analysis_v1/inputs_before.json',
]
pins = {}
conflicts = []
for rel in manifests:
    values = json.loads((BASE / rel).read_text())
    for path, expected in values.items():
        if path in pins and pins[path] != expected:
            conflicts.append(path)
        pins[path] = expected
changed = [path for path, expected in pins.items()
           if not Path(path).is_file() or sha(path) != expected]
review = BASE / 'review/native_final_review_v1.md'
assert review.is_file(), 'Independent final review must exist before sealing'

snapshot = BASE / 'source_final'
snapshot.mkdir(exist_ok=False)
sources = list((ROOT / 'stability_adapter_2/free_guitar_learning_v1').glob('fretting*.py'))
sources += list((ROOT / 'stability_adapter_2/free_guitar_learning_v1').glob('test_fretting*.py'))
sources += list((ROOT / 'stability_adapter_2/free_guitar_learning_v1').glob('run_fretting_probe_v*.py'))
sources += [BASE / rel for rel in ['selection_v1/inspect.py', 'replay_v1/replay.py', 'native_analysis_v1/analyze.py', 'finalize_v1.py']]
snapshot_map = {}
for source in sources:
    target = snapshot / source.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)
    snapshot_map[str(source)] = {'snapshot': str(target), 'sha256': sha(target)}
save('source_final_manifest.json', snapshot_map)

local_documents = [BASE / 'README.md', ROOT / 'stability_adapter_2/free_guitar_learning_v1/README_v2.md', ROOT / 'docs/plans/free_guitar_fretting_stage2_completion_20261017.md']
missing_links = []
for document in local_documents:
    for raw in re.findall(r'\]\((/[^)]+)\)', document.read_text()):
        target = re.sub(r':\d+$', '', raw)
        if not Path(target).exists():
            missing_links.append({'document': str(document), 'target': raw})

report = json.loads((BASE / 'native_probe_v1/report.json').read_text())
analysis = json.loads((BASE / 'native_analysis_v1/result.json').read_text())
replay = json.loads((BASE / 'replay_v1/result.json').read_text())
passed = not conflicts and not changed and not missing_links and report['completed'] and report['inputs_unchanged'] and analysis['inputs_unchanged'] and replay['inputs_unchanged']
save('final_verification.json', {
    'scope': 'stage2 single-target measurement integration, not trained music performance or calibrated string pressure',
    'passed': passed,
    'input_manifests': manifests,
    'unique_pinned_inputs_rehashed': len(pins),
    'conflicting_input_hashes': conflicts,
    'changed_or_missing_inputs': changed,
    'missing_document_links': missing_links,
    'independent_review': str(review),
    'independent_review_sha256': sha(review),
    'cpu_measurement_tests': 9,
    'cpu_adapter_tests': 3,
    'native_completed': report['completed'],
    'actual_imported_sources_missing_pins': report['missing_import_pins'],
    'original_source_parity_errors': report['original_source_parity_errors'],
    'native_candidate_samples': analysis['candidate_samples'],
    'native_total_samples': analysis['samples'],
    'new_physics_seconds': 23,
    'archived_replay_new_physics_seconds': 0,
    'new_training_updates': 0,
    'visual_check': 'Root inspected actual final whole_body and side hands PNGs. Side camera is not a fingertip close-up.',
    'source_snapshot_manifest': str(BASE / 'source_final_manifest.json'),
    'limitations': ['One diagnostic target selected from current grip', 'Contact candidate is not string force, vibration or sound', 'Target contact loss is not complete left-hand release', 'No learned fretting/strike, music rewards or PPO yet'],
})
artifacts = []
for path in sorted(BASE.rglob('*')):
    if path.is_file() and '__pycache__' not in path.parts and path.name != 'artifact_inventory.json':
        artifacts.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
save('artifact_inventory.json', {'scope': 'All stage2 files except this inventory and generated Python caches; includes original attempts and source snapshots', 'artifacts': artifacts})
print(json.dumps({'passed': passed, 'unique_pinned_inputs': len(pins), 'changed_inputs': changed, 'conflicts': conflicts, 'missing_links': missing_links, 'artifacts': len(artifacts)}, indent=2))
assert passed
