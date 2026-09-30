from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from typing import Any, Mapping, Sequence, Tuple


GESTURE_SINGLE_PICK = "single_pick"
GESTURE_STRUM = "strum"
GESTURE_ALTERNATE_RESTRIKE = "alternate_restrike"
DIRECTION_DOWN = 1
DIRECTION_UP = -1
DIRECTION_NAMES = {DIRECTION_DOWN: "down", DIRECTION_UP: "up"}
STRIKE_PLAN_SCHEMA = "tab2body.strike_plan.v4"
STRIKE_DIRECTION_PROFILE = "phrase_dp_microtiming_v3"
STRIKE_TRANSITION_PROFILE_V1 = "entry_side_edge_gap_v1"
STRIKE_TRANSITION_PROFILE = "entry_side_edge_gap_v2"


@dataclass(frozen=True)
class StrikeTransitionDiagnostic:
    from_event_index: int
    to_event_index: int
    traversal_end_time_s: float
    next_start_time_s: float
    edge_gap_s: float
    required_edge_gap_s: float
    previous_exit_string: int
    next_entry_string: int
    previous_direction: int
    next_direction: int
    next_entry_side: str
    direction_reversal: bool
    transfer_crossed_strings: Tuple[int, ...]
    same_string_restrike: bool
    clearance_required: bool
    rearm_required: bool
    original_tempo_feasible: bool
    bridge_split_candidate: bool


@dataclass(frozen=True)
class ReviewedStrikeOverride:
    override_id: str
    action: str
    source_event_ids: Tuple[Any, ...]
    reason: str
    evidence_json: str
    resolved_times_s: Tuple[float, ...] = ()

    @property
    def evidence(self) -> Mapping[str, Any]:
        return json.loads(self.evidence_json)

    def as_document(self) -> dict[str, Any]:
        result = {
            "override_id": self.override_id,
            "action": self.action,
            "source_event_ids": list(self.source_event_ids),
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }
        if self.resolved_times_s:
            result["resolved_times_s"] = list(self.resolved_times_s)
        return result


@dataclass(frozen=True)
class StrikeDirectionPlannerConfig:
    upstroke_prior_cost: float = 0.08
    onset_order_mismatch_cost: float = 2.50
    same_direction_recovery_cost: float = 1.10
    endpoint_travel_cost: float = 0.35
    reversal_cost: float = 0.03
    path_crossing_cost: float = 1.20
    clearance_urgency_cost: float = 1.00
    recovery_horizon_s: float = 0.35
    order_evidence_min_s: float = 1.0 / 60.0
    grouping_max_span_s: float = 0.050
    minimum_string_interval_s: float = 0.004
    default_string_interval_s: float = 0.007
    maximum_string_interval_s: float = 0.012


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
    direction_source: str = "phrase_planner"
    direction_confidence: float = 0.0
    source_times_s: Tuple[float, ...] = ()
    input_times_s: Tuple[float, ...] = ()
    source_reference_times_s: Tuple[float, ...] = ()
    time_uncertainties_s: Tuple[float, ...] = ()
    source_refs: Tuple[Any, ...] = ()
    traversal_offsets_s: Tuple[float, ...] = ()
    sweep_duration_s: float = 0.0
    timing_fit_rms_s: float = 0.0


