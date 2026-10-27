"""frozen-context 학습 표본과 승급 평가의 분리 계약."""
from dataclasses import replace
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.curriculum import (
    FingertipApproachCurriculum,
    FingertipApproachCurriculumConfig,
)
from train_fret import (
    DEFAULT_STOP_ON_CURRICULUM_STALL,
    finger_acquisition_schedule,
    finger_precision_schedule,
    format_frozen_context_runtime,
    fret_curriculum_stall_reason,
    frozen_context_runtime_snapshot,
    resolve_out_dir,
)


def _episode_stats(rate, episodes=1.0, weak_finger=None):
    stats = {
        "episodes": float(episodes),
        "f1_l": float(rate),
        "no_press_accuracy": 0.98 if rate >= 0.7 else 0.75,
        "no_press_correct_count": 98.0 if rate >= 0.7 else 75.0,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.01 if rate >= 0.7 else 0.20,
        "sustain_hold_rate": float(rate),
        "sustain_event_success_rate": float(rate),
        "sustain_event_count": 2.0,
        "press_dropout_rate": 0.01 if rate >= 0.7 else 0.20,
        "failure_termination": 0.0,
        "nonfinite": 0.0,
        "velocity_blowup": 0.0,
    }
    for finger in range(1, 5):
        finger_rate = 0.10 if finger == weak_finger else float(rate)
        stats[f"press_finger_{finger}_success"] = 10.0 * finger_rate
        stats[f"press_finger_{finger}_count"] = 10.0
        stats[f"finger_{finger}_press_success_frames"] = int(
            round(10.0 * finger_rate))
        stats[f"finger_{finger}_press_target_frames"] = 10
        stats[f"curriculum_finger_{finger}_target_active_count"] = 10.0
        stats[f"curriculum_finger_{finger}_target_distance"] = (
            0.080 if finger == weak_finger else 0.005)
        stats[f"finger_{finger}_target_distance_active_frames"] = 10.0
        stats[f"finger_{finger}_target_distance_sum"] = (
            0.80 if finger == weak_finger else 0.05)
    stats["thumb_press_readiness_sum"] = 9.0
    stats["thumb_press_readiness_count"] = 10.0
    stats["curriculum_thumb_press_readiness"] = 0.9
    return stats


def _split_stats(train_rate, eval_rate, weak_finger=None):
    stats = _episode_stats(eval_rate)
    stats["_frozen_train"] = _episode_stats(
        train_rate, weak_finger=weak_finger)
    stats["_frozen_eval"] = _episode_stats(eval_rate)
    return stats


def test_promotion_uses_only_fixed_evaluation_cohort():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        frozen_context_final_evaluation_iterations=2,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=2,
        frozen_context_recovery_max_blocks=4,
        bridge_window_episodes=2,
        bridge_promotion_windows=2,
        frozen_context_evaluation_min_finger_frames=1,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)

    state = curriculum.after_iteration(_split_stats(0.96, 0.10))
    assert not state["curriculum_frozen_context_evaluation_started"]
    assert state["curriculum_frozen_context_recovery_active"]
    assert state["curriculum_frozen_context_recovery_ready_streak"] == 1
    assert state["curriculum_frozen_context_recovery_teacher_scale"] == 0.0
    assert all(abs(
        state[
            f"curriculum_frozen_context_recovery_finger_{finger}_distance"]
        - 0.005) < 1e-9 for finger in range(1, 5))
    assert curriculum.bridge_accumulator["episodes"] == 0.0

    # 실제 러너에서는 이 경계의 apply()가 real-context reset을 한 번 수행한다.
    curriculum.frozen_context_final_applied = True
    state = curriculum.after_iteration(_split_stats(0.96, 0.10))
    assert not state["curriculum_frozen_context_recovery_active"]
    assert state[
        "curriculum_frozen_context_recovery_completed_iteration"] == 2
    assert state[
        "curriculum_frozen_context_evaluation_settle_iteration"] == 0
    assert not state["curriculum_frozen_context_evaluation_started"]

    state = curriculum.after_iteration(_split_stats(0.10, 0.96))
    assert state[
        "curriculum_frozen_context_evaluation_settle_iteration"] == 1
    assert not state["curriculum_frozen_context_evaluation_started"]

    state = curriculum.after_iteration(_split_stats(0.10, 0.96))
    assert state["curriculum_frozen_context_evaluation_started"]
    assert state["curriculum_frozen_context_evidence_reset_count"] == 1
    assert curriculum.bridge_accumulator["episodes"] == 1.0

    curriculum.after_iteration(_split_stats(0.10, 0.96))
    assert len(curriculum.bridge_windows) == 1
    assert curriculum.frozen_context_evidence_reset_count == 1
    assert curriculum.bridge_last_metrics["f1"] > 0.95
    assert curriculum.bridge_last_metrics["finger_min"] > 0.95


