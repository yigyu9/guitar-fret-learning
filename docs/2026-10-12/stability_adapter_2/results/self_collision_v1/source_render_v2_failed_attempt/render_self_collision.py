"""Replay saved OFF/ON self-collision poses on source geometry; no physics stepping."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

# Isaac Gym must be imported before MuJoCo by the existing environment helper.
from .environment import CONFIG_PATH  # noqa: F401
import mujoco
import numpy as np
from .replay_contact_geometry import recorded_probe
from .plot_joint_hold import geometry_asset_paths
from .render_best_run_video import camera, color_shapes, draw_route, font, set_saved_pose

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/self_collision_v1"
WIDTH, HEIGHT, VIEW_W, VIEW_H, FPS = 1280, 720, 640, 620, 12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked_run(phase, mode):
    run = phase / "short" / mode
    report, states, trace, contacts, self_contacts = (
        read(run / name) for name in ("report.json", "states.json", "trace.json", "contacts.json", "self_contacts.json"))
    if not all(report["checks"].values()) or report["physics_steps"] != 24 or report["physics_hz"] != 240:
        raise ValueError(f"{mode}: saved run contract or duration mismatch")
    if len(states) != 25 or len(trace) != 25 or len(contacts) != 24:
        raise ValueError(f"{mode}: expected 25 states/trace samples and 24 contact records")
    for step, (state, sample) in enumerate(zip(states, trace)):
        if state["physics_step"] != step or abs(sample["time_s"] - step / 240) > 1e-12:
            raise ValueError(f"{mode}: saved sample alignment mismatch at step {step}")
        if not sample.get("finite", False):
            raise ValueError(f"{mode}: nonfinite trace sample at step {step}")
    return run, report, states, trace, contacts, self_contacts


def render_pose(model, data, renderer, cam, report, state, sample):
    set_saved_pose(model, mujoco, report, state)
    mujoco.mj_forward(model, data)
    route = np.asarray(sample["route_points_m"], dtype=float)
    if route.ndim != 2 or route.shape[1] != 3 or not np.isfinite(route).all():
        raise ValueError(f"invalid saved strap route at step {state['physics_step']}")
    renderer.update_scene(data, camera=cam)
    draw_route(renderer, mujoco, route)
    return Image.fromarray(renderer.render())


def contact_counts(records):
    counts = {}
    for row in records:
        step = row.get("physics_step")
        if step is None or "contact" not in row:
            raise ValueError("malformed saved self-contact row")
        counts[step] = counts.get(step, 0) + 1
    return counts


def panel_canvas(left, right, header_left, header_right, footer):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    canvas.paste(left, (0, 38))
    canvas.paste(right, (640, 38))
    label_font, footer_font = font(16), font(13)
    draw.text((12, 9), header_left, fill="black", font=label_font)
    draw.text((652, 9), header_right, fill="black", font=label_font)
    draw.text((12, 663), footer, fill="#202020", font=footer_font)
    if draw.textbbox((12, 663), footer, font=footer_font)[2] > WIDTH - 10:
        raise ValueError("frame footer exceeds canvas width")
    draw.text((12, 687), "Raw contact rows are not force or sustained support; source replay, no added physics.",
              fill="#444444", font=footer_font)
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=Path, default=PHASE)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    phase, out_dir = args.phase.resolve(), args.out_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f"preserve existing output: {out_dir}")

    probe = read(phase / "importer_probe.json")
    comparison = read(phase / "comparison.json")
    if not comparison.get("inputs_verified_before_and_after") or len(comparison.get("rows", [])) != 2:
        raise ValueError("saved OFF/ON comparison provenance is incomplete")
    off = checked_run(phase, "off")
    on = checked_run(phase, "on")
    off_run, off_report, off_states, off_trace, off_contacts, off_self = off
    on_run, on_report, on_states, on_trace, on_contacts, on_self = on
    same_fields = ("initial_settings", "human_joint_names", "human_body_names", "guitar_body_names",
                   "initial_joint_targets_rad", "guitar_goal_position_m", "guitar_goal_quaternion_xyzw",
                   "absolute_rest_length_m", "native_pd_kp", "native_pd_kd", "native_drive_modes",
                   "native_effort_caps_nm", "physics_parameters")
    if off_states[0] != on_states[0] or any(off_report[key] != on_report[key] for key in same_fields):
        raise ValueError("OFF/ON initial state, target, strap, or PD settings differ")
    if probe.get("physics_steps") != 0:
        raise ValueError("importer probe unexpectedly contains physics steps")

    raw_names = ("report.json", "states.json", "trace.json", "contacts.json", "self_contacts.json",
                 "controls.json", "leg_torques.json")
    raw_paths = [phase / "importer_probe.json", phase / "comparison.json"]
    raw_paths += [Path(path) for path in probe["input_sha256"]]
    raw_paths += [run / name for run in (off_run, on_run) for name in raw_names]
    helpers = [Path(__file__).resolve(), Path(__file__).with_name("render_best_run_video.py"),
               Path(__file__).with_name("replay_contact_geometry.py"),
               Path(__file__).with_name("initial_overlap.py"), Path(__file__).with_name("environment.py"),
               Path(__file__).with_name("plot_joint_hold.py")]
    assets = geometry_asset_paths()
    raw_before = {str(path.resolve()): sha(path) for path in raw_paths}
    for source_map in (probe["input_sha256"], comparison["input_sha256"]):
        if any(raw_before.get(str(Path(path).resolve())) != expected for path, expected in source_map.items()):
            raise ValueError("embedded source input SHA mismatch")
    helper_before = {str(path.resolve()): sha(path) for path in helpers}
    asset_before = {str(path.resolve()): sha(path) for path in assets}

    out_dir.mkdir(parents=True)
    images_dir, videos_dir = out_dir / "images", out_dir / "videos"
    images_dir.mkdir()
    videos_dir.mkdir()
    model, data, shapes = recorded_probe(on_run, 0, include_ground=True)
    model.vis.global_.offwidth, model.vis.global_.offheight = VIEW_W, VIEW_H
    color_shapes(model, shapes)
    full_camera = camera(mujoco, [0, 0, .65], 2.1, 270, -8)
    hand_camera = camera(mujoco, [-.19, .10, .80], .90, 270, 0)
    full_renderer = hand_renderer = None
    encoder = None
    video_path = videos_dir / "self_collision_on_saved_poses_0p05x.mp4"
    ffmpeg_command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo",
                      "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
                      "-i", "-", "-frames:v", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                      "-preset", "medium", "-movflags", "+faststart", str(video_path)]
    try:
        full_renderer = mujoco.Renderer(model, height=VIEW_H, width=VIEW_W)
        hand_renderer = mujoco.Renderer(model, height=VIEW_H, width=VIEW_W)
        off_counts, on_counts = contact_counts(off_self), contact_counts(on_self)

        initial_full = render_pose(model, data, full_renderer, full_camera, on_report, on_states[0], on_trace[0])
        initial_hands = render_pose(model, data, hand_renderer, hand_camera, on_report, on_states[0], on_trace[0])
        initial_footer = "ON initial pose | native step-0 contact query unavailable | post-step self-contact rows: not measured"
        panel_canvas(initial_full, initial_hands, "FULL BODY + GUITAR (ON)", "HANDS + GUITAR NECK (ON)",
                     initial_footer).save(images_dir / "initial_on.png")

        off_hands = render_pose(model, data, hand_renderer, hand_camera, off_report, off_states[24], off_trace[24])
        on_hands = render_pose(model, data, hand_renderer, hand_camera, on_report, on_states[24], on_trace[24])
        off_pos = off_report["max_position_error_m"] * 1000
        on_pos = on_report["max_position_error_m"] * 1000
        off_rot, on_rot = off_report["max_rotation_error_deg"], on_report["max_rotation_error_deg"]
        compare = panel_canvas(off_hands, on_hands,
                               f"OFF | step 24 | raw rows {off_counts.get(24, 0)} (total {len(off_self)})",
                               f"ON | step 24 | raw rows {on_counts.get(24, 0)} (total {len(on_self)})",
                               f"0.1 s maxima: guitar position {off_pos:.3f} / {on_pos:.3f} mm; rotation {off_rot:.4f} / {on_rot:.4f} deg")
        compare.save(images_dir / "off_on_hands_step_024.png")

        encoder = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for step in range(25):
            full = render_pose(model, data, full_renderer, full_camera, on_report, on_states[step], on_trace[step])
            hands = render_pose(model, data, hand_renderer, hand_camera, on_report, on_states[step], on_trace[step])
            count_label = ("not queried at step 0" if step == 0 else
                           f"raw self-contact rows after step {step}: {on_counts.get(step, 0)} / cumulative {sum(v for k, v in on_counts.items() if k <= step)}")
            frame = panel_canvas(full, hands, "FULL BODY + GUITAR (ON)", "HANDS + GUITAR NECK (ON)",
                                 f"saved step {step}/24 | t={on_trace[step]['time_s']:.6f} s | {count_label}")
            encoder.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
        encoder.stdin.close()
        stderr = encoder.stderr.read().decode("utf-8", "replace")
        returncode = encoder.wait()
        if returncode:
            raise RuntimeError(f"ffmpeg failed ({returncode}): {stderr}")
        probe_video = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                      "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,duration",
                                      "-of", "json", str(video_path)], check=True, capture_output=True, text=True)
        stream = json.loads(probe_video.stdout)["streams"][0]
        if ((int(stream["width"]), int(stream["height"])) != (WIDTH, HEIGHT) or
                int(stream["nb_read_frames"]) != 25 or stream["avg_frame_rate"] != f"{FPS}/1"):
            raise RuntimeError(f"video verification failed: {stream}")
    finally:
        for renderer in (full_renderer, hand_renderer):
            if renderer is not None:
                renderer.close()
        if encoder is not None and encoder.poll() is None:
            if encoder.stdin and not encoder.stdin.closed:
                try:
                    encoder.stdin.close()
                except BrokenPipeError:
                    pass
            encoder.terminate()
            try:
                encoder.wait(timeout=5)
            except subprocess.TimeoutExpired:
                encoder.kill()
                encoder.wait()

    raw_after = {path: sha(Path(path)) for path in raw_before}
    helper_after = {str(path.resolve()): sha(path) for path in helpers}
    asset_after = {str(path.resolve()): sha(path) for path in assets}
    if raw_before != raw_after or helper_before != helper_after or asset_before != asset_after:
        raise RuntimeError("raw input, renderer helper, or source asset changed during rendering")

    outputs = sorted(images_dir.glob("*.png")) + [video_path]
    manifest = {
        "purpose": "Read-only replay and comparison of saved self-collision OFF/ON poses on source geometry",
        "native_sim_initializations_added": 0, "native_physics_steps_added": 0,
        "saved_steps_replayed": list(range(25)), "saved_times_s": [sample["time_s"] for sample in on_trace],
        "probe_initialization_mujoco_forward_calls": 1, "saved_pose_render_mujoco_forward_calls": 54,
        "mujoco_step_calls": 0, "off_on_initial_state_equal": True,
        "raw_inputs_sha256_before": raw_before, "raw_inputs_sha256_after": raw_after,
        "comparison_inputs_verified_before_and_after": comparison["inputs_verified_before_and_after"],
        "renderer_helpers_sha256_before": helper_before, "renderer_helpers_sha256_after": helper_after,
        "source_geometry_assets_sha256_before": asset_before, "source_geometry_assets_sha256_after": asset_after,
        "ffmpeg_command": ffmpeg_command, "ffmpeg_returncode": returncode, "ffmpeg_stderr": stderr,
        "ffprobe_stream": stream,
        "source_archive_note": "All consumed current raw inputs, helpers, and geometry assets were freshly SHA-256 checked before and after this render.",
        "outputs_sha256": {str(path.resolve()): sha(path) for path in outputs},
    }
    manifest_path = out_dir / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"out_dir": str(out_dir), "video_frames": 25, "native_steps_added": 0,
                      "raw_inputs": len(raw_before), "assets": len(asset_before)}, indent=2))


if __name__ == "__main__":
    main()
