"""Raw strike document validation, without the retired tensor runtime."""
from __future__ import annotations

import math
from typing import Any, Mapping

from ._strike_goal_compiler import normalize_reviewed_strike_overrides


STRIKE_TRAINING_SCHEMA_V1 = "tab2body.strike_training.v1"
STRIKE_TRAINING_SCHEMA_V2 = "tab2body.strike_training.v2"
STRIKE_TRAINING_SCHEMA_V3 = "tab2body.strike_training.v3"
STRIKE_TRAINING_SCHEMA = STRIKE_TRAINING_SCHEMA_V3
STRIKE_FPS = 60
N_GUITAR_STRINGS = 6
MAX_FRAME_ERROR = 0.5

_REQUIRED_EVENT_FIELDS = frozenset(("time", "frame", "string"))
_OPTIONAL_EVENT_FIELDS_V1_V2 = frozenset(("event_id",))
_OPTIONAL_EVENT_FIELDS_V3 = frozenset((
    "event_id", "source_time", "time_uncertainty_s", "source_ref"))


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _validate_event_id(value: Any, event_index: int) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(
            f"strike event {event_index}: event_id must be an integer or string")
    if isinstance(value, str) and not value:
        raise ValueError(
            f"strike event {event_index}: event_id must not be empty")
    return value