def test_missing_recovery_distance_state_is_json_finite():
    curriculum = FingertipApproachCurriculum(
        forced_stage="frozen_context")
    state = curriculum.state()
    json.dumps(state, allow_nan=False)
    assert state[
        "curriculum_frozen_context_recovery_last_distances"
    ] == {1: -1.0, 2: -1.0, 3: -1.0, 4: -1.0}
    assert all(
        state[
            f"curriculum_frozen_context_recovery_finger_{finger}_distance"
        ] == -1.0 for finger in range(1, 5))
    restored = FingertipApproachCurriculum(
        forced_stage="frozen_context")
    restored.load_context(state)
    assert all(math.isinf(distance) for distance in
               restored.frozen_context_recovery_last_distances.values())


def test_adaptive_weight_update_never_clears_bridge_evidence():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=1000,
        frozen_context_context_ramp_iterations=1,
        frozen_context_final_evaluation_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_min_weight_change=0.0,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.bridge_accumulator["episodes"] = 0.5
    before = dict(curriculum.bridge_accumulator)

    state = curriculum.after_iteration(
        _split_stats(0.95, 0.95, weak_finger=2))
    weights = state["curriculum_frozen_context_recovery_weights"]
    assert weights[1] == max(weights)
    assert all(weight >= 0.20 for weight in weights)
    assert abs(sum(weights) - 1.0) < 1e-9
    assert curriculum.bridge_accumulator == before
    assert state["curriculum_frozen_context_evidence_reset_count"] == 0


def test_ranked_sampler_alternates_equal_weak_fingers():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=1000,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_max_blocks=4,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)

    state = curriculum.after_iteration(
        _split_stats(0.95, 0.95, weak_finger=3))
    assert all(
        abs(left - right) < 1e-9
        for left, right in zip(
            state["curriculum_frozen_context_recovery_weights"],
            (0.2, 0.2, 0.4, 0.2)))
    assert state["curriculum_frozen_context_sampler_update_count"] == 1

    state = curriculum.after_iteration(
        _split_stats(0.95, 0.95, weak_finger=4))
    assert all(
        abs(left - right) < 1e-9
        for left, right in zip(
            state["curriculum_frozen_context_recovery_weights"],
            (0.2, 0.2, 0.2, 0.4)))
    assert state["curriculum_frozen_context_sampler_update_count"] == 2


def test_recovery_requires_best_rate_retention():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=1000,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=2,
        frozen_context_recovery_max_blocks=4,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)

    state = curriculum.after_iteration(_split_stats(0.95, 0.95))
    assert state["curriculum_frozen_context_recovery_ready_streak"] == 1

    regressed = _split_stats(0.95, 0.95)
    regressed["_frozen_train"]["press_finger_2_success"] = 8.0
    regressed["_frozen_train"]["finger_2_press_success_frames"] = 8
    state = curriculum.after_iteration(regressed)
    assert state["curriculum_frozen_context_recovery_active"]
    assert state["curriculum_frozen_context_recovery_ready_streak"] == 0
    assert abs(
        state["curriculum_frozen_context_recovery_retention_max_drop"]
        - 0.20) < 1e-9
    assert abs(
        state["curriculum_frozen_context_recovery_weights"][1]
        - 0.4) < 1e-9


