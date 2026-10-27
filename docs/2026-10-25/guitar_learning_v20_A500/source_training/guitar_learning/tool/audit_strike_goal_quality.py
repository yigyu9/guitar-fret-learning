from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


AUDIT_SCHEMA = "tab2body.strike_goal_quality_audit.v1"
STATUS_PASS = "PASS"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_INFEASIBLE = "INFEASIBLE"
STATUS_RANK = {
    STATUS_PASS: 0,
    STATUS_AMBIGUOUS: 1,
    STATUS_INFEASIBLE: 2,
}


@dataclass(frozen=True)
class AuditConfig:
    reference_match_window_ms: float = 250.0
    reference_ambiguous_delta_ms: float = 50.0
    reference_pitch_tolerance: float = 1.0
    grouping_boundary_margin_ms: float = 5.0
    edge_gap_margin_ms: float = 5.0
    numeric_epsilon_s: float = 1e-9

    def validate(self) -> "AuditConfig":
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite non-negative number")
            if not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if self.reference_match_window_ms <= 0.0:
            raise ValueError("reference_match_window_ms must be positive")
        return self


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("top-level JSON value must be an object")
    return value


def _finite_float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _time_to_frame(time_s: float, fps: int) -> int:
    return int(math.floor(float(time_s) * float(fps) + 0.5))


def _source_key(value: Any) -> Tuple[str, str]:
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        encoded = repr(value)
    return type(value).__name__, encoded


