#!/usr/bin/env python3
"""Preserve prior videos and copy completed wrist-feedback videos byte-for-byte."""

from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path("/home/ajou/yigyu/3")
DATA = ROOT / "docs/2026-10-12/stability_adapter_2"
PHASE = DATA / "results/quiet_wrist_yz_feedback_v1"
VIDEO_DIR = DATA / "videos"
OLD_INDEX = DATA / "VIDEO_INDEX_v16.md"
NEW_INDEX = DATA / "VIDEO_INDEX_v17.md"
UPDATE = DATA / "video_collection_update_v16.json"
CONDITIONS = ("off", "on")
VIEWS = ("whole_body", "hands")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def main():
    if NEW_INDEX.exists() or UPDATE.exists():
        raise RuntimeError("refusing to overwrite video index or collection update")
    analysis = read_json(PHASE / "analysis.json")
    if not analysis.get("checks") or not all(analysis["checks"].values()):
        raise ValueError("saved analysis must contain only passing checks")
    if analysis.get("physical_initializations") != 2 or analysis.get("physical_steps") != 2400:
        raise ValueError("analysis must describe two completed 1200-step trials")
    if analysis.get("actor_inference_calls") != 0 or analysis.get("training_updates") != 0:
        raise ValueError("this phase must not include actor inference or training")

    previous_videos = sorted(VIDEO_DIR.glob("*.mp4"))
    if len(previous_videos) != 166:
        raise ValueError("expected the preserved 166-video collection before append")
    old_video_sha = {str(path): sha256(path) for path in previous_videos}
    old_index_sha = sha256(OLD_INDEX)
    pending = []
    for condition in CONDITIONS:
        report = read_json(PHASE / "native" / condition / "report.json")
        if (report.get("completed") is not True or report.get("failure") is not None
                or report.get("physics_steps") != 1200 or report.get("simulation_elapsed_s") != 5.0
                or report.get("native_initialization_attempts") != 1
                or report.get("native_initializations") != 1
                or report.get("constraint_violations") != []
                or not report.get("checks") or not all(report["checks"].values())):
            raise ValueError(condition + " report does not describe one complete violation-free 5-second trial")
        videos = read_json(PHASE / "native" / condition / "videos.json")
        if set(videos) != set(VIEWS):
            raise ValueError(condition + " must provide hands and whole_body video metadata")
        for view in VIEWS:
            item = videos[view]
            source = Path(item["path"])
            if not source.is_file() or sha256(source) != item["sha256"]:
                raise ValueError(condition + " " + view + " source video SHA mismatch")
            stream = item.get("stream", {})
            if (item.get("ffmpeg_exit_code") != 0 or item.get("ffprobe_exit_code") != 0
                    or stream.get("nb_read_frames") != "151" or stream.get("avg_frame_rate") != "30/1"
                    or abs(float(stream.get("duration", "nan")) - 151 / 30.0) > 1e-6):
                raise ValueError(condition + " " + view + " is not a complete 151-frame/30-fps/5-second recording")
            destination = VIDEO_DIR / ("quiet_wrist_yz_feedback_v1__native__" + condition + "__" + view + ".mp4")
            if destination.exists():
                raise RuntimeError("refusing to overwrite collected video: " + str(destination))
            pending.append((condition, view, source, destination, item["sha256"], float(stream["duration"])))

    if NEW_INDEX.exists() or UPDATE.exists():
        raise RuntimeError("collection outputs appeared during validation")
    if any(Path(path).is_file() and sha256(path) != digest for path, digest in old_video_sha.items()):
        raise RuntimeError("a prior video changed during collection preparation")
    copies = []
    for condition, view, source, destination, digest, duration in pending:
        shutil.copy2(source, destination)
        copied_sha = sha256(destination)
        if copied_sha != digest:
            raise RuntimeError("byte-for-byte video copy SHA mismatch: " + str(destination))
        copies.append({
            "trial": condition,
            "view": view,
            "partial": False,
            "source": str(source),
            "copy": str(destination),
            "sha256": digest,
            "copy_sha256": copied_sha,
            "size": destination.stat().st_size,
            "duration_s": duration,
            "frame_count": 151,
            "fps": "30/1",
        })

    if any(sha256(Path(path)) != digest for path, digest in old_video_sha.items()):
        raise RuntimeError("a prior video changed during collection")
    if sha256(OLD_INDEX) != old_index_sha:
        raise RuntimeError("prior video index changed during collection")
    if len(list(VIDEO_DIR.glob("*.mp4"))) != 170:
        raise RuntimeError("expected 170 total videos after adding four complete recordings")

    lines = [
        "# 영상 모음 v17 — 170개",
        "",
        "Quiet wrist Y/Z feedback OFF/ON의 완료된 실제 Isaac Gym 영상 4개다. 기존 166개는 보존하고 새 파일은 재인코딩 없이 SHA exact 복사했다. 각 영상은 151 frame/30 fps, 재생 5.033333초이며 마지막 simulation 표본은 5.000초다.",
        "",
    ]
    for condition in CONDITIONS:
        lines.extend([
            "## quiet_wrist_yz_feedback_v1 — " + condition.upper(),
            "",
            "| 카메라 | 영상 | 재생시간(초) |",
            "|---|---|---:|",
        ])
        for item in copies:
            if item["trial"] == condition:
                lines.append("| " + item["view"] + " | [" + Path(item["copy"]).name + "](" + item["copy"] + ") | " + format(item["duration_s"], ".6f") + " |")
        lines.append("")
        lines.extend("![" + item["view"] + "](" + item["copy"] + ")" for item in copies if item["trial"] == condition)
        lines.append("")
    NEW_INDEX.write_text("\n".join(lines) + "\n" + OLD_INDEX.read_text(encoding="utf-8"), encoding="utf-8")
    UPDATE.write_text(json.dumps({
        "previous_index_sha256": old_index_sha,
        "new_index_sha256": sha256(NEW_INDEX),
        "previous_video_sha256": old_video_sha,
        "copies": copies,
        "total_count": 170,
        "analysis_input_count": len(analysis.get("input_sha256_before", {})),
        "scope": "four completed native videos are copied byte-for-byte; selected source copies are distinct from the full analysis hash closure",
        "producer_sha256": sha256(Path(__file__).resolve()),
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
