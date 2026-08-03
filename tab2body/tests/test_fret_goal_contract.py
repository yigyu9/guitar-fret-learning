"""CPU checks for the six-string, 22-fret S0 goal-loader contract."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.goals import (FretGoalSequence, build_finger_next_goal_vectors,
                       validate_fret_goal_frames,
                       validate_hand_position_target_frames)
from tools.build_fret_training_data import load_jams_notes, validate_builder_frames


def frame(index=0):
    return {
        "frame": index,
        "t": round(index / 60.0, 4),
        "fret_goal": [0] * 6,
        "finger_goal": [0] * 6,
        "barre_goal": [False] * 6,
        "hand_anchor_fret": 1.0,
        "hand_allowed_fret_range": [1, 6],
    }


def expect_error(frames, text, *, allow_barre=False):
    try:
        validate_fret_goal_frames(
            frames, fps=60, allow_barre=allow_barre, require_timeline=True)
    except ValueError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"invalid contract was accepted: expected {text!r}")


def hand_target(index=0):
    return {
        "frame": index,
        "t": round(index / 60.0, 4),
        "anchor_fret": 1.0,
        "allowed_fret_range": [1, 6],
        "wrist_pos_guitar": [0.075, 0.112, -0.023],
        "allowed_radius_m": 0.04,
    }


def expect_wrist_error(source, text):
    try:
        validate_hand_position_target_frames(
            source, required_start_t=0.0, required_end_t=1.0 / 60.0)
    except ValueError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(
            f"invalid wrist target was accepted: expected {text!r}")


def main():
    valid = [frame(0), frame(1)]
    valid[0]["fret_goal"][0] = 22
    valid[0]["finger_goal"][0] = 4
    stats = validate_fret_goal_frames(
        valid, fps=60, require_timeline=True)
    assert stats["max_fret"] == 22 and stats["multistring_finger_frames"] == 0

    invalid = copy.deepcopy(valid)
    invalid[0]["fret_goal"][0] = 23
    expect_error(invalid, "-1..22")
    invalid = copy.deepcopy(valid)
    invalid[0]["fret_goal"][0] = 4.0
    expect_error(invalid, "fret must be an integer")
    invalid = copy.deepcopy(valid)
    invalid[0]["finger_goal"][0] = 0
    expect_error(invalid, "requires finger 1..4")
    invalid = copy.deepcopy(valid)
    invalid[0]["finger_goal"][0] = 5
    expect_error(invalid, "outside 0..4")
    invalid = copy.deepcopy(valid)
    invalid[0]["barre_goal"] = [False] * 5
    expect_error(invalid, "exactly 6")
    invalid = copy.deepcopy(valid)
    invalid[1]["frame"] = 0
    expect_error(invalid, "contiguous")
    invalid = copy.deepcopy(valid)
    invalid[1]["t"] = invalid[0]["t"]
    expect_error(invalid, "strictly increasing")

    # Goal-derived hand-position fields enter every observation and therefore
    # must fail before tensor construction rather than silently create NaNs.
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_anchor_fret"] = float("nan")
    expect_error(invalid, "hand_anchor_fret must be a finite")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_anchor_fret"] = 23.0
    expect_error(invalid, "outside 1..22")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_allowed_fret_range"] = [1]
    expect_error(invalid, "exactly [low, high]")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_allowed_fret_range"] = [1, float("nan")]
    expect_error(invalid, "range must be finite")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_allowed_fret_range"] = [0, 6]
    expect_error(invalid, "ordered inside 1..22")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_allowed_fret_range"] = [6, 5]
    expect_error(invalid, "ordered inside 1..22")
    invalid = copy.deepcopy(valid)
    invalid[0]["hand_anchor_fret"] = 7.0
    invalid[0]["hand_allowed_fret_range"] = [1, 6]
    expect_error(invalid, "must lie inside")

    valid_wrist = [hand_target(0), hand_target(1)]
    wrist_stats = validate_hand_position_target_frames(
        valid_wrist, required_start_t=0.0, required_end_t=1.0 / 60.0)
    assert wrist_stats["contract_valid"] and wrist_stats["n_samples"] == 2
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["anchor_fret"] = float("nan")
    expect_wrist_error(invalid_wrist, "anchor_fret must be a finite")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["allowed_fret_range"] = [0, 6]
    expect_wrist_error(invalid_wrist, "ordered inside 1..22")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["wrist_pos_guitar"][1] = float("nan")
    expect_wrist_error(invalid_wrist, "wrist_pos_guitar must be finite")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["wrist_pos_guitar"] = [0.0, 0.0]
    expect_wrist_error(invalid_wrist, "must contain xyz")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["wrist_pos_guitar"][0] = 2.01
    expect_wrist_error(invalid_wrist, "gross +/-2.0m range")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["allowed_radius_m"] = float("nan")
    expect_wrist_error(invalid_wrist, "allowed_radius_m must be finite")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["allowed_radius_m"] = 0.0
    expect_wrist_error(invalid_wrist, "must be in (0, 1.0]")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[0]["allowed_radius_m"] = 1.01
    expect_wrist_error(invalid_wrist, "must be in (0, 1.0]")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[1]["t"] = invalid_wrist[0]["t"]
    expect_wrist_error(invalid_wrist, "timestamps must be strictly increasing")
    invalid_wrist = copy.deepcopy(valid_wrist)
    invalid_wrist[1]["frame"] = invalid_wrist[0]["frame"]
    expect_wrist_error(invalid_wrist, "frame indices must be strictly increasing")
    expect_wrist_error([valid_wrist[0]], "before required goal time")

    implicit = [frame()]
    implicit[0]["fret_goal"][:2] = [3, 3]
    implicit[0]["finger_goal"][:2] = [1, 1]
    expect_error(implicit, "allow_barre=False")
    try:
        validate_builder_frames(implicit)
    except ValueError as exc:
        assert "multiple active strings" in str(exc)
    else:
        raise AssertionError("builder accepted an implicit S0 barre")

    explicit = [frame()]
    explicit[0]["fret_goal"][:2] = [3, 3]
    explicit[0]["finger_goal"][:2] = [1, 1]
    explicit[0]["barre_goal"][:2] = [True, True]
    barre_stats = validate_fret_goal_frames(
        explicit, fps=60, allow_barre=True, require_timeline=True)
    assert barre_stats["multistring_finger_frames"] == 1
    vectors, metadata = build_finger_next_goal_vectors(
        explicit, fps=60, allow_barre=True)
    assert vectors.shape == (1, 4, 13)
    assert metadata["explicit_barre_finger_frames"] == 1

    inconsistent = copy.deepcopy(explicit)
    inconsistent[0]["barre_goal"][1] = False
    expect_error(inconsistent, "explicit barre", allow_barre=True)
    noncontiguous = copy.deepcopy(explicit)
    noncontiguous[0]["fret_goal"][1] = 0
    noncontiguous[0]["finger_goal"][1] = 0
    noncontiguous[0]["barre_goal"][1] = False
    noncontiguous[0]["fret_goal"][2] = 3
    noncontiguous[0]["finger_goal"][2] = 1
    noncontiguous[0]["barre_goal"][2] = True
    expect_error(noncontiguous, "contiguous", allow_barre=True)

    payload = {
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": valid,
    }
    with tempfile.TemporaryDirectory(prefix="fret_contract_", dir="/tmp") as tmp:
        goal_path = Path(tmp) / "valid.json"
        goal_path.write_text(json.dumps(payload))
        goals = FretGoalSequence(goal_path, num_envs=1, device="cpu")
        assert goals.validation_metadata["contract_valid"]
        assert not goals.barre_enabled

        hand_path = Path(tmp) / "valid.hand_position_targets.json"
        hand_payload = {
            "schema": "tab2body.hand_position_targets.v1",
            "coordinate_frame": "guitar local",
            "frames": valid_wrist,
        }
        hand_path.write_text(json.dumps(hand_payload))
        goals_with_wrist = FretGoalSequence(
            goal_path, num_envs=1, device="cpu",
            hand_targets_path=hand_path)
        assert goals_with_wrist.has_wrist_target
        assert goals_with_wrist.wrist.shape == (2, 3)
        assert goals_with_wrist.wrist_validation_metadata["contract_valid"]

        # Integration check: the loader must invoke the validator before
        # np.interp can accept a malformed source timeline.
        bad_hand_payload = copy.deepcopy(hand_payload)
        bad_hand_payload["frames"][1]["t"] = bad_hand_payload["frames"][0]["t"]
        bad_hand_path = Path(tmp) / "bad.hand_position_targets.json"
        bad_hand_path.write_text(json.dumps(bad_hand_payload))
        try:
            FretGoalSequence(
                goal_path, num_envs=1, device="cpu",
                hand_targets_path=bad_hand_path)
        except ValueError as exc:
            assert "strictly increasing" in str(exc)
        else:
            raise AssertionError("loader accepted a non-monotonic wrist target timeline")

        jams_path = Path(tmp) / "too_high.jams"
        jams_path.write_text(json.dumps({
            "annotations": [{
                "namespace": "note_midi",
                "annotation_metadata": {"data_source": "0"},
                "data": [{"value": 63, "time": 0.0, "duration": 1.0}],
            }],
        }))
        try:
            load_jams_notes(jams_path)
        except ValueError as exc:
            assert "range 0..22" in str(exc)
        else:
            raise AssertionError("builder accepted fret 23")

    print("PASS: loader and builder enforce the six-string 22-fret S0 contract")


if __name__ == "__main__":
    main()