@dataclass(frozen=True)
class CompiledStrikeGoal:
    events: Tuple[CompiledStrikeEvent, ...]
    original_times_s: Tuple[float, ...]
    easy_times_s: Tuple[float, ...]
    physical_min_gap_s: float
    matching_gap_s: float
    window_fraction: float
    planner_total_cost: float = 0.0
    direction_profile: str = STRIKE_DIRECTION_PROFILE
    transition_profile: str = STRIKE_TRANSITION_PROFILE
    planner_config: StrikeDirectionPlannerConfig = StrikeDirectionPlannerConfig()
    reviewed_overrides: Tuple[ReviewedStrikeOverride, ...] = ()

    def runtime_times(self, tempo_lambda: float) -> Tuple[float, ...]:
        value = _unit_interval("tempo_lambda", tempo_lambda)
        return tuple(
            original + (1.0 - value) * (easy - original)
            for original, easy in zip(self.original_times_s, self.easy_times_s))

    def event_windows(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
        tolerance = _positive_finite(
            "timing_tolerance_ms", timing_tolerance_ms) / 1000.0
        times = self.runtime_times(tempo_lambda)
        left = []
        right = []
        for index in range(len(times)):
            current_offsets = self.events[index].traversal_offsets_s
            previous_gap = None
            if index > 0:
                previous_offsets = self.events[index - 1].traversal_offsets_s
                previous_gap = (
                    times[index] + min(current_offsets)
                    - times[index - 1] - max(previous_offsets))
            next_gap = None
            if index + 1 < len(times):
                next_offsets = self.events[index + 1].traversal_offsets_s
                next_gap = (
                    times[index + 1] + min(next_offsets)
                    - times[index] - max(current_offsets))
            left.append(tolerance if previous_gap is None else min(
                tolerance, self.window_fraction * max(previous_gap, 0.0)))
            right.append(tolerance if next_gap is None else min(
                tolerance, self.window_fraction * max(next_gap, 0.0)))
        return tuple(left), tuple(right)

    def gap_diagnostics(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> Mapping[str, float | int | None]:
        times = self.runtime_times(tempo_lambda)
        original_gaps = [b - a for a, b in zip(
            self.original_times_s, self.original_times_s[1:])]
        effective_gaps = [b - a for a, b in zip(times, times[1:])]
        left, right = self.event_windows(tempo_lambda, timing_tolerance_ms)
        overlap_count = sum(
            (times[i] + max(self.events[i].traversal_offsets_s) + right[i]
             >= times[i + 1]
             + min(self.events[i + 1].traversal_offsets_s) - left[i + 1])
            for i in range(len(times) - 1))
        expansions = [easy - original for easy, original in zip(
            self.easy_times_s, self.original_times_s)]
        transitions = self.transition_diagnostics(tempo_lambda)
        return {
            "minimum_original_gap_s": min(original_gaps) if original_gaps else None,
            "minimum_effective_gap_s": min(effective_gaps) if effective_gaps else None,
            "maximum_cumulative_expansion_s": max(expansions, default=0.0),
            "required_matching_gap_s": self.matching_gap_s,
            "physical_min_gap_s": self.physical_min_gap_s,
            "overlap_window_count": int(overlap_count),
            "minimum_traversal_edge_gap_s": min(
                (item.edge_gap_s for item in transitions), default=None),
            "infeasible_transition_count": sum(
                not item.original_tempo_feasible for item in transitions),
            "clearance_required_transition_count": sum(
                item.clearance_required for item in transitions),
            "same_string_restrike_transition_count": sum(
                item.same_string_restrike for item in transitions),
            "rearm_required_transition_count": sum(
                item.rearm_required for item in transitions),
            "bridge_split_candidate_count": sum(
                item.bridge_split_candidate for item in transitions),
        }

    def transition_diagnostics(
            self, tempo_lambda: float = 1.0,
            *, minimum_edge_gap_s: float | None = None,
            clearance_edge_gap_s: float | None = None,
            ) -> Tuple[StrikeTransitionDiagnostic, ...]:
        value = _unit_interval("tempo_lambda", tempo_lambda)
        minimum_gap = (
            self.physical_min_gap_s if minimum_edge_gap_s is None
            else _positive_finite("minimum_edge_gap_s", minimum_edge_gap_s))
        clearance_gap = (
            minimum_gap if clearance_edge_gap_s is None
            else _positive_finite("clearance_edge_gap_s", clearance_edge_gap_s))
        times = self.runtime_times(value)
        return tuple(
            _transition_diagnostic(
                index, self.events[index], self.events[index + 1],
                times[index], times[index + 1], minimum_gap, clearance_gap)
            for index in range(len(self.events) - 1))

    def require_feasible_original_tempo_transitions(
            self, *, minimum_edge_gap_s: float | None = None,
            clearance_edge_gap_s: float | None = None) -> None:
        diagnostics = self.transition_diagnostics(
            1.0, minimum_edge_gap_s=minimum_edge_gap_s,
            clearance_edge_gap_s=clearance_edge_gap_s)
        infeasible = tuple(
            item for item in diagnostics if not item.original_tempo_feasible)
        if not infeasible:
            return
        first = infeasible[0]
        bridge = " bridge-split candidate" if first.bridge_split_candidate else ""
        raise ValueError(
            "infeasible original-tempo strike transition "
            f"{first.from_event_index}->{first.to_event_index}:{bridge} "
            f"traversal edge gap {first.edge_gap_s * 1000.0:.3f} ms is below "
            f"the required {first.required_edge_gap_s * 1000.0:.3f} ms; "
            f"clearance_required={first.clearance_required}, "
            f"crossed_strings={first.transfer_crossed_strings}. Audit the "
            "bundle and resolve its source timing/grouping with a reviewed "
            "merge or separate override before full-song training")

    @property
    def unsupported_events(self) -> Tuple[CompiledStrikeEvent, ...]:
        return tuple(event for event in self.events
                     if event.gesture == GESTURE_ALTERNATE_RESTRIKE)


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


def _entry_side_coordinate(string_index: int, direction: int) -> float:
    return float(string_index) + (0.25 if direction == DIRECTION_DOWN else -0.25)


def _exit_side_coordinate(string_index: int, direction: int) -> float:
    return float(string_index) + (-0.25 if direction == DIRECTION_DOWN else 0.25)


def _crossed_string_centers(start: float, end: float) -> Tuple[int, ...]:
    low, high = sorted((start, end))
    return tuple(
        string_index for string_index in range(6)
        if low < float(string_index) < high)


def _transition_diagnostic(
        index: int, previous: CompiledStrikeEvent,
        current: CompiledStrikeEvent, previous_time_s: float,
        current_time_s: float, minimum_edge_gap_s: float,
        clearance_edge_gap_s: float) -> StrikeTransitionDiagnostic:
    traversal_end_time_s = previous_time_s + previous.traversal_offsets_s[-1]
    next_start_time_s = current_time_s + current.traversal_offsets_s[0]
    edge_gap_s = next_start_time_s - traversal_end_time_s
    previous_exit = previous.traversal_strings[-1]
    next_entry = current.traversal_strings[0]
    exit_position = _exit_side_coordinate(previous_exit, previous.direction)
    entry_position = _entry_side_coordinate(next_entry, current.direction)
    crossed_strings = _crossed_string_centers(exit_position, entry_position)
    same_string_restrike = previous_exit == next_entry
    clearance_required = bool(crossed_strings)
    rearm_required = clearance_required or same_string_restrike
    required_gap = (
        clearance_edge_gap_s if clearance_required else minimum_edge_gap_s)
    feasible = edge_gap_s + 1e-12 >= required_gap
    next_audible_in_previous_bridge = bool(
        set(current.audible_strings).intersection(previous.protected_strings))
    bridge_split_candidate = bool(
        previous.gesture == GESTURE_STRUM
        and current.gesture == GESTURE_SINGLE_PICK
        and next_audible_in_previous_bridge
        and not feasible)
    return StrikeTransitionDiagnostic(
        from_event_index=index,
        to_event_index=index + 1,
        traversal_end_time_s=traversal_end_time_s,
        next_start_time_s=next_start_time_s,
        edge_gap_s=edge_gap_s,
        required_edge_gap_s=required_gap,
        previous_exit_string=previous_exit,
        next_entry_string=next_entry,
        previous_direction=previous.direction,
        next_direction=current.direction,
        next_entry_side=(
            "low_e_side" if current.direction == DIRECTION_DOWN
            else "high_e_side"),
        direction_reversal=previous.direction != current.direction,
        transfer_crossed_strings=crossed_strings,
        same_string_restrike=same_string_restrike,
        clearance_required=clearance_required,
        rearm_required=rearm_required,
        original_tempo_feasible=feasible,
        bridge_split_candidate=bridge_split_candidate,
    )


def _source_event_id(event: Mapping[str, Any], index: int) -> Any:
    return event.get("event_id", index)


def normalize_reviewed_strike_overrides(
        events: Sequence[Mapping[str, Any]],
        overrides: Sequence[Mapping[str, Any]] | None,
        ) -> Tuple[ReviewedStrikeOverride, ...]:
    if overrides is None:
        return ()
    if isinstance(overrides, (str, bytes)) or not isinstance(overrides, Sequence):
        raise ValueError("reviewed_overrides must be an array")
    event_ids = tuple(_source_event_id(event, index)
                      for index, event in enumerate(events))
    if any(isinstance(value, bool) or not isinstance(value, (int, str))
           for value in event_ids):
        raise ValueError("source event ids must be integers or strings")
    if len(set(event_ids)) != len(event_ids):
        raise ValueError("source event ids must be unique for reviewed overrides")
    event_index = {value: index for index, value in enumerate(event_ids)}
    normalized = []
    used_override_ids = set()
    claimed_event_indices = set()
    for override_index, item in enumerate(overrides):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"reviewed override {override_index} must be an object")
        action = item.get("action")
        if action not in ("merge", "separate"):
            raise ValueError(
                f"reviewed override {override_index}: action must be merge or separate")
        raw_ids = item.get("source_event_ids")
        if (isinstance(raw_ids, (str, bytes))
                or not isinstance(raw_ids, Sequence) or len(raw_ids) < 2):
            raise ValueError(
                f"reviewed override {override_index}: source_event_ids must "
                "contain at least two events")
        source_ids = tuple(raw_ids)
        try:
            indices = tuple(event_index[value] for value in source_ids)
        except (KeyError, TypeError) as exc:
            raise ValueError(
                f"reviewed override {override_index}: unknown source event id") from exc
        if indices != tuple(range(indices[0], indices[0] + len(indices))):
            raise ValueError(
                f"reviewed override {override_index}: source events must be "
                "consecutive and listed in timeline order")
        overlap = claimed_event_indices.intersection(indices)
        if overlap:
            raise ValueError(
                f"reviewed override {override_index}: source events overlap "
                "another reviewed override")
        claimed_event_indices.update(indices)
        reason = item.get("reason")
        evidence = item.get("evidence")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"reviewed override {override_index}: non-empty reason is required")
        if not isinstance(evidence, Mapping) or not evidence:
            raise ValueError(
                f"reviewed override {override_index}: non-empty evidence is required")
        try:
            evidence_json = json.dumps(
                dict(evidence), ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"reviewed override {override_index}: evidence must be JSON data") from exc
        override_id = item.get("override_id", f"review-{override_index}")
        if not isinstance(override_id, str) or not override_id.strip():
            raise ValueError(
                f"reviewed override {override_index}: override_id must be non-empty")
        if override_id in used_override_ids:
            raise ValueError(f"duplicate reviewed override id {override_id!r}")
        used_override_ids.add(override_id)
        raw_resolved = item.get("resolved_times_s", ())
        if (isinstance(raw_resolved, (str, bytes))
                or not isinstance(raw_resolved, Sequence)):
            raise ValueError(
                f"reviewed override {override_index}: resolved_times_s must be an array")
        resolved = tuple(float(value) for value in raw_resolved)
        if resolved and action != "merge":
            raise ValueError(
                f"reviewed override {override_index}: resolved times require merge")
        if resolved and len(resolved) != len(source_ids):
            raise ValueError(
                f"reviewed override {override_index}: resolved_times_s length must "
                "match source_event_ids")
        if (any(not math.isfinite(value) or value < 0.0 for value in resolved)
                or any(b < a for a, b in zip(resolved, resolved[1:]))):
            raise ValueError(
                f"reviewed override {override_index}: resolved times must be "
                "finite, non-negative and non-decreasing")
        normalized.append(ReviewedStrikeOverride(
            override_id=override_id,
            action=action,
            source_event_ids=source_ids,
            reason=reason.strip(),
            evidence_json=evidence_json,
            resolved_times_s=resolved,
        ))
    return tuple(normalized)


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


