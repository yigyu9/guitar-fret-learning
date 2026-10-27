from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re

from .run_layout import (
    RunLayout,
    default_strike_full_song_video_paths,
    default_strike_video_paths,
)


_STRIKE_CHECKPOINT = re.compile(r"^strike_(\d+)$")
_STRIKE_FULL_SONG_REPORT_SCHEMAS = frozenset((
    "tab2body.strike_full_song_rollout.v1",
    "tab2body.strike_full_song_rollout.v2",
))
STRIKE_PAIRED_PRACTICE_STAGES = frozenset((
    "S0_TWO_STRING_STRUM",
    "S1_STRUM_SPAN",
    "S2_TIMED_STRUM",
))
STRIKE_PRACTICE_DIRECTIONS = ("down", "up")
STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA = (
    "tab2body.strike_practice_direction_rollout.v1")


def strike_checkpoint_iteration(checkpoint) -> int:
    checkpoint = Path(checkpoint)
    match = _STRIKE_CHECKPOINT.fullmatch(checkpoint.stem)
    if match is None:
        raise ValueError(
            f"strike checkpoint name must be strike_<iteration>.pt: {checkpoint}")
    return int(match.group(1))


def strike_rollout_artifact_paths(checkpoint) -> dict[str, Path]:
    checkpoint = Path(checkpoint).resolve()
    videos = default_strike_video_paths(checkpoint)
    return {
        **videos,
        "report": videos["remembered"].with_name(
            f"{checkpoint.stem}_rollout.json"),
    }


def strike_rollout_is_complete(checkpoint) -> bool:
    return all(
        path.is_file() and path.stat().st_size > 0
        for path in strike_rollout_artifact_paths(checkpoint).values()
    )


def strike_paired_rollout_artifact_paths(
        checkpoint) -> dict[str, dict[str, Path]]:
    """Return additive down/up diagnostic paths for one S0--S2 checkpoint."""
    checkpoint = Path(checkpoint).resolve()
    run_root = checkpoint.parent.parent
    videos = run_root / "videos"
    return {
        direction: {
            "remembered": videos / (
                f"{checkpoint.stem}_rollout_{direction}_remembered.mp4"),
            "current": videos / (
                f"{checkpoint.stem}_rollout_{direction}_current.mp4"),
            "report": videos / (
                f"{checkpoint.stem}_rollout_{direction}.json"),
        }
        for direction in STRIKE_PRACTICE_DIRECTIONS
    }


def _strike_practice_direction_report_is_complete(
        report_path, expected_direction) -> bool:
    try:
        import json

        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return bool(
        isinstance(report, dict)
        and report.get("schema") == STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA
        and report.get("curriculum_stage") in STRIKE_PAIRED_PRACTICE_STAGES
        and report.get("requested_practice_direction") == expected_direction
        and report.get("practice_direction") == expected_direction
        and report.get("paired_practice_diagnostic") is True
        and report.get("training_runtime_restored_after_pair") is True
        and report.get("training_rng_restored_before_reset") is True)


def strike_paired_rollout_is_complete(checkpoint) -> bool:
    """Require two cameras and an actual-direction report for both directions."""
    pairs = strike_paired_rollout_artifact_paths(checkpoint)
    for direction, paths in pairs.items():
        if not all(
                path.is_file() and path.stat().st_size > 0
                for path in paths.values()):
            return False
        if not _strike_practice_direction_report_is_complete(
                paths["report"], direction):
            return False
    return True


def strike_periodic_rollout_is_complete(checkpoint) -> bool:
    """Accept the legacy single episode or the S0--S2 direction pair."""
    return bool(
        strike_rollout_is_complete(checkpoint)
        or strike_paired_rollout_is_complete(checkpoint))


def build_strike_practice_direction_report(
        *, direction, curriculum_stage, capture, metadata=None):
    """Build and validate one member of a paired S0--S2 diagnostic report."""
    direction = str(direction)
    stage = str(curriculum_stage)
    if direction not in STRIKE_PRACTICE_DIRECTIONS:
        raise ValueError("practice direction must be 'down' or 'up'")
    if stage not in STRIKE_PAIRED_PRACTICE_STAGES:
        raise ValueError("paired practice diagnostics require an S0--S2 stage")
    if not isinstance(capture, dict):
        raise TypeError("practice direction capture must be a mapping")
    actual = capture.get("practice_direction")
    if actual != direction:
        raise ValueError(
            "practice direction capture mismatch: "
            f"requested={direction!r}, actual={actual!r}")
    if (capture.get("paired_practice_diagnostic") is not True
            or capture.get("training_runtime_restored_after_pair") is not True
            or capture.get("training_rng_restored_before_reset") is not True):
        raise ValueError(
            "practice direction report requires a completed, runtime-restored "
            "paired capture")
    report = {
        "schema": STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA,
        "curriculum_stage": stage,
        "requested_practice_direction": direction,
        "practice_direction": actual,
        "paired_practice_diagnostic": True,
        "training_runtime_restored_after_pair": True,
        "training_rng_restored_before_reset": True,
        **({} if metadata is None else dict(metadata)),
        **capture,
    }
    report.update({
        "schema": STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA,
        "curriculum_stage": stage,
        "requested_practice_direction": direction,
        "practice_direction": actual,
        "paired_practice_diagnostic": True,
        "training_runtime_restored_after_pair": True,
        "training_rng_restored_before_reset": True,
    })
    return report