def test_recovery_assistance_uses_pooled_train_distance():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=1000,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=2,
        frozen_context_recovery_max_blocks=4,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    distance_failure = _split_stats(0.95, 0.95)
    train = distance_failure["_frozen_train"]
    train["finger_2_target_distance_active_frames"] = 10.0
    train["finger_2_target_distance_sum"] = 0.50
    distance_failure["_frozen_eval"][
        "finger_2_target_distance_sum"] = 0.001
    distance_failure["curriculum_finger_2_target_distance"] = 0.0001
    distance_failure["curriculum_finger_2_target_active_count"] = 1000.0

    state = curriculum.after_iteration(distance_failure)
    assert state["curriculum_frozen_context_recovery_ready_streak"] == 0
    assert state["curriculum_frozen_context_recovery_teacher_scale"] == 1.0
    assert state[
        "curriculum_frozen_context_recovery_finger_2_distance"] == 0.05
    assert abs(
        state["curriculum_frozen_context_recovery_weights"][1]
        - 0.4) < 1e-9


def test_recovery_does_not_fallback_to_full_rollout_distance():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=1000,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_max_blocks=4,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    split = _split_stats(0.95, 0.95)
    for finger in range(1, 5):
        split["_frozen_train"].pop(
            f"finger_{finger}_target_distance_sum")
        split["_frozen_train"].pop(
            f"finger_{finger}_target_distance_active_frames")
        split[f"curriculum_finger_{finger}_target_distance"] = 0.001
        split[f"curriculum_finger_{finger}_target_active_count"] = 1000.0

    state = curriculum.after_iteration(split)
    assert state[
        "curriculum_frozen_context_recovery_last_update_reason"
    ] == "insufficient_evidence:1,2,3,4"
    assert state["curriculum_frozen_context_recovery_ready_streak"] == 0


def test_frozen_promotion_uses_fixed_eval_thumb_readiness():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_min_iterations=1,
        frozen_context_max_iterations=100,
        thumb_geometry_gate_enabled=True,
        thumb_press_readiness_rate=0.35,
    )

    def stage_after(top_readiness, eval_readiness):
        curriculum = FingertipApproachCurriculum(config)
        curriculum.stage = "frozen_context"
        curriculum.stage_iteration = 1
        curriculum.frozen_context_recovery_active = False
        curriculum.frozen_context_evaluation_started = True
        curriculum.frozen_context_evaluation_started_iteration = 0
        curriculum._bridge_difficulty_ready = lambda: True
        curriculum._bridge_windows_pass = lambda soft=False: True
        curriculum._after_bridge_iteration(
            {"curriculum_thumb_press_readiness": top_readiness},
            bridge_stats={
                "curriculum_thumb_press_readiness": eval_readiness})
        return curriculum.stage

    assert stage_after(0.95, 0.10) == "frozen_context"
    assert stage_after(0.10, 0.95) == "goal_pair"


def test_recovery_exhaustion_stalls_without_evaluation():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_max_blocks=2,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)

    state = curriculum.after_iteration(
        _split_stats(0.95, 0.95, weak_finger=3))
    assert not state["curriculum_stalled"]
    state = curriculum.after_iteration(
        _split_stats(0.95, 0.95, weak_finger=3))
    assert state["curriculum_stalled"]
    assert state["curriculum_frozen_context_recovery_failed"]
    assert state["curriculum_frozen_context_recovery_exhausted"]
    assert not state["curriculum_frozen_context_recovery_active"]
    assert not state["curriculum_frozen_context_evaluation_started"]
    assert state["curriculum_frozen_context_phase"] == "recovery_failed"
    assert state["curriculum_frozen_context_recovery_teacher_scale"] == 0.0
    assert state["curriculum_frozen_context_evidence_reset_count"] == 0


