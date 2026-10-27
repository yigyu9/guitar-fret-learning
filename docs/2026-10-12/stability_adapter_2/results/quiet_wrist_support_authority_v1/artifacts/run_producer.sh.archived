#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
PHASE="$ROOT/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1"
ARTIFACTS="$PHASE/artifacts"
PRODUCER="$ROOT/stability_adapter_2/make_quiet_wrist_artifacts.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python

for path in \
  "$ARTIFACTS/run_producer.sh.archived" \
  "$PHASE/artifact_source" \
  "$PHASE/artifact_source_manifest.json" \
  "$PHASE/artifact_invocation.json" \
  "$PHASE/artifact_execution.json" \
  "$PHASE/artifact.log" \
  "$ARTIFACTS/quiet_wrist_support_response.png" \
  "$ARTIFACTS/manifest.json"; do
  if [[ -e "$path" ]]; then
    echo "refusing to overwrite existing artifact evidence: $path" >&2
    exit 2
  fi
done

mkdir -p "$ARTIFACTS"
cp --preserve=mode,timestamps "$0" "$ARTIFACTS/run_producer.sh.archived"

PRODUCER_SHA="$($PYTHON - "$ROOT" "$PHASE" "$PRODUCER" "$ARTIFACTS/run_producer.sh" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

root, phase, producer, wrapper = map(Path, sys.argv[1:])
analysis_path = phase / "analysis.json"
series_path = phase / "series.json"
analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
closure = analysis["input_sha256_before"]
if closure != analysis["input_sha256_after"]:
    raise SystemExit("analysis input closure before/after mismatch")

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

for original, expected in closure.items():
    if sha(original) != expected:
        raise SystemExit("analysis closure is stale: " + original)

selected = [
    producer, wrapper, analysis_path, series_path,
    root / "stability_adapter_2/analyze_quiet_wrist_support.py",
    root / "stability_adapter_2/run_quiet_wrist_support.py",
    root / "stability_adapter_2/run_quiet_wrist_support_phase.py",
    root / "stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md",
    root / "stability_adapter_2/QUIET_WRIST_SUPPORT_EXECUTION.md",
    phase / "plus_execution.json", phase / "plus.log",
    phase / "minus_execution.json", phase / "minus.log",
]
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

wrapper_archive = Path(str(wrapper) + ".archived")
wrapper_archive_copy = source_root / "artifacts/run_producer.sh.archived"
wrapper_archive_copy.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(wrapper_archive, wrapper_archive_copy)
wrapper_archive_sha = sha(wrapper_archive)
wrapper_archive_copy_sha = sha(wrapper_archive_copy)
if wrapper_archive_sha != wrapper_archive_copy_sha:
    raise SystemExit("archived wrapper copy SHA mismatch")
files.append({"original_path": str(wrapper_archive), "copy_path": str(wrapper_archive_copy), "sha256": wrapper_archive_sha, "copy_sha256": wrapper_archive_copy_sha})
manifest = {"files": files, "analysis_closure_count": len(closure), "analysis_source_archive": str(phase / "analysis_source_manifest.json"), "scope": "selected direct JSON/code/log inputs are copied here; full native/source closure remains in the analyzer source archive"}
(phase / "artifact_source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

source_sha = sha(producer)
if not any(item["original_path"] == str(producer) and item["sha256"] == source_sha for item in files):
    raise SystemExit("producer was not exact-SHA archived")
input_before = dict(closure)
input_before[str(analysis_path)] = sha(analysis_path)
input_before[str(series_path)] = sha(series_path)
for item in files:
    input_before[item["original_path"]] = item["sha256"]
manifest_path = phase / "artifact_source_manifest.json"
input_before[str(manifest_path)] = sha(manifest_path)
command = ["/home/ajou/miniconda3/envs/rl38/bin/python", "-u", "-m", "stability_adapter_2.make_quiet_wrist_artifacts"]
environment = {
    "QUIET_WRIST_PRODUCER_SHA256": source_sha,
    "MPLBACKEND": "Agg",
    "MPLCONFIGDIR": "/tmp/stability2_quiet_wrist_artifacts",
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

export QUIET_WRIST_PRODUCER_SHA256="$PRODUCER_SHA"
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/stability2_quiet_wrist_artifacts
COMMAND=("$PYTHON" -u -m stability_adapter_2.make_quiet_wrist_artifacts)
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
invocation_path = phase / "artifact_invocation.json"
invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
before = dict(invocation["input_sha256_before"])
before[str(invocation_path)] = hashlib.sha256(invocation_path.read_bytes()).hexdigest()
wrapper_archive = artifacts / "run_producer.sh.archived"
wrapper_sha = invocation["wrapper_sha256_before"]
if wrapper_sha != hashlib.sha256((artifacts / "run_producer.sh").read_bytes()).hexdigest() or wrapper_sha != hashlib.sha256(wrapper_archive.read_bytes()).hexdigest():
    raise SystemExit("archived wrapper SHA changed")
after = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in before}
log_path = phase / "artifact.log"
log_sha = hashlib.sha256(log_path.read_bytes()).hexdigest()
outputs = {}
for path in (artifacts / "quiet_wrist_support_response.png", artifacts / "manifest.json"):
    if path.is_file():
        outputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
env_keys = ["QUIET_WRIST_PRODUCER_SHA256", "MPLBACKEND", "MPLCONFIGDIR"]
record = {
    "command": command,
    "cwd": str(root),
    "environment": {key: os.environ[key] for key in env_keys},
    "exit_code": int(status),
    "wall_seconds": float(end) - float(start),
    "producer_sha256_before": invocation["producer_sha256_before"],
    "producer_sha256_after": hashlib.sha256((root / "stability_adapter_2/make_quiet_wrist_artifacts.py").read_bytes()).hexdigest(),
    "wrapper_sha256_before": wrapper_sha,
    "wrapper_sha256_after": hashlib.sha256((artifacts / "run_producer.sh").read_bytes()).hexdigest(),
    "input_sha256_before": before,
    "input_sha256_after": after,
    "log_sha256": log_sha,
    "outputs_sha256": outputs,
}
(phase / "artifact_execution.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if int(status) != 0 or before != after or record["producer_sha256_after"] != producer_sha or record["wrapper_sha256_after"] != wrapper_sha:
    raise SystemExit("artifact stage failed or a source/input changed")
PY