def validate_strike_training_data(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and summarize a raw strike-training document.

    Event objects are intentionally closed: their key set must be exactly
    v1/v2 retain the closed ``time/frame/string`` plus optional ``event_id``
    contract. v3 adds optional source-time provenance and reviewed grouping
    evidence without changing those required controller inputs.
    """
    if not isinstance(document, Mapping):
        raise ValueError("strike training document must be an object")
    schema = document.get("schema")
    if schema not in (
            STRIKE_TRAINING_SCHEMA_V1, STRIKE_TRAINING_SCHEMA_V2,
            STRIKE_TRAINING_SCHEMA_V3):
        raise ValueError(
            f"unsupported strike training schema: {document.get('schema')!r}")

    metadata = document.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("strike training metadata must be an object")
    fps = metadata.get("fps")
    if not _is_integer(fps):
        raise ValueError("strike training metadata.fps must be an integer")
    if fps != STRIKE_FPS:
        raise ValueError(
            f"physics/strike clock mismatch: expected {STRIKE_FPS} Hz, got {fps}")

    events = document.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("strike training events must be a non-empty array")

    previous_time = None
    previous_frame = None
    seen_event_ids = set()
    max_error_frames = 0.0
    used_strings = set()
    last_frame_by_string = {}
    last_time_by_string = {}
    minimum_same_string_restrike_frames = None
    minimum_same_string_restrike_s = None
    minimum_event_gap_s = None
    minimum_event_gap_frames = None
    timing_uncertainties = []
    source_time_count = 0
    source_ref_count = 0
    for event_index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise ValueError(f"strike event {event_index}: event must be an object")
        fields = frozenset(event)
        missing = sorted(_REQUIRED_EVENT_FIELDS - fields)
        optional_fields = (
            _OPTIONAL_EVENT_FIELDS_V3
            if schema == STRIKE_TRAINING_SCHEMA_V3
            else _OPTIONAL_EVENT_FIELDS_V1_V2)
        unknown = sorted(fields - _REQUIRED_EVENT_FIELDS - optional_fields)
        if missing or unknown:
            raise ValueError(
                f"strike event {event_index}: exact fields are time/frame/string "
                f"with schema-defined provenance; missing={missing}, "
                f"unknown={unknown}")

        time_s = event["time"]
        frame = event["frame"]
        string_index = event["string"]
        if not _is_finite_number(time_s) or float(time_s) < 0.0:
            raise ValueError(
                f"strike event {event_index}: time must be finite and non-negative")
        if not _is_integer(frame) or frame < 0:
            raise ValueError(
                f"strike event {event_index}: frame must be a non-negative integer")
        if (not _is_integer(string_index)
                or not 0 <= string_index < N_GUITAR_STRINGS):
            raise ValueError(
                f"strike event {event_index}: string must use Isaac order 0..5")

        time_s = float(time_s)
        error_frames = abs(time_s * fps - frame)


        if error_frames > MAX_FRAME_ERROR + 1e-9:
            raise ValueError(
                f"strike event {event_index}: time/frame mismatch is "
                f"{error_frames:.9f} frame, above the {MAX_FRAME_ERROR}-frame limit")

        if (previous_time is not None
                and schema == STRIKE_TRAINING_SCHEMA_V1
                and time_s <= previous_time):
            raise ValueError(
                "pick_monophonic_v1 requires strictly increasing event time; "
                f"event {event_index} has time={time_s} after {previous_time}")
        if previous_time is not None:
            if time_s < previous_time:
                raise ValueError(
                    f"strike event time must be non-decreasing; event "
                    f"{event_index} has time={time_s} after {previous_time}")
            gap_s = time_s - previous_time
            minimum_event_gap_s = (
                gap_s if minimum_event_gap_s is None
                else min(minimum_event_gap_s, gap_s))
        if (previous_frame is not None
                and schema == STRIKE_TRAINING_SCHEMA_V1
                and frame <= previous_frame):
            raise ValueError(
                "pick_monophonic_v1 allows at most one strike per 60 Hz frame; "
                f"event {event_index} has frame={frame} after {previous_frame}")
        if previous_frame is not None:
            if frame < previous_frame:
                raise ValueError(
                    f"strike event frame must be non-decreasing; event "
                    f"{event_index} has frame={frame} after {previous_frame}")
            gap_frames = frame - previous_frame
            minimum_event_gap_frames = (
                gap_frames if minimum_event_gap_frames is None
                else min(minimum_event_gap_frames, gap_frames))

        if "event_id" in event:
            event_id = _validate_event_id(event["event_id"], event_index)
            if event_id in seen_event_ids:
                raise ValueError(
                    f"strike event {event_index}: duplicate event_id {event_id!r}")
            seen_event_ids.add(event_id)

        if "source_time" in event:
            source_time = event["source_time"]
            if not _is_finite_number(source_time) or float(source_time) < 0.0:
                raise ValueError(
                    f"strike event {event_index}: source_time must be finite "
                    "and non-negative")
            source_time_count += 1
        if "time_uncertainty_s" in event:
            uncertainty = event["time_uncertainty_s"]
            if not _is_finite_number(uncertainty) or float(uncertainty) < 0.0:
                raise ValueError(
                    f"strike event {event_index}: time_uncertainty_s must be "
                    "finite and non-negative")
            timing_uncertainties.append(float(uncertainty))
        if "source_ref" in event:
            source_ref = event["source_ref"]
            if (isinstance(source_ref, bool)
                    or not isinstance(source_ref, (int, str))
                    or isinstance(source_ref, str) and not source_ref):
                raise ValueError(
                    f"strike event {event_index}: source_ref must be a "
                    "non-empty string or integer")
            source_ref_count += 1

        previous_time = time_s
        previous_frame = frame
        if string_index in last_frame_by_string:
            spacing = frame - last_frame_by_string[string_index]
            minimum_same_string_restrike_frames = (
                spacing if minimum_same_string_restrike_frames is None
                else min(minimum_same_string_restrike_frames, spacing))
            spacing_s = time_s - last_time_by_string[string_index]
            minimum_same_string_restrike_s = (
                spacing_s if minimum_same_string_restrike_s is None
                else min(minimum_same_string_restrike_s, spacing_s))
        last_frame_by_string[string_index] = frame
        last_time_by_string[string_index] = time_s
        max_error_frames = max(max_error_frames, error_frames)
        used_strings.add(string_index)

    raw_overrides = document.get("reviewed_overrides", ())
    if raw_overrides and schema != STRIKE_TRAINING_SCHEMA_V3:
        raise ValueError(
            "reviewed_overrides require tab2body.strike_training.v3")
    reviewed_overrides = normalize_reviewed_strike_overrides(
        events, raw_overrides)
    return {
        "contract_valid": True,
        "schema": schema,
        "profile": (
            "pick_monophonic_v1"
            if schema == STRIKE_TRAINING_SCHEMA_V1
            else ("pick_gesture_compiler_v2"
                  if schema == STRIKE_TRAINING_SCHEMA_V2
                  else "pick_gesture_compiler_v3")),
        "fps": fps,
        "time_authority": "events[].time",
        "string_convention": "Isaac 0=high-e, 5=low-E",
        "num_events": len(events),
        "n_frames": int(events[-1]["frame"]) + 1,
        "used_strings": sorted(used_strings),
        "minimum_same_string_restrike_frames":
            minimum_same_string_restrike_frames,
        "minimum_same_string_restrike_s":
            minimum_same_string_restrike_s,
        "minimum_event_gap_s": minimum_event_gap_s,
        "minimum_event_gap_frames": minimum_event_gap_frames,
        "max_time_frame_error_frames": float(max_error_frames),
        "max_time_frame_error_seconds": float(max_error_frames / fps),
        "source_time_count": source_time_count,
        "source_ref_count": source_ref_count,
        "maximum_time_uncertainty_s": max(timing_uncertainties, default=0.0),
        "reviewed_override_count": len(reviewed_overrides),
    }

