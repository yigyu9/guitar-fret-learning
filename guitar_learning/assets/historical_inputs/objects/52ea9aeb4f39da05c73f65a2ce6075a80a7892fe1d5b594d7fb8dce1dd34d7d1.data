"""Fail-closed Isaac Gym runtime audit for all eight strike stages."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import isaacgym
import torch

from tab2body.env.config import configured_kwargs
from tab2body.env.tasks import StrikeTask
from tab2body.strike_cfg import STRIKE
from tab2body.strike_contract import (
    A3_TIMED_SINGLE, S2_TIMED_STRUM, S3_SONG_INTEGRATION,
    STRIKE_STAGES as STAGES)


def build_parser():
    parser = argparse.ArgumentParser(
        description="audit strike action/observation/geometry contracts on GPU")
    parser.add_argument("--device", default=STRIKE["device"])
    parser.add_argument("--num-envs", type=int, default=6)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument(
        "--out", type=Path,
        default=PROJECT_ROOT / "docs" / "2026-07-29"
        / "strike_runtime_audit.json")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.num_envs < 6:
        raise ValueError("runtime audit needs at least six envs")
    if args.steps < 1:
        raise ValueError("runtime audit steps must be positive")
    env = StrikeTask(**configured_kwargs(
        StrikeTask,
        STRIKE,
        goal_path=STRIKE["goal_path"],
        grip_reference_path=STRIKE["grip_reference_path"],
        num_envs=args.num_envs,
        device=args.device,
        headless=True,
        seed=STRIKE["seed"],
        reset_noise=0.0,
        random_start=False,
    ))
    try:
        obs = env.reset()
        start, end = env.string_segments_g()
        lane, _normal = env._string_lane_geometry()
        lane_x = lane[0, :, 0]
        adjacent_gap = torch.sort(lane_x).values.diff().abs().min()
        max_across_offset = max(
            env.ready_across, env.entry_across, env.exit_across)
        if max_across_offset >= 0.5 * float(adjacent_gap):
            raise RuntimeError(
                "strike trajectory leaves its inter-string lane")

        report = {
            "schema": "tab2body.strike_runtime_audit.v1",
            "passed": True,
            "num_envs": env.num_envs,
            "num_actions": env.num_actions,
            "num_obs": env.num_obs,
            "value_dim": env.value_dim,
            "controlled_dof_names": list(env.controlled_dof_names),
            "direction_profile": env.direction_profile,
            "collision": env.strike_collision_audit,
            "right_guitar_penetration": {
                "threshold_m": env.penetration_monitor.threshold,
                "frames": env.penetration_monitor.frames,
                "termination_enabled":
                    env.penetration_monitor.termination_enabled,
            },
            "zone": {
                "allowed_y_m": list(env.allowed_y),
                "preferred_y_m": list(env.preferred_y),
                "lane_core_half_width_m": env.lane_core_half_width,
                "lane_allowed_half_width_m":
                    env.lane_allowed_half_width,
            },
            "geometry": {
                "string_start_g_env0": start[0].detach().cpu().tolist(),
                "string_end_g_env0": end[0].detach().cpu().tolist(),
                "minimum_adjacent_gap_m": float(adjacent_gap),
                "maximum_trajectory_across_offset_m":
                    float(max_across_offset),
            },
            "stages": {},
        }
        if obs.shape != (env.num_envs, env.num_obs):
            raise RuntimeError("strike reset observation shape mismatch")
        if not torch.isfinite(obs).all():
            raise RuntimeError("strike reset observation is non-finite")

        for stage in STAGES:
            tolerance = 50.0 if stage == S3_SONG_INTEGRATION else 100.0
            span = 6 if stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION) \
                else 2
            obs = env.set_curriculum_stage(
                stage, tolerance, strum_span=span, reset=True)
            reward_min = float("inf")
            reward_max = float("-inf")
            failure_count = 0
            max_penetration_depth = 0.0
            max_swept_penetration_depth = 0.0
            for _ in range(args.steps):
                obs, reward, _done, info = env.step(
                    env.policy_neutral_action.clone())
                if not torch.isfinite(obs).all():
                    raise RuntimeError(f"{stage}: non-finite observation")
                if not torch.isfinite(reward).all():
                    raise RuntimeError(f"{stage}: non-finite reward")
                reward_min = min(reward_min, float(reward.min()))
                reward_max = max(reward_max, float(reward.max()))
                failure_count += int(
                    info["failure_termination"].sum().item())
                for key in (
                        "guitar_penetration_depth",
                        "guitar_swept_penetration_depth"):
                    if not torch.isfinite(info[key]).all():
                        raise RuntimeError(
                            f"{stage}: non-finite {key}")
                max_penetration_depth = max(
                    max_penetration_depth,
                    float(info["guitar_penetration_depth"].max()))
                max_swept_penetration_depth = max(
                    max_swept_penetration_depth,
                    float(info["guitar_swept_penetration_depth"].max()))
            if failure_count:
                raise RuntimeError(
                    f"{stage}: hold probe caused {failure_count} failures")
            stage_report = {
                "timing_tolerance_ms": env.timing_tolerance_ms,
                "reward_min": reward_min,
                "reward_max": reward_max,
                "target_strings": sorted(set(
                    env._current_target_string().detach().cpu().tolist())),
                "lane_y_min_m": float(env.target_lane_y.min()),
                "lane_y_max_m": float(env.target_lane_y.max()),
                "max_right_guitar_penetration_depth_m":
                    max_penetration_depth,
                "max_right_guitar_swept_penetration_depth_m":
                    max_swept_penetration_depth,
            }
            if stage in (A3_TIMED_SINGLE, S2_TIMED_STRUM):
                target_time = env.practice_target_time_s
                if (float(target_time.min()) < 0.75
                        or float(target_time.max()) > 1.5):
                    raise RuntimeError("A3 practice time left [0.75, 1.5] s")
                stage_report["practice_target_time_min_s"] = float(
                    target_time.min())
                stage_report["practice_target_time_max_s"] = float(
                    target_time.max())
            if stage == S3_SONG_INTEGRATION:
                if (float(env.target_lane_y.min()) < env.preferred_y[0]
                        or float(env.target_lane_y.max()) > env.preferred_y[1]):
                    raise RuntimeError("S3 lane left the preferred strike zone")
            report["stages"][stage] = stage_report

        env.set_curriculum_stage(
            S3_SONG_INTEGRATION, 50.0,
            tempo_lambda=1.0, strum_span=6, reset=False)
        full_obs = env.set_evaluation_mode(full_song=True, reset=True)
        if full_obs is None:
            full_obs = env.reset()
        if not torch.isfinite(full_obs).all():
            raise RuntimeError("S3 full-song reset observation is non-finite")
        first_event_s = float(env.goals.time[0])
        start_s = float(env.song_time_s[0])
        pre_roll_frames = (first_event_s - start_s) * env.SIM_HZ
        if pre_roll_frames + 1e-6 < env.ready_hold_frames:
            raise RuntimeError(
                "S3 full-song pre-roll is shorter than READY hold")
        report["full_song"] = {
            "first_event_time_s": first_event_s,
            "start_time_s": start_s,
            "pre_roll_frames": pre_roll_frames,
            "ready_hold_frames": env.ready_hold_frames,
            "recovery_frames": env.recovery_frames,
            "max_episode_length": env.max_episode_length,
            "timing_sample_capacity": env._timing_capacity,
            "minimum_same_string_restrike_frames":
                env.goals.validation_metadata[
                    "minimum_same_string_restrike_frames"],
            "detector_minimum_restrike_frames":
                env.detector.rearm_min_frames + 1,
        }

        text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.out is not None:
            target = args.out.resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        print(text, end="")
        return report
    finally:
        env.close()


if __name__ == "__main__":
    main()
