"""오른손 pick strike 학습 입력의 최소 시간 계약.

원본 입력의 정본은 초 단위 ``events[].time``이다. ``frame``은 60 Hz
시뮬레이터와의 정합성을 검사하고 로그를 사람이 추적하기 위한 파생
필드이며, 런타임에서 시간을 다시 ``frame / fps``로 덮어쓰지 않는다.

현재 v1은 pick 단현만 다룬다. 따라서 이벤트는 시간과 60 Hz frame 양쪽에서
엄격히 증가해야 하며 한 frame에 둘 이상의 strike를 허용하지 않는다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import torch


STRIKE_TRAINING_SCHEMA = "tab2body.strike_training.v1"
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
    if document.get("schema") != STRIKE_TRAINING_SCHEMA:
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
    minimum_same_string_restrike_frames = None
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
        # A tiny arithmetic allowance keeps an exactly half-frame decimal input
        # from failing solely because of binary floating-point representation.
        if error_frames > MAX_FRAME_ERROR + 1e-9:
            raise ValueError(
                f"strike event {event_index}: time/frame mismatch is "
                f"{error_frames:.9f} frame, above the {MAX_FRAME_ERROR}-frame limit")

        if previous_time is not None and time_s <= previous_time:
            raise ValueError(
                "pick_monophonic_v1 requires strictly increasing event time; "
                f"event {event_index} has time={time_s} after {previous_time}")
        if previous_frame is not None and frame <= previous_frame:
            raise ValueError(
                "pick_monophonic_v1 allows at most one strike per 60 Hz frame; "
                f"event {event_index} has frame={frame} after {previous_frame}")

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
        last_frame_by_string[string_index] = frame
        max_error_frames = max(max_error_frames, error_frames)
        used_strings.add(string_index)

    return {
        "contract_valid": True,
        "schema": STRIKE_TRAINING_SCHEMA,
        "profile": "pick_monophonic_v1",
        "fps": fps,
        "time_authority": "events[].time",
        "string_convention": "Isaac 0=high-e, 5=low-E",
        "num_events": len(events),
        "n_frames": int(events[-1]["frame"]) + 1,
        "used_strings": sorted(used_strings),
        "minimum_same_string_restrike_frames":
            minimum_same_string_restrike_frames,
        "max_time_frame_error_frames": float(max_error_frames),
        "max_time_frame_error_seconds": float(max_error_frames / fps),
    }


class StrikeGoalSequence:
    """Validated immutable strike event tensors for one fixed input sequence.

    Episode progress, target matching and random-start state belong to
    :class:`StrikeTask`; this class only owns the canonical event timeline.
    """

    def __init__(self, path, device="cpu"):
        self.path = str(Path(path).resolve())
        document = json.loads(Path(self.path).read_text(encoding="utf-8"))
        self.validation_metadata = validate_strike_training_data(document)
        self.metadata = dict(document["metadata"])
        self.fps = int(self.validation_metadata["fps"])

        events = document["events"]
        self.time = torch.tensor(
            [float(event["time"]) for event in events],
            dtype=torch.float32, device=device)
        self.frame = torch.tensor(
            [int(event["frame"]) for event in events],
            dtype=torch.long, device=device)
        self.string = torch.tensor(
            [int(event["string"]) for event in events],
            dtype=torch.long, device=device)
        self.event_ids = tuple(
            event.get("event_id", index) for index, event in enumerate(events))

        # Descriptive aliases make task code self-documenting while retaining
        # the compact field names that mirror the JSON contract.
        self.event_time_s = self.time
        self.event_frame = self.frame
        self.event_string = self.string
        self.events = {
            "time": self.time,
            "frame": self.frame,
            "string": self.string,
        }
        self.num_events = len(events)
        self.n_events = self.num_events
        self.n_frames = int(self.validation_metadata["n_frames"])

    def require_physical_rearm_spacing(self, rearm_min_frames: int) -> None:
        """Reject a timeline that the configured same-string detector cannot emit."""
        if (isinstance(rearm_min_frames, bool)
                or int(rearm_min_frames) != rearm_min_frames
                or rearm_min_frames < 1):
            raise ValueError("rearm_min_frames must be a positive integer")
        # A release frame starts WAIT_REARM at zero.  The detector needs the
        # requested complete waiting frames, then the next frame can release.
        required_delta = int(rearm_min_frames) + 1
        actual = self.validation_metadata[
            "minimum_same_string_restrike_frames"]
        if actual is not None and actual < required_delta:
            raise ValueError(
                "strike goal contains a same-string restrike only "
                f"{actual} frames later, but detector re-arm requires at "
                f"least {required_delta} frames")
