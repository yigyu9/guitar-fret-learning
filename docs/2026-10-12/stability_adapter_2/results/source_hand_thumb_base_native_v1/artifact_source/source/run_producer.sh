#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/ajou/yigyu/3
PHASE="$ROOT/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1"
ART="$PHASE/artifacts"
PRODUCER="$ROOT/stability_adapter_2/make_thumb_base_native_artifacts.py"
WRAPPER="$ART/run_producer.sh"
SNAP="$PHASE/artifact_source"
LOG="$PHASE/artifact.log"
EXEC="$PHASE/artifact_execution.json"
MANIFEST="$ART/manifest.json"
PNG="$ART/thumb1_base_native_source_radius.png"
for path in "$SNAP" "$LOG" "$EXEC" "$MANIFEST" "$PNG" "$PHASE/artifact_source_manifest.json"; do
  if [[ -e "$path" ]]; then
    echo "refusing to overwrite existing artifact: $path" >&2
    exit 2
  fi
done
mkdir -p "$SNAP/source" "$SNAP/inputs"
cp -p "$PRODUCER" "$SNAP/source/make_thumb_base_native_artifacts.py"
cp -p "$WRAPPER" "$SNAP/source/run_producer.sh"
INPUTS=(
  "$PHASE/analysis.json"
  "$PHASE/native_batch.json"
  "$PHASE/preparation_execution.json"
  "$PHASE/finish_execution.json"
  "$ROOT/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json"
  "$ROOT/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png"
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
  "$PHASE/native/thumb1_x_minus005/initial_grip_audit.json"
  "$PHASE/native/thumb1_y_plus005/initial_grip_audit.json"
  "$PHASE/native/thumb1_x_minus010/initial_grip_audit.json"
  "$PHASE/native/thumb1_y_plus010/initial_grip_audit.json"
)
for source in "${INPUTS[@]}"; do
  rel="${source#$ROOT/}"
  mkdir -p "$SNAP/inputs/$(dirname "$rel")"
  cp -p "$source" "$SNAP/inputs/$rel"
done
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MPLCONFIGDIR=/tmp/stability2_thumb_base_artifacts
CMD=(/home/ajou/miniconda3/envs/rl38/bin/python "$PRODUCER")
set +e
"${CMD[@]}" > "$LOG" 2>&1
STATUS=$?
set -e
python - "$ROOT" "$PHASE" "$PRODUCER" "$WRAPPER" "$LOG" "$STATUS" "${CMD[@]}" <<'PY'
import hashlib, json, os, sys
from pathlib import Path
root, phase, producer, wrapper, log, status = sys.argv[1:7]
cmd = sys.argv[7:]
root, phase = Path(root), Path(phase)
snapshot = phase / "artifact_source"
inputs = [
    phase / "analysis.json", phase / "native_batch.json", phase / "preparation_execution.json", phase / "finish_execution.json",
    root / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json",
    root / "docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
] + [phase / "native" / label / "initial_grip_audit.json" for label in ["thumb1_x_minus005", "thumb1_y_plus005", "thumb1_x_minus010", "thumb1_y_plus010"]]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
files = [Path(producer), Path(wrapper)] + inputs
snaprows = []
for src in files:
    rel = str(src.relative_to(root)) if str(src).startswith(str(root) + os.sep) else src.as_posix().lstrip("/")
    copied = snapshot / ("source/" + src.name if src in [Path(producer), Path(wrapper)] else "inputs/" + rel)
    snaprows.append({"original_path": str(src), "copy_path": str(copied), "sha256": sha(src), "copy_sha256": sha(copied)})
if any(row["sha256"] != row["copy_sha256"] for row in snaprows):
    raise SystemExit("source snapshot hash mismatch")
(phase / "artifact_source_manifest.json").write_text(json.dumps({"files": snaprows}, indent=2) + "\n")
manifest_path = phase / "artifacts/manifest.json"
manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
execution = {
    "command": cmd,
    "environment": {key: os.environ.get(key) for key in ["MPLBACKEND", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MPLCONFIGDIR"]},
    "exit_code": int(status),
    "terminal_state": "completed" if int(status) == 0 else "failed",
    "source_snapshot": str(phase / "artifact_source_manifest.json"),
    "source_files": snaprows,
    "producer_sha256_before_after": [sha(snapshot / "source/make_thumb_base_native_artifacts.py"), sha(Path(producer))],
    "input_sha256_before": manifest.get("inputs_sha256_before", {}),
    "input_sha256_after": manifest.get("inputs_sha256_after", {}),
    "log_sha256": sha(Path(log)),
    "native_initializations": 0,
    "physics_steps": 0,
    "actor_inference_calls": 0,
    "training_updates": 0,
}
(phase / "artifact_execution.json").write_text(json.dumps(execution, indent=2, ensure_ascii=False) + "\n")
if int(status) != 0:
    raise SystemExit(int(status))
PY
