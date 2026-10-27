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

from tab2body.strike_contract import (
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
    STRIKE_STAGES,
)



CAMERA_DIRECTIONS = {
    "remembered": (0.15, 0.85, 0.62),
    "current": (-0.7474, 0.4317, 0.62),
}
CAMERA_DISTANCE_M = 0.7
CAMERA_HORIZONTAL_FOV_DEG = 42.0
PRACTICE_DIRECTION_CODES = {"down": 1, "up": -1}
PAIRED_PRACTICE_STAGES = frozenset((
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
))


def _mapping(value):
    return value if isinstance(value, dict) else {}


def actual_practice_direction(env, *, required=False):
    """Read the direction actually assigned to replay environment zero."""
    raw = getattr(env, "practice_direction", None)
    stage = str(getattr(env, "curriculum_stage", ""))
    if raw is None or stage not in PAIRED_PRACTICE_STAGES:
        if required:
            raise ValueError(
                "paired strike diagnostic requires S0, S1 or S2 "
                "practice_direction")
        return None
    try:
        code = int(raw.reshape(-1)[0].item())
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
        raise ValueError(
            "strike practice_direction must be a nonempty tensor") from exc
    for label, expected in PRACTICE_DIRECTION_CODES.items():
        if code == expected:
            return label
    raise ValueError(f"unknown strike practice direction code: {code}")


def force_practice_direction(env, direction):
    """Force a diagnostic direction and rebuild the actor observation."""
    direction = str(direction)
    if direction not in PRACTICE_DIRECTION_CODES:
        raise ValueError("practice direction must be 'down' or 'up'")
    if str(getattr(env, "curriculum_stage", "")) not in PAIRED_PRACTICE_STAGES:
        raise ValueError("forced practice direction is only valid in S0--S2")
    target = getattr(env, "practice_direction", None)
    fill = getattr(target, "fill_", None)
    if not callable(fill):
        raise ValueError("strike environment has no writable practice_direction")
    fill(PRACTICE_DIRECTION_CODES[direction])
    if actual_practice_direction(env, required=True) != direction:
        raise RuntimeError("strike environment did not accept forced direction")
    compute = getattr(env, "compute_observations", None)
    if not callable(compute):
        raise ValueError("strike environment cannot rebuild observations")
    return compute()


