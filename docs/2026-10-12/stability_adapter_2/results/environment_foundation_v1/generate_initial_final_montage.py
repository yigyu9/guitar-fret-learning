#!/usr/bin/env python3
"""Create a comparison montage from hash-verified native Isaac Gym PNG frames."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
RUNS = ("native_neutral_v2", "native_small_motion_v2")
VIEWS = ("whole_body", "hands")
FRAME_INDICES = (0, 150)
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
OUT = BASE / "initial_final_montage.png"
MANIFEST = BASE / "producer_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def input_paths() -> list[Path]:
    paths = [Path("/home/ajou/yigyu/3/stability_adapter_2/environment_foundation_v1.json"), BASE / "analysis.json"]
    for run in RUNS:
        run_dir = BASE / run
        paths.extend((run_dir / "report.json", run_dir / "media/capture.json", run_dir / "media/videos.json",
                      run_dir / "media/whole_body.mp4", run_dir / "media/hands.mp4"))
        for view in VIEWS:
            for index in FRAME_INDICES:
                paths.append(run_dir / "media" / "frames" / view / f"{index:05d}.png")
    return paths


def main() -> None:
    sources = input_paths()
    input_sha_before = {str(path): sha256(path) for path in sources}
    # Four source panels per run: whole-body and hands views at t=0 and t=5 s.
    tile_w, tile_h = 520, 293
    left, gap = 245, 14
    top = 195
    row_h = tile_h + 68
    width = left + 4 * tile_w + 3 * gap + 32
    height = top + 2 * row_h + 28
    canvas = Image.new("RGB", (width, height), "#f4f6f8")
    draw = ImageDraw.Draw(canvas)

    draw.text((32, 22), "상체 고정 하체 환경 · native 시작/5초 프레임 비교", font=font(32), fill="#172b4d")
    draw.text((32, 69), "설명용 원본 프레임 몽타주 | 물리 5.000초 | 학습 결과 아님", font=font(22), fill="#44546a")
    draw.rounded_rectangle((32, 111, width - 32, 151), radius=8, fill="#fff0dc", outline="#d97706", width=2)
    draw.text((48, 119), "CPU PhysX · Vulkan software graphics · strap OFF · root/하체 fixed · guitar free", font=font(19), fill="#7c2d12")

    headers = ["Whole body · 00000 / 0초", "Whole body · 00150 / 5초", "Hands · 00000 / 0초", "Hands · 00150 / 5초"]
    for col, label in enumerate(headers):
        x = left + col * (tile_w + gap)
        draw.text((x, top - 36), label, font=font(17), fill="#172b4d")

    for row, run in enumerate(RUNS):
        y = top + row * row_h
        run_label = "중립\n목표" if row == 0 else "작은\n목표 움직임"
        draw.rounded_rectangle((26, y + 94, left - 22, y + 194), radius=12,
                               fill="#e6f0ff" if row == 0 else "#e8f5e9", outline="#718096", width=2)
        for i, line in enumerate(run_label.split("\n")):
            draw.text((45, y + 113 + i * 31), line, font=font(20), fill="#172b4d")
        for v_i, view in enumerate(VIEWS):
            for t_i, idx in enumerate(FRAME_INDICES):
                col = v_i * 2 + t_i
                x = left + col * (tile_w + gap)
                frame = BASE / run / "media" / "frames" / view / f"{idx:05d}.png"
                capture = json.loads((BASE / run / "media" / "capture.json").read_text())
                frame_entry = capture["frames"][idx]
                assert frame_entry["physics_step"] == (0 if idx == 0 else 1200)
                assert frame_entry["time_s"] == (0.0 if idx == 0 else 5.0)
                expected = frame_entry["image_sha256"][str(frame.resolve())]
                assert sha256(frame) == expected, f"source frame hash mismatch: {frame}"
                image = Image.open(frame).convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
                canvas.paste(image, (x, y))
                draw.rectangle((x, y, x + tile_w - 1, y + tile_h - 1), outline="#8492a6", width=2)
                caption = f"{view} · frame {idx:05d} · {idx / 30:.1f}초"
                draw.text((x + 5, y + tile_h + 8), caption, font=font(16), fill="#344563")

    canvas.save(OUT, format="PNG", optimize=True)
    input_sha_after = {str(path): sha256(path) for path in sources}
    assert input_sha_before == input_sha_after, "source inputs changed during montage generation"
    outputs = (BASE / "README.md", OUT, Path(__file__).resolve())
    manifest = {
        "artifact": "environment_foundation_v1 native initial/final image montage and explanation",
        "created_by": str(Path(__file__).resolve()),
        "source_scope": "post-processing only; no physics run, environment change, reward, or PPO training",
        "frame_selection": {
            "indices": list(FRAME_INDICES), "physics_steps": [0, 1200],
            "physics_times_seconds": [0.0, 5.0], "views": list(VIEWS), "runs": list(RUNS),
        },
        "source_frame_sha256_verified_against_capture_json": True,
        "input_sha256_before": input_sha_before,
        "input_sha256_after": input_sha_after,
        "inputs_unchanged_during_production": True,
        "output_sha256": {str(path): sha256(path) for path in outputs},
        "montage_size_px": [canvas.width, canvas.height],
        "video_encoding_note": "151 frames at 30 fps (5.033333 s encoded duration); physics simulation duration is 5.0 s.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{OUT} {canvas.width}x{canvas.height} sha256={sha256(OUT)}")


if __name__ == "__main__":
    main()
