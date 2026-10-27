"""Root-only verification and archival copy; does not modify consumed inputs."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda p, obj: p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
assert not (PHASE/'final_verification.json').exists()
assert (PHASE/'review.md').is_file()
union = {}
attempts = []
for name in ('cpu_v1', 'cpu_v2'):
    before = json.loads((PHASE/name/'inputs_before.json').read_text())
    result = json.loads((PHASE/name/'result.json').read_text())
    assert before == result['inputs_after']
    assert not result['changed_inputs']
    for path, digest in before.items():
        assert path not in union or union[path] == digest
        assert sha(Path(path)) == digest, path
        union[path] = digest
    attempts.append(dict(name=name, returncode=result['returncode'], inputs=len(before),
                         test_log_sha256=sha(PHASE/name/'tests.log')))
assert attempts[-1]['returncode'] == 0
old = json.loads((ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/final_verification.json').read_text())['input_sha256']
assert all(Path(p).is_file() and sha(Path(p)) == digest for p, digest in old.items())
source_final = PHASE/'source_final'
source_final.mkdir(exist_ok=False)
copies = {}
for path, digest in union.items():
    relative = Path(path).relative_to(ROOT)
    destination = source_final/relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    assert sha(destination) == digest
    copies[str(destination.relative_to(PHASE))] = digest
documents = [ROOT/p for p in ('PROJECT_CONTEXT.md', 'stability_adapter_2/README.md', 'stability_adapter_2/PLAN.md',
    'docs/FRESH_MUSIC_USER_REVIEW.md', 'docs/plans/music_model_pipeline_20261015.md',
    'docs/plans/music_pipeline_implementation_20261015.md')]
documents += [PHASE/'README.md', PHASE/'review.md']
missing = []
for p in documents:
    for target in re.findall(r'\]\((/home/ajou/[^)]+)\)', p.read_text()):
        target = re.sub(r':\d+$', '', target)
        if not Path(target).exists(): missing.append(dict(document=str(p), target=target))
# Older context links are reported separately; new phase links must all exist.
new_missing = [item for item in missing if '/music_pipeline_v2/' in item['target']]
assert not new_missing, new_missing
write(PHASE/'final_verification.json', dict(
    scope='CPU module implementation and real-score/synthetic-physics integration; no native training or performance claim',
    attempts=attempts, passed_tests=26, native_runs=0, music_training_runs=0,
    input_union_sha256=union, source_final_sha256=copies,
    historical_native_input_count=len(old), historical_native_inputs_changed=[],
    working_document_sha256={str(p): sha(p) for p in documents},
    new_phase_missing_links=new_missing, historical_context_missing_links=missing,
    seal_source_sha256=sha(Path(__file__).resolve())))
files = {str(p.relative_to(PHASE)): dict(sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(PHASE.rglob('*')) if p.is_file()}
write(PHASE/'artifact_inventory.json', dict(scope='phase files excluding this inventory itself', files=files))
print(json.dumps(dict(archived_inputs=len(copies), phase_files=len(files),
                     historical_native_inputs=len(old), tests=26, historical_missing_links=len(missing))))