def test_missing_evidence_also_exhausts_recovery_blocks():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_max_blocks=2,
    )
    curriculum = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    curriculum.required_song_fingers = (1, 2, 3, 4)

    state = curriculum.after_iteration({})
    assert state["curriculum_frozen_context_recovery_block_count"] == 1
    assert state[
        "curriculum_frozen_context_recovery_last_update_reason"
    ].startswith("insufficient_evidence:")
    state = curriculum.after_iteration({})
    assert state["curriculum_frozen_context_recovery_block_count"] == 2
    assert state["curriculum_frozen_context_recovery_failed"]
    assert state["curriculum_stalled"]


def test_schema58_round_trip_and_schema56_restart_recovery():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        frozen_context_final_evaluation_iterations=5,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=2,
    )
    source = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    source.required_song_fingers = (1, 2, 3, 4)
    source.frozen_context_final_applied = True
    source.after_iteration(_split_stats(0.95, 0.95))
    state = source.after_iteration(_split_stats(0.95, 0.95))
    assert state["curriculum_schema_version"] == 58
    assert state[
        "curriculum_frozen_context_recovery_completed_iteration"] == 2

    restored = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    restored.load_context(state)
    restored_state = restored.state()
    assert restored_state[
        "curriculum_frozen_context_recovery_completed_iteration"] == 2
    assert not restored_state["curriculum_frozen_context_recovery_active"]
    assert restored_state[
        "curriculum_frozen_context_evaluation_settle_target"] == 5
    assert restored_state[
        "curriculum_frozen_context_recovery_last_distances"
    ] == state["curriculum_frozen_context_recovery_last_distances"]

    missing_distance = dict(state)
    missing_distance.pop(
        "curriculum_frozen_context_recovery_last_distances")
    restored_missing = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    restored_missing.load_context(missing_distance)
    assert all(math.isinf(distance) for distance in
               restored_missing.frozen_context_recovery_last_distances.values())

    schema56 = dict(state)
    schema56.update({
        "curriculum_schema_version": 56,
        "curriculum_stage_iteration": 38500,
        "curriculum_frozen_context_evaluation_started": True,
        "curriculum_stalled": True,
    })
    migrated = FingertipApproachCurriculum(
        config, forced_stage="frozen_context")
    migrated.load_context(schema56)
    migrated_state = migrated.state()
    assert migrated.stage_iteration == 0
    assert not migrated_state["curriculum_stalled"]
    assert migrated_state["curriculum_frozen_context_recovery_active"]
    assert migrated_state[
        "curriculum_frozen_context_recovery_completed_iteration"] == -1
    assert not migrated_state[
        "curriculum_frozen_context_evaluation_started"]


def test_frozen_timeout_clock_starts_at_evaluation():
    config = replace(
        FingertipApproachCurriculumConfig(),
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        frozen_context_final_evaluation_iterations=200,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=1,
        frozen_context_recovery_max_blocks=8,
    )
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "frozen_context"
    curriculum.stage_iteration = 3999
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.frozen_context_final_applied = True

    state = curriculum.after_iteration(_split_stats(0.95, 0.95))
    assert state[
        "curriculum_frozen_context_recovery_completed_iteration"] == 4000
    assert not state["curriculum_stalled"]
    for _ in range(199):
        state = curriculum.after_iteration(_split_stats(0.10, 0.95))
        assert not state["curriculum_stalled"]
        assert not state["curriculum_frozen_context_evaluation_started"]
    state = curriculum.after_iteration(_split_stats(0.10, 0.95))
    assert state["curriculum_stage_iteration"] == 4200
    assert state["curriculum_frozen_context_evaluation_started"]
    assert state["curriculum_frozen_context_evaluation_iteration"] == 0
    assert not state["curriculum_stalled"]


