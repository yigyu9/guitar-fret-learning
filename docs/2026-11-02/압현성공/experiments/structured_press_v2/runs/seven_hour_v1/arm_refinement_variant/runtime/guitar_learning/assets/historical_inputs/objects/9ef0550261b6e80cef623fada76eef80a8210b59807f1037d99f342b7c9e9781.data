"""CPU contract for the incompatible strum-v2 curriculum."""
from pathlib import Path
from dataclasses import replace
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.learning.strike_curriculum import (
    A0_PICK_GRIP, A1_TIP_READY, A2_SINGLE_CROSSING, A3_TIMED_SINGLE,
    A4_STRUM_CONTEXT_RECOVERY,
    S0_TWO_STRING_STRUM, S1_STRUM_SPAN, S2_TIMED_STRUM,
    S3_SONG_INTEGRATION, STRIKE_STAGES, StrikeCurriculum,
    StrikeCurriculumConfig,
)
from tab2body.strike_cfg import STRIKE
from tab2body.strike_metrics import (
    StrikeRewardAlignmentMonitor,
    pool_strike_raw_count_rates,
    pooled_rate_from_counts,
)
from tab2body.learning.ppo import aggregate_episode_rows


def config(adaptation_iterations=0):
    return StrikeCurriculumConfig(
        min_iterations={stage: 1 for stage in STRIKE_STAGES},
        max_iterations={stage: 50 for stage in STRIKE_STAGES},
        promotion_windows=1,
        terminal_evidence_episodes=1,
        s2_profiles=tuple(STRIKE["curriculum"]["s2_profiles"]),
        tempo_lambdas=tuple(STRIKE["curriculum"]["tempo_lambdas"]),
        s3_tempo_gates=tuple(STRIKE["curriculum"]["s3_tempo_gates"]),
        s2_rollback_cooldown_iterations=0,
        s2_profile_adaptation_iterations=adaptation_iterations,
        s3_uniform_curriculum_evidence_only=False,
    )


def base():
    return {
        "episodes": 1,
        "strike_grip_success_rate": 1.0,
        "strike_grip_quality_mean": 1.0,
        "strike_grip_quality_p05": 1.0,
        "strike_grip_pinch_quality_mean": 1.0,
        "strike_grip_free_quality_mean": 1.0,
        "strike_grip_bad_frame_rate": 0.0,
        "strike_grip_bad_streak_max_frames": 0.0,
        "strike_tip_ready_success_rate": 1.0,
        "strike_release_recall": 1.0,
        "strike_false_positive_rate": 0.0,
        "strike_episode_f1": 1.0,
        "strike_true_positive_count": 2.0,
        "strike_false_positive_count": 0.0,
        "strike_false_negative_count": 0.0,
        "strike_timing_p95_ms": 0.0,
        "strike_timing_pass_rate": 1.0,
        "strike_timing_signed_mean_ms": 0.0,
        "strike_timing_signed_p10_ms": 0.0,
        "strike_timing_signed_p90_ms": 0.0,
        "strike_zone_success_rate": 1.0,
        "strike_strum_event_count": 2.0,
        "strike_strum_completion_rate": 1.0,
        "strike_strum_traversal_recall": 1.0,
        "strike_strum_order_accuracy": 1.0,
        "strike_strum_direction_accuracy": 1.0,
        "strike_strum_timing_rms_ms": 0.0,
        "strike_strum_sweep_duration_mae_ms": 0.0,
        "strike_strum_microtiming_sample_count": 1.0,
        "strike_recovery_completion_rate": 1.0,
        "strike_recovery_event_count": 2.0,
        "strike_scheduled_recovery_event_count": 2.0,
        "strike_scheduled_recovery_completed_count": 2.0,
        "strike_full_recovery_event_count": 1.0,
        "strike_full_recovery_completed_count": 1.0,
        "strike_handoff_recovery_event_count": 1.0,
        "strike_handoff_recovery_completed_count": 1.0,
        "strike_recovery_reset_rate": 0.0,
        "strike_blocked_crossing_rate": 0.0,
        "strike_blocked_crossing_count": 0.0,
        "strike_down_event_count": 1.0,
        "strike_down_completed_count": 1.0,
        "strike_up_event_count": 1.0,
        "strike_up_completed_count": 1.0,
        "failure_termination": 0.0,
        "wrong_crossing_termination": 0.0,
        "irrecoverable_safety_failure": 0.0,
    }