def restore_stage_and_tolerance(checkpoint):
    """Restore the current task state after checking trainer/task alignment."""
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint must be a mapping")
    environment = checkpoint.get("environment_state")
    context = checkpoint.get("training_context")
    supported_environment_schemas = {
        "tab2body.strike_environment_state.v12",
        "tab2body.strike_environment_state.v13",
        "tab2body.strike_environment_state.v14",
    }
    if (not isinstance(environment, dict)
            or environment.get("schema")
            not in supported_environment_schemas):
        raise ValueError(
            "checkpoint requires strike environment_state.v12/v13/v14")
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
    strum_span = int(environment.get("strum_span", 0))
    if not 1 <= strum_span <= 6:
        raise ValueError("checkpoint strum span must be in [1, 6]")
    s2_profile_name = environment.get("s2_profile_name")
    if not isinstance(s2_profile_name, str) or not s2_profile_name:
        raise ValueError("checkpoint does not contain an S2 profile name")
    if environment.get("schema") == "tab2body.strike_environment_state.v14":
        s2_endpoint_recovery_active = environment.get(
            "s2_endpoint_recovery_active")
        s2_focus_direction = environment.get("s2_focus_direction")
        s2_focus_fraction = environment.get("s2_focus_fraction")
        if not isinstance(s2_endpoint_recovery_active, bool):
            raise ValueError(
                "checkpoint S2 endpoint recovery state must be bool")
        if s2_focus_direction not in ("balanced", "down", "up"):
            raise ValueError(
                "checkpoint S2 focus direction must be balanced/down/up")
        if isinstance(s2_focus_fraction, bool):
            raise ValueError("checkpoint S2 focus fraction must be numeric")
        try:
            s2_focus_fraction = float(s2_focus_fraction)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "checkpoint has no S2 focus fraction") from exc
        if (not math.isfinite(s2_focus_fraction)
                or not 0.5 <= s2_focus_fraction <= 0.7):
            raise ValueError(
                "checkpoint S2 focus fraction must be finite in [0.5, 0.7]")
        if (s2_endpoint_recovery_active
                and s2_focus_direction not in ("down", "up")):
            raise ValueError(
                "active S2 endpoint recovery requires down/up focus")
        if (not s2_endpoint_recovery_active
                and (s2_focus_direction != "balanced"
                     or abs(s2_focus_fraction - 0.5) > 1e-9)):
            raise ValueError(
                "inactive S2 endpoint recovery must be balanced at 0.5")
    else:
        s2_endpoint_recovery_active = False
        s2_focus_direction = "balanced"
        s2_focus_fraction = 0.5
    zone_gate_active = environment.get("zone_gate_active")
    if not isinstance(zone_gate_active, bool):
        raise ValueError("checkpoint zone gate state must be bool")
    dynamic_values = []
    for key in (
            "timing_reward_core_ms", "duration_reward_core_ms",
            "approach_lead_s", "timing_early_grace_ms",
            "timing_early_penalty_scale_ms"):
        value = environment.get(key)
        if isinstance(value, bool):
            raise ValueError(f"checkpoint {key} must be numeric")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"checkpoint does not contain {key}") from exc
        if (not math.isfinite(value)
                or (value <= 0.0 if key != "timing_early_grace_ms"
                    else value < 0.0)):
            raise ValueError(f"checkpoint {key} is invalid")
        dynamic_values.append(value)
    song_f1_gate = environment.get("song_f1_gate")
    if isinstance(song_f1_gate, bool):
        raise ValueError("checkpoint song F1 gate must be in [0, 1]")
    try:
        song_f1_gate = float(song_f1_gate)
    except (TypeError, ValueError) as exc:
        raise ValueError("checkpoint has no song F1 gate") from exc
    if not math.isfinite(song_f1_gate) or not 0.0 <= song_f1_gate <= 1.0:
        raise ValueError("checkpoint song F1 gate must be finite in [0, 1]")
    return (
        stage, tolerance, tempo_lambda, strum_span,
        s2_profile_name,
        s2_endpoint_recovery_active, s2_focus_direction, s2_focus_fraction,
        zone_gate_active, *dynamic_values, song_f1_gate)


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


def resolve_video_paths(
        checkpoint, remembered=None, current=None, full_song=False, *,
        diagnostic_suffix=None):
    """Apply the shared default naming contract, with per-view overrides."""
    from tab2body.learning.run_layout import (
        default_strike_full_song_video_paths,
        default_strike_video_paths,
    )

    defaults = (
        default_strike_full_song_video_paths(checkpoint)
        if full_song else default_strike_video_paths(checkpoint))
    if diagnostic_suffix is not None:
        video_dir = Path(checkpoint).resolve().parent.parent / "videos"
        defaults = {
            view: video_dir / (
                f"{Path(checkpoint).stem}_{diagnostic_suffix}_{view}.mp4")
            for view in CAMERA_DIRECTIONS
        }
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


def verify_diagnostic_actor_contract(
        checkpoint, env, model, goal_path, grip_reference_path, strike_config,
        *, allow_input_migration=False):
    """Fail closed on the frozen actor ABI while allowing new diagnostics.

    Reward, curriculum sampling and episode quota are intentionally excluded:
    an event-window replay never trains and explicitly overrides its quota.
    Physical geometry, detector, timing, inputs and the complete actor
    observation/action interface remain exact.
    """
    _, saved = _checkpoint_payload(checkpoint)
    from tab2body.strike_checkpoint import build_runtime_checkpoint_contract

    live_config = dict(strike_config)
    live_config["grip_reference_path"] = str(
        Path(grip_reference_path).resolve())
    saved_ppo = _mapping(_mapping(saved.get("config")).get("ppo"))
    live = build_runtime_checkpoint_contract(
        env, model, goal_path, config=live_config, ppo_config=saved_ppo)[
            "payload"]
    if not isinstance(allow_input_migration, bool):
        raise TypeError("allow_input_migration must be bool")
    exact_keys = ["schema", "task", "model", "control", "objective"]
    if not allow_input_migration:
        exact_keys.append("inputs")
    for key in exact_keys:
        if saved.get(key) != live.get(key):
            raise ValueError(
                f"diagnostic actor contract mismatch in {key}")
    saved_config = _mapping(saved.get("config"))
    live_contract_config = _mapping(live.get("config"))
    for key in ("model", "control", "objective", "observation_manifest", "timing"):
        if saved_config.get(key) != live_contract_config.get(key):
            raise ValueError(
                f"diagnostic actor config mismatch in {key}")
    saved_strike = _mapping(saved_config.get("strike"))
    live_strike = _mapping(live_contract_config.get("strike"))
    physical_keys = (
        "observation_contract", "action_scale", "action_alpha",
        "reset_soft_limit_fraction", "grip_control", "zone", "trajectory",
        "detector", "safety", "wrong_crossing_termination", "joint_limits",
        "direction_profile", "transition_profile", "recovery_contract",
        "strum_motion_contract", "pick_representation",
        "string_representation", "model_architecture",
    )
    for key in physical_keys:
        if saved_strike.get(key) != live_strike.get(key):
            raise ValueError(
                f"diagnostic physical contract mismatch in {key}")
    saved_lead = _mapping(saved_strike.get("episode")).get("timed_lead_frames")
    live_lead = _mapping(live_strike.get("episode")).get("timed_lead_frames")
    if saved_lead != live_lead:
        raise ValueError("diagnostic timed-lead contract mismatch")
    return saved


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


