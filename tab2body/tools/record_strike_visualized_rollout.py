"""Record an opt-in strike diagnostic replay with zone and pick overlays.

This tool is intentionally separate from :mod:`record_strike_rollout`.
The base recorder is part of the saved strike checkpoint implementation
fingerprint, so changing it would make already-trained checkpoints fail their
live-contract check.  This additive tool reuses its verified loading and
camera helpers while leaving the original videos and metadata untouched.

The overlay is diagnostic only.  It projects the live fixed-string geometry,
the guitar-local strike bands, and the geometry-less ``RH:pick`` point into
each Isaac Gym camera image.  It never adds collision or rigid geometry.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def resolve_visualized_video_paths(
        checkpoint, remembered=None, current=None, *, evaluation_state=False):
    """Return additive zone/pick video paths without touching base outputs."""
    checkpoint = Path(checkpoint).resolve()
    run_root = checkpoint.parent.parent
    video_root = run_root / "videos"
    stem = checkpoint.stem
    suffix = "_evalstate" if evaluation_state else ""
    defaults = {
        "remembered": (
            video_root / f"{stem}_rollout_remembered_zone_pick{suffix}.mp4"),
        "current": (
            video_root / f"{stem}_rollout_current_zone_pick{suffix}.mp4"),
    }
    return {
        "remembered": (
            Path(remembered).resolve()
            if remembered is not None else defaults["remembered"]),
        "current": (
            Path(current).resolve()
            if current is not None else defaults["current"]),
    }


def resolve_visualized_report_path(checkpoint, remembered_output, report=None):
    """Keep visualized metadata separate from the base rollout JSON."""
    if report is not None:
        return Path(report).resolve()
    return Path(remembered_output).resolve().with_name(
        f"{Path(checkpoint).stem}_rollout_zone_pick"
        f"{'_evalstate' if str(remembered_output).endswith('_evalstate.mp4') else ''}.json")


def restored_environment_spec(checkpoint):
    """Return the exact vectorized reset shape saved by a checkpoint.

    A one-environment replay cannot restore the checkpoint's per-environment
    reset generations.  That creates a different song/reset distribution and
    is unsuitable for judging a learned strike.  Keep this validation close to
    the recorder so all diagnostic tools share the same replay contract.
    """
    state = checkpoint.get("environment_state")
    if not isinstance(state, dict):
        raise ValueError("checkpoint has no environment_state for exact replay")
    generation = state.get("reset_generation")
    size = getattr(generation, "numel", None)
    if not callable(size) or int(size()) <= 0:
        raise ValueError("checkpoint reset_generation must be a nonempty tensor")
    if "random_start" not in state:
        raise ValueError("checkpoint environment_state has no random_start")
    return int(size()), bool(state["random_start"])


def construct_evaluation_replay_task(StrikeTask, args, strike_config, checkpoint):
    """Construct a task shape-compatible with checkpoint environment state."""
    import inspect

    num_envs, random_start = restored_environment_spec(checkpoint)
    signature = inspect.signature(StrikeTask)
    parameters = signature.parameters
    has_var_kwargs = any(
        value.kind == inspect.Parameter.VAR_KEYWORD
        for value in parameters.values())
    stable = {
        "goal_path": str(args.goal),
        "grip_reference_path": str(args.grip_reference),
        "num_envs": num_envs,
        "device": args.device,
        "headless": True,
        "seed": int(strike_config["seed"]),
        # Evaluation retains the training reset distribution.  Setting this
        # to zero was the remaining source of a visually plausible but policy
        # incompatible replay after restoring the RNG state.
        "reset_noise": float(strike_config["reset_noise"]),
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
        "random_start": random_start,
    }
    kwargs = {
        key: value for key, value in stable.items()
        if key in parameters or has_var_kwargs
    }
    return StrikeTask(**kwargs)


def restore_evaluation_replay(env, checkpoint):
    """Reproduce trainer evaluation's reset, resume, full-song reset order."""
    state = checkpoint.get("environment_state")
    if not isinstance(state, dict):
        raise ValueError("checkpoint has no environment_state for exact replay")
    # PPOTrainer initializes observations before resume.  The resume then
    # restores RNG/reset-generation and resets; evaluation requests full-song
    # and resets once more.  Preserve that order exactly.
    env.reset()
    env.load_curriculum_state_dict(state)
    env.set_evaluation_mode(True, reset=False)
    return env.reset()


