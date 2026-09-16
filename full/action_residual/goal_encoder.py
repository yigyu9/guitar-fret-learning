"""Typed goal/score encoding for the 128D Action Residual context.

The Full runtime owns the song clock and event cursor.  It passes semantic
fields to :class:`GoalScoreEncoder`; categorical values are deliberately not
pre-expanded by the environment.  Keeping one-hot and finger-embedding logic
inside this checkpointed module prevents training and deployment packers from
silently disagreeing.

The fixed layout is::

    global clock                                      8D
    current event + next three events  (4 * 30D)    120D
                                                     ----
                                                     128D

Each event first becomes an 85D record after categorical encoding, then all
four slots pass through the same ``85 -> 64 -> 30`` token encoder.  Padding
slots are multiplied by their validity bit after the MLP, guaranteeing an
exactly-zero token even if a future checkpoint contains non-zero biases.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, ClassVar

import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class GoalScoreBatch:
    """Semantic inputs for one batch of four-slot score windows.

    Scalar clock fields have shape ``[B]``.  Event fields use ``[B, 4, ...]``
    in current/next-1/next-2/next-3 order.  Continuous tensors must use the
    module's floating dtype; categorical IDs use an integer dtype and flags
    use ``torch.bool``.

    ``event_times_seconds[..., 5]`` is ordered as fret-window-open,
    strike-window-open, onset, deadline, release.  String axes always follow
    the simulator's canonical six-string order; this module does not accept
    source-file or JSON string indices with an unspecified order.
    """

    song_progress: torch.Tensor
    beat_phase_radians: torch.Tensor
    bar_phase_radians: torch.Tensor
    tempo_ratio: torch.Tensor
    clock_running: torch.Tensor
    timeline_valid: torch.Tensor

    event_valid: torch.Tensor
    event_times_seconds: torch.Tensor
    string_state: torch.Tensor
    target_fret_normalized: torch.Tensor
    finger_id: torch.Tensor
    audible_mask: torch.Tensor
    traversal_mask: torch.Tensor
    strike_direction: torch.Tensor
    strike_offsets_seconds: torch.Tensor
    gesture: torch.Tensor
    atomic_event: torch.Tensor


@dataclass(frozen=True)
class GoalScoreEncoding:
    """Debuggable intermediate tensors produced by ``encode``."""

    context: torch.Tensor
    global_clock: torch.Tensor
    raw_events: torch.Tensor
    event_tokens: torch.Tensor


class EventTokenEncoder(nn.Module):
    """Shared event MLP used for all four relative score slots."""

    def __init__(self, input_dim: int = 85, hidden_dim: int = 64,
                 output_dim: int = 30) -> None:
        super().__init__()
        if (input_dim, hidden_dim, output_dim) != (85, 64, 30):
            raise ValueError(
                "full.action_residual.goal_score.v1 requires 85 -> 64 -> 30")
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ELU(),
            nn.Linear(hidden_dim, output_dim),
            nn.ELU(),
        )
        for layer in self.network.modules():
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=math.sqrt(2.0))
                nn.init.zeros_(layer.bias)

    def forward(self, raw_events: torch.Tensor,
                event_valid: torch.Tensor) -> torch.Tensor:
        if raw_events.ndim != 3 or raw_events.shape[1:] != (4, 85):
            raise ValueError(
                "raw_events must have shape [batch, 4, 85], got "
                f"{tuple(raw_events.shape)}")
        if event_valid.dtype != torch.bool:
            raise TypeError("event_valid must have dtype torch.bool")
        if event_valid.shape != raw_events.shape[:2]:
            raise ValueError(
                "event_valid must have shape [batch, 4], got "
                f"{tuple(event_valid.shape)}")
        if event_valid.device != raw_events.device:
            raise ValueError("raw_events and event_valid must share a device")
        if not torch.isfinite(raw_events).all():
            raise ValueError("raw_events must be finite")

        batch = raw_events.shape[0]
        tokens = self.network(raw_events.reshape(batch * 4, 85))
        tokens = tokens.reshape(batch, 4, 30)
        # This post-MLP mask is a hard contract: invalid tokens are bitwise
        # zero regardless of learned biases or embedding contents.
        return tokens * event_valid.unsqueeze(-1).to(tokens.dtype)


class GoalScoreEncoder(nn.Module):
    """Encode a semantic score window into the coordinator's fixed 128D input."""

    ARCHITECTURE_ID: ClassVar[str] = "full.action_residual.goal_score.v1"
    EVENT_SLOTS: ClassVar[int] = 4
    STRING_COUNT: ClassVar[int] = 6
    GLOBAL_DIM: ClassVar[int] = 8
    RAW_EVENT_DIM: ClassVar[int] = 85
    EVENT_TOKEN_DIM: ClassVar[int] = 30
    OUTPUT_DIM: ClassVar[int] = 128

    EVENT_TIME_FIELDS: ClassVar[tuple[str, ...]] = (
        "dt_fret_window_open",
        "dt_strike_window_open",
        "dt_onset",
        "dt_deadline",
        "dt_release",
    )
    STRING_STATES: ClassVar[tuple[str, ...]] = (
        "DONT_CARE", "OPEN", "FRETTED", "MUTED")
    FINGER_IDS: ClassVar[tuple[str, ...]] = (
        "NONE", "INDEX", "MIDDLE", "RING", "LITTLE")
    STRIKE_DIRECTIONS: ClassVar[tuple[str, ...]] = (
        "NONE", "DOWN", "UP")
    GESTURES: ClassVar[tuple[str, ...]] = (
        "SINGLE", "STRUM", "RESTRIKE")

    # Signed seconds are divided by these values and clipped to [-1, 1].
    EVENT_TIME_SCALES_SECONDS: ClassVar[tuple[float, ...]] = (
        0.5, 0.5, 2.0, 2.0, 2.0)
    STRIKE_OFFSET_SCALE_SECONDS: ClassVar[float] = 0.25
    TEMPO_RATIO_CENTER: ClassVar[float] = 1.0
    TEMPO_RATIO_SCALE: ClassVar[float] = 1.0

    def __init__(self) -> None:
        super().__init__()
        # NONE is a semantic absence, not a trainable fifth finger.  The row
        # remains zero and the four anatomical finger rows are checkpointed.
        self.finger_embedding = nn.Embedding(
            len(self.FINGER_IDS), 4, padding_idx=0)
        nn.init.normal_(self.finger_embedding.weight, mean=0.0, std=0.02)
        with torch.no_grad():
            self.finger_embedding.weight[0].zero_()

        self.event_token_encoder = EventTokenEncoder()
        self.register_buffer(
            "event_time_scales_seconds",
            torch.tensor(self.EVENT_TIME_SCALES_SECONDS, dtype=torch.float32),
            persistent=True,
        )
        self.register_buffer(
            "strike_offset_scale_seconds",
            torch.tensor(self.STRIKE_OFFSET_SCALE_SECONDS, dtype=torch.float32),
            persistent=True,
        )

    @classmethod
    def _schema_without_hash(cls) -> dict[str, Any]:
        return {
            "architecture_id": cls.ARCHITECTURE_ID,
            "schema_version": 1,
            "final_layout": [
                {"name": "global_clock", "offset": 0, "size": 8},
                {"name": "event_current", "offset": 8, "size": 30},
                {"name": "event_next_1", "offset": 38, "size": 30},
                {"name": "event_next_2", "offset": 68, "size": 30},
                {"name": "event_next_3", "offset": 98, "size": 30},
            ],
            "global_layout": [
                "song_progress",
                "sin_beat_phase",
                "cos_beat_phase",
                "sin_bar_phase",
                "cos_bar_phase",
                "normalized_tempo_ratio",
                "clock_running",
                "timeline_valid",
            ],
            "event_slot_order": [
                "current", "next_1", "next_2", "next_3"],
            "canonical_string_order": [
                "high_e", "B", "G", "D", "A", "low_E"],
            "event_time_fields": list(cls.EVENT_TIME_FIELDS),
            "event_time_scales_seconds": list(
                cls.EVENT_TIME_SCALES_SECONDS),
            "raw_event_layout": [
                {"name": "event_valid", "offset": 0, "size": 1},
                {"name": "scaled_event_times", "offset": 1, "size": 5},
                {"name": "string_state_one_hot", "offset": 6, "size": 24},
                {"name": "target_fret_normalized", "offset": 30, "size": 6},
                {"name": "finger_embedding", "offset": 36, "size": 24},
                {"name": "audible_mask", "offset": 60, "size": 6},
                {"name": "traversal_mask", "offset": 66, "size": 6},
                {"name": "strike_direction_one_hot", "offset": 72, "size": 3},
                {"name": "scaled_strike_offsets", "offset": 75, "size": 6},
                {"name": "gesture_one_hot", "offset": 81, "size": 3},
                {"name": "atomic_event", "offset": 84, "size": 1},
            ],
            "categories": {
                "string_state": list(cls.STRING_STATES),
                "finger_id": list(cls.FINGER_IDS),
                "strike_direction": list(cls.STRIKE_DIRECTIONS),
                "gesture": list(cls.GESTURES),
            },
            "finger_embedding_dim": 4,
            "event_token_mlp": [85, 64, 30],
            "event_token_activation": "ELU",
            "invalid_event_rule": "zero payload and exact-zero output token",
            "strike_offset_scale_seconds": cls.STRIKE_OFFSET_SCALE_SECONDS,
            "tempo_normalization": {
                "center": cls.TEMPO_RATIO_CENTER,
                "scale": cls.TEMPO_RATIO_SCALE,
                "clip": [-1.0, 1.0],
            },
            "dimensions": {
                "global": cls.GLOBAL_DIM,
                "event_raw_after_embedding": cls.RAW_EVENT_DIM,
                "event_token": cls.EVENT_TOKEN_DIM,
                "event_slots": cls.EVENT_SLOTS,
                "output": cls.OUTPUT_DIM,
            },
        }

    @classmethod
    def schema_metadata(cls) -> dict[str, Any]:
        """Return a JSON-safe, immutable-by-copy checkpoint schema."""

        schema = cls._schema_without_hash()
        encoded = json.dumps(
            schema, ensure_ascii=True, sort_keys=True,
            separators=(",", ":")).encode("utf-8")
        schema["schema_sha256"] = hashlib.sha256(encoded).hexdigest()
        return deepcopy(schema)

    def get_extra_state(self) -> dict[str, Any]:
        """Persist the semantic layout alongside learned tensor weights."""

        return self.schema_metadata()

    def set_extra_state(self, state: dict[str, Any]) -> None:
        expected = self.schema_metadata()
        if not isinstance(state, dict) or state != expected:
            got = state.get("architecture_id") if isinstance(state, dict) else None
            raise RuntimeError(
                "goal/score checkpoint schema mismatch: expected "
                f"{self.ARCHITECTURE_ID!r}, got {got!r}")

    @staticmethod
    def _require_tensor(name: str, value: Any) -> torch.Tensor:
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{name} must be a torch.Tensor")
        return value

    @staticmethod
    def _require_shape(name: str, value: torch.Tensor,
                       shape: tuple[int, ...]) -> None:
        if value.shape != shape:
            raise ValueError(
                f"{name} must have shape {shape}, got {tuple(value.shape)}")

    @staticmethod
    def _require_bool(name: str, value: torch.Tensor) -> None:
        if value.dtype != torch.bool:
            raise TypeError(f"{name} must have dtype torch.bool")

    @staticmethod
    def _require_integer(name: str, value: torch.Tensor) -> None:
        integer_dtypes = {
            torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8}
        if value.dtype not in integer_dtypes:
            raise TypeError(f"{name} must have an integer dtype")

    @staticmethod
    def _require_category(name: str, value: torch.Tensor,
                          count: int) -> None:
        GoalScoreEncoder._require_integer(name, value)
        if bool(((value < 0) | (value >= count)).any()):
            raise ValueError(f"{name} IDs must be in [0, {count - 1}]")

    @staticmethod
    def _require_zero_on_invalid(
            name: str, value: torch.Tensor,
            invalid: torch.Tensor) -> None:
        if bool(torch.count_nonzero(value[invalid])):
            raise ValueError(f"{name} must be zero/false in invalid event slots")

    def _validate(self, batch: GoalScoreBatch) -> int:
        if not isinstance(batch, GoalScoreBatch):
            raise TypeError("batch must be a GoalScoreBatch")

        tensor_names = tuple(GoalScoreBatch.__dataclass_fields__)
        tensors = {
            name: self._require_tensor(name, getattr(batch, name))
            for name in tensor_names
        }
        if batch.song_progress.ndim != 1:
            raise ValueError(
                "song_progress must have shape [batch], got "
                f"{tuple(batch.song_progress.shape)}")
        count = batch.song_progress.shape[0]
        scalar_shape = (count,)
        event_shape = (count, self.EVENT_SLOTS)
        string_shape = (count, self.EVENT_SLOTS, self.STRING_COUNT)

        for name in (
                "song_progress", "beat_phase_radians", "bar_phase_radians",
                "tempo_ratio", "clock_running", "timeline_valid"):
            self._require_shape(name, tensors[name], scalar_shape)
        self._require_shape("event_valid", batch.event_valid, event_shape)
        self._require_shape(
            "event_times_seconds", batch.event_times_seconds,
            event_shape + (len(self.EVENT_TIME_FIELDS),))
        for name in (
                "string_state", "target_fret_normalized", "finger_id",
                "audible_mask", "traversal_mask", "strike_offsets_seconds"):
            self._require_shape(name, tensors[name], string_shape)
        for name in ("strike_direction", "gesture", "atomic_event"):
            self._require_shape(name, tensors[name], event_shape)

        float_names = (
            "song_progress", "beat_phase_radians", "bar_phase_radians",
            "tempo_ratio", "event_times_seconds", "target_fret_normalized",
            "strike_offsets_seconds",
        )
        expected_dtype = self.finger_embedding.weight.dtype
        expected_device = self.finger_embedding.weight.device
        for name, value in tensors.items():
            if value.device != expected_device:
                raise ValueError(
                    f"{name} must be on {expected_device}, got {value.device}")
        for name in float_names:
            value = tensors[name]
            if not value.is_floating_point():
                raise TypeError(f"{name} must have a floating dtype")
            if value.dtype != expected_dtype:
                raise TypeError(
                    f"{name} must have dtype {expected_dtype}, got {value.dtype}")
            if not torch.isfinite(value).all():
                raise ValueError(f"{name} must be finite")

        for name in (
                "clock_running", "timeline_valid", "event_valid",
                "audible_mask", "traversal_mask", "atomic_event"):
            self._require_bool(name, tensors[name])
        self._require_category(
            "string_state", batch.string_state, len(self.STRING_STATES))
        self._require_category(
            "finger_id", batch.finger_id, len(self.FINGER_IDS))
        self._require_category(
            "strike_direction", batch.strike_direction,
            len(self.STRIKE_DIRECTIONS))
        self._require_category("gesture", batch.gesture, len(self.GESTURES))

        if bool(((batch.song_progress < 0.0)
                 | (batch.song_progress > 1.0)).any()):
            raise ValueError("song_progress must be in [0, 1]")
        max_phase = 2.0 * math.pi
        for name in ("beat_phase_radians", "bar_phase_radians"):
            phase = tensors[name]
            if bool(((phase < 0.0) | (phase > max_phase)).any()):
                raise ValueError(f"{name} must be in [0, 2*pi]")
        if bool((batch.tempo_ratio <= 0.0).any()):
            raise ValueError("tempo_ratio must be positive")
        if bool(((batch.target_fret_normalized < 0.0)
                 | (batch.target_fret_normalized > 1.0)).any()):
            raise ValueError("target_fret_normalized must be in [0, 1]")

        if bool(((~batch.timeline_valid) & batch.clock_running).any()):
            raise ValueError("clock_running requires timeline_valid")
        if bool(((~batch.timeline_valid).unsqueeze(-1)
                 & batch.event_valid).any()):
            raise ValueError("invalid timelines cannot contain valid events")

        invalid = ~batch.event_valid
        for name in (
                "event_times_seconds", "string_state",
                "target_fret_normalized", "finger_id", "audible_mask",
                "traversal_mask", "strike_direction",
                "strike_offsets_seconds", "gesture", "atomic_event"):
            self._require_zero_on_invalid(name, tensors[name], invalid)

        valid_string = batch.event_valid.unsqueeze(-1)
        fretted = (batch.string_state == 2) & valid_string
        if bool(((batch.finger_id != 0) & ~fretted).any()):
            raise ValueError("finger_id must be NONE outside FRETTED strings")
        if bool((fretted & (batch.finger_id == 0)).any()):
            raise ValueError("each FRETTED string requires an anatomical finger")
        if bool(((batch.target_fret_normalized != 0.0) & ~fretted).any()):
            raise ValueError(
                "target_fret_normalized must be zero outside FRETTED strings")
        if bool((batch.audible_mask & ~batch.traversal_mask).any()):
            raise ValueError("audible_mask must be a subset of traversal_mask")
        if bool(((batch.strike_offsets_seconds != 0.0)
                 & ~batch.traversal_mask).any()):
            raise ValueError(
                "strike offsets must be zero on non-traversed strings")

        traverses = batch.traversal_mask.any(dim=-1)
        direction_is_none = batch.strike_direction == 0
        if bool((batch.event_valid
                 & (traverses == direction_is_none)).any()):
            raise ValueError(
                "valid traversals require DOWN/UP; non-traversals require NONE")
        return count

    def _encode_global(self, batch: GoalScoreBatch) -> torch.Tensor:
        tempo = torch.clamp(
            (batch.tempo_ratio - self.TEMPO_RATIO_CENTER)
            / self.TEMPO_RATIO_SCALE,
            min=-1.0,
            max=1.0,
        )
        return torch.stack((
            batch.song_progress,
            torch.sin(batch.beat_phase_radians),
            torch.cos(batch.beat_phase_radians),
            torch.sin(batch.bar_phase_radians),
            torch.cos(batch.bar_phase_radians),
            tempo,
            batch.clock_running.to(batch.song_progress.dtype),
            batch.timeline_valid.to(batch.song_progress.dtype),
        ), dim=-1)

    def _build_raw_events(self, batch: GoalScoreBatch) -> torch.Tensor:
        dtype = batch.song_progress.dtype
        valid = batch.event_valid.unsqueeze(-1).to(dtype)
        times = torch.clamp(
            batch.event_times_seconds
            / self.event_time_scales_seconds.to(dtype=dtype),
            min=-1.0,
            max=1.0,
        )
        string_state = F.one_hot(
            batch.string_state.to(torch.long),
            num_classes=len(self.STRING_STATES),
        ).to(dtype).flatten(start_dim=-2)
        finger = self.finger_embedding(batch.finger_id.to(torch.long))
        # NONE must stay a structural zero even if a damaged checkpoint has a
        # non-zero padding row.
        finger = finger * (batch.finger_id != 0).unsqueeze(-1).to(dtype)
        finger = finger.flatten(start_dim=-2)
        direction = F.one_hot(
            batch.strike_direction.to(torch.long),
            num_classes=len(self.STRIKE_DIRECTIONS),
        ).to(dtype)
        offsets = torch.clamp(
            batch.strike_offsets_seconds
            / self.strike_offset_scale_seconds.to(dtype=dtype),
            min=-1.0,
            max=1.0,
        )
        gesture = F.one_hot(
            batch.gesture.to(torch.long),
            num_classes=len(self.GESTURES),
        ).to(dtype)

        raw = torch.cat((
            valid,
            times,
            string_state,
            batch.target_fret_normalized,
            finger,
            batch.audible_mask.to(dtype),
            batch.traversal_mask.to(dtype),
            direction,
            offsets,
            gesture,
            batch.atomic_event.unsqueeze(-1).to(dtype),
        ), dim=-1)
        if raw.shape[-1] != self.RAW_EVENT_DIM:
            raise RuntimeError(
                f"internal event layout produced {raw.shape[-1]}D, expected 85D")
        # Besides making padding inspectable, this prevents categorical
        # one-hot values (e.g. DONT_CARE or SINGLE == index 0) from leaking out
        # of an invalid slot before the token MLP.
        return raw * valid

    def encode(self, batch: GoalScoreBatch) -> GoalScoreEncoding:
        """Return the 128D context plus audit-friendly intermediate tensors."""

        count = self._validate(batch)
        global_clock = self._encode_global(batch)
        raw_events = self._build_raw_events(batch)
        event_tokens = self.event_token_encoder(raw_events, batch.event_valid)
        context = torch.cat((
            global_clock,
            event_tokens.reshape(count, self.EVENT_SLOTS * self.EVENT_TOKEN_DIM),
        ), dim=-1)
        if context.shape != (count, self.OUTPUT_DIM):
            raise RuntimeError(
                f"internal goal layout produced {tuple(context.shape)}, "
                f"expected {(count, self.OUTPUT_DIM)}")
        if not torch.isfinite(context).all():
            raise RuntimeError("goal/score encoder produced non-finite output")
        return GoalScoreEncoding(
            context=context,
            global_clock=global_clock,
            raw_events=raw_events,
            event_tokens=event_tokens,
        )

    def forward(self, batch: GoalScoreBatch) -> torch.Tensor:
        return self.encode(batch).context


__all__ = [
    "EventTokenEncoder",
    "GoalScoreBatch",
    "GoalScoreEncoder",
    "GoalScoreEncoding",
]
