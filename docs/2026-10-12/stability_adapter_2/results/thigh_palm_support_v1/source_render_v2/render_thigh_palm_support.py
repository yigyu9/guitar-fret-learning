"""Replay one saved short native run on source geometry; never steps physics."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Import Isaac Gym before MuJoCo through environment/replay helpers.
from stability_adapter_2.environment import CONFIG_PATH  # noqa: F401
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np
from stability_adapter_2.plot_joint_hold import geometry_asset_paths
from stability_adapter_2.replay_contact_geometry import recorded_probe


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1"
RUN = PHASE / "short/clear_2um"
WIDTH, HEIGHT = 1920, 720
PANEL_W, PANEL_H = 640, 620
FPS = 12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def font(size):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def verify_hash_map(mapping):
    for raw_path, expected in mapping.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"input SHA mismatch: {path}")


def load_inputs(phase):
    preflight = read_json(phase / "preflight.json")
    search = read_json(phase / "search_near_touch.json")
    comparison = read_json(phase / "comparison_near_touch.json")
    search_all = read_json(phase / "search.json")
    comparison_all = read_json(phase / "comparison.json")
    comparison_validated = read_json(phase / "comparison_validated.json")
    # The sealed validated comparison resolves historical producer snapshots;
    # the earlier broad search/comparison JSON files remain preserved history.
    for source in (preflight, search, comparison_validated):
        verify_hash_map(source.get("input_sha256", {}))
    row = next((item for item in comparison_validated["rows"] if item["name"] == "clear_2um"), None)
    if row is None or not comparison_validated.get("inputs_verified_before_and_after"):
        raise ValueError("clear_2um row or verified comparison is missing")
    run = Path(row["run"])
    report, states, trace, contacts = (read_json(run / name) for name in
                                       ("report.json", "states.json", "trace.json", "contacts.json"))
    if not all(report["checks"].values()) or report["physics_steps"] != 24 or report["physics_hz"] != 240:
        raise ValueError("saved run contract or duration does not match the requested short run")
    if len(states) != 25 or len(trace) != 25 or len(contacts) != 24:
        raise ValueError("expected 25 saved states/trace samples and 24 contact records")
    for step, (state, sample) in enumerate(zip(states, trace)):
        if state["physics_step"] != step or not math.isclose(sample["time_s"], step / 240, abs_tol=1e-12):
            raise ValueError(f"saved sample alignment mismatch at step {step}")
        if not sample.get("finite", True):
            raise ValueError(f"nonfinite trace sample at step {step}")
    input_paths = [phase / name for name in ("preflight.json", "search.json", "search_near_touch.json",
                                              "comparison.json", "comparison_near_touch.json",
                                              "comparison_validated.json")]
    input_paths += [run / name for name in ("report.json", "states.json", "trace.json", "contacts.json",
                                             "controls.json", "leg_torques.json")]
    input_hashes = {str(path.resolve()): sha(path) for path in input_paths}
    # The preflight right-thigh witness is a baseline reference; translate only its guitar point
    # by the candidate's recorded creation-only offset for an annotated locator, not a new query.
    thigh = min(preflight["right_thigh_to_guitar"], key=lambda item: item["capsule_surface_separation_m"])
    palm_sample = row["source_samples"][0]["palm_neck"]
    return (preflight, search, comparison, comparison_all, comparison_validated, row, run, report,
            states, trace, contacts, input_hashes, thigh, palm_sample)


def set_saved_pose(model, report, state):
    for actor, names_key, states_key in (("human", "human_body_names", "human_body_states"),
                                         ("guitar", "guitar_body_names", "guitar_body_states")):
        for name, body_state in zip(report[names_key], state[states_key]):
            body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, actor + "/" + name)
            if body_id > 0:
                pose = body_state["pose"]
                p, q = pose["p"], pose["r"]
                model.body_pos[body_id] = [p["x"], p["y"], p["z"]]
                model.body_quat[body_id] = [q["w"], q["x"], q["y"], q["z"]]


def camera(lookat, distance, azimuth, elevation):
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.lookat[:] = lookat
    cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
    return cam


def add_line(scene, start, end, color, width=2.5):
    geom = scene.geoms[scene.ngeom]
    rgba = np.asarray(color, dtype=np.float32)
    mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_LINE, np.ones(3), np.zeros(3),
                        np.eye(3).reshape(-1), rgba)
    mujoco.mjv_connector(geom, mujoco.mjtGeom.mjGEOM_LINE, width,
                         np.asarray(start, dtype=np.float64), np.asarray(end, dtype=np.float64))
    geom.rgba[:] = rgba
    scene.ngeom += 1


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


def draw_route(scene, route):
    if scene.ngeom + len(route) > scene.maxgeom:
        raise RuntimeError("MuJoCo scene capacity is too small for the saved strap route")
    for start, end in zip(route[:-1], route[1:]):
        add_line(scene, start, end, (1.0, .55, .05, .95), 2.0)


def witness_points(preflight, report, thigh, palm_sample):
    delta = np.asarray(report["guitar_initial_translation_m"], dtype=float)
    hip_capsule = np.asarray(thigh["capsule_surface_witness_world_m"], dtype=float)
    hip_guitar = np.asarray(thigh["guitar_witness_world_m"], dtype=float) + delta
    palm_left, palm_right = (np.asarray(point, dtype=float) for point in palm_sample["hull_witness_points_m"])
    return {"hip_capsule": hip_capsule, "hip_guitar_shifted": hip_guitar,
            "palm": palm_left, "palm_guitar": palm_right, "guitar_translation": delta}


def project_point(gl_camera, point, width, height):
    """Project a world point using MuJoCo's current GL-camera frustum."""
    forward = np.asarray(gl_camera.forward, dtype=float)
    up = np.asarray(gl_camera.up, dtype=float)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    relative = np.asarray(point, dtype=float) - np.asarray(gl_camera.pos, dtype=float)
    depth = float(np.dot(relative, forward))
    if depth <= gl_camera.frustum_near:
        return None
    vertical_half_angle = gl_camera.frustum_top / gl_camera.frustum_near
    horizontal_half = vertical_half_angle * depth * width / height
    px = width * .5 + np.dot(relative, right) / horizontal_half * width * .5
    py = height * .5 - np.dot(relative, up) / (vertical_half_angle * depth) * height * .5
    return float(px), float(py)


