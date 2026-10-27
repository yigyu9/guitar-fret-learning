from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tools.audit_strike_goal_quality import (
    AuditConfig,
    STATUS_AMBIGUOUS,
    STATUS_INFEASIBLE,
    STATUS_PASS,
    audit_bundle,
    audit_bundles,
    main as audit_main,
)


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _raw(notes, fps=60):
    return {
        "schema": "tab2body.strike_training.v2",
        "metadata": {"fps": fps},
        "events": [{
            "time": float(note["t_on"]),
            "frame": int(math.floor(float(note["t_on"]) * fps + 0.5)),
            "string": 5 - int(note["string"]),
        } for note in notes],
    }


def _plan_event(raw_events, source_ids, direction, traversal, offsets):
    source_times = [raw_events[index]["time"] for index in source_ids]
    strings = list(dict.fromkeys(
        raw_events[index]["string"] for index in source_ids))
    center = sum(source_times) / len(source_times)
    return {
        "time": center,
        "frame": int(math.floor(center * 60.0 + 0.5)),
        "gesture": "strum" if len(source_ids) > 1 else "single_pick",
        "strings": strings,
        "direction": direction,
        "traversal_strings": traversal,
        "protected_strings": [
            string_index for string_index in traversal
            if string_index not in strings],
        "source_event_ids": source_ids,
        "direction_source": "test",
        "direction_confidence": 1.0,
        "source_times_s": source_times,
        "traversal_offsets_s": offsets,
        "sweep_duration_s": max(offsets) - min(offsets),
        "timing_fit_rms_s": 0.0,
    }


def _plan(events, physical_gap_s=0.05, grouping_span_s=0.05):
    return {
        "schema": "tab2body.strike_plan.v4",
        "metadata": {
            "fps": 60,
            "planner_config": {"grouping_max_span_s": grouping_span_s},
        },
        "events": events,
        "timeline": {
            "original_times_s": [event["time"] for event in events],
            "easy_times_s": [event["time"] for event in events],
            "physical_min_gap_s": physical_gap_s,
            "matching_gap_s": 0.1,
            "window_fraction": 0.45,
        },
    }


def _jams(notes, onset_offsets=None):
    onset_offsets = onset_offsets or {}
    annotations = []
    for string_index in range(6):
        data = []
        for source_index, note in enumerate(notes):
            if note["string"] != string_index:
                continue
            data.append({
                "time": note["t_on"] + onset_offsets.get(source_index, 0.0),
                "duration": 0.1,
                "value": note["midi"],
                "confidence": None,
            })
        if data:
            annotations.append({
                "namespace": "note_midi",
                "annotation_metadata": {"data_source": str(string_index)},
                "data": data,
            })
    return {"annotations": annotations, "file_metadata": {}, "sandbox": {}}


def _bundle(root, name, notes, plan, include_jams=True):
    bundle = root / name
    raw = _raw(notes)
    _write_json(bundle / "mapping" / "fingering.json", {"notes": notes})
    _write_json(bundle / "training" / "strike_training.json", raw)
    _write_json(bundle / "training" / "strike_plan.json", plan(raw["events"]))
    if include_jams:
        _write_json(bundle / "source" / "annotation.jams", _jams(notes))
    return bundle


def _clean_bundle(root):
    notes = [
        {"t_on": 0.1, "string": 0, "midi": 40},
        {"t_on": 0.3, "string": 1, "midi": 45},
    ]

    def build(raw_events):
        events = [
            _plan_event(raw_events, [0], "down", [5], [0.0]),
            _plan_event(raw_events, [1], "up", [4], [0.0]),
        ]
        return _plan(events)

    return _bundle(root, "clean", notes, build)


def _ambiguous_bundle(root):
    notes = [
        {"t_on": 1.0, "string": 0, "midi": 40},
        {"t_on": 1.03, "string": 5, "midi": 64},
    ]

    def build(raw_events):
        event = _plan_event(
            raw_events, [0, 1], "down", [5, 4, 3, 2, 1, 0],
            [-0.015, -0.009, -0.003, 0.003, 0.009, 0.015])
        return _plan([event])

    return _bundle(root, "ambiguous", notes, build)


def _infeasible_bundle(root):
    notes = [
        {"t_on": 1.0, "string": 0, "midi": 40},
        {"t_on": 1.0348, "string": 5, "midi": 64},
        {"t_on": 1.0813, "string": 4, "midi": 59},
    ]

    def build(raw_events):
        events = [
            _plan_event(
                raw_events, [0, 1], "down", [5, 4, 3, 2, 1, 0],
                [-0.0174, -0.01044, -0.00348,
                 0.00348, 0.01044, 0.0174]),
            _plan_event(raw_events, [2], "up", [1], [0.0]),
        ]
        return _plan(events)

    return _bundle(root, "infeasible", notes, build)