def strike_full_song_rollout_artifact_paths(checkpoint) -> dict[str, Path]:
    checkpoint = Path(checkpoint).resolve()
    videos = default_strike_full_song_video_paths(checkpoint)
    return {
        **videos,
        "report": videos["remembered"].with_name(
            f"{checkpoint.stem}_full_song.json"),
    }


def strike_full_song_rollout_is_complete(checkpoint) -> bool:
    paths = strike_full_song_rollout_artifact_paths(checkpoint)
    if not all(
            path.is_file() and path.stat().st_size > 0
            for path in paths.values()):
        return False
    try:
        import json

        report = json.loads(paths["report"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    if not isinstance(report, dict):
        return False
    schema = report.get("schema")
    if schema not in _STRIKE_FULL_SONG_REPORT_SCHEMAS:
        return False
    if not (
            report.get("evaluation_scope") == "full_song_original_tempo"
            and report.get("captured_original_song_duration") is True
            and report.get("stitched_after_episode_reset") is False):
        return False
    if schema == "tab2body.strike_full_song_rollout.v1":
        return True
    if not (
            report.get("completed_full_timeline") is True
            and report.get("ended_before_original_song_end") is False):
        return False
    raw_steps = report.get("steps_simulated")
    raw_minimum_steps = report.get("minimum_original_song_steps")
    if isinstance(raw_steps, bool) or isinstance(raw_minimum_steps, bool):
        return False
    try:
        steps = int(raw_steps)
        minimum_steps = int(raw_minimum_steps)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return minimum_steps > 0 and steps >= minimum_steps


def strike_full_song_capture_contract(env) -> dict[str, float | int]:
    if str(env.curriculum_stage) != "S3_SONG_INTEGRATION":
        raise ValueError("full-song capture requires S3_SONG_INTEGRATION")
    first_time_s = float(env.goals.time[0].item())
    final_time_s = float(env.goals.time[-1].item())
    start_time_s = float(env.full_song_start_time_s)
    simulation_hz = int(env.SIM_HZ)
    minimum_steps = int(math.ceil(
        (final_time_s - start_time_s) * simulation_hz)) + 1
    return {
        "goal_event_count": int(env.goals.num_events),
        "goal_first_event_time_s": first_time_s,
        "goal_final_event_time_s": final_time_s,
        "original_song_duration_s": final_time_s - first_time_s,
        "evaluation_start_time_s": start_time_s,
        "minimum_original_song_steps": minimum_steps,
        "capture_step_limit": int(env.max_episode_length),
        "capture_duration_limit_s": (
            int(env.max_episode_length) / simulation_hz),
    }


def strike_full_song_capture_summary(contract, capture) -> dict[str, object]:
    steps = int(capture["steps_simulated"])
    minimum_steps = int(contract["minimum_original_song_steps"])
    episode_end = capture.get("episode_end", {})
    captured_duration = steps >= minimum_steps
    return {
        **contract,
        "captured_original_song_duration": captured_duration,
        "completed_full_timeline": bool(
            episode_end.get("goal_finished", False)),
        "ended_before_original_song_end": bool(
            capture.get("episode_ended", False) and not captured_duration),
    }


def strike_full_song_quality_key(report) -> tuple[float, ...]:
    if not isinstance(report, dict):
        raise TypeError("full-song quality report must be a mapping")
    if report.get("schema") != "tab2body.strike_full_song_rollout.v2":
        raise ValueError("full-song quality ranking requires report schema v2")
    summary = report.get("event_trace_summary")
    episode_end = report.get("episode_end")
    grip = report.get("grip_preservation")
    if not all(isinstance(value, dict)
               for value in (summary, episode_end, grip)):
        raise ValueError(
            "full-song quality ranking requires trace, safety and grip summaries")
    names = (
        "traversal_f1", "event_completion_rate", "strum_completion_rate",
        "blocked_crossing_count", "wrong_crossing_count",
    )
    try:
        values = tuple(float(summary[name]) for name in names)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("full-song quality metrics are missing or invalid") from exc
    if not all(math.isfinite(value) for value in values):
        raise ValueError("full-song quality metrics must be finite")
    traversal_f1, event_completion, strum_completion, blocked, wrong = values
    raw_timing = summary.get("timing_abs_p95_ms")
    if raw_timing is None:
        timing_available = 0.0
        timing = 0.0
    else:
        try:
            timing = float(raw_timing)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "full-song timing metric is invalid") from exc
        timing_available = 1.0
    if (not 0.0 <= traversal_f1 <= 1.0
            or not 0.0 <= event_completion <= 1.0
            or not 0.0 <= strum_completion <= 1.0
            or blocked < 0.0 or wrong < 0.0
            or not math.isfinite(timing) or timing < 0.0):
        raise ValueError("full-song quality metrics are outside valid ranges")
    safety_passed = not bool(episode_end.get(
        "irrecoverable_safety_failure", True))
    return (
        float(safety_passed),
        float(grip.get("passed") is True),
        traversal_f1,
        event_completion,
        strum_completion,
        -blocked,
        -wrong,
        timing_available,
        -timing,
    )


def strike_full_song_is_better(candidate, incumbent) -> bool:
    return strike_full_song_quality_key(candidate) > (
        strike_full_song_quality_key(incumbent))


def completed_strike_rollout_iterations(layout: RunLayout) -> tuple[int, ...]:
    checkpoint_stems = set()
    patterns = (
        ("strike_*_rollout_remembered.mp4", "_rollout_remembered.mp4"),
        ("strike_*_rollout_down_remembered.mp4",
         "_rollout_down_remembered.mp4"),
    )
    for pattern, suffix in patterns:
        for remembered in layout.videos.glob(pattern):
            checkpoint_stems.add(remembered.name[:-len(suffix)])
    completed = []
    for stem in checkpoint_stems:
        checkpoint = layout.checkpoints / f"{stem}.pt"
        try:
            iteration = strike_checkpoint_iteration(checkpoint)
        except ValueError:
            continue
        if strike_periodic_rollout_is_complete(checkpoint):
            completed.append(iteration)
    return tuple(sorted(set(completed)))


@dataclass
class PeriodicCheckpointVideoSchedule:
    minimum_gap_iterations: int
    last_completed_iteration: int = 0

    def __post_init__(self):
        if (isinstance(self.minimum_gap_iterations, bool)
                or int(self.minimum_gap_iterations) < 1):
            raise ValueError("minimum video gap must be a positive integer")
        if (isinstance(self.last_completed_iteration, bool)
                or int(self.last_completed_iteration) < 0):
            raise ValueError(
                "last completed video iteration must be a non-negative integer")
        self.minimum_gap_iterations = int(self.minimum_gap_iterations)
        self.last_completed_iteration = int(self.last_completed_iteration)

    @classmethod
    def from_layout(cls, layout, minimum_gap_iterations):
        completed = completed_strike_rollout_iterations(layout)
        return cls(
            minimum_gap_iterations=int(minimum_gap_iterations),
            last_completed_iteration=max(completed, default=0),
        )

    def is_due(self, checkpoint) -> bool:
        checkpoint = Path(checkpoint)
        if not checkpoint.is_file():
            return False
        iteration = strike_checkpoint_iteration(checkpoint)
        if strike_periodic_rollout_is_complete(checkpoint):
            self.mark_completed(iteration)
            return False
        return (
            iteration - self.last_completed_iteration
            >= self.minimum_gap_iterations
        )

    def mark_completed(self, iteration) -> None:
        iteration = int(iteration)
        if iteration < self.last_completed_iteration:
            raise ValueError(
                "completed video iteration cannot move backwards")
        self.last_completed_iteration = iteration


__all__ = [
    "PeriodicCheckpointVideoSchedule",
    "STRIKE_PAIRED_PRACTICE_STAGES",
    "STRIKE_PRACTICE_DIRECTIONS",
    "STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA",
    "build_strike_practice_direction_report",
    "completed_strike_rollout_iterations",
    "strike_full_song_capture_contract",
    "strike_full_song_capture_summary",
    "strike_full_song_is_better",
    "strike_full_song_quality_key",
    "strike_checkpoint_iteration",
    "strike_full_song_rollout_artifact_paths",
    "strike_full_song_rollout_is_complete",
    "strike_rollout_artifact_paths",
    "strike_rollout_is_complete",
    "strike_paired_rollout_artifact_paths",
    "strike_paired_rollout_is_complete",
    "strike_periodic_rollout_is_complete",
]
