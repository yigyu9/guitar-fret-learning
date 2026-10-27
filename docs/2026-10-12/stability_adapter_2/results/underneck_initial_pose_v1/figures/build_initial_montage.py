#!/usr/bin/env python3
"""Make a labeled contact sheet from the already saved native initial views."""
import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PHASE = Path(__file__).resolve().parents[1]
RUN = PHASE / "native_refine10000"
INPUTS = {
    "initial_values": RUN / "initial_values.json",
    "initial_audit": RUN / "initial_audit.json",
    "report": RUN / "report.json",
    "capture": RUN / "images" / "capture.json",
    "selected_candidate": PHASE / "refine" / "candidate_w10000.json",
    "whole_body_frame": RUN / "images" / "frames" / "whole_body" / "00000.png",
    "front_hand_frame": RUN / "images" / "frames" / "hands" / "00000.png",
    "rear_hand_frame": RUN / "rear_hand.png",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=PHASE / "figures" / "initial_views_v1")
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    image_path = out_dir / "initial_native_views.png"
    manifest_path = out_dir / "manifest.json"
    execution_path = out_dir / "artifact_execution.json"
    if out_dir.exists() or image_path.exists() or manifest_path.exists() or execution_path.exists():
        raise FileExistsError(f"refusing to overwrite: {out_dir}")

    started_at = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    producer = Path(__file__).resolve()
    before = {str(producer): sha(producer)}
    before.update({str(path.resolve()): sha(path) for path in INPUTS.values()})
    values = json.loads(INPUTS["initial_values"].read_text())
    audit = json.loads(INPUTS["initial_audit"].read_text())
    report = json.loads(INPUTS["report"].read_text())
    capture = json.loads(INPUTS["capture"].read_text())
    candidate = json.loads(INPUTS["selected_candidate"].read_text())
    if audit.get("checks", {}).get("zero_physics_steps") is not True or report.get("physics_steps") != 0:
        raise ValueError("expected a saved zero-step initial audit")
    if report.get("native_initializations") != 1 or report.get("strap_force_enabled") is not False:
        raise ValueError("unexpected native initial report contract")
    if capture.get("renderer") != "Isaac Gym native camera" or capture.get("frames", [{}])[0].get("physics_step") != 0:
        raise ValueError("expected the recorded native step-0 camera frame")
    if not isinstance(candidate, dict):
        raise ValueError("candidate input is not an object")

    labels = ["Whole body view | saved native step 0", "Front hand view | saved native step 0", "Rear hand view | saved native step 0"]
    keys = ["whole_body_frame", "front_hand_frame", "rear_hand_frame"]
    panel_w, panel_h, label_h = 640, 360, 45
    margin, gap, footer_h = 24, 18, 48
    sheet = Image.new("RGB", (margin * 2 + 3 * panel_w + 2 * gap, margin * 2 + label_h + panel_h + footer_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, (key, label) in enumerate(zip(keys, labels)):
        x = margin + i * (panel_w + gap)
        y = margin
        draw.text((x + 6, y + 14), label, fill="#20252b", font=font)
        im = Image.open(INPUTS[key]).convert("RGB")
        if im.size != (1280, 720):
            raise ValueError(f"unexpected source frame size for {key}: {im.size}")
        im = im.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
        sheet.paste(im, (x, y + label_h))
    draw.text((margin, sheet.height - footer_h + 10), "Saved native camera images, uniformly scaled to fit; no crops, overlays, or new render/physics.", fill="#303840", font=font)
    out_dir.mkdir(parents=True, exist_ok=False)
    sheet.save(image_path, format="PNG", optimize=False)
    after = {path: sha(Path(path)) for path in before}
    if before != after:
        image_path.unlink(missing_ok=True)
        raise RuntimeError("an input changed during montage generation")
    manifest = {
        "inputs_sha256": before,
        "output_sha256": {str(image_path): sha(image_path)},
        "producer_sha256": sha(producer),
        "source_images": [str(INPUTS[k].resolve()) for k in keys],
        "source_image_size_px": [1280, 720],
        "panel_size_px": [panel_w, panel_h],
        "labels": labels,
        "scope": "montage of previously saved native Isaac Gym step-0 images; no crop, overlays, new rendering, or physics",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    execution = {
        "command": [sys.executable, str(producer), "--out-dir", str(out_dir)],
        "environment": {k: __import__("os").environ.get(k) for k in ["MPLCONFIGDIR", "MUJOCO_GL", "PYTHONPATH", "LD_LIBRARY_PATH"]},
        "python": platform.python_version(),
        "started_at_utc": started_at,
        "elapsed_seconds": time.monotonic() - started_clock,
        "returncode": 0,
        "native_initializations": 0,
        "physics_steps": 0,
        "manifest": str(manifest_path),
        "output": str(image_path),
    }
    execution_path.write_text(json.dumps(execution, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(image_path)
    print(manifest_path)
    print(execution_path)


if __name__ == "__main__":
    main()
