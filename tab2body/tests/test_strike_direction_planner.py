from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_goal_compiler import (
    DIRECTION_DOWN,
    DIRECTION_UP,
    STRIKE_DIRECTION_PROFILE,
    STRIKE_PLAN_SCHEMA,
    compile_strike_events,
)
from env.strike_goals import StrikeGoalSequence
from tools.build_strike_plan import build_strike_plan


def raw(events):
    return {
        "schema": "tab2body.strike_training.v2",
        "metadata": {"fps": 60},
        "events": events,
    }


def main():
    phrase = raw([
        {"time": 0.000, "frame": 0, "string": 5},
        {"time": 0.020, "frame": 1, "string": 4},
        {"time": 0.040, "frame": 2, "string": 3},
        {"time": 0.300, "frame": 18, "string": 2},
        {"time": 0.360, "frame": 22, "string": 2},
        {"time": 0.420, "frame": 25, "string": 2},
    ])
    compiled = compile_strike_events(
        phrase["events"], fps=60, rearm_min_frames=2,
        follow_through_min_frames=1, initial_timing_tolerance_ms=100)
    assert compiled.events[0].gesture == "strum"
    assert compiled.events[0].direction == DIRECTION_DOWN
    assert compiled.events[0].traversal_strings == (5, 4, 3)
    assert compiled.events[0].direction_source == "onset_order"
    later = [event.direction for event in compiled.events[1:]]
    assert DIRECTION_DOWN in later and DIRECTION_UP in later

    plan = build_strike_plan(phrase)
    assert plan["schema"] == STRIKE_PLAN_SCHEMA
    assert set(plan["events"][0]) >= {
        "time", "frame", "gesture", "strings", "direction"}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "strike_plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        goals = StrikeGoalSequence(path, device="cpu")
        assert goals.validation_metadata["direction_profile"] == (
            STRIKE_DIRECTION_PROFILE)
        assert torch.equal(
            goals.direction,
            torch.tensor([event.direction for event in compiled.events]))
        assert goals.traversal_mask[0, 3:6].all()
        traversal = compiled.events[0]
        assert traversal.traversal_offsets_s[0] < 0.0
        assert traversal.traversal_offsets_s[-1] > 0.0
        assert torch.allclose(
            goals.traversal_offset[0, list(traversal.traversal_strings)],
            torch.tensor(traversal.traversal_offsets_s), atol=1e-6)
        assert abs(sum(traversal.source_times_s) / 3 - traversal.time_s) < 1e-12

        broken = json.loads(json.dumps(plan))
        broken["events"][0]["direction"] = "up"
        path.write_text(json.dumps(broken), encoding="utf-8")
        try:
            StrikeGoalSequence(path, device="cpu")
        except ValueError as exc:
            assert "direction/traversal mismatch" in str(exc)
        else:
            raise AssertionError("direction/traversal mismatch was accepted")

    no_recross = compile_strike_events([
        {"time": 0.0000, "frame": 0, "string": 4},
        {"time": 0.0580, "frame": 3, "string": 3},
        {"time": 0.0580, "frame": 3, "string": 2},
        {"time": 0.0580, "frame": 3, "string": 1},
        {"time": 0.1161, "frame": 7, "string": 0},
    ], fps=60, rearm_min_frames=2, follow_through_min_frames=1,
        initial_timing_tolerance_ms=100)
    assert tuple(event.direction for event in no_recross.events) == (
        DIRECTION_DOWN, DIRECTION_DOWN, DIRECTION_DOWN)
    assert tuple(
        transition.transfer_crossed_strings
        for transition in no_recross.transition_diagnostics()) == ((), ())
    assert tuple(round(transition.edge_gap_s, 4)
                 for transition in no_recross.transition_diagnostics()) == (
                     0.0510, 0.0511)
    assert all(
        not transition.clearance_required
        for transition in no_recross.transition_diagnostics())

    upward_evidence = compile_strike_events([
        {"time": 0.000, "frame": 0, "string": 0},
        {"time": 0.020, "frame": 1, "string": 1},
        {"time": 0.040, "frame": 2, "string": 2},
    ], fps=60, rearm_min_frames=2, follow_through_min_frames=1,
        initial_timing_tolerance_ms=100)
    assert upward_evidence.events[0].direction == DIRECTION_UP
    assert upward_evidence.events[0].direction_source == "onset_order"

    print("PASS: path-aware phrase directions compile into an immutable StrikePlan")


if __name__ == "__main__":
    main()
