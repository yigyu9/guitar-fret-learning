#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
PHASE="$ROOT/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1"
OUT="$PHASE/artifacts"
SNAP="$PHASE/artifact_source"
LOG="$PHASE/artifact.log"
EXEC="$PHASE/artifact_execution.json"
SOURCE_MANIFEST="$PHASE/artifact_source_manifest.json"
PRODUCER="$ROOT/stability_adapter_2/make_arm_position_artifacts.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python
MPL_CACHE=/tmp/arm_position_mpl_cache

for path in "$OUT/arm_source_geometry.png" "$OUT/manifest.json" "$SNAP" "$LOG" "$EXEC" "$SOURCE_MANIFEST"; do
    if [[ -e "$path" ]]; then
        echo "refusing to overwrite existing artifact path: $path" >&2
        exit 2
    fi
done
mkdir -p "$OUT" "$SNAP"

export ARM_POSITION_PRODUCER_SHA256="$(sha256sum "$PRODUCER" | awk '{print $1}')"
export ARM_POSITION_WRAPPER_SHA256="$(sha256sum "$0" | awk '{print $1}')"

"$PYTHON" - <<'PY'
import hashlib
import json
import shutil
from pathlib import Path

root = Path('/home/ajou/yigyu/3')
phase = root / 'docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1'
snapshot = phase / 'artifact_source'
analysis_path = phase / 'analysis.json'
analysis = json.loads(analysis_path.read_text(encoding='utf-8'))
closure = analysis['input_sha256_before']
if len(closure) != 76 or closure != analysis['input_sha256_after']:
    raise SystemExit('analysis closure is not the expected unchanged 76-input map')
extra = [
    phase / 'analysis.json',
    phase / 'analysis_execution.json',
    phase / 'analysis_invocation.json',
    phase / 'analysis_source_manifest.json',
    root / 'stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md',
    root / 'stability_adapter_2/ARM_POSITION_EXECUTION.md',
    root / 'stability_adapter_2/analyze_arm_position.py',
    root / 'stability_adapter_2/search_arm_position.py',
    root / 'stability_adapter_2/make_arm_position_artifacts.py',
    phase / 'artifacts/run_producer.sh',
]
paths = sorted(set([Path(p) for p in closure] + extra), key=str)

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
        raise SystemExit('missing source to archive: ' + str(path))
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
        raise SystemExit('source snapshot SHA mismatch: ' + str(path))
    rows.append({
        'original_path': str(path),
        'copy_path': str(copy_path),
        'sha256': original_hash,
        'copy_sha256': copy_hash,
    })
    input_before[str(path)] = original_hash
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

export ARM_POSITION_EXIT_CODE="$EXIT_CODE"
export ARM_POSITION_LOG_SHA256="$(sha256sum "$LOG" | awk '{print $1}')"
"$PYTHON" - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path('/home/ajou/yigyu/3')
phase = root / 'docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1'
analysis = json.loads((phase / 'analysis.json').read_text(encoding='utf-8'))
closure = analysis['input_sha256_before']
extra = [
    phase / 'analysis.json', phase / 'analysis_execution.json',
    phase / 'analysis_invocation.json', phase / 'analysis_source_manifest.json',
    root / 'stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md',
    root / 'stability_adapter_2/ARM_POSITION_EXECUTION.md',
    root / 'stability_adapter_2/analyze_arm_position.py',
    root / 'stability_adapter_2/search_arm_position.py',
    root / 'stability_adapter_2/make_arm_position_artifacts.py',
    phase / 'artifacts/run_producer.sh',
]
paths = sorted(set([Path(p) for p in closure] + extra), key=str)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

before = json.loads((phase / 'artifact_source/input_sha256_before.json').read_text(encoding='utf-8'))
after = {}
for path in paths:
    after[str(path)] = digest(path)
producer = root / 'stability_adapter_2/make_arm_position_artifacts.py'
log = phase / 'artifact.log'
execution = {
    'command': ['/home/ajou/miniconda3/envs/rl38/bin/python', str(producer)],
    'wrapper': str(phase / 'artifacts/run_producer.sh'),
    'environment': {'MPLBACKEND': 'Agg', 'MPLCONFIGDIR': '/tmp/arm_position_mpl_cache', 'python': '/home/ajou/miniconda3/envs/rl38/bin/python'},
    'exit_code': int(os.environ['ARM_POSITION_EXIT_CODE']),
    'terminal_state': 'completed' if int(os.environ['ARM_POSITION_EXIT_CODE']) == 0 else 'failed',
    'producer_sha256_before': os.environ['ARM_POSITION_PRODUCER_SHA256'],
    'producer_sha256_after': digest(producer),
    'wrapper_sha256_before': os.environ['ARM_POSITION_WRAPPER_SHA256'],
    'wrapper_sha256_after': digest(phase / 'artifacts/run_producer.sh'),
    'input_sha256_before': before,
    'input_sha256_after': after,
    'source_snapshot_manifest': str(phase / 'artifact_source_manifest.json'),
    'log_sha256': os.environ['ARM_POSITION_LOG_SHA256'],
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