class _FakeGoals:
    practice_available_fingers = range(4)
    practice_goal_pair_available_incoming_fingers = ()

    def __init__(self):
        self.weights = None
        self.mix = None
        self.evaluation_fraction = None

    def set_chord_focus_index(self, *_args, **_kwargs):
        return False

    def set_random_start_probability(self, _value):
        return False

    def set_frozen_context_real_probability(self, _value):
        return False

    def set_frozen_context_finger_weights(self, weights):
        changed = tuple(weights) != self.weights
        self.weights = tuple(weights)
        return changed

    def set_frozen_context_mix_weights(self, weights):
        self.mix = tuple(weights)
        return True

    def set_frozen_context_evaluation_fraction(self, fraction):
        self.evaluation_fraction = float(fraction)
        return True


class _FakeEnv:
    def __init__(self):
        self.goals = _FakeGoals()
        self.reset_count = 0
        self.recovery_calls = []

    def set_frozen_context_recovery(self, active, teacher_scale=0.0):
        self.recovery_calls.append((bool(active), float(teacher_scale)))
        return True

    def set_curriculum_stage(self, *_args, **_kwargs):
        return None

    def reset(self):
        self.reset_count += 1
        return "reset"


def test_weight_changes_do_not_reset_active_environments():
    curriculum = FingertipApproachCurriculum(
        forced_stage="frozen_context")
    env = _FakeEnv()
    curriculum.apply(env)
    assert env.reset_count == 0
    assert env.recovery_calls[-1] == (True, 1.0)
    curriculum.frozen_context_recovery_weights = (0.2, 0.3, 0.25, 0.25)
    curriculum.frozen_context_recovery_last_rates = {
        1: 0.80, 2: 0.60, 3: 0.80, 4: 0.80}
    curriculum.frozen_context_recovery_last_distances = {
        finger: 0.020 for finger in range(1, 5)}
    curriculum.apply(env)
    assert env.goals.weights == (0.2, 0.3, 0.25, 0.25)
    assert env.recovery_calls[-1][0]
    assert abs(env.recovery_calls[-1][1] - 0.5) < 1e-9
    assert env.reset_count == 0

    curriculum.frozen_context_recovery_last_rates = {
        finger: 0.80 for finger in range(1, 5)}
    curriculum.frozen_context_recovery_last_distances[2] = 0.050
    curriculum.apply(env)
    assert env.recovery_calls[-1] == (True, 1.0)
    curriculum.frozen_context_recovery_last_distances[2] = 0.0375
    curriculum.apply(env)
    assert env.recovery_calls[-1][0]
    assert abs(env.recovery_calls[-1][1] - 0.5) < 1e-9
    curriculum.frozen_context_recovery_last_distances[2] = 0.025
    curriculum.apply(env)
    assert env.recovery_calls[-1] == (True, 0.0)


