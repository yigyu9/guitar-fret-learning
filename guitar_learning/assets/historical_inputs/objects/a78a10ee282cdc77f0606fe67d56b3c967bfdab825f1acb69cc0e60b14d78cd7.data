"""CPU checks for the minimal pick strike input and builder contracts."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_goals import (
    STRIKE_TRAINING_SCHEMA,
    StrikeGoalSequence,
    validate_strike_training_data,
)
from tools.build_strike_training_data import (
    build_strike_training_data,
    main as build_main,
)


def expect_error(fragment, callback):
    try:
        callback()
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {fragment!r}")


def document(events):
    return {
        "schema": STRIKE_TRAINING_SCHEMA,
        "metadata": {"fps": 60},
        "events": events,
    }


def main():
    fixture_root = PACKAGE_ROOT / "tests" / "fixtures" / "strike"
    strum_fixture = StrikeGoalSequence(
        fixture_root / "strum_6_string.json", device="cpu")
    assert strum_fixture.num_events == 1
    assert strum_fixture.validation_metadata["strum_events"] == 1
    assert strum_fixture.traversal_mask.all()
    mixed_fixture = StrikeGoalSequence(
        fixture_root / "mixed_phrase.json", device="cpu")
    assert mixed_fixture.validation_metadata["single_pick_events"] == 3
    assert mixed_fixture.validation_metadata["strum_events"] == 1
    dense_fixture = StrikeGoalSequence(
        fixture_root / "single_dense.json", device="cpu")
    expect_error(
        "alternate same-string restrike",
        dense_fixture.require_supported_gestures)


    valid = document([
        {"time": 0.5 / 60.0, "frame": 0, "string": 0, "event_id": "first"},
        {"time": 1.5 / 60.0, "frame": 2, "string": 5, "event_id": 9},
        {"time": 3.0 / 60.0, "frame": 3, "string": 2},
    ])
    summary = validate_strike_training_data(valid)
    assert summary["contract_valid"]
    assert summary["num_events"] == 3
    assert summary["n_frames"] == 4
    assert summary["used_strings"] == [0, 2, 5]
    assert abs(summary["max_time_frame_error_frames"] - 0.5) < 1e-9

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "valid.strike_training.json"
        path.write_text(json.dumps(valid), encoding="utf-8")
        goals = StrikeGoalSequence(path, device="cpu")
        assert goals.num_events == goals.n_events == 1
        assert goals.source_num_events == 3
        assert goals.n_frames == 4 and goals.fps == 60
        assert goals.time.dtype == torch.float32
        assert goals.frame.dtype == torch.long
        assert goals.string.dtype == torch.long
        assert goals.event_time_s.data_ptr() == goals.time.data_ptr()
        assert goals.event_frame.data_ptr() == goals.frame.data_ptr()
        assert goals.event_string.data_ptr() == goals.string.data_ptr()
        assert torch.equal(goals.string, torch.tensor([5]))
        assert torch.equal(
            goals.traversal_mask,
            torch.tensor([[True, True, True, True, True, True]]))
        assert goals.event_ids == (("first", 9, 2),)
        goals.require_physical_rearm_spacing(2)
        easy_diagnostics = goals.gap_diagnostics(0.0, 100.0)
        original_diagnostics = goals.gap_diagnostics(1.0, 100.0)
        assert easy_diagnostics["overlap_window_count"] == 0
        assert original_diagnostics["overlap_window_count"] == 0
        assert goals.validation_metadata["easy_timeline"] == easy_diagnostics

        too_fast = document([
            {"time": 0.0, "frame": 0, "string": 2},
            {"time": 2.0 / 60.0, "frame": 2, "string": 2},
        ])
        fast_path = Path(directory) / "too_fast.strike_training.json"
        fast_path.write_text(json.dumps(too_fast), encoding="utf-8")
        fast_goals = StrikeGoalSequence(fast_path, device="cpu")
        assert fast_goals.validation_metadata[
            "minimum_same_string_restrike_frames"] == 2
        assert fast_goals.validation_metadata[
            "minimum_event_gap_frames"] == 2
        expect_error(
            "re-arm requires at least 3 frames",
            lambda: fast_goals.require_physical_rearm_spacing(2))
        fast_goals.require_nonoverlapping_match_windows(10.0)
        fast_goals.require_nonoverlapping_match_windows(20.0)
        expect_error(
            "alternate same-string restrike",
            fast_goals.require_supported_gestures)
        fast_goals.require_motor_recovery_spacing(2)
        expect_error(
            "motor recovery requires at least 3 frames",
            lambda: fast_goals.require_motor_recovery_spacing(3))




        different_strings_too_fast = document([
            {"time": 0.0, "frame": 0, "string": 0},
            {"time": 2.0 / 60.0, "frame": 2, "string": 5},
        ])
        global_fast_path = (
            Path(directory) / "different_strings_too_fast.strike_training.json")
        global_fast_path.write_text(
            json.dumps(different_strings_too_fast), encoding="utf-8")
        global_fast_goals = StrikeGoalSequence(global_fast_path, device="cpu")
        assert global_fast_goals.validation_metadata[
            "minimum_same_string_restrike_s"] is None
        global_fast_goals.require_physical_rearm_spacing(2)
        assert global_fast_goals.num_events == 1
        assert global_fast_goals.validation_metadata["strum_events"] == 1
        global_fast_goals.require_supported_gestures()




        rounded_apart = document([
            {"time": 0.5 / 60.0, "frame": 0, "string": 1},
            {"time": 2.5 / 60.0, "frame": 3, "string": 1},
        ])
        rounded_path = Path(directory) / "rounded_apart.strike_training.json"
        rounded_path.write_text(json.dumps(rounded_apart), encoding="utf-8")
        rounded_goals = StrikeGoalSequence(rounded_path, device="cpu")
        assert rounded_goals.validation_metadata[
            "minimum_event_gap_frames"] == 3
        expect_error(
            "re-arm requires at least 3 frames",
            lambda: rounded_goals.require_physical_rearm_spacing(2))
        expect_error(
            "motor recovery requires at least 3 frames",
            lambda: rounded_goals.require_motor_recovery_spacing(3))

    outside = document([
        {"time": 0.500001 / 60.0, "frame": 0, "string": 0},
    ])
    expect_error("above the 0.5-frame limit",
                 lambda: validate_strike_training_data(outside))

    wrong_fps = deepcopy(valid)
    wrong_fps["metadata"]["fps"] = 120
    expect_error("expected 60 Hz",
                 lambda: validate_strike_training_data(wrong_fps))

    extra_field = deepcopy(valid)
    extra_field["events"][0]["fret"] = 3
    expect_error("exact fields",
                 lambda: validate_strike_training_data(extra_field))

    wrong_string = deepcopy(valid)
    wrong_string["events"][0]["string"] = 6
    expect_error("Isaac order 0..5",
                 lambda: validate_strike_training_data(wrong_string))

    duplicate_id = deepcopy(valid)
    duplicate_id["events"][1]["event_id"] = "first"
    expect_error("duplicate event_id",
                 lambda: validate_strike_training_data(duplicate_id))

    same_time = document([
        {"time": 0.1, "frame": 6, "string": 0},
        {"time": 0.1, "frame": 6, "string": 1},
    ])
    assert validate_strike_training_data(same_time)["contract_valid"]

    same_frame = document([
        {"time": 0.100, "frame": 6, "string": 0},
        {"time": 0.105, "frame": 6, "string": 1},
    ])
    assert validate_strike_training_data(same_frame)["contract_valid"]


    fingering = {
        "convention": "string 0 = low-E (CSV/model convention)",
        "notes": [
            {"t_on": 0.0, "string": 0, "fret": 0},
            {"t_on": 0.1, "string": 5, "fret": 7},
            {"t_on": 0.25, "string": 2, "fret": 4},
        ],
    }
    built = build_strike_training_data(fingering)
    assert [event["time"] for event in built["events"]] == [0.0, 0.1, 0.25]
    assert [event["frame"] for event in built["events"]] == [0, 6, 15]
    assert [event["string"] for event in built["events"]] == [5, 0, 3]
    assert all(set(event) == {"time", "frame", "string"}
               for event in built["events"])
    assert built["validation"]["contract_valid"]

    polyphonic = {
        "notes": [
            {"t_on": 0.1, "string": 0},
            {"t_on": 0.1, "string": 1},
        ],
    }
    polyphonic_built = build_strike_training_data(polyphonic)
    assert len(polyphonic_built["events"]) == 2
    assert polyphonic_built["validation"]["profile"] == (
        "pick_gesture_compiler_v3")

    subframe_double = {
        "notes": [
            {"t_on": 0.100, "string": 0},
            {"t_on": 0.105, "string": 1},
        ],
    }
    subframe_built = build_strike_training_data(subframe_double)
    assert [event["frame"] for event in subframe_built["events"]] == [6, 6]


    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "song.fingering.json"
        output = Path(directory) / "song.strike_training.json"
        source.write_text(json.dumps(fingering), encoding="utf-8")
        build_main([str(source), "--out", str(output)])
        cli_goals = StrikeGoalSequence(output, device="cpu")
        assert torch.allclose(
            cli_goals.time, torch.tensor([0.0, 0.1, 0.25]))
        assert torch.equal(cli_goals.frame, torch.tensor([0, 6, 15]))
        assert torch.equal(cli_goals.string, torch.tensor([5, 0, 3]))

    print("PASS: strike time authority, monophonic validation and string mapping")


if __name__ == "__main__":
    main()
