#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
OUT="$ROOT/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts"
PRODUCER="$ROOT/stability_adapter_2/make_fixed_strap_source_compatibility_artifacts.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python

for target in \
  "$OUT/run_producer.sh.archived" \
  "$OUT/producer.log" \
  "$OUT/producer_execution.json" \
  "$OUT/artifact_manifest.json" \
  "$OUT/source_snapshot.json" \
  "$OUT/source_snapshot" \
  "$OUT/fixed_strap_source_range_changes.png"; do
  if [[ -e "$target" ]]; then
    echo "Refusing nonempty artifact output: $target" >&2
    exit 2
  fi
done

cp -- "$OUT/run_producer.sh" "$OUT/run_producer.sh.archived"
PRODUCER_BEFORE=$(sha256sum "$PRODUCER" | cut -d ' ' -f 1)
WRAPPER_SHA=$(sha256sum "$OUT/run_producer.sh.archived" | cut -d ' ' -f 1)
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/mplconfig_fixed_strap_source_compatibility_v1
export PYTHONPATH="$ROOT"
START_NS=$(date +%s%N)
set +e
"$PYTHON" "$PRODUCER" >"$OUT/producer.log" 2>&1
STATUS=$?
set -e
END_NS=$(date +%s%N)
"$PYTHON" - "$OUT" "$PRODUCER_BEFORE" "$WRAPPER_SHA" "$STATUS" "$START_NS" "$END_NS" "$PYTHON" "$PRODUCER" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

out = Path(sys.argv[1])
producer_before, wrapper_sha = sys.argv[2], sys.argv[3]
status, start_ns, end_ns = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
python, producer = sys.argv[7], sys.argv[8]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
manifest_path = out / 'artifact_manifest.json'
manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
log_path = out / 'producer.log'
metadata = {
    'command': [python, producer],
    'environment': {key: os.environ.get(key) for key in ['MPLBACKEND', 'MPLCONFIGDIR', 'PYTHONPATH']},
    'exit_code': status,
    'wall_seconds': (end_ns - start_ns) / 1e9,
    'producer_sha256_before': producer_before,
    'producer_sha256_after': sha(producer),
    'wrapper_sha256': wrapper_sha,
    'log_sha256': sha(log_path),
    'inputs_sha256_before': manifest.get('inputs_sha256_before', {}),
    'inputs_sha256_after': manifest.get('inputs_sha256_after', {}),
    'outputs_sha256': manifest.get('outputs_sha256', {}),
    'direct_input_count': manifest.get('direct_input_count'),
    'native_initializations': 0,
    'physics_steps': 0,
    'actor_inference_calls': 0,
    'training_updates': 0,
}
(out / 'producer_execution.json').write_text(json.dumps(metadata, indent=2) + '\n')
PY
cat "$OUT/producer.log"
exit "$STATUS"
