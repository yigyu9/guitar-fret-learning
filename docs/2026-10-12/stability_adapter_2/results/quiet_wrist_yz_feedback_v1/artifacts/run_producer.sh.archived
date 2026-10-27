#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
PHASE="$ROOT/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1"
ARTIFACTS="$PHASE/artifacts"
PRODUCER="$ROOT/stability_adapter_2/make_wrist_yz_feedback_artifacts.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python

for path in \
  "$ARTIFACTS/run_producer.sh.archived" \
  "$PHASE/artifact_source" \
  "$PHASE/artifact_source_manifest.json" \
  "$PHASE/artifact_invocation.json" \
  "$PHASE/artifact_execution.json" \
  "$PHASE/artifact.log" \
  "$ARTIFACTS/quiet_wrist_yz_feedback_response.png" \
  "$ARTIFACTS/manifest.json"; do
  if [[ -e "$path" ]]; then
    echo "refusing to overwrite existing artifact evidence: $path" >&2
    exit 2
  fi
done

for path in \
  "$PHASE/analysis.json" "$PHASE/series.json" \
  "$PHASE/off_execution.json" "$PHASE/off.log" "$PHASE/off_inputs.json" \
  "$PHASE/on_execution.json" "$PHASE/on.log" "$PHASE/on_inputs.json" \
  "$PHASE/native/off/report.json" "$PHASE/native/off/videos.json" \
  "$PHASE/native/on/report.json" "$PHASE/native/on/videos.json"; do
  if [[ ! -f "$path" ]]; then
    echo "required saved analysis or completed trial input is missing: $path" >&2
    exit 3
  fi
done

mkdir -p "$ARTIFACTS"
cp --preserve=mode,timestamps "$0" "$ARTIFACTS/run_producer.sh.archived"

PRODUCER_SHA="$("$PYTHON" - "$ROOT" "$PHASE" "$PRODUCER" "$ARTIFACTS/run_producer.sh" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

root, phase, producer, wrapper = map(Path, sys.argv[1:])
analysis_path = phase / "analysis.json"
series_path = phase / "series.json"
analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
closure = analysis.get("input_sha256_before", {})
if not closure or closure != analysis.get("input_sha256_after"):
    raise SystemExit("analysis input closure before/after mismatch")

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

for original, expected in closure.items():
    if not Path(original).is_file() or sha(original) != expected:
        raise SystemExit("analysis closure is stale: " + original)

selected = [
    producer, wrapper, analysis_path, series_path,
    root / "stability_adapter_2/analyze_quiet_wrist_yz_feedback.py",
    root / "stability_adapter_2/run_quiet_wrist_yz_feedback.py",
    root / "stability_adapter_2/run_quiet_wrist_yz_feedback_phase.py",
    root / "stability_adapter_2/wrist_yz_guitar_feedback.py",
    root / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md",
    root / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md",
    root / "stability_adapter_2/preflight_wrist_yz_feedback.py",
    phase / "preflight.json", phase / "preflight_source.py",
    phase / "off_inputs.json", phase / "off_invocation.json",
    phase / "off_execution.json", phase / "off.log",
    phase / "on_inputs.json", phase / "on_invocation.json",
    phase / "on_execution.json", phase / "on.log",
]
for condition in ("off", "on"):
    native = phase / "native" / condition
    for name in ("initial_values.json", "report.json", "capture.json", "videos.json", "attempt.json"):
        selected.append(native / name)
source_root = phase / "artifact_source"
source_root.mkdir(parents=True, exist_ok=False)
files = []
for original in selected:
    if not original.is_file():
        raise SystemExit("missing selected artifact input: " + str(original))
    digest = sha(original)
    try:
        relative = original.relative_to(root)
    except ValueError:
        relative = Path("external") / original.as_posix().lstrip("/")
    copied = source_root / relative
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(original, copied)
    copied_sha = sha(copied)
    if digest != copied_sha:
        raise SystemExit("artifact source copy mismatch: " + str(original))
    files.append({"original_path": str(original), "copy_path": str(copied), "sha256": digest, "copy_sha256": copied_sha})

archive = Path(str(wrapper) + ".archived")
archive_copy = source_root / "artifacts/run_producer.sh.archived"
archive_copy.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(archive, archive_copy)
archive_sha = sha(archive)
if sha(archive_copy) != archive_sha:
    raise SystemExit("archived wrapper copy SHA mismatch")
