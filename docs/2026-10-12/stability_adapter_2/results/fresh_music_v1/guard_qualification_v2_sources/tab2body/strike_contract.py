"""Pure shared names for the pick-only strike acquisition contract."""
from __future__ import annotations

import math


A0_PICK_GRIP = "A0_PICK_GRIP"
A1_TIP_READY = "A1_TIP_READY"
A2_SINGLE_CROSSING = "A2_SINGLE_CROSSING"
A3_TIMED_SINGLE = "A3_TIMED_SINGLE"
A4_STRUM_CONTEXT_RECOVERY = "A4_STRUM_CONTEXT_RECOVERY"
S0_TWO_STRING_STRUM = "S0_TWO_STRING_STRUM"
S1_STRUM_SPAN = "S1_STRUM_SPAN"
S2_TIMED_STRUM = "S2_TIMED_STRUM"
S3_SONG_INTEGRATION = "S3_SONG_INTEGRATION"

STRIKE_STAGES = (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    A4_STRUM_CONTEXT_RECOVERY,
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
)

# A song without a strum must not be forced through synthetic strum stages.
# The shared pick acquisition stages still lead into the same song-integration
# stage, where the plan's actual gestures remain authoritative.
PICK_ONLY_STRIKE_STAGES = (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    S3_SONG_INTEGRATION,
)


def strike_curriculum_stages(song_has_strum):
    """Return the deterministic stage route for one compiled song plan."""
    if not isinstance(song_has_strum, bool):
        raise TypeError("song_has_strum must be bool")
    return STRIKE_STAGES if song_has_strum else PICK_ONLY_STRIKE_STAGES

SINGLE_PRACTICE_STAGES = (
    A0_PICK_GRIP, A1_TIP_READY, A2_SINGLE_CROSSING, A3_TIMED_SINGLE)
STRUM_STAGES = (
    A4_STRUM_CONTEXT_RECOVERY, S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN, S2_TIMED_STRUM,
    S3_SONG_INTEGRATION)
STRUM_ONLY_STAGES = (
    A4_STRUM_CONTEXT_RECOVERY, S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN, S2_TIMED_STRUM)
PRACTICE_DIRECTION_STAGES = SINGLE_PRACTICE_STAGES + STRUM_ONLY_STAGES
STRUM_MICROTIMING_STAGES = (S2_TIMED_STRUM, S3_SONG_INTEGRATION)
TIMED_STAGES = (A3_TIMED_SINGLE, S2_TIMED_STRUM, S3_SONG_INTEGRATION)
ZONE_STAGES = (A3_TIMED_SINGLE, S2_TIMED_STRUM, S3_SONG_INTEGRATION)
SONG_TIMELINE_STAGES = (S3_SONG_INTEGRATION,)

TERMINAL_EVIDENCE_STAGES = STRIKE_STAGES

TIMED_PRACTICE_MIN_TIME_S = 0.75
TIMED_PRACTICE_MAX_TIME_S = 1.50


def minimum_strike_stage_horizon(
        stage,
        event_times_s,
        *,
        sim_hz,
        ready_hold_frames,
        recovery_frames,
        rearm_min_frames,
        timed_lead_frames,
        song_events_per_episode,
        timing_tolerance_ms=None):
    """Return the minimum frames that can finish one legal stage episode."""
    if stage not in STRIKE_STAGES:
        raise ValueError(f"unknown strike stage: {stage!r}")
    integer_values = {
        "sim_hz": sim_hz,
        "ready_hold_frames": ready_hold_frames,
        "recovery_frames": recovery_frames,
        "rearm_min_frames": rearm_min_frames,
        "timed_lead_frames": timed_lead_frames,
        "song_events_per_episode": song_events_per_episode,
    }
    for name, value in integer_values.items():
        minimum = 0 if name == "timed_lead_frames" else 1
        if (isinstance(value, bool) or not isinstance(value, int)
                or value < minimum):
            raise ValueError(f"{name} must be an integer >= {minimum}")
    times = tuple(float(value) for value in event_times_s)
    if (not times
            or not all(math.isfinite(value) and value >= 0.0 for value in times)
            or any(later <= earlier
                   for earlier, later in zip(times, times[1:]))):
        raise ValueError(
            "event_times_s must be finite, non-negative and increasing")
    recovery_tail = max(recovery_frames, rearm_min_frames)
    if stage == A0_PICK_GRIP:
        return 1
    if stage == A1_TIP_READY:
        return ready_hold_frames
    if stage in (
            A2_SINGLE_CROSSING, A4_STRUM_CONTEXT_RECOVERY,
            S0_TWO_STRING_STRUM, S1_STRUM_SPAN):
        return ready_hold_frames + 1 + recovery_tail
    if (isinstance(timing_tolerance_ms, bool)
            or timing_tolerance_ms is None
            or not math.isfinite(float(timing_tolerance_ms))
            or float(timing_tolerance_ms) <= 0.0):
        raise ValueError(
            "timed stage needs finite positive timing_tolerance_ms")
    tolerance_frames = int(math.ceil(
        float(timing_tolerance_ms) / 1000.0 * sim_hz))
    if stage in (A3_TIMED_SINGLE, S2_TIMED_STRUM):
        return (
            int(math.ceil(TIMED_PRACTICE_MAX_TIME_S * sim_hz))
            + tolerance_frames + recovery_tail)
    quota = min(song_events_per_episode, len(times))
    maximum_span_s = max(
        times[index + quota - 1] - times[index]
        for index in range(len(times) - quota + 1))
    return (
        timed_lead_frames
        + int(math.ceil(maximum_span_s * sim_hz))
        + tolerance_frames + recovery_tail)


__all__ = [
    "A0_PICK_GRIP",
    "A1_TIP_READY",
    "A2_SINGLE_CROSSING",
    "A3_TIMED_SINGLE",
    "A4_STRUM_CONTEXT_RECOVERY",
    "S0_TWO_STRING_STRUM",
    "S1_STRUM_SPAN",
    "S2_TIMED_STRUM",
    "S3_SONG_INTEGRATION",
    "SINGLE_PRACTICE_STAGES",
    "STRUM_STAGES",
    "STRUM_ONLY_STAGES",
    "PRACTICE_DIRECTION_STAGES",
    "STRUM_MICROTIMING_STAGES",
    "TIMED_STAGES",
    "ZONE_STAGES",
    "SONG_TIMELINE_STAGES",
    "STRIKE_STAGES",
    "PICK_ONLY_STRIKE_STAGES",
    "strike_curriculum_stages",
    "TERMINAL_EVIDENCE_STAGES",
    "TIMED_PRACTICE_MAX_TIME_S",
    "TIMED_PRACTICE_MIN_TIME_S",
    "minimum_strike_stage_horizon",
]
