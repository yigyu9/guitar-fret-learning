#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ajou/yigyu/3
DATA="$ROOT/docs/2026-10-12/stability_adapter_2"
PHASE="$DATA/results/quiet_wrist_yz_feedback_v1"
ARTIFACTS="$PHASE/artifacts"
COLLECTOR="$ROOT/stability_adapter_2/collect_wrist_yz_feedback_videos.py"
PYTHON=/home/ajou/miniconda3/envs/rl38/bin/python

for path in \
  "$ARTIFACTS/collection_producer.sh.archived" \
  "$PHASE/collection_source" \
  "$PHASE/collection_source_manifest.json" \
  "$PHASE/collection_invocation.json" \
  "$PHASE/collection_execution.json" \
  "$PHASE/collection.log" \
  "$DATA/VIDEO_INDEX_v17.md" \
  "$DATA/video_collection_update_v16.json"; do
  if [[ -e "$path" ]]; then
    echo "refusing to overwrite existing collection evidence: $path" >&2
    exit 2
  fi
done

for path in \
  "$PHASE/analysis.json" "$PHASE/series.json" \
  "$PHASE/off_execution.json" "$PHASE/off.log" "$PHASE/off_inputs.json" \
  "$PHASE/on_execution.json" "$PHASE/on.log" "$PHASE/on_inputs.json" \
  "$PHASE/native/off/report.json" "$PHASE/native/off/capture.json" "$PHASE/native/off/videos.json" \
  "$PHASE/native/on/report.json" "$PHASE/native/on/capture.json" "$PHASE/native/on/videos.json" \
  "$DATA/VIDEO_INDEX_v16.md"; do
  if [[ ! -f "$path" ]]; then
    echo "required completed trial, analysis, or preserved index is missing: $path" >&2
    exit 3
  fi
done

for condition in off on; do
  for view in hands whole_body; do
    if [[ ! -f "$PHASE/native/$condition/$view.mp4" ]]; then
      echo "required completed native video is missing: $PHASE/native/$condition/$view.mp4" >&2
      exit 3
    fi
    destination="$DATA/videos/quiet_wrist_yz_feedback_v1__native__${condition}__${view}.mp4"
    if [[ -e "$destination" ]]; then
      echo "refusing to overwrite collected video: $destination" >&2
      exit 2
    fi
  done
done

mkdir -p "$ARTIFACTS"
cp --preserve=mode,timestamps "$0" "$ARTIFACTS/collection_producer.sh.archived"

COLLECTOR_SHA="$("$PYTHON" - "$ROOT" "$DATA" "$PHASE" "$COLLECTOR" "$ARTIFACTS/collection_producer.sh" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

root, data, phase, collector, wrapper = map(Path, sys.argv[1:])
analysis_path = phase / "analysis.json"
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
    collector, wrapper, analysis_path, phase / "series.json",
    data / "VIDEO_INDEX_v16.md",
    root / "stability_adapter_2/analyze_quiet_wrist_yz_feedback.py",
    root / "stability_adapter_2/run_quiet_wrist_yz_feedback.py",
    root / "stability_adapter_2/run_quiet_wrist_yz_feedback_phase.py",
    root / "stability_adapter_2/wrist_yz_guitar_feedback.py",
    root / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md",
    root / "stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md",
    phase / "off_inputs.json", phase / "off_invocation.json", phase / "off_execution.json", phase / "off.log",
    phase / "on_inputs.json", phase / "on_invocation.json", phase / "on_execution.json", phase / "on.log",
]
for condition in ("off", "on"):
    native = phase / "native" / condition
    for name in ("attempt.json", "initial_values.json", "report.json", "capture.json", "videos.json"):
        selected.append(native / name)
    for view in ("whole_body", "hands"):
        selected.append(native / (view + ".mp4"))
source_root = phase / "collection_source"
source_root.mkdir(parents=True, exist_ok=False)
files = []
for original in selected:
    if not original.is_file():
        raise SystemExit("missing selected collection input: " + str(original))
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
        raise SystemExit("collection source copy mismatch: " + str(original))
    files.append({"original_path": str(original), "copy_path": str(copied), "sha256": digest, "copy_sha256": copied_sha})

archive = Path(str(wrapper) + ".archived")
archive_copy = source_root / "artifacts/collection_producer.sh.archived"
archive_copy.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(archive, archive_copy)
archive_sha = sha(archive)
if sha(archive_copy) != archive_sha:
    raise SystemExit("archived collection wrapper copy SHA mismatch")