def draw_projected_witnesses(canvas, renderers, witnesses):
    draw = ImageDraw.Draw(canvas)
    specs = [
        (1, witnesses["hip_capsule"], witnesses["hip_guitar_shifted"],
         (238, 126, 25), (35, 91, 175), "R_Hip surface ref", "Guitar ref"),
        (2, witnesses["palm"], witnesses["palm_guitar"],
         (20, 175, 95), (35, 91, 175), "LH:palm hull", "Neck hull"),
    ]
    for panel, first, second, color_a, color_b, label_a, label_b in specs:
        cam = renderers[panel].scene.camera[0]
        points = [project_point(cam, first, PANEL_W, PANEL_H),
                  project_point(cam, second, PANEL_W, PANEL_H)]
        if any(point is None for point in points):
            continue
        points = [(x + panel * PANEL_W, y + 34) for x, y in points]
        # These are 2D labels over the image, intentionally visible through geometry.
        draw.line([points[0], points[1]], fill=color_a, width=3)
        for (x, y), color in zip(points, (color_a, color_b)):
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), outline=color, width=3)
        text_x, text_y = panel * PANEL_W + 10, 48
        for index, (label, color, point) in enumerate(((label_a, color_a, points[0]),
                                                        (label_b, color_b, points[1]))):
            y = text_y + index * 23
            box = draw.textbbox((text_x, y), label, font=font(13))
            draw.rectangle((box[0] - 3, box[1] - 2, box[2] + 4, box[3] + 2), fill=(255, 255, 255))
            draw.text((text_x, y), label, fill=color, font=font(13))
            draw.line((box[2] + 4, y + 8, point[0], point[1]), fill=color, width=2)


def render_panels(model, data, renderers, cameras, report, state, sample):
    set_saved_pose(model, report, state)
    mujoco.mj_forward(model, data)
    route = np.asarray(sample["route_points_m"], dtype=float)
    if route.ndim != 2 or route.shape[1] != 3 or not np.isfinite(route).all():
        raise ValueError(f"invalid saved strap route at physics step {state['physics_step']}")
    panels = []
    for index, (renderer, cam) in enumerate(zip(renderers, cameras)):
        renderer.update_scene(data, camera=cam)
        draw_route(renderer.scene, route)
        panels.append(Image.fromarray(renderer.render()))
    return panels


