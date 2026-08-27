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
        goal_pair_focus_min_iterations=1,
        goal_pair_retention_focus_probability=0.30,
        goal_pair_mixed_focus_probability=0.30,
        goal_pair_timeout_focus_probability=0.40,
        goal_pair_recovery_min_iterations=2,
        goal_pair_recovery_windows=2,
        goal_pair_full_song_focus_min_evidence=10,
        goal_pair_phase_baseline_warmup_iterations=1,
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
        stats[f"{rehearsal}_wrong_press"] = 0.01

        full_song = (
            f"curriculum_goal_pair_full_song_finger_{finger}")
        stats[f"{full_song}_target_active_count"] = 20.0
        stats[f"{full_song}_press_success"] = 0.90
        stats[f"{full_song}_target_distance"] = 0.006
        stats[f"{full_song}_hold_quality"] = 0.90
        stats[f"{full_song}_dropout_rate"] = 0.02
        stats[f"{full_song}_wrong_press"] = 0.01

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
        incoming = f"curriculum_goal_pair_incoming_finger_{finger}"
        stats[f"{incoming}_active_count"] = 20.0
        stats[f"{incoming}_wrong_press"] = 0.01
    return stats


def main():
    config = _config()
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.goal_pair_incoming_fingers = (1, 2, 3, 4)

    state = curriculum.state()
    assert state["curriculum_schema_version"] == 44
    assert state["curriculum_goal_pair_phase"] == "retention"
    assert state["curriculum_goal_pair_rehearsal_probability"] == 1.0

    joint_config = FingertipApproachCurriculumConfig()
    assert joint_config.goal_pair_retention_focus_probability == 0.0
    assert joint_config.goal_pair_mixed_focus_probability == 0.25
    assert joint_config.goal_pair_timeout_focus_probability == 0.35
    assert joint_config.goal_pair_recovery_rehearsal_probability == 0.50
    assert joint_config.goal_pair_recovery_sequence_probability == 0.50
    assert joint_config.goal_pair_recovery_sequence_max_events == 16
    assert joint_config.goal_pair_recovery_full_song_fraction == 0.20
    assert joint_config.goal_pair_recovery_uncovered_pose_probability == 0.35
    joint = FingertipApproachCurriculum(
        replace(
            config,
            goal_pair_retention_focus_probability=0.0,
            goal_pair_mixed_focus_probability=0.0,
            goal_pair_timeout_focus_probability=0.0),
        forced_stage="goal_pair")
    joint.required_song_fingers = (1, 2, 3, 4)
    joint.goal_pair_incoming_fingers = (1, 2, 3, 4)
    joint.after_iteration(_stats(rehearsal_pass=False))
    assert joint.goal_pair_focus_finger == 0

    recovered = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    recovered.required_song_fingers = (1, 2, 3, 4)
    recovered.goal_pair_recovery_active = True
    recovered.goal_pair_recovery_iteration = (
        config.goal_pair_recovery_min_iterations)
    recovered.goal_pair_recovery_good_windows = (
        config.goal_pair_recovery_windows)
    recovery_state = recovered.state()
    assert recovery_state[
        "curriculum_goal_pair_sequence_probability"] == 0.50
    assert recovery_state[
        "curriculum_goal_pair_sequence_max_events"] == 16
    assert recovery_state[
        "curriculum_goal_pair_sequence_full_song_fraction"] == 0.20
    assert recovery_state[
        "curriculum_goal_pair_uncovered_pose_probability"] == 0.35
    assert not any(recovered.goal_pair_mastered_fingers)
    assert recovered._sync_goal_pair_recovery(_stats())
    assert not recovered.goal_pair_recovery_active

    song_blocked = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    song_blocked.required_song_fingers = (1, 2, 3, 4)
    song_blocked.goal_pair_recovery_active = True
    song_blocked.goal_pair_recovery_iteration = (
        config.goal_pair_recovery_min_iterations)
    song_blocked.goal_pair_recovery_good_windows = (
        config.goal_pair_recovery_windows)
    weak_song = _stats()
    weak_song[
        "curriculum_goal_pair_full_song_finger_4_press_success"] = 0.0
    assert not song_blocked._sync_goal_pair_recovery(weak_song)
    assert song_blocked.goal_pair_recovery_active

    transfer_gate = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    transfer_gate.goal_pair_phase = "mixed"
    transfer_gate.goal_pair_mixed_level = 1
    weak_transfer = _stats()
    weak_transfer[
        "curriculum_goal_pair_full_song_finger_2_press_success"] = 0.0
    passed, _ = transfer_gate._goal_pair_focus_unresolved(
        weak_transfer, 2)
    assert not passed
    wrong_transition = _stats()
    wrong_transition[
        "curriculum_goal_pair_incoming_finger_2_wrong_press"] = 0.20
    passed, _ = transfer_gate._goal_pair_focus_unresolved(
        wrong_transition, 2)
    assert not passed

    rotating = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    rotating.required_song_fingers = (1, 2, 3, 4)
    rotating.goal_pair_incoming_fingers = (1, 2, 3, 4)
    rotating.goal_pair_recovery_active = True
    rotating.goal_pair_focus_finger = 2
    rotating.goal_pair_focus_iteration = config.goal_pair_focus_min_iterations
    tied_song = _stats()
    tied_song[
        "curriculum_goal_pair_full_song_finger_2_press_success"] = 0.0
    tied_song[
        "curriculum_goal_pair_full_song_finger_4_press_success"] = 0.0
    assert rotating._update_goal_pair_focus(tied_song, {})
    assert rotating.goal_pair_focus_finger == 4

    song_focus = FingertipApproachCurriculum(
        config, forced_stage="goal_pair")
    song_focus.required_song_fingers = (1, 2, 3, 4)
    song_focus.goal_pair_incoming_fingers = (1, 2, 3, 4)
    song_focus.goal_pair_recovery_active = True
    song_focus.goal_pair_mastered_fingers = [True] * 4
    song_focus.goal_pair_focus_finger = 2
    song_focus.goal_pair_focus_iteration = 0
    weak_song_focus = _stats()
    weak_song_focus[
        "curriculum_goal_pair_full_song_finger_2_press_success"] = 0.0
    weak_song_focus[
        "curriculum_goal_pair_full_song_finger_4_press_success"] = 0.0
    assert not song_focus._update_goal_pair_focus(weak_song_focus, {})
    assert song_focus.goal_pair_focus_finger == 2
    song_focus.goal_pair_focus_iteration = (
        config.goal_pair_focus_min_iterations)
    assert song_focus._update_goal_pair_focus(weak_song_focus, {})
    assert song_focus.goal_pair_focus_finger == 4

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
    assert state["curriculum_goal_pair_phase_iteration"] == 1
    assert state["curriculum_goal_pair_mixed_level"] == 0
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.90
    assert state["curriculum_goal_pair_preview_only"]

    for _ in range(5):
        state = curriculum.after_iteration(_stats(mixed_pass=False))
    assert state["curriculum_goal_pair_phase"] == "mixed"
    state = curriculum.after_iteration(_stats())
    assert state["curriculum_goal_pair_phase"] == "mixed"
    assert state["curriculum_goal_pair_mixed_level"] == 1
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.80
    assert not state["curriculum_goal_pair_preview_only"]
    curriculum.after_iteration(_stats())
    state = curriculum.after_iteration(_stats())
    assert state["curriculum_goal_pair_phase"] == "mixed"
    assert state["curriculum_goal_pair_mixed_level"] == 2
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.65
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
    source.goal_pair_focus_iteration = 51
    source.goal_pair_focus_scores = [
        (0.8, -0.01, 1.0), (0.7, -0.02, 2.0),
        (0.6, -0.03, 3.0), (0.5, -0.04, 4.0)]
    source.goal_pair_mastered_fingers = [True, False, True, False]
    source.goal_pair_mastery_streaks = [2, 1, 2, 0]
    source.goal_pair_mastery_fail_streaks = [0, 1, 0, 1]
    source.goal_pair_phase_timeout_count = 3
    source.goal_pair_recovery_active = True
    source.goal_pair_recovery_iteration = 25
    source.goal_pair_recovery_good_windows = 1
    source.goal_pair_recovery_count = 2
    source.goal_pair_recovery_reason = "performance_regression"
    source.goal_pair_phase_baseline = {
        "episodes": 4096.0,
        "f1": 0.90,
        "finger_min": 0.82,
        "no_press": 0.95,
        "wrong": 0.03,
        "sustain": 0.86,
        "event_success": 0.60,
        "event_count": 1.2,
        "dropout": 0.12,
        "failure": 0.01,
    }
    source.goal_pair_phase_baseline_label = "mixed:2"
    source.goal_pair_recovery_failures = ("sustain",)
    source.goal_pair_recovery_rollback_count = 1
    source.goal_pair_last_recovery_rollback = (
        "mixed:1->mixed:0:quality_timeout")
    source.recent.extend((1.0, 0.0))
    restored = FingertipApproachCurriculum(config)
    restored.load_context(source.state())
    assert restored.stage == "goal_pair"
    assert restored.goal_pair_phase == "mixed"
    assert restored.goal_pair_phase_iteration == 17
    assert restored.goal_pair_mixed_level == 2
    assert restored.goal_pair_mixed_level_iteration == 7
    assert restored.goal_pair_focus_finger == 4
    assert restored.goal_pair_focus_iteration == 51
    assert restored.goal_pair_focus_scores == source.goal_pair_focus_scores
    assert restored.goal_pair_mastered_fingers == [True, False, True, False]
    assert restored.goal_pair_mastery_streaks == [2, 1, 2, 0]
    assert restored.goal_pair_mastery_fail_streaks == [0, 1, 0, 1]
    assert restored.goal_pair_phase_timeout_count == 3
    assert restored.goal_pair_recovery_active
    assert restored.goal_pair_recovery_iteration == 25
    assert restored.goal_pair_recovery_good_windows == 1
    assert restored.goal_pair_recovery_count == 2
    assert restored.goal_pair_recovery_reason == "performance_regression"
    assert restored.goal_pair_phase_baseline == (
        source.goal_pair_phase_baseline)
    assert restored.goal_pair_phase_baseline_label == "mixed:2"
    assert restored.goal_pair_recovery_failures == ("sustain",)
    assert restored.goal_pair_recovery_rollback_count == 1
    assert restored.goal_pair_last_recovery_rollback == (
        "mixed:1->mixed:0:quality_timeout")
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

    migrated_v12 = FingertipApproachCurriculum(config)
    migrated_v12.load_context({
        "curriculum_schema_version": 12,
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 300,
        "curriculum_goal_pair_phase": "retention",
        "curriculum_goal_pair_phase_iteration": 50,
        "curriculum_goal_pair_mastered_fingers": [True, False, True, True],
        "curriculum_goal_pair_mastery_streaks": [2, 0, 2, 2],
    })
    assert migrated_v12.stage == "goal_pair"
    assert migrated_v12.goal_pair_mastered_fingers == [
        True, False, True, True]
    assert migrated_v12.goal_pair_mastery_fail_streaks == [0, 0, 0, 0]

    migrated_v14_state = source.state()
    migrated_v14_state["curriculum_schema_version"] = 14
    for key in (
            "curriculum_goal_pair_phase_baseline",
            "curriculum_goal_pair_phase_baseline_label",
            "curriculum_goal_pair_recovery_failures",
            "curriculum_goal_pair_recovery_rollback_count",
            "curriculum_goal_pair_last_recovery_rollback"):
        migrated_v14_state.pop(key, None)
    migrated_v14_state["curriculum_bridge_last_metrics"] = dict(
        source.goal_pair_phase_baseline)
    migrated_v14 = FingertipApproachCurriculum(config)
    migrated_v14.load_context(migrated_v14_state)
    assert migrated_v14.goal_pair_phase_baseline == (
        source.goal_pair_phase_baseline)
    assert migrated_v14.goal_pair_phase_baseline_label == "mixed:2"
    assert migrated_v14.goal_pair_recovery_iteration == 0
    assert migrated_v14.goal_pair_recovery_good_windows == 0
    assert migrated_v14.goal_pair_focus_finger == 0

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
    assert accumulated.goal_pair_mastery_streaks == [1, 1, 1, 0]
    assert all(
        value == 0.0
        for key, value in accumulated.goal_pair_phase_evidence.items()
        if not key.startswith(("preservation_", "full_song_")))
    assert (
        accumulated.goal_pair_phase_evidence["preservation_count"] > 0.0)

    hold_config = replace(
        config,
        goal_pair_retention_min_iterations=20,
        goal_pair_phase_max_iterations=40)
    hold_mastery = FingertipApproachCurriculum(
        hold_config, forced_stage="goal_pair")
    hold_mastery.required_song_fingers = (1, 2, 3, 4)
    hold_mastery.goal_pair_incoming_fingers = (1, 2, 3, 4)
    unstable_hold = _stats()
    unstable_hold["sustain_hold_rate"] = 0.60
    unstable_hold["press_dropout_rate"] = 0.30
    hold_mastery.after_iteration(unstable_hold)
    hold_mastery.after_iteration(unstable_hold)
    assert not any(hold_mastery.goal_pair_mastered_fingers)
    hold_mastery.after_iteration(_stats())
    hold_mastery.after_iteration(_stats())
    assert all(hold_mastery.goal_pair_mastered_fingers)

    rollback_config = replace(
        config,
        goal_pair_recovery_min_iterations=1,
        goal_pair_recovery_max_iterations=2,
        goal_pair_phase_max_iterations=20)
    rollback = FingertipApproachCurriculum(
        rollback_config, forced_stage="goal_pair")
    rollback.required_song_fingers = (1, 2, 3, 4)
    rollback.goal_pair_incoming_fingers = (1, 2, 3, 4)
    rollback.goal_pair_phase = "mixed"
    rollback.goal_pair_recovery_active = True
    rollback.goal_pair_recovery_reason = "performance_regression"
    rollback.goal_pair_phase_baseline = {
        "f1": 0.95,
        "no_press": 0.995,
        "wrong": 0.005,
        "event_success": 0.95,
        "finger_min": 0.95,
        "failure": 0.0,
    }
    rollback.goal_pair_phase_baseline_label = "mixed:0"
    rollback.regression_hold = True
    rollback_stats = _stats(rehearsal_pass=False)
    rollback_stats["f1_l"] = 0.50
    rollback.after_iteration(rollback_stats)
    rollback_state = rollback.after_iteration(rollback_stats)
    assert rollback.goal_pair_phase == "retention"
    assert not rollback.goal_pair_recovery_active
    assert rollback_state["curriculum_goal_pair_recovery_rollback"]
    assert rollback_state[
        "curriculum_goal_pair_recovery_rollback_count"] == 1
    assert rollback_state[
        "curriculum_goal_pair_last_recovery_rollback"] == (
            "mixed:0->retention:performance_regression")

    fallback = FingertipApproachCurriculum(rollback_config)
    fallback.stage = "goal_pair"
    fallback.required_song_fingers = (1, 2, 3, 4)
    fallback.goal_pair_incoming_fingers = (1, 2, 3, 4)
    fallback.goal_pair_phase = "retention"
    fallback.goal_pair_recovery_active = True
    fallback.goal_pair_recovery_reason = "retention_timeout"
    fallback.goal_pair_phase_baseline = {
        "f1": 0.95,
        "no_press": 0.995,
        "wrong": 0.005,
        "event_success": 0.95,
        "finger_min": 0.95,
        "failure": 0.0,
    }
    fallback.goal_pair_phase_baseline_label = "retention"
    fallback.regression_hold = True
    fallback_stats = _stats(rehearsal_pass=False)
    fallback_stats["f1_l"] = 0.50
    fallback.after_iteration(fallback_stats)
    fallback_state = fallback.after_iteration(fallback_stats)
    assert fallback.stage == "frozen_context"
    assert fallback_state["curriculum_goal_pair_recovery_rollback"]
    assert fallback_state[
        "curriculum_goal_pair_last_recovery_rollback"] == (
            "retention->frozen_context:retention_timeout")

    timeout_config = replace(
        config,
        goal_pair_phase_max_iterations=2,
        goal_pair_retention_min_iterations=1)
    timeout = FingertipApproachCurriculum(
        timeout_config, forced_stage="goal_pair")
    timeout.required_song_fingers = (1, 2, 3, 4)
    timeout.goal_pair_incoming_fingers = (1, 2, 3, 4)
    timeout.after_iteration(_stats(rehearsal_pass=False))
    timeout_state = timeout.after_iteration(
        _stats(rehearsal_pass=False))
    assert timeout.goal_pair_phase == "retention"
    assert timeout.goal_pair_phase_iteration == 0
    assert timeout.goal_pair_mastered_fingers == [True, True, True, False]
    assert timeout_state["curriculum_goal_pair_phase_timeout_count"] == 1
    assert timeout_state["curriculum_goal_pair_focus_probability"] == 0.40
    assert timeout_state["curriculum_goal_pair_recovery"]
    assert timeout_state["curriculum_goal_pair_rehearsal_probability"] == 0.50
    assert timeout_state["curriculum_goal_pair_sequence_probability"] == 0.50

    mixed_timeout = FingertipApproachCurriculum(
        timeout_config, forced_stage="goal_pair")
    mixed_timeout.goal_pair_phase = "mixed"
    mixed_timeout.required_song_fingers = (1, 2, 3, 4)
    mixed_timeout.goal_pair_incoming_fingers = (1, 2, 3, 4)
    mixed_timeout.after_iteration(_stats(rehearsal_pass=False))
    mixed_timeout_state = mixed_timeout.after_iteration(
        _stats(rehearsal_pass=False))
    assert mixed_timeout_state["curriculum_goal_pair_recovery"]
    assert mixed_timeout_state[
        "curriculum_goal_pair_recovery_reason"] == "mixed_timeout"
    assert mixed_timeout_state[
        "curriculum_goal_pair_rehearsal_probability"] == 0.50
    assert mixed_timeout_state[
        "curriculum_goal_pair_sequence_probability"] == 0.50
    assert not mixed_timeout_state["curriculum_goal_pair_preview_only"]

    regression_config = replace(
        config,
        goal_pair_mastery_regression_windows=2)
    mastery_regression = FingertipApproachCurriculum(
        regression_config, forced_stage="goal_pair")
    mastery_regression.required_song_fingers = (1, 2, 3, 4)
    mastery_regression.goal_pair_incoming_fingers = (1, 2, 3, 4)
    mastery_regression.goal_pair_mastered_fingers = [True] * 4
    mastery_regression.goal_pair_mastery_streaks = [2] * 4
    mastery_regression.after_iteration(_stats(rehearsal_pass=False))
    assert mastery_regression.goal_pair_mastered_fingers[3]
    state = mastery_regression.after_iteration(
        _stats(rehearsal_pass=False))
    assert not mastery_regression.goal_pair_mastered_fingers[3]
    assert state["curriculum_goal_pair_focus_finger"] == 4

    focus_lock_config = replace(
        config,
        goal_pair_focus_min_iterations=3,
        goal_pair_retention_min_iterations=20)
    focus_lock = FingertipApproachCurriculum(
        focus_lock_config, forced_stage="goal_pair")
    focus_lock.required_song_fingers = (1, 2, 3, 4)
    focus_lock.goal_pair_incoming_fingers = (1, 2, 3, 4)
    focus_lock.after_iteration(_stats(rehearsal_pass=False))
    assert focus_lock.goal_pair_focus_finger == 4
    weak_third = _stats()
    weak_third[
        "curriculum_goal_pair_rehearsal_finger_3_press_success"] = 0.0
    weak_third[
        "curriculum_goal_pair_rehearsal_finger_3_target_distance"] = 0.040
    weak_third[
        "curriculum_goal_pair_rehearsal_finger_4_press_success"] = 0.0
    weak_third[
        "curriculum_goal_pair_rehearsal_finger_4_target_distance"] = 0.040
    focus_lock.after_iteration(weak_third)
    focus_lock.after_iteration(weak_third)
    assert focus_lock.goal_pair_focus_finger == 4
    focus_lock.after_iteration(weak_third)
    assert focus_lock.goal_pair_focus_finger == 3

    synchronized_focus = FingertipApproachCurriculum(
        focus_lock_config, forced_stage="goal_pair")
    synchronized_focus.required_song_fingers = (1, 2, 3, 4)
    synchronized_focus.goal_pair_incoming_fingers = (1, 2, 3, 4)
    scores = {
        1: (0.80, -0.01, 1),
        2: (0.70, -0.01, 2),
        3: (0.30, -0.04, 3),
        4: (0.60, -0.02, 4),
    }
    for finger in range(1, 4):
        synchronized_focus._update_goal_pair_focus(
            {}, {finger: (False, scores[finger])})
        assert synchronized_focus.goal_pair_focus_finger == 0
    synchronized_focus._update_goal_pair_focus(
        {}, {4: (False, scores[4])})
    assert synchronized_focus.goal_pair_focus_finger == 3

    bridge_focus = FingertipApproachCurriculum(
        focus_lock_config, forced_stage="goal_pair")
    bridge_focus.required_song_fingers = (1, 2, 3, 4)
    bridge_focus.goal_pair_incoming_fingers = (1, 2, 3, 4)
    bridge_focus.goal_pair_recovery_active = True
    bridge_focus.bridge_last_metrics = {
        "finger_1_rate": 0.60,
        "finger_2_rate": 0.20,
        "finger_3_rate": 0.40,
        "finger_4_rate": 0.50,
    }
    bridge_focus._update_goal_pair_focus(
        {}, {
            finger: (False, scores[finger])
            for finger in range(1, 5)
        })
    assert bridge_focus.goal_pair_focus_finger == 2

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
            {"goal_pair_phase_max_iterations": 0},
            {"goal_pair_focus_min_iterations": 0},
            {"goal_pair_recovery_min_iterations": 0},
            {"goal_pair_recovery_max_iterations": 1},
            {"goal_pair_recovery_windows": 0},
            {"goal_pair_recovery_rehearsal_probability": 1.1},
            {"goal_pair_phase_baseline_warmup_iterations": -1},
            {"goal_pair_mastery_regression_windows": 0},
            {"goal_pair_mastery_retain_distance": 0.0},
            {"goal_pair_rehearsal_hold_quality": 0.70},
            {"goal_pair_rehearsal_dropout_rate": 0.20},
            {"frozen_context_focus_probability": 1.1},
            {"frozen_context_focus_min_evidence": 0},
            {"frozen_context_recovery_distance": 0.0},
            {"frozen_context_hard_min_f1_rate": 1.1},
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

    print("PASS: phase-relative goal-pair recovery and schema-44 migration")


if __name__ == "__main__":
    main()