def _reviewed_bundle(root, status="proposed_pending_audio_review"):
    notes = [
        {"t_on": 1.0, "string": 0, "midi": 40},
        {"t_on": 1.08, "string": 1, "midi": 45},
        {"t_on": 1.16, "string": 2, "midi": 50},
    ]
    raw = _raw(notes)
    raw["schema"] = "tab2body.strike_training.v3"
    override = {
        "override_id": "reviewed-source-chord",
        "action": "merge",
        "source_event_ids": [0, 1, 2],
        "resolved_times_s": [1.0, 1.005, 1.01],
        "reason": "source annotation confirms one three-string chord",
        "evidence": {
            "source": "annotation.jams",
            "manual_audio_review": "pending",
        },
    }
    raw["reviewed_overrides"] = [override]
    event = _plan_event(
        raw["events"], [0, 1, 2], "down", [5, 4, 3],
        [-0.005, 0.0, 0.005])
    event["input_times_s"] = [1.0, 1.08, 1.16]
    event["source_times_s"] = [1.0, 1.005, 1.01]
    event["time"] = 1.005
    event["frame"] = 60
    plan = _plan([event])
    plan["reviewed_overrides"] = [override]
    bundle = root / "reviewed"
    _write_json(bundle / "mapping" / "fingering.json", {"notes": notes})
    _write_json(bundle / "training" / "strike_training.json", raw)
    _write_json(bundle / "training" / "strike_plan.json", plan)
    _write_json(bundle / "source" / "annotation.jams", _jams(notes))
    _write_json(bundle / "training" / "strike_review.proposed.json", {
        "schema": "tab2body.strike_review.v1",
        "status": status,
        "reviewed_overrides": [override],
    })
    return bundle


def test_clean_bundle_passes_without_gpu_imports():
    with tempfile.TemporaryDirectory() as directory:
        report = audit_bundle(_clean_bundle(Path(directory)))
    assert report["status"] == STATUS_PASS
    assert report["input_consistency"]["mismatch_count"] == 0
    assert report["compiled_plan_consistency"]["issue_count"] == 0
    assert report["reference_onsets"]["matched_count"] == 2
    assert report["traversal_edge_gaps"]["below_physical_count"] == 0


def test_noncontiguous_inferred_strum_is_ambiguous_without_provenance():
    with tempfile.TemporaryDirectory() as directory:
        report = audit_bundle(_ambiguous_bundle(Path(directory)))
    assert report["status"] == STATUS_AMBIGUOUS
    assert len(report["noncontiguous_inferred_strums"]) == 1
    item = report["noncontiguous_inferred_strums"][0]
    assert item["audible_strings"] == [5, 0]
    assert item["inferred_intermediate_strings"] == [1, 2, 3, 4]
    assert not item["explicit_mute_or_span_provenance"]


def test_actual_edge_gap_and_reversal_make_dense_transition_infeasible():
    with tempfile.TemporaryDirectory() as directory:
        report = audit_bundle(_infeasible_bundle(Path(directory)))
    assert report["status"] == STATUS_INFEASIBLE
    bad_edges = [
        edge for edge in report["traversal_edge_gaps"]["edges"]
        if edge["below_physical_minimum"]]
    assert len(bad_edges) == 1
    assert bad_edges[0]["previous_plan_event"] == 0
    assert bad_edges[0]["current_plan_event"] == 1
    assert abs(bad_edges[0]["actual_edge_gap_ms"] - 46.5) < 1e-6
    assert abs(bad_edges[0]["deficit_ms"] - 3.5) < 1e-6
    grouping = report["ambiguous_grouping_boundaries"]
    assert any(
        item["left_source_event_id"] == 1
        and item["right_source_event_id"] == 2
        and "locally_below_physical_gap_but_split" in item["reasons"]
        for item in grouping)
    reversal = next(
        item for item in report["reversal_direct_paths"]
        if item["current_plan_event"] == 1)
    assert reversal["direction_reversal"]
    assert reversal["direct_path_intermediate_crossings"] == [0]
    assert reversal["previously_crossed_strings_requiring_rearm"] == [0]
    assert reversal["risk"] == "infeasible"


def test_reference_onset_delta_is_reported_and_classified():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        bundle = _clean_bundle(root)
        notes = json.loads(
            (bundle / "mapping" / "fingering.json").read_text())["notes"]
        _write_json(
            bundle / "source" / "annotation.jams",
            _jams(notes, onset_offsets={1: 0.08}))
        report = audit_bundle(bundle, AuditConfig(
            reference_ambiguous_delta_ms=50.0))
    assert report["status"] == STATUS_AMBIGUOUS
    reference = report["reference_onsets"]
    assert reference["matched_count"] == 2
    assert reference["large_delta_count"] == 1
    assert abs(reference["delta_summary"]["absolute_max_ms"] - 80.0) < 1e-6


