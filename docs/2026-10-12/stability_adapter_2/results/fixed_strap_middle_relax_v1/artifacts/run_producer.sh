#!/usr/bin/env bash
set -u
ROOT=/home/ajou/yigyu/3
OUT="$ROOT/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts"
for path in "$OUT/run_producer.sh.archived" "$OUT/producer.log" "$OUT/producer_execution.json" "$OUT/middle_relax_native_summary.png" "$OUT/artifact_manifest.json" "$OUT/source_snapshot.json" "$OUT/source_snapshot"; do
  if [ -e "$path" ]; then
    echo "refusing to overwrite existing execution evidence: $path" >&2
    exit 2
  fi
done
cp "$0" "$OUT/run_producer.sh.archived"
set +e
cd "$ROOT"
START=$(date +%s.%N)
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mplconfig_fixed_strap_middle_relax_v1 /home/ajou/miniconda3/envs/rl38/bin/python "$ROOT/stability_adapter_2/make_middle_relax_artifacts.py" --out-dir "$OUT" > "$OUT/producer.log" 2>&1
status=$?
END=$(date +%s.%N)
set -e
python3 - "$OUT" "$status" "$START" "$END" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
out = Path(sys.argv[1])
status = int(sys.argv[2])
start = float(sys.argv[3])
end = float(sys.argv[4])
log = out / 'producer.log'
manifest_path = out / 'artifact_manifest.json'
manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
log_sha = hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None
record = {
    'command': ['/home/ajou/miniconda3/envs/rl38/bin/python', '/home/ajou/yigyu/3/stability_adapter_2/make_middle_relax_artifacts.py', '--out-dir', str(out)],
    'environment': {'MPLBACKEND': 'Agg', 'MPLCONFIGDIR': '/tmp/mplconfig_fixed_strap_middle_relax_v1'},
    'exit_code': status,
    'wall_seconds': end - start,
    'producer_log_sha256': log_sha,
    'producer_sha256_before': manifest.get('producer_sha256_before'),
    'producer_sha256_after': manifest.get('producer_sha256_after'),
    'inputs_sha256_before': manifest.get('inputs_sha256_before'),
    'inputs_sha256_after': manifest.get('inputs_sha256_after'),
    'outputs_sha256': manifest.get('outputs_sha256'),
    'native_initializations_during_artifact': 0,
    'physics_steps_during_artifact': 0,
    'actor_inference_calls_during_artifact': 0,
    'training_updates_during_artifact': 0,
}
(out / 'producer_execution.json').write_text(json.dumps(record, indent=2) + '\n')
PY
exit "$status"