def _restore_task(env, stage, tolerance, tempo_lambda, strum_span,
                  s2_profile_name,
                  s2_endpoint_recovery_active, s2_focus_direction,
                  s2_focus_fraction, zone_gate_active,
                  timing_reward_core_ms, duration_reward_core_ms,
                  approach_lead_s, timing_early_grace_ms,
                  timing_early_penalty_scale_ms, song_f1_gate,
                  full_song=False):
    env.set_curriculum_stage(
        stage, tolerance, tempo_lambda=tempo_lambda,
        strum_span=strum_span,
        s2_profile_name=s2_profile_name,
        s2_endpoint_recovery_active=s2_endpoint_recovery_active,
        s2_focus_direction=s2_focus_direction,
        s2_focus_fraction=s2_focus_fraction,
        zone_active=zone_gate_active,
        timing_reward_core_ms=timing_reward_core_ms,
        duration_reward_core_ms=duration_reward_core_ms,
        approach_lead_s=approach_lead_s,
        timing_early_grace_ms=timing_early_grace_ms,
        timing_early_penalty_scale_ms=timing_early_penalty_scale_ms,
        song_f1_gate=song_f1_gate,
        reset=False)
    env.set_evaluation_mode(
        bool(full_song),
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


def _first_vector(value, size):
    if value is None:
        return [0.0] * size
    try:
        vector = value.detach().reshape(-1, value.shape[-1])[0].cpu().tolist()
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError):
        return [0.0] * size
    if len(vector) != size:
        raise ValueError(
            f"strike diagnostic vector has {len(vector)} entries; expected {size}")
    return [float(item) for item in vector]


def _goal_event_trace(env, index, *, practice_direction=None):
    traversal = env.goals.traversal_mask[index].detach().cpu().tolist()
    audible = env.goals.audible_mask[index].detach().cpu().tolist()
    gesture_code = int(env.goals.gesture[index].item())
    direction_code = int(env.goals.direction[index].item())
    planned_direction = "down" if direction_code == 1 else "up"
    actual_direction = practice_direction or planned_direction
    return {
        "event_index": int(index),
        "source_event_ids": list(env.goals.event_ids[index]),
        "frame": int(env.goals.frame[index].item()),
        "original_time_s": float(env.goals.time[index].item()),
        "effective_time_s": float(env._event_times[index].item()),
        "gesture": {
            0: "single_pick", 1: "strum", 2: "alternate_restrike",
        }.get(gesture_code, f"unknown_{gesture_code}"),
        "direction": actual_direction,
        "practice_direction": practice_direction,
        "planned_direction": planned_direction,
        "traversal_strings_0_based": [
            string for string, active in enumerate(traversal) if active],
        "audible_strings_0_based": [
            string for string, active in enumerate(audible) if active],
        "crossings": [],
        "observed_frame_count": 0,
        "target_hit": False,
        "miss": False,
        "wrong_crossing_count": 0.0,
        "timing_error_ms": [],
    }


