"""Compile reviewed song-bundle inputs into the shared G0 event timeline.

The compiler is intentionally a strict, standard-library-only boundary.  It
does not import Isaac Gym, Torch, or the dense per-frame Fret goal runtime.
Canonical events are built from musical source notes selected by each strike
plan event; the dense Fret frames are fingerprinted but never treated as the
audible score.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from tab2body.env.strike_goal_compiler import (
    DIRECTION_NAMES,
    GESTURE_ALTERNATE_RESTRIKE,
    CompiledStrikeEvent,
    compiled_strike_goal_from_plan_document,
)


CANONICAL_PLAY_EVENT_SCHEMA = "tab2body.canonical_play_events.v1"
SONG_BUNDLE_SCHEMA = "tab2body.song_bundle.v1"
FRET_TRAINING_SCHEMA = "tab2body.fret_training.v1"
STRIKE_TRAINING_SCHEMAS = {
    "tab2body.strike_training.v1",
    "tab2body.strike_training.v2",
    "tab2body.strike_training.v3",
}
# Strike's final timing tolerance is 50 ms.  At 60 Hz that corresponds to
# three control frames; the per-transition slack calculation below may still
# reduce an individual event's usable rescue window to 0, 1 or 2 frames.
DEFAULT_MAX_DELAY_FRAMES = 3
N_GUITAR_STRINGS = 6
MAX_FRET = 22
_TIME_TOLERANCE_S = 1e-4 + 1e-12
_SOURCE_PATHS = (
    "mapping/fingering.json",
    "training/fret_training.json",
    "training/strike_plan.json",
)
EventId = Union[int, str]


class SongBundleValidationError(ValueError):
    """The reviewed song bundle cannot define an unambiguous G0 timeline."""


class UnsupportedCanonicalEventError(SongBundleValidationError):
    """A structurally valid event requests a capability not supported in G0."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False)