files.append({"original_path": str(archive), "copy_path": str(archive_copy), "sha256": archive_sha, "copy_sha256": sha(archive_copy)})
manifest_path = phase / "collection_source_manifest.json"
manifest_path.write_text(json.dumps({
    "files": files,
    "analysis_closure_count": len(closure),
    "analysis_source_archive": str(phase / "analysis_source_manifest.json"),
    "scope": "selected collection metadata and four source MP4 files are copied here; all 166 preserved prior videos and the full analysis closure are hash-checked but are not copied into this selected-input archive",
}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

input_before = dict(closure)
for original in (analysis_path, phase / "series.json", data / "VIDEO_INDEX_v16.md"):
    input_before[str(original)] = sha(original)
for video in sorted((data / "videos").glob("*.mp4")):
    input_before[str(video)] = sha(video)
for item in files:
    input_before[item["original_path"]] = item["sha256"]
input_before[str(manifest_path)] = sha(manifest_path)
command = ["/home/ajou/miniconda3/envs/rl38/bin/python", "-u", "-m", "stability_adapter_2.collect_wrist_yz_feedback_videos"]
environment = {"PYTHONPATH": str(root)}
invocation_path = phase / "collection_invocation.json"
invocation_path.write_text(json.dumps({
    "command": command,
    "cwd": str(root),
    "environment": environment,
    "collector_sha256_before": sha(collector),
    "wrapper_sha256_before": sha(wrapper),
    "input_sha256_before": input_before,
    "source_manifest_sha256": sha(manifest_path),
}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(sha(collector))
PY
)"

export PYTHONPATH="$ROOT"
COMMAND=("$PYTHON" -u -m stability_adapter_2.collect_wrist_yz_feedback_videos)
START=$(date +%s.%N)
set +e
"${COMMAND[@]}" >"$PHASE/collection.log" 2>&1
STATUS=$?
set -e
END=$(date +%s.%N)

"$PYTHON" - "$ROOT" "$DATA" "$PHASE" "$COLLECTOR_SHA" "$STATUS" "$START" "$END" "${COMMAND[@]}" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

root, data, phase = map(Path, sys.argv[1:4])
collector_sha, status, start, end = sys.argv[4:7]
command = sys.argv[7:]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
invocation_path = phase / "collection_invocation.json"
invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
before = dict(invocation["input_sha256_before"])
before[str(invocation_path)] = sha(invocation_path)
artifacts = phase / "artifacts"
wrapper_archive = artifacts / "collection_producer.sh.archived"
wrapper_sha = invocation["wrapper_sha256_before"]
if wrapper_sha != sha(artifacts / "collection_producer.sh") or wrapper_sha != sha(wrapper_archive):
    raise SystemExit("archived collection wrapper SHA changed")
after = {path: sha(Path(path)) for path in before}
log_path = phase / "collection.log"
outputs = {}
for path in (data / "VIDEO_INDEX_v17.md", data / "video_collection_update_v16.json"):
    if path.is_file():
        outputs[str(path)] = sha(path)
for condition in ("off", "on"):
    for view in ("whole_body", "hands"):
        path = data / "videos" / ("quiet_wrist_yz_feedback_v1__native__" + condition + "__" + view + ".mp4")
        if path.is_file():
            outputs[str(path)] = sha(path)
record = {
    "command": command,
    "cwd": str(root),
    "environment": {"PYTHONPATH": os.environ["PYTHONPATH"]},
    "exit_code": int(status),
    "wall_seconds": float(end) - float(start),
    "collector_sha256_before": invocation["collector_sha256_before"],
    "collector_sha256_after": sha(root / "stability_adapter_2/collect_wrist_yz_feedback_videos.py"),
    "wrapper_sha256_before": wrapper_sha,
    "wrapper_sha256_after": sha(artifacts / "collection_producer.sh"),
    "input_sha256_before": before,
    "input_sha256_after": after,
    "log_sha256": sha(log_path),
    "outputs_sha256": outputs,
}
(phase / "collection_execution.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if int(status) != 0 or before != after or record["collector_sha256_after"] != collector_sha or record["wrapper_sha256_after"] != wrapper_sha:
    raise SystemExit("collection stage failed or a source/input changed")
PY