def summarize_strike_event_trace(events):
    tp = 0
    fp = 0
    fn = 0
    completed = 0
    timing = []
    strum_events = 0
    strum_completed = 0
    blocked = 0
    wrong = 0.0
    observed_events = [
        event for event in events
        if int(event.get("observed_frame_count", 1)) > 0
    ]
    for event in observed_events:
        required = set(event["traversal_strings_0_based"])
        accepted = {
            crossing["string_0_based"]
            for crossing in event["crossings"]
            if crossing["accepted"]
        }
        tp += len(required & accepted)
        fn += len(required - accepted)
        fp += sum(
            1 for crossing in event["crossings"]
            if not crossing["accepted"])
        blocked += sum(
            1 for crossing in event["crossings"]
            if crossing["blocked_wait_rearm"])
        wrong += float(event["wrong_crossing_count"])
        completed += int(bool(event["target_hit"]))
        timing.extend(float(value) for value in event["timing_error_ms"])
        if event["gesture"] == "strum":
            strum_events += 1
            strum_completed += int(bool(event["target_hit"]))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2.0 * precision * recall / max(precision + recall, 1e-8)
    absolute_timing = sorted(abs(value) for value in timing)
    p95_index = max(0, math.ceil(0.95 * len(absolute_timing)) - 1)
    return {
        "planned_event_count": len(events),
        "observed_event_count": len(observed_events),
        "completed_event_count": completed,
        "event_completion_rate": completed / max(len(observed_events), 1),
        "strum_event_count": strum_events,
        "strum_completed_count": strum_completed,
        "strum_completion_rate": strum_completed / max(strum_events, 1),
        "traversal_true_positive_count": tp,
        "traversal_false_positive_count": fp,
        "traversal_false_negative_count": fn,
        "traversal_precision": precision,
        "traversal_recall": recall,
        "traversal_f1": f1,
        "blocked_crossing_count": blocked,
        "wrong_crossing_count": wrong,
        "timing_sample_count": len(timing),
        "timing_signed_mean_ms": (
            sum(timing) / len(timing) if timing else None),
        "timing_abs_p95_ms": (
            absolute_timing[p95_index] if absolute_timing else None),
    }


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


