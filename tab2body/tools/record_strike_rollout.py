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
import importlib
import inspect
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


STRIKE_STAGES = (
    "A0_PICK_GRIP",
    "A1_TIP_READY",
    "A2_FREE_CROSSING",
    "A3_TIMED_CROSSING",
    "A4_ZONE_CONTROL",
)

# Frozen in render_pick_grip_pose.py and PROJECT_CONTEXT.md.  Values point
# from the shared RH:palm target toward the camera.
CAMERA_DIRECTIONS = {
    "remembered": (0.15, 0.85, 0.62),
    "current": (-0.7474, 0.4317, 0.62),
}
CAMERA_DISTANCE_M = 0.7
CAMERA_HORIZONTAL_FOV_DEG = 42.0


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _state_sources(checkpoint):
    environment = _mapping(checkpoint.get("environment_state"))
    context = _mapping(checkpoint.get("training_context"))
    sources = []
    for source in (environment, context):
        nested = _mapping(source.get("curriculum"))
        sources.append(source)
        if nested:
            sources.append(nested)
    return sources


def restore_stage_and_tolerance(checkpoint):
    """Resolve the saved task stage and timing tolerance, fail-closed.

    ``environment_state`` is authoritative when present because it captures
    the task itself.  ``training_context`` supports checkpoints produced
    before task-local curriculum state was added.
    """
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint must be a mapping")
    sources = _state_sources(checkpoint)

    stage = None
    stage_keys = ("curriculum_stage", "stage")
    for source in sources:
        for key in stage_keys:
            if key in source:
                stage = source[key]
                break
        if stage is not None:
            break
    if stage not in STRIKE_STAGES:
        raise ValueError(
            "checkpoint does not contain a valid strike curriculum stage")

    tolerance = None
    tolerance_keys = (
        "timing_tolerance_ms",
        "curriculum_timing_tolerance_ms",
        "curriculum_tolerance_ms",
    )
    for source in sources:
        for key in tolerance_keys:
            if key in source:
                tolerance = source[key]
                break
        if tolerance is not None:
            break
    if isinstance(tolerance, bool):
        raise ValueError("checkpoint timing tolerance must be positive")
    try:
        tolerance = float(tolerance)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "checkpoint does not contain a timing tolerance") from exc
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("checkpoint timing tolerance must be finite and positive")
    return stage, tolerance


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


def _controlled_dof_names(env):
    indices = env.ctrl_idx.detach().cpu().tolist()
    return [str(env.dof_names[index]) for index in indices]


def _fallback_verify_live_contract(
        checkpoint, validated, payload, env, goal_path, grip_reference_path):
    """Minimum complete compatibility check if the training helper is absent."""
    from tab2body.learning.checkpoint_contract import (
        file_sha256,
        verify_checkpoint_contract,
    )

    # This call checks the signature and exercises the standard verification
    # entry point.  The explicit comparisons below bind it to the live task.
    verify_checkpoint_contract(
        checkpoint, validated, purpose="record strike rollout")
    model = _mapping(payload.get("model"))
    live_dimensions = {
        "num_obs": int(env.num_obs),
        "num_actions": int(env.num_actions),
        "value_dim": int(env.value_dim),
    }
    for key, live_value in live_dimensions.items():
        if int(model.get(key, -1)) != live_value:
            raise ValueError(
                "checkpoint/live {} mismatch: {} != {}".format(
                    key, model.get(key), live_value))

    saved_names = list(_mapping(payload.get("control")).get(
        "controlled_dof_names", ()))
    live_names = _controlled_dof_names(env)
    if saved_names != live_names:
        raise ValueError("checkpoint/live controlled DOF ordering mismatch")

    inputs = _mapping(payload.get("inputs"))
    goal_hash = file_sha256(goal_path)
    grip_hash = file_sha256(grip_reference_path)
    if inputs.get("goal_sha256") != goal_hash:
        raise ValueError("checkpoint goal SHA-256 does not match --goal")
    if inputs.get("grip_reference_sha256") != grip_hash:
        raise ValueError(
            "checkpoint grip-reference SHA-256 does not match --grip-reference")

    manifest = getattr(env, "observation_manifest", None)
    saved_manifest = _mapping(payload.get("config")).get(
        "observation_manifest")
    if manifest is not None and list(manifest) != list(saved_manifest or ()):
        raise ValueError("checkpoint/live observation manifest mismatch")


