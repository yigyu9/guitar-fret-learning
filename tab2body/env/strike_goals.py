from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import torch

from .strike_goal_compiler import (
    GESTURE_ALTERNATE_RESTRIKE,
    GESTURE_SINGLE_PICK,
    GESTURE_STRUM,
    compile_strike_events,
)


STRIKE_TRAINING_SCHEMA_V1 = "tab2body.strike_training.v1"
STRIKE_TRAINING_SCHEMA_V2 = "tab2body.strike_training.v2"
STRIKE_TRAINING_SCHEMA = STRIKE_TRAINING_SCHEMA_V2
STRIKE_FPS = 60
N_GUITAR_STRINGS = 6
MAX_FRAME_ERROR = 0.5

_REQUIRED_EVENT_FIELDS = frozenset(("time", "frame", "string"))
_OPTIONAL_EVENT_FIELDS = frozenset(("event_id",))


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
    """Validate and summarize a ``tab2body.strike_training.v1`` document.

    Event objects are intentionally closed: their key set must be exactly
    ``time/frame/string`` with only an optional ``event_id``. The Isaac string
    convention is fixed to index 0=high-e through index 5=low-E.
    """
    if not isinstance(document, Mapping):
        raise ValueError("strike training document must be an object")
    schema = document.get("schema")
    if schema not in (STRIKE_TRAINING_SCHEMA_V1, STRIKE_TRAINING_SCHEMA_V2):
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
    for event_index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise ValueError(f"strike event {event_index}: event must be an object")
        fields = frozenset(event)
        missing = sorted(_REQUIRED_EVENT_FIELDS - fields)
        unknown = sorted(fields - _REQUIRED_EVENT_FIELDS - _OPTIONAL_EVENT_FIELDS)
        if missing or unknown:
            raise ValueError(
                f"strike event {event_index}: exact fields are time/frame/string "
                f"with optional event_id; missing={missing}, unknown={unknown}")

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

    return {
        "contract_valid": True,
        "schema": schema,
        "profile": (
            "pick_monophonic_v1"
            if schema == STRIKE_TRAINING_SCHEMA_V1
            else "pick_gesture_compiler_v2"),
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
    }


