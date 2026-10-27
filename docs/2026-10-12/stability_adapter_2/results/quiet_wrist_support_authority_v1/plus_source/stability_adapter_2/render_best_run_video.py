"""Replay saved native poses on source collision geometry; never runs physics."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Import order: environment imports Isaac Gym before MuJoCo.
from stability_adapter_2.environment import CONFIG_PATH  # noqa: F401
import mujoco
import numpy as np
from stability_adapter_2.replay_contact_geometry import recorded_probe
from stability_adapter_2.plot_joint_hold import geometry_asset_paths

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/best_run_video_v1"
WIDTH, HEIGHT = 1280, 720
VIEW_W, VIEW_H = 640, 620


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def font(size):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def load_saved_inputs(phase):
    selection = read_json(phase / "selection.json")
    candidates = read_json(phase / "full_run_candidates.json")
    manifest = read_json(phase / "selection_inputs_manifest.json")
    if not candidates or candidates[0]["run"] != selection["run"]:
        raise ValueError("selected run is not the first ranked full-duration candidate")
    for source, expected in manifest["input_sha256"].items():
        path = Path(source)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"selection input SHA mismatch: {path}")
    run = Path(selection["run"])
    report, states, trace = (read_json(run / name) for name in ("report.json", "states.json", "trace.json"))
    if len(states) != 241 or len(trace) != 241 or report["physics_steps"] != 240 or report["physics_hz"] != 240:
        raise ValueError("expected saved states/trace at steps 0..240 and 240 Hz")
    if report["stability_success"] not in (None, False) or selection["stability_success"] is not False:
        raise ValueError("selected run's recorded success flag changed")
    for step, (state, sample) in enumerate(zip(states, trace)):
        if state["physics_step"] != step or abs(sample["time_s"] - step / 240) > 1e-12:
            raise ValueError(f"saved sample alignment mismatch at step {step}")
        if not sample.get("finite", False):
            raise ValueError(f"nonfinite saved trace at step {step}")
    return selection, candidates, manifest, run, report, states, trace


def color_shapes(model, shapes):
    for shape in shapes:
        if shape["actor"] == "guitar":
            color = (.10, .31, .78, 1)
        elif shape["actor"] == "ground":
            color = (.72, .73, .75, 1)
        elif shape["body"].startswith("LH:") or shape["body"] == "L_Wrist":
            color = (.10, .66, .30, 1)
        elif shape["body"].startswith("RH:") or shape["body"] == "R_Wrist":
            color = (.78, .12, .52, 1)
        else:
            color = (.58, .61, .66, 1)
        model.geom_rgba[shape["geom_id"]] = color


def set_saved_pose(model, mujoco, report, state):
    for actor, names_key, states_key in (
            ("human", "human_body_names", "human_body_states"),
            ("guitar", "guitar_body_names", "guitar_body_states")):
        for name, body_state in zip(report[names_key], state[states_key]):
            body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, actor + "/" + name)
            if body_id <= 0:
                continue
            pose = body_state["pose"]
            p, q = pose["p"], pose["r"]
            model.body_pos[body_id] = [p["x"], p["y"], p["z"]]
            model.body_quat[body_id] = [q["w"], q["x"], q["y"], q["z"]]


def camera(mujoco, lookat, distance, azimuth, elevation):
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.lookat[:] = lookat
    cam.distance = distance
    cam.azimuth = azimuth
    cam.elevation = elevation
    return cam


def draw_route(renderer, mujoco, route):
    scene = renderer.scene
    if scene.ngeom + len(route) - 1 > scene.maxgeom:
        raise RuntimeError("MuJoCo scene capacity is too small for saved strap route")
    for start, end in zip(route[:-1], route[1:]):
        geom = scene.geoms[scene.ngeom]
        rgba = np.asarray([1.0, .55, .05, .95], dtype=np.float32)
        mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_LINE, np.ones(3), np.zeros(3),
                            np.eye(3).reshape(-1), rgba)
        mujoco.mjv_connector(geom, mujoco.mjtGeom.mjGEOM_LINE, 2.2, start, end)
        geom.rgba[:] = rgba
        scene.ngeom += 1


def compose_frame(panels, step, sample, playback):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    canvas.paste(panels[0], (0, 38))
    canvas.paste(panels[1], (640, 38))
    draw = ImageDraw.Draw(canvas)
    small, tiny = font(16), font(12)
    draw.text((12, 10), "FULL BODY + GUITAR", fill="black", font=small)
    draw.text((652, 10), "HANDS + GUITAR NECK", fill="black", font=small)
    pos_mm = sample["position_error_m"] * 1000
    rot = sample["rotation_error_deg"]
    speed = sample["linear_speed_mps"]
    omega = sample["angular_speed_rad_s"]
    line1 = (f"step {step}/240 | t={sample['time_s']:.4f} s | playback {playback} | "
              f"guitar error {pos_mm:.1f} mm / {rot:.2f} deg | v={speed:.3f} m/s, omega={omega:.3f} rad/s")
    draw.text((12, 663), line1, fill="black", font=tiny)
    if draw.textbbox((12, 663), line1, font=tiny)[2] > WIDTH - 12:
        raise ValueError("video footer exceeds frame width")
    line2 = ("Saved native poses on source collision geometry; no PhysX rendering or physics steps. "
              "Recorded stability_success=False; terminal motion remains nonzero.")
    draw.text((12, 687), line2, fill="#333333", font=tiny)
    if draw.textbbox((12, 687), line2, font=tiny)[2] > WIDTH - 12:
        raise ValueError("video footer exceeds frame width")
    return canvas


def render(phase, out_dir, preview_only):
    selection, candidates, selection_manifest, run, report, states, trace = load_saved_inputs(phase)
    if (out_dir / "videos").exists() or (out_dir / "images").exists() or (out_dir / "render_manifest.json").exists():
        raise FileExistsError("preserve existing video/image outputs; choose an empty output location")
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # This constructs only a MuJoCo source-geometry probe at saved step 0.
    model, data, shapes = recorded_probe(run, 0, include_ground=True)
    model.vis.global_.offwidth = VIEW_W
    model.vis.global_.offheight = VIEW_H
    color_shapes(model, shapes)
    full_renderer = close_renderer = None
    encoders = []
    try:
        full_renderer = mujoco.Renderer(model, height=VIEW_H, width=VIEW_W)
        close_renderer = mujoco.Renderer(model, height=VIEW_H, width=VIEW_W)
        cams = [camera(mujoco, [0, 0, .65], 2.1, 270, -8),
                camera(mujoco, [-.19, .10, .80], .90, 270, 0)]
        preview_steps = (0, 120, 240)

        def render_panels(step):
            set_saved_pose(model, mujoco, report, states[step])
            # Update source-shape transforms only; this is not a dynamics step.
            mujoco.mj_forward(model, data)
            route = np.asarray(trace[step]["route_points_m"], dtype=float)
            if route.ndim != 2 or route.shape[1] != 3 or not np.isfinite(route).all():
                raise ValueError(f"invalid saved strap route at step {step}")
            panels = []
            for renderer, cam in zip((full_renderer, close_renderer), cams):
                renderer.update_scene(data, camera=cam)
                draw_route(renderer, mujoco, route)
                panels.append(Image.fromarray(renderer.render()))
            return panels

        if preview_only:
            for step in preview_steps:
                frame = compose_frame(render_panels(step), step, trace[step], "0.25x preview")
                frame.save(images_dir / f"preview_step_{step:03d}.png")
            return {"preview_only": True, "preview_steps": list(preview_steps)}

        videos_dir = out_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        outputs = [("slow_0p25x", 60), ("realtime_1x", 240)]
        encoders, commands = [], {}
        for name, fps in outputs:
            path = videos_dir / f"best_run_{name}.mp4"
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(fps),
                   "-i", "-", "-frames:v", "241", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   "-preset", "medium", "-movflags", "+faststart", str(path)]
            encoders.append((name, path, subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)))
            commands[name] = cmd
        for step in range(241):
            panels = render_panels(step)
            sample = trace[step]
            if step in preview_steps:
                preview = compose_frame(panels, step, sample, "0.25x preview")
                preview.save(images_dir / f"preview_step_{step:03d}.png")
            for name, _path, proc in encoders:
                pace = "0.25x" if name == "slow_0p25x" else "1x"
                frame = compose_frame(panels, step, sample, pace)
                proc.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
        encoder_meta = {}
        for name, path, proc in encoders:
            proc.stdin.close()
            stderr = proc.stderr.read().decode("utf-8", "replace")
            rc = proc.wait()
            if rc != 0:
                raise RuntimeError(f"ffmpeg failed for {name} (exit {rc}): {stderr}")
            probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                    "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,duration",
                                    "-of", "json", str(path)], check=True, capture_output=True, text=True)
            stream = json.loads(probe.stdout)["streams"][0]
            if int(stream["nb_read_frames"]) != 241 or (int(stream["width"]), int(stream["height"])) != (WIDTH, HEIGHT):
                raise RuntimeError(f"video verification failed: {path.name} {stream}")
            encoder_meta[name] = {"path": str(path.resolve()), "sha256": sha(path), "ffmpeg_command": commands[name],
                                  "returncode": rc, "ffprobe_stream": stream, "stderr": stderr}

        helpers = [Path(__file__).resolve(), Path(__file__).with_name("replay_contact_geometry.py"),
                   Path(__file__).with_name("initial_overlap.py"), Path(__file__).with_name("environment.py"),
                   Path(__file__).with_name("plot_joint_hold.py")]
        selection_files = [phase / "selection.json", phase / "full_run_candidates.json",
                           phase / "selection_inputs_manifest.json", run / "report.json", run / "states.json", run / "trace.json"]
        manifest = {"purpose": "Read-only source-collision-geometry replay of all 241 saved states; no native simulation",
                    "selected_run": str(run.resolve()), "selection_sha256": {str(p.resolve()): sha(p) for p in selection_files},
                    "selection_input_sha256": selection_manifest["input_sha256"],
                    "source_geometry_assets_sha256": {str(p): sha(Path(p)) for p in geometry_asset_paths()},
                    "replay_helpers_sha256": {str(p.resolve()): sha(p) for p in helpers},
                    "saved_step_numbers": list(range(241)), "frame_count": 241, "physics_steps_replayed": 240,
                    "probe_initialization_forward_calls": 1, "render_loop_mujoco_forward_calls": 241,
                    "mujoco_forward_calls_total": 242, "mujoco_step_calls": 0,
                    "native_sim_initializations": 0,
                    "cameras": [{"lookat": [0, 0, .65], "distance": 2.1, "azimuth": 270, "elevation": -8},
                                {"lookat": [-.19, .10, .80], "distance": .90, "azimuth": 270, "elevation": 0}],
                    "video_outputs": encoder_meta,
                    "preview_png_sha256": {str(p.resolve()): sha(p) for p in sorted(images_dir.glob("*.png"))}}
        (out_dir / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
    finally:
        for renderer in (full_renderer, close_renderer):
            if renderer is not None:
                renderer.close()
        for _name, _path, proc in encoders:
            if proc.poll() is None:
                if proc.stdin and not proc.stdin.closed:
                    try:
                        proc.stdin.close()
                    except BrokenPipeError:
                        pass
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=Path, default=PHASE)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--preview-only", action="store_true")
    args = parser.parse_args()
    result = render(args.phase, args.out_dir, args.preview_only)
    print(json.dumps({"preview_only": args.preview_only, "out_dir": str(args.out_dir.resolve()),
                      "frames": result.get("frame_count", len(result.get("preview_steps", [])))}, indent=2))


if __name__ == "__main__":
    main()