def compiled_strike_goal_from_plan_document(
        document: Mapping[str, Any]) -> CompiledStrikeGoal:
    if document.get("schema") != STRIKE_PLAN_SCHEMA:
        raise ValueError("unsupported strike plan schema")
    raw_events = document.get("events")
    timeline = document.get("timeline")
    metadata = document.get("metadata")
    if not isinstance(raw_events, list) or not raw_events:
        raise ValueError("strike plan events must be a non-empty array")
    if not isinstance(timeline, Mapping) or not isinstance(metadata, Mapping):
        raise ValueError("strike plan metadata and timeline must be objects")
    name_to_direction = {name: value for value, name in DIRECTION_NAMES.items()}
    events = []
    previous_time = -math.inf
    allowed_gestures = {
        GESTURE_SINGLE_PICK, GESTURE_STRUM, GESTURE_ALTERNATE_RESTRIKE}
    for index, item in enumerate(raw_events):
        if not isinstance(item, Mapping):
            raise ValueError(f"strike plan event {index} must be an object")
        try:
            time_s = float(item["time"])
            frame = int(item["frame"])
            gesture = str(item["gesture"])
            direction = name_to_direction[item["direction"]]
            audible = tuple(int(value) for value in item["strings"])
            traversal = tuple(int(value) for value in item["traversal_strings"])
            protected = tuple(int(value) for value in item["protected_strings"])
            source_ids = tuple(item["source_event_ids"])
            source = str(item["direction_source"])
            confidence = float(item["direction_confidence"])
            source_times = tuple(float(value) for value in item["source_times_s"])
            input_times = tuple(float(value) for value in
                                item.get("input_times_s", source_times))
            source_reference_times = tuple(float(value) for value in
                                           item.get(
                                               "source_reference_times_s",
                                               input_times))
            time_uncertainties = tuple(float(value) for value in
                                       item.get(
                                           "time_uncertainties_s",
                                           [0.0] * len(source_times)))
            source_refs = tuple(item.get(
                "source_refs", [None] * len(source_times)))
            offsets = tuple(
                float(value) for value in item["traversal_offsets_s"])
            duration = float(item["sweep_duration_s"])
            fit_rms = float(item["timing_fit_rms_s"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid strike plan event {index}") from exc
        if not math.isfinite(time_s) or time_s < previous_time:
            raise ValueError("strike plan event times must be finite and ordered")
        if frame < 0 or gesture not in allowed_gestures:
            raise ValueError(f"invalid strike plan event {index}")
        if not audible or not traversal or any(
                value < 0 or value > 5 for value in audible + traversal + protected):
            raise ValueError(f"invalid strings in strike plan event {index}")
        if protected != tuple(value for value in traversal if value not in audible):
            raise ValueError(f"inconsistent protected strings in event {index}")
        expected = (
            tuple(range(max(traversal), min(traversal) - 1, -1))
            if direction == DIRECTION_DOWN else
            tuple(range(min(traversal), max(traversal) + 1)))
        if len(traversal) > 1 and traversal != expected:
            raise ValueError(f"direction/traversal mismatch in event {index}")
        if not 0.0 <= confidence <= 1.0 or not source:
            raise ValueError(f"invalid direction evidence in event {index}")
        if (len(source_times) != len(source_ids)
                or len(input_times) != len(source_ids)
                or len(source_reference_times) != len(source_ids)
                or len(time_uncertainties) != len(source_ids)
                or len(source_refs) != len(source_ids)
                or len(offsets) != len(traversal)
                or any(not math.isfinite(value)
                       for value in source_times + input_times
                       + source_reference_times + time_uncertainties + offsets)
                or any(value < 0.0 for value in input_times
                       + source_reference_times + time_uncertainties)
                or any(value is not None and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, str))
                    or isinstance(value, str) and not value)
                       for value in source_refs)
                or not math.isfinite(duration) or duration < 0.0
                or not math.isfinite(fit_rms) or fit_rms < 0.0):
            raise ValueError(f"invalid microtiming in event {index}")
        if any(b <= a for a, b in zip(offsets, offsets[1:])):
            raise ValueError(
                f"traversal offsets must be strictly increasing in event {index}")
        expected_duration = offsets[-1] - offsets[0]
        if not math.isclose(duration, expected_duration, abs_tol=1e-12):
            raise ValueError(f"sweep duration mismatch in event {index}")
        if not math.isclose(
                sum(source_times) / len(source_times), time_s,
                abs_tol=1e-9):
            raise ValueError(f"strum center time mismatch in event {index}")
        events.append(CompiledStrikeEvent(
            time_s=time_s, frame=frame, gesture=gesture, direction=direction,
            audible_strings=audible, traversal_strings=traversal,
            protected_strings=protected, source_event_ids=source_ids,
            direction_source=source, direction_confidence=confidence,
            source_times_s=source_times, input_times_s=input_times,
            source_reference_times_s=source_reference_times,
            time_uncertainties_s=time_uncertainties,
            source_refs=source_refs, traversal_offsets_s=offsets,
            sweep_duration_s=duration, timing_fit_rms_s=fit_rms))
        previous_time = time_s
    try:
        original = tuple(float(value) for value in timeline["original_times_s"])
        easy = tuple(float(value) for value in timeline["easy_times_s"])
        physical = float(timeline["physical_min_gap_s"])
        matching = float(timeline["matching_gap_s"])
        fraction = float(timeline["window_fraction"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid strike plan timeline") from exc
    if original != tuple(event.time_s for event in events):
        raise ValueError("strike plan timeline does not match events")
    if len(easy) != len(events) or any(b <= a for a, b in zip(easy, easy[1:])):
        raise ValueError("strike plan easy timeline must be strictly increasing")
    raw_planner_config = metadata.get("planner_config", {})
    if not isinstance(raw_planner_config, Mapping):
        raise ValueError("strike plan planner_config must be an object")
    try:
        planner_config = StrikeDirectionPlannerConfig(**raw_planner_config)
    except TypeError as exc:
        raise ValueError("invalid strike plan planner_config") from exc
    raw_overrides = document.get("reviewed_overrides", ())
    flattened_source_events = [
        {"event_id": source_id}
        for event in events for source_id in event.source_event_ids]
    reviewed_overrides = normalize_reviewed_strike_overrides(
        flattened_source_events, raw_overrides)
    result = CompiledStrikeGoal(
        events=tuple(events), original_times_s=original, easy_times_s=easy,
        physical_min_gap_s=_positive_finite("physical_min_gap_s", physical),
        matching_gap_s=_positive_finite("matching_gap_s", matching),
        window_fraction=_unit_interval("window_fraction", fraction),
        planner_total_cost=float(metadata.get("planner_total_cost", 0.0)),
        direction_profile=str(metadata.get(
            "direction_profile", STRIKE_DIRECTION_PROFILE)),
        planner_config=planner_config,
        reviewed_overrides=reviewed_overrides)
    raw_transitions = document.get("transitions")
    transition_profile = metadata.get("transition_profile")
    if raw_transitions is None:
        if transition_profile is not None:
            raise ValueError(
                "strike plan declares transition_profile without transitions")
        return result
    if transition_profile not in (
            STRIKE_TRANSITION_PROFILE_V1, STRIKE_TRANSITION_PROFILE):
        raise ValueError("unsupported strike transition profile")
    if not isinstance(raw_transitions, list):
        raise ValueError("strike plan transitions must be an array")
    derived = result.transition_diagnostics(1.0)
    if len(raw_transitions) != len(derived):
        raise ValueError("strike plan transition count does not match events")
    for index, (raw, expected_transition) in enumerate(
            zip(raw_transitions, derived)):
        if not isinstance(raw, Mapping):
            raise ValueError(f"strike plan transition {index} must be an object")
        try:
            raw_from = int(raw["from_event_index"])
            raw_to = int(raw["to_event_index"])
            raw_end_time = float(raw["traversal_end_time_s"])
            raw_start_time = float(raw["next_start_time_s"])
            raw_edge_gap = float(raw["edge_gap_s"])
            raw_required_gap = float(raw["required_edge_gap_s"])
            raw_previous_exit = int(raw["previous_exit_string"])
            raw_next_entry = int(raw["next_entry_string"])
            raw_previous_direction = name_to_direction[
                raw["previous_direction"]]
            raw_next_direction = name_to_direction[raw["next_direction"]]
            raw_entry_side = str(raw["next_entry_side"])
            raw_reversal = raw["direction_reversal"]
            raw_crossed = tuple(int(value) for value in
                                raw["transfer_crossed_strings"])
            raw_same_string = raw.get(
                "same_string_restrike",
                expected_transition.same_string_restrike)
            raw_clearance = raw["clearance_required"]
            raw_rearm = raw.get(
                "rearm_required", expected_transition.rearm_required)
            raw_feasible = raw["original_tempo_feasible"]
            raw_bridge = raw["bridge_split_candidate"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid strike plan transition {index}") from exc
        expected_raw_clearance = expected_transition.clearance_required
        if transition_profile == STRIKE_TRANSITION_PROFILE_V1:
            expected_raw_clearance = (
                expected_raw_clearance
                or expected_transition.same_string_restrike)
        if (raw_from != expected_transition.from_event_index
                or raw_to != expected_transition.to_event_index
                or not math.isclose(
                    raw_end_time,
                    expected_transition.traversal_end_time_s,
                    rel_tol=0.0, abs_tol=1e-9)
                or not math.isclose(
                    raw_start_time, expected_transition.next_start_time_s,
                    rel_tol=0.0, abs_tol=1e-9)
                or not math.isclose(
                    raw_edge_gap, expected_transition.edge_gap_s,
                    rel_tol=0.0, abs_tol=1e-9)
                or not math.isclose(
                    raw_required_gap,
                    expected_transition.required_edge_gap_s,
                    rel_tol=0.0, abs_tol=1e-12)
                or raw_previous_exit != expected_transition.previous_exit_string
                or raw_next_entry != expected_transition.next_entry_string
                or raw_previous_direction != expected_transition.previous_direction
                or raw_next_direction != expected_transition.next_direction
                or raw_entry_side != expected_transition.next_entry_side
                or not isinstance(raw_reversal, bool)
                or raw_reversal != expected_transition.direction_reversal
                or raw_crossed != expected_transition.transfer_crossed_strings
                or not isinstance(raw_same_string, bool)
                or raw_same_string != expected_transition.same_string_restrike
                or not isinstance(raw_clearance, bool)
                or raw_clearance != expected_raw_clearance
                or not isinstance(raw_rearm, bool)
                or raw_rearm != expected_transition.rearm_required
                or not isinstance(raw_feasible, bool)
                or raw_feasible != expected_transition.original_tempo_feasible
                or not isinstance(raw_bridge, bool)
                or raw_bridge != expected_transition.bridge_split_candidate):
            raise ValueError(
                f"strike plan transition {index} does not match events")
    return result


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
