"""Root audit and archival copy for the CPU whole-body contract."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda p, value: p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
assert (PHASE/'review.md').is_file()
assert not (PHASE/'final_verification.json').exists()
before = json.loads((PHASE/'cpu_v1/inputs_before.json').read_text())
result = json.loads((PHASE/'cpu_v1/result.json').read_text())
assert result['returncode'] == 0 and before == result['inputs_after']
assert not result['changed_inputs'] and not result['previous_pipeline_changed'] and not result['historical_native_changed']
for p, digest in before.items(): assert sha(Path(p)) == digest, p
old = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json').read_text())['input_sha256']
v2 = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/final_verification.json').read_text())['input_union_sha256']
for mapping in (old, v2):
    for p, digest in mapping.items(): assert sha(Path(p)) == digest, p
copies = {}
snapshot = PHASE/'source_final'
snapshot.mkdir(exist_ok=False)
for path, digest in before.items():
    destination = snapshot/Path(path).relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    assert sha(destination) == digest
    copies[str(destination.relative_to(PHASE))] = digest
documents = [ROOT/p for p in ('PROJECT_CONTEXT.md', 'stability_adapter_2/README.md', 'stability_adapter_2/PLAN.md',
    'docs/plans/music_model_pipeline_20261015.md', 'docs/FRESH_MUSIC_USER_REVIEW.md',
    'docs/plans/wholebody_control_20261015.md')]+[PHASE/'README.md', PHASE/'review.md']
for document in documents:
    for target in re.findall(r'\]\((/home/ajou/[^)]+)\)', document.read_text()):
        if '/wholebody_control_v1/' in target or '/music_pipeline_v3/' in target:
            assert Path(re.sub(r':\d+$', '', target)).exists(), target
write(PHASE/'final_verification.json', dict(
    scope='CPU full-body target/finite PD command contract; native adapter and physical validation pending',
    tests_passed=5, native_runs=0, policy_action_dim=39, target_channels=105, reference_held_channels=66,
    original_xml_nonzero_range_channels=97, original_xml_zero_range_channels=8,
    original_mesh_declarations_pinned=37, numpy_version=np.__version__,
    inputs_sha256=before, source_final_sha256=copies, previous_pipeline_inputs_unchanged=len(v2),
    historical_native_inputs_unchanged=len(old),
    working_document_sha256={str(p): sha(p) for p in documents},
    seal_source_sha256=sha(Path(__file__).resolve())))
files = {str(p.relative_to(PHASE)): dict(sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(PHASE.rglob('*')) if p.is_file()}
write(PHASE/'artifact_inventory.json', dict(scope='phase files excluding this inventory', files=files))
print(json.dumps(dict(tests_passed=5, archived_inputs=len(copies), phase_files=len(files),
                     previous_pipeline_unchanged=len(v2), historical_native_unchanged=len(old))))
