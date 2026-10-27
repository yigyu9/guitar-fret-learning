"""Record a fail-closed, explicitly unqualified Full-G0 diagnostic rollout.

This is a plumbing diagnostic, not G0 qualification evidence.  It owns one
physical :class:`StrikeTask`, attaches a :class:`FretTask` policy view to that
same simulator, and advances the shared 105D actuator exactly once per frame.
The currently available checkpoints are not G0-qualified, so every artifact is
labelled ``diagnostic_unqualified`` and production postprocessor guards are
left untouched.

If setup, action inversion, physics, detector, or video encoding fails, the
tool writes JSON trace/summary artifacts and deliberately publishes no MP4.
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
import traceback
from typing import Optional


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
LOCAL_ISAACGYM_PYTHON = PROJECT_ROOT / "isaacgym" / "python"
if (LOCAL_ISAACGYM_PYTHON / "isaacgym" / "__init__.py").is_file():
    sys.path.insert(0, str(LOCAL_ISAACGYM_PYTHON))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ARTIFACT_SCHEMA = "tab2body.full_g0_diagnostic_unqualified.v1"
DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT / "docs" / "2026-09-21" / "synchronizer" / "full_g0")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "record one-simulator Full-G0 plumbing diagnostics; outputs are "
            "always diagnostic_unqualified and never promotion evidence"))
    ap.add_argument("--fret-checkpoint", required=True, type=Path)
    ap.add_argument("--strike-checkpoint", required=True, type=Path)
    ap.add_argument("--song", default="02_Jazz1-200-B_solo")
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument(
        "--max-steps", type=int, default=None,
        help=(
            "optional diagnostic safety cap; by default the recorder derives "
            "a ceiling from the complete canonical timeline and runs until "
            "the final event resolves"))
    ap.add_argument("--fps", type=int, choices=(30, 60), default=30)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument(
        "--no-watermark", action="store_true",
        help="record raw simulator frames without the diagnostic banner")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--video-name", default="full_g0_diagnostic_unqualified.mp4")
    ap.add_argument("--trace-name", default="full_g0_trace.json")
    ap.add_argument("--summary-name", default="full_g0_summary.json")
    ap.add_argument(
        "--pre-side-epsilon-m", type=float, default=0.00025,
        help="strict negative entry-plane margin used by Strike readiness")
    ap.add_argument(
        "--braking-horizon-ms", type=float, default=25.0,
        help=(
            "first hold target retreats against measured joint velocity by "
            "this prediction horizon"))
    return ap


def _validate_output_names(args) -> None:
    for label in ("video_name", "trace_name", "summary_name"):
        value = Path(getattr(args, label))
        if value.name != str(value) or value.name in {"", ".", ".."}:
            raise ValueError(f"--{label.replace('_', '-')} must be a file name")
    if Path(args.video_name).suffix.lower() != ".mp4":
        raise ValueError("--video-name must end in .mp4")
    if args.trace_name == args.summary_name:
        raise ValueError("trace and summary names must differ")


def _validate_args(args) -> None:
    _validate_output_names(args)
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("--max-steps must be positive")
    if args.width <= 0 or args.height <= 0:
        raise ValueError("video dimensions must be positive")
    if 60 % args.fps:
        raise ValueError("--fps must divide the 60 Hz simulator clock")
    minimum_video_steps = 60 // args.fps + 1
    if args.max_steps is not None and args.max_steps < minimum_video_steps:
        raise ValueError(
            "--max-steps must capture at least two video frames "
            f"(minimum {minimum_video_steps} at {args.fps} FPS)")
    if not math.isfinite(args.pre_side_epsilon_m) \
            or args.pre_side_epsilon_m < 0.0:
        raise ValueError("--pre-side-epsilon-m must be finite and non-negative")
    if not math.isfinite(args.braking_horizon_ms) \
            or args.braking_horizon_ms < 0.0:
        raise ValueError("--braking-horizon-ms must be finite and non-negative")
    args.fret_checkpoint = args.fret_checkpoint.resolve()
    args.strike_checkpoint = args.strike_checkpoint.resolve()
    for label, path in (
            ("Fret checkpoint", args.fret_checkpoint),
            ("Strike checkpoint", args.strike_checkpoint)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} not found: {path}")


def _json_value(value):
    """Convert small Torch/Numpy diagnostic values without importing either."""
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _full_timeline_step_limit(timeline, preroll_frames: int) -> int:
    """Return a fail-safe ceiling that cannot truncate a normal full rollout.

    An overdue event is resolved at most once per physics frame.  The event
    count is therefore retained as drain reserve after the latest authored
    deadline instead of assuming that every earlier event resolved on time.
    The loop still exits immediately when the canonical score clock finishes.
    """
    latest_completion = max(
        max(
            event.release_decision_deadline_frame,
            event.traversal_end_frame + event.effective_delay_cap_frames,
        )
        for event in timeline.events
    )
    return int(preroll_frames) + int(latest_completion) + len(
        timeline.events) + 1


def _diagnostic_gate_status(
        *, timeline_completed: bool, blocked_count: int,
        hold_saturation_count: int, unsafe_state_frame_count: int,
        joint_limit_violation_count: int):
    failures = []
    if not timeline_completed:
        failures.append("timeline_incomplete")
    if blocked_count:
        failures.append("crossing_detected_while_permission_closed")
    if hold_saturation_count:
        failures.append("current_pose_hold_saturated")
    if unsafe_state_frame_count:
        failures.append("nonfinite_or_velocity_blowup")
    if joint_limit_violation_count:
        failures.append("joint_limit_violation")
    passed = not failures
    status = (
        "diagnostic_completed" if passed else
        "diagnostic_incomplete_timeline"
        if not timeline_completed else
        "diagnostic_failed_gate")
    return passed, failures, status


def _diagnostic_label(no_watermark: bool) -> Optional[str]:
    return (None if no_watermark else
            "DIAGNOSTIC_UNQUALIFIED / NOT G0 VALIDATION")


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.pending")
    temporary.write_text(
        json.dumps(_json_value(document), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    temporary.replace(path)


def _checkpoint_control(source):
    payload = source.contract["payload"]
    control = payload.get("control")
    if not isinstance(control, dict):
        raise ValueError(f"{source.task} checkpoint lacks control contract")
    return control


def _camera(env, gymapi, *, width, height):
    # Reuse the established Fret upper-body framing so the neck, both hands,
    # torso and guitar are visible from the playable side.
    from tab2body.tools.record_fret_rollout import upper_body_camera

    camera = upper_body_camera(
        env, int(width), int(height), horizontal_fov_deg=55.0)
    eye, target = camera.eye, camera.target
    properties = gymapi.CameraProperties()
    properties.width = int(width)
    properties.height = int(height)
    properties.horizontal_fov = 55.0
    handle = env.gym.create_camera_sensor(env.envs[0], properties)
    if handle < 0:
        raise RuntimeError("Isaac Gym camera creation failed")
    env.gym.set_camera_location(
        handle, env.envs[0], gymapi.Vec3(*eye), gymapi.Vec3(*target))
    return handle


def _capture_frame(
        env, camera, gymapi, output: Path, label: Optional[str], *, width: int,
        height: int) -> None:
    from PIL import Image, ImageDraw

    env.gym.step_graphics(env.sim)
    env.gym.render_all_camera_sensors(env.sim)
    env.gym.write_camera_image_to_file(
        env.sim, env.envs[0], camera, gymapi.IMAGE_COLOR, str(output))
    if not output.is_file():
        raise RuntimeError("Isaac Gym did not write the camera frame")
    image = Image.open(output).convert("RGB")
    if image.size != (int(width), int(height)):
        raise RuntimeError(
            f"unexpected Isaac camera image size: {image.size} "
            f"(expected {(int(width), int(height))})")
    if label is not None:
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 620, 42), fill=(110, 0, 0))
        draw.text((16, 15), label, fill=(255, 255, 255))
    image.save(output)


def _encode_video(frame_dir: Path, staged_video: Path, fps: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to publish the MP4")
    command = [
        ffmpeg, "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frame_dir / "%06d.png"), "-c:v", "libx264",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(staged_video),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not staged_video.is_file() \
            or staged_video.stat().st_size == 0:
        raise RuntimeError(
            "ffmpeg failed: " + (completed.stderr.strip() or "unknown error"))


def _set_source_time_views(fret_env, strike_env, runtime) -> None:
    event = runtime.clock.current()
    score_frame = event.score_frame
    frame = score_frame.clamp_min(0)
    fret_env.goals.frame_idx.copy_(frame.clamp_max(fret_env.goals.n_frames - 1))
    fret_env.preparation_remaining.copy_(
        (-score_frame).clamp(min=0, max=fret_env.preparation_frames))
    strike_env.event_index.copy_(
        event.event_index.clamp_max(strike_env.goals.num_events - 1))
    # Strike-v2 timing features consume the real score clock, including the
    # common negative pre-roll, so both frozen skills see the same countdown.
    strike_env.song_time_s.copy_(event.score_time_s)


def _fret_readiness(fret_env, target_frets, *, refresh: bool):
    from tab2body.full.readiness import evaluate_sounding_fret_readiness

    cells = (fret_env.reward_fn.refresh_press_state() if refresh
             else fret_env.reward_fn.active_press_cells())
    return evaluate_sounding_fret_readiness(cells, target_frets)


def _strike_readiness(strike_env, pre_side_epsilon_m):
    import torch
    from tab2body.env.strike_detector import DETECTOR_ARMED
    from tab2body.env.tasks.task_strike import PHASE_APPROACH
    from tab2body.full.readiness import evaluate_strike_readiness

    tip = strike_env.to_guitar_frame(
        strike_env.hbody_pos("RH:pick")[:, None])[:, 0]
    segments = strike_env.string_segments_g()
    lane, normal = strike_env._string_lane_geometry(
        strike_env.target_lane_y, segments=segments)
    (target_string, _lane_y, center, _ready, entry, _exit,
     _final) = strike_env._current_target_geometry()
    rows = torch.arange(strike_env.num_envs, device=strike_env.device)
    target_normal = normal[rows, target_string]
    direction = strike_env._current_motion_context()["target_direction"].to(
        tip.dtype)
    signed_axis = direction[:, None] * target_normal
    signed_distance = ((tip - center) * signed_axis).sum(dim=1)
    velocity = strike_env._tip_velocity_g
    approach_speed = (velocity * signed_axis).sum(dim=1)
    # Stationary is admissible once the entry hold is latched; only clearly
    # reversing motion invalidates readiness.
    direction_ok = approach_speed >= -float(strike_env.detector.min_across_speed)
    armed = strike_env.detector.state[rows, target_string] == DETECTOR_ARMED
    q = strike_env.dof_state.view(
        strike_env.num_envs, strike_env.n_dof, 2)[:, :, 0]
    grip = strike_env.grip_reference.measure(q)["grip_success"]
    readiness = evaluate_strike_readiness(
        strike_env.motor_phase, grip,
        torch.linalg.vector_norm(tip - entry, dim=1), armed, direction_ok,
        signed_distance, approach_phase=PHASE_APPROACH,
        entry_distance_threshold_m=strike_env.entry_distance,
        pre_side_epsilon_m=pre_side_epsilon_m)
    return readiness, {
        "target_string": target_string,
        "entry_signed_distance_m": signed_distance,
        "entry_distance_m": torch.linalg.vector_norm(tip - entry, dim=1),
        "approach_speed_m_s": approach_speed,
        "detector_armed": armed,
        "grip_success": grip,
    }


def _advance_diagnostic_motor_state(strike_env, command, release) -> None:
    """Minimal external phase projection; never presented as source parity."""
    import torch
    from tab2body.env.tasks.task_strike import (
        PHASE_APPROACH, PHASE_READY, PHASE_RELEASE_RECOVER,
    )

    tip = strike_env.to_guitar_frame(
        strike_env.hbody_pos("RH:pick")[:, None])[:, 0]
    _target, _lane, _center, ready, _entry, _exit, _final = (
        strike_env._current_target_geometry())
    q = strike_env.dof_state.view(
        strike_env.num_envs, strike_env.n_dof, 2)[:, :, 0]
    grip = strike_env.grip_reference.measure(q)["grip_success"]
    at_ready = torch.linalg.vector_norm(tip - ready, dim=1) \
        <= strike_env.ready_distance
    in_ready = strike_env.motor_phase == PHASE_READY
    strike_env.ready_streak.copy_(torch.where(
        in_ready & at_ready & grip, strike_env.ready_streak + 1,
        torch.where(in_ready, torch.zeros_like(strike_env.ready_streak),
                    strike_env.ready_streak)))
    lead_frames = int(math.ceil(strike_env.approach_lead_s * strike_env.SIM_HZ))
    approach_window = command.event.score_frame \
        >= command.event.release_boundary_frame - lead_frames
    open_approach = in_ready & approach_window \
        & (strike_env.ready_streak >= strike_env.ready_hold_frames)
    strike_env.motor_phase.copy_(torch.where(
        open_approach, torch.full_like(strike_env.motor_phase, PHASE_APPROACH),
        strike_env.motor_phase))
    released = release.any(dim=1) & command.decision.strike_permission
    strike_env.motor_phase.copy_(torch.where(
        released,
        torch.full_like(strike_env.motor_phase, PHASE_RELEASE_RECOVER),
        strike_env.motor_phase))
    recovering = strike_env.motor_phase == PHASE_RELEASE_RECOVER
    strike_env.recovery_count.copy_(torch.where(
        recovering, strike_env.recovery_count + 1,
        torch.zeros_like(strike_env.recovery_count)))
    rearmed = (strike_env.detector.state == 0).all(dim=1)
    recovered = recovering & rearmed \
        & (strike_env.recovery_count >= strike_env.recovery_frames)
    strike_env.motor_phase.copy_(torch.where(
        recovered, torch.full_like(strike_env.motor_phase, PHASE_READY),
        strike_env.motor_phase))


def _run(args, summary, trace, video_path: Path) -> None:
    # Isaac Gym must precede Torch in this process.
    import isaacgym  # noqa: F401
    from isaacgym import gymapi
    import torch

    from tab2body.cfg import FRET
    from tab2body.env.config import configured_kwargs
    from tab2body.env.rewards.fret import adjacent_finger_action_synergy
    from tab2body.env.rewards.strike import constrain_pick_grip_actions
    from tab2body.env.tasks import FretTask, StrikeTask
    from tab2body.env.tasks.task_strike import PHASE_READY
    from tab2body.env.tasks.task_full import (
        FullG0PhysicsSnapshot, FullG0SharedActuator, FullG0TaskController,
    )
    from tab2body.full.action import FullActionManifest
    from tab2body.full.events import compile_song_bundle_events
    from tab2body.full.runtime import G0SynchronizationRuntime
    from tab2body.full.source_policies import load_frozen_skill_pair
    from tab2body.song_bundles import (
        bundle_path, fret_goal_path, hand_targets_path, strike_goal_path,
    )
    from tab2body.strike_cfg import STRIKE

    bundle = (args.bundle.resolve() if args.bundle is not None
              else bundle_path(args.song).resolve())
    pair = load_frozen_skill_pair(
        song_id=args.song, bundle_path=bundle,
        fret_checkpoint=args.fret_checkpoint,
        strike_checkpoint=args.strike_checkpoint, device=args.device)
    timeline = compile_song_bundle_events(bundle)
    manifest = FullActionManifest.from_mjcf(
        PACKAGE_ROOT / "assets" / "smpl_mpl_hands_body.xml",
        fret_action_names=pair.fret.action_names,
        strike_action_names=pair.strike.action_names)
    summary["sources"] = {
        "qualified_for_g0": pair.qualified_for_g0,
        "fret": {
            **pair.fret.qualification.to_document(),
            "checkpoint_sha256": pair.fret.checkpoint_sha256,
            "contract_sha256": pair.fret.contract_sha256,
        },
        "strike": {
            **pair.strike.qualification.to_document(),
            "checkpoint_sha256": pair.strike.checkpoint_sha256,
            "contract_sha256": pair.strike.contract_sha256,
        },
    }
    summary["runtime_mode"] = "identity_integration_probe_only"
    summary["validation_claim"] = False

    fret_control = _checkpoint_control(pair.fret)
    strike_control = _checkpoint_control(pair.strike)
    for name in ("action_alpha", "action_scale", "reset_soft_limit_fraction"):
        if float(fret_control[name]) != float(strike_control[name]):
            raise RuntimeError(f"source actuator scalar mismatch: {name}")

    strike_env = StrikeTask(**configured_kwargs(
        StrikeTask, STRIKE, goal_path=str(strike_goal_path(args.song)),
        grip_reference_path=str(STRIKE["grip_reference_path"]), num_envs=1,
        device=args.device, headless=True, seed=42, random_start=False,
        action_alpha=float(strike_control["action_alpha"]),
        action_scale=float(strike_control["action_scale"]),
        reset_soft_limit_fraction=float(
            strike_control["reset_soft_limit_fraction"])))
    try:
        strike_env.set_curriculum_stage(
            "S3_SONG_INTEGRATION", 50.0, tempo_lambda=1.0, reset=False)
        strike_env.set_evaluation_mode(full_song=True, reset=False)
        strike_env.reset()

        # StrikeTask owns the shared simulator and therefore its authored limit
        # setup.  The Fret profile mismatch remains an explicit diagnostic
        # limitation; production handshakes are not bypassed or forged.
        fret_env = FretTask(**configured_kwargs(
            FretTask, FRET, goal_path=str(fret_goal_path(args.song)),
            hand_targets_path=str(hand_targets_path(args.song)), num_envs=1,
            device=args.device, headless=True, seed=42, random_start=False,
            action_alpha=float(fret_control["action_alpha"]),
            action_scale=float(fret_control["action_scale"]),
            reset_soft_limit_fraction=float(
                fret_control["reset_soft_limit_fraction"]),
            human_hard_limits_enabled=False, human_hard_limit_path=None,
            shared_backend=strike_env))
        fret_env.set_curriculum_stage("full_song", reset=False)
        # Seed the goal-independent contact hysteresis once.  Every subsequent
        # physical frame refreshes it exactly once, after the shared step.
        fret_env.reward_fn.refresh_press_state()

        actuator = FullG0SharedActuator(strike_env, manifest)
        hold_action = actuator.previous_full_action.clone()
        runtime = G0SynchronizationRuntime(
            pair, timeline, manifest, num_envs=1,
            allow_identity_postprocessors=True)
        controller = FullG0TaskController(runtime)
        controller.reset(hold_action)
        automatic_step_limit = _full_timeline_step_limit(
            timeline, runtime.clock.preroll_frames)
        step_limit = (
            automatic_step_limit
            if args.max_steps is None else int(args.max_steps))
        summary.update({
            "execution_scope": (
                "full_timeline_auto"
                if args.max_steps is None else "explicit_step_cap"),
            "automatic_full_timeline_step_limit": automatic_step_limit,
            "configured_step_limit": step_limit,
        })
        summary["braking_horizon_ms"] = float(args.braking_horizon_ms)
        summary["source_semantics_exact"] = False
        summary["source_semantics_limitations"] = [
            "unqualified source checkpoints",
            "identity runtime postprocessors",
            "Fret view uses the Strike-owned authored joint-limit backend",
            "Strike motor phase is projected by this diagnostic recorder",
        ]

        camera = _camera(
            strike_env, gymapi, width=args.width, height=args.height)
        frame_stride = 60 // args.fps
        staged_video = video_path.with_name(
            f".{video_path.stem}.pending{video_path.suffix}")
        if staged_video.exists():
            staged_video.unlink()
        with tempfile.TemporaryDirectory(prefix="full_g0_frames_") as temp:
            frame_dir = Path(temp)
            frame_number = 0
            previous_event = -1
            blocked_count = accepted_count = 0
            hold_saturation_count = 0
            unsafe_state_frame_count = 0
            joint_limit_violation_count = 0
            max_abs_joint_velocity = 0.0
            max_pd_target_error = 0.0
            min_joint_limit_margin = float("inf")
            worst_limit_joint = None
            worst_limit_q = None
            worst_limit_lower = None
            worst_limit_upper = None
            for step_index in range(step_limit):
                _set_source_time_views(fret_env, strike_env, runtime)
                event_now = runtime.clock.current()
                event_id = int(event_now.event_index[0].item())
                if event_id != previous_event:
                    strike_env.event_resolved.zero_()
                    strike_env._event_release_mask.zero_()
                    strike_env.ready_streak.zero_()
                    strike_env.motor_phase.fill_(PHASE_READY)
                    previous_event = event_id

                fret_env.prev_action.copy_(
                    actuator.previous_full_action[:, actuator.fret_indices])
                strike_env.prev_action.copy_(
                    actuator.previous_full_action[:, actuator.strike_indices])
                fret_state = _fret_readiness(
                    fret_env, event_now.target_frets, refresh=False)
                strike_state, strike_diag = _strike_readiness(
                    strike_env, args.pre_side_epsilon_m)
                fret_obs = fret_env.compute_synchronizer_observation(
                    press_advance_frames=3)
                strike_obs = strike_env._build_strike_v2_observation()
                if fret_obs.shape != (1, pair.fret.obs_dim) \
                        or strike_obs.shape != (1, pair.strike.obs_dim):
                    raise RuntimeError("exact source observation builder shape drift")
                hold = actuator.strike_entry_hold(
                    braking_horizon_s=args.braking_horizon_ms / 1000.0)

                current_goal = fret_env.goals.current()

                def simulate_once(command):
                    nonlocal hold_saturation_count
                    if bool((command.decision.hold_strike_action
                             & hold.saturated).any().item()):
                        hold_saturation_count += 1
                        raise RuntimeError(
                            "current-pose first-frame hold saturated")
                    actuator.commit_strike_hold(
                        command.decision.hold_strike_action,
                        hold.pose_action)
                    full_command = command.action.full_action.clone()
                    fret_action = full_command[:, actuator.fret_indices]
                    action_mask = fret_env.policy_action_mask(
                        include_goal_pair_routing=False)
                    fret_action = torch.where(
                        action_mask, fret_action, fret_env.prev_action)
                    follower = fret_env._current_finger_activity()
                    follower = __import__(
                        "tab2body.env.rewards.fret", fromlist=[
                            "finger_synergy_follower_mask"]).finger_synergy_follower_mask(
                                follower, current_goal["finger_event"])
                    fret_action, _induced, _gate = adjacent_finger_action_synergy(
                        fret_action, fret_env.prev_action,
                        fret_env._finger_flexion_action_indices, follower,
                        fret_env.ctrl_half, action_scale=fret_env.action_scale,
                        coefficients=fret_env.finger_synergy_coefficients,
                        min_driver_delta_deg=
                            fret_env.finger_synergy_min_driver_delta_deg,
                        full_driver_delta_deg=
                            fret_env.finger_synergy_full_driver_delta_deg,
                        max_induced_delta_deg=
                            fret_env.finger_synergy_max_induced_delta_deg)
                    fret_action = torch.where(
                        command.decision.hold_fret_action[:, None],
                        full_command[:, actuator.fret_indices], fret_action)
                    strike_action = constrain_pick_grip_actions(
                        full_command[:, actuator.strike_indices],
                        strike_env._grip_reference_action,
                        strike_env._grip_residual_action_span,
                        strike_env._action_is_hand)
                    strike_action = torch.where(
                        command.decision.hold_strike_action[:, None],
                        full_command[:, actuator.strike_indices], strike_action)
                    full_command[:, actuator.fret_indices] = fret_action
                    full_command[:, actuator.strike_indices] = strike_action

                    previous_tip = strike_env.to_guitar_frame(
                        strike_env.hbody_pos("RH:pick")[:, None])[:, 0].clone()
                    executed = actuator.apply_and_step(full_command)
                    strike_env.progress_buf.add_(1)
                    tip = strike_env.to_guitar_frame(
                        strike_env.hbody_pos("RH:pick")[:, None])[:, 0]
                    strike_env._tip_velocity_g.copy_(
                        (tip - previous_tip) * strike_env.SIM_HZ)
                    start, end = strike_env.string_segments_g()
                    detection = strike_env.detector.step(
                        previous_tip, tip, start, end,
                        dt=1.0 / strike_env.SIM_HZ)
                    release = detection["release"]
                    strike_env._previous_tip_g.copy_(tip)
                    strike_env._previous_tip_valid.fill_(True)
                    strike_env._last_release.copy_(release)
                    _advance_diagnostic_motor_state(
                        strike_env, command, release)
                    post_fret = _fret_readiness(
                        fret_env, command.event.target_frets,
                        refresh=True).ready_mask
                    return FullG0PhysicsSnapshot(
                        executed_full_action=executed,
                        crossing_mask=release,
                        crossing_subframe_t=detection["subframe_t"],
                        crossing_direction=detection["direction"],
                        fret_ready_mask=post_fret)

                step = controller.step(
                    fret_observation=fret_obs,
                    strike_observation=strike_obs,
                    hold_action=hold_action,
                    fret_ready_mask=fret_state.ready_mask,
                    strike_ready=strike_state.ready,
                    guitar_stable=torch.ones(
                        1, dtype=torch.bool, device=args.device),
                    strike_entry_hold_action=hold.pre_ema_action,
                    simulate_once=simulate_once)
                blocked = int(step.synchronization.blocked_crossing_mask.sum().item())
                accepted = int(step.synchronization.accepted_crossing_mask.sum().item())
                blocked_count += blocked
                accepted_count += accepted
                dof = strike_env.dof_state.view(
                    strike_env.num_envs, strike_env.n_dof, 2)
                q, qd = dof[:, :, 0], dof[:, :, 1]
                movable = strike_env.nonlocked_idx
                lower = strike_env.dof_lower.view(
                    strike_env.num_envs, strike_env.n_dof)
                upper = strike_env.dof_upper.view(
                    strike_env.num_envs, strike_env.n_dof)
                movable_margins = torch.minimum(
                    q - lower, upper - q)[:, movable]
                limit_margin, local_limit_index = movable_margins[0].min(0)
                limit_dof_index = int(
                    movable[int(local_limit_index.item())].item())
                limit_joint_name = strike_env.dof_names[limit_dof_index]
                limit_q = float(q[0, limit_dof_index].item())
                limit_lower = float(lower[0, limit_dof_index].item())
                limit_upper = float(upper[0, limit_dof_index].item())
                max_qd = qd[:, movable].abs().amax()
                target_error = (
                    strike_env.pd_target.view(
                        strike_env.num_envs, strike_env.n_dof)[:, movable]
                    - q[:, movable]).abs().amax()
                termination = strike_env.termination_reasons()
                unsafe_state = torch.zeros(
                    strike_env.num_envs, dtype=torch.bool,
                    device=strike_env.device)
                for name, value in termination.items():
                    if name.startswith("nonfinite_") \
                            or name == "velocity_blowup":
                        unsafe_state |= value
                unsafe_state_frame_count += int(unsafe_state.sum().item())
                limit_violation = limit_margin < -1e-6
                joint_limit_violation_count += int(limit_violation.item())
                max_abs_joint_velocity = max(
                    max_abs_joint_velocity, float(max_qd.item()))
                max_pd_target_error = max(
                    max_pd_target_error, float(target_error.item()))
                if float(limit_margin.item()) < min_joint_limit_margin:
                    min_joint_limit_margin = float(limit_margin.item())
                    worst_limit_joint = limit_joint_name
                    worst_limit_q = limit_q
                    worst_limit_lower = limit_lower
                    worst_limit_upper = limit_upper
                trace.append({
                    "step": step_index,
                    "event_id": event_id,
                    "score_frame": int(step.command.event.score_frame[0].item()),
                    "deadline_action": int(step.command.decision.action[0].item()),
                    "fret_ready_mask": fret_state.ready_mask[0],
                    "strike_ready": bool(strike_state.ready[0].item()),
                    "strike_permission": bool(
                        step.command.decision.strike_permission[0].item()),
                    "hold_strike": bool(
                        step.command.decision.hold_strike_action[0].item()),
                    "hold_saturated": bool(hold.saturated[0].item()),
                    "timing_shift_frames": int(
                        step.command.decision.timing_shift_frames[0].item()),
                    "crossing_mask": step.physics.crossing_mask[0],
                    "blocked_crossing_mask":
                        step.synchronization.blocked_crossing_mask[0],
                    "accepted_crossing_mask":
                        step.synchronization.accepted_crossing_mask[0],
                    "resolved": bool(step.synchronization.resolved[0].item()),
                    "outcome": int(step.synchronization.outcome[0].item()),
                    "max_abs_joint_velocity_rad_s": float(max_qd.item()),
                    "min_joint_limit_margin_rad": float(limit_margin.item()),
                    "min_margin_joint": limit_joint_name,
                    "min_margin_joint_q_rad": limit_q,
                    "min_margin_joint_lower_rad": limit_lower,
                    "min_margin_joint_upper_rad": limit_upper,
                    "max_pd_target_error_rad": float(target_error.item()),
                    "unsafe_state": bool(unsafe_state[0].item()),
                    "termination_reasons": {
                        name: bool(value[0].item())
                        for name, value in termination.items()
                        if name != "base_termination"
                    },
                    **{name: value[0] for name, value in strike_diag.items()},
                })
                if step_index % frame_stride == 0:
                    _capture_frame(
                        strike_env, camera,
                        gymapi, frame_dir / f"{frame_number:06d}.png",
                        _diagnostic_label(args.no_watermark),
                        width=args.width, height=args.height)
                    frame_number += 1
                if bool(runtime.clock.finished.all().item()):
                    break

            if not trace or frame_number < 2:
                raise RuntimeError("physical diagnostic produced insufficient evidence")
            _encode_video(frame_dir, staged_video, args.fps)
            staged_video.replace(video_path)
            timeline_completed = bool(runtime.clock.finished.all().item())
            physical_gate_passed, gate_failures, status = (
                _diagnostic_gate_status(
                    timeline_completed=timeline_completed,
                    blocked_count=blocked_count,
                    hold_saturation_count=hold_saturation_count,
                    unsafe_state_frame_count=unsafe_state_frame_count,
                    joint_limit_violation_count=joint_limit_violation_count))
            summary.update({
                "status": status,
                "physical_loop_completed": True,
                "timeline_completed": timeline_completed,
                "physical_gate_passed": physical_gate_passed,
                "physical_gate_failures": gate_failures,
                "steps": len(trace),
                "video_frames": frame_number,
                "blocked_crossing_count": blocked_count,
                "accepted_crossing_count": accepted_count,
                "hold_saturation_count": hold_saturation_count,
                "unsafe_state_frame_count": unsafe_state_frame_count,
                "joint_limit_violation_count": joint_limit_violation_count,
                "max_abs_joint_velocity_rad_s": max_abs_joint_velocity,
                "min_joint_limit_margin_rad": min_joint_limit_margin,
                "worst_limit_joint": worst_limit_joint,
                "worst_limit_joint_q_rad": worst_limit_q,
                "worst_limit_joint_lower_rad": worst_limit_lower,
                "worst_limit_joint_upper_rad": worst_limit_upper,
                "max_pd_target_error_rad": max_pd_target_error,
                "physics_step_count": actuator.physics_step_count,
                "video": str(video_path),
            })
    finally:
        if hasattr(strike_env, "gym") and hasattr(strike_env, "sim"):
            strike_env.gym.destroy_sim(strike_env.sim)


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    # Validate leaf names before resolving or touching any output path.  An
    # invalid name must never redirect the stale-video quarantine outside the
    # requested output directory.
    _validate_output_names(args)
    output_dir = args.output_dir.resolve()
    video_path = output_dir / args.video_name
    trace_path = output_dir / args.trace_name
    summary_path = output_dir / args.summary_name
    summary = {
        "schema": ARTIFACT_SCHEMA,
        "mode": "diagnostic_unqualified",
        "status": "initializing",
        "validation_claim": False,
        "song_id": args.song,
        "fret_checkpoint": str(args.fret_checkpoint),
        "strike_checkpoint": str(args.strike_checkpoint),
        "diagnostic_watermark": not args.no_watermark,
        "physical_loop_completed": False,
        "video": None,
    }
    trace = []
    try:
        _validate_args(args)
        output_dir.mkdir(parents=True, exist_ok=True)
        if len({video_path, trace_path, summary_path}) != 3:
            raise ValueError(
                "video, trace and summary output paths must differ")
        _run(args, summary, trace, video_path)
    except Exception as exc:  # fail-closed artifact is part of this tool's ABI
        summary.update({
            "status": "fail_closed",
            "failure_type": type(exc).__name__,
            "failure": str(exc),
            "traceback": traceback.format_exc(),
            "physical_loop_completed": False,
            "video": None,
        })
        pending = video_path.with_name(
            f".{video_path.stem}.pending{video_path.suffix}")
        if pending.exists():
            pending.unlink()
        # Never leave a previous result looking like the output of this failed run.
        if video_path.exists():
            quarantine = video_path.with_suffix(".stale.mp4")
            video_path.replace(quarantine)
            summary["quarantined_previous_video"] = str(quarantine)
        exit_code = 2
    else:
        exit_code = 0
    finally:
        _write_json(trace_path, {
            "schema": ARTIFACT_SCHEMA,
            "mode": "diagnostic_unqualified",
            "frames": trace,
        })
        summary["trace"] = str(trace_path)
        summary["summary"] = str(summary_path)
        _write_json(summary_path, summary)
    print(json.dumps(_json_value(summary), ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
