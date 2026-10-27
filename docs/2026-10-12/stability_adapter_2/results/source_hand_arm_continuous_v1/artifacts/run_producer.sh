#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
PHASE="$ROOT/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1"
OUT="$PHASE/artifacts"
SNAP="$PHASE/artifact_source"
LOG="$PHASE/artifact.log"
EXEC="$PHASE/artifact_execution.json"
SOURCE_MANIFEST="$PHASE/artifact_source_manifest.json"
PRODUCER="$ROOT/stability_adapter_2/make_arm_continuous_artifacts.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python
MPL_CACHE=/tmp/arm_continuous_mpl_cache

for path in "$OUT/arm_continuous_progress.png" "$OUT/manifest.json" "$SNAP" "$LOG" "$EXEC" "$SOURCE_MANIFEST"; do
    if [[ -e "$path" ]]; then
        echo "refusing to overwrite existing artifact path: $path" >&2
        exit 2
    fi
done
mkdir -p "$OUT" "$SNAP"

export ARM_CONTINUOUS_PRODUCER_SHA256="$(sha256sum "$PRODUCER" | awk '{print $1}')"
export ARM_CONTINUOUS_WRAPPER_SHA256="$(sha256sum "$0" | awk '{print $1}')"

"$PYTHON" - <<'PY'
import hashlib
import json
import shutil
from pathlib import Path

root = Path('/home/ajou/yigyu/3')
phase = root / 'docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1'
snapshot = phase / 'artifact_source'
search_execution = json.loads((phase / 'search_execution.json').read_text(encoding='utf-8'))
analysis_execution = json.loads((phase / 'analysis_v2_execution.json').read_text(encoding='utf-8'))
analysis = json.loads((phase / 'analysis_v2.json').read_text(encoding='utf-8'))
search_map = search_execution['input_sha256_before']
analysis_map = analysis_execution['input_sha256_before']
if len(search_map) != 72 or search_map != search_execution['input_sha256_after']:
    raise SystemExit('source search closure is not the unchanged 72-input map')
if len(analysis_map) != 81 or analysis_map != analysis_execution['input_sha256_after']:
    raise SystemExit('corrected analysis closure is not the unchanged 81-input map')
if analysis_map != analysis.get('input_sha256_before') or analysis_map != analysis.get('input_sha256_after'):
    raise SystemExit('corrected analysis and execution input closures differ')
if analysis_map.get(str(phase / 'evaluations.jsonl')) is None:
    raise SystemExit('v2 analysis closure omits saved evaluations.jsonl')

manifest_paths = [
    phase / 'search_source_manifest.json',
    phase / 'analysis_source_manifest.json',
    phase / 'analysis_v2_source_manifest.json',
]
snapshot_sources = set()
for manifest_path in manifest_paths:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for original, entry in manifest.items():
        source = Path(original)
        copy = Path(entry['snapshot'])
        if not source.is_file() or not copy.is_file():
            raise SystemExit('missing source or preserved snapshot: ' + str(original))
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
            raise SystemExit('preserved source hash no longer matches manifest: ' + str(original))
        if hashlib.sha256(copy.read_bytes()).hexdigest() != entry['sha256']:
            raise SystemExit('preserved copy hash no longer matches manifest: ' + str(copy))
        snapshot_sources.add(source)
        snapshot_sources.add(copy)

