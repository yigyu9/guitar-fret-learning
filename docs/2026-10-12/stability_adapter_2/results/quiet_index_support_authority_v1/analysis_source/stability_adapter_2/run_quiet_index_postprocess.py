"""Archive and run one saved-data analysis or video-collection stage."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "stability_adapter_2"
DATA = ROOT / "docs/2026-10-12/stability_adapter_2"
PHASE = DATA / "results/quiet_index_support_authority_v1"
BASELINE = DATA / "results/initial_middle3_alignment_v1/native"
BASELINE_TASKS = BASELINE / "tasks.jsonl"
RUNNER = APP / "run_quiet_index_postprocess.py"
ANALYZER = APP / "analyze_quiet_index_support_v2.py"
COLLECTOR = APP / "collect_quiet_index_videos.py"
PLAN = APP / "QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md"
LEAF = APP / "QUIET_INDEX_SUPPORT_EXECUTION.md"
RETRY_LEAF = APP / "QUIET_INDEX_NATIVE_RETRY_V2.md"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_capture_inputs(paths, folder):
    capture = read_json(folder / "capture.json")
    videos = read_json(folder / "videos.json")
    for frame in capture["frames"]:
        for key in ("image_sha256", "raw_image_sha256"):
            for image_path in frame.get(key, {}):
                paths.add(Path(image_path))
    for item in videos.values():
        paths.add(Path(item["path"]))


def copy_inputs(paths, stage):
    before = {}
    snapshots = []
    for path in sorted(paths, key=str):
        if not path.is_file():
            raise FileNotFoundError(str(path))
        digest = sha256(path)
        before[str(path)] = digest
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            relative = Path("external") / path.as_posix().lstrip("/")
        destination = PHASE / (stage + "_source") / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copy_digest = sha256(destination)
        if copy_digest != digest:
            raise RuntimeError("snapshot SHA mismatch: " + str(path))
        snapshots.append({"original_path": str(path), "copy_path": str(destination), "sha256": digest, "copy_sha256": copy_digest})
    write_json(PHASE / (stage + "_source_manifest.json"), {"files": snapshots})
    return before


def analysis_inputs():
    paths = {RUNNER, ANALYZER, PLAN, LEAF, RETRY_LEAF, BASELINE_TASKS}
    for label, folder in [("baseline", BASELINE), ("plus", PHASE / "native/plus"), ("minus", PHASE / "native/minus_retry_v2")]:
        paths.update(folder / name for name in (
            "initial_values.json", "states.jsonl", "trace.jsonl", "controls.jsonl",
            "contacts.jsonl", "report.json", "initial_grip_audit.json", "capture.json", "videos.json",
        ))
        add_capture_inputs(paths, folder)
        if label == "plus":
            paths.update({PHASE / "plus_execution.json", PHASE / "plus_inputs.json", PHASE / "plus_invocation.json", PHASE / "plus.log"})
        elif label == "minus":
            paths.update({PHASE / "minus_retry_v2_execution.json", PHASE / "minus_retry_v2_inputs.json", PHASE / "minus_retry_v2_invocation.json", PHASE / "minus_retry_v2.log", PHASE / "minus_retry_v2_source_manifest.json"})
    crash_record = PHASE / "minus_native_crash.json"
    crash = read_json(crash_record)
    paths.update({crash_record, PHASE / "minus_execution.json", PHASE / "minus_inputs.json", PHASE / "minus_invocation.json", PHASE / "minus.log"})
    paths.update(Path(path) for path in crash["output_inventory"])
    paths.update({PHASE / "partial_videos/videos.json"})
    partial = read_json(PHASE / "partial_videos/videos.json")
    paths.update(Path(item["path"]) for item in partial.values())
    execution_files = [PHASE / name for name in ("plus_execution.json", "minus_execution.json", "minus_retry_v2_execution.json")]
    for execution_file in execution_files:
        paths.add(execution_file)
        execution = read_json(execution_file)
        paths.update(Path(path) for path in execution["input_sha256_before"])
    return paths


def collection_inputs():
    index = DATA / "VIDEO_INDEX_v13.md"
    paths = {RUNNER, COLLECTOR, index, PHASE / "analysis.json"}
    paths.update(Path(path) for path in (PHASE / "native/plus/videos.json", PHASE / "native/minus_retry_v2/videos.json", PHASE / "partial_videos/videos.json"))
    for label in ("plus", "minus"):
        folder = "plus" if label == "plus" else "minus_retry_v2"
        video_data = read_json(PHASE / "native" / folder / "videos.json")
        paths.update(Path(item["path"]) for item in video_data.values())
    partial = read_json(PHASE / "partial_videos/videos.json")
    paths.update(Path(item["path"]) for item in partial.values())
    paths.update((DATA / "videos").glob("*.mp4"))
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("analysis", "collection"))
    stage = parser.parse_args().stage
    if stage == "analysis":
        outputs = [PHASE / "analysis.json", PHASE / "series.json"]
        module = "analyze_quiet_index_support_v2"
        paths = analysis_inputs()
    else:
        outputs = [DATA / "VIDEO_INDEX_v14.md", DATA / "video_collection_update_v13.json"]
        module = "collect_quiet_index_videos"
        paths = collection_inputs()
    execution = PHASE / (stage + "_execution.json")
    invocation = PHASE / (stage + "_invocation.json")
    log_path = PHASE / (stage + ".log")
    manifest_path = PHASE / (stage + "_source_manifest.json")
    source_dir = PHASE / (stage + "_source")
    if any(path.exists() for path in outputs + [execution, invocation, log_path, manifest_path, source_dir]):
        raise RuntimeError("stage outputs already exist; refusing to overwrite")

    PHASE.mkdir(parents=True, exist_ok=True)
    before = copy_inputs(paths, stage)
    command = [sys.executable, "-u", "-m", "stability_adapter_2." + module]
    environment = dict(os.environ)
    environment.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MPLBACKEND": "Agg"})
    env_keys = ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MPLBACKEND"]
    write_json(invocation, {"command": command, "cwd": str(ROOT), "environment": {key: environment[key] for key in env_keys}, "input_sha256": before})
    before[str(invocation)] = sha256(invocation)

    started = time.monotonic()
    with log_path.open("xb") as log_stream:
        result = subprocess.run(command, cwd=str(ROOT), env=environment, stdout=log_stream, stderr=subprocess.STDOUT)
    after = {path: sha256(path) for path in before}
    record = {
        "stage": stage,
        "command": command,
        "cwd": str(ROOT),
        "environment": {key: environment[key] for key in env_keys},
        "exit_code": result.returncode,
        "wall_seconds": time.monotonic() - started,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "log_sha256": sha256(log_path),
    }
    write_json(execution, record)
    print(log_path.read_text(encoding="utf-8", errors="replace")[-6000:])
    if result.returncode != 0 or before != after:
        raise RuntimeError("postprocess failed or changed a sealed input; see " + str(execution))


if __name__ == "__main__":
    main()
