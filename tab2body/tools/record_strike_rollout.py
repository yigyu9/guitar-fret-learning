"""Record one deterministic virtual-pick rollout from two frozen cameras.

Both videos observe the exact same simulation frames.  The camera directions,
distance and field of view are the two presets retained by
``render_pick_grip_pose.py``: ``remembered`` and ``current``.

Isaac Gym must be imported before torch, so simulator imports intentionally
live inside :func:`main`; importing this module for its artifact-contract
helpers remains CPU-only.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.strike_contract import STRIKE_STAGES



CAMERA_DIRECTIONS = {
    "remembered": (0.15, 0.85, 0.62),
    "current": (-0.7474, 0.4317, 0.62),
}
CAMERA_DISTANCE_M = 0.7
CAMERA_HORIZONTAL_FOV_DEG = 42.0


def _mapping(value):
    return value if isinstance(value, dict) else {}


def restore_stage_and_tolerance(checkpoint):
    """Restore the current task state after checking trainer/task alignment."""
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint must be a mapping")
    environment = checkpoint.get("environment_state")
    context = checkpoint.get("training_context")
    if (not isinstance(environment, dict)
            or environment.get("schema")
            != "tab2body.strike_environment_state.v2"):
        raise ValueError(
            "checkpoint requires current strike environment_state.v2")
    if not isinstance(context, dict):
        raise ValueError("checkpoint requires a training_context mapping")
    for key in ("curriculum_stage", "curriculum_timing_tolerance_ms"):
        if key not in context:
            raise ValueError(f"training_context is missing {key}")

    from tab2body.learning.ppo import verify_checkpoint_curriculum_alignment

    verify_checkpoint_curriculum_alignment(checkpoint)
    stage = environment.get("curriculum_stage")
    if stage not in STRIKE_STAGES:
        raise ValueError(
            "checkpoint does not contain a valid strike curriculum stage")
    tolerance = environment.get("timing_tolerance_ms")
    if isinstance(tolerance, bool):
        raise ValueError("checkpoint timing tolerance must be positive")
    try:
        tolerance = float(tolerance)
    except (TypeError, ValueError) as exc:
        raise ValueError("checkpoint does not contain a timing tolerance") from exc
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("checkpoint timing tolerance must be finite and positive")
    tempo_lambda = environment.get("tempo_lambda")
    if isinstance(tempo_lambda, bool):
        raise ValueError("checkpoint tempo lambda must be in [0, 1]")
    try:
        tempo_lambda = float(tempo_lambda)
    except (TypeError, ValueError) as exc:
        raise ValueError("checkpoint does not contain a tempo lambda") from exc
    if not math.isfinite(tempo_lambda) or not 0.0 <= tempo_lambda <= 1.0:
        raise ValueError("checkpoint tempo lambda must be finite and in [0, 1]")
    return stage, tolerance, tempo_lambda


def require_ffmpeg():
    executable = shutil.which("ffmpeg")
    if executable is None:
        raise RuntimeError(
            "ffmpeg is required to create strike rollout MP4 files; "
            "install ffmpeg and retry")
    return executable


def _unit(values):
    norm = math.sqrt(sum(float(value) ** 2 for value in values))
    if norm <= 0.0:
        raise ValueError("camera direction must be non-zero")
    return tuple(float(value) / norm for value in values)


def resolve_video_paths(checkpoint, remembered=None, current=None):
    """Apply the shared default naming contract, with per-view overrides."""
    from tab2body.learning.run_layout import default_strike_video_paths

    defaults = default_strike_video_paths(checkpoint)
    return {
        "remembered": (
            Path(remembered).resolve() if remembered is not None
            else defaults["remembered"]),
        "current": (
            Path(current).resolve() if current is not None
            else defaults["current"]),
    }


def _checkpoint_payload(checkpoint):
    from tab2body.learning.checkpoint_contract import (
        STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
        validate_contract_document,
    )

    if "checkpoint_contract" not in checkpoint:
        raise ValueError(
            "cannot record a legacy checkpoint without checkpoint_contract")
    validated = validate_contract_document(checkpoint["checkpoint_contract"])
    payload = validated["payload"]
    if payload.get("schema") != STRIKE_CHECKPOINT_CONTRACT_SCHEMA:
        raise ValueError("checkpoint is not a strike policy contract")
    if payload.get("task") != "strike":
        raise ValueError("checkpoint contract task must be 'strike'")
    return validated, payload


def verify_live_contract(
        checkpoint, env, model, goal_path, grip_reference_path, strike_config):
    """Verify integrity and equality with the freshly constructed live task."""
    _, payload = _checkpoint_payload(checkpoint)
    from tab2body.learning.checkpoint_contract import verify_checkpoint_contract
    from tab2body.strike_checkpoint import build_runtime_checkpoint_contract

    live_config = dict(strike_config)
    live_config["grip_reference_path"] = str(
        Path(grip_reference_path).resolve())
    saved_ppo = _mapping(_mapping(payload.get("config")).get("ppo"))
    live_contract = build_runtime_checkpoint_contract(
        env, model, goal_path, config=live_config, ppo_config=saved_ppo)
    verify_checkpoint_contract(
        checkpoint, live_contract, purpose="record strike rollout")
    return payload


def _construct_task(StrikeTask, args, strike_config):
    """Construct the one-environment recorder through the current task API."""
    from tab2body.env.config import configured_kwargs

    return StrikeTask(**configured_kwargs(
        StrikeTask,
        strike_config,
        goal_path=str(args.goal),
        grip_reference_path=str(args.grip_reference),
        num_envs=1,
        device=args.device,
        headless=True,
        seed=int(strike_config["seed"]),
        reset_noise=0.0,
        random_start=False,
    ))


def _restore_task(env, stage, tolerance, tempo_lambda):
    env.set_curriculum_stage(
        stage, tolerance, tempo_lambda=tempo_lambda, reset=False)
    env.set_evaluation_mode(
        stage == "A4_ZONE_CONTROL" and tempo_lambda >= 1.0,
        reset=False)
    return env.reset()


def _load_checkpoint(torch, path, device):
    try:
        checkpoint = torch.load(
            str(path), map_location=device, weights_only=True)
    except TypeError:


        checkpoint = torch.load(str(path), map_location=device)
    if not isinstance(checkpoint, dict) or "model" not in checkpoint:
        raise ValueError("checkpoint must contain a model state dict")
    return checkpoint


def _first_scalar(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    try:
        item = value.detach().reshape(-1)[0].cpu().item()
        item = float(item)
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError):
        return None
    return item if math.isfinite(item) else None


def _encode_video(ffmpeg, frames, fps, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            prefix=f".{target.stem}.", suffix=target.suffix,
            dir=target.parent, delete=False) as stream:
        temporary_output = Path(stream.name)
    command = [
        ffmpeg, "-y", "-loglevel", "error",
        "-framerate", str(fps),
        "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(temporary_output),
    ]
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        if result.returncode:
            detail = result.stderr.strip() or "unknown ffmpeg error"
            raise RuntimeError(
                "ffmpeg failed while creating {}: {}".format(target, detail))
        temporary_output.replace(target)
    finally:
        temporary_output.unlink(missing_ok=True)


def parser():
    from tab2body.strike_cfg import STRIKE

    ap = argparse.ArgumentParser(
        description="record deterministic strike rollout from two fixed cameras")
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--goal", type=Path, default=Path(STRIKE["goal_path"]))
    ap.add_argument(
        "--grip-reference", type=Path,
        default=Path(STRIKE["grip_reference_path"]))
    ap.add_argument("--device", default=STRIKE["device"])
    ap.add_argument("--fps", type=int, default=30, choices=(30, 60))
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--out-remembered", type=Path, default=None)
    ap.add_argument("--out-current", type=Path, default=None)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if args.width <= 0 or args.height <= 0:
        raise ValueError("video dimensions must be positive")
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("max steps must be positive")
    args.checkpoint = args.checkpoint.resolve()
    args.goal = args.goal.resolve()
    args.grip_reference = args.grip_reference.resolve()
    for label, path in (
            ("checkpoint", args.checkpoint),
            ("goal", args.goal),
            ("grip reference", args.grip_reference)):
        if not path.is_file():
            raise FileNotFoundError("{} does not exist: {}".format(label, path))
    ffmpeg = require_ffmpeg()


    import isaacgym
    from isaacgym import gymapi
    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE

    checkpoint = _load_checkpoint(torch, args.checkpoint, args.device)
    stage, tolerance, tempo_lambda = restore_stage_and_tolerance(checkpoint)
    outputs = resolve_video_paths(
        args.checkpoint, args.out_remembered, args.out_current)
    if outputs["remembered"] == outputs["current"]:
        raise ValueError("remembered/current video paths must be distinct")
    for output in outputs.values():
        output.parent.mkdir(parents=True, exist_ok=True)

    env = _construct_task(StrikeTask, args, STRIKE)
    try:
        if env.SIM_HZ % args.fps:
            raise ValueError(
                f"fps must divide the {env.SIM_HZ} Hz simulation clock")
        contract = _checkpoint_payload(checkpoint)[1]
        contract_model = _mapping(contract.get("model"))
        init_std = float(contract_model.get(
            "policy_init_std", STRIKE["policy_init_std"]))
        model = ActorCritic(
            env.num_obs, env.num_actions, env.value_dim,
            init_std=init_std).to(args.device)
        verify_live_contract(
            checkpoint, env, model, args.goal, args.grip_reference, STRIKE)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        obs = _restore_task(env, stage, tolerance, tempo_lambda)

        target_tensor = env.hbody_pos("RH:palm")[0].detach().cpu()
        target = tuple(float(value) for value in target_tensor)
        camera_properties = gymapi.CameraProperties()
        camera_properties.width = args.width
        camera_properties.height = args.height
        camera_properties.horizontal_fov = CAMERA_HORIZONTAL_FOV_DEG
        cameras = {}
        camera_report = {}
        for view, raw_direction in CAMERA_DIRECTIONS.items():
            direction = _unit(raw_direction)
            eye = tuple(
                target[axis] + CAMERA_DISTANCE_M * direction[axis]
                for axis in range(3))
            camera = env.gym.create_camera_sensor(
                env.envs[0], camera_properties)
            if camera < 0:
                raise RuntimeError(
                    "Isaac Gym could not create the {} camera".format(view))
            env.gym.set_camera_location(
                camera, env.envs[0],
                gymapi.Vec3(*eye), gymapi.Vec3(*target))
            cameras[view] = camera
            camera_report[view] = {
                "eye_world_m": list(eye),
                "target_world_m": list(target),
                "direction_target_to_camera": list(direction),
                "distance_m": CAMERA_DISTANCE_M,
                "horizontal_fov_deg": CAMERA_HORIZONTAL_FOV_DEG,
                "width": args.width,
                "height": args.height,
            }

        if args.max_steps is not None:
            max_steps = args.max_steps
        else:
            max_steps = int(STRIKE["artifact_max_steps"])
            goal_frames = getattr(getattr(env, "goals", None), "n_frames", 0)
            if stage == "A4_ZONE_CONTROL":
                max_steps = max(
                    max_steps, int(goal_frames) + int(env.SIM_HZ))

        stride = env.SIM_HZ // args.fps
        written = 0
        simulated = 0
        reset_count = 0
        reward_sum = 0.0
        sampled_info = {}
        with tempfile.TemporaryDirectory(
                prefix="tab2body_strike_rollout_") as temporary:
            temporary = Path(temporary)
            frame_dirs = {}
            for view in CAMERA_DIRECTIONS:
                directory = temporary / view
                directory.mkdir()
                frame_dirs[view] = directory

            for sim_frame in range(max_steps):
                if sim_frame % stride == 0:
                    env.gym.step_graphics(env.sim)
                    env.gym.render_all_camera_sensors(env.sim)
                    for view, camera in cameras.items():
                        env.gym.write_camera_image_to_file(
                            env.sim, env.envs[0], camera,
                            gymapi.IMAGE_COLOR,
                            str(frame_dirs[view] / "{:05d}.png".format(written)))
                    written += 1

                with torch.no_grad():
                    action, _log_prob, _value = model.act(
                        obs, deterministic=True)
                obs, reward, done, info = env.step(action)
                simulated += 1
                reward_value = _first_scalar(reward)
                if reward_value is not None:
                    reward_sum += reward_value
                for key in (
                        "grip_quality", "tip_ready_success_rate",
                        "release_count", "target_hit",
                        "wrong_crossing_count", "timing_error_ms",
                        "zone_quality", "strum_order_violation_count",
                        "strum_wrong_direction_count",
                        "strum_protected_crossing_count",
                        "strum_duplicate_crossing_count",
                        "wrong_crossing_rate", "joint_limit_max_usage",
                        "minimum_effective_gap_s", "overlap_window_count"):
                    value = _first_scalar(info.get(key))
                    if value is not None:
                        sampled_info[key] = value
                if bool(done.reshape(-1)[0].item()):
                    reset_count += 1
                    break

            if written == 0:
                raise RuntimeError("strike rollout produced no video frames")
            for view, target_path in outputs.items():
                _encode_video(
                    ffmpeg, frame_dirs[view], args.fps, target_path)

        report = {
            "schema": "tab2body.strike_rollout_artifacts.v1",
            "checkpoint": str(args.checkpoint),
            "goal": str(args.goal),
            "grip_reference": str(args.grip_reference),
            "checkpoint_contract_sha256": checkpoint[
                "checkpoint_contract"]["sha256"],
            "curriculum_stage": stage,
            "timing_tolerance_ms": tolerance,
            "tempo_lambda": tempo_lambda,
            "evaluation_scope": (
                "full_song_original_tempo"
                if env.evaluation_full_song
                else "training_phrase_current_tempo"),
            "deterministic": True,
            "simulation_hz": env.SIM_HZ,
            "video_fps": args.fps,
            "steps_simulated": simulated,
            "frames_per_view": written,
            "episode_ended": bool(reset_count),
            "mean_reward": reward_sum / max(simulated, 1),
            "last_diagnostics": sampled_info,
            "cameras": camera_report,
            "videos": {
                view: str(path.resolve())
                for view, path in outputs.items()
            },
        }
        report_path = outputs["remembered"].with_name(
            "{}_rollout.json".format(args.checkpoint.stem))
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("report: {}".format(report_path))
    finally:
        env.close()


if __name__ == "__main__":
    main()