def canonical_content_sha256(value: Any) -> str:
    """Return the stable SHA-256 used by canonical timeline contracts."""
    if hasattr(value, "content_document"):
        value = value.content_document()
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(
                stream,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    ValueError(f"non-finite JSON number {token}")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SongBundleValidationError(f"cannot read strict JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise SongBundleValidationError(f"JSON root must be an object: {path}")
    return value


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _event_id(value: Any, *, where: str) -> EventId:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise SongBundleValidationError(
            f"{where}: event id must be an integer or non-empty string")
    if isinstance(value, str) and not value:
        raise SongBundleValidationError(f"{where}: event id must not be empty")
    return value


def _finite(value: Any, *, where: str, minimum: Optional[float] = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SongBundleValidationError(f"{where}: expected a finite number")
    result = float(value)
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        suffix = "" if minimum is None else f" >= {minimum}"
        raise SongBundleValidationError(
            f"{where}: expected a finite number{suffix}")
    return result


def _integer(
        value: Any, *, where: str, minimum: Optional[int] = None,
        maximum: Optional[int] = None) -> int:
    if not _is_int(value):
        raise SongBundleValidationError(f"{where}: expected an integer")
    result = int(value)
    if minimum is not None and result < minimum:
        raise SongBundleValidationError(f"{where}: must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise SongBundleValidationError(f"{where}: must be <= {maximum}")
    return result


def _time_to_frame(time_s: float, fps: int) -> int:
    return int(math.floor(time_s * float(fps) + 0.5))


def _sequence(value: Any, *, where: str, non_empty: bool = True) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SongBundleValidationError(f"{where}: expected an array")
    if non_empty and not value:
        raise SongBundleValidationError(f"{where}: array must not be empty")
    return value


def _checked_bundle_file(root: Path, relative: str) -> Path:
    candidate = root / relative
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SongBundleValidationError(
            f"bundle file escapes its root: {relative}") from exc
    if not candidate.is_file():
        raise SongBundleValidationError(f"required bundle file is missing: {relative}")
    return candidate


@dataclass(frozen=True)
class CanonicalSourceFile:
    relative_path: str
    sha256: str
    bytes: int

    def to_document(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "bytes": self.bytes,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "CanonicalSourceFile":
        if not isinstance(value, Mapping):
            raise SongBundleValidationError("source file entry must be an object")
        path = value.get("relative_path")
        digest = value.get("sha256")
        if not isinstance(path, str) or not path:
            raise SongBundleValidationError("source relative_path must be non-empty")
        parsed_path = Path(path)
        if parsed_path.is_absolute() or ".." in parsed_path.parts:
            raise SongBundleValidationError("source relative_path must stay in the bundle")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)):
            raise SongBundleValidationError("source sha256 must be lowercase hex")
        size = _integer(value.get("bytes"), where=f"{path}.bytes", minimum=0)
        return cls(path, digest, size)


@dataclass(frozen=True)
class CanonicalStringTarget:
    """One audible string/note selected by a canonical strike event.

    ``string`` follows the Isaac convention (0=high-e, 5=low-E), while
    ``source_string`` preserves the mapping convention (0=low-E, 5=high-e).
    Traversed-but-muted strings never appear as targets.
    """

    source_event_id: EventId
    mapping_note_index: int
    source_string: int
    string: int
    fret: int
    finger: Optional[int]
    barre: bool
    midi: Optional[int]
    note_on_s: float
    note_off_s: float
    sustain_until_s: float
    press_start_s: Optional[float]
    release_s: Optional[float]
    traversal_offset_s: float
    fret_event_index: Optional[int]
    capability_status: str
    unsupported_reasons: Tuple[str, ...] = ()

    @property
    def supported(self) -> bool:
        return not self.unsupported_reasons

    def to_document(self) -> dict[str, Any]:
        return {
            "source_event_id": self.source_event_id,
            "mapping_note_index": self.mapping_note_index,
            "source_string": self.source_string,
            "string": self.string,
            "fret": self.fret,
            "finger": self.finger,
            "barre": self.barre,
            "midi": self.midi,
            "note_on_s": self.note_on_s,
            "note_off_s": self.note_off_s,
            "sustain_until_s": self.sustain_until_s,
            "press_start_s": self.press_start_s,
            "release_s": self.release_s,
            "traversal_offset_s": self.traversal_offset_s,
            "fret_event_index": self.fret_event_index,
            "capability_status": self.capability_status,
            "unsupported_reasons": list(self.unsupported_reasons),
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "CanonicalStringTarget":
        if not isinstance(value, Mapping):
            raise SongBundleValidationError("string target must be an object")
        source_id = _event_id(value.get("source_event_id"), where="string target")
        status = value.get("capability_status")
        if not isinstance(status, str) or not status:
            raise SongBundleValidationError("capability_status must be non-empty")
        raw_reasons = _sequence(
            value.get("unsupported_reasons", ()),
            where="unsupported_reasons", non_empty=False)
        if any(not isinstance(reason, str) or not reason for reason in raw_reasons):
            raise SongBundleValidationError("unsupported reasons must be strings")

        def optional_number(name: str) -> Optional[float]:
            raw = value.get(name)
            return None if raw is None else _finite(raw, where=name, minimum=0.0)

        finger_raw = value.get("finger")
        finger = None if finger_raw is None else _integer(
            finger_raw, where="finger", minimum=0, maximum=4)
        midi_raw = value.get("midi")
        midi = None if midi_raw is None else _integer(midi_raw, where="midi")
        fret_event_raw = value.get("fret_event_index")
        fret_event_index = None if fret_event_raw is None else _integer(
            fret_event_raw, where="fret_event_index", minimum=0)
        barre = value.get("barre")
        if not isinstance(barre, bool):
            raise SongBundleValidationError("barre must be boolean")
        result = cls(
            source_event_id=source_id,
            mapping_note_index=_integer(
                value.get("mapping_note_index"), where="mapping_note_index",
                minimum=0),
            source_string=_integer(
                value.get("source_string"), where="source_string", minimum=0,
                maximum=5),
            string=_integer(
                value.get("string"), where="string", minimum=0, maximum=5),
            fret=_integer(
                value.get("fret"), where="fret", minimum=0,
                maximum=MAX_FRET),
            finger=finger,
            barre=barre,
            midi=midi,
            note_on_s=_finite(value.get("note_on_s"), where="note_on_s", minimum=0),
            note_off_s=_finite(
                value.get("note_off_s"), where="note_off_s", minimum=0),
            sustain_until_s=_finite(
                value.get("sustain_until_s"), where="sustain_until_s", minimum=0),
            press_start_s=optional_number("press_start_s"),
            release_s=optional_number("release_s"),
            traversal_offset_s=_finite(
                value.get("traversal_offset_s"), where="traversal_offset_s"),
            fret_event_index=fret_event_index,
            capability_status=status,
            unsupported_reasons=tuple(raw_reasons),
        )
        if result.string != 5 - result.source_string:
            raise SongBundleValidationError("string convention conversion is inconsistent")
        if result.note_off_s < result.note_on_s:
            raise SongBundleValidationError("note_off_s precedes note_on_s")
        if not result.note_on_s <= result.sustain_until_s <= result.note_off_s:
            raise SongBundleValidationError("sustain_until_s is outside note lifetime")
        return result


@dataclass(frozen=True)
class CanonicalStrikeProjection:
    gesture: str
    direction: str
    audible_strings: Tuple[int, ...]
    traversal_strings: Tuple[int, ...]
    protected_strings: Tuple[int, ...]
    traversal_offsets_s: Tuple[float, ...]
    sweep_duration_s: float

    def to_document(self) -> dict[str, Any]:
        return {
            "gesture": self.gesture,
            "direction": self.direction,
            "audible_strings": list(self.audible_strings),
            "traversal_strings": list(self.traversal_strings),
            "protected_strings": list(self.protected_strings),
            "traversal_offsets_s": list(self.traversal_offsets_s),
            "sweep_duration_s": self.sweep_duration_s,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "CanonicalStrikeProjection":
        if not isinstance(value, Mapping):
            raise SongBundleValidationError("strike projection must be an object")
        gesture = value.get("gesture")
        direction = value.get("direction")
        if not isinstance(gesture, str) or not gesture:
            raise SongBundleValidationError("strike gesture must be non-empty")
        if direction not in tuple(DIRECTION_NAMES.values()):
            raise SongBundleValidationError("strike direction must be up or down")

        def strings(name: str) -> Tuple[int, ...]:
            raw = _sequence(value.get(name), where=name)
            return tuple(_integer(item, where=name, minimum=0, maximum=5)
                         for item in raw)

        audible = strings("audible_strings")
        traversal = strings("traversal_strings")
        protected = strings("protected_strings") if value.get(
            "protected_strings") else ()
        offsets = tuple(_finite(item, where="traversal_offsets_s") for item in
                        _sequence(value.get("traversal_offsets_s"),
                                  where="traversal_offsets_s"))
        if len(offsets) != len(traversal):
            raise SongBundleValidationError(
                "traversal offset count must match traversal strings")
        if protected != tuple(item for item in traversal if item not in audible):
            raise SongBundleValidationError("protected traversal strings are inconsistent")
        if len(set(audible)) != len(audible) or len(set(traversal)) != len(traversal):
            raise SongBundleValidationError("strike string sequences must be unique")
        if any(right <= left for left, right in zip(offsets, offsets[1:])):
            raise SongBundleValidationError(
                "strike traversal offsets must increase strictly")
        duration = _finite(
            value.get("sweep_duration_s"), where="sweep_duration_s", minimum=0)
        if not math.isclose(duration, offsets[-1] - offsets[0], abs_tol=1e-12):
            raise SongBundleValidationError("strike sweep duration is inconsistent")
        return cls(
            gesture=gesture, direction=direction, audible_strings=audible,
            traversal_strings=traversal, protected_strings=protected,
            traversal_offsets_s=offsets, sweep_duration_s=duration)


@dataclass(frozen=True)
class CanonicalPlayEvent:
    event_id: str
    event_index: int
    score_time_s: float
    score_frame: int
    source_event_ids: Tuple[EventId, ...]
    chord_group: str
    string_targets: Tuple[CanonicalStringTarget, ...]
    strike: CanonicalStrikeProjection
    release_boundary_time_s: float
    release_boundary_frame: int
    effective_delay_cap_frames: int
    release_decision_deadline_s: float
    release_decision_deadline_frame: int
    traversal_end_time_s: float
    traversal_end_frame: int
    outgoing_edge_gap_s: Optional[float]
    outgoing_required_gap_s: Optional[float]
    unsupported_reasons: Tuple[str, ...] = ()

    @property
    def supported(self) -> bool:
        return not self.unsupported_reasons

    def to_document(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_index": self.event_index,
            "score_time_s": self.score_time_s,
            "score_frame": self.score_frame,
            "source_event_ids": list(self.source_event_ids),
            "chord_group": self.chord_group,
            "string_targets": [item.to_document() for item in self.string_targets],
            "strike": self.strike.to_document(),
            "release_boundary_time_s": self.release_boundary_time_s,
            "release_boundary_frame": self.release_boundary_frame,
            "effective_delay_cap_frames": self.effective_delay_cap_frames,
            "release_decision_deadline_s": self.release_decision_deadline_s,
            "release_decision_deadline_frame": (
                self.release_decision_deadline_frame),
            "traversal_end_time_s": self.traversal_end_time_s,
            "traversal_end_frame": self.traversal_end_frame,
            "outgoing_edge_gap_s": self.outgoing_edge_gap_s,
            "outgoing_required_gap_s": self.outgoing_required_gap_s,
            "unsupported_reasons": list(self.unsupported_reasons),
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any], *, fps: int) -> "CanonicalPlayEvent":
        if not isinstance(value, Mapping):
            raise SongBundleValidationError("canonical event must be an object")
        event_id = value.get("event_id")
        chord_group = value.get("chord_group")
        if not isinstance(event_id, str) or not event_id:
            raise SongBundleValidationError("canonical event_id must be non-empty")
        if not isinstance(chord_group, str) or not chord_group:
            raise SongBundleValidationError("canonical chord_group must be non-empty")
        source_ids = tuple(_event_id(item, where=event_id) for item in
                           _sequence(value.get("source_event_ids"),
                                     where=f"{event_id}.source_event_ids"))
        targets = tuple(CanonicalStringTarget.from_document(item) for item in
                        _sequence(value.get("string_targets"),
                                  where=f"{event_id}.string_targets"))
        strike = CanonicalStrikeProjection.from_document(value.get("strike"))
        raw_reasons = _sequence(
            value.get("unsupported_reasons", ()),
            where=f"{event_id}.unsupported_reasons", non_empty=False)
        if any(not isinstance(reason, str) or not reason for reason in raw_reasons):
            raise SongBundleValidationError("event unsupported reasons must be strings")

        def optional_number(name: str) -> Optional[float]:
            raw = value.get(name)
            return None if raw is None else _finite(raw, where=name)

        event = cls(
            event_id=event_id,
            event_index=_integer(
                value.get("event_index"), where="event_index", minimum=0),
            score_time_s=_finite(
                value.get("score_time_s"), where="score_time_s", minimum=0),
            score_frame=_integer(
                value.get("score_frame"), where="score_frame", minimum=0),
            source_event_ids=source_ids,
            chord_group=chord_group,
            string_targets=targets,
            strike=strike,
            release_boundary_time_s=_finite(
                value.get("release_boundary_time_s"),
                where="release_boundary_time_s", minimum=0),
            release_boundary_frame=_integer(
                value.get("release_boundary_frame"),
                where="release_boundary_frame", minimum=0),
            effective_delay_cap_frames=_integer(
                value.get("effective_delay_cap_frames"),
                where="effective_delay_cap_frames", minimum=0,
                maximum=DEFAULT_MAX_DELAY_FRAMES),
            release_decision_deadline_s=_finite(
                value.get("release_decision_deadline_s"),
                where="release_decision_deadline_s", minimum=0),
            release_decision_deadline_frame=_integer(
                value.get("release_decision_deadline_frame"),
                where="release_decision_deadline_frame", minimum=0),
            traversal_end_time_s=_finite(
                value.get("traversal_end_time_s"),
                where="traversal_end_time_s", minimum=0),
            traversal_end_frame=_integer(
                value.get("traversal_end_frame"),
                where="traversal_end_frame", minimum=0),
            outgoing_edge_gap_s=optional_number("outgoing_edge_gap_s"),
            outgoing_required_gap_s=optional_number("outgoing_required_gap_s"),
            unsupported_reasons=tuple(raw_reasons),
        )
        if event.score_frame != _time_to_frame(event.score_time_s, fps):
            raise SongBundleValidationError("canonical score frame is inconsistent")
        if event.release_boundary_frame != _time_to_frame(
                event.release_boundary_time_s, fps):
            raise SongBundleValidationError("release boundary frame is inconsistent")
        if event.release_decision_deadline_frame != (
                event.release_boundary_frame + event.effective_delay_cap_frames):
            raise SongBundleValidationError(
                "release decision deadline frame is inconsistent")
        if not math.isclose(
                event.release_decision_deadline_s,
                event.release_boundary_time_s
                + event.effective_delay_cap_frames / float(fps),
                abs_tol=1e-12):
            raise SongBundleValidationError(
                "release decision deadline time is inconsistent")
        expected_end_time = (
            event.score_time_s + max(event.strike.traversal_offsets_s))
        if not math.isclose(
                event.traversal_end_time_s, expected_end_time,
                abs_tol=1e-12):
            raise SongBundleValidationError(
                "traversal end time is inconsistent")
        if event.traversal_end_frame != _time_to_frame(
                event.traversal_end_time_s, fps):
            raise SongBundleValidationError(
                "traversal end frame is inconsistent")
        if event.traversal_end_time_s < event.release_boundary_time_s:
            raise SongBundleValidationError(
                "traversal ends before its release boundary")
        if tuple(target.source_event_id for target in targets) != source_ids:
            raise SongBundleValidationError("target/source event identity is inconsistent")
        if tuple(dict.fromkeys(target.string for target in targets)) != (
                strike.audible_strings):
            raise SongBundleValidationError("target audible strings are inconsistent")
        return event


@dataclass(frozen=True)
class CanonicalEventTimeline:
    schema: str
    song_id: str
    fps: int
    timing_mode: str
    source_files: Tuple[CanonicalSourceFile, ...]
    events: Tuple[CanonicalPlayEvent, ...]
    content_sha256: str

    def content_document(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "song_id": self.song_id,
            "fps": self.fps,
            "timing_mode": self.timing_mode,
            "source_files": [item.to_document() for item in self.source_files],
            "events": [item.to_document() for item in self.events],
        }

    def to_document(self) -> dict[str, Any]:
        value = self.content_document()
        value["content_sha256"] = self.content_sha256
        return value

    # ``as_document`` matches the existing strike-plan serialization idiom.
    as_document = to_document

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(
            self.to_document(), ensure_ascii=False, indent=indent,
            sort_keys=indent is None, allow_nan=False) + ("\n" if indent else "")

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "CanonicalEventTimeline":
        if not isinstance(value, Mapping):
            raise SongBundleValidationError("canonical timeline must be an object")
        if value.get("schema") != CANONICAL_PLAY_EVENT_SCHEMA:
            raise SongBundleValidationError("unsupported canonical event schema")
        song_id = value.get("song_id")
        timing_mode = value.get("timing_mode")
        digest = value.get("content_sha256")
        if not isinstance(song_id, str) or not song_id:
            raise SongBundleValidationError("canonical song_id must be non-empty")
        if timing_mode != "original":
            raise SongBundleValidationError("G0 canonical timing_mode must be original")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)):
            raise SongBundleValidationError("canonical content_sha256 is invalid")
        fps = _integer(value.get("fps"), where="fps", minimum=1)
        sources = tuple(CanonicalSourceFile.from_document(item) for item in
                        _sequence(value.get("source_files"), where="source_files"))
        events = tuple(CanonicalPlayEvent.from_document(item, fps=fps) for item in
                       _sequence(value.get("events"), where="events"))
        source_paths = tuple(item.relative_path for item in sources)
        if len(set(source_paths)) != len(source_paths):
            raise SongBundleValidationError("canonical source file paths are duplicated")
        if tuple(event.event_index for event in events) != tuple(range(len(events))):
            raise SongBundleValidationError("canonical event indices are not contiguous")
        if len({event.event_id for event in events}) != len(events):
            raise SongBundleValidationError("canonical event ids are duplicated")
        if any(right.score_time_s < left.score_time_s for left, right in
               zip(events, events[1:])):
            raise SongBundleValidationError("canonical event time is not monotonic")
        for event in events[:-1]:
            if (event.outgoing_edge_gap_s is None
                    or event.outgoing_required_gap_s is None):
                raise SongBundleValidationError(
                    "non-final event is missing outgoing transition timing")
            available = math.floor(
                (event.outgoing_edge_gap_s - event.outgoing_required_gap_s)
                * fps + 1e-9)
            expected_cap = min(DEFAULT_MAX_DELAY_FRAMES, available)
            if available < 0 or event.effective_delay_cap_frames != expected_cap:
                raise SongBundleValidationError(
                    "event delay cap does not match outgoing transition margin")
        if (events[-1].outgoing_edge_gap_s is not None
                or events[-1].outgoing_required_gap_s is not None
                or events[-1].effective_delay_cap_frames
                != DEFAULT_MAX_DELAY_FRAMES):
            raise SongBundleValidationError("final event delay contract is inconsistent")
        timeline = cls(
            schema=CANONICAL_PLAY_EVENT_SCHEMA, song_id=song_id, fps=fps,
            timing_mode=timing_mode, source_files=sources, events=events,
            content_sha256=digest)
        actual = canonical_content_sha256(timeline)
        if actual != digest:
            raise SongBundleValidationError(
                f"canonical content hash mismatch: expected {digest}, got {actual}")
        return timeline

    @classmethod
    def from_json(cls, text: str) -> "CanonicalEventTimeline":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SongBundleValidationError("invalid canonical timeline JSON") from exc
        return cls.from_document(value)


def _manifest_sources(
        root: Path, manifest: Mapping[str, Any],
        relative_paths: Sequence[str]) -> Tuple[CanonicalSourceFile, ...]:
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        raise SongBundleValidationError("bundle manifest files must be an object")
    results = []
    for relative in relative_paths:
        path = _checked_bundle_file(root, relative)
        entry = files.get(relative)
        if not isinstance(entry, Mapping):
            raise SongBundleValidationError(
                f"bundle manifest has no fingerprint for {relative}")
        expected = entry.get("sha256")
        if (not isinstance(expected, str) or len(expected) != 64
                or any(ch not in "0123456789abcdef" for ch in expected)):
            raise SongBundleValidationError(
                f"bundle manifest has invalid sha256 for {relative}")
        actual = _file_sha256(path)
        if actual != expected:
            raise SongBundleValidationError(
                f"bundle manifest hash mismatch for {relative}: "
                f"expected {expected}, got {actual}")
        size = path.stat().st_size
        manifest_size = entry.get("bytes")
        if manifest_size is not None and manifest_size != size:
            raise SongBundleValidationError(
                f"bundle manifest byte count mismatch for {relative}")
        results.append(CanonicalSourceFile(relative, actual, size))
    return tuple(results)


def _validate_manifest(root: Path) -> Mapping[str, Any]:
    manifest = _load_json(_checked_bundle_file(root, "manifest.json"))
    if manifest.get("schema") != SONG_BUNDLE_SCHEMA:
        raise SongBundleValidationError("unsupported song bundle manifest schema")
    song_id = manifest.get("song_id")
    if not isinstance(song_id, str) or not song_id:
        raise SongBundleValidationError("bundle manifest song_id must be non-empty")
    if song_id != root.name:
        raise SongBundleValidationError(
            f"bundle song_id {song_id!r} does not match directory {root.name!r}")
    return manifest


def _plan_references_raw_strike(plan: Mapping[str, Any]) -> bool:
    metadata = plan.get("metadata")
    if not isinstance(metadata, Mapping):
        raise SongBundleValidationError("strike plan metadata must be an object")
    return metadata.get("source") is not None or metadata.get("source_sha256") is not None


def _mapping_notes(document: Mapping[str, Any]) -> Tuple[Mapping[str, Any], ...]:
    convention = document.get("convention")
    if not isinstance(convention, str) or "0 = low-E" not in convention:
        raise SongBundleValidationError(
            "fingering convention must explicitly declare string 0 = low-E")
    raw_notes = _sequence(document.get("notes"), where="fingering.notes")
    notes = []
    ids = []
    previous_onset = -math.inf
    for index, raw in enumerate(raw_notes):
        if not isinstance(raw, Mapping):
            raise SongBundleValidationError(f"fingering note {index} must be an object")
        onset = _finite(raw.get("t_on"), where=f"note {index}.t_on", minimum=0)
        note_off = _finite(raw.get("t_off"), where=f"note {index}.t_off", minimum=0)
        if onset < previous_onset:
            raise SongBundleValidationError("fingering note onsets are not monotonic")
        if note_off < onset:
            raise SongBundleValidationError(f"fingering note {index} ends before onset")
        _integer(raw.get("string"), where=f"note {index}.string", minimum=0,
                 maximum=5)
        _integer(raw.get("fret"), where=f"note {index}.fret", minimum=0,
                 maximum=MAX_FRET)
        source_id = _event_id(raw.get("event_id", index), where=f"note {index}")
        ids.append(source_id)
        notes.append(raw)
        previous_onset = onset
    if len(set(ids)) != len(ids):
        raise SongBundleValidationError("fingering source event ids must be unique")
    return tuple(notes)


def _validate_fret_training(
        document: Mapping[str, Any], fps: int) -> Tuple[Mapping[str, Any], ...]:
    if document.get("schema") != FRET_TRAINING_SCHEMA:
        raise SongBundleValidationError("unsupported fret training schema")
    metadata = document.get("metadata")
    if not isinstance(metadata, Mapping):
        raise SongBundleValidationError("fret training metadata must be an object")
    fret_fps = _integer(metadata.get("fps"), where="fret training fps", minimum=1)
    if fret_fps != fps:
        raise SongBundleValidationError(
            f"fret/strike FPS mismatch: {fret_fps} != {fps}")
    raw_events = _sequence(
        document.get("events"), where="fret_training.events", non_empty=False)
    events = []
    for index, raw in enumerate(raw_events):
        if not isinstance(raw, Mapping):
            raise SongBundleValidationError(f"fret event {index} must be an object")
        finger = _integer(raw.get("finger"), where=f"fret event {index}.finger",
                          minimum=1, maximum=4)
        string = _integer(raw.get("string"), where=f"fret event {index}.string",
                          minimum=0, maximum=5)
        fret = _integer(raw.get("fret"), where=f"fret event {index}.fret",
                        minimum=1, maximum=MAX_FRET)
        barre = raw.get("barre")
        if not isinstance(barre, bool):
            raise SongBundleValidationError(f"fret event {index}.barre must be boolean")
        press = _finite(raw.get("t_press"), where=f"fret event {index}.t_press",
                        minimum=0)
        release = _finite(
            raw.get("t_release"), where=f"fret event {index}.t_release", minimum=0)
        if release < press:
            raise SongBundleValidationError(f"fret event {index} releases before press")
        strikes = tuple(_finite(item, where=f"fret event {index}.strikes", minimum=0)
                        for item in _sequence(raw.get("strikes"),
                                              where=f"fret event {index}.strikes"))
        if any(right <= left for left, right in zip(strikes, strikes[1:])):
            raise SongBundleValidationError(
                f"fret event {index} strike times must increase strictly")
        if strikes[0] + _TIME_TOLERANCE_S < press or (
                strikes[-1] > release + _TIME_TOLERANCE_S):
            raise SongBundleValidationError(
                f"fret event {index} does not cover all linked strikes")
        copied = dict(raw)
        copied.update({
            "finger": finger, "string": string, "fret": fret,
            "barre": barre, "t_press": press, "t_release": release,
            "strikes": strikes,
        })
        events.append(copied)
    return tuple(events)


def _source_ids(
        records: Sequence[Mapping[str, Any]], *, label: str) -> Tuple[EventId, ...]:
    result = tuple(_event_id(record.get("event_id", index), where=f"{label} {index}")
                   for index, record in enumerate(records))
    if len(set(result)) != len(result):
        raise SongBundleValidationError(f"{label} event ids must be unique")
    return result


def _validate_raw_strike_identity(
        raw_document: Mapping[str, Any], notes: Sequence[Mapping[str, Any]],
        mapping_hash: str, fps: int) -> Tuple[EventId, ...]:
    if raw_document.get("schema") not in STRIKE_TRAINING_SCHEMAS:
        raise SongBundleValidationError("unsupported strike training schema")
    metadata = raw_document.get("metadata")
    raw_events = _sequence(raw_document.get("events"), where="strike_training.events")
    if not isinstance(metadata, Mapping):
        raise SongBundleValidationError("strike training metadata must be an object")
    raw_fps = _integer(metadata.get("fps"), where="strike training fps", minimum=1)
    if raw_fps != fps:
        raise SongBundleValidationError(
            f"raw strike/plan FPS mismatch: {raw_fps} != {fps}")
    declared_mapping_hash = metadata.get("source_sha256")
    if declared_mapping_hash is not None and declared_mapping_hash != mapping_hash:
        raise SongBundleValidationError(
            "strike_training metadata source_sha256 does not match fingering.json")
    if len(raw_events) != len(notes):
        raise SongBundleValidationError(
            "strike_training must contain exactly one source event per fingering note")
    note_ids = _source_ids(notes, label="fingering")
    raw_ids = _source_ids(raw_events, label="raw strike")
    if raw_ids != note_ids:
        raise SongBundleValidationError(
            "raw strike event identity/order does not match fingering notes")
    for index, (raw, note) in enumerate(zip(raw_events, notes)):
        if not isinstance(raw, Mapping):
            raise SongBundleValidationError(f"raw strike event {index} must be an object")
        time_s = _finite(raw.get("time"), where=f"raw strike {index}.time", minimum=0)
        note_time = _finite(note.get("t_on"), where=f"note {index}.t_on", minimum=0)
        source_string = _integer(
            note.get("string"), where=f"note {index}.string", minimum=0, maximum=5)
        raw_string = _integer(
            raw.get("string"), where=f"raw strike {index}.string", minimum=0,
            maximum=5)
        frame = _integer(raw.get("frame"), where=f"raw strike {index}.frame",
                         minimum=0)
        if not math.isclose(time_s, note_time, abs_tol=_TIME_TOLERANCE_S):
            raise SongBundleValidationError(
                f"raw strike event {index} time does not match fingering note")
        if raw_string != 5 - source_string:
            raise SongBundleValidationError(
                f"raw strike event {index} has incorrect string conversion")
        if frame != _time_to_frame(time_s, fps):
            raise SongBundleValidationError(
                f"raw strike event {index} frame does not match time/FPS")
    return raw_ids


def _validate_plan_partition(
        events: Sequence[CompiledStrikeEvent], expected_ids: Sequence[EventId]) -> None:
    flattened = tuple(source_id for event in events for source_id in
                      event.source_event_ids)
    if len(set(flattened)) != len(flattened):
        raise SongBundleValidationError(
            "strike plan source_event_ids are not a unique partition")
    if flattened != tuple(expected_ids):
        expected_set = set(expected_ids)
        actual_set = set(flattened)
        missing = [item for item in expected_ids if item not in actual_set]
        extra = [item for item in flattened if item not in expected_set]
        raise SongBundleValidationError(
            "strike plan source_event_ids must be the complete, ordered raw "
            f"event partition; missing={missing[:5]!r}, extra={extra[:5]!r}")


def _technique_reasons(note: Mapping[str, Any]) -> Tuple[str, ...]:
    reasons = []
    normal_labels = (None, "", "normal", "standard", "none")
    for name in ("technique", "articulation"):
        value = note.get(name)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized not in normal_labels:
                reasons.append(f"unsupported_{name}:{normalized}")
        elif value not in normal_labels:
            reasons.append(f"unsupported_{name}")
    for name in ("hammer_on", "pull_off", "slide", "bend"):
        if note.get(name):
            reasons.append(f"unsupported_{name}")
    return tuple(reasons)


def _matching_fret_event(
        note: Mapping[str, Any], fret_events: Sequence[Mapping[str, Any]],
        note_index: int) -> Tuple[Optional[int], Optional[Mapping[str, Any]]]:
    fret = int(note["fret"])
    if fret == 0:
        return None, None
    onset = float(note["t_on"])
    candidates = []
    for index, event in enumerate(fret_events):
        if int(event["string"]) != int(note["string"]):
            continue
        if int(event["fret"]) != fret:
            continue
        if any(math.isclose(onset, strike, abs_tol=_TIME_TOLERANCE_S)
               for strike in event["strikes"]):
            candidates.append((index, event))
    if len(candidates) > 1:
        raise SongBundleValidationError(
            f"fingering note {note_index} links to multiple Fret events")
    return candidates[0] if candidates else (None, None)


def _target_from_note(
        source_id: EventId, note_index: int, note: Mapping[str, Any],
        strike: CompiledStrikeEvent,
        fret_events: Sequence[Mapping[str, Any]]) -> CanonicalStringTarget:
    source_string = int(note["string"])
    isaac_string = 5 - source_string
    fret = int(note["fret"])
    finger_raw = note.get("finger")
    raw_finger_number = int(finger_raw) if _is_int(finger_raw) else None
    finger = raw_finger_number if raw_finger_number in (0, 1, 2, 3, 4) else None
    barre_raw = note.get("barre", False)
    if not isinstance(barre_raw, bool):
        raise SongBundleValidationError(
            f"fingering note {note_index}.barre must be boolean")
    midi_raw = note.get("midi")
    midi = None if midi_raw is None else _integer(
        midi_raw, where=f"note {note_index}.midi")
    onset = float(note["t_on"])
    note_off = float(note["t_off"])
    cut = _finite(note.get("t_cut", note_off), where=f"note {note_index}.t_cut",
                  minimum=0)
    sustain = min(note_off, cut)
    if sustain < onset:
        raise SongBundleValidationError(
            f"fingering note {note_index} sustain ends before onset")
    reasons = list(_technique_reasons(note))
    if barre_raw:
        reasons.append("unsupported_barre")
    if fret > 0 and raw_finger_number not in (1, 2, 3, 4):
        reasons.append("missing_or_invalid_fretted_finger")
    if fret == 0 and raw_finger_number not in (None, 0):
        reasons.append("open_string_has_fretted_finger")

    fret_event_index, fret_event = _matching_fret_event(
        note, fret_events, note_index)
    press_start = None
    release = sustain if fret == 0 else None
    if fret_event is not None:
        press_start = float(fret_event["t_press"])
        release = float(fret_event["t_release"])
        if finger is not None and int(fret_event["finger"]) != finger:
            reasons.append("fret_event_finger_mismatch")
        if bool(fret_event["barre"]) != barre_raw:
            reasons.append("fret_event_barre_mismatch")
    elif fret > 0:
        reasons.append("missing_fret_event_link")

    try:
        traversal_position = strike.traversal_strings.index(isaac_string)
    except ValueError as exc:
        raise SongBundleValidationError(
            f"source event {source_id!r} audible string is not traversed") from exc
    traversal_offset = strike.traversal_offsets_s[traversal_position]
    status = "unsupported" if reasons else ("open" if fret == 0 else "linked")
    return CanonicalStringTarget(
        source_event_id=source_id,
        mapping_note_index=note_index,
        source_string=source_string,
        string=isaac_string,
        fret=fret,
        finger=finger,
        barre=barre_raw,
        midi=midi,
        note_on_s=onset,
        note_off_s=note_off,
        sustain_until_s=sustain,
        press_start_s=press_start,
        release_s=release,
        traversal_offset_s=traversal_offset,
        fret_event_index=fret_event_index,
        capability_status=status,
        unsupported_reasons=tuple(dict.fromkeys(reasons)),
    )


def _canonical_event(
        index: int, strike: CompiledStrikeEvent,
        source_lookup: Mapping[EventId, Tuple[int, Mapping[str, Any]]],
        fret_events: Sequence[Mapping[str, Any]], fps: int,
        delay_cap: int, outgoing_edge_gap_s: Optional[float],
        outgoing_required_gap_s: Optional[float]) -> CanonicalPlayEvent:
    targets = tuple(
        _target_from_note(
            source_id, source_lookup[source_id][0], source_lookup[source_id][1],
            strike, fret_events)
        for source_id in strike.source_event_ids)
    derived_audible = tuple(dict.fromkeys(target.string for target in targets))
    if derived_audible != strike.audible_strings:
        raise SongBundleValidationError(
            f"strike event {index} audible strings disagree with fingering: "
            f"plan={strike.audible_strings!r}, mapping={derived_audible!r}")
    event_reasons = []
    if strike.gesture == GESTURE_ALTERNATE_RESTRIKE:
        event_reasons.append("unsupported_alternate_restrike")
    for target in targets:
        event_reasons.extend(target.unsupported_reasons)
    boundary_time = strike.time_s + min(strike.traversal_offsets_s)
    if boundary_time < 0.0:
        raise SongBundleValidationError(
            f"strike event {index} traversal starts before time zero")
    event_id = f"event-{index:06d}"
    release_deadline_s = boundary_time + delay_cap / float(fps)
    boundary_frame = _time_to_frame(boundary_time, fps)
    traversal_end_time = strike.time_s + max(strike.traversal_offsets_s)
    traversal_end_frame = _time_to_frame(traversal_end_time, fps)
    projection = CanonicalStrikeProjection(
        gesture=strike.gesture,
        direction=DIRECTION_NAMES[strike.direction],
        audible_strings=strike.audible_strings,
        traversal_strings=strike.traversal_strings,
        protected_strings=strike.protected_strings,
        traversal_offsets_s=strike.traversal_offsets_s,
        sweep_duration_s=strike.sweep_duration_s,
    )
    return CanonicalPlayEvent(
        event_id=event_id,
        event_index=index,
        score_time_s=strike.time_s,
        score_frame=strike.frame,
        source_event_ids=strike.source_event_ids,
        chord_group=event_id,
        string_targets=targets,
        strike=projection,
        release_boundary_time_s=boundary_time,
        release_boundary_frame=boundary_frame,
        effective_delay_cap_frames=delay_cap,
        release_decision_deadline_s=release_deadline_s,
        release_decision_deadline_frame=boundary_frame + delay_cap,
        traversal_end_time_s=traversal_end_time,
        traversal_end_frame=traversal_end_frame,
        outgoing_edge_gap_s=outgoing_edge_gap_s,
        outgoing_required_gap_s=outgoing_required_gap_s,
        unsupported_reasons=tuple(dict.fromkeys(event_reasons)),
    )


def compile_song_bundle_events(
        bundle_root: Union[str, Path], *,
        fail_on_unsupported: bool = True) -> CanonicalEventTimeline:
    """Validate and compile one reviewed song bundle for fixed-guitar G0.

    Source-policy dense Fret frames are not consulted when constructing musical
    events.  Fret ``events`` only contribute their authoritative press/release
    times after a source-note identity match.
    """
    root = Path(bundle_root).resolve()
    if not root.is_dir():
        raise SongBundleValidationError(f"song bundle directory not found: {root}")
    manifest = _validate_manifest(root)

    fingering_path = _checked_bundle_file(root, "mapping/fingering.json")
    fret_path = _checked_bundle_file(root, "training/fret_training.json")
    plan_path = _checked_bundle_file(root, "training/strike_plan.json")
    fingering = _load_json(fingering_path)
    fret_training = _load_json(fret_path)
    plan_document = _load_json(plan_path)
    raw_referenced = _plan_references_raw_strike(plan_document)
    relative_sources = list(_SOURCE_PATHS)
    if raw_referenced:
        relative_sources.append("training/strike_training.json")
    source_files = _manifest_sources(root, manifest, relative_sources)
    source_hash = {item.relative_path: item.sha256 for item in source_files}

    metadata = plan_document.get("metadata")
    fps = _integer(metadata.get("fps"), where="strike plan fps", minimum=1)
    try:
        compiled = compiled_strike_goal_from_plan_document(plan_document)
    except (KeyError, TypeError, ValueError) as exc:
        raise SongBundleValidationError(f"invalid compiled strike plan: {exc}") from exc
    for index, event in enumerate(compiled.events):
        if event.frame != _time_to_frame(event.time_s, fps):
            raise SongBundleValidationError(
                f"strike plan event {index} frame does not match time/FPS")

    notes = _mapping_notes(fingering)
    note_ids = _source_ids(notes, label="fingering")
    fret_events = _validate_fret_training(fret_training, fps)
    expected_source_ids = note_ids
    if raw_referenced:
        source_name = Path(str(metadata.get("source"))).name
        if source_name != "strike_training.json":
            raise SongBundleValidationError(
                "strike plan source must reference training/strike_training.json")
        declared_raw_hash = metadata.get("source_sha256")
        actual_raw_hash = source_hash["training/strike_training.json"]
        if declared_raw_hash != actual_raw_hash:
            raise SongBundleValidationError(
                "strike plan source_sha256 does not match strike_training.json")
        raw_document = _load_json(
            _checked_bundle_file(root, "training/strike_training.json"))
        expected_source_ids = _validate_raw_strike_identity(
            raw_document, notes, source_hash["mapping/fingering.json"], fps)
    _validate_plan_partition(compiled.events, expected_source_ids)
    source_lookup = {
        source_id: (index, note)
        for index, (source_id, note) in enumerate(zip(note_ids, notes))
    }

    transitions = compiled.transition_diagnostics(1.0)
    delay_caps = []
    for transition in transitions:
        available_frames = math.floor(
            (transition.edge_gap_s - transition.required_edge_gap_s) * fps
            + 1e-9)
        if available_frames < 0:
            raise SongBundleValidationError(
                "strike transition has negative timing margin at "
                f"{transition.from_event_index}->{transition.to_event_index}: "
                f"edge_gap={transition.edge_gap_s}, "
                f"required_gap={transition.required_edge_gap_s}")
        delay_caps.append(min(DEFAULT_MAX_DELAY_FRAMES, available_frames))
    delay_caps.append(DEFAULT_MAX_DELAY_FRAMES)

    events = []
    for index, strike in enumerate(compiled.events):
        transition = transitions[index] if index < len(transitions) else None
        try:
            event = _canonical_event(
                index, strike, source_lookup, fret_events, fps,
                delay_caps[index],
                None if transition is None else transition.edge_gap_s,
                None if transition is None else transition.required_edge_gap_s)
        except KeyError as exc:
            raise SongBundleValidationError(
                f"strike event {index} references unknown source event {exc.args[0]!r}") from exc
        events.append(event)

    unsupported = [event for event in events if not event.supported]
    if fail_on_unsupported and unsupported:
        first = unsupported[0]
        raise UnsupportedCanonicalEventError(
            f"{len(unsupported)} canonical event(s) require unsupported G0 "
            f"capabilities; first={first.event_id}, "
            f"source_event_ids={first.source_event_ids!r}, "
            f"reasons={first.unsupported_reasons!r}. Recompile with "
            "fail_on_unsupported=False only for diagnostic inspection")

    timeline = CanonicalEventTimeline(
        schema=CANONICAL_PLAY_EVENT_SCHEMA,
        song_id=str(manifest["song_id"]),
        fps=fps,
        timing_mode="original",
        source_files=source_files,
        events=tuple(events),
        content_sha256="",
    )
    return CanonicalEventTimeline(
        schema=timeline.schema,
        song_id=timeline.song_id,
        fps=timeline.fps,
        timing_mode=timeline.timing_mode,
        source_files=timeline.source_files,
        events=timeline.events,
        content_sha256=canonical_content_sha256(timeline),
    )


# Readable alias for callers that think in terms of the artifact rather than
# the bundle operation.
compile_canonical_play_events = compile_song_bundle_events