extra = [
    phase / 'search.json', phase / 'evaluations.jsonl', phase / 'search_execution.json',
    phase / 'search_source_manifest.json', phase / 'analysis_v2.json',
    phase / 'analysis_v2_execution.json', phase / 'analysis_v2_source_manifest.json',
    phase / 'analysis_v2_invocation.json', phase / 'analysis_failure.json',
    phase / 'analysis_invocation.json', phase / 'analysis_source_manifest.json',
    root / 'stability_adapter_2/ARM_CONTINUOUS_EXECUTION.md',
    root / 'stability_adapter_2/ARM_CONTINUOUS_ANALYSIS_V2.md',
    root / 'stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md',
    root / 'stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md',
    root / 'stability_adapter_2/search_arm_continuous.py',
    root / 'stability_adapter_2/analyze_arm_continuous.py',
    root / 'stability_adapter_2/analyze_arm_continuous_v2.py',
    root / 'stability_adapter_2/make_arm_continuous_artifacts.py',
    phase / 'artifacts/run_producer.sh',
]
paths = set(Path(path) for path in search_map)
paths.update(Path(path) for path in analysis_map)
paths.update(snapshot_sources)
paths.update(extra)
paths = sorted(paths, key=str)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

rows = []
input_before = {}
for path in paths:
    if not path.is_file():
        raise SystemExit('missing artifact source input: ' + str(path))
    input_before[str(path)] = digest(path)
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = Path('external') / str(path).lstrip('/')
    copy_path = snapshot / relative
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(path), str(copy_path))
    original_hash = digest(path)
    copy_hash = digest(copy_path)
    if original_hash != copy_hash:
        raise SystemExit('artifact source snapshot SHA mismatch: ' + str(path))
    rows.append({
        'original_path': str(path),
        'copy_path': str(copy_path),
        'sha256': original_hash,
        'copy_sha256': copy_hash,
    })
(phase / 'artifact_source_manifest.json').write_text(
    json.dumps({'files': rows}, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
    encoding='utf-8',
)
(snapshot / 'input_sha256_before.json').write_text(
    json.dumps(input_before, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
    encoding='utf-8',
)
PY

set +e
MPLBACKEND=Agg MPLCONFIGDIR="$MPL_CACHE" "$PYTHON" "$PRODUCER" > "$LOG" 2>&1
EXIT_CODE=$?
set -e
export ARM_CONTINUOUS_EXIT_CODE="$EXIT_CODE"
export ARM_CONTINUOUS_LOG_SHA256="$(sha256sum "$LOG" | awk '{print $1}')"

"$PYTHON" - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path('/home/ajou/yigyu/3')
phase = root / 'docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1'
before = json.loads((phase / 'artifact_source/input_sha256_before.json').read_text(encoding='utf-8'))

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

after = {path: digest(path) for path in before}
producer = root / 'stability_adapter_2/make_arm_continuous_artifacts.py'
wrapper = phase / 'artifacts/run_producer.sh'
execution = {
    'command': ['/home/ajou/miniconda3/envs/rl38/bin/python', str(producer)],
    'wrapper': str(wrapper),
    'environment': {
        'MPLBACKEND': 'Agg',
        'MPLCONFIGDIR': '/tmp/arm_continuous_mpl_cache',
        'python': '/home/ajou/miniconda3/envs/rl38/bin/python',
    },
    'exit_code': int(os.environ['ARM_CONTINUOUS_EXIT_CODE']),
    'terminal_state': 'completed' if int(os.environ['ARM_CONTINUOUS_EXIT_CODE']) == 0 else 'failed',
    'producer_sha256_before': os.environ['ARM_CONTINUOUS_PRODUCER_SHA256'],
    'producer_sha256_after': digest(producer),
    'wrapper_sha256_before': os.environ['ARM_CONTINUOUS_WRAPPER_SHA256'],
    'wrapper_sha256_after': digest(wrapper),
    'input_sha256_before': before,
    'input_sha256_after': after,
    'source_snapshot_manifest': str(phase / 'artifact_source_manifest.json'),
    'log_sha256': os.environ['ARM_CONTINUOUS_LOG_SHA256'],
    'native_calls': 0,
    'physics_steps': 0,
    'actor_inference_calls': 0,
    'training_updates': 0,
}
(phase / 'artifact_execution.json').write_text(
    json.dumps(execution, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
    encoding='utf-8',
)
PY

exit "$EXIT_CODE"
