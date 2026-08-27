"""Deterministic Strike motion/safety diagnostic replay.

This audit intentionally does not create reward gates.  It records the
distributions needed to decide R6--R17 thresholds after a policy can already
produce physical RELEASE events: tip speed/depth, recovery crossings,
joint-group velocity/acceleration/jerk, action saturation, grip quality and
analytical right-arm guitar penetration.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PHASE_NAMES = {
    0: "READY",
    1: "APPROACH",
    2: "RELEASE_RECOVER",
}


def resolve_motion_audit_path(checkpoint, output=None):
    checkpoint = Path(checkpoint).resolve()
    if output is not None:
        return Path(output).resolve()
    if checkpoint.parent.name == "checkpoints":
        return (
            checkpoint.parent.parent / "evaluations"
            / f"{checkpoint.stem}.motion_diagnostics.json")
    return checkpoint.with_name(
        f"{checkpoint.stem}.motion_diagnostics.json")


def summarize_samples(values):
    """Return a finite deterministic summary without external dependencies."""
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return {
            "count": 0,
            "mean": None,
            "p50": None,
            "p95": None,
            "maximum": None,
        }

    def percentile(probability):
        position = probability * (len(finite) - 1)
        lower = int(math.floor(position))
        upper = int(math.ceil(position))
        if lower == upper:
            return finite[lower]
        fraction = position - lower
        return finite[lower] + fraction * (finite[upper] - finite[lower])

    return {
        "count": len(finite),
        "mean": sum(finite) / len(finite),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "maximum": finite[-1],
    }


def _write_json_atomic(path, value):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    document = json.dumps(
        value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp",
                delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _scalar(value):
    return value.detach().reshape(-1)[0].cpu().item()


def _group_control_indices(names):
    groups = {
        "shoulder": [],
        "elbow": [],
        "wrist": [],
        "hand": [],
    }
    for index, name in enumerate(names):
        if name.startswith("R_Shoulder"):
            groups["shoulder"].append(index)
        elif name.startswith("R_Elbow"):
            groups["elbow"].append(index)
        elif name.startswith("R_Wrist"):
            groups["wrist"].append(index)
        elif name.startswith("RH:"):
            groups["hand"].append(index)
        else:
            raise ValueError(f"unclassified Strike control DOF: {name}")
    expected = {"shoulder": 3, "elbow": 3, "wrist": 3, "hand": 21}
    actual = {name: len(indices) for name, indices in groups.items()}
    if actual != expected:
        raise ValueError(
            f"Strike motion diagnostic control groups changed: {actual}")
    return groups


def parser():
    from tab2body.strike_cfg import STRIKE

    ap = argparse.ArgumentParser(
        description="replay a Strike checkpoint and measure motion diagnostics")
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--goal", type=Path, default=Path(STRIKE["goal_path"]))
    ap.add_argument(
        "--grip-reference", type=Path,
        default=Path(STRIKE["grip_reference_path"]))
    ap.add_argument("--device", default=STRIKE["device"])
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("max steps must be positive")
    args.checkpoint = args.checkpoint.resolve()
    args.goal = args.goal.resolve()
    args.grip_reference = args.grip_reference.resolve()
    output = resolve_motion_audit_path(args.checkpoint, args.out)
    for label, path in (
            ("checkpoint", args.checkpoint),
            ("goal", args.goal),
            ("grip reference", args.grip_reference)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")


    import isaacgym
    import torch

    from tab2body.env.strike_detector import DIRECTION_UP
    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE
    from tab2body.tools import record_strike_rollout as base

    checkpoint = base._load_checkpoint(
        torch, args.checkpoint, args.device)
    stage, tolerance, tempo_lambda = base.restore_stage_and_tolerance(checkpoint)
    env = base._construct_task(StrikeTask, args, STRIKE)
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
        obs = base._restore_task(env, stage, tolerance, tempo_lambda)

        control_names = list(env.controlled_dof_names)
        groups = _group_control_indices(control_names)
        phase_group_samples = {
            phase: {
                group: {
                    "velocity": [], "acceleration": [], "jerk": [],
                    "joint_limit_usage": [],
                }
                for group in groups
            }
            for phase in PHASE_NAMES.values()
        }
        overall = {
            "tip_speed_m_s": [],
            "grip_quality": [],
            "grip_pinch_rms_rad": [],
            "grip_free_rms_rad": [],
            "action_saturation_fraction": [],
            "penetration_depth_m": [],
            "swept_penetration_depth_m": [],
            "joint_limit_max_usage": [],
            "joint_limit_near_rate": [],
        }
        release_depths = []
        release_speeds = []
        release_records = []
        recovery_frames = 0
        recovery_outside_string_field = 0
        recovery_release_count = 0
        recovery_reverse_release_count = 0
        penetration_frames = 0
        penetration_terminations = 0
        phase_violations = 0
        blocked_crossings = 0
        failure_terminations = 0

        string_start, string_end = env.string_segments_g()
        all_string_x = torch.cat([
            string_start[0, :, 0], string_end[0, :, 0]])
        string_x_min = float(all_string_x.min().detach().cpu())
        string_x_max = float(all_string_x.max().detach().cpu())
        corridor_margin = float(env.detector.rearm_separation)

        previous_qd = None
        previous_acceleration = None
        simulated = 0
        episode_ended = False
        max_steps = (
            int(args.max_steps)
            if args.max_steps is not None
            else max(
                int(STRIKE["artifact_max_steps"]),
                int(env.goals.n_frames) + env.SIM_HZ
                if env.evaluation_full_song
                else int(env.max_episode_length) + 1,
            ))

        with torch.no_grad():
            for step_index in range(max_steps):
                action, _log_probability, _value = model.act(
                    obs, deterministic=True)
                obs, _reward, done, info = env.step(action)
                simulated += 1

                action_phase = int(_scalar(info["action_motor_phase"]))
                phase_name = PHASE_NAMES.get(
                    action_phase, f"UNKNOWN_{action_phase}")
                if phase_name not in phase_group_samples:
                    raise RuntimeError(
                        f"unknown Strike motor phase in audit: {action_phase}")

                state = env.dof_state.view(
                    env.num_envs, env.n_dof, 2)
                qd = state[0, env.ctrl_idx, 1].detach().cpu()
                acceleration = (
                    None if previous_qd is None
                    else (qd - previous_qd) * env.SIM_HZ)
                jerk = (
                    None
                    if acceleration is None or previous_acceleration is None
                    else (acceleration - previous_acceleration) * env.SIM_HZ)
                for group, indices in groups.items():
                    index_tensor = torch.tensor(indices, dtype=torch.long)
                    group_qd = qd[index_tensor]
                    phase_group_samples[phase_name][group][
                        "joint_limit_usage"].append(float(_scalar(
                            info[f"joint_limit_{group}_max_usage"])))
                    phase_group_samples[phase_name][group][
                        "velocity"].append(float(torch.sqrt(
                            torch.mean(group_qd * group_qd))))
                    if acceleration is not None:
                        group_acceleration = acceleration[index_tensor]
                        phase_group_samples[phase_name][group][
                            "acceleration"].append(float(torch.sqrt(torch.mean(
                                group_acceleration * group_acceleration))))
                    if jerk is not None:
                        group_jerk = jerk[index_tensor]
                        phase_group_samples[phase_name][group][
                            "jerk"].append(float(torch.sqrt(
                                torch.mean(group_jerk * group_jerk))))
                previous_qd = qd
                if acceleration is not None:
                    previous_acceleration = acceleration

                overall["tip_speed_m_s"].append(float(
                    _scalar(info["tip_speed_m_s"])))
                overall["grip_quality"].append(float(
                    _scalar(info["grip_quality"])))
                overall["grip_pinch_rms_rad"].append(float(
                    _scalar(info["grip_pinch_rms_rad"])))
                overall["grip_free_rms_rad"].append(float(
                    _scalar(info["grip_free_rms_rad"])))
                overall["action_saturation_fraction"].append(float(
                    _scalar(info["action_saturation_fraction"])))
                overall["joint_limit_max_usage"].append(float(
                    _scalar(info["joint_limit_max_usage"])))
                overall["joint_limit_near_rate"].append(float(
                    _scalar(info["joint_limit_near_rate"])))
                penetration_depth = float(_scalar(
                    info["guitar_penetration_depth"]))
                swept_depth = float(_scalar(
                    info["guitar_swept_penetration_depth"]))
                overall["penetration_depth_m"].append(penetration_depth)
                overall["swept_penetration_depth_m"].append(swept_depth)
                penetration_frames += int(bool(_scalar(
                    info["guitar_penetration"])))
                penetration_terminations += int(bool(_scalar(
                    info["guitar_penetration_termination"])))
                phase_violations += int(bool(_scalar(
                    info["release_phase_violation"])))
                blocked_crossings += int(round(float(_scalar(
                    info["blocked_release_count"]))))
                failure_terminations += int(bool(_scalar(
                    info["failure_termination"])))

                release_indices = torch.nonzero(
                    info["release_mask"][0]).reshape(-1)
                for string_index in release_indices.detach().cpu().tolist():
                    depth = float(_scalar(
                        info["release_depth_m"][0, string_index]))
                    speed = float(_scalar(
                        info["release_across_speed_m_s"][0, string_index]))
                    direction = int(_scalar(
                        info["release_direction"][0, string_index]))
                    release_depths.append(depth)
                    release_speeds.append(abs(speed))
                    release_records.append({
                        "simulation_step": step_index + 1,
                        "string_zero_based": int(string_index),
                        "motor_phase": phase_name,
                        "direction": direction,
                        "depth_m": depth,
                        "across_speed_m_s": speed,
                        "crossing_y_g_m": float(_scalar(
                            info["release_crossing_y"][0, string_index])),
                        "zone_allowed": bool(_scalar(
                            info["release_zone_allowed"][0, string_index])),
                    })

                if phase_name == "RELEASE_RECOVER":
                    recovery_frames += 1
                    tip_x = float(_scalar(info["tip_position_g"][0, 0]))
                    outside = (
                        tip_x < string_x_min - corridor_margin
                        or tip_x > string_x_max + corridor_margin)
                    recovery_outside_string_field += int(outside)
                    recovery_release_count += int(release_indices.numel())
                    if release_indices.numel():
                        directions = info["release_direction"][
                            0, release_indices]
                        recovery_reverse_release_count += int(
                            (directions == DIRECTION_UP).sum().detach().cpu())

                if bool(_scalar(done)):
                    episode_ended = True
                    break

        phase_report = {
            phase: {
                group: {
                    quantity: summarize_samples(values)
                    for quantity, values in quantities.items()
                }
                for group, quantities in phase_groups.items()
            }
            for phase, phase_groups in phase_group_samples.items()
        }
        report = {
            "schema": "tab2body.strike_motion_diagnostics.v1",
            "checkpoint": str(args.checkpoint),
            "checkpoint_contract_sha256": checkpoint[
                "checkpoint_contract"]["sha256"],
            "goal": str(args.goal),
            "stage": stage,
            "timing_tolerance_ms": tolerance,
            "tempo_lambda": tempo_lambda,
            "evaluation_scope": (
                "full_song_original_tempo"
                if env.evaluation_full_song
                else "training_phrase_current_tempo"),
            "simulation_hz": env.SIM_HZ,
            "simulation_steps": simulated,
            "episode_ended": episode_ended,
            "replay_initialization": (
                "deterministic one-environment task reset; checkpoint model "
                "and semantic contract verified"),
            "joint_groups": {
                name: [control_names[index] for index in indices]
                for name, indices in groups.items()
            },
            "overall": {
                name: summarize_samples(values)
                for name, values in overall.items()
            },
            "phase_joint_kinematics": phase_report,
            "release": {
                "count": len(release_records),
                "depth_m": summarize_samples(release_depths),
                "absolute_across_speed_m_s": summarize_samples(
                    release_speeds),
                "phase_violation_count": phase_violations,
                "blocked_wait_rearm_crossing_count": blocked_crossings,
                "records": release_records,
            },
            "recovery": {
                "frame_count": recovery_frames,
                "outside_full_string_field_count":
                    recovery_outside_string_field,
                "outside_full_string_field_fraction": (
                    recovery_outside_string_field / recovery_frames
                    if recovery_frames else None),
                "release_count": recovery_release_count,
                "reverse_release_count": recovery_reverse_release_count,
            },
            "safety": {
                "diagnostic_threshold_m": float(
                    env.penetration_monitor.threshold),
                "termination_enabled": bool(
                    env.penetration_monitor.termination_enabled),
                "penetration_frame_count": penetration_frames,
                "penetration_termination_count": penetration_terminations,
                "failure_termination_count": failure_terminations,
            },
            "decision_status": {
                "pick_angle_and_grip_force": "DEFER_NO_RIGID_PICK",
                "maximum_release_depth": "DIAG_NEEDS_DISTRIBUTION",
                "maximum_release_speed": "DIAG_NEEDS_DISTRIBUTION",
                "joint_group_motion_cost": "DIAG_NEEDS_SUCCESSFUL_POLICY",
                "acceleration_and_jerk": "DIAG_NEEDS_SUCCESSFUL_POLICY",
                "recovery_corridor": "DIAG_NEEDS_SUCCESSFUL_POLICY",
                "guitar_penetration_gate": "DIAG_NEEDS_CALIBRATION",
                "contact_force": "DEFER_NO_PAIR_CONTACT_PHYSICS",
            },
        }
        _write_json_atomic(output, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"report: {output}")
        return report
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
