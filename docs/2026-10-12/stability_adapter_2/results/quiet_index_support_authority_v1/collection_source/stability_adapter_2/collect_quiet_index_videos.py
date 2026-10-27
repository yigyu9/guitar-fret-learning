"""Copy completed and partial quiet-index videos and append collection v14."""

from pathlib import Path
import hashlib
import json
import shutil


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/2026-10-12/stability_adapter_2"
PHASE = DATA / "results/quiet_index_support_authority_v1"
VIDEO_DIR = DATA / "videos"
OLD_INDEX = DATA / "VIDEO_INDEX_v13.md"
NEW_INDEX = DATA / "VIDEO_INDEX_v14.md"
UPDATE = DATA / "video_collection_update_v13.json"
ANALYSIS = PHASE / "analysis.json"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    if NEW_INDEX.exists() or UPDATE.exists():
        raise RuntimeError("refusing to overwrite the frozen v14 index/update")
    old_videos = sorted(VIDEO_DIR.glob("*.mp4"))
    if len(old_videos) != 152:
        raise RuntimeError("expected to preserve the existing 152-video collection")
    old_video_hashes = {str(path): sha256(path) for path in old_videos}
    old_index_hash = sha256(OLD_INDEX)

    analysis = read_json(ANALYSIS)
    if not analysis.get("checks") or not all(analysis["checks"].values()):
        raise ValueError("saved analysis must have all checks passing before collection")

    pending = []
    for label, folder in (("plus", "plus"), ("minus", "minus_retry_v2")):
        videos = read_json(PHASE / "native" / folder / "videos.json")
        if set(videos) != {"whole_body", "hands"}:
            raise ValueError(label + " trial does not contain exactly the two expected camera videos")
        for view in ("whole_body", "hands"):
            item = videos[view]
            source = Path(item["path"])
            expected = item["sha256"]
            destination = VIDEO_DIR / ("quiet_index_support_authority_v1__native__" + label + "__" + view + ".mp4")
            if (destination.exists() or sha256(source) != expected or
                    item.get("stream", {}).get("nb_read_frames") != "151" or
                    item.get("stream", {}).get("avg_frame_rate") != "30/1"):
                raise RuntimeError("missing, changed, or already-copied source video: " + str(source))
            pending.append((label, view, source, destination, expected, False, float(item["stream"]["duration"])))

    partial_videos = read_json(PHASE / "partial_videos/videos.json")
    if set(partial_videos) != {"whole_body", "hands"}:
        raise ValueError("crash record must contain the two preserved partial videos")
    for view in ("whole_body", "hands"):
        item = partial_videos[view]
        source = Path(item["path"])
        expected = item["sha256"]
        destination = VIDEO_DIR / ("quiet_index_support_authority_v1__native__minus_crash_partial__" + view + ".mp4")
        if (destination.exists() or sha256(source) != expected or not item.get("partial") or
                item.get("ffmpeg_exit_code") != 0 or item.get("stream", {}).get("nb_read_frames") != "19" or
                item.get("stream", {}).get("duration") != "0.633333" or item.get("last_captured_simulation_s") != 0.6):
            raise RuntimeError("partial video metadata/source mismatch: " + str(source))
        pending.append(("minus_crash_partial", view, source, destination, expected, True, float(item["stream"]["duration"])))

    copies = []
    for label, view, source, destination, expected, partial, duration_s in pending:
        shutil.copy2(source, destination)
        copy_sha = sha256(destination)
        if copy_sha != expected:
            raise RuntimeError("video copy SHA mismatch: " + str(destination))
        copies.append({
            "trial": label,
            "view": view,
            "partial": partial,
            "source": str(source),
            "copy": str(destination),
            "sha256": expected,
            "copy_sha256": copy_sha,
            "size": destination.stat().st_size,
            "duration_s": duration_s,
        })

    if any(sha256(path) != digest for path, digest in old_video_hashes.items()) or sha256(OLD_INDEX) != old_index_hash:
        raise RuntimeError("an existing collection item changed during copy")
    if len(list(VIDEO_DIR.glob("*.mp4"))) != 158:
        raise RuntimeError("expected 152 preserved videos plus four completed and two partial copies")

    lines = [
        "# 영상 모음 v14 — 158개",
        "",
        "quiet index-support authority 비교의 완료된 plus/minus 실제 Isaac Gym strap-on 전체 몸/손 영상 4개와, 첫 minus 시도에서 보존한 19프레임 부분 영상 2개입니다. 기존 v13의 152개 항목은 그대로 두고 재인코딩 없이 복사했습니다. 부분 영상의 재생시간은 19/30초(0.633333초)이며, 관측된 시뮬레이션 시각 0.633333초 또는 5초 완료 영상으로 혼동하지 않도록 완료 영상과 별도 표기합니다.",
        "",
    ]
    for trial in ("plus", "minus"):
        lines.extend(["## quiet_index_support_authority_v1 — " + trial + " 완료 trial", "", "| 카메라 | 영상 | 재생시간(초) | 시뮬레이션 종료시각(초) |", "|---|---|---:|---:|"])
        for item in [entry for entry in copies if entry["trial"] == trial]:
            lines.append("| " + item["view"] + " | [" + Path(item["copy"]).name + "](" + item["copy"] + ") | " + format(item["duration_s"], ".6f") + " | 5.0 |")
        lines.extend(["", *["![" + Path(item["copy"]).name + "](" + item["copy"] + ")" for item in copies if item["trial"] == trial], ""])
    lines.extend(["## quiet_index_support_authority_v1 — first minus crash partial", "", "| 카메라 | 영상 | 재생시간(초) | 마지막 저장 frame의 시뮬레이션 시각(초) |", "|---|---|---:|---:|"])
    for item in [entry for entry in copies if item_is_partial(entry)]:
        lines.append("| " + item["view"] + " | [" + Path(item["copy"]).name + "](" + item["copy"] + ") | " + format(item["duration_s"], ".6f") + " | 0.6 |")
    lines.extend(["", *["![" + Path(item["copy"]).name + "](" + item["copy"] + ")" for item in copies if item_is_partial(item)], ""])
    new_text = "\n".join(lines) + "\n" + OLD_INDEX.read_text(encoding="utf-8")
    NEW_INDEX.write_text(new_text, encoding="utf-8")
    update = {
        "previous_index_sha256": old_index_hash,
        "new_index_sha256": sha256(NEW_INDEX),
        "previous_video_sha256": old_video_hashes,
        "copies": copies,
        "total_count": 158,
        "producer_sha256": sha256(Path(__file__)),
    }
    UPDATE.write_text(json.dumps(update, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(NEW_INDEX))


def item_is_partial(item):
    return item.get("partial") is True


if __name__ == "__main__":
    main()
