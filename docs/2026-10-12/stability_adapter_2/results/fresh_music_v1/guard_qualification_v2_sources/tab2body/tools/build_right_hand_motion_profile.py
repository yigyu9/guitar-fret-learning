from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping


SCHEMA = "tab2body.right_hand_reference_motion.v1"
PROFILE_SCHEMA = "tab2body.right_hand_motion_profile.v1"
PHASES = ("READY", "APPROACH", "RELEASE", "RECOVER")
GESTURES = ("single_pick", "strum")


def _quantile(values, probability):
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def build_motion_profile(document: Mapping[str, object], source_sha256: str):
    if document.get("schema") != SCHEMA:
        raise ValueError("unsupported right-hand reference motion schema")
    frames = document.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("right-hand reference motion requires frames")
    grouped = {}
    joint_names = None
    for index, frame in enumerate(frames):
        if not isinstance(frame, Mapping):
            raise ValueError(f"reference frame {index} must be an object")
        phase = frame.get("phase")
        gesture = frame.get("gesture")
        joints = frame.get("joint_positions_rad")
        confidence = frame.get("confidence", 1.0)
        if phase not in PHASES or gesture not in GESTURES:
            raise ValueError(f"reference frame {index} has invalid phase/gesture")
        if not isinstance(joints, Mapping) or not joints:
            raise ValueError(f"reference frame {index} requires joint positions")
        if isinstance(confidence, bool):
            raise ValueError("reference confidence must be in [0, 1]")
        confidence = float(confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("reference confidence must be in [0, 1]")
        names = tuple(sorted(joints))
        if joint_names is None:
            joint_names = names
        elif names != joint_names:
            raise ValueError("reference frames must share an exact joint set")
        values = {}
        for name in names:
            value = joints[name]
            if isinstance(value, bool):
                raise ValueError(f"reference joint {name} must be finite")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError(f"reference joint {name} must be finite")
            values[name] = value
        if confidence > 0.0:
            grouped.setdefault((gesture, phase), []).append(values)
    profiles = {}
    for (gesture, phase), samples in sorted(grouped.items()):
        key = f"{gesture}:{phase}"
        profiles[key] = {
            "gesture": gesture,
            "phase": phase,
            "frames": len(samples),
            "joints": {
                name: {
                    "p01_rad": _quantile(
                        [sample[name] for sample in samples], 0.01),
                    "p05_rad": _quantile(
                        [sample[name] for sample in samples], 0.05),
                    "median_rad": _quantile(
                        [sample[name] for sample in samples], 0.50),
                    "p95_rad": _quantile(
                        [sample[name] for sample in samples], 0.95),
                    "p99_rad": _quantile(
                        [sample[name] for sample in samples], 0.99),
                }
                for name in joint_names
            },
        }
    return {
        "schema": PROFILE_SCHEMA,
        "source_sha256": source_sha256,
        "source_kind": document.get("source_kind", "unknown"),
        "joint_names": list(joint_names or ()),
        "profiles": profiles,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    source = args.source.resolve()
    raw = source.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    profile = build_motion_profile(
        document, hashlib.sha256(raw).hexdigest())
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
