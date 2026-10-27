#!/usr/bin/env python3
"""Prepare the local GOAT release in the project's moum CSV/audio layout.

The GOAT release contains Guitar Pro scores, DadaGP text, MIDI, DI audio and
five amplifier renders.  The current Conformer v1 loader expects one WAV per
directory/audio_name pair and these columns:

    unique_id,directory_name,audio_name,string,start,end,pitch,source

This script uses the GP5 score as the source of truth for string, fret and
pitch.  It uses the score tempo map for absolute times and, when available,
applies an affine time alignment using the fine-aligned MIDI's first and last
note.  Audio is symlinked instead of copied because the GOAT release is large.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from contextlib import ExitStack
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PPQ = 960.0  # Guitar Pro beat time used by DadaGP and the GP5 parser.
CORE_COLUMNS = [
    "unique_id",
    "directory_name",
    "audio_name",
    "string",
    "start",
    "end",
    "pitch",
    "source",
]

AUDIO_VARIANTS: Sequence[Tuple[str, str]] = (
    ("GOAT_DI", "di_audio_path"),
    ("GOAT_amp_1", "amp_audio_path_1"),
    ("GOAT_amp_2", "amp_audio_path_2"),
    ("GOAT_amp_3", "amp_audio_path_3"),
    ("GOAT_amp_4", "amp_audio_path_4"),
    ("GOAT_amp_5", "amp_audio_path_5"),
)


def import_guitarpro():
    try:
        import guitarpro  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyGuitarPro 0.6 is required. Install it with "
            "python -m pip install 'PyGuitarPro==0.6'."
        ) from exc
    return guitarpro


def resolve_goat_path(source_root: Path, metadata_path: str) -> Optional[Path]:
    """Resolve metadata's GOAT/... path against the extracted release."""
    if not metadata_path:
        return None
    raw = Path(metadata_path)
    if raw.is_absolute():
        return raw
    parts = raw.parts
    if parts and parts[0].lower() == "goat":
        parts = parts[1:]
    candidate = source_root / "data" / Path(*parts)
    if candidate.exists():
        return candidate
    # A few local copies may place item directories directly under source.
    candidate = source_root / Path(*parts)
    return candidate


def read_wav_duration(path: Path) -> Optional[float]:
    try:
        import wave

        with wave.open(str(path), "rb") as wav:
            if wav.getframerate() <= 0:
                return None
            return wav.getnframes() / float(wav.getframerate())
    except Exception:
        return None


def _tempo_events(song, guitarpro) -> List[Tuple[float, float]]:
    events: Dict[float, float] = {0.0: float(song.tempo)}
    for track in song.tracks:
        for measure in track.measures:
            for voice in measure.voices:
                for beat in voice.beats:
                    change = beat.effect.mixTableChange
                    if change is not None and change.tempo is not None:
                        value = getattr(change.tempo, "value", None)
                        if value:
                            events[float(beat.start)] = float(value)
    return sorted(events.items())


def _tick_to_seconds_fn(tempo_events: Sequence[Tuple[float, float]]):
    """Return a monotonic GP-tick to seconds converter."""
    cumulative: List[Tuple[float, float, float]] = []
    current_seconds = 0.0
    previous_tick = 0.0
    current_tempo = float(tempo_events[0][1])
    for tick, tempo in tempo_events[1:]:
        tick = max(float(tick), previous_tick)
        current_seconds += (tick - previous_tick) * 60.0 / (PPQ * current_tempo)
        cumulative.append((previous_tick, tick, current_seconds - (tick - previous_tick) * 60.0 / (PPQ * current_tempo)))
        previous_tick = tick
        current_tempo = float(tempo)
    cumulative.append((previous_tick, math.inf, current_seconds))

    def tick_to_seconds(tick: float) -> float:
        tick = float(tick)
        # Most notes are in the last interval, so scan from the end first.
        for start, end, start_seconds in reversed(cumulative):
            if tick >= start:
                tempo = current_tempo
                # Find the tempo active at this interval.  The interval's
                # tempo is recoverable from the event list without storing a
                # second structure by locating its start tick.
                for event_tick, event_tempo in reversed(tempo_events):
                    if event_tick <= start:
                        tempo = float(event_tempo)
                        break
                return start_seconds + (tick - start) * 60.0 / (PPQ * tempo)
        return tick * 60.0 / (PPQ * float(tempo_events[0][1]))

    return tick_to_seconds


