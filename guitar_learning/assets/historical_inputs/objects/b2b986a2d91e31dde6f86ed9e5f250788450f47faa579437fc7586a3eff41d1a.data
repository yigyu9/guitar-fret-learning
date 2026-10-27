"""fingering ``notes``에서 pick-only strike 학습 입력을 만든다.

입력 fingering의 string은 CSV/모델 관례인 0=low-E, 5=high-e다.
builder 경계에서 정확히 한 번 ``5 - string``으로 뒤집어 Isaac 관례
0=high-e, 5=low-E로 저장한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_goals import (
    N_GUITAR_STRINGS,
    STRIKE_FPS,
    STRIKE_TRAINING_SCHEMA,
    validate_strike_training_data,
)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value)))


def time_to_frame(time_s: float, fps: int = STRIKE_FPS) -> int:
    """Quantize non-negative canonical time to its nearest simulation frame."""
    time_s = float(time_s)
    if not math.isfinite(time_s) or time_s < 0.0:
        raise ValueError("strike time must be finite and non-negative")
    if not _is_integer(fps) or fps <= 0:
        raise ValueError("fps must be a positive integer")
    return int(math.floor(time_s * fps + 0.5))


def build_strike_training_data(
        fingering: Mapping[str, Any], source_path=None,
        reviewed_overrides=None) -> dict[str, Any]:
    """Convert ordered fingering notes into a gesture-compilable timeline."""
    if not isinstance(fingering, Mapping):
        raise ValueError("fingering document must be an object")
    notes = fingering.get("notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError("fingering notes must be a non-empty array")

    events = []
    previous_time = None
    previous_frame = None
    for note_index, note in enumerate(notes):
        if not isinstance(note, Mapping):
            raise ValueError(f"fingering note {note_index}: note must be an object")
        if "t_on" not in note or "string" not in note:
            raise ValueError(
                f"fingering note {note_index}: t_on and string are required")
        time_s = note["t_on"]
        source_string = note["string"]
        if not _is_finite_number(time_s) or float(time_s) < 0.0:
            raise ValueError(
                f"fingering note {note_index}: t_on must be finite and non-negative")
        if (not _is_integer(source_string)
                or not 0 <= source_string < N_GUITAR_STRINGS):
            raise ValueError(
                f"fingering note {note_index}: source string must be 0..5 "
                "with 0=low-E")

        time_s = float(time_s)
        frame = time_to_frame(time_s)
        if previous_time is not None and time_s < previous_time:
            raise ValueError(
                "strike gesture input requires fingering notes in "
                f"non-decreasing t_on order; note {note_index} has {time_s} "
                f"after {previous_time}")
        if previous_frame is not None and frame < previous_frame:
            raise ValueError(
                "strike gesture input requires non-decreasing 60 Hz frames; "
                f"note {note_index} maps to frame {frame} after "
                f"{previous_frame}")

        event = {
            "time": time_s,
            "frame": frame,
            "string": 5 - source_string,
        }
        for field in (
                "event_id", "source_time", "time_uncertainty_s", "source_ref"):
            if field in note:
                event[field] = note[field]
        events.append(event)
        previous_time = time_s
        previous_frame = frame

    source = str(Path(source_path).resolve()) if source_path is not None else None
    source_sha256 = (
        hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
        if source_path is not None else None)
    embedded_overrides = fingering.get(
        "strike_reviewed_overrides", fingering.get("reviewed_overrides"))
    if reviewed_overrides is not None and embedded_overrides is not None:
        raise ValueError(
            "reviewed overrides must come from either fingering or the explicit "
            "argument, not both")
    selected_overrides = (
        embedded_overrides if reviewed_overrides is None else reviewed_overrides)
    output = {
        "schema": STRIKE_TRAINING_SCHEMA,
        "metadata": {
            "fps": STRIKE_FPS,
            "profile": "pick_gesture_compiler_v3",
            "time_authority": "events[].time copied from fingering.notes[].t_on",
            "source": source,
            "source_sha256": source_sha256,
            "source_string_convention": "fingering notes 0=low-E, 5=high-e",
            "string_convention": "Isaac 0=high-e, 5=low-E",
        },
        "events": events,
    }
    if selected_overrides is not None:
        output["reviewed_overrides"] = selected_overrides
    output["validation"] = validate_strike_training_data(output)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="build a 60 Hz pick gesture timeline from fingering notes")
    parser.add_argument("fingering", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--review-overrides", type=Path)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    source = json.loads(args.fingering.read_text(encoding="utf-8"))
    reviewed_overrides = None
    if args.review_overrides is not None:
        override_document = json.loads(
            args.review_overrides.read_text(encoding="utf-8"))
        reviewed_overrides = (
            override_document.get("reviewed_overrides")
            if isinstance(override_document, Mapping)
            else override_document)
    output = build_strike_training_data(
        source, source_path=args.fingering,
        reviewed_overrides=reviewed_overrides)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "out": str(args.out.resolve()),
        "validation": output["validation"],
    }, indent=2, ensure_ascii=False))
    return output


if __name__ == "__main__":
    main()
