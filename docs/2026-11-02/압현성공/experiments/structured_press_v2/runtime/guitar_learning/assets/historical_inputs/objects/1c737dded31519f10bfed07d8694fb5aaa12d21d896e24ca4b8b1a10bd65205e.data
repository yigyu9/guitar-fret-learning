"""Offline strike-plan generation using the shared runtime plan contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence, Tuple

from guitar_learning.score.strike_goal_compiler import (
    CompiledStrikeEvent, CompiledStrikeGoal, DIRECTION_DOWN, DIRECTION_NAMES,
    DIRECTION_UP, GESTURE_ALTERNATE_RESTRIKE, GESTURE_SINGLE_PICK, GESTURE_STRUM,
    STRIKE_DIRECTION_PROFILE, STRIKE_PLAN_SCHEMA, STRIKE_TRANSITION_PROFILE,
    STRIKE_TRANSITION_PROFILE_V1, ReviewedStrikeOverride,
    StrikeDirectionPlannerConfig, StrikeTransitionDiagnostic,
    _crossed_string_centers, _entry_side_coordinate, _exit_side_coordinate,
    _positive_finite, _source_event_id, _transition_diagnostic, _unit_interval,
    compiled_strike_goal_from_plan_document, normalize_reviewed_strike_overrides,
)


@dataclass(frozen=True)
class _StrikeGroup:
    time_s: float
    frame: int
    gesture: str
    audible_strings: Tuple[int, ...]
    low_string: int
    high_string: int
    source_event_ids: Tuple[Any, ...]
    order_direction: int
    order_confidence: float
    source_times_s: Tuple[float, ...]
    input_times_s: Tuple[float, ...]
    source_reference_times_s: Tuple[float, ...]
    time_uncertainties_s: Tuple[float, ...]
    source_refs: Tuple[Any, ...]



def _review_grouping_controls(events, reviewed_overrides):
    event_ids = tuple(_source_event_id(event, index)
                      for index, event in enumerate(events))
    event_index = {value: index for index, value in enumerate(event_ids)}
    force_merge_boundaries = set()
    force_split_boundaries = set()
    resolved_times = {}
    for override in reviewed_overrides:
        indices = tuple(event_index[value] for value in override.source_event_ids)
        internal_boundaries = set(indices[1:])
        if override.action == "merge":
            force_merge_boundaries.update(internal_boundaries)
            if indices[0] > 0:
                force_split_boundaries.add(indices[0])
            if indices[-1] + 1 < len(events):
                force_split_boundaries.add(indices[-1] + 1)
            resolved_times.update(zip(indices, override.resolved_times_s))
        else:
            force_split_boundaries.update(internal_boundaries)
    conflict = force_merge_boundaries.intersection(force_split_boundaries)
    if conflict:
        raise ValueError(
            "reviewed overrides contain conflicting merge/separate boundaries")
    effective_events = []
    for index, event in enumerate(events):
        copied = dict(event)
        copied["_input_time"] = float(event["time"])
        if index in resolved_times:
            copied["time"] = resolved_times[index]
        effective_events.append(copied)
    effective_times = tuple(float(event["time"]) for event in effective_events)
    if any(not math.isfinite(value) or value < 0.0 for value in effective_times):
        raise ValueError("reviewed override produced invalid event times")
    if any(b < a for a, b in zip(effective_times, effective_times[1:])):
        raise ValueError(
            "reviewed override resolved times break global timeline order")
    return (
        tuple(effective_events), force_merge_boundaries,
        force_split_boundaries)



def _group_cluster(cluster, source_indices, physical_min_gap_s, fps, config):
    strings = tuple(int(event["string"]) for event in cluster)
    unique = tuple(dict.fromkeys(strings))
    if len(cluster) == 1:
        gesture = GESTURE_SINGLE_PICK
    elif len(unique) == len(strings):
        gesture = GESTURE_STRUM
    else:
        gesture = GESTURE_ALTERNATE_RESTRIKE
    source_ids = tuple(_source_event_id(event, index)
                       for event, index in zip(cluster, source_indices))
    pair_score = 0
    informative = 0
    for left, right in zip(cluster, cluster[1:]):
        dt = float(right["time"]) - float(left["time"])
        ds = int(right["string"]) - int(left["string"])
        if dt >= config.order_evidence_min_s - 1e-12 and ds:
            informative += 1
            pair_score += -1 if ds < 0 else 1
    onset_span = float(cluster[-1]["time"]) - float(cluster[0]["time"])
    if informative and pair_score:
        order_direction = DIRECTION_DOWN if pair_score < 0 else DIRECTION_UP
        order_confidence = (
            abs(pair_score) / informative
            * min(1.0, onset_span / max(physical_min_gap_s, 1e-9)))
    else:
        order_direction = 0
        order_confidence = 0.0
    return _StrikeGroup(
        time_s=sum(float(event["time"]) for event in cluster) / len(cluster),
        frame=int(math.floor(
            (sum(float(event["time"]) for event in cluster) / len(cluster))
            * float(fps) + 0.5)),
        gesture=gesture,
        audible_strings=unique,
        low_string=min(unique),
        high_string=max(unique),
        source_event_ids=source_ids,
        order_direction=order_direction,
        order_confidence=float(order_confidence),
        source_times_s=tuple(float(event["time"]) for event in cluster),
        input_times_s=tuple(float(event["_input_time"]) for event in cluster),
        source_reference_times_s=tuple(
            float(event.get("source_time", event["_input_time"]))
            for event in cluster),
        time_uncertainties_s=tuple(
            float(event.get("time_uncertainty_s", 0.0)) for event in cluster),
        source_refs=tuple(event.get("source_ref") for event in cluster),
    )



def _microtiming(group, direction, traversal, config):
    if len(traversal) <= 1:
        return (0.0,), 0.0, 0.0
    rank = {string_index: index for index, string_index in enumerate(traversal)}
    samples = [
        (rank[string_index], time_s - group.time_s)
        for string_index, time_s in zip(
            group.audible_strings, group.source_times_s)
        if string_index in rank]
    mean_rank = sum(item[0] for item in samples) / len(samples)
    mean_time = sum(item[1] for item in samples) / len(samples)
    variance = sum((item[0] - mean_rank) ** 2 for item in samples)
    slope = (
        sum((item[0] - mean_rank) * (item[1] - mean_time)
            for item in samples) / variance
        if variance > 1e-12 else 0.0)
    if slope <= 0.0:
        interval = config.default_string_interval_s
    else:
        interval = min(
            config.maximum_string_interval_s,
            max(config.minimum_string_interval_s, slope))
    duration = min(
        config.grouping_max_span_s,
        interval * (len(traversal) - 1))
    interval = duration / (len(traversal) - 1)
    midpoint = (len(traversal) - 1) / 2.0
    offsets = tuple((index - midpoint) * interval
                    for index in range(len(traversal)))
    residuals = [
        time_offset - offsets[string_rank]
        for string_rank, time_offset in samples]
    rms = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    return offsets, duration, rms



def _traversal(group: _StrikeGroup, direction: int) -> Tuple[int, ...]:
    if group.gesture == GESTURE_SINGLE_PICK:
        return group.audible_strings
    if direction == DIRECTION_DOWN:
        return tuple(range(group.high_string, group.low_string - 1, -1))
    return tuple(range(group.low_string, group.high_string + 1))



def _emission_cost(group, direction, config):
    cost = config.upstroke_prior_cost if direction == DIRECTION_UP else 0.0
    if group.order_direction and direction != group.order_direction:
        cost += config.onset_order_mismatch_cost * group.order_confidence
    return cost



def _transition_cost(
        previous, previous_direction, current, direction, config,
        physical_min_gap_s):
    previous_path = _traversal(previous, previous_direction)
    current_path = _traversal(current, direction)
    previous_offsets, _, _ = _microtiming(
        previous, previous_direction, previous_path, config)
    current_offsets, _, _ = _microtiming(
        current, direction, current_path, config)
    edge_gap = max(
        0.0,
        current.time_s + current_offsets[0]
        - previous.time_s - previous_offsets[-1])
    urgency = max(0.0, 1.0 - edge_gap / config.recovery_horizon_s)
    clearance_urgency = max(
        0.0, 1.0 - edge_gap / max(physical_min_gap_s, 1e-9))
    endpoint_distance = abs(previous_path[-1] - current_path[0]) / 5.0
    cost = config.endpoint_travel_cost * endpoint_distance * (0.25 + urgency)
    exit_position = _exit_side_coordinate(
        previous_path[-1], previous_direction)
    entry_position = _entry_side_coordinate(current_path[0], direction)
    crossed_strings = _crossed_string_centers(exit_position, entry_position)
    same_string_restrike = previous_path[-1] == current_path[0]
    if crossed_strings:
        crossing_fraction = len(crossed_strings) / 5.0
        cost += config.path_crossing_cost * (
            0.5 + urgency + crossing_fraction)
        cost += config.clearance_urgency_cost * clearance_urgency
    if direction == previous_direction:
        if crossed_strings or same_string_restrike:
            reset_span = (len(previous_path) + len(current_path) - 2) / 10.0
            cost += (
                config.same_direction_recovery_cost
                * urgency * (0.5 + reset_span))
    else:
        cost += config.reversal_cost * (1.0 - urgency)
    return cost



def _plan_directions(groups, config, physical_min_gap_s):
    directions = (DIRECTION_DOWN, DIRECTION_UP)
    n = len(groups)
    forward = [[math.inf, math.inf] for _ in range(n)]
    parents = [[0, 0] for _ in range(n)]
    for d_index, direction in enumerate(directions):
        forward[0][d_index] = _emission_cost(groups[0], direction, config)
    for index in range(1, n):
        for d_index, direction in enumerate(directions):
            candidates = [
                forward[index - 1][p_index]
                + _transition_cost(groups[index - 1], previous,
                                   groups[index], direction, config,
                                   physical_min_gap_s)
                + _emission_cost(groups[index], direction, config)
                for p_index, previous in enumerate(directions)]
            parent = min(range(2), key=lambda p: (candidates[p], p))
            forward[index][d_index] = candidates[parent]
            parents[index][d_index] = parent
    final_index = min(range(2), key=lambda d: (forward[-1][d], d))
    chosen_indices = [0] * n
    chosen_indices[-1] = final_index
    for index in range(n - 1, 0, -1):
        chosen_indices[index - 1] = parents[index][chosen_indices[index]]

    backward = [[0.0, 0.0] for _ in range(n)]
    for index in range(n - 2, -1, -1):
        for d_index, direction in enumerate(directions):
            backward[index][d_index] = min(
                _transition_cost(groups[index], direction,
                                 groups[index + 1], following, config,
                                 physical_min_gap_s)
                + _emission_cost(groups[index + 1], following, config)
                + backward[index + 1][f_index]
                for f_index, following in enumerate(directions))
    planned = []
    for index, chosen_index in enumerate(chosen_indices):
        conditioned = [forward[index][d] + backward[index][d] for d in range(2)]
        margin = abs(conditioned[0] - conditioned[1])
        confidence = 1.0 - math.exp(-margin)
        group = groups[index]
        chosen = directions[chosen_index]
        source = (
            "onset_order"
            if group.order_direction == chosen and group.order_confidence >= 0.5
            else "phrase_planner")
        planned.append((chosen, source, confidence))
    return tuple(planned), float(forward[-1][final_index])



def compile_strike_events(
        events: Sequence[Mapping[str, Any]], *, fps: int,
        rearm_min_frames: int, follow_through_min_frames: int,
        initial_timing_tolerance_ms: float, window_fraction: float = 0.45,
        planner_config: StrikeDirectionPlannerConfig | None = None,
        reviewed_overrides: Sequence[Mapping[str, Any]] | None = None,
        ) -> CompiledStrikeGoal:
    if not events:
        raise ValueError("strike compiler requires at least one event")
    if isinstance(fps, bool) or not isinstance(fps, int) or fps < 1:
        raise ValueError("fps must be a positive integer")
    for name, value in (("rearm_min_frames", rearm_min_frames),
                        ("follow_through_min_frames", follow_through_min_frames)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    fraction = _unit_interval("window_fraction", window_fraction)
    if fraction <= 0.0 or fraction >= 0.5:
        raise ValueError("window_fraction must be in (0, 0.5)")
    tolerance_s = _positive_finite(
        "initial_timing_tolerance_ms", initial_timing_tolerance_ms) / 1000.0
    config = planner_config or StrikeDirectionPlannerConfig()
    non_negative_costs = {
        "upstroke_prior_cost": config.upstroke_prior_cost,
        "onset_order_mismatch_cost": config.onset_order_mismatch_cost,
        "same_direction_recovery_cost": config.same_direction_recovery_cost,
        "endpoint_travel_cost": config.endpoint_travel_cost,
        "reversal_cost": config.reversal_cost,
        "path_crossing_cost": config.path_crossing_cost,
        "clearance_urgency_cost": config.clearance_urgency_cost,
    }
    if any(not math.isfinite(value) or value < 0.0
           for value in non_negative_costs.values()):
        raise ValueError(
            "strike planner costs must be finite and non-negative")
    if (not math.isfinite(config.recovery_horizon_s)
            or config.recovery_horizon_s <= 0.0):
        raise ValueError("recovery_horizon_s must be finite and positive")
    if (not math.isfinite(config.order_evidence_min_s)
            or config.order_evidence_min_s < 0.0):
        raise ValueError(
            "order_evidence_min_s must be finite and non-negative")
    if (not math.isfinite(config.grouping_max_span_s)
            or config.grouping_max_span_s <= 0.0):
        raise ValueError("grouping_max_span_s must be finite and positive")
    intervals = (
        config.minimum_string_interval_s,
        config.default_string_interval_s,
        config.maximum_string_interval_s)
    if (any(not math.isfinite(value) or value <= 0.0 for value in intervals)
            or not intervals[0] <= intervals[1] <= intervals[2]):
        raise ValueError("string interval limits must be positive and ordered")
    physical_min_gap_s = (
        max(rearm_min_frames, follow_through_min_frames) + 1) / float(fps)
    matching_gap_s = tolerance_s / fraction
    normalized_overrides = normalize_reviewed_strike_overrides(
        events, reviewed_overrides)
    effective_events, force_merge, force_split = _review_grouping_controls(
        events, normalized_overrides)
    clusters, source_indices = [], []
    current, current_indices = [effective_events[0]], [0]
    for index, event in enumerate(effective_events[1:], start=1):
        gap_s = float(event["time"]) - float(current[-1]["time"])
        group_span_s = float(event["time"]) - float(current[0]["time"])
        should_group = (
            index in force_merge
            or (index not in force_split
                and gap_s < physical_min_gap_s - 1e-12
                and group_span_s <= config.grouping_max_span_s + 1e-12))
        if should_group:
            current.append(event)
            current_indices.append(index)
        else:
            clusters.append(tuple(current)); source_indices.append(tuple(current_indices))
            current, current_indices = [event], [index]
    clusters.append(tuple(current)); source_indices.append(tuple(current_indices))
    groups = tuple(_group_cluster(
        cluster, indices, physical_min_gap_s, fps, config)
                   for cluster, indices in zip(clusters, source_indices))
    planned, total_cost = _plan_directions(
        groups, config, physical_min_gap_s)
    compiled_events = []
    for group, (direction, source, confidence) in zip(groups, planned):
        traversal = _traversal(group, direction)
        offsets, duration, fit_rms = _microtiming(
            group, direction, traversal, config)
        audible = tuple(dict.fromkeys(group.audible_strings))
        compiled_events.append(CompiledStrikeEvent(
            time_s=group.time_s,
            frame=group.frame,
            gesture=group.gesture,
            direction=direction,
            audible_strings=audible,
            traversal_strings=traversal,
            protected_strings=tuple(s for s in traversal if s not in audible),
            source_event_ids=group.source_event_ids,
            direction_source=source,
            direction_confidence=confidence,
            source_times_s=group.source_times_s,
            input_times_s=group.input_times_s,
            source_reference_times_s=group.source_reference_times_s,
            time_uncertainties_s=group.time_uncertainties_s,
            source_refs=group.source_refs,
            traversal_offsets_s=offsets,
            sweep_duration_s=duration,
            timing_fit_rms_s=fit_rms,
        ))
    compiled_events = tuple(compiled_events)
    original_times = tuple(event.time_s for event in compiled_events)
    easy_times = [original_times[0]]
    for index, (previous, current_time) in enumerate(
            zip(original_times, original_times[1:]), start=1):
        traversal_span_between = (
            max(compiled_events[index - 1].traversal_offsets_s)
            - min(compiled_events[index].traversal_offsets_s))
        easy_times.append(easy_times[-1] + max(
            current_time - previous, physical_min_gap_s,
            matching_gap_s + traversal_span_between))
    return CompiledStrikeGoal(
        events=compiled_events,
        original_times_s=original_times,
        easy_times_s=tuple(easy_times),
        physical_min_gap_s=physical_min_gap_s,
        matching_gap_s=matching_gap_s,
        window_fraction=fraction,
        planner_total_cost=total_cost,
        planner_config=config,
        reviewed_overrides=normalized_overrides,
    )



def strike_plan_document(compiled: CompiledStrikeGoal, *, fps: int,
                         source: str | None = None,
                         source_sha256: str | None = None) -> dict[str, Any]:
    transitions = compiled.transition_diagnostics(1.0)
    return {
        "schema": STRIKE_PLAN_SCHEMA,
        "metadata": {
            "fps": int(fps),
            "source": source,
            "source_sha256": source_sha256,
            "direction_profile": compiled.direction_profile,
            "planner_total_cost": compiled.planner_total_cost,
            "planner_config": asdict(compiled.planner_config),
            "transition_profile": compiled.transition_profile,
            "string_convention": "Isaac 0=high-e, 5=low-E",
        },
        "events": [{
            "time": event.time_s,
            "frame": event.frame,
            "gesture": event.gesture,
            "strings": list(event.audible_strings),
            "direction": DIRECTION_NAMES[event.direction],
            "traversal_strings": list(event.traversal_strings),
            "protected_strings": list(event.protected_strings),
            "source_event_ids": list(event.source_event_ids),
            "direction_source": event.direction_source,
            "direction_confidence": event.direction_confidence,
            "source_times_s": list(event.source_times_s),
            "input_times_s": list(event.input_times_s),
            "source_reference_times_s": list(
                event.source_reference_times_s),
            "time_uncertainties_s": list(event.time_uncertainties_s),
            "source_refs": list(event.source_refs),
            "traversal_offsets_s": list(event.traversal_offsets_s),
            "sweep_duration_s": event.sweep_duration_s,
            "timing_fit_rms_s": event.timing_fit_rms_s,
        } for event in compiled.events],
        "transitions": [{
            "from_event_index": item.from_event_index,
            "to_event_index": item.to_event_index,
            "traversal_end_time_s": item.traversal_end_time_s,
            "next_start_time_s": item.next_start_time_s,
            "edge_gap_s": item.edge_gap_s,
            "required_edge_gap_s": item.required_edge_gap_s,
            "previous_exit_string": item.previous_exit_string,
            "next_entry_string": item.next_entry_string,
            "previous_direction": DIRECTION_NAMES[item.previous_direction],
            "next_direction": DIRECTION_NAMES[item.next_direction],
            "next_entry_side": item.next_entry_side,
            "direction_reversal": item.direction_reversal,
            "transfer_crossed_strings": list(item.transfer_crossed_strings),
            "same_string_restrike": item.same_string_restrike,
            "clearance_required": item.clearance_required,
            "rearm_required": item.rearm_required,
            "original_tempo_feasible": item.original_tempo_feasible,
            "bridge_split_candidate": item.bridge_split_candidate,
        } for item in transitions],
        "reviewed_overrides": [
            item.as_document() for item in compiled.reviewed_overrides],
        "timeline": {
            "original_times_s": list(compiled.original_times_s),
            "easy_times_s": list(compiled.easy_times_s),
            "physical_min_gap_s": compiled.physical_min_gap_s,
            "matching_gap_s": compiled.matching_gap_s,
            "window_fraction": compiled.window_fraction,
        },
    }



__all__ = [
    "CompiledStrikeEvent", "CompiledStrikeGoal", "DIRECTION_DOWN",
    "DIRECTION_NAMES", "DIRECTION_UP", "GESTURE_ALTERNATE_RESTRIKE",
    "GESTURE_SINGLE_PICK", "GESTURE_STRUM", "STRIKE_DIRECTION_PROFILE",
    "STRIKE_PLAN_SCHEMA", "STRIKE_TRANSITION_PROFILE",
    "STRIKE_TRANSITION_PROFILE_V1",
    "ReviewedStrikeOverride", "StrikeDirectionPlannerConfig",
    "StrikeTransitionDiagnostic",
    "compile_strike_events", "compiled_strike_goal_from_plan_document",
    "normalize_reviewed_strike_overrides", "strike_plan_document",
]