def parse_gp5(path: Path, guitarpro) -> Tuple[List[dict], List[Tuple[float, float]], Counter]:
    song = guitarpro.parse(str(path))
    tempo_events = _tempo_events(song, guitarpro)
    tick_to_seconds = _tick_to_seconds_fn(tempo_events)
    notes: List[dict] = []
    note_types: Counter = Counter()

    for track in song.tracks:
        if track.isPercussionTrack:
            continue
        for measure in track.measures:
            for voice in measure.voices:
                for beat in voice.beats:
                    if beat.status.name != "normal":
                        continue
                    start_tick = float(beat.start)
                    duration_tick = float(beat.duration.time)
                    if duration_tick <= 0:
                        continue
                    start = tick_to_seconds(start_tick)
                    end = tick_to_seconds(start_tick + duration_tick)
                    for note in beat.notes:
                        if not (1 <= int(note.string) <= 6):
                            continue
                        note_type = getattr(note.type, "name", str(note.type))
                        note_types[note_type] += 1
                        # GP uses s1=highest string and s6=lowest string;
                        # moum/v1 uses index 0=lowest string and 5=highest.
                        moum_string = 6 - int(note.string)
                        notes.append(
                            {
                                "string": moum_string,
                                "pitch": int(note.realValue),
                                "start": start,
                                "end": end,
                                "start_tick": start_tick,
                                "end_tick": start_tick + duration_tick,
                                "fret": int(note.value),
                                "note_type": note_type,
                            }
                        )
    notes.sort(key=lambda row: (row["start"], row["string"], row["pitch"], row["fret"]))
    return notes, tempo_events, note_types


def fine_midi_anchors(path: Optional[Path]) -> Optional[Tuple[float, float]]:
    """Return first-note and last-note times from fine-aligned MIDI.

    music21 is intentionally optional.  If it is unavailable or a MIDI file
    is malformed, the GP5 tempo timeline remains the safe fallback.
    """
    if path is None or not path.exists():
        return None
    try:
        from music21 import chord, converter, note

        score = converter.parse(str(path))
        records = []
        for part in score.parts:
            for record in part.flatten().secondsMap:
                element = record["element"]
                if isinstance(element, (note.Note, chord.Chord)):
                    records.append(record)
        if not records:
            return None
        first = min(float(record["offsetSeconds"]) for record in records)
        last = max(float(record["endTimeSeconds"]) for record in records)
        if not (math.isfinite(first) and math.isfinite(last) and last > first):
            return None
        return first, last
    except Exception:
        return None


def align_times(notes: List[dict], anchors: Optional[Tuple[float, float]]) -> str:
    if not notes or anchors is None:
        return "gp5_tempo"
    raw_first = min(row["start"] for row in notes)
    raw_last = max(row["end"] for row in notes)
    fine_first, fine_last = anchors
    if not (raw_last > raw_first and fine_last > fine_first):
        return "gp5_tempo"
    scale = (fine_last - fine_first) / (raw_last - raw_first)
    for row in notes:
        row["start"] = fine_first + (row["start"] - raw_first) * scale
        row["end"] = fine_first + (row["end"] - raw_first) * scale
    return "affine_fine_midi"


def safe_link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing path: {destination}")
    destination.symlink_to(source.resolve())