def verify_live_contract(
        checkpoint, env, model, goal_path, grip_reference_path, strike_config):
    """Verify integrity and equality with the freshly constructed live task."""
    validated, payload = _checkpoint_payload(checkpoint)
    try:
        train_module = importlib.import_module("tab2body.train_strike")
    except ModuleNotFoundError as exc:
        if exc.name != "tab2body.train_strike":
            raise
        train_module = None
    helper = (
        getattr(train_module, "build_runtime_checkpoint_contract", None)
        if train_module is not None else None)
    if helper is not None:
        from tab2body.learning.checkpoint_contract import (
            verify_checkpoint_contract,
        )

        live_config = dict(strike_config)
        live_config["grip_reference_path"] = str(
            Path(grip_reference_path).resolve())
        saved_ppo = _mapping(
            _mapping(payload.get("config")).get("ppo"))
        live_contract = helper(
            env, model, goal_path, config=live_config,
            ppo_config=saved_ppo)
        verify_checkpoint_contract(
            checkpoint, live_contract, purpose="record strike rollout")
    else:
        _fallback_verify_live_contract(
            checkpoint, validated, payload, env,
            goal_path, grip_reference_path)
    return payload


def _construct_task(StrikeTask, args, strike_config):
    """Pass the stable task arguments plus explicitly supported eval options."""
    signature = inspect.signature(StrikeTask)
    parameters = signature.parameters
    has_var_kwargs = any(
        value.kind == inspect.Parameter.VAR_KEYWORD
        for value in parameters.values())
    stable = {
        "goal_path": str(args.goal),
        "grip_reference_path": str(args.grip_reference),
        "num_envs": 1,
        "device": args.device,
        "headless": True,
        "seed": int(strike_config["seed"]),
        "reset_noise": 0.0,
        "reset_soft_limit_fraction": float(
            strike_config["reset_soft_limit_fraction"]),
        "action_alpha": float(strike_config["action_alpha"]),
        "action_scale": float(strike_config["action_scale"]),
        "zone": strike_config["zone"],
        "trajectory": strike_config["trajectory"],
        "detector": strike_config["detector"],
        "reward": strike_config["reward"],
        "episode": strike_config["episode"],
        "failure_termination_penalty": float(
            strike_config["failure_termination_penalty"]),
        "random_start": False,
    }
    kwargs = {
        key: value for key, value in stable.items()
        if key in parameters or has_var_kwargs
    }
    # These names are not part of the required task API.  Supply them only
    # when the constructor explicitly advertises them.
    optional = {
        "full_song": True,
        "evaluation_mode": True,
        "config": strike_config,
    }
    kwargs.update({
        key: value for key, value in optional.items()
        if key in parameters
    })
    return StrikeTask(**kwargs)


def _set_evaluation_mode(env, stage):
    setter = getattr(env, "set_evaluation_mode", None)
    if callable(setter):
        setter(stage == "A4_ZONE_CONTROL")


def _restore_task(env, stage, tolerance):
    setter = getattr(env, "set_curriculum_stage", None)
    if not callable(setter):
        raise RuntimeError("StrikeTask lacks set_curriculum_stage")
    try:
        setter(stage, tolerance, reset=False)
    except TypeError:
        # Permit a keyword-only tolerance without weakening any semantics.
        setter(stage=stage, tolerance_ms=tolerance, reset=False)
    _set_evaluation_mode(env, stage)
    return env.reset()


def _load_checkpoint(torch, path, device):
    try:
        checkpoint = torch.load(
            str(path), map_location=device, weights_only=True)
    except TypeError:
        # PyTorch versions bundled with some Isaac Gym installs predate the
        # weights_only keyword.  The file is user-selected local input.
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
    command = [
        ffmpeg, "-y", "-loglevel", "error",
        "-framerate", str(fps),
        "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(target),
    ]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)
    if result.returncode:
        detail = result.stderr.strip() or "unknown ffmpeg error"
        raise RuntimeError(
            "ffmpeg failed while creating {}: {}".format(target, detail))


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
    if 60 % args.fps:
        raise ValueError("fps must divide the 60 Hz simulation clock")
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

    # Isaac Gym has to register its torch bridge before torch itself loads.
    import isaacgym  # noqa: F401
    from isaacgym import gymapi
    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE

    checkpoint = _load_checkpoint(torch, args.checkpoint, args.device)
    stage, tolerance = restore_stage_and_tolerance(checkpoint)
    outputs = resolve_video_paths(
        args.checkpoint, args.out_remembered, args.out_current)
    for output in outputs.values():
        output.parent.mkdir(parents=True, exist_ok=True)

    env = _construct_task(StrikeTask, args, STRIKE)
    try:
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
        obs = _restore_task(env, stage, tolerance)

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
                max_steps = max(max_steps, int(goal_frames) + 60)

        stride = 60 // args.fps
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
                        "zone_quality"):
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
            "deterministic": True,
            "simulation_hz": 60,
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
        close = getattr(env, "close", None)
        if callable(close):
            close()
        elif getattr(env, "sim", None) is not None:
            env.gym.destroy_sim(env.sim)
            env.sim = None


if __name__ == "__main__":
    main()
