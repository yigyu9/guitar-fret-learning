"""CPU regression checks for the read-only Fret goal-pair diagnosis."""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.tools.diagnose_fret_goal_pair import (
    diagnose, load_run_config, current_regime,
)


def _row(iteration, *, rollback=1, pinky_full=0.40, preservation=0.70):
    row = {
        "iteration": iteration, "reward": 0.7, "f1_l": 0.93,
        "press_success_rate": 0.91, "chord_ready_rate": 0.65,
        "sustain_event_success_rate_pooled": 0.86,
        "wrong_press_rate": 0.006, "press_dropout_rate": 0.02,
        "value_loss": 7.0, "kl": 0.015, "ppo_early_stop": False,
        "next_curriculum_stage": "goal_pair",
        "next_curriculum_goal_pair_phase": "mixed",
        "next_curriculum_goal_pair_mixed_level": 0,
        "next_curriculum_goal_pair_recovery": False,
        "next_curriculum_goal_pair_recovery_rollback_count": rollback,
        "next_curriculum_goal_pair_focus_finger": 4,
        "next_curriculum_goal_pair_mastered_count": 3,
        "curriculum_goal_pair_pretransition_active_count": 600,
        "curriculum_goal_pair_pretransition_current_press_quality": preservation,
        "curriculum_goal_pair_pretransition_current_press_preserved": 0.75,
    }
    for finger in range(1, 5):
        rehearsal = f"curriculum_goal_pair_rehearsal_finger_{finger}_"
        transition = f"curriculum_goal_pair_transition_finger_{finger}_"
        full = f"curriculum_goal_pair_full_song_finger_{finger}_"
        row.update({
            rehearsal + "target_active_count": 600,
            rehearsal + "press_success": 0.95,
            rehearsal + "target_distance": 0.003,
            rehearsal + "hold_quality": 0.90,
            rehearsal + "hold_acquired_frame_rate": 0.95,
            rehearsal + "full_hold_frame_rate": 0.85,
            rehearsal + "dropout_rate": 0.01,
            rehearsal + "wrong_press": 0.0,
            transition + "target_active_count": 600,
            transition + "press_success": 0.85,
            transition + "target_distance": 0.004,
            transition + "hold_quality": 0.85,
            transition + "hold_acquired_frame_rate": 0.90,
            transition + "full_hold_frame_rate": 0.75,
            transition + "dropout_rate": 0.02,
            transition + "wrong_press": 0.01,
            transition + "next_active_count": 600,
            transition + "next_distance": 0.02,
            transition + "next_progress": 0.0,
            full + "target_active_count": 100,
            full + "press_success": (
                pinky_full if finger == 4 else 0.90),
            full + "target_distance": 0.003,
            full + "hold_quality": 0.85,
            full + "hold_acquired_frame_rate": 0.90,
            full + "full_hold_frame_rate": 0.75,
            full + "dropout_rate": 0.02,
            full + "wrong_press": 0.01,
        })
    row.update({
        "curriculum_chord_shape_9_target_active_count": 40,
        "curriculum_chord_shape_9_success": 0.0,
        "curriculum_chord_shape_9_distance": 0.024,
        "curriculum_chord_shape_9_alignment": 0.4,
    })
    return row


def _checks():
    rows = [_row(1, rollback=0), _row(2), _row(3)]
    got = diagnose(rows, window=100)
    assert got["iteration_range"] == [2, 3]
    assert got["window_rows"] == 2
    assert got["regime"]["preview_only"] is True
    assert got["fingers"]["4"]["full_song"]["success"] == 0.40
    assert got["fingers"]["4"]["rehearsal"][
        "hold_acquired_frame_rate"] == 0.95
    assert got["fingers"]["4"]["rehearsal"][
        "full_hold_frame_rate"] == 0.85
    assert got["fingers"]["4"]["full_song"]["count"] == 200
    assert "global.pretransition_preservation" in got[
        "final_promotion_failures"]
    assert "pinky.full_song_success" in got["final_promotion_failures"]
    assert "pinky.transition_success" not in got["current_level_failures"]
    assert got["weak_chord_signatures"] == [9]
    assert got["recommendations"][0]["finger"] == "pinky"

    before, after = _row(4), _row(5)
    before["curriculum_goal_pair_mixed_level"] = 0
    before["next_curriculum_goal_pair_mixed_level"] = 1
    after["curriculum_goal_pair_mixed_level"] = 1
    selected, _, _ = current_regime([before, after])
    assert len(selected) == 1, "transition row belongs to its rollout regime"

    row = _row(6)
    prefix = "curriculum_goal_pair_sequence_finger_4_"
    full = "curriculum_goal_pair_full_song_finger_4_"
    row.update({prefix + "target_active_count": 1000,
                prefix + "press_success": 0.6,
                full + "target_active_count": 600,
                full + "press_success": 0.8})
    got = diagnose([row])
    short = got["fingers"]["4"]["short_sequence"]
    assert abs(short["success"] - 0.3) < 1e-8
    assert short["count"] == 400
    row[full + "target_active_count"] = 1200
    short = diagnose([row])["fingers"]["4"]["short_sequence"]
    assert short["success"] is None and short["invalid_rows"] == 1

    row = _row(7)
    row["curriculum_goal_pair_phase"] = "full"
    report = diagnose([row])["gate_report"]
    assert report["checks"]["stage_age"]["passed"] is None
    assert report["checks"]["regression_clear"]["passed"] is None
    row["curriculum_stage_iteration"] = 5000
    row["curriculum_regression_hold"] = True
    report = diagnose([row])["gate_report"]
    assert report["checks"]["stage_age"]["value"] == 5000
    assert report["checks"]["regression_clear"]["passed"] is False

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "run_manifest.json").write_text(json.dumps({
            "curriculum_config": {
                "goal_pair_mixed_sequence_max_events": [8, 12, 16],
                "goal_pair_full_sequence_max_events": 16,
                "goal_pair_sequence_press_rate": 0.83}}))
        config, provenance = load_run_config(root / "logs" / "metrics.jsonl")
        assert config.goal_pair_sequence_press_rate == 0.83
        assert config.goal_pair_mixed_sequence_max_events == (8, 12, 16)
        assert provenance["source"].endswith("run_manifest.json")


if __name__ == "__main__":
    _checks()
    print("fret goal-pair diagnosis tests: PASS")