def write_csv(path: Path, rows: Iterable[dict], columns: Sequence[str] = CORE_COLUMNS) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/home/ajou/yigyu/guitar_project/tablature/data/GOAT"),
        help="Extracted GOAT directory containing metadata.csv and data/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/home/ajou/yigyu/3/data/moum_goat"),
        help="Separate moum-shaped output directory; existing paths are never overwritten.",
    )
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    metadata_path = source / "metadata.csv"
    if not metadata_path.exists():
        raise SystemExit(f"GOAT metadata not found: {metadata_path}")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output is not empty; choose a new path: {output}")

    guitarpro = import_guitarpro()
    with metadata_path.open(newline="", encoding="utf-8-sig") as handle:
        metadata = list(csv.DictReader(handle))
    metadata.sort(key=lambda row: row["item"])

    output_audio = output / "audio"
    output_annotation = output / "annotation"
    raw_annotation = output_annotation / "GOAT_raw"
    output_audio.mkdir(parents=True, exist_ok=True)
    output_annotation.mkdir(parents=True, exist_ok=True)
    raw_annotation.mkdir(parents=True, exist_ok=True)

    item_reports: List[dict] = []
    note_type_total: Counter = Counter()
    pitch_total: Counter = Counter()
    variant_audio_count: Counter = Counter()
    variant_item_count: Counter = Counter()
    split_item_count: Counter = Counter()
    split_audio_count: Counter = Counter()
    alignment_count: Counter = Counter()
    total_notes = 0
    total_clipped_notes = 0
    total_dropped_notes = 0
    csv_names = (
        "goat_notes.csv",
        "goat_notes_di.csv",
        "integrated_guitar_data.csv",
        "train_guitar_data.csv",
        "test_guitar_data.csv",
        "train_guitar_data_di.csv",
        "test_guitar_data_di.csv",
    )
    csv_counts: Counter = Counter()

    with ExitStack() as stack:
        writers = {}
        for filename in csv_names:
            handle = stack.enter_context(
                (output_annotation / filename).open("w", newline="", encoding="utf-8")
            )
            writer = csv.DictWriter(handle, fieldnames=CORE_COLUMNS)
            writer.writeheader()
            writers[filename] = writer

        for row in metadata:
            item = row["item"].strip()
            gp5_path = resolve_goat_path(source, row["gp5_path"].strip())
            if gp5_path is None or not gp5_path.exists():
                raise SystemExit(f"Missing GP5 for {item}: {row['gp5_path']}")

            notes, tempo_events, note_types = parse_gp5(gp5_path, guitarpro)
            fine_path = resolve_goat_path(source, row["finealigned_midi_path"].strip())
            anchors = fine_midi_anchors(fine_path)
            alignment = align_times(notes, anchors)
            alignment_count[alignment] += 1

            audio_sources = []
            for variant, metadata_key in AUDIO_VARIANTS:
                audio_path = resolve_goat_path(source, row[metadata_key].strip())
                if audio_path is None or not audio_path.exists():
                    raise SystemExit(f"Missing {metadata_key} for {item}: {row[metadata_key]}")
                destination = output_audio / variant / f"{item}.wav"
                safe_link(audio_path, destination)
                audio_sources.append((variant, audio_path))
                variant_audio_count[variant] += 1
                variant_item_count[variant] += 1
                split_audio_count[row["split"].strip()] += 1

            audio_duration = read_wav_duration(audio_sources[0][1])
            notes_before_clip = len(notes)
            clipped_notes = 0
            dropped_notes = 0
            valid_notes = []
            for note in notes:
                start = max(0.0, float(note["start"]))
                end = max(0.0, float(note["end"]))
                if audio_duration is not None:
                    if start >= audio_duration:
                        dropped_notes += 1
                        continue
                    if end > audio_duration:
                        end = audio_duration
                        clipped_notes += 1
                if end <= start:
                    dropped_notes += 1
                    continue
                note["start"] = start
                note["end"] = end
                valid_notes.append(note)
            notes = valid_notes
            total_clipped_notes += clipped_notes
            total_dropped_notes += dropped_notes
            note_type_total.update(note["note_type"] for note in notes)
            pitch_total.update(note["pitch"] for note in notes)
            total_notes += len(notes)

            # Keep all original annotation formats reachable without duplicating
            # the 16 GB release.  They are deliberately not mixed into the CSV.
            for key in (
                "gp_path",
                "gp5_path",
                "dadagp_path",
                "unaligned_midi_path",
                "finealigned_midi_path",
            ):
                raw_path = resolve_goat_path(source, row[key].strip())
                if raw_path is not None and raw_path.exists():
                    safe_link(raw_path, raw_annotation / raw_path.name)

            split = row["split"].strip().lower()
            split_item_count[split] += 1
            item_report = {
                "item": item,
                "split": split,
                "notes": len(notes),
                "notes_before_audio_clip": notes_before_clip,
                "notes_clipped_to_audio": clipped_notes,
                "notes_dropped_after_audio": dropped_notes,
                "tempo_events": len(tempo_events),
                "alignment": alignment,
                "fine_midi_anchors": anchors,
                "audio_duration_seconds": audio_duration,
                "tuning_class": row.get("tuning_class", "").strip(),
                "guitar_brand": row.get("guitar_brand", "").strip(),
                "player": row.get("player", "").strip(),
            }
            item_reports.append(item_report)

            for variant, _audio_path in audio_sources:
                uid = f"{variant}_{item}"
                for note in notes:
                    note_row = {
                        "unique_id": uid,
                        "directory_name": variant,
                        "audio_name": item,
                        "string": note["string"],
                        "start": f"{max(0.0, note['start']):.9f}",
                        "end": f"{max(0.0, note['end']):.9f}",
                        "pitch": note["pitch"],
                        "source": "GOAT",
                    }
                    for filename in ("goat_notes.csv", "integrated_guitar_data.csv"):
                        writers[filename].writerow(note_row)
                        csv_counts[filename] += 1
                    if variant == "GOAT_DI":
                        writers["goat_notes_di.csv"].writerow(note_row)
                        csv_counts["goat_notes_di.csv"] += 1
                    split_filename = f"{split}_guitar_data.csv"
                    writers[split_filename].writerow(note_row)
                    csv_counts[split_filename] += 1
                    split_di_filename = f"{split}_guitar_data_di.csv"
                    if variant == "GOAT_DI":
                        writers[split_di_filename].writerow(note_row)
                        csv_counts[split_di_filename] += 1

    # Add a path-corrected metadata table for later experiments.  The original
    # metadata values are retained for provenance; local_* columns are resolved
    # paths in the extracted source tree.
    metadata_columns = list(metadata[0].keys()) + [
        "local_data_directory",
        "audio_duration_seconds",
        "conversion_alignment",
        "converted_note_count",
    ]
    metadata_rows = []
    report_by_item = {report["item"]: report for report in item_reports}
    for row in metadata:
        item_report = report_by_item[row["item"]]
        out_row = dict(row)
        out_row.update(
            {
                "local_data_directory": str(source / "data" / row["item"]),
                "audio_duration_seconds": item_report["audio_duration_seconds"],
                "conversion_alignment": item_report["alignment"],
                "converted_note_count": item_report["notes"],
            }
        )
        metadata_rows.append(out_row)
    write_csv(output_annotation / "GOAT_metadata.csv", metadata_rows, metadata_columns)

    below_v1_range = sum(value for pitch, value in pitch_total.items() if pitch < 40)
    above_v1_range = sum(value for pitch, value in pitch_total.items() if pitch > 88)
    report = {
        "source": str(source),
        "output": str(output),
        "source_format": "Guitar Pro 5 (.gp5)",
        "label_interpretation": {
            "string_mapping": "GP s1(high e) -> moum string 5; GP s6(low E) -> moum string 0",
            "pitch": "GP note.realValue using the score's actual string tuning",
            "duration": "GP beat duration",
            "time": "GP5 tempo map; affine first/last-note correction from fine-aligned MIDI when available",
        },
        "items": {
            "total": len(metadata),
            "train": split_item_count["train"],
            "test": split_item_count["test"],
        },
        "audio": {
            "variants": [variant for variant, _ in AUDIO_VARIANTS],
            "audio_symlinks": sum(variant_audio_count.values()),
            "train_audio_tracks": split_audio_count["train"],
            "test_audio_tracks": split_audio_count["test"],
            "copied_bytes": 0,
            "note": "Audio is symlinked to the extracted GOAT release; keep the source directory in place.",
        },
        "notes": {
            "per_di_track": total_notes,
            "csv_rows_all_variants": csv_counts["goat_notes.csv"],
            "notes_clipped_to_audio": total_clipped_notes,
            "notes_dropped_after_audio": total_dropped_notes,
            "note_types": dict(note_type_total),
            "pitch_min": min(pitch_total),
            "pitch_max": max(pitch_total),
            "below_current_v1_min_midi_40": below_v1_range,
            "above_current_v1_max_midi_88": above_v1_range,
        },
        "alignment": dict(alignment_count),
        "csv_rows": csv_counts,
        "items_detail": item_reports,
    }
    (output / "conversion_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    readme = f"""# GOAT in moum layout

Generated from `{source}`.

This is a separate output tree; the existing `moum` data was not modified.
Audio files are symbolic links to the extracted GOAT release, so the source
directory must remain available.

## Layout

```text
{output}/
  audio/
    GOAT_DI/item_0.wav
    GOAT_amp_1/item_0.wav ... GOAT_amp_5/item_0.wav
  annotation/
    integrated_guitar_data.csv
    train_guitar_data.csv
    test_guitar_data.csv
    goat_notes_di.csv
    GOAT_metadata.csv
    GOAT_raw/               # GP5, GP, DadaGP text and MIDI symlinks
```

The canonical manifests contain the DI recording plus five amplifier
variants.  `*_di.csv` contains only the DI recording for a clean baseline.
The official GOAT train/test item split is preserved across all variants, so
amplifier renders from one item never cross the split boundary.

The CSV uses the current Conformer v1 schema:
`unique_id,directory_name,audio_name,string,start,end,pitch,source`.
GP strings are converted from GP's high-to-low numbering to moum's
low-to-high zero-based numbering.  Pitches use each GP5 score's actual string
tuning.  The current v1 loader's MIDI range is 40--88; rows outside that range
are retained in the CSV but are ignored by that loader until its range is
expanded.

See `conversion_report.json` for counts and per-item alignment details.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")

    print(json.dumps({
        "output": str(output),
        "items": len(metadata),
        "di_notes": total_notes,
        "audio_tracks": sum(variant_audio_count.values()),
        "csv_rows": csv_counts,
        "alignment": dict(alignment_count),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
