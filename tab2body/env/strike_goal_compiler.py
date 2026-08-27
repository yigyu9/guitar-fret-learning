from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence, Tuple


GESTURE_SINGLE_PICK = "single_pick"
GESTURE_STRUM = "strum"
GESTURE_ALTERNATE_RESTRIKE = "alternate_restrike"
DIRECTION_DOWN = 1
DIRECTION_UP = -1


@dataclass(frozen=True)
class CompiledStrikeEvent:
    time_s: float
    frame: int
    gesture: str
    direction: int
    audible_strings: Tuple[int, ...]
    traversal_strings: Tuple[int, ...]
    protected_strings: Tuple[int, ...]
    source_event_ids: Tuple[Any, ...]


@dataclass(frozen=True)
class CompiledStrikeGoal:
    events: Tuple[CompiledStrikeEvent, ...]
    original_times_s: Tuple[float, ...]
    easy_times_s: Tuple[float, ...]
    physical_min_gap_s: float
    matching_gap_s: float
    window_fraction: float

    def runtime_times(self, tempo_lambda: float) -> Tuple[float, ...]:
        value = _unit_interval("tempo_lambda", tempo_lambda)
        return tuple(
            original + (1.0 - value) * (easy - original)
            for original, easy in zip(
                self.original_times_s, self.easy_times_s))

    def event_windows(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
        tolerance = _positive_finite(
            "timing_tolerance_ms", timing_tolerance_ms) / 1000.0
        times = self.runtime_times(tempo_lambda)
        left = []
        right = []
        for index in range(len(times)):
            previous_gap = None if index == 0 else times[index] - times[index - 1]
            next_gap = None if index + 1 == len(times) else times[index + 1] - times[index]
            left.append(tolerance if previous_gap is None else min(
                tolerance, self.window_fraction * previous_gap))
            right.append(tolerance if next_gap is None else min(
                tolerance, self.window_fraction * next_gap))
        return tuple(left), tuple(right)

    def gap_diagnostics(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> Mapping[str, float | int | None]:
        times = self.runtime_times(tempo_lambda)
        original_gaps = [
            later - earlier for earlier, later in zip(
                self.original_times_s, self.original_times_s[1:])]
        effective_gaps = [
            later - earlier for earlier, later in zip(times, times[1:])]
        left, right = self.event_windows(
            tempo_lambda, timing_tolerance_ms)
        overlap_count = sum(
            times[index] + right[index]
            >= times[index + 1] - left[index + 1]
            for index in range(len(times) - 1))
        expansions = [
            easy - original for easy, original in zip(
                self.easy_times_s, self.original_times_s)]
        return {
            "minimum_original_gap_s": (
                min(original_gaps) if original_gaps else None),
            "minimum_effective_gap_s": (
                min(effective_gaps) if effective_gaps else None),
            "maximum_cumulative_expansion_s": max(expansions, default=0.0),
            "required_matching_gap_s": self.matching_gap_s,
            "physical_min_gap_s": self.physical_min_gap_s,
            "overlap_window_count": int(overlap_count),
        }

    @property
    def unsupported_events(self) -> Tuple[CompiledStrikeEvent, ...]:
        return tuple(
            event for event in self.events
            if event.gesture == GESTURE_ALTERNATE_RESTRIKE)


def _positive_finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite and positive")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _unit_interval(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite and in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return result


def _source_event_id(event: Mapping[str, Any], index: int) -> Any:
    return event.get("event_id", index)


def _compile_cluster(
        cluster: Sequence[Mapping[str, Any]],
        source_indices: Sequence[int]) -> CompiledStrikeEvent:
    strings = tuple(int(event["string"]) for event in cluster)
    unique = tuple(dict.fromkeys(strings))
    source_ids = tuple(
        _source_event_id(event, index)
        for event, index in zip(cluster, source_indices))
    if len(cluster) == 1:
        gesture = GESTURE_SINGLE_PICK
        traversal = unique
    elif len(unique) == len(strings):
        gesture = GESTURE_STRUM
        low = min(unique)
        high = max(unique)
        traversal = tuple(range(high, low - 1, -1))
    else:
        gesture = GESTURE_ALTERNATE_RESTRIKE
        traversal = unique
    protected = tuple(
        string_index for string_index in traversal
        if string_index not in unique)
    return CompiledStrikeEvent(
        time_s=float(cluster[0]["time"]),
        frame=int(cluster[0]["frame"]),
        gesture=gesture,
        direction=DIRECTION_DOWN,
        audible_strings=unique,
        traversal_strings=traversal,
        protected_strings=protected,
        source_event_ids=source_ids,
    )


def compile_strike_events(
        events: Sequence[Mapping[str, Any]], *, fps: int,
        rearm_min_frames: int, follow_through_min_frames: int,
        initial_timing_tolerance_ms: float,
        window_fraction: float = 0.45) -> CompiledStrikeGoal:
    if not events:
        raise ValueError("strike compiler requires at least one event")
    if isinstance(fps, bool) or not isinstance(fps, int) or fps < 1:
        raise ValueError("fps must be a positive integer")
    for name, value in (
            ("rearm_min_frames", rearm_min_frames),
            ("follow_through_min_frames", follow_through_min_frames)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    fraction = _unit_interval("window_fraction", window_fraction)
    if fraction <= 0.0 or fraction >= 0.5:
        raise ValueError("window_fraction must be in (0, 0.5)")
    tolerance_s = _positive_finite(
        "initial_timing_tolerance_ms",
        initial_timing_tolerance_ms) / 1000.0
    physical_min_gap_s = (
        max(rearm_min_frames, follow_through_min_frames) + 1) / float(fps)
    matching_gap_s = tolerance_s / fraction
    clusters = []
    source_indices = []
    current = [events[0]]
    current_indices = [0]
    for index, event in enumerate(events[1:], start=1):
        gap_s = float(event["time"]) - float(current[-1]["time"])
        if gap_s < physical_min_gap_s - 1e-12:
            current.append(event)
            current_indices.append(index)
        else:
            clusters.append(tuple(current))
            source_indices.append(tuple(current_indices))
            current = [event]
            current_indices = [index]
    clusters.append(tuple(current))
    source_indices.append(tuple(current_indices))
    compiled_events = tuple(
        _compile_cluster(cluster, indices)
        for cluster, indices in zip(clusters, source_indices))
    original_times = tuple(event.time_s for event in compiled_events)
    easy_times = [original_times[0]]
    for previous, current_time in zip(original_times, original_times[1:]):
        original_gap = current_time - previous
        easy_times.append(
            easy_times[-1] + max(
                original_gap, physical_min_gap_s, matching_gap_s))
    return CompiledStrikeGoal(
        events=compiled_events,
        original_times_s=original_times,
        easy_times_s=tuple(easy_times),
        physical_min_gap_s=physical_min_gap_s,
        matching_gap_s=matching_gap_s,
        window_fraction=fraction,
    )
