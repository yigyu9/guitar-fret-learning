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

from env.strike_goals import (  # noqa: E402
    STRIKE_TRAINING_SCHEMA,
    StrikeGoalSequence,
    validate_strike_training_data,
)
from tools.build_strike_training_data import (  # noqa: E402
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
    # time is authoritative; exact half-frame disagreement is accepted at both
    # sides of the nearest-frame boundary.
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
        assert goals.num_events == goals.n_events == 3
        assert goals.n_frames == 4 and goals.fps == 60
        assert goals.time.dtype == torch.float32
        assert goals.frame.dtype == torch.long
        assert goals.string.dtype == torch.long
        assert goals.event_time_s.data_ptr() == goals.time.data_ptr()
        assert goals.event_frame.data_ptr() == goals.frame.data_ptr()
        assert goals.event_string.data_ptr() == goals.string.data_ptr()
        assert torch.equal(goals.string, torch.tensor([0, 5, 2]))
        assert goals.event_ids == ("first", 9, 2)
        goals.require_physical_rearm_spacing(2)

        too_fast = document([
            {"time": 0.0, "frame": 0, "string": 2},
            {"time": 2.0 / 60.0, "frame": 2, "string": 2},
        ])
        fast_path = Path(directory) / "too_fast.strike_training.json"
        fast_path.write_text(json.dumps(too_fast), encoding="utf-8")
        fast_goals = StrikeGoalSequence(fast_path, device="cpu")
        assert fast_goals.validation_metadata[
            "minimum_same_string_restrike_frames"] == 2
        expect_error(
            "re-arm requires at least 3 frames",
            lambda: fast_goals.require_physical_rearm_spacing(2))

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
    expect_error("strictly increasing event time",
                 lambda: validate_strike_training_data(same_time))

    same_frame = document([
        {"time": 0.100, "frame": 6, "string": 0},
        {"time": 0.105, "frame": 6, "string": 1},
    ])
    expect_error("at most one strike per 60 Hz frame",
                 lambda: validate_strike_training_data(same_frame))

    # Builder performs the source 0=low-E -> Isaac 0=high-e reversal once.
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
    expect_error("strictly increasing t_on",
                 lambda: build_strike_training_data(polyphonic))

    subframe_double = {
        "notes": [
            {"t_on": 0.100, "string": 0},
            {"t_on": 0.105, "string": 1},
        ],
    }
    expect_error("at most one note onset per 60 Hz frame",
                 lambda: build_strike_training_data(subframe_double))

    # CLI writes the same validated contract and keeps source timing unchanged.
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