def _percentile(values: Sequence[float], probability: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def _summary_ms(values_s: Sequence[float]) -> Mapping[str, Any]:
    values_ms = [float(value) * 1000.0 for value in values_s]
    absolute = [abs(value) for value in values_ms]
    return {
        "count": len(values_ms),
        "signed_mean_ms": (
            sum(values_ms) / len(values_ms) if values_ms else None),
        "absolute_mean_ms": (
            sum(absolute) / len(absolute) if absolute else None),
        "absolute_p95_ms": _percentile(absolute, 0.95),
        "absolute_max_ms": max(absolute) if absolute else None,
    }


def _empty_bundle_report(bundle: Path) -> Dict[str, Any]:
    paths = {
        "fingering": bundle / "mapping" / "fingering.json",
        "strike_input": bundle / "training" / "strike_training.json",
        "strike_plan": bundle / "training" / "strike_plan.json",
        "reference_jams": bundle / "source" / "annotation.jams",
    }
    return {
        "song_id": bundle.name,
        "bundle": str(bundle.resolve()),
        "status": STATUS_PASS,
        "files": {
            name: {"path": str(path.resolve()), "exists": path.is_file()}
            for name, path in paths.items()
        },
        "counts": {},
        "input_consistency": {},
        "compiled_plan_consistency": {},
        "reviewed_overrides": {
            "count": 0,
            "top_level_status": None,
            "status_class": "not_applicable",
            "status_sources": [],
            "review_documents": [],
            "embedded_in_strike_input": False,
            "input_plan_payload_match": None,
            "items": [],
            "issues": [],
        },
        "reference_onsets": {"available": paths["reference_jams"].is_file()},
        "ambiguous_grouping_boundaries": [],
        "noncontiguous_inferred_strums": [],
        "traversal_edge_gaps": {
            "physical_min_gap_ms": None,
            "minimum_actual_edge_gap_ms": None,
            "edges": [],
            "below_physical_count": 0,
            "near_physical_count": 0,
        },
        "reversal_direct_paths": [],
        "findings": [],
    }


def _add_finding(
        report: Dict[str, Any], severity: str, category: str,
        message: str, **details: Any) -> None:
    finding = {
        "severity": severity,
        "category": category,
        "message": message,
    }
    if details:
        finding["details"] = details
    report["findings"].append(finding)


def _finalize_bundle(report: Dict[str, Any]) -> Dict[str, Any]:
    report["status"] = max(
        (finding["severity"] for finding in report["findings"]),
        key=lambda value: STATUS_RANK[value], default=STATUS_PASS)
    report["finding_counts"] = dict(Counter(
        finding["severity"] for finding in report["findings"]))
    return report


def _expected_raw_event(note: Mapping[str, Any], fps: int) -> Optional[dict]:
    time_s = _finite_float(note.get("t_on"))
    source_string = note.get("string")
    if time_s is None or time_s < 0.0:
        return None
    if not _integer(source_string) or not 0 <= source_string <= 5:
        return None
    return {
        "time": time_s,
        "frame": _time_to_frame(time_s, fps),
        "string": 5 - source_string,
    }


def _audit_fingering_to_input(
        report: Dict[str, Any], fingering: Mapping[str, Any],
        strike_input: Mapping[str, Any], fps: int,
        config: AuditConfig) -> Tuple[List[Mapping[str, Any]], List[Mapping[str, Any]]]:
    notes = fingering.get("notes")
    raw_events = strike_input.get("events")
    if not isinstance(notes, list) or not isinstance(raw_events, list):
        _add_finding(
            report, STATUS_INFEASIBLE, "invalid_input_structure",
            "fingering.notes and strike input events must both be arrays")
        return [], []

    mismatches = []
    onset_deltas = []
    invalid_notes = []
    for index, (note, event) in enumerate(zip(notes, raw_events)):
        if not isinstance(note, Mapping) or not isinstance(event, Mapping):
            mismatches.append({"source_event_id": index, "reason": "not_object"})
            continue
        expected = _expected_raw_event(note, fps)
        if expected is None:
            invalid_notes.append(index)
            continue
        actual_time = _finite_float(event.get("time"))
        if actual_time is not None:
            onset_deltas.append(actual_time - expected["time"])
        fields = {}
        if actual_time is None or abs(actual_time - expected["time"]) > 1e-6:
            fields["time"] = {
                "expected": expected["time"], "actual": event.get("time")}
        if event.get("frame") != expected["frame"]:
            fields["frame"] = {
                "expected": expected["frame"], "actual": event.get("frame")}
        if event.get("string") != expected["string"]:
            fields["string"] = {
                "expected": expected["string"], "actual": event.get("string")}
        if fields:
            mismatches.append({"source_event_id": index, "fields": fields})

    count_delta = len(raw_events) - len(notes)
    if count_delta:
        mismatches.append({
            "reason": "event_count_mismatch",
            "fingering_notes": len(notes),
            "strike_events": len(raw_events),
        })
    if invalid_notes:
        mismatches.append({
            "reason": "invalid_fingering_notes",
            "source_event_ids": invalid_notes[:20],
            "count": len(invalid_notes),
        })

    report["input_consistency"] = {
        "fingering_note_count": len(notes),
        "strike_input_event_count": len(raw_events),
        "onset_deltas": _summary_ms(onset_deltas),
        "mismatch_count": len(mismatches),
        "mismatch_samples": mismatches[:20],
    }
    if mismatches:
        _add_finding(
            report, STATUS_INFEASIBLE, "fingering_strike_input_mismatch",
            "strike input is not a lossless [time, frame, 5-string] projection "
            "of fingering notes",
            mismatch_count=len(mismatches), samples=mismatches[:5])
    return notes, raw_events


def _event_offsets(event: Mapping[str, Any]) -> List[float]:
    offsets = event.get("traversal_offsets_s", [0.0])
    if not isinstance(offsets, list) or not offsets:
        return []
    result = []
    for value in offsets:
        numeric = _finite_float(value)
        if numeric is None:
            return []
        result.append(numeric)
    return result


def _audit_plan_consistency(
        report: Dict[str, Any], raw_events: Sequence[Mapping[str, Any]],
        plan: Mapping[str, Any], fps: int,
        config: AuditConfig) -> Tuple[List[Mapping[str, Any]], Dict[int, int]]:
    plan_events = plan.get("events")
    if not isinstance(plan_events, list):
        _add_finding(
            report, STATUS_INFEASIBLE, "invalid_plan_structure",
            "strike plan events must be an array")
        return [], {}

    raw_by_id = {}
    raw_index_by_id = {}
    duplicate_raw_ids = []
    for index, event in enumerate(raw_events):
        if not isinstance(event, Mapping):
            continue
        source_id = event.get("event_id", index)
        key = _source_key(source_id)
        if key in raw_by_id:
            duplicate_raw_ids.append(source_id)
        raw_by_id[key] = event
        raw_index_by_id[key] = index

    issues = []
    coverage = Counter()
    raw_to_plan = {}
    resolved_minus_input = []
    resolved_authority = {}
    raw_overrides = plan.get("reviewed_overrides", [])
    if isinstance(raw_overrides, list):
        for override in raw_overrides:
            if not isinstance(override, Mapping):
                continue
            source_ids = override.get("source_event_ids")
            resolved_times = override.get("resolved_times_s")
            if (isinstance(source_ids, list)
                    and isinstance(resolved_times, list)
                    and len(source_ids) == len(resolved_times)):
                for source_id, resolved_time in zip(source_ids, resolved_times):
                    value = _finite_float(resolved_time)
                    if value is not None:
                        resolved_authority[_source_key(source_id)] = value
    for plan_index, event in enumerate(plan_events):
        if not isinstance(event, Mapping):
            issues.append({"plan_event": plan_index, "reason": "not_object"})
            continue
        source_ids = event.get("source_event_ids")
        source_times = event.get("source_times_s")
        input_times = event.get("input_times_s", source_times)
        if not isinstance(source_ids, list) or not source_ids:
            issues.append({
                "plan_event": plan_index,
                "reason": "missing_source_event_ids",
            })
            continue
        resolved = []
        missing = []
        for source_id in source_ids:
            key = _source_key(source_id)
            raw = raw_by_id.get(key)
            if raw is None:
                missing.append(source_id)
                continue
            resolved.append((source_id, raw, raw_index_by_id[key]))
            coverage[key] += 1
            raw_to_plan[raw_index_by_id[key]] = plan_index
        if missing:
            issues.append({
                "plan_event": plan_index,
                "reason": "unknown_source_event_ids",
                "source_event_ids": missing,
            })
        if len(resolved) != len(source_ids):
            continue

        raw_times = [_finite_float(raw.get("time")) for _, raw, _ in resolved]
        raw_strings = [raw.get("string") for _, raw, _ in resolved]
        if any(value is None for value in raw_times):
            issues.append({
                "plan_event": plan_index, "reason": "invalid_raw_source_time"})
            continue
        raw_input_times = [float(value) for value in raw_times if value is not None]
        if not isinstance(input_times, list) or len(input_times) != len(raw_input_times):
            issues.append({
                "plan_event": plan_index,
                "reason": "input_times_length_mismatch",
            })
        else:
            deltas = []
            for actual, expected in zip(input_times, raw_input_times):
                actual_float = _finite_float(actual)
                if actual_float is None:
                    deltas.append(None)
                else:
                    deltas.append((actual_float - expected) * 1000.0)
            if any(value is None or abs(value) > 0.001 for value in deltas):
                issues.append({
                    "plan_event": plan_index,
                    "reason": "input_time_mismatch",
                    "deltas_ms": deltas,
                })

        effective_times = []
        if not isinstance(source_times, list) or len(source_times) != len(raw_input_times):
            issues.append({
                "plan_event": plan_index,
                "reason": "source_times_length_mismatch",
            })
        else:
            effective_times = [_finite_float(value) for value in source_times]
            if any(value is None or value < 0.0 for value in effective_times):
                issues.append({
                    "plan_event": plan_index,
                    "reason": "invalid_resolved_source_times",
                })
            elif isinstance(input_times, list):
                finite_inputs = [_finite_float(value) for value in input_times]
                if (len(finite_inputs) == len(effective_times)
                        and all(value is not None for value in finite_inputs)):
                    resolved_minus_input.extend(
                        float(resolved_time) - float(input_time)
                        for resolved_time, input_time in zip(
                            effective_times, finite_inputs))
                    for source_id, resolved_time, input_time in zip(
                            source_ids, effective_times, finite_inputs):
                        if (abs(float(resolved_time) - float(input_time))
                                <= config.numeric_epsilon_s):
                            continue
                        authority = resolved_authority.get(
                            _source_key(source_id))
                        if (authority is None
                                or abs(authority - float(resolved_time))
                                > config.numeric_epsilon_s):
                            issues.append({
                                "plan_event": plan_index,
                                "reason": "unproven_resolved_source_time",
                                "source_event_id": source_id,
                                "input_time_s": input_time,
                                "source_time_s": resolved_time,
                            })

        if any(not _integer(value) or not 0 <= value <= 5
               for value in raw_strings):
            issues.append({
                "plan_event": plan_index,
                "reason": "invalid_raw_source_string",
                "actual": raw_strings,
            })
        else:
            expected_strings = list(dict.fromkeys(raw_strings))
            if event.get("strings") != expected_strings:
                issues.append({
                    "plan_event": plan_index,
                    "reason": "audible_string_mismatch",
                    "expected": expected_strings,
                    "actual": event.get("strings"),
                })
        if len(effective_times) != len(raw_input_times) or any(
                value is None for value in effective_times):
            continue
        center_times = [
            float(value) for value in effective_times if value is not None]
        center = sum(center_times) / len(center_times)
        actual_center = _finite_float(event.get("time"))
        if actual_center is None or abs(actual_center - center) > 1e-6:
            issues.append({
                "plan_event": plan_index,
                "reason": "center_time_mismatch",
                "expected": center,
                "actual": event.get("time"),
            })
        if event.get("frame") != _time_to_frame(center, fps):
            issues.append({
                "plan_event": plan_index,
                "reason": "center_frame_mismatch",
                "expected": _time_to_frame(center, fps),
                "actual": event.get("frame"),
            })

        traversal = event.get("traversal_strings")
        offsets = _event_offsets(event)
        direction = event.get("direction")
        if not isinstance(traversal, list) or not traversal:
            issues.append({
                "plan_event": plan_index, "reason": "empty_traversal"})
        else:
            if (any(not _integer(value) or not 0 <= value <= 5
                    for value in traversal)
                    or any(abs(right - left) != 1
                           for left, right in zip(traversal, traversal[1:]))):
                issues.append({
                    "plan_event": plan_index,
                    "reason": "noncontiguous_or_invalid_traversal",
                    "traversal_strings": traversal,
                })
            expected_step = -1 if direction == "down" else 1 if direction == "up" else 0
            if expected_step == 0:
                issues.append({
                    "plan_event": plan_index,
                    "reason": "invalid_direction", "direction": direction})
            elif len(traversal) > 1 and any(
                    right - left != expected_step
                    for left, right in zip(traversal, traversal[1:])):
                issues.append({
                    "plan_event": plan_index,
                    "reason": "direction_traversal_mismatch",
                    "direction": direction,
                    "traversal_strings": traversal,
                })
            audible = event.get("strings")
            if isinstance(audible, list) and any(
                    string_index not in traversal for string_index in audible):
                issues.append({
                    "plan_event": plan_index,
                    "reason": "audible_string_outside_traversal",
                })
        traversal_length = len(traversal) if isinstance(traversal, list) else 0
        if len(offsets) != traversal_length:
            issues.append({
                "plan_event": plan_index,
                "reason": "traversal_offset_length_mismatch",
            })
        elif any(right < left - config.numeric_epsilon_s
                 for left, right in zip(offsets, offsets[1:])):
            issues.append({
                "plan_event": plan_index,
                "reason": "nonmonotonic_traversal_offsets",
            })

    for source_id in duplicate_raw_ids:
        issues.append({
            "reason": "duplicate_raw_source_id", "source_event_id": source_id})
    uncovered = []
    duplicated = []
    for key, index in raw_index_by_id.items():
        count = coverage[key]
        if count == 0:
            uncovered.append(index)
        elif count > 1:
            duplicated.append(index)
    if uncovered:
        issues.append({
            "reason": "uncovered_raw_events", "source_event_ids": uncovered[:50],
            "count": len(uncovered)})
    if duplicated:
        issues.append({
            "reason": "multiply_compiled_raw_events",
            "source_event_ids": duplicated[:50], "count": len(duplicated)})

    timeline = plan.get("timeline")
    original_times = timeline.get("original_times_s") if isinstance(timeline, Mapping) else None
    if not isinstance(original_times, list) or len(original_times) != len(plan_events):
        issues.append({"reason": "timeline_event_count_mismatch"})
    else:
        for index, (event, timeline_time) in enumerate(zip(plan_events, original_times)):
            event_time = _finite_float(event.get("time")) if isinstance(event, Mapping) else None
            value = _finite_float(timeline_time)
            if (event_time is None or value is None
                    or abs(event_time - value) > 1e-6):
                issues.append({
                    "plan_event": index, "reason": "timeline_time_mismatch"})
                break

    report["compiled_plan_consistency"] = {
        "raw_event_count": len(raw_events),
        "plan_event_count": len(plan_events),
        "covered_raw_event_count": sum(count > 0 for count in coverage.values()),
        "resolved_minus_input_onset_deltas": _summary_ms(
            resolved_minus_input),
        "issue_count": len(issues),
        "issue_samples": issues[:30],
    }
    if issues:
        _add_finding(
            report, STATUS_INFEASIBLE, "strike_input_plan_mismatch",
            "compiled StrikePlan does not preserve every raw event exactly once",
            issue_count=len(issues), samples=issues[:5])
    return plan_events, raw_to_plan


def _override_identity(item: Mapping[str, Any], index: int) -> Tuple[Any, ...]:
    override_id = item.get("override_id", f"review-{index}")
    source_ids = item.get("source_event_ids")
    if not isinstance(source_ids, list):
        source_ids = []
    return (
        str(override_id), item.get("action"),
        tuple(_source_key(value) for value in source_ids),
    )


def _override_payload(item: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    reason = item.get("reason")
    return {
        "override_id": item.get("override_id", f"review-{index}"),
        "action": item.get("action"),
        "source_event_ids": item.get("source_event_ids"),
        "resolved_times_s": item.get("resolved_times_s", []),
        "reason": reason.strip() if isinstance(reason, str) else reason,
        "evidence": item.get("evidence"),
    }


def _override_sets_match(
        left: Sequence[Mapping[str, Any]],
        right: Sequence[Mapping[str, Any]]) -> bool:
    if len(left) != len(right):
        return False
    left_ids = sorted(
        (_override_identity(item, index) for index, item in enumerate(left)),
        key=repr)
    right_ids = sorted(
        (_override_identity(item, index) for index, item in enumerate(right)),
        key=repr)
    return left_ids == right_ids


def _override_payloads_match(
        left: Sequence[Mapping[str, Any]],
        right: Sequence[Mapping[str, Any]]) -> bool:
    if not _override_sets_match(left, right):
        return False
    left_items = sorted(
        ((_override_identity(item, index), _override_payload(item, index))
         for index, item in enumerate(left)), key=lambda item: repr(item[0]))
    right_items = sorted(
        ((_override_identity(item, index), _override_payload(item, index))
         for index, item in enumerate(right)), key=lambda item: repr(item[0]))
    return all(
        left_identity == right_identity and left_payload == right_payload
        for (left_identity, left_payload), (right_identity, right_payload)
        in zip(left_items, right_items))


def _document_review_status(document: Mapping[str, Any]) -> Any:
    for key in ("review_status", "status"):
        if key in document:
            return document.get(key)
    metadata = document.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("review_status", "status"):
            if key in metadata:
                return metadata.get(key)
    review = document.get("review")
    if isinstance(review, Mapping):
        return review.get("status")
    return None


def _review_status_class(statuses: Sequence[str]) -> str:
    normalized = [
        value.strip().lower().replace("-", "_").replace(" ", "_")
        for value in statuses if value.strip()]
    if any(any(token in value for token in (
            "reject", "denied", "invalid", "withdrawn",
            "not_approved", "unapproved"))
           for value in normalized):
        return "rejected"
    if any(any(token in value for token in (
            "pending", "proposed", "draft", "unreviewed", "needs_review"))
           for value in normalized):
        return "pending"
    approved = (
        "approved", "accepted", "verified", "final", "complete", "reviewed")
    if normalized and all(any(token in value for token in approved)
                          for value in normalized):
        return "approved"
    return "unknown"


def _audit_reviewed_overrides(
        report: Dict[str, Any], bundle: Path,
        strike_input: Mapping[str, Any], plan: Mapping[str, Any],
        raw_events: Sequence[Mapping[str, Any]],
        plan_events: Sequence[Mapping[str, Any]],
        raw_to_plan: Mapping[int, int], config: AuditConfig) -> None:
    raw_plan_overrides = plan.get("reviewed_overrides", [])
    if raw_plan_overrides is None:
        raw_plan_overrides = []
    if not isinstance(raw_plan_overrides, list):
        report["reviewed_overrides"] = {
            "count": 0,
            "top_level_status": None,
            "status_class": "invalid",
            "status_sources": [],
            "review_documents": [],
            "embedded_in_strike_input": False,
            "input_plan_payload_match": None,
            "items": [],
            "issues": [{"reason": "plan_reviewed_overrides_not_array"}],
        }
        _add_finding(
            report, STATUS_INFEASIBLE, "reviewed_override_contract_invalid",
            "StrikePlan reviewed_overrides must be an array")
        return
    plan_overrides = [
        item for item in raw_plan_overrides if isinstance(item, Mapping)]
    if not raw_plan_overrides:
        input_overrides = strike_input.get("reviewed_overrides")
        if isinstance(input_overrides, list) and input_overrides:
            report["reviewed_overrides"].update({
                "status_class": "invalid",
                "embedded_in_strike_input": True,
                "input_plan_payload_match": False,
                "issues": [{"reason": "input_overrides_missing_from_plan"}],
            })
            _add_finding(
                report, STATUS_INFEASIBLE,
                "reviewed_override_contract_invalid",
                "strike input embeds reviewed overrides that are absent from "
                "the compiled StrikePlan")
        return

    issues = []
    if len(plan_overrides) != len(raw_plan_overrides):
        issues.append({"reason": "reviewed_override_not_object"})
    raw_index = {}
    for index, event in enumerate(raw_events):
        if isinstance(event, Mapping):
            raw_index[_source_key(event.get("event_id", index))] = index
    effective_by_source = {}
    input_by_source = {}
    for event in plan_events:
        if not isinstance(event, Mapping):
            continue
        source_ids = event.get("source_event_ids")
        source_times = event.get("source_times_s")
        input_times = event.get("input_times_s", source_times)
        if (not isinstance(source_ids, list)
                or not isinstance(source_times, list)
                or not isinstance(input_times, list)
                or len(source_ids) != len(source_times)
                or len(source_ids) != len(input_times)):
            continue
        for source_id, source_time, input_time in zip(
                source_ids, source_times, input_times):
            effective_by_source[_source_key(source_id)] = _finite_float(source_time)
            input_by_source[_source_key(source_id)] = _finite_float(input_time)

    items = []
    identities = set()
    claimed = set()
    resolved_claims = set()
    for override_index, override in enumerate(plan_overrides):
        identity = _override_identity(override, override_index)
        if identity in identities:
            issues.append({
                "override_index": override_index,
                "reason": "duplicate_override_identity"})
        identities.add(identity)
        override_id, action, _ = identity
        source_ids = override.get("source_event_ids")
        reason = override.get("reason")
        evidence = override.get("evidence")
        resolved_times = override.get("resolved_times_s", [])
        item_issues = []
        if action not in ("merge", "separate"):
            item_issues.append("invalid_action")
        if not isinstance(source_ids, list) or len(source_ids) < 2:
            item_issues.append("invalid_source_event_ids")
            source_ids = []
        if not isinstance(reason, str) or not reason.strip():
            item_issues.append("missing_reason")
        if not isinstance(evidence, Mapping) or not evidence:
            item_issues.append("missing_evidence")
        if not isinstance(resolved_times, list):
            item_issues.append("resolved_times_not_array")
            resolved_times = []
        finite_resolved = [_finite_float(value) for value in resolved_times]
        if (any(value is None or value < 0.0 for value in finite_resolved)
                or any(right < left for left, right in zip(
                    [value for value in finite_resolved if value is not None],
                    [value for value in finite_resolved if value is not None][1:]))):
            item_issues.append("invalid_resolved_times")
        if resolved_times and (
                action != "merge" or len(resolved_times) != len(source_ids)):
            item_issues.append("resolved_times_contract_mismatch")

        indices = []
        for source_id in source_ids:
            index = raw_index.get(_source_key(source_id))
            if index is None:
                item_issues.append("unknown_source_event_id")
            else:
                indices.append(index)
        if indices and indices != list(range(indices[0], indices[0] + len(indices))):
            item_issues.append("source_events_not_consecutive")
        if claimed.intersection(indices):
            item_issues.append("overlapping_reviewed_overrides")
        claimed.update(indices)

        compiled_groups = {
            raw_to_plan[index] for index in indices if index in raw_to_plan}
        if action == "merge" and indices and len(compiled_groups) != 1:
            item_issues.append("merge_not_reflected_in_plan")
        if action == "separate" and len(indices) > 1 and any(
                raw_to_plan.get(left) == raw_to_plan.get(right)
                for left, right in zip(indices, indices[1:])):
            item_issues.append("separation_not_reflected_in_plan")

        effective_times = [
            effective_by_source.get(_source_key(source_id))
            for source_id in source_ids]
        input_times = [
            input_by_source.get(_source_key(source_id))
            for source_id in source_ids]
        if resolved_times and len(resolved_times) == len(effective_times):
            resolved_claims.update(_source_key(source_id) for source_id in source_ids)
            if any(
                    actual is None or expected is None
                    or abs(actual - expected) > config.numeric_epsilon_s
                    for actual, expected in zip(
                        effective_times, finite_resolved)):
                item_issues.append("resolved_times_not_reflected_in_plan")
        elif not resolved_times and any(
                effective is not None and input_time is not None
                and abs(effective - input_time) > config.numeric_epsilon_s
                for effective, input_time in zip(effective_times, input_times)):
            item_issues.append("unproven_resolved_time_change")

        evidence_status = (
            evidence.get("manual_audio_review")
            if isinstance(evidence, Mapping) else None)
        item_report = {
            "override_id": override_id,
            "action": action,
            "source_event_ids": source_ids,
            "reason": reason,
            "evidence": dict(evidence) if isinstance(evidence, Mapping) else evidence,
            "resolved_times_s": resolved_times,
            "plan_source_times_s": effective_times,
            "plan_input_times_s": input_times,
            "resolved_minus_input_deltas_ms": [
                ((effective - input_time) * 1000.0
                 if effective is not None and input_time is not None else None)
                for effective, input_time in zip(effective_times, input_times)],
            "evidence_review_status": evidence_status,
            "issues": item_issues,
        }
        items.append(item_report)
        for reason_name in item_issues:
            issues.append({
                "override_index": override_index,
                "override_id": override_id,
                "reason": reason_name,
            })

    changed_without_override = []
    for source_key, effective_time in effective_by_source.items():
        input_time = input_by_source.get(source_key)
        if (effective_time is not None and input_time is not None
                and abs(effective_time - input_time) > config.numeric_epsilon_s
                and source_key not in resolved_claims):
            changed_without_override.append({
                "source_event_key": list(source_key),
                "input_time_s": input_time,
                "source_time_s": effective_time,
            })
    if changed_without_override:
        issues.append({
            "reason": "source_times_changed_without_resolved_override",
            "count": len(changed_without_override),
            "samples": changed_without_override[:20],
        })

    input_overrides = strike_input.get("reviewed_overrides")
    input_override_match = None
    if input_overrides is not None:
        if (not isinstance(input_overrides, list)
                or any(not isinstance(item, Mapping) for item in input_overrides)):
            issues.append({"reason": "input_reviewed_overrides_invalid"})
            input_override_match = False
        else:
            input_override_match = _override_payloads_match(
                input_overrides, plan_overrides)
            if not input_override_match:
                issues.append({"reason": "input_plan_override_mismatch"})

    status_sources = []
    for source_kind, document, path in (
            ("strike_plan", plan, report["files"]["strike_plan"]["path"]),
            ("strike_input", strike_input,
             report["files"]["strike_input"]["path"])):
        status = _document_review_status(document)
        if status is not None:
            status_sources.append({
                "kind": source_kind,
                "path": path,
                "status": status,
                "matched_overrides": True,
            })

    review_documents = []
    for path in sorted((bundle / "training").glob("strike_review*.json")):
        try:
            document = _json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            review_documents.append({
                "path": str(path.resolve()), "readable": False,
                "error": str(exc), "matched_overrides": False})
            continue
        document_overrides = document.get("reviewed_overrides")
        matched = (
            isinstance(document_overrides, list)
            and all(isinstance(item, Mapping) for item in document_overrides)
            and _override_sets_match(plan_overrides, document_overrides))
        status = _document_review_status(document)
        entry = {
            "path": str(path.resolve()),
            "readable": True,
            "schema": document.get("schema"),
            "status": status,
            "matched_overrides": matched,
        }
        review_documents.append(entry)
        if matched:
            status_sources.append({
                "kind": "separate_review_document",
                "path": str(path.resolve()),
                "status": status,
                "matched_overrides": True,
            })
            if not _override_payloads_match(
                    plan_overrides, document_overrides):
                issues.append({
                    "reason": "review_document_override_payload_mismatch",
                    "path": str(path.resolve()),
                })

    statuses = [
        item["status"] for item in status_sources
        if isinstance(item.get("status"), str) and item["status"].strip()]
    status_class = _review_status_class(statuses)
    unique_statuses = list(dict.fromkeys(statuses))
    top_level_status = (
        unique_statuses[0] if len(unique_statuses) == 1
        else unique_statuses if unique_statuses else None)
    report["reviewed_overrides"] = {
        "count": len(plan_overrides),
        "top_level_status": top_level_status,
        "status_class": status_class,
        "status_sources": status_sources,
        "review_documents": review_documents,
        "embedded_in_strike_input": input_overrides is not None,
        "input_plan_payload_match": input_override_match,
        "items": items,
        "issues": issues,
    }
    if issues:
        _add_finding(
            report, STATUS_INFEASIBLE, "reviewed_override_contract_invalid",
            "reviewed override provenance is inconsistent with raw input or plan",
            issue_count=len(issues), samples=issues[:10])
    if status_class == "rejected":
        _add_finding(
            report, STATUS_INFEASIBLE, "review_status_rejected",
            "StrikePlan applies a rejected reviewed override",
            top_level_status=top_level_status, sources=status_sources)
    elif status_class == "pending":
        _add_finding(
            report, STATUS_AMBIGUOUS, "review_status_pending",
            "StrikePlan applies an override whose top-level review is still "
            "proposed or pending",
            top_level_status=top_level_status, sources=status_sources)
    elif status_class == "unknown":
        _add_finding(
            report, STATUS_AMBIGUOUS, "review_status_missing_or_unknown",
            "StrikePlan applies a reviewed override without a single approved "
            "top-level review status",
            top_level_status=top_level_status, sources=status_sources)


def _jams_pitch(value: Any) -> Optional[float]:
    if isinstance(value, Mapping):
        for key in ("midi", "pitch", "value"):
            if key in value:
                return _finite_float(value[key])
        return None
    return _finite_float(value)


def _reference_notes(jams: Mapping[str, Any]) -> List[dict]:
    annotations = jams.get("annotations")
    if not isinstance(annotations, list):
        return []
    result = []
    for annotation_index, annotation in enumerate(annotations):
        if not isinstance(annotation, Mapping) or annotation.get("namespace") != "note_midi":
            continue
        metadata = annotation.get("annotation_metadata")
        source_string = metadata.get("data_source") if isinstance(metadata, Mapping) else None
        try:
            source_string = int(source_string)
        except (TypeError, ValueError):
            continue
        if not 0 <= source_string <= 5:
            continue
        data = annotation.get("data")
        if not isinstance(data, list):
            continue
        for data_index, item in enumerate(data):
            if not isinstance(item, Mapping):
                continue
            time_s = _finite_float(item.get("time"))
            pitch = _jams_pitch(item.get("value"))
            if time_s is None or pitch is None:
                continue
            result.append({
                "source_string": source_string,
                "time": time_s,
                "midi": pitch,
                "annotation_index": annotation_index,
                "data_index": data_index,
            })
    return result


def _match_reference_sequence(
        sources: Sequence[Tuple[int, Mapping[str, Any]]],
        references: Sequence[Mapping[str, Any]],
        config: AuditConfig) -> List[Tuple[int, int]]:
    n, m = len(sources), len(references)
    matches = [[0] * (m + 1) for _ in range(n + 1)]
    costs = [[0.0] * (m + 1) for _ in range(n + 1)]
    actions = [[""] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        actions[i][0] = "S"
    for j in range(1, m + 1):
        actions[0][j] = "R"

    window_s = config.reference_match_window_ms / 1000.0
    for i in range(1, n + 1):
        source = sources[i - 1][1]
        source_time = _finite_float(source.get("t_on"))
        source_pitch = _finite_float(source.get("midi"))
        for j in range(1, m + 1):
            reference = references[j - 1]
            candidates = [
                (matches[i - 1][j], costs[i - 1][j], 1, "S"),
                (matches[i][j - 1], costs[i][j - 1], 0, "R"),
            ]
            reference_time = _finite_float(reference.get("time"))
            reference_pitch = _finite_float(reference.get("midi"))
            pitch_ok = (
                source_pitch is None or reference_pitch is None
                or abs(source_pitch - reference_pitch)
                <= config.reference_pitch_tolerance)
            if (source_time is not None and reference_time is not None
                    and abs(source_time - reference_time) <= window_s
                    and pitch_ok):
                candidates.append((
                    matches[i - 1][j - 1] + 1,
                    costs[i - 1][j - 1] + abs(source_time - reference_time),
                    2, "M"))
            chosen = max(candidates, key=lambda item: (item[0], -item[1], item[2]))
            matches[i][j], costs[i][j], _, actions[i][j] = chosen

    result = []
    i, j = n, m
    while i > 0 or j > 0:
        action = actions[i][j]
        if action == "M":
            result.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif action == "S":
            i -= 1
        elif action == "R":
            j -= 1
        else:
            break
    result.reverse()
    return result


def _audit_reference_onsets(
        report: Dict[str, Any], notes: Sequence[Mapping[str, Any]],
        jams: Optional[Mapping[str, Any]], config: AuditConfig) -> None:
    if jams is None:
        report["reference_onsets"] = {
            "available": False,
            "reason": "source/annotation.jams is optional and was not found",
        }
        return
    references = _reference_notes(jams)
    if not references:
        report["reference_onsets"] = {
            "available": True,
            "reference_note_count": 0,
            "matched_count": 0,
            "unmatched_source_count": len(notes),
        }
        _add_finding(
            report, STATUS_AMBIGUOUS, "missing_note_midi_reference",
            "JAMS exists but contains no usable note_midi annotations")
        return

    sources_by_string = {string_index: [] for string_index in range(6)}
    references_by_string = {string_index: [] for string_index in range(6)}
    invalid_source_indices = []
    for source_index, note in enumerate(notes):
        if not isinstance(note, Mapping):
            invalid_source_indices.append(source_index)
            continue
        source_string = note.get("string")
        source_time = _finite_float(note.get("t_on"))
        if (not _integer(source_string) or not 0 <= source_string <= 5
                or source_time is None or source_time < 0.0):
            invalid_source_indices.append(source_index)
            continue
        sources_by_string[source_string].append((source_index, note))
    for reference in references:
        references_by_string[reference["source_string"]].append(reference)
    for values in sources_by_string.values():
        values.sort(key=lambda item: float(item[1].get("t_on", math.inf)))
    for values in references_by_string.values():
        values.sort(key=lambda item: item["time"])

    matched = []
    matched_source_indices = set()
    matched_reference_keys = set()
    for string_index in range(6):
        sources = sources_by_string[string_index]
        string_references = references_by_string[string_index]
        for source_local, reference_local in _match_reference_sequence(
                sources, string_references, config):
            source_index, note = sources[source_local]
            reference = string_references[reference_local]
            delta_s = float(note["t_on"]) - float(reference["time"])
            matched_source_indices.add(source_index)
            matched_reference_keys.add((
                reference["annotation_index"], reference["data_index"]))
            matched.append({
                "source_event_id": source_index,
                "source_string": string_index,
                "source_time_s": float(note["t_on"]),
                "reference_time_s": float(reference["time"]),
                "delta_ms": delta_s * 1000.0,
                "source_midi": note.get("midi"),
                "reference_midi": reference["midi"],
            })

    deltas_s = [item["delta_ms"] / 1000.0 for item in matched]
    large = [item for item in matched
             if abs(item["delta_ms"]) > config.reference_ambiguous_delta_ms]
    unmatched_sources = [
        index for index in range(len(notes))
        if index not in matched_source_indices]
    unmatched_reference_count = sum(
        (reference["annotation_index"], reference["data_index"])
        not in matched_reference_keys for reference in references)
    report["reference_onsets"] = {
        "available": True,
        "source_note_count": len(notes),
        "reference_note_count": len(references),
        "matched_count": len(matched),
        "unmatched_source_count": len(unmatched_sources),
        "unmatched_reference_count": unmatched_reference_count,
        "invalid_source_count": len(invalid_source_indices),
        "delta_summary": _summary_ms(deltas_s),
        "ambiguous_delta_threshold_ms": config.reference_ambiguous_delta_ms,
        "large_delta_count": len(large),
        "large_delta_samples": sorted(
            large, key=lambda item: abs(item["delta_ms"]), reverse=True)[:20],
        "unmatched_source_event_ids": unmatched_sources[:50],
    }
    if large or unmatched_sources or invalid_source_indices:
        _add_finding(
            report, STATUS_AMBIGUOUS, "source_reference_onset_ambiguity",
            "fingering onsets cannot all be aligned confidently to JAMS "
            "note_midi references",
            large_delta_count=len(large),
            unmatched_source_count=len(unmatched_sources),
            invalid_source_count=len(invalid_source_indices))


def _audit_grouping_boundaries(
        report: Dict[str, Any], raw_events: Sequence[Mapping[str, Any]],
        plan_events: Sequence[Mapping[str, Any]], raw_to_plan: Mapping[int, int],
        physical_gap_s: Optional[float], grouping_span_s: Optional[float],
        config: AuditConfig) -> None:
    if physical_gap_s is None:
        return
    margin_s = config.grouping_boundary_margin_ms / 1000.0
    plan_first_source_time = {}
    for plan_index, event in enumerate(plan_events):
        source_times = event.get("source_times_s") if isinstance(event, Mapping) else None
        if isinstance(source_times, list):
            finite = [_finite_float(value) for value in source_times]
            finite = [value for value in finite if value is not None]
            if finite:
                plan_first_source_time[plan_index] = min(finite)

    boundaries = []
    for source_index in range(len(raw_events) - 1):
        left, right = raw_events[source_index:source_index + 2]
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            continue
        left_time = _finite_float(left.get("time"))
        right_time = _finite_float(right.get("time"))
        if left_time is None or right_time is None:
            continue
        left_plan = raw_to_plan.get(source_index)
        right_plan = raw_to_plan.get(source_index + 1)
        if left_plan is None or right_plan is None:
            continue
        gap_s = right_time - left_time
        same_group = left_plan == right_plan
        reasons = []
        if not same_group and gap_s < physical_gap_s - config.numeric_epsilon_s:
            reasons.append("locally_below_physical_gap_but_split")
        if abs(gap_s - physical_gap_s) <= margin_s:
            reasons.append("adjacent_gap_near_grouping_threshold")
        prospective_span_s = None
        if not same_group and left_plan in plan_first_source_time:
            prospective_span_s = right_time - plan_first_source_time[left_plan]
            if (grouping_span_s is not None
                    and abs(prospective_span_s - grouping_span_s) <= margin_s):
                reasons.append("cluster_span_near_grouping_limit")
        if not reasons:
            continue
        boundaries.append({
            "left_source_event_id": source_index,
            "right_source_event_id": source_index + 1,
            "left_plan_event": left_plan,
            "right_plan_event": right_plan,
            "same_compiled_group": same_group,
            "left_time_s": left_time,
            "right_time_s": right_time,
            "adjacent_gap_ms": gap_s * 1000.0,
            "physical_gap_ms": physical_gap_s * 1000.0,
            "prospective_cluster_span_ms": (
                prospective_span_s * 1000.0
                if prospective_span_s is not None else None),
            "grouping_max_span_ms": (
                grouping_span_s * 1000.0
                if grouping_span_s is not None else None),
            "reasons": reasons,
        })
    report["ambiguous_grouping_boundaries"] = boundaries
    if boundaries:
        _add_finding(
            report, STATUS_AMBIGUOUS, "ambiguous_grouping_boundary",
            "one or more adjacent raw events sit on conflicting or unstable "
            "single/strum grouping boundaries",
            count=len(boundaries), samples=boundaries[:5])


def _has_explicit_span_provenance(event: Mapping[str, Any]) -> bool:
    keys = (
        "mute_provenance", "span_provenance",
        "protected_string_provenance", "explicit_muted_strings",
        "explicit_span", "mute_source_event_ids", "span_source_event_ids",
    )
    if any(event.get(key) not in (None, False, "", [], {}) for key in keys):
        return True
    provenance = event.get("provenance")
    return isinstance(provenance, Mapping) and any(
        provenance.get(key) not in (None, False, "", [], {}) for key in keys)


def _audit_noncontiguous_strums(
        report: Dict[str, Any], plan_events: Sequence[Mapping[str, Any]]) -> None:
    ambiguous = []
    for plan_index, event in enumerate(plan_events):
        if not isinstance(event, Mapping) or event.get("gesture") != "strum":
            continue
        audible = event.get("strings")
        traversal = event.get("traversal_strings")
        if not isinstance(audible, list) or not audible:
            continue
        if any(not _integer(value) for value in audible):
            continue
        span = list(range(min(audible), max(audible) + 1))
        inferred = [value for value in span if value not in audible]
        if not inferred or _has_explicit_span_provenance(event):
            continue
        ambiguous.append({
            "plan_event": plan_index,
            "time_s": event.get("time"),
            "direction": event.get("direction"),
            "audible_strings": audible,
            "traversal_strings": traversal,
            "inferred_intermediate_strings": inferred,
            "protected_strings": event.get("protected_strings", []),
            "source_event_ids": event.get("source_event_ids", []),
            "explicit_mute_or_span_provenance": False,
        })
    report["noncontiguous_inferred_strums"] = ambiguous
    if ambiguous:
        _add_finding(
            report, STATUS_AMBIGUOUS,
            "noncontiguous_strum_without_provenance",
            "noncontiguous audible endpoints were expanded through silent "
            "strings without explicit mute/span provenance",
            count=len(ambiguous), samples=ambiguous[:5])


def _physical_and_grouping_gaps(
        report: Dict[str, Any], plan: Mapping[str, Any],
        ) -> Tuple[Optional[float], Optional[float]]:
    timeline = plan.get("timeline")
    physical = (
        _finite_float(timeline.get("physical_min_gap_s"))
        if isinstance(timeline, Mapping) else None)
    metadata = plan.get("metadata")
    planner = metadata.get("planner_config") if isinstance(metadata, Mapping) else None
    grouping = (
        _finite_float(planner.get("grouping_max_span_s"))
        if isinstance(planner, Mapping) else None)
    if physical is None or physical <= 0.0:
        _add_finding(
            report, STATUS_AMBIGUOUS, "missing_physical_gap_contract",
            "StrikePlan does not provide a positive timeline.physical_min_gap_s")
        physical = None
    if grouping is not None and grouping <= 0.0:
        grouping = None
    return physical, grouping


def _audit_traversal_edges(
        report: Dict[str, Any], plan_events: Sequence[Mapping[str, Any]],
        physical_gap_s: Optional[float], config: AuditConfig) -> List[dict]:
    edges = []
    near_count = 0
    below_count = 0
    margin_s = config.edge_gap_margin_ms / 1000.0
    for current_index in range(1, len(plan_events)):
        previous = plan_events[current_index - 1]
        current = plan_events[current_index]
        if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
            continue
        previous_time = _finite_float(previous.get("time"))
        current_time = _finite_float(current.get("time"))
        previous_offsets = _event_offsets(previous)
        current_offsets = _event_offsets(current)
        if (previous_time is None or current_time is None
                or not previous_offsets or not current_offsets):
            continue
        previous_edge = previous_time + max(previous_offsets)
        current_edge = current_time + min(current_offsets)
        edge_gap_s = current_edge - previous_edge
        below = (
            physical_gap_s is not None
            and edge_gap_s < physical_gap_s - config.numeric_epsilon_s)
        near = (
            physical_gap_s is not None and not below
            and edge_gap_s <= physical_gap_s + margin_s)
        below_count += int(below)
        near_count += int(near)
        edge = {
            "previous_plan_event": current_index - 1,
            "current_plan_event": current_index,
            "previous_source_event_ids": previous.get("source_event_ids", []),
            "current_source_event_ids": current.get("source_event_ids", []),
            "previous_last_edge_time_s": previous_edge,
            "current_first_edge_time_s": current_edge,
            "center_gap_ms": (current_time - previous_time) * 1000.0,
            "actual_edge_gap_ms": edge_gap_s * 1000.0,
            "physical_min_gap_ms": (
                physical_gap_s * 1000.0 if physical_gap_s is not None else None),
            "deficit_ms": (
                max(0.0, physical_gap_s - edge_gap_s) * 1000.0
                if physical_gap_s is not None else None),
            "below_physical_minimum": below,
            "near_physical_minimum": near,
        }
        edges.append(edge)
        if below:
            _add_finding(
                report, STATUS_INFEASIBLE,
                "traversal_edge_gap_below_physical",
                f"plan events {current_index - 1}->{current_index} leave "
                f"{edge_gap_s * 1000.0:.3f} ms between actual string edges, "
                f"below the {physical_gap_s * 1000.0:.3f} ms contract",
                **edge)
        elif near:
            _add_finding(
                report, STATUS_AMBIGUOUS,
                "traversal_edge_gap_near_physical",
                f"plan events {current_index - 1}->{current_index} have only "
                f"{edge_gap_s * 1000.0:.3f} ms between actual string edges",
                **edge)
    report["traversal_edge_gaps"] = {
        "physical_min_gap_ms": (
            physical_gap_s * 1000.0 if physical_gap_s is not None else None),
        "minimum_actual_edge_gap_ms": (
            min(edge["actual_edge_gap_ms"] for edge in edges)
            if edges else None),
        "edges": edges,
        "below_physical_count": below_count,
        "near_physical_count": near_count,
    }
    return edges


def _audit_reversal_direct_paths(
        report: Dict[str, Any], plan_events: Sequence[Mapping[str, Any]],
        edges: Sequence[Mapping[str, Any]], physical_gap_s: Optional[float],
        config: AuditConfig) -> None:
    edge_by_current = {
        edge["current_plan_event"]: edge for edge in edges}
    records = []
    margin_s = config.edge_gap_margin_ms / 1000.0
    for current_index in range(1, len(plan_events)):
        previous = plan_events[current_index - 1]
        current = plan_events[current_index]
        if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
            continue
        previous_path = previous.get("traversal_strings")
        current_path = current.get("traversal_strings")
        if (not isinstance(previous_path, list) or not previous_path
                or not isinstance(current_path, list) or not current_path):
            continue
        previous_exit = previous_path[-1]
        current_entry = current_path[0]
        if not _integer(previous_exit) or not _integer(current_entry):
            continue
        previous_direction = previous.get("direction")
        current_direction = current.get("direction")
        reversal = previous_direction != current_direction
        current_step = -1 if current_direction == "down" else 1 if current_direction == "up" else 0
        direct_crossings = []
        if current_step:
            displacement = current_entry - previous_exit
            if displacement == 0 and reversal:
                direct_crossings = [previous_exit]
            elif displacement * current_step > 0:
                start = previous_exit if reversal else previous_exit + current_step
                direct_crossings = list(range(start, current_entry, current_step))
        if not reversal and not direct_crossings:
            continue
        rearm_strings = [
            value for value in direct_crossings if value in previous_path]
        edge = edge_by_current.get(current_index, {})
        edge_gap_ms = edge.get("actual_edge_gap_ms")
        risk = "monitor"
        if direct_crossings and physical_gap_s is not None and edge_gap_ms is not None:
            edge_gap_s = float(edge_gap_ms) / 1000.0
            if edge_gap_s < physical_gap_s - config.numeric_epsilon_s:
                risk = "infeasible"
            elif edge_gap_s <= physical_gap_s + margin_s:
                risk = "ambiguous"
        record = {
            "previous_plan_event": current_index - 1,
            "current_plan_event": current_index,
            "previous_source_event_ids": previous.get("source_event_ids", []),
            "current_source_event_ids": current.get("source_event_ids", []),
            "previous_direction": previous_direction,
            "current_direction": current_direction,
            "direction_reversal": reversal,
            "previous_exit_string": previous_exit,
            "current_entry_string": current_entry,
            "direct_path_intermediate_crossings": direct_crossings,
            "previously_crossed_strings_requiring_rearm": rearm_strings,
            "clear_reset_required": not bool(direct_crossings),
            "actual_edge_gap_ms": edge_gap_ms,
            "risk": risk,
        }
        records.append(record)
        if risk == "ambiguous":
            _add_finding(
                report, STATUS_AMBIGUOUS,
                "reversal_direct_path_rearm_risk",
                f"plan events {current_index - 1}->{current_index} require a "
                "direct-path crossing near the detector re-arm limit",
                **record)
    report["reversal_direct_paths"] = records


def audit_bundle(
        bundle: Path, config: Optional[AuditConfig] = None) -> Dict[str, Any]:
    config = (config or AuditConfig()).validate()
    bundle = Path(bundle).resolve()
    report = _empty_bundle_report(bundle)
    required = ("fingering", "strike_input", "strike_plan")
    missing = [name for name in required if not report["files"][name]["exists"]]
    if missing:
        _add_finding(
            report, STATUS_AMBIGUOUS, "missing_strike_artifact",
            "bundle is not fully compiled and cannot be audited end-to-end",
            missing=missing)

    documents = {}
    for name in required:
        if not report["files"][name]["exists"]:
            continue
        path = Path(report["files"][name]["path"])
        try:
            documents[name] = _json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _add_finding(
                report, STATUS_INFEASIBLE, "unreadable_strike_artifact",
                f"cannot read {name}: {exc}", path=str(path))

    jams = None
    if report["files"]["reference_jams"]["exists"]:
        path = Path(report["files"]["reference_jams"]["path"])
        try:
            jams = _json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _add_finding(
                report, STATUS_AMBIGUOUS, "unreadable_reference_jams",
                f"optional JAMS reference cannot be read: {exc}", path=str(path))

    if any(name not in documents for name in required):
        fingering = documents.get("fingering", {})
        notes = fingering.get("notes") if isinstance(fingering, Mapping) else None
        notes = notes if isinstance(notes, list) else []
        strike_events = documents.get("strike_input", {}).get("events", [])
        plan_events = documents.get("strike_plan", {}).get("events", [])
        _audit_reference_onsets(report, notes, jams, config)
        report["counts"] = {
            "fingering_notes": len(notes),
            "strike_input_events": (
                len(strike_events) if isinstance(strike_events, list) else 0),
            "compiled_plan_events": (
                len(plan_events) if isinstance(plan_events, list) else 0),
            "single_pick_events": 0,
            "strum_events": 0,
        }
        return _finalize_bundle(report)

    strike_input = documents["strike_input"]
    plan = documents["strike_plan"]
    input_metadata = strike_input.get("metadata")
    plan_metadata = plan.get("metadata")
    fps_value = (
        input_metadata.get("fps") if isinstance(input_metadata, Mapping)
        else None)
    plan_fps = (
        plan_metadata.get("fps") if isinstance(plan_metadata, Mapping)
        else None)
    if not _integer(fps_value) or fps_value <= 0:
        _add_finding(
            report, STATUS_INFEASIBLE, "invalid_input_fps",
            "strike input metadata.fps must be a positive integer")
        fps = 60
    else:
        fps = fps_value
    if plan_fps != fps:
        _add_finding(
            report, STATUS_INFEASIBLE, "input_plan_fps_mismatch",
            "strike input and StrikePlan fps values differ",
            strike_input_fps=fps, strike_plan_fps=plan_fps)

    notes, raw_events = _audit_fingering_to_input(
        report, documents["fingering"], strike_input, fps, config)
    plan_events, raw_to_plan = _audit_plan_consistency(
        report, raw_events, plan, fps, config)
    _audit_reviewed_overrides(
        report, bundle, strike_input, plan, raw_events, plan_events,
        raw_to_plan, config)
    _audit_reference_onsets(report, notes, jams, config)
    physical_gap_s, grouping_span_s = _physical_and_grouping_gaps(report, plan)
    _audit_grouping_boundaries(
        report, raw_events, plan_events, raw_to_plan,
        physical_gap_s, grouping_span_s, config)
    _audit_noncontiguous_strums(report, plan_events)
    edges = _audit_traversal_edges(
        report, plan_events, physical_gap_s, config)
    _audit_reversal_direct_paths(
        report, plan_events, edges, physical_gap_s, config)
    report["counts"] = {
        "fingering_notes": len(notes),
        "strike_input_events": len(raw_events),
        "compiled_plan_events": len(plan_events),
        "single_pick_events": sum(
            event.get("gesture") == "single_pick"
            for event in plan_events if isinstance(event, Mapping)),
        "strum_events": sum(
            event.get("gesture") == "strum"
            for event in plan_events if isinstance(event, Mapping)),
    }
    return _finalize_bundle(report)


def audit_bundles(
        bundles: Iterable[Path], config: Optional[AuditConfig] = None,
        root: Optional[Path] = None) -> Dict[str, Any]:
    config = (config or AuditConfig()).validate()
    reports = [audit_bundle(Path(bundle), config) for bundle in bundles]
    counts = Counter(report["status"] for report in reports)
    overall = max(
        (report["status"] for report in reports),
        key=lambda value: STATUS_RANK[value], default=STATUS_PASS)
    return {
        "schema": AUDIT_SCHEMA,
        "root": str(Path(root).resolve()) if root is not None else None,
        "config": asdict(config),
        "summary": {
            "bundle_count": len(reports),
            "status_counts": {
                status: counts.get(status, 0)
                for status in (STATUS_PASS, STATUS_AMBIGUOUS, STATUS_INFEASIBLE)
            },
            "overall_status": overall,
        },
        "bundles": reports,
    }


def render_human(document: Mapping[str, Any]) -> str:
    summary = document["summary"]
    lines = [
        "Strike goal quality audit",
        f"Overall: {summary['overall_status']} "
        f"({summary['bundle_count']} bundle(s))",
    ]
    counts = summary["status_counts"]
    lines.append(
        "Status counts: " + ", ".join(
            f"{status}={counts[status]}"
            for status in (STATUS_PASS, STATUS_AMBIGUOUS, STATUS_INFEASIBLE)))
    for report in document["bundles"]:
        bundle_counts = report.get("counts", {})
        lines.extend(["", f"[{report['status']}] {report['song_id']}",
                      f"  {report['bundle']}"])
        if bundle_counts:
            lines.append(
                "  events: fingering={fingering_notes}, raw={strike_input_events}, "
                "plan={compiled_plan_events}, strum={strum_events}".format(
                    **bundle_counts))
        review = report.get("reviewed_overrides", {})
        if review.get("count"):
            lines.append(
                f"  reviewed overrides: count={review['count']}, "
                f"status={review.get('top_level_status')}, "
                f"class={review.get('status_class')}")
            for item in review.get("items", []):
                evidence = item.get("evidence")
                evidence_keys = (
                    sorted(evidence) if isinstance(evidence, Mapping) else [])
                lines.append(
                    f"    {item.get('override_id')} {item.get('action')} "
                    f"sources={item.get('source_event_ids')}: "
                    f"{item.get('reason')} (evidence={evidence_keys})")
        reference = report.get("reference_onsets", {})
        if reference.get("available") and "matched_count" in reference:
            delta = reference.get("delta_summary", {})
            maximum = delta.get("absolute_max_ms")
            maximum_text = "n/a" if maximum is None else f"{maximum:.3f} ms"
            lines.append(
                f"  JAMS onset matches: {reference['matched_count']}/"
                f"{reference.get('source_note_count', 0)}, "
                f"max |delta|={maximum_text}")
        edge = report.get("traversal_edge_gaps", {})
        minimum = edge.get("minimum_actual_edge_gap_ms")
        if minimum is not None:
            lines.append(
                f"  actual edge gap: min={minimum:.3f} ms, "
                f"below={edge['below_physical_count']}, "
                f"near={edge['near_physical_count']}")
        lines.append(
            f"  grouping ambiguity={len(report.get('ambiguous_grouping_boundaries', []))}, "
            f"unproven inferred strum={len(report.get('noncontiguous_inferred_strums', []))}, "
            f"reversal/direct-path records={len(report.get('reversal_direct_paths', []))}")
        for finding in report.get("findings", []):
            lines.append(
                f"  - {finding['severity']} {finding['category']}: "
                f"{finding['message']}")
    return "\n".join(lines)


def render_output(document: Mapping[str, Any], output_format: str) -> str:
    if output_format == "human":
        return render_human(document) + "\n"
    json_text = json.dumps(
        document, indent=2, ensure_ascii=False, allow_nan=False)
    if output_format == "json":
        return json_text + "\n"
    if output_format == "both":
        return render_human(document) + "\n\nJSON\n" + json_text + "\n"
    raise ValueError(f"unsupported output format: {output_format}")


def _write_text_atomic(path: Path, value: str) -> Path:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp",
                delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[2]
    default_root = project_root / "data" / "song_bundles"
    parser = argparse.ArgumentParser(
        description="audit fingering -> strike input -> StrikePlan quality "
        "without importing Isaac Gym or torch")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--bundle", type=Path)
    target.add_argument("--all", action="store_true")
    parser.add_argument(
        "--song-bundles-root", type=Path, default=default_root)
    parser.add_argument(
        "--format", choices=("human", "json", "both"), default="human")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--reference-match-window-ms", type=float, default=250.0)
    parser.add_argument(
        "--reference-ambiguous-delta-ms", type=float, default=50.0)
    parser.add_argument("--reference-pitch-tolerance", type=float, default=1.0)
    parser.add_argument("--grouping-boundary-margin-ms", type=float, default=5.0)
    parser.add_argument("--edge-gap-margin-ms", type=float, default=5.0)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config = AuditConfig(
        reference_match_window_ms=args.reference_match_window_ms,
        reference_ambiguous_delta_ms=args.reference_ambiguous_delta_ms,
        reference_pitch_tolerance=args.reference_pitch_tolerance,
        grouping_boundary_margin_ms=args.grouping_boundary_margin_ms,
        edge_gap_margin_ms=args.edge_gap_margin_ms,
    ).validate()
    root = args.song_bundles_root.resolve()
    if args.all:
        if not root.is_dir():
            raise FileNotFoundError(f"song bundle root does not exist: {root}")
        bundles = sorted(path for path in root.iterdir() if path.is_dir())
    else:
        bundles = [args.bundle.resolve()]
    document = audit_bundles(bundles, config=config, root=root)
    output = render_output(document, args.format)
    print(output, end="")
    if args.out is not None:
        _write_text_atomic(args.out, output)
    if args.strict and document["summary"]["overall_status"] == STATUS_INFEASIBLE:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
