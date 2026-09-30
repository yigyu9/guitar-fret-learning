"""Register reviewed Stage1 outputs as a canonical per-song bundle.

The source Stage1 directory remains untouched. Re-running the command refreshes
the manifest and accepts already-copied files when their content is identical.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.song_bundles import bundle_path  # noqa: E402
from tab2body.env.strike_goal_compiler import (  # noqa: E402
    STRIKE_TRANSITION_PROFILE,
    compiled_strike_goal_from_plan_document,
)


STAGE1_TARGETS = {
    "*_mic.wav": "source/audio.wav",
    "*.notes.csv": "mapping/tablature.notes.csv",
    "*.fingering.json": "mapping/fingering.json",
    "*.chords.json": "mapping/chords.json",
    "*.notes.json": "mapping/notes.json",
    "*.fingering.png": "preview/fingering.png",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_reviewed(source: Path, target: Path, replace: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha256(source) == sha256(target):
            return
        if not replace:
            raise FileExistsError(
                f"{target} already exists with different content; use --replace")
    shutil.copy2(source, target)


def one_match(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise ValueError(
            f"{directory}: expected exactly one {pattern!r}, found {len(matches)}")
    return matches[0]


def infer_bpm(song_id: str) -> int | None:
    match = re.search(r"-(\d+)-", song_id)
    return int(match.group(1)) if match else None


def write_tablature_if_missing(root: Path) -> None:
    """Recover the canonical CSV when a legacy bundle only has fingering JSON."""
    target = root / "mapping" / "tablature.notes.csv"
    source = root / "mapping" / "fingering.json"
    if target.exists() or not source.is_file():
        return
    document = json.loads(source.read_text(encoding="utf-8"))
    notes = document.get("notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError(f"{source}: notes must be a non-empty array")
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("string", "start", "end", "pitch"))
        writer.writeheader()
        for index, note in enumerate(notes):
            try:
                writer.writerow({
                    "string": int(note["string"]),
                    "start": float(note["t_on"]),
                    "end": float(note["t_off"]),
                    "pitch": int(note["midi"]),
                })
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"{source}: invalid fingering note {index}") from exc


def strike_training_status(root: Path, fingering: dict | None) -> dict:
    raw = root / "training" / "strike_training.json"
    plan = root / "training" / "strike_plan.json"
    if raw.is_file() and plan.is_file():
        document = json.loads(plan.read_text(encoding="utf-8"))
        profile = document.get("metadata", {}).get(
            "direction_profile", "phrase_dp_microtiming_v3")
        unsupported = sum(
            event.get("gesture") == "alternate_restrike"
            for event in document.get("events", []))
        if unsupported:
            return {
                "state": "unsupported", "profile": profile,
                "reason": f"{unsupported} alternate_restrike event(s)"}
        compiled = compiled_strike_goal_from_plan_document(document)
        infeasible = tuple(
            item for item in compiled.transition_diagnostics(1.0)
            if not item.original_tempo_feasible)
        if infeasible:
            first = infeasible[0]
            return {
                "state": "infeasible",
                "profile": profile,
                "transition_profile": STRIKE_TRANSITION_PROFILE,
                "infeasible_transition_count": len(infeasible),
                "reason": (
                    f"transition {first.from_event_index}->"
                    f"{first.to_event_index} has only "
                    f"{first.edge_gap_s * 1000.0:.3f} ms after the previous "
                    "traversal edge"),
            }
        return {
            "state": "ready", "profile": profile,
            "transition_profile": STRIKE_TRANSITION_PROFILE,
        }
    if raw.is_file():
        return {
            "state": "plan_missing", "profile": "pick_gesture_compiler_v2",
            "reason": "strike_training.json exists but strike_plan.json is missing"}
    notes = fingering.get("notes", []) if fingering else []
    previous_time = None
    previous_frame = None
    for index, note in enumerate(notes):
        time_s = float(note["t_on"])
        frame = int(time_s * 60.0 + 0.5)
        if previous_time is not None and time_s <= previous_time:
            return {
                "state": "ineligible",
                "profile": "pick_monophonic_v1",
                "reason": (
                    f"notes {index - 1} and {index} have non-increasing onset "
                    f"{time_s:.6f}s; simultaneous notes require a future "
                    "strum/polyphonic mapper"),
            }
        if previous_frame is not None and frame <= previous_frame:
            return {
                "state": "ineligible",
                "profile": "pick_monophonic_v1",
                "reason": (
                    f"note {index} shares 60 Hz frame {frame} with the preceding "
                    "note; pick_monophonic_v1 allows one onset per frame"),
            }
        previous_time = time_s
        previous_frame = frame
    return {"state": "missing", "profile": "pick_monophonic_v1"}


def write_manifest(song_id: str, root: Path, provenance: dict | None = None) -> Path:
    files = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    diagnostics = []
    violations = []
    fingering = None
    fingering_path = root / "mapping" / "fingering.json"
    if fingering_path.is_file():
        fingering = json.loads(fingering_path.read_text(encoding="utf-8"))
        diagnostics = fingering.get("diagnostics", [])
        violations = fingering.get("violations", [])

    existing = root / "manifest.json"
    if provenance is None and existing.is_file():
        provenance = json.loads(existing.read_text(encoding="utf-8")).get(
            "provenance", {})
    payload = {
        "schema": "tab2body.song_bundle.v1",
        "song_id": song_id,
        "bpm": infer_bpm(song_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "source": "immutable audio and optional annotation",
            "mapping": "reviewed tablature and left-hand finger mapping",
            "training": "Isaac Gym fret/strike runtime goals",
            "preview": "human-readable renderings",
        },
        "provenance": provenance or {},
        "availability": {
            "tablature": (root / "mapping" / "tablature.notes.csv").is_file(),
            "fingering": fingering_path.is_file(),
            "fret_training": (root / "training" / "fret_training.json").is_file(),
            "strike_training": (root / "training" / "strike_training.json").is_file(),
            "strike_plan": (root / "training" / "strike_plan.json").is_file(),
        },
        "training_status": {
            "fret": {
                "state": (
                    "ready"
                    if (root / "training" / "fret_training.json").is_file()
                    else "missing")
            },
            "strike": strike_training_status(root, fingering),
        },
        "mapping_validation": {
            "n_diagnostics": len(diagnostics),
            "n_violations": len(violations),
            "diagnostics": diagnostics,
            "violations": violations,
        },
        "files": files,
    }
    existing.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return existing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="copy a reviewed Stage1 result into data/song_bundles")
    parser.add_argument("song_id")
    parser.add_argument(
        "--stage1", type=Path,
        help="Stage1 directory; omit to refresh an existing bundle manifest")
    parser.add_argument("--annotation", type=Path)
    parser.add_argument("--replace", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = bundle_path(args.song_id)
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("source", "mapping", "training", "preview"):
        (root / directory).mkdir(exist_ok=True)

    provenance = None
    if args.stage1 is not None:
        stage1 = args.stage1.resolve()
        if not stage1.is_dir():
            raise FileNotFoundError(f"Stage1 directory not found: {stage1}")
        provenance = {
            "registered_from": str(stage1),
            "registration_mode": "reviewed_stage1_copy",
        }
        for pattern, relative in STAGE1_TARGETS.items():
            copy_reviewed(
                one_match(stage1, pattern), root / relative, args.replace)
    if args.annotation is not None:
        annotation = args.annotation.resolve()
        if not annotation.is_file():
            raise FileNotFoundError(f"annotation not found: {annotation}")
        copy_reviewed(
            annotation, root / "source" / "annotation.jams", args.replace)

    write_tablature_if_missing(root)
    manifest = write_manifest(args.song_id, root, provenance)
    print(json.dumps({
        "bundle": str(root),
        "manifest": str(manifest),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
