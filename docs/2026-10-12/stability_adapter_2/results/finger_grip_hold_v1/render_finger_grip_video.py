"""Post-process saved Isaac Gym camera frames; this script runs no simulator."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PHASE = Path(__file__).resolve().parent
CAPTURE = PHASE / "native_video/frames/capture.json"
CAPTURE_RUN = PHASE / "native_video/run"
REFERENCE_RUN = PHASE / "hold_1s/seed120_palm_feedback_v2"


def read_json(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        raise FileExistsError(f"preserve existing output: {out}")
    out.mkdir(parents=True)

    capture = read_json(CAPTURE)
    trace = read_json(CAPTURE_RUN / "trace.json")
    states = read_json(CAPTURE_RUN / "states.json")
    contacts = read_json(CAPTURE_RUN / "contacts.json")
    if len(capture["frames"]) != 61 or len(trace) != 241:
        raise ValueError("expected 61 captured times and 241 saved native states")
    if len(states) != 241 or capture.get("graphics_device_id") != 0:
        raise ValueError("unexpected camera run length/device metadata")
    if not all(row.get("render_preserves_states") is True for row in capture["frames"]):
        raise ValueError("camera readback did not preserve saved states")

    # The capture run's physical arrays must exactly match the selected 1 s result.
    equivalent_raw = ("trace.json", "states.json", "contacts.json", "controls.json",
                      "leg_torques.json", "lh_contacts.json")
    for name in equivalent_raw:
        if read_json(CAPTURE_RUN / name) != read_json(REFERENCE_RUN / name):
            raise ValueError(f"camera run differs from selected 1 s saved result: {name}")

    source_paths = [CAPTURE, *(CAPTURE_RUN / name for name in
                    ("report.json", "trace.json", "states.json", "contacts.json", "controls.json",
                     "leg_torques.json", "lh_contacts.json")),
                    *(REFERENCE_RUN / name for name in equivalent_raw), Path(__file__).resolve()]
    frame_records = capture["frames"]
    for frame in frame_records:
        step = frame["physics_step"]
        if step % 4 or abs(frame["time_s"] - step / 240) > 1e-12:
            raise ValueError(f"unexpected camera sample mapping at step {step}")
        for image_path, expected in frame["image_sha256"].items():
            path = Path(image_path)
            source_paths.append(path)
            if not path.is_file() or sha(path) != expected:
                raise ValueError(f"captured frame SHA mismatch: {path}")
    source_paths = sorted(set(source_paths))
    before = {str(p): sha(p) for p in source_paths}

    whole0 = Image.open(Path(next(k for k in frame_records[0]["image_sha256"] if "whole_body" in k))).convert("RGB")
    frame_size = whole0.size
    if frame_size != (1280, 720):
        raise ValueError(f"unexpected native camera image dimensions: {frame_size}")
    del whole0

    frame_dir = out / "frames_composited"
    frame_dir.mkdir()
    regular = font(22)
    small = font(18)
    for index, frame in enumerate(frame_records):
        images = frame["image_sha256"]
        whole_path = next(Path(k) for k in images if "whole_body" in k)
        hands_path = next(Path(k) for k in images if "hands" in k)
        whole = Image.open(whole_path).convert("RGB")
        hands = Image.open(hands_path).convert("RGB")
        canvas = Image.new("RGB", (2560, 720))
        canvas.paste(whole, (0, 0))
        canvas.paste(hands, (1280, 0))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle((0, 0, 2559, 34), fill=(0, 0, 0, 210))
        draw.text((18, 4), "Whole body · Isaac Gym native camera", font=regular, fill="white")
        draw.text((1298, 4), "Hands · Isaac Gym native camera", font=regular, fill="white")
        step = frame["physics_step"]
        row = trace[step]
        t = frame["time_s"]
        draw.rectangle((0, 680, 2559, 719), fill=(0, 0, 0, 210))
        draw.text((18, 688), f"t = {t:.3f} s  |  physics step {step}/240  |  playback 0.2×",
                  font=small, fill="white")
        draw.text((860, 688),
                  f"guitar error: {row['position_error_m'] * 1000:.2f} mm, {row['rotation_error_deg']:.3f}°",
                  font=small, fill="white")
        draw.text((1930, 688), "stability not certified", font=small, fill="white")
        canvas.save(frame_dir / f"frame_{index:05d}.png", optimize=True)
        whole.close()
        hands.close()
        canvas.close()

    video = out / "finger_grip_hold_0p2x.mp4"
    ffmpeg = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-framerate", "12",
        "-i", str(frame_dir / "frame_%05d.png"), "-frames:v", "61",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(video),
    ], capture_output=True, text=True, check=True)
    (out / "ffmpeg.log").write_text(ffmpeg.stderr)
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate,nb_read_frames",
        "-of", "json", str(video),
    ], capture_output=True, text=True, check=True)
    probe_data = json.loads(probe.stdout)["streams"][0]
    if (probe_data["codec_name"], probe_data["width"], probe_data["height"],
            probe_data["avg_frame_rate"], probe_data["nb_read_frames"]) != ("h264", 2560, 720, "12/1", "61"):
        raise ValueError(f"unexpected encoded video stream: {probe_data}")
    (out / "ffprobe.json").write_text(json.dumps(probe_data, indent=2) + "\n")

    montage = Image.new("RGB", (2560, 720), "black")
    picks = [0, 12, 32, 60]  # 0, .2, .5333, and 1.0 s (nearest captured frame to contact end)
    draw = ImageDraw.Draw(montage)
    for col, idx in enumerate(picks):
        frame = frame_records[idx]
        hand_path = Path(next(k for k in frame["image_sha256"] if "hands" in k))
        whole_path = Path(next(k for k in frame["image_sha256"] if "whole_body" in k))
        hand = Image.open(hand_path).convert("RGB").resize((640, 360), Image.Resampling.LANCZOS)
        body = Image.open(whole_path).convert("RGB").resize((640, 360), Image.Resampling.LANCZOS)
        montage.paste(body, (col * 640, 0))
        montage.paste(hand, (col * 640, 360))
        draw.text((col * 640 + 12, 12), f"Whole body · {frame['time_s']:.3f} s", font=small, fill="white", stroke_width=2, stroke_fill="black")
        draw.text((col * 640 + 12, 370), f"Hands · {frame['time_s']:.3f} s", font=small, fill="white", stroke_width=2, stroke_fill="black")
        hand.close()
        body.close()
    # The fourth column uses step 240; the third (step 128) is the last 60 Hz sample before contact ends at step 131.
    montage.save(out / "native_camera_montage.png", optimize=True)
    montage.close()
    after = {str(p): sha(p) for p in source_paths}
    if before != after:
        raise RuntimeError("a saved camera input changed during post-processing")
    manifest = {
        "phase": "finger_grip_hold_v1/native_video",
        "operation": "post-process existing Isaac Gym native camera frames only; no simulator call",
        "source_simulation": {"native_initializations": 1, "physics_steps": 240,
                              "frame_count": len(frame_records), "capture_rate_hz": 60,
                              "steps_per_frame": 4, "playback_rate_fps": 12, "playback_speed": 0.2,
                              "graphics_device_id": 0, "graphics_backend_identity": "not queried",
                              "physics_backend": "CPU PhysX"},
        "exact_raw_match_to_selected_1s_run": True,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "ffmpeg_command": ["ffmpeg", "-framerate", "12", "-i", "frames_composited/frame_%05d.png",
                           "-frames:v", "61", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart"],
        "ffmpeg_returncode": ffmpeg.returncode,
        "output_sha256": {str(p.relative_to(out)): sha(p) for p in
                           [out / "finger_grip_hold_0p2x.mp4", out / "native_camera_montage.png",
                            out / "ffprobe.json", out / "ffmpeg.log",
                            *sorted(frame_dir.glob("frame_*.png"))]},
        "ffprobe": probe_data,
    }
    (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    execution = {
        "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "returncode": 0,
        "environment": {k: os.environ.get(k) for k in ("MUJOCO_GL", "PYTHONPATH", "LD_LIBRARY_PATH", "MPLBACKEND")},
        "native_calls": 0,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "render_manifest": str(out / "render_manifest.json"),
    }
    (out / "render_execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    print(json.dumps({"out_dir": str(out), "video": str(video), "frames": len(frame_records),
                      "size": [probe_data["width"], probe_data["height"]]}))


if __name__ == "__main__":
    main()