def parser():
    from tab2body.strike_cfg import STRIKE

    ap = argparse.ArgumentParser(
        description=(
            "record deterministic strike replay with six-string, strike-zone "
            "and virtual-pick diagnostic overlays"))
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
    ap.add_argument("--trail-frames", type=int, default=12)
    ap.add_argument("--out-remembered", type=Path, default=None)
    ap.add_argument("--out-current", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    return ap


def _validate_args(args):
    if args.width <= 0 or args.height <= 0:
        raise ValueError("video dimensions must be positive")
    if 60 % args.fps:
        raise ValueError("fps must divide the 60 Hz simulation clock")
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("max steps must be positive")
    if args.trail_frames < 1:
        raise ValueError("trail frames must be positive")

    args.checkpoint = args.checkpoint.resolve()
    args.goal = args.goal.resolve()
    args.grip_reference = args.grip_reference.resolve()
    for label, path in (
            ("checkpoint", args.checkpoint),
            ("goal", args.goal),
            ("grip reference", args.grip_reference)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")


def _camera_spec(CameraSpec, eye, target, args, horizontal_fov):
    return CameraSpec(
        eye=tuple(float(value) for value in eye),
        target=tuple(float(value) for value in target),
        width=int(args.width),
        height=int(args.height),
        horizontal_fov_deg=float(horizontal_fov),
    )


def _finite_float(value):
    value = float(value)
    return value if math.isfinite(value) else None


def main(argv=None):
    args = parser().parse_args(argv)
    _validate_args(args)

    # Isaac Gym must register its bridge before torch or overlay helpers that
    # may import torch are loaded.
    import isaacgym  # noqa: F401
    from isaacgym import gymapi
    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE
    from tab2body.tools import record_strike_rollout as base
    from tab2body.tools.strike_visualization import (
        CameraSpec,
        OVERLAY_COLORS,
        VISUAL_STRING_RIBBON_HALF_WIDTH_M,
        draw_strike_zone_pick_overlay,
    )

    ffmpeg = base.require_ffmpeg()
    checkpoint = base._load_checkpoint(
        torch, args.checkpoint, args.device)
    stage, tolerance = base.restore_stage_and_tolerance(checkpoint)
    outputs = resolve_visualized_video_paths(
        args.checkpoint, args.out_remembered, args.out_current,
        evaluation_state=True)
    report_path = resolve_visualized_report_path(
        args.checkpoint, outputs["remembered"], args.report)
    all_targets = (*outputs.values(), report_path)
    if len({path.resolve() for path in all_targets}) != len(all_targets):
        raise ValueError("visualized video and report paths must be distinct")
    for output in all_targets:
        output.parent.mkdir(parents=True, exist_ok=True)

    env = construct_evaluation_replay_task(
        StrikeTask, args, STRIKE, checkpoint)
    try:
        contract = base._checkpoint_payload(checkpoint)[1]
        contract_model = base._mapping(contract.get("model"))
        init_std = float(contract_model.get(
            "policy_init_std", STRIKE["policy_init_std"]))
        model = ActorCritic(
            env.num_obs, env.num_actions, env.value_dim,
            init_std=init_std).to(args.device)
        base.verify_live_contract(
            checkpoint, env, model, args.goal, args.grip_reference, STRIKE)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        if stage != "A4_ZONE_CONTROL":
            raise ValueError(
                "exact evaluation replay currently requires A4_ZONE_CONTROL")
        obs = restore_evaluation_replay(env, checkpoint)

        target_tensor = env.hbody_pos("RH:palm")[0].detach().cpu()
        target = tuple(float(value) for value in target_tensor)
        camera_properties = gymapi.CameraProperties()
        camera_properties.width = args.width
        camera_properties.height = args.height
        camera_properties.horizontal_fov = (
            base.CAMERA_HORIZONTAL_FOV_DEG)
        cameras = {}
        camera_specs = {}
        camera_report = {}
        for view, raw_direction in base.CAMERA_DIRECTIONS.items():
            direction = base._unit(raw_direction)
            eye = tuple(
                target[axis]
                + base.CAMERA_DISTANCE_M * direction[axis]
                for axis in range(3))
            camera = env.gym.create_camera_sensor(
                env.envs[0], camera_properties)
            if camera < 0:
                raise RuntimeError(
                    f"Isaac Gym could not create the {view} camera")
            env.gym.set_camera_location(
                camera, env.envs[0],
                gymapi.Vec3(*eye), gymapi.Vec3(*target))
            cameras[view] = camera
            camera_specs[view] = _camera_spec(
                CameraSpec, eye, target, args,
                base.CAMERA_HORIZONTAL_FOV_DEG)
            camera_report[view] = {
                "eye_world_m": list(eye),
                "target_world_m": list(target),
                "direction_target_to_camera": list(direction),
                "distance_m": base.CAMERA_DISTANCE_M,
                "horizontal_fov_deg":
                    base.CAMERA_HORIZONTAL_FOV_DEG,
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
        pick_trail_world = []
        target_strings_seen = set()
        lane_y_min = None
        lane_y_max = None
        last_overlay_state = {}

        with tempfile.TemporaryDirectory(
                prefix="tab2body_strike_zone_pick_") as temporary:
            temporary = Path(temporary)
            frame_dirs = {}
            for view in base.CAMERA_DIRECTIONS:
                directory = temporary / view
                directory.mkdir()
                frame_dirs[view] = directory

            for sim_frame in range(max_steps):
                if sim_frame % stride == 0:
                    env.gym.step_graphics(env.sim)
                    env.gym.render_all_camera_sensors(env.sim)

                    pick = (
                        env.hbody_pos("RH:pick")[0].detach().cpu().tolist())
                    pick_trail_world.append(
                        tuple(float(value) for value in pick))
                    del pick_trail_world[:-args.trail_frames]

                    frame_states = {}
                    for view, camera in cameras.items():
                        frame_path = (
                            frame_dirs[view]
                            / f"{written:05d}.png")
                        env.gym.write_camera_image_to_file(
                            env.sim, env.envs[0], camera,
                            gymapi.IMAGE_COLOR, str(frame_path))
                        frame_states[view] = (
                            draw_strike_zone_pick_overlay(
                                frame_path,
                                env,
                                camera_specs[view],
                                pick_trail_world=pick_trail_world[:-1],
                            ))
                    # Geometry state is view-independent; retain one copy.
                    last_overlay_state = frame_states["remembered"]
                    target_string = last_overlay_state.get(
                        "target_string_number")
                    if target_string is not None:
                        target_strings_seen.add(int(target_string))
                    lane_y = last_overlay_state.get("target_lane_y_m")
                    if lane_y is not None:
                        lane_y = _finite_float(lane_y)
                    if lane_y is not None:
                        lane_y_min = (
                            lane_y if lane_y_min is None
                            else min(lane_y_min, lane_y))
                        lane_y_max = (
                            lane_y if lane_y_max is None
                            else max(lane_y_max, lane_y))
                    written += 1

                with torch.no_grad():
                    action, _log_prob, _value = model.act(
                        obs, deterministic=True)
                obs, reward, done, _info = env.step(action)
                simulated += 1
                reward_value = base._first_scalar(reward)
                if reward_value is not None:
                    reward_sum += reward_value
                if bool(done.reshape(-1)[0].item()):
                    reset_count += 1
                    break

            if written == 0:
                raise RuntimeError(
                    "strike diagnostic replay produced no video frames")
            for view, target_path in outputs.items():
                base._encode_video(
                    ffmpeg, frame_dirs[view], args.fps, target_path)

        report = {
            "schema":
                "tab2body.strike_zone_pick_rollout_artifacts.v1",
            "checkpoint": str(args.checkpoint),
            "goal": str(args.goal),
            "grip_reference": str(args.grip_reference),
            "checkpoint_contract_sha256":
                checkpoint["checkpoint_contract"]["sha256"],
            "curriculum_stage": stage,
            "timing_tolerance_ms": tolerance,
            "source_mode": "deterministic_replay",
            "replay_initialization": (
                "checkpoint environment_state restored at its saved "
                "vectorized environment count"),
            "deterministic": True,
            "simulation_hz": 60,
            "video_fps": args.fps,
            "steps_simulated": simulated,
            "frames_per_view": written,
            "episode_ended": bool(reset_count),
            "mean_reward": reward_sum / max(simulated, 1),
            "cameras": camera_report,
            "overlay": {
                "coordinate_frame": "live guitar-local",
                "compositing": (
                    "post-render 3D-to-2D diagnostic projection; "
                    "no simulation or collision geometry added"),
                "strings": [
                    {
                        "string": index,
                        "start_body": f"G:string{index}",
                        "end_body": f"G:string{index}_end",
                    }
                    for index in range(1, 7)
                ],
                "allowed_y_m": list(env.allowed_y),
                "preferred_y_m": list(env.preferred_y),
                "lane_core_half_width_m": env.lane_core_half_width,
                "lane_allowed_half_width_m":
                    env.lane_allowed_half_width,
                "visual_string_ribbon_half_width_m":
                    VISUAL_STRING_RIBBON_HALF_WIDTH_M,
                "pick_body": "RH:pick",
                "virtual_marker_no_geometry": True,
                "trail_frames": args.trail_frames,
                "colors": OVERLAY_COLORS,
                "target_strings_seen": sorted(target_strings_seen),
                "sampled_lane_y_min_m": lane_y_min,
                "sampled_lane_y_max_m": lane_y_max,
                "last_state": last_overlay_state,
            },
            "videos": {
                view: str(path.resolve())
                for view, path in outputs.items()
            },
        }
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"report: {report_path}")
        return report
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()
        elif getattr(env, "sim", None) is not None:
            env.gym.destroy_sim(env.sim)
            env.sim = None


if __name__ == "__main__":
    main()
