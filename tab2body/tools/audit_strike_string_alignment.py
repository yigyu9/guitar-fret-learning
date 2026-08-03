"""Audit target-string versus detected release-string alignment.

The report distinguishes a real policy/detector string error from a visual
target switch during ``RELEASE_RECOVER``.  It replays one deterministic
full-song episode and records only steps with a release, hit, miss, or event
advance.  No physics, checkpoint, or training state is modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PHASE_NAMES = {
    0: "READY",
    1: "APPROACH",
    2: "RELEASE_RECOVER",
}


def parser():
    from tab2body.strike_cfg import STRIKE

    ap = argparse.ArgumentParser(
        description=(
            "replay a strike checkpoint and audit target/release string "
            "alignment"))
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--goal", type=Path, default=Path(STRIKE["goal_path"]))
    ap.add_argument(
        "--grip-reference", type=Path,
        default=Path(STRIKE["grip_reference_path"]))
    ap.add_argument("--device", default=STRIKE["device"])
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    return ap


def _scalar(value):
    return value.detach().reshape(-1)[0].cpu().item()


def _phase(value):
    value = int(value)
    return PHASE_NAMES.get(value, f"UNKNOWN_{value}")


def _default_output(checkpoint):
    checkpoint = Path(checkpoint).resolve()
    if checkpoint.parent.name == "checkpoints":
        return (
            checkpoint.parent.parent / "evaluations"
            / f"{checkpoint.stem}.string_alignment.json")
    return checkpoint.with_name(
        f"{checkpoint.stem}.string_alignment.json")


def main(argv=None):
    args = parser().parse_args(argv)
    if args.max_steps is not None and args.max_steps <= 0:
        raise ValueError("max steps must be positive")
    args.checkpoint = args.checkpoint.resolve()
    args.goal = args.goal.resolve()
    args.grip_reference = args.grip_reference.resolve()
    output = (
        args.out.resolve()
        if args.out is not None else _default_output(args.checkpoint))
    for label, path in (
            ("checkpoint", args.checkpoint),
            ("goal", args.goal),
            ("grip reference", args.grip_reference)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")

    import isaacgym  # noqa: F401
    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic
    from tab2body.strike_cfg import STRIKE
    from tab2body.tools import record_strike_rollout as base
    from tab2body.tools.record_strike_visualized_rollout import (
        construct_evaluation_replay_task,
        restore_evaluation_replay,
    )

    checkpoint = base._load_checkpoint(
        torch, args.checkpoint, args.device)
    stage, tolerance = base.restore_stage_and_tolerance(checkpoint)
    if stage != "A4_ZONE_CONTROL":
        raise ValueError(
            "string-alignment audit requires an A4 checkpoint")

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
        obs = restore_evaluation_replay(env, checkpoint)

        max_steps = (
            int(args.max_steps)
            if args.max_steps is not None
            else max(
                int(STRIKE["artifact_max_steps"]),
                int(env.goals.n_frames) + 60,
            ))
        records = []
        release_offsets = Counter()
        wrong_release_offsets = Counter()
        release_pairs = Counter()
        target_hits = Counter()
        target_misses = Counter()
        target_switches_in_recovery = 0
        simulated = 0
        episode_ended = False

        for step_index in range(max_steps):
            target_before = int(
                _scalar(env._current_target_string())) + 1
            event_before = int(_scalar(env.event_index))
            phase_before = _phase(_scalar(env.motor_phase))
            song_time_before = float(_scalar(env.song_time_s))

            with torch.no_grad():
                action, _log_prob, _value = model.act(
                    obs, deterministic=True)
            obs, _reward, done, info = env.step(action)
            simulated += 1

            releases = [
                int(index) + 1
                for index in torch.nonzero(
                    env._last_release[0]).reshape(-1).cpu().tolist()
            ]
            target_hit = bool(_scalar(info["target_hit"]))
            miss = bool(_scalar(info["miss"]))
            wrong_count = int(round(
                float(_scalar(info["wrong_crossing_count"]))))
            target_after = int(
                _scalar(env._current_target_string())) + 1
            event_after = int(_scalar(env.event_index))
            phase_after = _phase(_scalar(env.motor_phase))

            wrong_releases = list(releases)
            if target_hit and target_before in wrong_releases:
                wrong_releases.remove(target_before)
            for released in releases:
                offset = released - target_before
                release_offsets[offset] += 1
                release_pairs[(target_before, released)] += 1
            for released in wrong_releases:
                wrong_release_offsets[released - target_before] += 1
            if target_hit:
                target_hits[target_before] += 1
            if miss:
                target_misses[target_before] += 1
            if (
                target_after != target_before
                and phase_after == "RELEASE_RECOVER"
            ):
                target_switches_in_recovery += 1

            if (
                releases or target_hit or miss
                or event_after != event_before
            ):
                records.append({
                    "simulation_step": step_index + 1,
                    "song_time_before_s": song_time_before,
                    "event_index_before": event_before,
                    "event_index_after": event_after,
                    "target_string_before": target_before,
                    "target_string_after": target_after,
                    "released_strings": releases,
                    "release_offsets_from_target": [
                        released - target_before
                        for released in releases
                    ],
                    "wrong_released_strings": wrong_releases,
                    "target_hit": target_hit,
                    "miss": miss,
                    "wrong_crossing_count": wrong_count,
                    "phase_before": phase_before,
                    "phase_after": phase_after,
                    "target_switched_during_recovery": (
                        target_after != target_before
                        and phase_after == "RELEASE_RECOVER"
                    ),
                })

            if bool(_scalar(done)):
                episode_ended = True
                break

        summary = {
            "total_release_pulses": int(sum(release_offsets.values())),
            "exact_target_releases": int(release_offsets[0]),
            "release_offset_counts": {
                str(offset): int(count)
                for offset, count in sorted(release_offsets.items())
            },
            "wrong_release_offset_counts": {
                str(offset): int(count)
                for offset, count in sorted(
                    wrong_release_offsets.items())
            },
            "target_release_pairs": [
                {
                    "target_string": target,
                    "released_string": released,
                    "offset": released - target,
                    "count": int(count),
                }
                for (target, released), count in sorted(
                    release_pairs.items())
            ],
            "target_hit_counts": {
                str(string): int(count)
                for string, count in sorted(target_hits.items())
            },
            "target_miss_counts": {
                str(string): int(count)
                for string, count in sorted(target_misses.items())
            },
            "target_switches_during_release_recover":
                target_switches_in_recovery,
        }
        report = {
            "schema": "tab2body.strike_string_alignment_audit.v1",
            "checkpoint": str(args.checkpoint),
            "checkpoint_contract_sha256":
                checkpoint["checkpoint_contract"]["sha256"],
            "goal": str(args.goal),
            "stage": stage,
            "timing_tolerance_ms": tolerance,
            "string_conventions": {
                "input_fingering":
                    "0=low-E, 5=high-e",
                "runtime_zero_based":
                    "0=high-e, 5=low-E",
                "report_one_based":
                    "1=high-e, 6=low-E",
            },
            "simulation_steps": simulated,
            "replay_initialization": "checkpoint environment_state restored",
            "episode_ended": episode_ended,
            "summary": summary,
            "records": records,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"report: {output}")
        return report
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
