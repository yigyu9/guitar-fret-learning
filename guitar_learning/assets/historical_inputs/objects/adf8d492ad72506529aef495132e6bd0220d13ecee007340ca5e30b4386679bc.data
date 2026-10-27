"""GuitarSet JAMS 또는 검수된 fingering에서 fret 학습용 JSON을 만든다.

출력은 두 표현을 함께 보존한다.
  1) events: fingermapping의 왼손 press 이벤트
  2) frames: 60 Hz에서 바로 텐서화할 수 있는 줄별 goal과 완만한 hand position

실행 예:
  python3 -m tab2body.tools.build_fret_training_data \
    guitar_v3/data/moum/annotation/audio_mono-mic/02_Jazz1-200-B_solo.jams \
    --audio guitar_v3/data/moum/audio/audio_mono-mic/02_Jazz1-200-B_solo_mic.wav \
    --out data/song_bundles/02_Jazz1-200-B_solo/training/fret_training.json

  python3 -m tab2body.tools.build_fret_training_data \
    --fingering data/song_bundles/<song_id>/mapping/fingering.json \
    --audio data/song_bundles/<song_id>/source/audio.wav \
    --out data/song_bundles/<song_id>/training/fret_training.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FM_DIR = ROOT / "tab2fingermapping" / "fingermapping"
sys.path.insert(0, str(FM_DIR))
import run_fingering  # noqa: E402


OPEN_MIDI = [40, 45, 50, 55, 59, 64]  # annotation string 0=low-E
FPS = 60
MAX_FRET = 22
ALLOW_BARRE = False             # S0: schema remains extensible, runtime target does not use barre
POSITION_PREP_S = 0.25
POSITION_MARGIN_LOW = 1
POSITION_WINDOW = 6
FRET_Y_GUITAR = {
    1: 0.18162, 2: 0.14871, 3: 0.11764, 4: 0.088313,
    5: 0.060633, 6: 0.034506, 7: 0.009846, 8: -0.01343,
    9: -0.035399, 10: -0.056136, 11: -0.075708, 12: -0.094182,
    13: -0.11162, 14: -0.12808, 15: -0.14361, 16: -0.15828,
    17: -0.17212, 18: -0.18518, 19: -0.19751, 20: -0.20915,
    21: -0.22013, 22: -0.2305,
}
WRIST_HIGH_E_OFFSET = 0.075
WRIST_NUT_SIDE_OFFSET = 0.024
WRIST_BACK_Z = -0.0227
WRIST_SOFT_RADIUS = 0.04


def load_jams_notes(path: Path) -> list[dict]:
    """GuitarSet의 string별 note_midi annotation을 tab note로 변환."""
    raw = json.loads(path.read_text())
    notes = []
    unsupported = []
    for ann in raw["annotations"]:
        if ann.get("namespace") != "note_midi":
            continue
        string = int(ann["annotation_metadata"]["data_source"])
        if not 0 <= string < len(OPEN_MIDI):
            raise ValueError(f"annotation string {string} is outside the six-string contract")
        for item in ann["data"]:
            midi = int(round(float(item["value"])))
            fret = midi - OPEN_MIDI[string]
            if not 0 <= fret <= MAX_FRET:
                unsupported.append((string, fret, float(item["time"])))
            else:
                t_on = float(item["time"])
                notes.append({
                    "string": string,
                    "start": t_on,
                    "end": t_on + float(item["duration"]),
                    "pitch": midi,
                    "fret": fret,
                })
    if unsupported:
        preview = ", ".join(
            f"string={string}, fret={fret}, t={time:.4f}"
            for string, fret, time in unsupported[:5])
        raise ValueError(
            f"annotation contains {len(unsupported)} fret target(s) outside the "
            f"physical asset range 0..{MAX_FRET}: {preview}")
    return sorted(notes, key=lambda n: (n["start"], n["string"]))


def load_fingering_notes(document: dict) -> list[dict]:
    """Normalize the reviewed ``fingering.notes`` representation."""
    source = document.get("notes")
    if not isinstance(source, list) or not source:
        raise ValueError("fingering notes must be a non-empty array")
    notes = []
    for index, note in enumerate(source):
        try:
            string = int(note["string"])
            start = float(note["t_on"])
            end = float(note["t_off"])
            fret = int(note["fret"])
            pitch = int(note.get("midi", OPEN_MIDI[string] + fret))
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"invalid fingering note {index}: {note!r}") from exc
        if not 0 <= string < len(OPEN_MIDI):
            raise ValueError(f"fingering note {index}: string must be 0..5")
        if not 0 <= fret <= MAX_FRET:
            raise ValueError(
                f"fingering note {index}: fret {fret} is outside 0..{MAX_FRET}")
        if not (math.isfinite(start) and math.isfinite(end) and end > start):
            raise ValueError(
                f"fingering note {index}: invalid interval {start}..{end}")
        notes.append({
            "string": string,
            "start": start,
            "end": end,
            "pitch": pitch,
            "fret": fret,
        })
    return sorted(notes, key=lambda n: (n["start"], n["string"]))


def write_fingering_inputs(notes: list[dict], directory: Path) -> tuple[Path, Path]:
    csv_path = directory / "annotation.notes.csv"
    chord_path = directory / "annotation.chords.json"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["string", "start", "end", "pitch"])
        writer.writeheader()
        writer.writerows({k: n[k] for k in writer.fieldnames} for n in notes)
    duration = max((n["end"] for n in notes), default=0.0)
    chord_path.write_text(json.dumps({
        "fps": 86.1328125,
        "source": "GuitarSet annotation; chord-independent N segment",
        "segments": [{"t0": 0.0, "t1": duration + 1e-3, "label": "N", "conf": 0}],
    }, indent=1))
    return csv_path, chord_path


def infer_position_states(hand: list[dict], duration: float) -> list[dict]:
    """운지 P를 넓은 6프렛 hand-position band로 바꾸고 같은 구간을 병합."""
    raw = []
    last_anchor = None
    for state in hand:
        if state["P"] is not None:
            last_anchor = max(1, min(MAX_FRET, int(state["P"])))
        if last_anchor is None:
            continue
        lo = max(1, last_anchor - POSITION_MARGIN_LOW)
        hi = min(MAX_FRET, lo + POSITION_WINDOW - 1)
        lo = max(1, hi - POSITION_WINDOW + 1)
        raw.append({
            "t": float(state["t"]),
            "anchor_fret": last_anchor,
            "center_fret": round((lo + hi) / 2.0, 3),
            "allowed_fret_range": [lo, hi],
        })
    if not raw:
        return []
    merged = []
    for state in raw:
        key = (state["anchor_fret"], tuple(state["allowed_fret_range"]))
        if merged and merged[-1]["_key"] == key:
            continue
        state["_key"] = key
        merged.append(state)
    for i, state in enumerate(merged):
        state["t_start"] = state.pop("t")
        state["t_end"] = merged[i + 1]["t"] if i + 1 < len(merged) else duration
        state.pop("_key")
    return merged


def position_at(t: float, states: list[dict]) -> tuple[float, list[int]]:
    if not states:
        return 1.0, [1, POSITION_WINDOW]
    idx = max(0, next((i - 1 for i, s in enumerate(states) if s["t_start"] > t), len(states) - 1))
    cur = states[idx]
    anchor = float(cur["anchor_fret"])
    if idx + 1 < len(states):
        nxt = states[idx + 1]
        prep_start = max(cur["t_start"], nxt["t_start"] - POSITION_PREP_S)
        if t >= prep_start and nxt["t_start"] > prep_start:
            alpha = (t - prep_start) / (nxt["t_start"] - prep_start)
            anchor += alpha * (float(nxt["anchor_fret"]) - anchor)
    lo = max(1, min(MAX_FRET - POSITION_WINDOW + 1,
                    int(math.floor(anchor)) - POSITION_MARGIN_LOW))
    return round(anchor, 4), [lo, lo + POSITION_WINDOW - 1]


def fret_y_at(anchor):
    """Interpolate the actual guitar-asset fret-wire local-y coordinate."""
    anchor = max(1.0, min(float(MAX_FRET), float(anchor)))
    lo = int(math.floor(anchor))
    hi = min(MAX_FRET, lo + 1)
    alpha = anchor - lo
    return (1.0 - alpha) * FRET_Y_GUITAR[lo] + alpha * FRET_Y_GUITAR[hi]


def build_hand_position_targets(frames):
    """Build a per-song wrist soft target from its own hand-anchor timeline."""
    target_frames = []
    for frame in frames:
        anchor = float(frame["hand_anchor_fret"])
        target_frames.append({
            "frame": int(frame["frame"]),
            "t": float(frame["t"]),
            "anchor_fret": anchor,
            "allowed_fret_range": list(frame["hand_allowed_fret_range"]),
            "wrist_pos_guitar": [
                WRIST_HIGH_E_OFFSET,
                round(fret_y_at(anchor) + WRIST_NUT_SIDE_OFFSET, 6),
                WRIST_BACK_Z,
            ],
            "allowed_radius_m": WRIST_SOFT_RADIUS,
        })
    return {
        "schema": "tab2body.hand_position_targets.v1",
        "coordinate_frame": "guitar local",
        "method": "per-song hand anchor + actual guitar_asset fret-wire y",
        "offsets_m": {
            "high_e_side": WRIST_HIGH_E_OFFSET,
            "nut_side": WRIST_NUT_SIDE_OFFSET,
            "back_z": WRIST_BACK_Z,
            "soft_radius": WRIST_SOFT_RADIUS,
        },
        "frames": target_frames,
    }


def release_windows(presses: list[dict]) -> list[dict]:
    """Return intentional NO_PRESS gaps before the next press on each string.

    Same-position retriggers that should stay held are already merged upstream by
    ``press_events``.  Therefore, any remaining event boundary is an intentional
    release.  If another event follows on the string, the gap from the current
    ``t_release`` to the next ``t_press`` becomes NO_PRESS.  After the final event
    there is no future movement requirement, so the goal returns to DONT_CARE.
    """
    by_string = {string: [] for string in range(6)}
    for event in presses:
        by_string[int(event["string"])].append(event)

    windows = []
    for string, events in by_string.items():
        events.sort(key=lambda e: (float(e["t_press"]), float(e["t_release"])))
        for current, following in zip(events, events[1:]):
            start = float(current["t_release"])
            end = float(following["t_press"])
            if end > start:
                windows.append({
                    "string": string,
                    "t_start": start,
                    "t_end": end,
                    "released_fret": int(current["fret"]),
                    "next_fret": int(following["fret"]),
                })
    return sorted(windows, key=lambda w: (w["t_start"], w["string"]))


def rasterize(notes: list[dict], presses: list[dict], positions: list[dict], duration: float) -> list[dict]:
    """JSON string 순서를 Isaac goal 순서(high-e→low-E)로 반전해 60Hz화."""
    frames = []
    releases = release_windows(presses)
    ordered_presses = sorted(presses, key=lambda e: (float(e["t_press"]),
                                                      float(e["t_release"])))
    n_frames = int(math.ceil(duration * FPS)) + 1
    for frame in range(n_frames):
        t = frame / FPS
        fret_goal = [0] * 6       # 0=DONT_CARE, -1=NO_PRESS(open/release), f>=1=PRESS
        finger_goal = [0] * 6
        barre_goal = [False] * 6
        for note in notes:
            if note["fret"] == 0 and note["start"] <= t < note["end"]:
                fret_goal[5 - note["string"]] = -1
        # R5: after an intentional release, require no physical fret press until the
        # next event's preparation window begins.  Active PRESS always takes priority.
        for window in releases:
            if window["t_start"] <= t < window["t_end"]:
                fret_goal[5 - window["string"]] = -1
        for event in ordered_presses:
            if event["t_press"] <= t < event["t_release"]:
                goal_idx = 5 - event["string"]
                fret_goal[goal_idx] = event["fret"]
                finger_goal[goal_idx] = event["finger"]
                barre_goal[goal_idx] = event["barre"]
        anchor, allowed = position_at(t, positions)
        frames.append({
            "frame": frame,
            "t": round(t, 4),
            "fret_goal": fret_goal,
            "finger_goal": finger_goal,
            "barre_goal": barre_goal,
            "hand_anchor_fret": anchor,
            "hand_anchor_norm": round((anchor - 1.0) / (MAX_FRET - 1.0), 6),
            "hand_allowed_fret_range": allowed,
        })
    return frames


def validate_builder_frames(frames: list[dict], allow_barre=ALLOW_BARRE) -> dict:
    """Fail fast before serializing a goal the S0 environment cannot execute."""
    max_fret = 0
    multistring_frames = 0
    for frame_idx, frame in enumerate(frames):
        for field in ("fret_goal", "finger_goal", "barre_goal"):
            if len(frame[field]) != 6:
                raise ValueError(f"frame {frame_idx}: {field} must have six entries")
        for string, (fret, finger, barre) in enumerate(zip(
                frame["fret_goal"], frame["finger_goal"], frame["barre_goal"])):
            if not isinstance(fret, int) or isinstance(fret, bool) or not -1 <= fret <= MAX_FRET:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: invalid fret target {fret!r}")
            if not isinstance(finger, int) or isinstance(finger, bool) or not 0 <= finger <= 4:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: invalid finger target {finger!r}")
            if not isinstance(barre, bool):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre target must be boolean")
            if (fret > 0) != (finger > 0):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: PRESS/finger mismatch")
            if barre and not allow_barre:
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre is disabled for S0")
            if barre and (fret <= 0 or finger != 1):
                raise ValueError(
                    f"frame {frame_idx}, string {string}: barre requires an "
                    "index-finger PRESS")
            max_fret = max(max_fret, fret)
        for finger in range(1, 5):
            active = [string for string in range(6)
                      if frame["finger_goal"][string] == finger
                      and frame["fret_goal"][string] > 0]
            if len(active) > 1:
                multistring_frames += 1
                if not allow_barre:
                    raise ValueError(
                        f"frame {frame_idx}, finger {finger}: multiple active strings "
                        f"{active} are not allowed in S0")
                frets = {frame["fret_goal"][string] for string in active}
                if (finger != 1 or len(frets) != 1
                        or not all(frame["barre_goal"][string] for string in active)
                        or active[-1] - active[0] + 1 != len(active)):
                    raise ValueError(
                        f"frame {frame_idx}, finger {finger}: inconsistent barre target")
    return {
        "contract_valid": True,
        "max_fret": max_fret,
        "multistring_finger_frames": multistring_frames,
        "allow_barre": bool(allow_barre),
    }


def complexity(notes: list[dict]) -> dict:
    groups = []
    for note in notes:
        if not groups or note["start"] - groups[-1][-1] > 0.05:
            groups.append([note["start"]])
        else:
            groups[-1].append(note["start"])
    frets = [n["fret"] for n in notes if n["fret"] > 0]
    return {
        "n_notes": len(notes),
        "max_onset_polyphony": max(map(len, groups), default=0),
        "used_strings": sorted({n["string"] for n in notes}),
        "fretted_range": [min(frets), max(frets)] if frets else None,
        "n_distinct_frets": len(set(frets)),
        "has_open_strings": any(n["fret"] == 0 for n in notes),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("annotation", type=Path, nargs="?")
    parser.add_argument(
        "--fingering", type=Path,
        help="검수된 mapping/fingering.json에서 직접 학습 입력 생성")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fingering-out", type=Path,
                        help="중간 원본 fingering.json도 보존할 경로")
    parser.add_argument("--hand-targets-out", type=Path,
                        help="기본값: fret_training.json 옆의 같은 곡 hand_position_targets.json")
    args = parser.parse_args(argv)

    if (args.annotation is None) == (args.fingering is None):
        raise SystemExit("annotation JAMS 또는 --fingering 중 하나만 지정해야 합니다")
    if args.fingering is not None:
        fingering = json.loads(args.fingering.read_text(encoding="utf-8"))
        notes = load_fingering_notes(fingering)
        input_path = args.fingering
        input_type = "reviewed tab2fingermapping fingering JSON"
    else:
        notes = load_jams_notes(args.annotation)
        if not notes:
            raise SystemExit("annotation에 유효한 note_midi가 없습니다")
        with tempfile.TemporaryDirectory(prefix="fret_training_", dir="/tmp") as tmp:
            csv_path, chord_path = write_fingering_inputs(notes, Path(tmp))
            fingering_path = Path(tmp) / "annotation.fingering.json"
            fingering = run_fingering.run(csv_path, chord_path, fingering_path)
        input_path = args.annotation
        input_type = "GuitarSet per-string note_midi ground truth"
    duration = max(n["end"] for n in notes)

    if args.fingering_out:
        args.fingering_out.parent.mkdir(parents=True, exist_ok=True)
        args.fingering_out.write_text(json.dumps(fingering, indent=1, ensure_ascii=False))

    keep = ("finger", "string", "fret", "barre", "t_press", "t_release", "strikes")
    events = [{k: event[k] for k in keep} for event in fingering["presses"]]
    positions = infer_position_states(fingering["hand"], duration)
    frames = rasterize(notes, events, positions, duration)
    frame_contract = validate_builder_frames(frames)
    output = {
        "schema": "tab2body.fret_training.v1",
        "metadata": {
            "audio": str(args.audio.resolve()),
            "mapping_input": str(input_path.resolve()),
            "mapping_input_type": input_type,
            "fps": FPS,
            "asset_max_fret": MAX_FRET,
            "allow_barre": ALLOW_BARRE,
            "duration": round(duration, 4),
            "string_convention_events": "0=low-E, 5=high-e",
            "string_convention_frame_goals": "index 0=high-e, 5=low-E (Isaac goal order)",
            "fret_encoding": "0=don't-care, -1=must-not-press/open, >=1=press fret",
            "release_transition": ("same-position retriggers are merged as PRESS; "
                                   "an intentional gap before another fret event is NO_PRESS; "
                                   "after the final event is DONT_CARE"),
            "finger_encoding": "0=none, 1=index, 2=middle, 3=ring, 4=pinky",
            "hand_position": "anchor=estimated index-finger fret; allowed range is a 6-fret soft band",
        },
        "selection": {
            "training_mode": "per-song trajectory optimization",
            "reason": "one policy repeatedly optimizes this fixed song and fingering timeline",
            "complexity": complexity(notes),
        },
        "events": events,
        "hand_positions": positions,
        "frames": frames,
        "validation": {
            "dropped_invalid_fret": fingering["stats"]["dropped_invalid_fret"],
            "n_events": len(events),
            "n_release_windows": len(release_windows(events)),
            "n_frames": len(frames),
            "frame_contract": frame_contract,
            "diagnostics": fingering["diagnostics"],
            "violations": fingering["violations"],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=1, ensure_ascii=False))
    hand_out = args.hand_targets_out
    if hand_out is None:
        suffix = ".fret_training.json"
        name = args.out.name
        if name == "fret_training.json":
            hand_name = "hand_position_targets.json"
        elif name.endswith(suffix):
            hand_name = name[:-len(suffix)] + ".hand_position_targets.json"
        else:
            hand_name = args.out.stem + ".hand_position_targets.json"
        hand_out = args.out.with_name(hand_name)
    hand_out.parent.mkdir(parents=True, exist_ok=True)
    hand_out.write_text(json.dumps(
        build_hand_position_targets(frames), indent=1, ensure_ascii=False))
    print(json.dumps({"out": str(args.out), "hand_targets_out": str(hand_out),
                      "selection": output["selection"],
                      "validation": output["validation"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