def test_exploration_and_stall_contracts():
    recovery = {
        "curriculum_stage": "frozen_context",
        "curriculum_stage_iteration": 500,
        "curriculum_frozen_context_recovery_active": True,
        "curriculum_frozen_context_recovery_exhausted": False,
        "curriculum_frozen_context_recovery_focus_fingers": [3, 4],
        "curriculum_frozen_context_recovery_ready_streak": 1,
        "curriculum_frozen_context_recovery_teacher_scale": 0.75,
        "curriculum_frozen_context_sampler_update_count": 2,
        "curriculum_frozen_context_evaluation_started": False,
        "curriculum_frozen_context_evaluation_settle_iteration": 0,
        "curriculum_frozen_context_evaluation_settle_progress": 0.0,
        "curriculum_frozen_context_evaluation_settle_target": 200,
    }
    assert finger_acquisition_schedule(recovery) == (True, (3, 4))
    assert finger_precision_schedule(recovery) == (False, 0, ())

    settle = dict(
        recovery,
        curriculum_stage_iteration=650,
        curriculum_frozen_context_recovery_active=False,
        curriculum_frozen_context_recovery_completed_iteration=500,
        curriculum_frozen_context_recovery_teacher_scale=0.0,
        curriculum_frozen_context_evaluation_settle_iteration=150,
        curriculum_frozen_context_evaluation_settle_progress=0.75,
    )
    assert finger_acquisition_schedule(settle) == (False, ())
    assert finger_precision_schedule(settle) == (True, 150, ())
    settle_snapshot = frozen_context_runtime_snapshot(settle)
    assert settle_snapshot["phase"] == "teacher_free_settle"
    assert settle_snapshot["precision_age"] == 150
    assert "settle=150/200 (75%)" in format_frozen_context_runtime(
        settle_snapshot)

    evaluation = dict(
        settle,
        curriculum_stage_iteration=737,
        curriculum_frozen_context_evaluation_started=True,
        curriculum_frozen_context_evaluation_iteration=37,
        curriculum_frozen_context_evaluation_settle_iteration=200,
        curriculum_frozen_context_evaluation_settle_progress=1.0,
    )
    assert finger_acquisition_schedule(evaluation) == (False, ())
    assert finger_precision_schedule(evaluation) == (True, 237, ())
    assert frozen_context_runtime_snapshot(evaluation)["phase"] == "evaluation"

    assert fret_curriculum_stall_reason({
        "curriculum_stage": "frozen_context",
        "curriculum_stalled": True,
        "curriculum_frozen_context_evaluation_started": True,
    }) == "curriculum_stall:frozen_context:evaluation_failed"
    assert fret_curriculum_stall_reason({
        "curriculum_stage": "frozen_context",
        "curriculum_stalled": True,
        "curriculum_frozen_context_evaluation_started": False,
    }) is None
    assert fret_curriculum_stall_reason({
        "next_curriculum_stage": "frozen_context",
        "next_curriculum_stalled": True,
        "next_curriculum_frozen_context_recovery_active": True,
        "next_curriculum_frozen_context_recovery_exhausted": True,
        "next_curriculum_frozen_context_evaluation_started": False,
    }) == "curriculum_stall:frozen_context:recovery_exhausted"


def test_contract_migration_uses_a_new_run_directory():
    checkpoint = (
        "/tmp/old_fret_run/checkpoints/fret_034500.pt")
    resumed = Path(resolve_out_dir(
        "song", checkpoint=checkpoint))
    migrated = Path(resolve_out_dir(
        "song", checkpoint=checkpoint, migrate_contract=True))
    assert resumed == Path("/tmp/old_fret_run")
    assert migrated != resumed
    assert migrated.parent.name == "runs"
    assert migrated.name.endswith("_song")


def test_structural_curriculum_stall_stops_by_default():
    assert DEFAULT_STOP_ON_CURRICULUM_STALL is True


def main():
    test_promotion_uses_only_fixed_evaluation_cohort()
    test_missing_recovery_distance_state_is_json_finite()
    test_adaptive_weight_update_never_clears_bridge_evidence()
    test_ranked_sampler_alternates_equal_weak_fingers()
    test_recovery_requires_best_rate_retention()
    test_recovery_assistance_uses_pooled_train_distance()
    test_recovery_does_not_fallback_to_full_rollout_distance()
    test_frozen_promotion_uses_fixed_eval_thumb_readiness()
    test_recovery_exhaustion_stalls_without_evaluation()
    test_missing_evidence_also_exhausts_recovery_blocks()
    test_schema58_round_trip_and_schema56_restart_recovery()
    test_frozen_timeout_clock_starts_at_evaluation()
    test_weight_changes_do_not_reset_active_environments()
    test_exploration_and_stall_contracts()
    test_contract_migration_uses_a_new_run_directory()
    test_structural_curriculum_stall_stops_by_default()
    print("PASS: frozen-context recovery and evaluation separation")


if __name__ == "__main__":
    main()