class LiveStrikeRolloutRecorder:
    def __init__(self, gymapi, env, *, fps=30, width=1600, height=900):
        if fps < 1 or env.SIM_HZ % fps:
            raise ValueError(
                f"fps must be positive and divide the {env.SIM_HZ} Hz simulation clock")
        if width < 1 or height < 1:
            raise ValueError("video dimensions must be positive")
        self.gymapi = gymapi
        self.env = env
        self.fps = int(fps)
        self.width = int(width)
        self.height = int(height)
        self.ffmpeg = require_ffmpeg()
        self.cameras = None
        self.camera_report = None

    def _ensure_cameras(self):
        if self.cameras is not None:
            return
        target_tensor = self.env.hbody_pos("RH:palm")[0].detach().cpu()
        target = tuple(float(value) for value in target_tensor)
        properties = self.gymapi.CameraProperties()
        properties.width = self.width
        properties.height = self.height
        properties.horizontal_fov = CAMERA_HORIZONTAL_FOV_DEG
        cameras = {}
        report = {}
        for view, raw_direction in CAMERA_DIRECTIONS.items():
            direction = _unit(raw_direction)
            eye = tuple(
                target[axis] + CAMERA_DISTANCE_M * direction[axis]
                for axis in range(3))
            camera = self.env.gym.create_camera_sensor(
                self.env.envs[0], properties)
            if camera < 0:
                raise RuntimeError(
                    f"Isaac Gym could not create the {view} camera")
            self.env.gym.set_camera_location(
                camera, self.env.envs[0],
                self.gymapi.Vec3(*eye), self.gymapi.Vec3(*target))
            cameras[view] = camera
            report[view] = {
                "eye_world_m": list(eye),
                "target_world_m": list(target),
                "direction_target_to_camera": list(direction),
                "distance_m": CAMERA_DISTANCE_M,
                "horizontal_fov_deg": CAMERA_HORIZONTAL_FOV_DEG,
                "width": self.width,
                "height": self.height,
            }
        self.cameras = cameras
        self.camera_report = report

    def record(self, torch, model, observation, outputs, max_steps):
        max_steps = int(max_steps)
        if max_steps < 1:
            raise ValueError("max steps must be positive")
        outputs = {
            view: Path(outputs[view]).resolve()
            for view in CAMERA_DIRECTIONS
        }
        if outputs["remembered"] == outputs["current"]:
            raise ValueError("remembered/current video paths must be distinct")
        for output in outputs.values():
            output.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_cameras()

        stride = self.env.SIM_HZ // self.fps
        written = 0
        simulated = 0
        reset_count = 0
        reward_sum = 0.0
        sampled_info = {}
        episode_end = {}
        grip_quality_samples = []
        pinch_quality_samples = []
        free_quality_samples = []
        grip_bad_streak = 0
        grip_bad_streak_max = 0
        practice_direction = actual_practice_direction(self.env)
        event_trace = [
            _goal_event_trace(
                self.env, index, practice_direction=practice_direction)
            for index in range(self.env.goals.num_events)
        ]
        was_training = bool(model.training)
        model.eval()
        try:
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
                        self.env.gym.step_graphics(self.env.sim)
                        self.env.gym.render_all_camera_sensors(self.env.sim)
                        for view, camera in self.cameras.items():
                            self.env.gym.write_camera_image_to_file(
                                self.env.sim, self.env.envs[0], camera,
                                self.gymapi.IMAGE_COLOR,
                                str(frame_dirs[view]
                                    / f"{written:05d}.png"))
                        written += 1

                    event_index_before = int(
                        self.env.event_index.reshape(-1)[0].item())
                    song_time_before = float(
                        self.env.song_time_s.reshape(-1)[0].item())
                    with torch.no_grad():
                        action, _log_prob, _value = model.act(
                            observation, deterministic=True)
                    observation, reward, done, info = self.env.step(action)
                    simulated += 1
                    reward_value = _first_scalar(reward)
                    if reward_value is not None:
                        reward_sum += reward_value
                    for key in (
                            "grip_quality", "grip_pinch_quality",
                            "grip_free_quality", "tip_ready_success_rate",
                            "release_count", "target_hit",
                            "wrong_crossing_count", "timing_error_ms",
                            "zone_quality", "strum_order_violation_count",
                            "strum_wrong_direction_count",
                            "strum_unplanned_crossing_count",
                            "strum_duplicate_crossing_count",
                            "recovery_progress",
                            "recovery_complete_pulse",
                            "scheduled_recovery_progress",
                            "scheduled_recovery_complete_pulse",
                            "recovery_handoff",
                            "recovery_same_string_handoff",
                            "recovery_required_frames",
                            "recovery_available_frames",
                            "recovery_reset_count",
                            "wrong_crossing_rate", "joint_limit_max_usage",
                            "minimum_effective_gap_s", "overlap_window_count"):
                        value = _first_scalar(info.get(key))
                        if value is not None:
                            sampled_info[key] = value
                    if 0 <= event_index_before < len(event_trace):
                        event = event_trace[event_index_before]
                        event["observed_frame_count"] += 1
                        release = _first_vector(info.get("release_mask"), 6)
                        accepted = _first_vector(
                            info.get("accepted_release_mask"), 6)
                        blocked = _first_vector(
                            info.get("blocked_release_mask"), 6)
                        direction = _first_vector(
                            info.get("release_direction"), 6)
                        subframe = _first_vector(
                            info.get("release_subframe_t"), 6)
                        for string_index in range(6):
                            if not (release[string_index]
                                    or blocked[string_index]):
                                continue
                            event["crossings"].append({
                                "simulation_frame": int(sim_frame),
                                "song_time_s": (
                                    song_time_before
                                    + subframe[string_index]
                                    / self.env.SIM_HZ),
                                "string_0_based": int(string_index),
                                "physical_release": bool(
                                    release[string_index]),
                                "accepted": bool(accepted[string_index]),
                                "blocked_wait_rearm": bool(
                                    blocked[string_index]),
                                "direction": int(direction[string_index]),
                            })
                        event["target_hit"] |= bool(
                            _first_scalar(info.get("target_hit")) or 0.0)
                        event["miss"] |= bool(
                            _first_scalar(info.get("miss")) or 0.0)
                        event["wrong_crossing_count"] += float(
                            _first_scalar(
                                info.get("wrong_crossing_count")) or 0.0)
                        if bool(_first_scalar(
                                info.get("timing_sample")) or 0.0):
                            timing_error = _first_scalar(
                                info.get("timing_error_ms"))
                            if timing_error is not None:
                                event["timing_error_ms"].append(timing_error)
                    grip_quality = _first_scalar(info.get("grip_quality"))
                    pinch_quality = _first_scalar(
                        info.get("grip_pinch_quality"))
                    free_quality = _first_scalar(
                        info.get("grip_free_quality"))
                    if grip_quality is not None:
                        if pinch_quality is None or free_quality is None:
                            raise RuntimeError(
                                "strike rollout omitted grip group quality")
                        grip_quality_samples.append(grip_quality)
                        pinch_quality_samples.append(pinch_quality)
                        free_quality_samples.append(free_quality)
                        if grip_quality < self.env.grip_bad_quality_threshold:
                            grip_bad_streak += 1
                            grip_bad_streak_max = max(
                                grip_bad_streak_max, grip_bad_streak)
                        else:
                            grip_bad_streak = 0
                    if bool(done.reshape(-1)[0].item()):
                        reset_count += 1
                        for key in getattr(
                                self.env, "episode_reason_keys", ()):
                            value = _first_scalar(info.get(f"episode_{key}"))
                            if value is not None:
                                episode_end[key] = bool(value)
                        break

                if written == 0:
                    raise RuntimeError(
                        "strike rollout produced no video frames")
                for view, target_path in outputs.items():
                    _encode_video(
                        self.ffmpeg, frame_dirs[view], self.fps,
                        target_path)
        finally:
            model.train(was_training)

        if not grip_quality_samples:
            raise RuntimeError("strike rollout produced no grip diagnostics")
        grip_tensor = torch.tensor(grip_quality_samples)
        pinch_tensor = torch.tensor(pinch_quality_samples)
        free_tensor = torch.tensor(free_quality_samples)
        grip_summary = {
            "sample_count": len(grip_quality_samples),
            "quality_mean": float(grip_tensor.mean()),
            "quality_p05": float(torch.quantile(grip_tensor, 0.05)),
            "quality_min": float(grip_tensor.min()),
            "pinch_quality_mean": float(pinch_tensor.mean()),
            "free_quality_mean": float(free_tensor.mean()),
            "bad_quality_threshold": self.env.grip_bad_quality_threshold,
            "bad_frame_rate": float(
                (grip_tensor < self.env.grip_bad_quality_threshold)
                .float().mean()),
            "bad_streak_max_frames": grip_bad_streak_max,
        }
        grip_summary["passed"] = bool(
            grip_summary["quality_mean"]
            >= self.env.curriculum_grip_quality_mean_gate
            and grip_summary["quality_p05"]
            >= self.env.curriculum_grip_quality_p05_gate
            and grip_summary["pinch_quality_mean"]
            >= self.env.curriculum_pinch_quality_mean_gate
            and grip_summary["free_quality_mean"]
            >= self.env.curriculum_free_quality_mean_gate
            and grip_summary["bad_frame_rate"]
            <= self.env.curriculum_max_grip_bad_frame_rate
            and grip_summary["bad_streak_max_frames"]
            <= self.env.curriculum_max_grip_bad_streak_frames)
        return {
            "deterministic": True,
            "practice_direction": practice_direction,
            "simulation_hz": self.env.SIM_HZ,
            "video_fps": self.fps,
            "steps_simulated": simulated,
            "frames_per_view": written,
            "simulation_duration_s": simulated / self.env.SIM_HZ,
            "video_duration_s": written / self.fps,
            "episode_ended": bool(reset_count),
            "episode_end": episode_end,
            "stitched_after_episode_reset": False,
            "mean_reward": reward_sum / max(simulated, 1),
            "last_diagnostics": sampled_info,
            "grip_preservation": grip_summary,
            "event_trace_summary": summarize_strike_event_trace(event_trace),
            "event_trace": event_trace,
            "cameras": self.camera_report,
            "videos": {
                view: str(path)
                for view, path in outputs.items()
            },
        }

    def record_practice_direction_pair(
            self, torch, model, outputs, max_steps, *,
            snapshot_runtime, restore_runtime):
        """Record matched down/up practice episodes and restore training state.

        ``restore_runtime`` must restore RNG/reset-generation state and perform
        the training reset.  Restoring the same snapshot before each member
        gives both directions identical sampled event/time conditions; the
        final restore returns the observation from which training can resume.
        """
        if str(getattr(
                self.env, "curriculum_stage", "")) not in PAIRED_PRACTICE_STAGES:
            raise ValueError("paired strike recordings require S0--S2")
        if not callable(snapshot_runtime) or not callable(restore_runtime):
            raise TypeError(
                "paired strike recording requires runtime snapshot/restore "
                "callbacks")
        if not isinstance(outputs, dict) or set(outputs) != set(
                PRACTICE_DIRECTION_CODES):
            raise ValueError(
                "paired strike outputs must contain exactly down and up")
        for direction, paths in outputs.items():
            if not isinstance(paths, dict):
                raise TypeError(
                    f"{direction} strike outputs must be a mapping")
            missing = set(CAMERA_DIRECTIONS) - set(paths)
            if missing:
                raise ValueError(
                    f"{direction} strike outputs are missing: "
                    + ", ".join(sorted(missing)))

        runtime = snapshot_runtime(self.env)
        captures = {}
        restored_observation = None
        capture_error = None
        try:
            for direction in PRACTICE_DIRECTION_CODES:
                observation = restore_runtime(self.env, runtime)
                observation = force_practice_direction(self.env, direction)
                capture = self.record(
                    torch, model, observation, outputs[direction], max_steps)
                actual = capture.get("practice_direction")
                if actual != direction:
                    raise RuntimeError(
                        "paired strike recorder observed the wrong direction: "
                        f"requested={direction}, actual={actual}")
                capture["requested_practice_direction"] = direction
                capture["paired_practice_diagnostic"] = True
                captures[direction] = capture
        except BaseException as exc:
            capture_error = exc
            raise
        finally:
            try:
                restored_observation = restore_runtime(self.env, runtime)
            except BaseException as restore_error:
                if capture_error is not None:
                    raise RuntimeError(
                        "paired strike capture failed and training runtime "
                        "restoration also failed") from restore_error
                raise
        for capture in captures.values():
            capture["training_runtime_restored_after_pair"] = True
            capture["training_rng_restored_before_reset"] = True
        return captures, restored_observation


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
    ap.add_argument("--full-song", action="store_true")
    ap.add_argument(
        "--start-event", type=int, default=None,
        help="record an exact S3 diagnostic window beginning at this event")
    ap.add_argument(
        "--event-count", type=int, default=1,
        help="number of consecutive events in an exact diagnostic window")
    ap.add_argument(
        "--tempo-lambda", type=float, default=None,
        help="diagnostic window tempo interpolation in [0, 1]")
    ap.add_argument(
        "--allow-input-migration", action="store_true",
        help=("diagnostic event-window only: accept changed source/config "
              "input hashes while preserving the actor and physical ABI"))
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if args.width <= 0 or args.height <= 0:
        raise ValueError("video dimensions must be positive")
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("max steps must be positive")
    if args.full_song and args.start_event is not None:
        raise ValueError("--full-song and --start-event are mutually exclusive")
    if args.start_event is None and args.tempo_lambda is not None:
        raise ValueError("--tempo-lambda requires --start-event")
    if args.allow_input_migration and args.start_event is None:
        raise ValueError("--allow-input-migration requires --start-event")
    if args.start_event is not None and (
            args.start_event < 0 or args.event_count < 1):
        raise ValueError("diagnostic event window must be positive and in range")
    diagnostic_tempo = (
        0.0 if args.start_event is not None and args.tempo_lambda is None
        else args.tempo_lambda)
    if (diagnostic_tempo is not None
            and not 0.0 <= diagnostic_tempo <= 1.0):
        raise ValueError("--tempo-lambda must be in [0, 1]")
    args.checkpoint = args.checkpoint.resolve()
    args.goal = args.goal.resolve()
    args.grip_reference = args.grip_reference.resolve()
    for label, path in (
            ("checkpoint", args.checkpoint),
            ("goal", args.goal),
            ("grip reference", args.grip_reference)):
        if not path.is_file():
            raise FileNotFoundError("{} does not exist: {}".format(label, path))
    import isaacgym
    from isaacgym import gymapi
    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE

    checkpoint = _load_checkpoint(torch, args.checkpoint, args.device)
    restored_curriculum = restore_stage_and_tolerance(checkpoint)
    stage, tolerance, tempo_lambda, strum_span = restored_curriculum[:4]
    if args.full_song and stage != "S3_SONG_INTEGRATION":
        raise ValueError("--full-song requires an S3_SONG_INTEGRATION checkpoint")
    diagnostic_suffix = None
    if args.start_event is not None:
        end_event = args.start_event + args.event_count - 1
        tempo_tag = f"{diagnostic_tempo:.2f}".replace(".", "p")
        diagnostic_suffix = (
            f"events_{args.start_event:03d}_{end_event:03d}_"
            f"lambda_{tempo_tag}")
    outputs = resolve_video_paths(
        args.checkpoint, args.out_remembered, args.out_current,
        full_song=args.full_song, diagnostic_suffix=diagnostic_suffix)
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
        from tab2body.learning.strike_v2_model import strike_actor_critic_class
        ModelType = strike_actor_critic_class(env.observation_contract)
        model = ModelType(
            env.num_obs, env.num_actions, env.value_dim,
            init_std=init_std).to(args.device)
        if args.start_event is None:
            verify_live_contract(
                checkpoint, env, model, args.goal, args.grip_reference, STRIKE)
        else:
            verify_diagnostic_actor_contract(
                checkpoint, env, model, args.goal, args.grip_reference, STRIKE,
                allow_input_migration=args.allow_input_migration)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        obs = _restore_task(
            env, *restored_curriculum, full_song=args.full_song)
        if args.start_event is not None:
            obs = env.set_diagnostic_event_window(
                args.start_event,
                args.event_count,
                tempo_lambda=diagnostic_tempo)

        if args.max_steps is not None:
            max_steps = args.max_steps
        elif args.full_song or args.start_event is not None:
            max_steps = int(env.max_episode_length)
        else:
            max_steps = int(STRIKE["artifact_max_steps"])

        recorder = LiveStrikeRolloutRecorder(
            gymapi, env, fps=args.fps, width=args.width,
            height=args.height)
        if args.full_song:
            env.wrong_crossing_termination_enabled = False
        capture = recorder.record(
            torch, model, obs, outputs, max_steps)

        report = {
            "schema": (
                "tab2body.strike_full_song_rollout.v2"
                if args.full_song
                else "tab2body.strike_event_window_diagnostic.v1"
                if args.start_event is not None
                else "tab2body.strike_rollout_artifacts.v2"),
            "checkpoint": str(args.checkpoint),
            "goal": str(args.goal),
            "grip_reference": str(args.grip_reference),
            "checkpoint_contract_sha256": checkpoint[
                "checkpoint_contract"]["sha256"],
            "curriculum_stage": stage,
            "timing_tolerance_ms": tolerance,
            "tempo_lambda": (
                1.0 if args.full_song else
                diagnostic_tempo if args.start_event is not None else
                tempo_lambda),
            "s2_profile_name": env.s2_profile_name,
            "s2_endpoint_recovery_active": bool(
                env.s2_endpoint_recovery_active),
            "s2_focus_direction": str(env.s2_focus_direction),
            "s2_focus_fraction": float(env.s2_focus_fraction),
            "approach_lead_s": env.approach_lead_s,
            "timing_early_grace_ms": env.timing_early_grace_ms,
            "timing_early_penalty_scale_ms": (
                env.timing_early_penalty_scale_ms),
            "evaluation_scope": (
                "full_song_original_tempo"
                if args.full_song
                else "diagnostic_event_window"
                if args.start_event is not None
                else "training_phrase_current_tempo"),
            "diagnostic_start_event": args.start_event,
            "diagnostic_event_count": (
                args.event_count if args.start_event is not None else None),
            **capture,
        }
        if args.full_song:
            from tab2body.learning.periodic_checkpoint_video import (
                strike_full_song_capture_contract,
                strike_full_song_capture_summary,
            )

            report.update(strike_full_song_capture_summary(
                strike_full_song_capture_contract(env), capture))
            report.update({
                "wrong_crossing_termination_suppressed": True,
                "irrecoverable_safety_termination_preserved": True,
            })
            report_path = outputs["remembered"].with_name(
                "{}_full_song.json".format(args.checkpoint.stem))
        elif args.start_event is not None:
            report_path = outputs["remembered"].with_name(
                f"{args.checkpoint.stem}_{diagnostic_suffix}.json")
        else:
            report_path = outputs["remembered"].with_name(
                "{}_rollout.json".format(args.checkpoint.stem))
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("report: {}".format(report_path))
        if (args.full_song
                and not report["captured_original_song_duration"]):
            raise RuntimeError(
                "S3 rollout ended before the original song duration")
    finally:
        env.close()


if __name__ == "__main__":
    main()