def main():
    grip_rows = [
        {
            "strike_grip_quality_mean": 0.90,
            "strike_grip_quality_p05": 0.80,
            "strike_grip_quality_min": 0.80,
            "strike_grip_bad_streak_max_frames": 3.0,
            "_grip_quality": [0.80, 1.00],
        },
        {
            "strike_grip_quality_mean": 0.95,
            "strike_grip_quality_p05": 0.90,
            "strike_grip_quality_min": 0.90,
            "strike_grip_bad_streak_max_frames": 7.0,
            "_grip_quality": [0.90, 1.00],
        },
    ]
    grip_aggregate = aggregate_episode_rows(
        grip_rows,
        (
            "strike_grip_quality_mean", "strike_grip_quality_p05",
            "strike_grip_quality_min",
            "strike_grip_bad_streak_max_frames",
        ),
        ())
    assert abs(grip_aggregate["strike_grip_quality_mean"] - 0.925) < 1e-6
    assert grip_aggregate["strike_grip_quality_min"] == 0.80
    assert grip_aggregate["strike_grip_bad_streak_max_frames"] == 7.0

    raw_metric_keys = (
        "strike_down_event_count", "strike_down_completed_count",
        "strike_up_event_count", "strike_up_completed_count",
        "strike_strum_event_count", "strike_strum_completion_rate",
        "strike_down_completion_rate", "strike_up_completion_rate",
        "strike_worst_direction_completion_rate",
        "strike_recovery_event_count",
        "strike_scheduled_recovery_event_count",
        "strike_scheduled_recovery_completed_count",
        "strike_conditional_recovery_completion_rate",
        "strike_scheduled_recovery_completion_rate",
        "strike_end_to_end_recovery_completion_rate",
    )
    pooled_episode_rows = aggregate_episode_rows([
        {
            "strike_down_event_count": 10.0,
            "strike_down_completed_count": 10.0,
            "strike_up_event_count": 1.0,
            "strike_up_completed_count": 0.0,
            "strike_strum_event_count": 11.0,
            "strike_strum_completion_rate": 0.0,
            "strike_down_completion_rate": 0.0,
            "strike_up_completion_rate": 0.0,
            "strike_worst_direction_completion_rate": 0.0,
            "strike_recovery_event_count": 10.0,
            "strike_scheduled_recovery_event_count": 20.0,
            "strike_scheduled_recovery_completed_count": 5.0,
            "strike_conditional_recovery_completion_rate": 0.0,
            "strike_scheduled_recovery_completion_rate": 0.0,
            "strike_end_to_end_recovery_completion_rate": 0.0,
        },
        {
            "strike_down_event_count": 1.0,
            "strike_down_completed_count": 0.0,
            "strike_up_event_count": 20.0,
            "strike_up_completed_count": 20.0,
            "strike_strum_event_count": 21.0,
            "strike_strum_completion_rate": 0.0,
            "strike_down_completion_rate": 0.0,
            "strike_up_completion_rate": 0.0,
            "strike_worst_direction_completion_rate": 0.0,
            "strike_recovery_event_count": 1.0,
            "strike_scheduled_recovery_event_count": 1.0,
            "strike_scheduled_recovery_completed_count": 1.0,
            "strike_conditional_recovery_completion_rate": 0.0,
            "strike_scheduled_recovery_completion_rate": 0.0,
            "strike_end_to_end_recovery_completion_rate": 0.0,
        },
    ], raw_metric_keys, ())
    assert abs(
        pooled_episode_rows["strike_down_completion_rate"] - 10.0 / 11.0
    ) < 1e-9
    assert abs(
        pooled_episode_rows["strike_up_completion_rate"] - 20.0 / 21.0
    ) < 1e-9
    assert abs(
        pooled_episode_rows["strike_worst_direction_completion_rate"]
        - 10.0 / 11.0
    ) < 1e-9
    assert abs(
        pooled_episode_rows["strike_strum_completion_rate"] - 30.0 / 32.0
    ) < 1e-9
    assert abs(
        pooled_episode_rows[
            "strike_conditional_recovery_completion_rate"] - 6.0 / 11.0
    ) < 1e-9
    assert abs(
        pooled_episode_rows[
            "strike_end_to_end_recovery_completion_rate"] - 6.0 / 21.0
    ) < 1e-9

    degraded_grip = StrikeCurriculum(config())
    degraded = base()
    degraded["strike_grip_quality_p05"] = 0.84
    degraded_grip.after_iteration(degraded)
    assert degraded_grip.stage == A0_PICK_GRIP
    assert "grip_quality_p05" in degraded_grip.last_gate_failures

    stalled = StrikeCurriculum(config())
    stalled.stage = S0_TWO_STRING_STRUM
    failed_strum = base()
    failed_strum["strike_release_recall"] = 0.0
    failed_strum["strike_strum_completion_rate"] = 0.0
    failed_strum["strike_strum_traversal_recall"] = 0.0
    for _ in range(50):
        stalled.after_iteration(failed_strum)
    assert stalled.stalled
    assert stalled.stage == S0_TWO_STRING_STRUM
    total_at_stall = stalled.total_iteration
    stalled.after_iteration(base())
    assert stalled.total_iteration == total_at_stall + 1
    assert stalled.stage == S1_STRUM_SPAN
    assert not stalled.stalled

    recovery_gate = StrikeCurriculum(config())
    recovery_gate.stage = A4_STRUM_CONTEXT_RECOVERY
    noisy_recovery = base()
    noisy_recovery["strike_recovery_reset_rate"] = 0.1
    noisy_recovery["strike_blocked_crossing_rate"] = 0.1
    noisy_recovery["strike_blocked_crossing_count"] = 0.2
    recovery_gate.after_iteration(noisy_recovery)
    assert "recovery_reset_rate" in recovery_gate.last_gate_failures
    assert "blocked_crossing_rate" in recovery_gate.last_gate_failures

    dual_recovery_gate = StrikeCurriculum(config())
    dual_recovery_gate.stage = S3_SONG_INTEGRATION
    impossible_fixed = base()
    impossible_fixed["strike_recovery_completion_rate"] = 0.77
    dual_recovery_gate.after_iteration(impossible_fixed)
    assert "recovery_completion" not in dual_recovery_gate.last_gate_failures
    assert "scheduled_recovery_completion" not in (
        dual_recovery_gate.last_gate_failures)
    failed_handoff = base()
    failed_handoff["strike_handoff_recovery_completed_count"] = 0.0
    dual_recovery_gate.after_iteration(failed_handoff)
    assert "handoff_recovery_completion" in (
        dual_recovery_gate.last_gate_failures)

    success_gated = StrikeCurriculum(config())
    success_gated.stage = S2_TIMED_STRUM
    success_gated.s2_profile_index = 1
    insufficient = base()
    insufficient["strike_timing_pass_rate"] = 0.69
    for _ in range(5):
        success_gated.after_iteration(insufficient)
    assert success_gated.s2_profile_name == "T0_400MS"
    assert success_gated.timing_tolerance_ms == 400
    success_gated.after_iteration(base())
    assert success_gated.s2_profile_name == "T1_250MS"

    endpoint_timing_is_diagnostic = StrikeCurriculum(config())
    endpoint_timing_is_diagnostic.stage = S2_TIMED_STRUM
    physical_success = base()
    physical_success.update({
        "strike_timing_pass_rate": 0.0,
        "strike_timing_signed_mean_ms": -390.0,
        "strike_timing_signed_p10_ms": -400.0,
        "strike_timing_signed_p90_ms": -380.0,
        "strike_strum_microtiming_sample_count": 0.0,
        "strike_strum_timing_rms_ms": 999.0,
        "strike_strum_sweep_duration_mae_ms": 999.0,
    })
    endpoint_timing_is_diagnostic.after_iteration(physical_success)
    assert endpoint_timing_is_diagnostic.s2_profile_name == "T0_400MS"

    centering_gate = StrikeCurriculum(config())
    centering_gate.stage = S2_TIMED_STRUM
    centering_gate.s2_profile_index = 2
    off_center = base()
    off_center["strike_timing_signed_mean_ms"] = -170.0
    off_center["strike_timing_signed_p10_ms"] = -200.0
    off_center["strike_timing_signed_p90_ms"] = -140.0
    centering_gate.after_iteration(off_center)
    assert centering_gate.s2_profile_name == "T1_250MS"
    assert "timing_center_mean" in centering_gate.last_gate_failures
    assert "timing_center_tail" in centering_gate.last_gate_failures
    centering_gate.after_iteration(base())
    assert centering_gate.s2_profile_name == "T2_225MS"

    adaptation = StrikeCurriculum(config(adaptation_iterations=2))
    adaptation.stage = S2_TIMED_STRUM
    adaptation.after_iteration(base())
    assert adaptation.s2_profile_name == "T0_400MS"
    assert adaptation.s2_adaptation_remaining == 2
    severe_adaptation = base()
    severe_adaptation["strike_timing_pass_rate"] = 0.0
    severe_adaptation["strike_strum_completion_rate"] = 0.0
    severe_adaptation["strike_strum_traversal_recall"] = 0.0
    for _ in range(2):
        adaptation.after_iteration(severe_adaptation)
    assert adaptation.s2_profile_name == "T0_400MS"
    assert adaptation.rollback_count == 0
    for _ in range(3):
        adaptation.after_iteration(severe_adaptation)
    assert adaptation.s2_profile_name == "E0_BALANCED_ENDPOINT"
    assert adaptation.rollback_count == 1

    rollback = StrikeCurriculum(config())
    rollback.stage = S2_TIMED_STRUM
    rollback.s2_profile_index = 2
    severe = base()
    severe["strike_timing_pass_rate"] = 0.0
    severe["strike_strum_completion_rate"] = 0.0
    severe["strike_strum_traversal_recall"] = 0.0
    for _ in range(3):
        rollback.after_iteration(severe)
    assert rollback.s2_profile_name == "T0_400MS"
    assert rollback.rollback_count == 1
    restored_rollback = StrikeCurriculum(config())
    restored_rollback.load_context(rollback.state())
    assert restored_rollback.state() == rollback.state()

    transferred = StrikeCurriculum(config())
    transfer_state = transferred.initialize_song_integration_transfer(0.5)
    assert transferred.stage == S3_SONG_INTEGRATION
    assert transferred.tempo_lambda == 0.5
    assert transferred.total_iteration == 0
    assert transfer_state["curriculum_last_gate_failures"] == "policy_transfer"

    pooled = StrikeCurriculum(config())
    pooled.stage = S3_SONG_INTEGRATION
    first = base()
    first.update({
        "episodes": 2,
        "strike_true_positive_count": 2.0,
        "strike_false_positive_count": 0.0,
        "strike_false_negative_count": 0.0,
        "strike_episode_f1": 1.0,
    })
    second = base()
    second.update({
        "episodes": 1,
        "strike_true_positive_count": 0.0,
        "strike_false_positive_count": 1.0,
        "strike_false_negative_count": 1.0,
        "strike_episode_f1": 0.0,
    })
    pooled.config = StrikeCurriculumConfig(
        min_iterations={stage: 1 for stage in STRIKE_STAGES},
        max_iterations={stage: 50 for stage in STRIKE_STAGES},
        promotion_windows=1,
        terminal_evidence_episodes=3,
        s3_uniform_curriculum_evidence_only=False,
        s2_profiles=tuple(STRIKE["curriculum"]["s2_profiles"]),
        tempo_lambdas=tuple(STRIKE["curriculum"]["tempo_lambdas"]),
        s3_tempo_gates=tuple(STRIKE["curriculum"]["s3_tempo_gates"]),
    )
    assert pooled._consume_evidence(first) is None
    pooled_evidence = pooled._consume_evidence(second)
    assert abs(pooled_evidence["strike_episode_f1"] - 0.8) < 1e-6

    raw_pooled = StrikeCurriculum(config())
    raw_pooled.stage = S2_TIMED_STRUM
    raw_pooled.config = StrikeCurriculumConfig(
        min_iterations={stage: 1 for stage in STRIKE_STAGES},
        max_iterations={stage: 50 for stage in STRIKE_STAGES},
        promotion_windows=1,
        terminal_evidence_episodes=3,
        s2_profiles=tuple(STRIKE["curriculum"]["s2_profiles"]),
        tempo_lambdas=tuple(STRIKE["curriculum"]["tempo_lambdas"]),
        s3_tempo_gates=tuple(STRIKE["curriculum"]["s3_tempo_gates"]),
    )
    direction_first = base()
    direction_first.update({
        "episodes": 2,
        "strike_strum_event_count": 11.0,
        "strike_down_event_count": 10.0,
        "strike_down_completed_count": 10.0,
        "strike_up_event_count": 1.0,
        "strike_up_completed_count": 0.0,
        "strike_recovery_event_count": 10.0,
        "strike_scheduled_recovery_event_count": 20.0,
        "strike_scheduled_recovery_completed_count": 5.0,
    })
    direction_second = base()
    direction_second.update({
        "episodes": 1,
        "strike_strum_event_count": 21.0,
        "strike_down_event_count": 1.0,
        "strike_down_completed_count": 0.0,
        "strike_up_event_count": 20.0,
        "strike_up_completed_count": 20.0,
        "strike_recovery_event_count": 1.0,
        "strike_scheduled_recovery_event_count": 1.0,
        "strike_scheduled_recovery_completed_count": 1.0,
    })
    assert raw_pooled._consume_evidence(direction_first) is None
    direction_evidence = raw_pooled._consume_evidence(direction_second)
    assert abs(
        direction_evidence["strike_down_completion_rate"] - 20.0 / 21.0
    ) < 1e-9
    assert abs(
        direction_evidence["strike_up_completion_rate"] - 20.0 / 22.0
    ) < 1e-9
    assert abs(
        direction_evidence["strike_worst_direction_completion_rate"]
        - 20.0 / 22.0
    ) < 1e-9
    assert abs(
        direction_evidence["strike_conditional_recovery_completion_rate"]
        - 11.0 / 21.0
    ) < 1e-9
    assert abs(
        direction_evidence["strike_end_to_end_recovery_completion_rate"]
        - 11.0 / 41.0
    ) < 1e-9
    assert pooled_rate_from_counts(
        {"completed": 9.0, "events": 10.0},
        "completed", "events") == 0.9
    assert pooled_rate_from_counts(
        {"completed": 11.0, "events": 10.0},
        "completed", "events") is None
    pooled_rates = pool_strike_raw_count_rates({
        "strike_down_event_count": 10.0,
        "strike_down_completed_count": 9.0,
        "strike_up_event_count": 2.0,
        "strike_up_completed_count": 1.0,
        "strike_strum_event_count": 12.0,
        "strike_recovery_event_count": 8.0,
        "strike_scheduled_recovery_event_count": 12.0,
        "strike_scheduled_recovery_completed_count": 6.0,
        "strike_down_completion_rate": 0.0,
        "strike_up_completion_rate": 0.0,
    })
    assert pooled_rates["strike_down_completion_rate"] == 0.9
    assert pooled_rates["strike_up_completion_rate"] == 0.5
    assert pooled_rates["strike_worst_direction_completion_rate"] == 0.5
    assert abs(
        pooled_rates["strike_strum_completion_rate"] - 10.0 / 12.0
    ) < 1e-9
    assert pooled_rates[
        "strike_conditional_recovery_completion_rate"] == 0.75
    assert pooled_rates[
        "strike_end_to_end_recovery_completion_rate"] == 0.5
    invalid_pooled_rates = pool_strike_raw_count_rates({
        **pooled_rates,
        "strike_down_completed_count": 11.0,
    })
    assert invalid_pooled_rates["strike_down_completion_rate"] == -1.0
    assert invalid_pooled_rates[
        "strike_worst_direction_completion_rate"] == -1.0
    assert invalid_pooled_rates["strike_strum_completion_rate"] == -1.0

    missing_direction = StrikeCurriculum(config())
    missing_direction.stage = S2_TIMED_STRUM
    missing_direction_raw = base()
    del missing_direction_raw["strike_down_completed_count"]
    missing_direction.after_iteration(missing_direction_raw)
    assert "direction_completion_evidence" in (
        missing_direction.last_gate_failures)

    endpoint_recovery = StrikeCurriculum(config())
    endpoint_recovery.stage = S2_TIMED_STRUM
    one_sided = base()
    one_sided.update({
        "strike_strum_event_count": 20.0,
        "strike_down_event_count": 10.0,
        "strike_down_completed_count": 0.0,
        "strike_up_event_count": 10.0,
        "strike_up_completed_count": 10.0,
    })
    for _ in range(3):
        endpoint_recovery.after_iteration(one_sided)
    assert endpoint_recovery.s2_endpoint_recovery_active
    assert endpoint_recovery.s2_focus_direction == "down"
    assert endpoint_recovery.s2_focus_fraction == 0.70
    assert endpoint_recovery.s2_gate_evidence_mode == "uniform_balanced"
    endpoint_state = endpoint_recovery.state()
    restored_endpoint = StrikeCurriculum(config())
    restored_endpoint.load_context(endpoint_state)
    assert restored_endpoint.state() == endpoint_state
    endpoint_recovery.after_iteration(one_sided)
    assert endpoint_recovery.s2_profile_name == "E0_BALANCED_ENDPOINT"
    assert endpoint_recovery.last_gate_failures == (
        "uniform_direction_evidence_missing",)
    uniform_success = dict(one_sided)
    uniform_success.update({
        "strike_strum_event_count": 20.0,
        "strike_down_completed_count": 10.0,
        "strike_up_completed_count": 10.0,
        "strike_true_positive_count": 20.0,
        "strike_false_negative_count": 0.0,
        "strike_recovery_event_count": 20.0,
        "strike_scheduled_recovery_event_count": 20.0,
        "strike_scheduled_recovery_completed_count": 20.0,
    })
    endpoint_recovery.after_iteration({
        **one_sided,
        "_uniform_evidence": uniform_success,
    })
    assert endpoint_recovery.s2_profile_name == "T0_400MS"
    assert not endpoint_recovery.s2_endpoint_recovery_active
    assert endpoint_recovery.s2_focus_direction == "balanced"

    timed_transfer = StrikeCurriculum(config())
    timed_transfer.after_iteration(base())
    transfer = timed_transfer.initialize_timed_strum_transfer()
    assert timed_transfer.stage == S2_TIMED_STRUM
    assert timed_transfer.s2_profile_name == "E0_BALANCED_ENDPOINT"
    assert timed_transfer.strum_span == 6
    assert timed_transfer.total_iteration == 0
    assert transfer["curriculum_last_gate_failures"] == (
        "timed_strum_policy_transfer")

    tempo_gate = StrikeCurriculum(config())
    tempo_gate.stage = S3_SONG_INTEGRATION
    tempo_gate.tempo_level = 3
    relaxed = base()
    relaxed["wrong_crossing_termination"] = 0.06
    relaxed["failure_termination"] = 0.06
    relaxed["strike_episode_f1"] = 0.98
    relaxed["strike_true_positive_count"] = 98.0
    relaxed["strike_false_positive_count"] = 1.0
    relaxed["strike_false_negative_count"] = 1.0
    tempo_gate.after_iteration(relaxed)
    assert "failure_rate" not in tempo_gate.last_gate_failures

    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        diagnostic = monitor.update({
            "curriculum_stage": S2_TIMED_STRUM,
            "curriculum_s2_profile_name": "T0_400MS",
            "reward": 0.0 if index < 10 else 1.0,
            "strike_strum_completion_rate": 1.0 if index < 10 else 0.0,
            "strike_worst_direction_completion_rate": (
                1.0 if index < 10 else 0.0),
            "strike_timing_p95_ms": 10.0 if index < 10 else 100.0,
            "strike_false_positive_rate": 0.0 if index < 10 else 0.2,
            "strike_timing_signed_mean_ms": (
                -20.0 if index < 10 else -80.0),
        })
    assert diagnostic["reward_alignment_warning"]
    plateau_monitor = StrikeRewardAlignmentMonitor(window=20)
    for index in range(20):
        plateau_diagnostic = plateau_monitor.update({
            "curriculum_stage": S2_TIMED_STRUM,
            "curriculum_s2_profile_name": "T1_250MS",
            "reward": 0.05,
            "strike_strum_completion_rate": 1.0,
            "strike_worst_direction_completion_rate": 1.0,
            "strike_timing_p95_ms": 170.0,
            "strike_false_positive_rate": 0.0,
            "strike_timing_signed_mean_ms": (
                -140.0 if index < 10 else -180.0),
        })
    assert plateau_diagnostic["reward_alignment_warning"]
    reset_diagnostic = monitor.update({
        "curriculum_stage": S2_TIMED_STRUM,
        "curriculum_s2_profile_name": "T1_250MS",
        "reward": 0.0,
        "strike_strum_completion_rate": 0.0,
        "strike_worst_direction_completion_rate": 0.0,
        "strike_timing_p95_ms": 0.0,
        "strike_false_positive_rate": 0.0,
        "strike_timing_signed_mean_ms": 0.0,
    })
    assert reset_diagnostic["reward_alignment_samples"] == 1

    fail_closed = StrikeCurriculum(config())
    for _ in range(3):
        fail_closed.after_iteration(base())
    missing_timing = base()
    del missing_timing["strike_timing_p95_ms"]
    fail_closed.after_iteration(missing_timing)
    assert fail_closed.stage == A3_TIMED_SINGLE
    assert fail_closed.timing_tolerance_ms == 100

    curriculum = StrikeCurriculum(config())
    assert curriculum.stage == A0_PICK_GRIP
    curriculum.after_iteration(base())
    assert curriculum.stage == A1_TIP_READY
    curriculum.after_iteration(base())
    assert curriculum.stage == A2_SINGLE_CROSSING
    curriculum.after_iteration(base())
    assert curriculum.stage == A3_TIMED_SINGLE
    for expected in (67, 50):
        curriculum.after_iteration(base())
        assert curriculum.timing_tolerance_ms == expected
    curriculum.after_iteration(base())
    assert curriculum.stage == A4_STRUM_CONTEXT_RECOVERY
    assert curriculum.strum_span == 1
    curriculum.after_iteration(base())
    assert curriculum.stage == S0_TWO_STRING_STRUM
    assert curriculum.strum_span == 2
    curriculum.after_iteration(base())
    assert curriculum.stage == S1_STRUM_SPAN
    assert curriculum.strum_span == 3
    for expected in (4, 5, 6):
        curriculum.after_iteration(base())
        assert curriculum.strum_span == expected
    curriculum.after_iteration(base())
    assert curriculum.stage == S2_TIMED_STRUM
    for expected in (400, 250, 225, 200, 175, 150, 100, 100, 67, 50):
        curriculum.after_iteration(base())
        assert curriculum.timing_tolerance_ms == expected
    curriculum.after_iteration(base())
    assert curriculum.stage == S3_SONG_INTEGRATION
    for expected in (0.25, 0.5, 0.75, 0.9, 0.95, 0.975, 1.0):
        curriculum.after_iteration(base())
        assert curriculum.tempo_lambda == expected
    curriculum.record_original_tempo_evaluation(curriculum.total_iteration, {
        "strike_f1": 1.0, "release_recall": 1.0,
        "false_positive_rate": 0.0,
        "end_to_end_recovery_completion_rate": 1.0,
        "recovery_reset_rate": 0.0,
    })
    curriculum.after_iteration(base())
    assert curriculum.complete
    state = curriculum.state()
    restored = StrikeCurriculum(config())
    restored.load_context(state)
    assert restored.state() == state
    old = dict(state)
    old["curriculum_schema_version"] = 12
    try:
        restored.load_context(old)
    except ValueError as exc:
        assert "incompatible" in str(exc)
        assert "actor-only" in str(exc)
    else:
        raise AssertionError("old Strike checkpoint must be rejected")
    assert state["curriculum_last_gate_failures"] == "none"
    assert state["curriculum_gate_evaluation_count"] > 0
    leads = [
        float(profile["approach_lead_s"])
        for profile in STRIKE["curriculum"]["s2_profiles"]]
    assert all(next_value <= value for value, next_value in zip(
        leads, leads[1:]))
    assert state["curriculum_approach_lead_s"] == leads[-1]

    pick_only = StrikeCurriculum(config(), song_has_strum=False)
    assert pick_only.active_stages == (
        A0_PICK_GRIP, A1_TIP_READY, A2_SINGLE_CROSSING,
        A3_TIMED_SINGLE, S3_SONG_INTEGRATION)
    for expected_stage in (
            A1_TIP_READY, A2_SINGLE_CROSSING, A3_TIMED_SINGLE):
        pick_only.after_iteration(base())
        assert pick_only.stage == expected_stage
    for expected_tolerance in (67, 50):
        pick_only.after_iteration(base())
        assert pick_only.timing_tolerance_ms == expected_tolerance
    pick_only.after_iteration(base())
    assert pick_only.stage == S3_SONG_INTEGRATION
    assert pick_only.strum_span == 1
    no_strum_stats = base()
    no_strum_stats.update({
        "strike_strum_event_count": 0.0,
        "strike_strum_completion_rate": 0.0,
        "strike_strum_traversal_recall": 0.0,
        "strike_strum_order_accuracy": 0.0,
        "strike_strum_direction_accuracy": 0.0,
        "strike_strum_microtiming_sample_count": 0.0,
        "strike_strum_timing_rms_ms": 999.0,
        "strike_strum_sweep_duration_mae_ms": 999.0,
    })
    pick_only.after_iteration(no_strum_stats)
    assert pick_only.last_evidence_passed
    assert "strum_events" not in pick_only.last_gate_failures
    pick_only_state = pick_only.state()
    assert pick_only_state["curriculum_route"] == "pick_only"
    restored_pick_only = StrikeCurriculum(config(), song_has_strum=False)
    restored_pick_only.load_context(pick_only_state)
    assert restored_pick_only.state() == pick_only_state
    try:
        StrikeCurriculum(config()).load_context(pick_only_state)
    except ValueError as exc:
        assert "route disagrees" in str(exc)
    else:
        raise AssertionError(
            "a pick-only checkpoint must not resume on a strum route")

    stalled_rehearsal = StrikeCurriculum(config(), song_has_strum=False)
    stalled_rehearsal.stage = S3_SONG_INTEGRATION
    stalled_rehearsal.stage_iteration = (
        stalled_rehearsal.config.max_iterations[S3_SONG_INTEGRATION] - 1)
    failed_song = dict(no_strum_stats)
    failed_song.update({
        "strike_true_positive_count": 0.0,
        "strike_false_positive_count": 0.0,
        "strike_false_negative_count": 2.0,
        "strike_release_recall": 0.0,
        "strike_episode_f1": 0.0,
    })
    stalled_rehearsal.after_iteration(failed_song)
    assert stalled_rehearsal.stalled
    assert stalled_rehearsal.tempo_lambda == 1.0
    assert stalled_rehearsal.s3_original_tempo_rehearsal_active
    assert stalled_rehearsal.last_gate_failures == (
        "s3_original_tempo_rehearsal",)
    stalled_rehearsal.record_original_tempo_evaluation(51, {
        "strike_f1": 0.80,
        "release_recall": 0.80,
        "false_positive_rate": 0.01,
        "end_to_end_recovery_completion_rate": 0.80,
        "recovery_reset_rate": 0.01,
    })
    stalled_rehearsal.record_original_tempo_evaluation(52, {
        "strike_f1": 0.70,
        "release_recall": 0.70,
        "false_positive_rate": 0.02,
        "end_to_end_recovery_completion_rate": 0.70,
        "recovery_reset_rate": 0.02,
    })
    assert not stalled_rehearsal.original_tempo_retention_passed
    assert "original_tempo_retention" in stalled_rehearsal._gate_failures(
        failed_song)

    monitor_config = replace(
        config(), promotion_windows=3,
        s3_uniform_curriculum_evidence_only=True,
        s3_original_tempo_holdout_max_age_iterations=10)
    monitor = StrikeCurriculum(monitor_config, song_has_strum=False)
    monitor.initialize_song_integration_transfer(1.0)
    monitor.complete = True
    good = {
        "strike_f1": 1.0, "release_recall": 1.0,
        "false_positive_rate": 0.0,
        "end_to_end_recovery_completion_rate": 1.0,
        "recovery_reset_rate": 0.0,
    }
    assert monitor.state()["curriculum_ever_mastered"]
    assert monitor.original_tempo_holdout_status == "missing"
    assert monitor.current_quality_passed is None
    monitor.after_iteration({"_uniform_evidence": base()})
    assert monitor.gate_evaluation_count == 1
    assert not monitor.quality_recovery_needed
    for iteration in (2, 3, 4):
        monitor.after_iteration({"_uniform_evidence": base()})
        monitor.record_original_tempo_evaluation(iteration, good)
    monitor.after_iteration({"_uniform_evidence": base()})
    assert monitor.current_quality_passed is True
    assert monitor.gate_evaluation_count == 5
    assert monitor.complete and monitor.tempo_lambda == 1.0

    mild_regression = dict(good, strike_f1=0.98)
    for iteration in (6, 7):
        monitor.after_iteration({"_uniform_evidence": base()})
        monitor.record_original_tempo_evaluation(iteration, mild_regression)
        assert monitor.original_tempo_retention_passed is True
        assert not monitor.quality_recovery_needed
    monitor.after_iteration({"_uniform_evidence": base()})
    monitor.record_original_tempo_evaluation(8, mild_regression)
    assert monitor.original_tempo_retention_drop < 0.05
    assert monitor.original_tempo_retention_passed is False
    assert monitor.current_quality_passed is False
    assert monitor.quality_recovery_needed
    assert monitor.complete
    restored_monitor = StrikeCurriculum(monitor_config, song_has_strum=False)
    restored_monitor.load_context(monitor.state())
    assert restored_monitor.state() == monitor.state()
    for iteration in (9, 10, 11):
        monitor.after_iteration({"_uniform_evidence": base()})
        monitor.record_original_tempo_evaluation(iteration, good)
    monitor.after_iteration({"_uniform_evidence": base()})
    assert monitor.current_quality_passed is True
    assert not monitor.quality_recovery_needed

    for _ in range(3):
        monitor.after_iteration({"_uniform_evidence": failed_song})
    assert monitor.quality_recovery_needed
    assert monitor.current_quality_passed is False
    assert monitor.complete and monitor.tempo_lambda == 1.0
    monitor.after_iteration({"_uniform_evidence": base()})
    assert not monitor.quality_recovery_needed
    for _ in range(6):
        monitor.after_iteration({"_uniform_evidence": base()})
    assert monitor.original_tempo_holdout_status == "stale"
    assert monitor.current_quality_passed is None
    assert not monitor.quality_recovery_needed
    monitor.record_original_tempo_evaluation(monitor.total_iteration, good)
    assert monitor.original_tempo_holdout_status == "pending"
    assert monitor.current_quality_passed is None
    try:
        monitor.record_original_tempo_evaluation(monitor.total_iteration, good)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate holdouts must not count as fresh evidence")

    unbiased = StrikeCurriculum(monitor_config, song_has_strum=False)
    unbiased.initialize_song_integration_transfer(0.0)
    assert not unbiased.stalled
    biased_bad = dict(failed_song, _uniform_evidence=base())
    unbiased.after_iteration(biased_bad)
    assert unbiased.last_evidence_passed
    biased_good = dict(base(), _uniform_evidence=failed_song)
    unbiased.after_iteration(biased_good)
    assert not unbiased.last_evidence_passed
    count_before = unbiased.gate_evaluation_count
    unbiased.after_iteration(base())
    assert unbiased.gate_evaluation_count == count_before
    assert unbiased.last_gate_failures == ("uniform_song_evidence_missing",)

    for value in (float("nan"), float("inf"), -0.1, 1.1):
        try:
            monitor.record_original_tempo_evaluation(
                monitor.total_iteration + 1, dict(good, strike_f1=value))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid holdout metrics must fail closed")
    invalid_context = dict(monitor.state())
    invalid_context["curriculum_original_tempo_holdout_iteration"] = float("inf")
    try:
        restored_monitor.load_context(invalid_context)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid holdout iteration must fail closed")
    print("PASS: A0-A4 recovery then S0-S3 strum curriculum")


if __name__ == "__main__":
    main()
