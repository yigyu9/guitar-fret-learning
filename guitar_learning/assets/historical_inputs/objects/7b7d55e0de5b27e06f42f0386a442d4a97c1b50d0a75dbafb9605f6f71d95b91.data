"""곡의 고유 손모양 목록과 검증된 자세 캐시를 라이브러리로 묶는다."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch


def chord_key(frame):
    targets = []
    for string, (fret, finger, barre) in enumerate(zip(
            frame["fret_goal"], frame["finger_goal"],
            frame["barre_goal"]), start=1):
        if int(fret) > 0:
            targets.append((int(finger), string, int(fret), bool(barre)))
    return tuple(sorted(targets))


def chord_catalog(goal):
    catalog = {}
    for frame in goal["frames"]:
        key = chord_key(frame)
        if not key:
            continue
        record = catalog.setdefault(key, {
            "targets": [list(value) for value in key],
            "first_frame": int(frame["frame"]),
            "occurrences": 0,
        })
        record["occurrences"] += 1
    return sorted(
        catalog.values(),
        key=lambda row: (row["first_frame"], row["targets"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--output")
    args = parser.parse_args()

    goal_path = Path(args.goal).expanduser().resolve()
    goal_bytes = goal_path.read_bytes()
    goal = json.loads(goal_bytes)
    output = (
        Path(args.output).expanduser().resolve()
        if args.output else goal_path.with_name("fret_pose_library.pt"))
    success_rsi = None
    source_checkpoint = None
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint).expanduser().resolve()
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False)
        context = checkpoint.get("training_context", {})
        expected = hashlib.sha256(goal_bytes).hexdigest()
        if context.get("goal_sha256") != expected:
            raise ValueError("checkpoint and goal hashes do not match")
        success_rsi = checkpoint.get("environment_state", {}).get(
            "success_rsi")
        if success_rsi is None:
            raise ValueError("checkpoint has no fret success-pose cache")
        source_checkpoint = str(checkpoint_path)

    payload = {
        "schema": "digit.fret-pose-library.v1",
        "goal_path": str(goal_path),
        "goal_sha256": hashlib.sha256(goal_bytes).hexdigest(),
        "chord_catalog": chord_catalog(goal),
        "source_checkpoint": source_checkpoint,
        "success_rsi": success_rsi or {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output)
    print(f"saved={output} chord_shapes={len(payload['chord_catalog'])}")


if __name__ == "__main__":
    main()
