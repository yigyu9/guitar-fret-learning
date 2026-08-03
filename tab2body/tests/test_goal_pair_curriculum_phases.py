"""CPU checks for performance-gated goal-pair phases."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.curriculum import (
    FingertipApproachCurriculum,
    FingertipApproachCurriculumConfig,
)


def _config():
    return FingertipApproachCurriculumConfig(
        goal_pair_min_iterations=1,
        goal_pair_max_iterations=20,
        goal_pair_retention_min_iterations=2,
        goal_pair_mixed_min_iterations=2,
        goal_pair_full_min_iterations=1,
        goal_pair_phase_min_evidence=10,
        promotion_windows=2,
        bridge_window_episodes=1,
        bridge_promotion_windows=2,
    )


def _stats(rehearsal_pass=True, mixed_pass=True,
           promotion_pass=True):
    stats = {
        "episodes": 1.0,
        "f1_l": 0.96,
        "no_press_correct_count": 99.5,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.005,
        "sustain_hold_rate": 0.96,
        "sustain_event_success_rate": 0.95,
        "sustain_event_count": 2.0,
        "press_dropout_rate": 0.02,
        "failure_termination": 0.0,
        "nonfinite": 0.0,
        "velocity_blowup": 0.0,
        "curriculum_goal_pair_pretransition_current_press_preserved": (
            0.95 if mixed_pass else 0.50),
        "curriculum_goal_pair_pretransition_current_press_preserved_count":
            40.0,
        "curriculum_goal_pair_pretransition_current_press_quality": (
            0.95 if mixed_pass else 0.10),
        "curriculum_goal_pair_pretransition_current_press_quality_count":
            40.0,
        "curriculum_goal_pair_sequence_active_count": 2048.0,
        "curriculum_goal_pair_sequence_press_success": 0.90,
        "curriculum_goal_pair_sequence_no_press_success": 0.95,
        "curriculum_goal_pair_sequence_wrong_press": 0.01,
        "curriculum_goal_pair_sequence_penetration": 0.0,
        "curriculum_goal_pair_sequence_thumb_support": 0.80,
    }
    for finger in range(1, 5):
        stats[f"press_finger_{finger}_success"] = 9.5
        stats[f"press_finger_{finger}_count"] = 10.0
        rehearsal_success = (
            0.90 if rehearsal_pass or finger != 4 else 0.0)
        rehearsal_distance = (
            0.006 if rehearsal_pass or finger != 4 else 0.040)
        rehearsal = (
            f"curriculum_goal_pair_rehearsal_finger_{finger}")
        stats[f"{rehearsal}_target_active_count"] = 20.0
        stats[f"{rehearsal}_target_active"] = 0.25
        stats[f"{rehearsal}_press_success"] = rehearsal_success
        stats[f"{rehearsal}_target_distance"] = rehearsal_distance

        transition = (
            f"curriculum_goal_pair_transition_finger_{finger}")
        transition_success = (
            0.90 if promotion_pass else (0.0 if finger == 4 else 0.90))
        stats[f"{transition}_target_active_count"] = 20.0
        stats[f"{transition}_target_active"] = 0.25
        stats[f"{transition}_press_success"] = transition_success
        stats[f"{transition}_next_active_count"] = 20.0
        stats[f"{transition}_next_distance"] = (
            0.015 if mixed_pass else 0.050)
        stats[f"{transition}_next_progress"] = (
            0.001 if mixed_pass else -0.001)
    return stats


def main():
    config = _config()
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.goal_pair_incoming_fingers = (1, 2, 3, 4)

    state = curriculum.state()
    assert state["curriculum_schema_version"] == 11
    assert state["curriculum_goal_pair_phase"] == "retention"
    assert state["curriculum_goal_pair_rehearsal_probability"] == 1.0

    for _ in range(5):
        state = curriculum.after_iteration(_stats(rehearsal_pass=False))
    assert state["curriculum_goal_pair_phase"] == "retention"
    assert state["curriculum_goal_pair_focus_finger"] == 4

    state = curriculum.after_iteration({})
    assert state["curriculum_goal_pair_focus_finger"] == 4

    sparse_current = _stats(rehearsal_pass=False)
    sparse_current[
        "curriculum_goal_pair_rehearsal_finger_4_target_active_count"] = 9.0
    state = curriculum.after_iteration(sparse_current)
    assert state["curriculum_goal_pair_focus_finger"] == 4

    for _ in range(4):
        state = curriculum.after_iteration(_stats())
    assert state["curriculum_goal_pair_phase"] == "mixed"
    assert state["curriculum_goal_pair_phase_iteration"] == 0
    assert state["curriculum_goal_pair_mixed_level"] == 0
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.90
    assert state["curriculum_goal_pair_preview_only"]

    for _ in range(5):
        state = curriculum.after_iteration(_stats(mixed_pass=False))
    assert state["curriculum_goal_pair_phase"] == "mixed"
    for _ in range(3):
        state = curriculum.after_iteration(_stats())
    assert state["curriculum_goal_pair_phase"] == "mixed"
    assert state["curriculum_goal_pair_mixed_level"] == 1
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.80
    assert not state["curriculum_goal_pair_preview_only"]
    for expected_level, expected_rehearsal in ((2, 0.65),):
        curriculum.after_iteration(_stats())
        state = curriculum.after_iteration(_stats())
        assert state["curriculum_goal_pair_phase"] == "mixed"
        assert state["curriculum_goal_pair_mixed_level"] == expected_level
        assert (
            state["curriculum_goal_pair_rehearsal_probability"]
            == expected_rehearsal)
    curriculum.after_iteration(_stats())
    state = curriculum.after_iteration(_stats())
    assert state["curriculum_goal_pair_phase"] == "full"
    assert state["curriculum_goal_pair_rehearsal_probability"] == 1.0 / 3.0
    assert state["curriculum_goal_pair_focus_finger"] == 0
    assert not state["curriculum_goal_pair_preview_only"]

    preview_config = replace(
        config,
        goal_pair_mixed_min_iterations=1,
        goal_pair_phase_min_evidence=10,
        promotion_windows=1)
    preview = FingertipApproachCurriculum(
        preview_config, forced_stage="goal_pair")
    preview.goal_pair_phase = "mixed"
    preview.required_song_fingers = (1, 2, 3, 4)
    preview.goal_pair_incoming_fingers = (1, 2, 3, 4)
    preview_stats = _stats()
    for finger in range(1, 5):
        prefix = (
            f"curriculum_goal_pair_transition_finger_{finger}")
        preview_stats[f"{prefix}_target_active_count"] = 0.0
        preview_stats[f"{prefix}_target_active"] = 0.0
        preview_stats[f"{prefix}_press_success"] = 0.0
    state = preview.after_iteration(preview_stats)
    assert state["curriculum_goal_pair_mixed_level"] == 1
    assert not state["curriculum_goal_pair_preview_only"]
    state = preview.after_iteration(preview_stats)
    assert state["curriculum_goal_pair_mixed_level"] == 1

    source = FingertipApproachCurriculum(config)
    source.stage = "goal_pair"
    source.goal_pair_phase = "mixed"
    source.goal_pair_phase_iteration = 17
    source.goal_pair_mixed_level = 2
    source.goal_pair_mixed_level_iteration = 7
    source.goal_pair_focus_finger = 4
    source.recent.extend((1.0, 0.0))
    restored = FingertipApproachCurriculum(config)
    restored.load_context(source.state())
    assert restored.stage == "goal_pair"
    assert restored.goal_pair_phase == "mixed"
    assert restored.goal_pair_phase_iteration == 17
    assert restored.goal_pair_mixed_level == 2
    assert restored.goal_pair_mixed_level_iteration == 7
    assert restored.goal_pair_focus_finger == 4
    assert tuple(restored.recent) == (1.0, 0.0)

    migrated = FingertipApproachCurriculum(config)
    migrated.load_context({
        "curriculum_schema_version": 6,
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 900,
        "curriculum_total_iteration": 1500,
        "curriculum_stalled": True,
        "curriculum_recent": [1.0, 1.0],
    })
    assert migrated.stage == "goal_pair"
    assert migrated.stage_iteration == 0
    assert migrated.goal_pair_phase == "retention"
    assert migrated.goal_pair_phase_iteration == 0
    assert migrated.goal_pair_focus_finger == 0
    assert not migrated.recent

    migrated_v9 = FingertipApproachCurriculum(config)
    migrated_v9.load_context({
        "curriculum_schema_version": 9,
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 900,
        "curriculum_total_iteration": 1500,
        "curriculum_goal_pair_phase": "full",
        "curriculum_goal_pair_phase_iteration": 400,
        "curriculum_goal_pair_focus_finger": 4,
        "curriculum_recent": [1.0, 1.0],
    })
    assert migrated_v9.stage == "goal_pair"
    assert migrated_v9.stage_iteration == 0
    assert migrated_v9.goal_pair_phase == "retention"
    assert migrated_v9.goal_pair_phase_iteration == 0
    assert migrated_v9.goal_pair_focus_finger == 0
    assert not migrated_v9.recent

    migrated_v10 = FingertipApproachCurriculum(config)
    migrated_v10.load_context({
        "curriculum_schema_version": 10,
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 300,
        "curriculum_goal_pair_phase": "mixed",
        "curriculum_goal_pair_mixed_level": 2,
    })
    assert migrated_v10.stage == "goal_pair"
    assert migrated_v10.stage_iteration == 0
    assert migrated_v10.goal_pair_phase == "retention"

    accumulated_config = replace(
        config,
        goal_pair_phase_min_evidence=100,
        goal_pair_retention_min_iterations=1)
    accumulated = FingertipApproachCurriculum(
        accumulated_config, forced_stage="goal_pair")
    accumulated.required_song_fingers = (1, 2, 3, 4)
    accumulated.goal_pair_incoming_fingers = (1, 2, 3, 4)
    for _ in range(4):
        state = accumulated.after_iteration(
            _stats(rehearsal_pass=False))
        assert state["curriculum_goal_pair_focus_finger"] == 0
    state = accumulated.after_iteration(
        _stats(rehearsal_pass=False))
    assert state["curriculum_goal_pair_focus_finger"] == 4
    assert all(
        value == 0.0
        for value in accumulated.goal_pair_phase_evidence.values())

    hard_config = replace(
        config,
        goal_pair_max_iterations=1,
        goal_pair_full_min_iterations=1,
        bridge_hard_timeout_min_per_finger_rate=0.20)
    hard = FingertipApproachCurriculum(hard_config)
    hard.stage = "goal_pair"
    hard.goal_pair_phase = "full"
    hard.goal_pair_phase_iteration = 1
    hard.required_song_fingers = (1, 2, 3, 4)
    hard.goal_pair_incoming_fingers = (1, 2, 3, 4)
    hard_failure = _stats(promotion_pass=False)
    hard_failure.update({
        "f1_l": 0.20,
        "no_press_correct_count": 80.0,
        "wrong_press_rate": 0.20,
        "sustain_hold_rate": 0.30,
        "sustain_event_success_rate": 0.20,
        "press_dropout_rate": 0.20,
        "failure_termination": 0.20,
    })
    state = hard.after_iteration(hard_failure)
    assert hard.stage == "goal_pair"
    assert state["curriculum_stalled"]
    hard._reset_goal_pair_phase_evidence()
    hard_ready = dict(hard_failure)
    hard_ready.update(_stats())
    hard_ready.update({
        "f1_l": 0.20,
        "no_press_correct_count": 80.0,
        "wrong_press_rate": 0.20,
        "sustain_hold_rate": 0.30,
        "sustain_event_success_rate": 0.20,
        "press_dropout_rate": 0.20,
        "failure_termination": 0.20,
    })
    state = hard.after_iteration(hard_ready)
    assert hard.stage == "transition_window"
    assert state["curriculum_forced_advance"]
    assert state["curriculum_last_forced_advance_from"] == (
        "goal_pair:hard_timeout")

    for invalid in (
            {"goal_pair_retention_rehearsal_probability": 0.4},
            {"goal_pair_phase_min_evidence": 0},
            {"goal_pair_retention_min_iterations": 0},
            {"goal_pair_pretransition_preservation_rate": 1.1},
            {"goal_pair_mixed_transition_fractions": (0.20, 0.10, 0.35)},
            {"goal_pair_mixed_distances": (0.050, 0.060, 0.025)},
            {"goal_pair_preview_levels": 3},
            {"goal_pair_preview_levels": True},
            {"goal_pair_focus_lateral_exploration_std": 0.0}):
        try:
            replace(config, **invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid goal-pair config accepted: {invalid}")

    print("PASS: preview-first goal-pair curriculum and schema-11 migration")


if __name__ == "__main__":
    main()
