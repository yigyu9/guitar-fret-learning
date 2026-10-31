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
    STRIKE_PLAN_SCHEMA,
    STRIKE_TRANSITION_PROFILE,
    STRIKE_TRANSITION_PROFILE_V1,
    compile_strike_events,
    compiled_strike_goal_from_plan_document,
    strike_plan_document,
)
from env.strike_goals import (
    STRIKE_TRAINING_SCHEMA_V2,
    STRIKE_TRAINING_SCHEMA_V3,
    StrikeGoalSequence,
    validate_strike_training_data,
)
from tools.build_strike_plan import build_strike_plan
from tools.build_strike_training_data import build_strike_training_data


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def bridge_events():
    return [
        {"time": 35.2595, "frame": 2116, "string": 5, "event_id": 147},
        {"time": 35.2943, "frame": 2118, "string": 0, "event_id": 148},
        {"time": 35.3408, "frame": 2120, "string": 1, "event_id": 149},
    ]


def compile_bridge(overrides=None):
    return compile_strike_events(
        bridge_events(), fps=60, rearm_min_frames=2,
        follow_through_min_frames=1,
        initial_timing_tolerance_ms=100,
        reviewed_overrides=overrides)


def main():
    compiled = compile_bridge()
    assert len(compiled.events) == 2
    assert compiled.events[0].gesture == "strum"
    assert compiled.events[0].protected_strings == (4, 3, 2, 1)
    transition = compiled.transition_diagnostics()[0]
    assert abs(transition.edge_gap_s - 0.0465) < 1e-9
    assert transition.required_edge_gap_s == 0.05
    assert transition.direction_reversal
    assert transition.next_entry_side == "high_e_side"
    assert transition.transfer_crossed_strings == (0,)
    assert not transition.same_string_restrike
    assert transition.clearance_required
    assert transition.rearm_required
    assert not transition.original_tempo_feasible
    assert transition.bridge_split_candidate
    expect_error(
        "bridge-split candidate",
        compiled.require_feasible_original_tempo_transitions)

    plan = strike_plan_document(compiled, fps=60)
    assert plan["schema"] == STRIKE_PLAN_SCHEMA
    assert plan["metadata"]["transition_profile"] == (
        STRIKE_TRANSITION_PROFILE)
    assert plan["transitions"][0]["bridge_split_candidate"]
    assert plan["transitions"][0]["rearm_required"]
    restored = compiled_strike_goal_from_plan_document(plan)
    assert restored.transition_diagnostics()[0] == transition

    old_plan = json.loads(json.dumps(plan))
    old_plan["metadata"].pop("transition_profile")
    old_plan.pop("transitions")
    old_plan.pop("reviewed_overrides")
    old_restored = compiled_strike_goal_from_plan_document(old_plan)
    assert old_restored.transition_diagnostics()[0].bridge_split_candidate

    same_string = compile_strike_events([
        {"time": 0.0, "frame": 0, "string": 2, "event_id": "same-a"},
        {"time": 0.1, "frame": 6, "string": 2, "event_id": "same-b"},
    ], fps=60, rearm_min_frames=2, follow_through_min_frames=1,
        initial_timing_tolerance_ms=100)
    same_transition = same_string.transition_diagnostics()[0]
    assert same_transition.same_string_restrike
    assert not same_transition.clearance_required
    assert same_transition.rearm_required
    same_plan = strike_plan_document(same_string, fps=60)
    legacy_transition_plan = json.loads(json.dumps(same_plan))
    legacy_transition_plan["metadata"]["transition_profile"] = (
        STRIKE_TRANSITION_PROFILE_V1)
    legacy_transition = legacy_transition_plan["transitions"][0]
    legacy_transition["clearance_required"] = True
    legacy_transition.pop("same_string_restrike")
    legacy_transition.pop("rearm_required")
    legacy_restored = compiled_strike_goal_from_plan_document(
        legacy_transition_plan)
    upgraded_transition = legacy_restored.transition_diagnostics()[0]
    assert upgraded_transition.same_string_restrike
    assert not upgraded_transition.clearance_required
    assert upgraded_transition.rearm_required
    assert legacy_restored.transition_profile == STRIKE_TRANSITION_PROFILE

    reviewed = [{
        "override_id": "source-chord-35s",
        "action": "merge",
        "source_event_ids": [147, 148, 149],
        "resolved_times_s": [35.27797, 35.28015, 35.28305],
        "reason": "source annotation and symbolic score agree on one chord",
        "evidence": {
            "kind": "source_annotation",
            "reference": "annotation-note-group-79",
        },
    }]
    corrected = compile_bridge(reviewed)
    assert len(corrected.events) == 1
    assert corrected.events[0].gesture == "strum"
    assert corrected.events[0].source_event_ids == (147, 148, 149)
    assert corrected.events[0].source_times_s == (
        35.27797, 35.28015, 35.28305)
    assert corrected.transition_diagnostics() == ()
    corrected_plan = strike_plan_document(corrected, fps=60)
    assert corrected_plan["reviewed_overrides"][0]["override_id"] == (
        "source-chord-35s")
    corrected_restored = compiled_strike_goal_from_plan_document(corrected_plan)
    assert corrected_restored.reviewed_overrides[0].reason.startswith("source")

    expect_error(
        "non-empty evidence",
        lambda: compile_bridge([{
            "action": "merge",
            "source_event_ids": [147, 148, 149],
            "reason": "unverified",
            "evidence": {},
        }]))

    close_events = [
        {"time": 0.0, "frame": 0, "string": 5, "event_id": "a"},
        {"time": 0.02, "frame": 1, "string": 4, "event_id": "b"},
    ]
    separated = compile_strike_events(
        close_events, fps=60, rearm_min_frames=2,
        follow_through_min_frames=1, initial_timing_tolerance_ms=100,
        reviewed_overrides=[{
            "action": "separate",
            "source_event_ids": ["a", "b"],
            "reason": "independent source attacks",
            "evidence": {"kind": "manual_audio_review", "reviewer": "test"},
        }])
    assert len(separated.events) == 2

    raw_v2 = {
        "schema": STRIKE_TRAINING_SCHEMA_V2,
        "metadata": {"fps": 60},
        "events": [{"time": 0.0, "frame": 0, "string": 5}],
    }
    assert validate_strike_training_data(raw_v2)["contract_valid"]
    fingering = {
        "notes": [{
            "t_on": 0.1,
            "string": 0,
            "event_id": "note-a",
            "source_time": 0.095,
            "time_uncertainty_s": 0.012,
            "source_ref": "annotation:7",
        }],
    }
    raw_v3 = build_strike_training_data(fingering)
    assert raw_v3["schema"] == STRIKE_TRAINING_SCHEMA_V3
    assert set(raw_v3["events"][0]) == {
        "time", "frame", "string", "event_id", "source_time",
        "time_uncertainty_s", "source_ref"}
    assert raw_v3["validation"]["maximum_time_uncertainty_s"] == 0.012

    source_document = {
        "schema": STRIKE_TRAINING_SCHEMA_V3,
        "metadata": {"fps": 60},
        "events": bridge_events(),
    }
    expect_error(
        "infeasible original-tempo strike transition",
        lambda: build_strike_plan(
            source_document, require_original_tempo_feasible=True))
    source_document["reviewed_overrides"] = reviewed
    corrected_document = build_strike_plan(
        source_document, require_original_tempo_feasible=True)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "strike_plan.json"
        path.write_text(json.dumps(corrected_document), encoding="utf-8")
        goals = StrikeGoalSequence(path, device="cpu")
        goals.require_feasible_original_tempo_transitions()
        assert goals.transition_edge_gap.numel() == 0
        assert goals.transition_bridge_split_candidate.dtype == torch.bool
        assert goals.transition_same_string_restrike.dtype == torch.bool
        assert goals.transition_rearm_required.dtype == torch.bool

    print("PASS: strike traversal-edge transition and reviewed override contract")


if __name__ == "__main__":
    main()