def compose(panels, step, sample, annotated=False):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    labels = ("FULL BODY + GUITAR", "R_Hip / GUITAR", "LH:palm / NECK")
    for i, panel in enumerate(panels):
        canvas.paste(panel, (i * PANEL_W, 34))
        draw.text((i * PANEL_W + 12, 8), labels[i], fill="black", font=font(18))
    pos_mm = sample["position_error_m"] * 1000
    rot_deg = sample["rotation_error_deg"]
    line1 = f"saved native step {step}/24 | t={sample['time_s']:.6f} s | guitar error {pos_mm:.3f} mm / {rot_deg:.4f} deg"
    draw.text((12, 655), line1, fill="black", font=font(16))
    if annotated:
        line2 = "2D projected witness overlays ignore geometry occlusion; circle size is illustrative, not distance scale."
    else:
        line2 = "Saved native poses replayed on source collision geometry; no PhysX rendering and no added simulation steps."
    draw.text((12, 682), line2, fill="#333333", font=font(14))
    if draw.textbbox((12, 682), line2, font=font(14))[2] > WIDTH - 10:
        raise ValueError("frame footer exceeds canvas width")
    return canvas


def plot_metrics(trace, output):
    times = [sample["time_s"] for sample in trace]
    pos = [sample["position_error_m"] * 1000 for sample in trace]
    rot = [sample["rotation_error_deg"] for sample in trace]
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    axes[0].plot(times, pos, color="#2457a6", lw=2)
    axes[0].set_ylabel("Position error (mm)")
    axes[1].plot(times, rot, color="#a3396e", lw=2)
    axes[1].set_ylabel("Rotation error (deg)")
    axes[1].set_xlabel("Saved native time (s)")
    axes[0].set_title("clear_2um: saved trace errors over 0.1 s")
    for ax in axes:
        ax.grid(True, alpha=.25)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def render(phase, out_dir):
    if out_dir.exists():
        raise FileExistsError(f"preserve existing render output: {out_dir}")
    (preflight, search, comparison, comparison_all, comparison_validated, row, run, report, states, trace,
     contacts, input_hashes, thigh, palm_sample) = load_inputs(phase)
    (out_dir / "images").mkdir(parents=True)
    (out_dir / "videos").mkdir()
    run_files = [run / name for name in ("report.json", "states.json", "trace.json", "contacts.json",
                                          "controls.json", "leg_torques.json")]
    all_hashes = {str(Path(path).resolve()): sha(path) for path in run_files}
    all_hashes.update(input_hashes)
    verify_hash_map(preflight["input_sha256"])
    verify_hash_map(search["input_sha256"])
    before = dict(all_hashes)
    helpers = [Path(__file__).resolve(), Path(__file__).with_name("replay_contact_geometry.py"),
               Path(__file__).with_name("initial_overlap.py"), Path(__file__).with_name("environment.py"),
               Path(__file__).with_name("plot_joint_hold.py")]
    helper_hash_before = {str(path.resolve()): sha(path) for path in helpers}
    for input_map in (search["input_sha256"],
                      comparison_validated["input_sha256"], preflight["input_sha256"]):
        before.update(input_map)

    model, data, shapes = recorded_probe(run, 0, include_ground=True)
    model.vis.global_.offwidth = PANEL_W
    model.vis.global_.offheight = PANEL_H
    color_shapes(model, shapes)
    cameras = [camera([0, 0, .65], 2.1, 270, -8),
               camera([.07, .04, .49], .55, 270, 0),
               camera([-.12, .12, .75], .60, 270, 0)]
    renderers = []
    encoders = []
    try:
        renderers = [mujoco.Renderer(model, height=PANEL_H, width=PANEL_W) for _ in cameras]
        witnesses = witness_points(preflight, report, thigh, palm_sample)
        initial_panels = render_panels(model, data, renderers, cameras, report, states[0], trace[0])
        initial = compose(initial_panels, 0, trace[0], annotated=True)
        draw_projected_witnesses(initial, renderers, witnesses)
        initial_path = out_dir / "images/initial_annotated.png"
        initial.save(initial_path)
        end_panels = render_panels(model, data, renderers, cameras, report, states[-1], trace[-1])
        end = compose(end_panels, 24, trace[-1])
        end_path = out_dir / "images/end_step_024.png"
        end.save(end_path)
        metrics_path = out_dir / "images/trace_metrics.png"
        plot_metrics(trace, metrics_path)

        video_path = out_dir / "videos/clear_2um_saved_pose_0p05x.mp4"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
                   "-i", "-", "-frames:v", "25", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   "-preset", "medium", "-movflags", "+faststart", str(video_path)]
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        encoders.append(proc)
        for step in range(25):
            panels = render_panels(model, data, renderers, cameras, report, states[step], trace[step])
            frame = compose(panels, step, trace[step])
            proc.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
        proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", "replace")
        returncode = proc.wait()
        if returncode:
            raise RuntimeError(f"ffmpeg failed ({returncode}): {stderr}")
        probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,duration",
                                "-of", "json", str(video_path)], check=True, capture_output=True, text=True)
        stream = json.loads(probe.stdout)["streams"][0]
        if (int(stream["nb_read_frames"]) != 25 or (int(stream["width"]), int(stream["height"])) != (WIDTH, HEIGHT)
                or stream["avg_frame_rate"] != f"{FPS}/1"):
            raise RuntimeError(f"video verification failed: {stream}")

        assets = geometry_asset_paths()
        after = {path: sha(Path(path)) for path in before}
        if before != after:
            raise RuntimeError("raw or referenced input hashes changed while rendering")
        helper_hash_after = {str(path.resolve()): sha(path) for path in helpers}
        if helper_hash_before != helper_hash_after:
            raise RuntimeError("renderer/helper source changed while rendering")
        outputs = [initial_path, end_path, metrics_path, video_path]
        manifest = {
            "purpose": "Read-only replay of saved clear_2um native poses on source collision geometry; no physics stepping",
            "selected_run": str(run.resolve()), "saved_steps": list(range(25)), "saved_times_s": [s["time_s"] for s in trace],
            "native_physics_steps_added": 0, "native_sim_initializations_added": 0,
            "probe_initialization_mujoco_forward_calls": 1, "render_loop_mujoco_forward_calls": 27,
            "mujoco_step_calls": 0, "video_frame_count": 25, "video_fps": FPS,
            "native_time_span_s": .1, "video_duration_s": float(stream["duration"]), "playback_factor": .05,
            "inputs_sha256": before,
            "source_geometry_assets_sha256": {str(path.resolve()): sha(path) for path in assets},
            "renderer_helpers_sha256_before": helper_hash_before,
            "renderer_helpers_sha256_after": helper_hash_after,
            "historical_source_snapshots": comparison_validated.get("historical_source_snapshots", []),
            "camera_settings": [{"lookat": c.lookat.tolist(), "distance": c.distance,
                                 "azimuth": c.azimuth, "elevation": c.elevation} for c in cameras],
            "annotated_witness_semantics": {
                "LH_palm": "selected run comparison_near_touch step-0 unsigned source-hull witness points",
                "R_Hip": "baseline preflight capsule/guitar witness; guitar endpoint translated by selected run's recorded creation offset, not recomputed",
                "marker_size": "illustrative only; not geometric distance scale"},
            "ffmpeg_command": command, "ffmpeg_returncode": returncode, "ffmpeg_stderr": stderr,
            "ffprobe_stream": stream,
            "outputs_sha256": {str(path.resolve()): sha(path) for path in outputs},
        }
        manifest_path = out_dir / "render_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
    finally:
        for renderer in renderers:
            renderer.close()
        for proc in encoders:
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