files.append({"original_path": str(archive), "copy_path": str(archive_copy), "sha256": archive_sha, "copy_sha256": sha(archive_copy)})
manifest = {
    "files": files,
    "analysis_closure_count": len(closure),
    "analysis_source_archive": str(phase / "analysis_source_manifest.json"),
    "scope": "selected snapshots are copied here; the full analysis input closure is hash-checked and native originals remain at their recorded paths",
}
manifest_path = phase / "artifact_source_manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

source_sha = sha(producer)
if not any(item["original_path"] == str(producer) and item["sha256"] == source_sha for item in files):
    raise SystemExit("producer was not exact-SHA archived")
input_before = dict(closure)
input_before[str(analysis_path)] = sha(analysis_path)
input_before[str(series_path)] = sha(series_path)
for item in files:
    input_before[item["original_path"]] = item["sha256"]
input_before[str(manifest_path)] = sha(manifest_path)
command = ["/home/ajou/miniconda3/envs/rl38/bin/python", "-u", "-m", "stability_adapter_2.make_wrist_yz_feedback_artifacts"]
environment = {
    "WRIST_YZ_FEEDBACK_PRODUCER_SHA256": source_sha,
    "MPLBACKEND": "Agg",
    "MPLCONFIGDIR": "/tmp/stability2_wrist_yz_feedback_artifacts",
}
invocation_path = phase / "artifact_invocation.json"
invocation_path.write_text(json.dumps({
    "command": command,
    "cwd": str(root),
    "environment": environment,
    "producer_sha256_before": source_sha,
    "wrapper_sha256_before": sha(wrapper),
    "input_sha256_before": input_before,
    "source_manifest_sha256": sha(manifest_path),
}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(source_sha)
PY
)"

export WRIST_YZ_FEEDBACK_PRODUCER_SHA256="$PRODUCER_SHA"
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/stability2_wrist_yz_feedback_artifacts
COMMAND=("$PYTHON" -u -m stability_adapter_2.make_wrist_yz_feedback_artifacts)
START=$(date +%s.%N)
set +e
"${COMMAND[@]}" >"$PHASE/artifact.log" 2>&1
STATUS=$?
set -e
END=$(date +%s.%N)

"$PYTHON" - "$ROOT" "$PHASE" "$ARTIFACTS" "$PRODUCER_SHA" "$STATUS" "$START" "$END" "${COMMAND[@]}" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

root, phase, artifacts = map(Path, sys.argv[1:4])
producer_sha, status, start, end = sys.argv[4:8]
command = sys.argv[8:]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
invocation_path = phase / "artifact_invocation.json"
invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
before = dict(invocation["input_sha256_before"])
before[str(invocation_path)] = sha(invocation_path)
wrapper_archive = artifacts / "run_producer.sh.archived"
wrapper_sha = invocation["wrapper_sha256_before"]
if wrapper_sha != sha(artifacts / "run_producer.sh") or wrapper_sha != sha(wrapper_archive):
    raise SystemExit("archived wrapper SHA changed")
after = {path: sha(Path(path)) for path in before}
log_path = phase / "artifact.log"
outputs = {}
for path in (artifacts / "quiet_wrist_yz_feedback_response.png", artifacts / "manifest.json"):
    if path.is_file():
        outputs[str(path)] = sha(path)
env_keys = ["WRIST_YZ_FEEDBACK_PRODUCER_SHA256", "MPLBACKEND", "MPLCONFIGDIR"]
record = {
    "command": command,
    "cwd": str(root),
    "environment": {key: os.environ[key] for key in env_keys},
    "exit_code": int(status),
    "wall_seconds": float(end) - float(start),
    "producer_sha256_before": invocation["producer_sha256_before"],
    "producer_sha256_after": sha(root / "stability_adapter_2/make_wrist_yz_feedback_artifacts.py"),
    "wrapper_sha256_before": wrapper_sha,
    "wrapper_sha256_after": sha(artifacts / "run_producer.sh"),
    "input_sha256_before": before,
    "input_sha256_after": after,
    "log_sha256": sha(log_path),
    "outputs_sha256": outputs,
}
(phase / "artifact_execution.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if int(status) != 0 or before != after or record["producer_sha256_after"] != producer_sha or record["wrapper_sha256_after"] != wrapper_sha:
    raise SystemExit("artifact stage failed or a source/input changed")
PY