class StrikeGoalSequence:
    """Validated immutable strike event tensors for one fixed input sequence.

    Episode progress, target matching and random-start state belong to
    :class:`StrikeTask`; this class only owns the canonical event timeline.
    """

    def __init__(
            self, path, device="cpu", *, rearm_min_frames=2,
            follow_through_min_frames=1,
            initial_timing_tolerance_ms=100,
            window_fraction=0.45):
        self.path = str(Path(path).resolve())
        document = json.loads(Path(self.path).read_text(encoding="utf-8"))
        self.validation_metadata = validate_strike_training_data(document)
        self.metadata = dict(document["metadata"])
        self.fps = int(self.validation_metadata["fps"])

        source_events = document["events"]
        self.compiled = compile_strike_events(
            source_events,
            fps=self.fps,
            rearm_min_frames=rearm_min_frames,
            follow_through_min_frames=follow_through_min_frames,
            initial_timing_tolerance_ms=initial_timing_tolerance_ms,
            window_fraction=window_fraction)
        events = self.compiled.events
        self.time = torch.tensor(
            self.compiled.original_times_s,
            dtype=torch.float32, device=device)
        self.easy_time = torch.tensor(
            self.compiled.easy_times_s,
            dtype=torch.float32, device=device)
        self.frame = torch.tensor(
            [event.frame for event in events],
            dtype=torch.long, device=device)
        self.string = torch.tensor(
            [event.traversal_strings[0] for event in events],
            dtype=torch.long, device=device)
        self.exit_string = torch.tensor(
            [event.traversal_strings[-1] for event in events],
            dtype=torch.long, device=device)
        gesture_codes = {
            GESTURE_SINGLE_PICK: 0,
            GESTURE_STRUM: 1,
            GESTURE_ALTERNATE_RESTRIKE: 2,
        }
        self.gesture = torch.tensor(
            [gesture_codes[event.gesture] for event in events],
            dtype=torch.long, device=device)
        self.direction = torch.tensor(
            [event.direction for event in events],
            dtype=torch.long, device=device)
        self.audible_mask = torch.tensor([
            [string_index in event.audible_strings
             for string_index in range(N_GUITAR_STRINGS)]
            for event in events], dtype=torch.bool, device=device)
        self.traversal_mask = torch.tensor([
            [string_index in event.traversal_strings
             for string_index in range(N_GUITAR_STRINGS)]
            for event in events], dtype=torch.bool, device=device)
        self.protected_mask = torch.tensor([
            [string_index in event.protected_strings
             for string_index in range(N_GUITAR_STRINGS)]
            for event in events], dtype=torch.bool, device=device)
        self.event_ids = tuple(event.source_event_ids for event in events)
        self.source_num_events = len(source_events)

        self.event_time_s = self.time
        self.event_frame = self.frame
        self.event_string = self.string
        self.events = {
            "time": self.time,
            "easy_time": self.easy_time,
            "frame": self.frame,
            "string": self.string,
            "exit_string": self.exit_string,
            "gesture": self.gesture,
            "direction": self.direction,
            "audible_mask": self.audible_mask,
            "traversal_mask": self.traversal_mask,
            "protected_mask": self.protected_mask,
        }
        self.num_events = len(events)
        self.n_events = self.num_events
        self.n_frames = int(self.validation_metadata["n_frames"])
        self.validation_metadata.update({
            "source_num_events": self.source_num_events,
            "compiled_num_events": self.num_events,
            "single_pick_events": sum(
                event.gesture == GESTURE_SINGLE_PICK for event in events),
            "strum_events": sum(
                event.gesture == GESTURE_STRUM for event in events),
            "unsupported_alternate_restrike_events": len(
                self.compiled.unsupported_events),
            "physical_min_gap_s": self.compiled.physical_min_gap_s,
            "easy_matching_gap_s": self.compiled.matching_gap_s,
            "window_fraction": self.compiled.window_fraction,
            "easy_timeline": self.compiled.gap_diagnostics(
                0.0, initial_timing_tolerance_ms),
            "original_timeline": self.compiled.gap_diagnostics(
                1.0, initial_timing_tolerance_ms),
        })

    def gap_diagnostics(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> dict[str, float | int | None]:
        return dict(self.compiled.gap_diagnostics(
            tempo_lambda, timing_tolerance_ms))

    def runtime_time(self, tempo_lambda: float) -> torch.Tensor:
        value = float(tempo_lambda)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("tempo_lambda must be finite and in [0, 1]")
        return self.time + (1.0 - value) * (self.easy_time - self.time)

    def runtime_windows(
            self, tempo_lambda: float,
            timing_tolerance_ms: float) -> tuple[torch.Tensor, torch.Tensor]:
        left, right = self.compiled.event_windows(
            tempo_lambda, timing_tolerance_ms)
        return (
            torch.tensor(left, dtype=self.time.dtype, device=self.time.device),
            torch.tensor(right, dtype=self.time.dtype, device=self.time.device),
        )

    def require_supported_gestures(self) -> None:
        unsupported = self.compiled.unsupported_events
        if not unsupported:
            return
        first = unsupported[0]
        raise ValueError(
            "strike goal requires alternate same-string restrike, but the "
            "current down-pick controller supports only single_pick and strum; "
            f"first unsupported source events={first.source_event_ids!r}")

    def require_physical_rearm_spacing(self, rearm_min_frames: int) -> None:
        """Reject a timeline that the configured same-string detector cannot emit."""
        if (isinstance(rearm_min_frames, bool)
                or int(rearm_min_frames) != rearm_min_frames
                or rearm_min_frames < 1):
            raise ValueError("rearm_min_frames must be a positive integer")


        required_delta = int(rearm_min_frames) + 1
        actual_s = self.validation_metadata[
            "minimum_same_string_restrike_s"]
        actual_frames = (
            None if actual_s is None else actual_s * self.fps)
        if (actual_frames is not None
                and actual_frames + 1e-9 < required_delta):
            raise ValueError(
                "strike goal contains a same-string restrike only "
                f"{actual_frames:g} frames later, but detector re-arm requires at "
                f"least {required_delta} frames")

    def require_nonoverlapping_match_windows(
            self, timing_tolerance_ms: float) -> None:
        """Reject ordered events whose symmetric match windows overlap.

        The v1 matcher owns only the current event.  Until a multi-event
        ordered matcher exists, overlapping adjacent windows could consume a
        valid next-string release as a false positive for the preceding event.
        """
        if (isinstance(timing_tolerance_ms, bool)
                or not isinstance(timing_tolerance_ms, (int, float))
                or not math.isfinite(float(timing_tolerance_ms))
                or float(timing_tolerance_ms) <= 0.0):
            raise ValueError(
                "timing_tolerance_ms must be finite and positive")
        left, right = self.compiled.event_windows(
            1.0, timing_tolerance_ms)
        times = self.compiled.original_times_s
        for index in range(len(times) - 1):
            if times[index] + right[index] >= times[index + 1] - left[index + 1]:
                raise RuntimeError(
                    "adaptive strike matching windows unexpectedly overlap")

    def require_motor_recovery_spacing(
            self, minimum_event_delta_frames: int) -> None:
        if (isinstance(minimum_event_delta_frames, bool)
                or not isinstance(minimum_event_delta_frames, int)
                or minimum_event_delta_frames < 1):
            raise ValueError(
                "minimum_event_delta_frames must be a positive integer")
        actual_s = self.validation_metadata["minimum_event_gap_s"]
        actual_frames = (
            None if actual_s is None else actual_s * self.fps)
        if (actual_frames is not None
                and actual_frames + 1e-9 < minimum_event_delta_frames):
            raise ValueError(
                f"{actual_frames:g} frames apart, but motor recovery requires at "
                f"least {minimum_event_delta_frames} frames")