def test_proposed_reviewed_override_is_valid_but_remains_ambiguous():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        bundle = _reviewed_bundle(root)
        pending = audit_bundle(bundle)
        review_path = bundle / "training" / "strike_review.proposed.json"
        review_document = json.loads(review_path.read_text(encoding="utf-8"))
        review_document["status"] = "approved"
        _write_json(review_path, review_document)
        approved = audit_bundle(bundle)
        plan_path = bundle / "training" / "strike_plan.json"
        unreviewed_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        unreviewed_plan.pop("reviewed_overrides")
        _write_json(plan_path, unreviewed_plan)
        unreviewed_resolution = audit_bundle(bundle)
    assert pending["status"] == STATUS_AMBIGUOUS
    assert not any(
        finding["severity"] == STATUS_INFEASIBLE
        for finding in pending["findings"])
    assert pending["compiled_plan_consistency"]["issue_count"] == 0
    assert abs(pending["compiled_plan_consistency"][
        "resolved_minus_input_onset_deltas"]["absolute_max_ms"] - 150.0) < 1e-6
    review = pending["reviewed_overrides"]
    assert review["top_level_status"] == "proposed_pending_audio_review"
    assert review["status_class"] == "pending"
    assert review["status_sources"] == [{
        "kind": "separate_review_document",
        "path": str((bundle / "training" /
                     "strike_review.proposed.json").resolve()),
        "status": "proposed_pending_audio_review",
        "matched_overrides": True,
    }]
    assert review["items"][0]["source_event_ids"] == [0, 1, 2]
    assert review["items"][0]["reason"].startswith("source annotation")
    assert review["items"][0]["evidence"]["manual_audio_review"] == "pending"
    assert approved["status"] == STATUS_PASS
    assert approved["reviewed_overrides"]["status_class"] == "approved"
    assert unreviewed_resolution["status"] == STATUS_INFEASIBLE
    assert any(
        sample.get("reason") == "unproven_resolved_source_time"
        for sample in unreviewed_resolution[
            "compiled_plan_consistency"]["issue_samples"])


def test_all_bundle_summary_and_strict_cli_exit():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        clean = _clean_bundle(root)
        infeasible = _infeasible_bundle(root)
        document = audit_bundles([clean, infeasible], root=root)
        assert document["summary"]["overall_status"] == STATUS_INFEASIBLE
        assert document["summary"]["status_counts"][STATUS_PASS] == 1
        assert document["summary"]["status_counts"][STATUS_INFEASIBLE] == 1
        output = io.StringIO()
        output_path = root / "artifacts" / "strike_goal_audit.json"
        with redirect_stdout(output):
            exit_code = audit_main([
                "--bundle", str(infeasible), "--format", "json",
                "--out", str(output_path), "--strict"])
        parsed = json.loads(output.getvalue())
        saved = output_path.read_text(encoding="utf-8")
    assert exit_code == 2
    assert parsed["summary"]["overall_status"] == STATUS_INFEASIBLE
    assert saved == output.getvalue()


def test_current_promoted_song_is_physically_feasible_read_only():
    bundle = PROJECT_ROOT / "data" / "song_bundles" / "00_SS1-68-E_comp"
    assert bundle.is_dir()
    report = audit_bundle(bundle)
    assert report["status"] == STATUS_AMBIGUOUS
    assert report["counts"]["compiled_plan_events"] == 104
    assert report["counts"]["strum_events"] == 43
    assert report["reviewed_overrides"]["top_level_status"] == (
        "approved_user_delegated")
    assert report["reviewed_overrides"]["status_class"] == "approved"
    assert report["reviewed_overrides"]["items"][0][
        "source_event_ids"] == [147, 148, 149]
    edges = report["traversal_edge_gaps"]
    assert edges["below_physical_count"] == 0
    assert abs(edges["minimum_actual_edge_gap_ms"] - 51.0) < 1e-6
    assert not any(
        finding["severity"] == STATUS_INFEASIBLE
        for finding in report["findings"])


def main():
    test_clean_bundle_passes_without_gpu_imports()
    test_noncontiguous_inferred_strum_is_ambiguous_without_provenance()
    test_actual_edge_gap_and_reversal_make_dense_transition_infeasible()
    test_reference_onset_delta_is_reported_and_classified()
    test_proposed_reviewed_override_is_valid_but_remains_ambiguous()
    test_all_bundle_summary_and_strict_cli_exit()
    test_current_promoted_song_is_physically_feasible_read_only()
    print("PASS: strike goal quality audit covers source, plan, and traversal risk")


if __name__ == "__main__":
    main()