def render_initial_v2(phase, source_render_dir, out_dir):
    """Regenerate only the annotated initial image and copy frozen v1 media."""
    if out_dir.exists():
        raise FileExistsError(f"preserve existing render output: {out_dir}")
    (preflight, search, comparison, comparison_all, comparison_validated, row, run, report, states, trace,
     contacts, input_hashes, thigh, palm_sample) = load_inputs(phase)
    old_manifest_path = source_render_dir / "render_manifest.json"
    old_manifest = read_json(old_manifest_path)
    if old_manifest["video_frame_count"] != 25 or old_manifest["native_physics_steps_added"] != 0:
        raise ValueError("frozen v1 media does not match this saved 25-frame run")
    source_files = {"images/end_step_024.png": "images/end_step_024.png",
                    "images/trace_metrics.png": "images/trace_metrics.png",
                    "videos/clear_2um_saved_pose_0p05x.mp4": "videos/clear_2um_saved_pose_0p05x.mp4"}
    for relative in source_files:
        source_path = source_render_dir / relative
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        expected = next((value for path, value in old_manifest["outputs_sha256"].items()
                         if Path(path).as_posix().endswith(relative)), None)
        if expected != sha(source_path):
            raise ValueError(f"frozen v1 media SHA mismatch: {source_path}")

    run_files = [run / name for name in ("report.json", "states.json", "trace.json", "contacts.json",
                                          "controls.json", "leg_torques.json")]
    all_hashes = {str(Path(path).resolve()): sha(path) for path in run_files}
    all_hashes.update(input_hashes)
    before = dict(all_hashes)
    for input_map in (search["input_sha256"], comparison_validated["input_sha256"],
                      preflight["input_sha256"]):
        before.update(input_map)
    helpers = [Path(__file__).resolve(), Path(__file__).with_name("replay_contact_geometry.py"),
               Path(__file__).with_name("initial_overlap.py"), Path(__file__).with_name("environment.py"),
               Path(__file__).with_name("plot_joint_hold.py")]
    helper_before = {str(path.resolve()): sha(path) for path in helpers}

    images_dir, videos_dir = out_dir / "images", out_dir / "videos"
    images_dir.mkdir(parents=True)
    videos_dir.mkdir()
    for relative in source_files:
        destination = out_dir / relative
        shutil.copy2(source_render_dir / relative, destination)

    model, data, shapes = recorded_probe(run, 0, include_ground=True)
    model.vis.global_.offwidth = PANEL_W
    model.vis.global_.offheight = PANEL_H
    color_shapes(model, shapes)
    cameras = [camera([0, 0, .65], 2.1, 270, -8),
               camera([.07, .04, .49], .55, 270, 0),
               camera([-.12, .12, .75], .60, 270, 0)]
    renderers = []
    try:
        renderers = [mujoco.Renderer(model, height=PANEL_H, width=PANEL_W) for _ in cameras]
        panels = render_panels(model, data, renderers, cameras, report, states[0], trace[0])
        image = compose(panels, 0, trace[0], annotated=True)
        draw_projected_witnesses(image, renderers, witness_points(preflight, report, thigh, palm_sample))
        initial_path = images_dir / "initial_annotated.png"
        image.save(initial_path)
    finally:
        for renderer in renderers:
            renderer.close()

    after = {path: sha(Path(path)) for path in before}
    helper_after = {str(path.resolve()): sha(path) for path in helpers}
    if before != after or helper_before != helper_after:
        raise RuntimeError("input or renderer source hash changed during initial annotation")
    outputs = [out_dir / relative for relative in source_files] + [initial_path]
    manifest = {
        "purpose": "v2 initial 2D projected witness annotation; end image, metrics and video copied unchanged from v1",
        "selected_run": str(run.resolve()), "saved_steps": list(range(25)), "video_frame_count": 25,
        "native_physics_steps_added": 0, "native_sim_initializations_added": 0,
        "probe_initialization_mujoco_forward_calls": 1, "render_loop_mujoco_forward_calls": 1,
        "mujoco_step_calls": 0, "inputs_sha256": before,
        "renderer_helpers_sha256_before": helper_before, "renderer_helpers_sha256_after": helper_after,
        "historical_source_snapshots": comparison_validated.get("historical_source_snapshots", []),
        "copied_unchanged_from_v1": {str((out_dir / relative).resolve()): {
            "source": str((source_render_dir / relative).resolve()), "sha256": sha(source_render_dir / relative),
            "v1_manifest_sha256": sha(old_manifest_path)} for relative in source_files},
        "annotation_semantics": {
            "R_Hip": "projected baseline preflight witness; candidate guitar endpoint shifted by recorded creation translation, not recomputed",
            "LH_palm": "selected run step-0 unsigned source-hull witness pair",
            "overlay": "2D points are placed from MuJoCo GL camera projection and drawn over geometry; occlusion is intentionally ignored; ring size is illustrative"},
        "outputs_sha256": {str(path.resolve()): sha(path) for path in outputs},
    }
    manifest_path = out_dir / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=Path, default=PHASE)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--initial-only", action="store_true",
                        help="refresh only the initial overlay; copy the remaining frozen outputs from --source-render-dir")
    parser.add_argument("--source-render-dir", type=Path)
    args = parser.parse_args()
    if args.initial_only:
        if args.source_render_dir is None:
            parser.error("--initial-only requires --source-render-dir")
        manifest = render_initial_v2(args.phase.resolve(), args.source_render_dir.resolve(), args.out_dir.resolve())
    else:
        manifest = render(args.phase.resolve(), args.out_dir.resolve())
    print(json.dumps({"out_dir": str(args.out_dir.resolve()), "frame_count": manifest["video_frame_count"],
                      "native_steps_added": manifest["native_physics_steps_added"]}, indent=2))


if __name__ == "__main__":
    main()
