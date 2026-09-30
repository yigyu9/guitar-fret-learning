from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_goal_compiler import compile_strike_events, strike_plan_document
from env.strike_goals import validate_strike_training_data


def build_strike_plan(
        source_document, *, source_path=None, rearm_min_frames=2,
        follow_through_min_frames=1, initial_timing_tolerance_ms=100.0,
        window_fraction=0.45, reviewed_overrides=None,
        require_original_tempo_feasible=False,
        minimum_edge_gap_s=None, clearance_edge_gap_s=None):
    validation = validate_strike_training_data(source_document)
    embedded_overrides = source_document.get("reviewed_overrides")
    if reviewed_overrides is not None and embedded_overrides is not None:
        raise ValueError(
            "reviewed overrides must come from either the source document or "
            "the explicit argument, not both")
    selected_overrides = (
        embedded_overrides if reviewed_overrides is None else reviewed_overrides)
    compiled = compile_strike_events(
        source_document["events"], fps=validation["fps"],
        rearm_min_frames=rearm_min_frames,
        follow_through_min_frames=follow_through_min_frames,
        initial_timing_tolerance_ms=initial_timing_tolerance_ms,
        window_fraction=window_fraction,
        reviewed_overrides=selected_overrides)
    if require_original_tempo_feasible:
        compiled.require_feasible_original_tempo_transitions(
            minimum_edge_gap_s=minimum_edge_gap_s,
            clearance_edge_gap_s=clearance_edge_gap_s)
    source_sha256 = None
    if source_path:
        source_sha256 = hashlib.sha256(
            Path(source_path).read_bytes()).hexdigest()
    return strike_plan_document(
        compiled, fps=validation["fps"],
        source=(str(Path(source_path).resolve()) if source_path else None),
        source_sha256=source_sha256)


def build_parser():
    parser = argparse.ArgumentParser(
        description="compile raw strike events into a fixed phrase StrikePlan")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rearm-min-frames", type=int, default=2)
    parser.add_argument("--follow-through-min-frames", type=int, default=1)
    parser.add_argument("--initial-timing-tolerance-ms", type=float, default=100.0)
    parser.add_argument("--review-overrides", type=Path)
    parser.add_argument(
        "--require-original-tempo-feasible", action="store_true")
    parser.add_argument("--minimum-edge-gap-ms", type=float)
    parser.add_argument("--clearance-edge-gap-ms", type=float)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    source = json.loads(args.input.read_text(encoding="utf-8"))
    reviewed_overrides = None
    if args.review_overrides is not None:
        override_document = json.loads(
            args.review_overrides.read_text(encoding="utf-8"))
        reviewed_overrides = (
            override_document.get("reviewed_overrides")
            if isinstance(override_document, dict)
            else override_document)
    plan = build_strike_plan(
        source, source_path=args.input,
        rearm_min_frames=args.rearm_min_frames,
        follow_through_min_frames=args.follow_through_min_frames,
        initial_timing_tolerance_ms=args.initial_timing_tolerance_ms,
        reviewed_overrides=reviewed_overrides,
        require_original_tempo_feasible=
            args.require_original_tempo_feasible,
        minimum_edge_gap_s=(
            None if args.minimum_edge_gap_ms is None
            else args.minimum_edge_gap_ms / 1000.0),
        clearance_edge_gap_s=(
            None if args.clearance_edge_gap_ms is None
            else args.clearance_edge_gap_ms / 1000.0))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    counts = {
        "down": 0, "up": 0, "single_pick": 0, "strum": 0,
        "alternate_restrike": 0}
    for event in plan["events"]:
        counts[event["direction"]] += 1
        if event["gesture"] in counts:
            counts[event["gesture"]] += 1
    print(json.dumps({
        "out": str(args.out.resolve()),
        "source_events": len(source["events"]),
        "planned_events": len(plan["events"]),
        "counts": counts,
        "planner_total_cost": plan["metadata"]["planner_total_cost"],
        "infeasible_original_tempo_transitions": sum(
            not item["original_tempo_feasible"]
            for item in plan["transitions"]),
        "bridge_split_candidates": sum(
            item["bridge_split_candidate"] for item in plan["transitions"]),
    }, indent=2, ensure_ascii=False))
    return plan


if __name__ == "__main__":
    main()
