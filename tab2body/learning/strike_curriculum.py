"""Performance-gated single-pick and strum acquisition curriculum."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from typing import Mapping, Tuple

from tab2body.strike_metrics import (
    STRIKE_RAW_COUNT_METRIC_KEYS,
    pool_strike_raw_count_rates,
    pooled_rate_from_counts,
)
from tab2body.strike_contract import (
    A0_PICK_GRIP,
    A1_TIP_READY,
    A2_SINGLE_CROSSING,
    A3_TIMED_SINGLE,
    A4_STRUM_CONTEXT_RECOVERY,
    S0_TWO_STRING_STRUM,
    S1_STRUM_SPAN,
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
    STRIKE_STAGES,
    TIMED_STAGES,
    strike_curriculum_stages,
)

S2_ENDPOINT_PROFILE_NAME = "E0_BALANCED_ENDPOINT"


@dataclass(frozen=True)
class StrikeCurriculumConfig:
    min_iterations: Mapping[str, int]
    max_iterations: Mapping[str, int]
    default_approach_lead_s: float = 0.25
    promotion_windows: int = 3
    terminal_evidence_episodes: int = 1
    grip_success_gate: float = 0.90
    grip_quality_mean_gate: float = 0.92
    grip_quality_p05_gate: float = 0.85
    pinch_quality_mean_gate: float = 0.95
    free_quality_mean_gate: float = 0.85
    max_grip_bad_frame_rate: float = 0.05
    max_grip_bad_streak_frames: int = 12
    tip_ready_success_gate: float = 0.85
    release_recall_gate: float = 0.80
    false_positive_rate_by_stage: Mapping[str, float] = field(
        default_factory=lambda: {stage: 0.05 for stage in STRIKE_STAGES})
    failure_rate_by_stage: Mapping[str, float] = field(
        default_factory=lambda: {stage: 0.0 for stage in STRIKE_STAGES})
    timed_f1_by_level: Tuple[float, ...] = (0.80, 0.90, 0.95)
    timing_tolerances_ms: Tuple[int, ...] = (100, 67, 50)
    s2_profiles: Tuple[Mapping[str, object], ...] = ()
    s2_rollback_windows: int = 3
    s2_rollback_cooldown_iterations: int = 200
    s2_profile_adaptation_iterations: int = 200
    s2_rollback_timing_pass_rate: float = 0.35
    s2_rollback_completion_rate: float = 0.25
    s2_rollback_traversal_rate: float = 0.80
    s2_rollback_direction_rate: float = 0.80
    s2_rollback_false_positive_rate: float = 0.20
    s2_endpoint_recovery_windows: int = 3
    s2_endpoint_recovery_trigger_rate: float = 0.60
    s2_endpoint_focus_fraction: float = 0.70
    strum_spans: Tuple[int, ...] = (3, 4, 5, 6)
    strum_completion_gate: float = 0.90
    strum_traversal_gate: float = 0.95
    strum_order_gate: float = 0.98
    strum_direction_gate_by_stage: Mapping[str, float] = field(
        default_factory=lambda: {stage: 0.98 for stage in STRIKE_STAGES})
    recovery_completion_gate: float = 0.95
    full_recovery_completion_gate: float = 0.95
    handoff_recovery_completion_gate: float = 0.95
    recovery_reset_rate_by_stage: Mapping[str, float] = field(
        default_factory=lambda: {stage: 0.05 for stage in STRIKE_STAGES})
    blocked_crossing_rate_by_stage: Mapping[str, float] = field(
        default_factory=lambda: {stage: 0.05 for stage in STRIKE_STAGES})
    strum_timing_rms_gate_ms: float = 35.0
    strum_duration_mae_gate_ms: float = 30.0
    zone_success_gate: float = 0.95
    song_f1_gate: float = 0.98
    tempo_lambdas: Tuple[float, ...] = (
        0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.975, 1.0)
    s3_episode_event_counts: Tuple[int, ...] = (
        8, 16, 32, 42, 42, 42, 42, 42)
    s3_tempo_gates: Tuple[Mapping[str, float], ...] = ()
    s3_uniform_curriculum_evidence_only: bool = True
    s3_stalled_original_tempo_recovery: bool = True
    s3_original_tempo_retention_drop_f1: float = 0.05
    s3_original_tempo_holdout_max_age_iterations: int = 1500

    def __post_init__(self):
        for name, values in (
                ("min_iterations", self.min_iterations),
                ("max_iterations", self.max_iterations)):
            if set(values) != set(STRIKE_STAGES):
                raise ValueError(f"{name} must cover every strike stage")
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 0
                   for v in values.values()):
                raise ValueError(f"{name} must contain non-negative integers")
        if any(self.max_iterations[s] < self.min_iterations[s]
               for s in STRIKE_STAGES):
            raise ValueError("strike stage maximum cannot precede minimum")
        if self.promotion_windows < 1 or self.terminal_evidence_episodes < 1:
            raise ValueError("curriculum window sizes must be positive")
        if not isinstance(self.s3_uniform_curriculum_evidence_only, bool):
            raise TypeError("S3 uniform-evidence option must be bool")
        if not isinstance(self.s3_stalled_original_tempo_recovery, bool):
            raise TypeError("S3 stalled recovery option must be bool")
        holdout_age = self.s3_original_tempo_holdout_max_age_iterations
        if (isinstance(holdout_age, bool) or not isinstance(holdout_age, int)
                or holdout_age < 1):
            raise ValueError("S3 holdout maximum age must be a positive integer")
        if (not math.isfinite(
                float(self.s3_original_tempo_retention_drop_f1))
                or not 0.0 <= float(self.s3_original_tempo_retention_drop_f1)
                <= 1.0):
            raise ValueError(
                "S3 original-tempo retention drop must be in [0, 1]")
        if (isinstance(self.max_grip_bad_streak_frames, bool)
                or not isinstance(self.max_grip_bad_streak_frames, int)
                or self.max_grip_bad_streak_frames < 0):
            raise ValueError("max grip bad streak must be a non-negative integer")
        s2_iteration_controls = (
            self.s2_rollback_windows,
            self.s2_rollback_cooldown_iterations,
            self.s2_profile_adaptation_iterations,
            self.s2_endpoint_recovery_windows,
        )
        if (any(isinstance(value, bool) or not isinstance(value, int)
                for value in s2_iteration_controls)
                or self.s2_rollback_windows < 1
                or self.s2_endpoint_recovery_windows < 1
                or self.s2_rollback_cooldown_iterations < 0
                or self.s2_profile_adaptation_iterations < 0):
            raise ValueError(
                "S2 rollback window/cooldown/adaptation is invalid")
        for name, mapping in (
                ("false_positive_rate_by_stage",
                 self.false_positive_rate_by_stage),
                ("failure_rate_by_stage", self.failure_rate_by_stage),
                ("strum_direction_gate_by_stage",
                 self.strum_direction_gate_by_stage),
                ("recovery_reset_rate_by_stage",
                 self.recovery_reset_rate_by_stage),
                ("blocked_crossing_rate_by_stage",
                 self.blocked_crossing_rate_by_stage)):
            if set(mapping) != set(STRIKE_STAGES):
                raise ValueError(f"{name} must cover every strike stage")
            if any(not math.isfinite(float(value))
                   or not 0.0 <= float(value) <= 1.0
                   for value in mapping.values()):
                raise ValueError(f"{name} values must be finite in [0, 1]")
        gates = (
            self.grip_success_gate, self.grip_quality_mean_gate,
            self.grip_quality_p05_gate, self.pinch_quality_mean_gate,
            self.free_quality_mean_gate, self.max_grip_bad_frame_rate,
            self.tip_ready_success_gate,
            self.release_recall_gate,
            *self.timed_f1_by_level, self.strum_completion_gate,
            self.strum_traversal_gate, self.strum_order_gate,
            self.recovery_completion_gate,
            self.full_recovery_completion_gate,
            self.handoff_recovery_completion_gate,
            self.zone_success_gate,
            self.song_f1_gate)
        if any(not math.isfinite(float(v)) or not 0.0 <= float(v) <= 1.0
               for v in gates):
            raise ValueError("curriculum gates must be finite in [0, 1]")
        if (not math.isfinite(float(self.strum_timing_rms_gate_ms))
                or not math.isfinite(float(self.strum_duration_mae_gate_ms))
                or self.strum_timing_rms_gate_ms <= 0.0
                or self.strum_duration_mae_gate_ms <= 0.0):
            raise ValueError("strum microtiming gates must be positive")
        if (len(self.timed_f1_by_level) != len(self.timing_tolerances_ms)
                or any(b >= a for a, b in zip(
                    self.timing_tolerances_ms,
                    self.timing_tolerances_ms[1:]))):
            raise ValueError("timing schedule must be aligned and decreasing")
        if self.s3_tempo_gates:
            if len(self.s3_tempo_gates) != len(self.tempo_lambdas):
                raise ValueError(
                    "S3 tempo gates must align with tempo_lambdas")
            expected = {
                "f1", "wrong_termination_rate", "blocked_crossing_rate"}
            for gate in self.s3_tempo_gates:
                if not isinstance(gate, Mapping) or set(gate) != expected:
                    raise ValueError(
                        "each S3 tempo gate must contain f1, "
                        "wrong_termination_rate and blocked_crossing_rate")
                if any(not math.isfinite(float(value))
                       or not 0.0 <= float(value) <= 1.0
                       for value in gate.values()):
                    raise ValueError("S3 tempo gates must be finite in [0, 1]")
        if (len(self.s3_episode_event_counts) != len(self.tempo_lambdas)
                or any(isinstance(value, bool) or not isinstance(value, int)
                       or value < 1 for value in self.s3_episode_event_counts)
                or any(b < a for a, b in zip(
                    self.s3_episode_event_counts,
                    self.s3_episode_event_counts[1:]))):
            raise ValueError(
                "S3 episode-event counts must be positive, nondecreasing and "
                "aligned with tempo_lambdas")
        required_profile_keys = {
            "name", "tolerance_ms", "timing_pass_rate", "completion_rate",
            "timing_rms_ms", "duration_mae_ms", "timing_reward_core_ms",
            "duration_reward_core_ms", "timing_center_mean_abs_ms",
            "timing_center_tail_abs_ms", "approach_lead_s",
            "timing_early_grace_ms", "timing_early_penalty_scale_ms",
            "zone_active", "zone_success_rate",
            "worst_direction_completion_rate",
            "end_to_end_recovery_rate",
        }
        if not self.s2_profiles:
            raise ValueError("S2 timing profiles cannot be empty")
        previous_tolerance = math.inf
        previous_approach_lead = math.inf
        names = set()
        for index, profile in enumerate(self.s2_profiles):
            if not isinstance(profile, Mapping) or set(profile) != required_profile_keys:
                raise ValueError(
                    f"S2 profile {index} must have exact profile keys")
            name = profile["name"]
            if not isinstance(name, str) or not name or name in names:
                raise ValueError("S2 profile names must be unique strings")
            names.add(name)
            if name == S2_ENDPOINT_PROFILE_NAME and index != 0:
                raise ValueError("E0 balanced endpoint profile must be first")
            tolerance = float(profile["tolerance_ms"])
            positive = (
                tolerance, float(profile["timing_rms_ms"]),
                float(profile["duration_mae_ms"]),
                float(profile["timing_reward_core_ms"]),
                float(profile["duration_reward_core_ms"]),
                float(profile["timing_center_mean_abs_ms"]),
                float(profile["timing_center_tail_abs_ms"]),
                float(profile["approach_lead_s"]),
                float(profile["timing_early_penalty_scale_ms"]),
            )
            if any(not math.isfinite(value) or value <= 0.0
                   for value in positive):
                raise ValueError("S2 profile time values must be positive")
            center_mean = float(profile["timing_center_mean_abs_ms"])
            center_tail = float(profile["timing_center_tail_abs_ms"])
            if center_mean > center_tail or center_tail > tolerance:
                raise ValueError(
                    "S2 profile center gates must satisfy mean <= tail <= "
                    "tolerance")
            if tolerance > previous_tolerance:
                raise ValueError("S2 profile tolerances cannot increase")
            previous_tolerance = tolerance
            approach_lead = float(profile["approach_lead_s"])
            if approach_lead > previous_approach_lead:
                raise ValueError("S2 profile approach lead cannot increase")
            previous_approach_lead = approach_lead
            early_grace = float(profile["timing_early_grace_ms"])
            if (not math.isfinite(early_grace) or early_grace < 0.0
                    or early_grace > tolerance):
                raise ValueError(
                    "S2 profile early grace must be in [0, tolerance]")
            rates = (
                float(profile["timing_pass_rate"]),
                float(profile["completion_rate"]),
                float(profile["zone_success_rate"]),
                float(profile["worst_direction_completion_rate"]),
                float(profile["end_to_end_recovery_rate"]),
            )
            if (any(isinstance(profile[key], bool) for key in (
                    "timing_pass_rate", "completion_rate",
                    "zone_success_rate", "worst_direction_completion_rate",
                    "end_to_end_recovery_rate"))
                    or any(not math.isfinite(value)
                           or not 0.0 <= value <= 1.0 for value in rates)):
                raise ValueError("S2 profile rates must be in [0, 1]")
            if not isinstance(profile["zone_active"], bool):
                raise TypeError("S2 profile zone_active must be bool")
            if (not profile["zone_active"]
                    and float(profile["zone_success_rate"]) != 0.0):
                raise ValueError("inactive S2 zone profiles require zero gate")
        rollback_rates = (
            self.s2_rollback_timing_pass_rate,
            self.s2_rollback_completion_rate,
            self.s2_rollback_traversal_rate,
            self.s2_rollback_direction_rate,
            self.s2_rollback_false_positive_rate,
            self.s2_endpoint_recovery_trigger_rate,
            self.s2_endpoint_focus_fraction,
        )
        if (any(isinstance(value, bool) for value in rollback_rates)
                or any(not math.isfinite(float(value))
               or not 0.0 <= float(value) <= 1.0
               for value in rollback_rates)):
            raise ValueError("S2 rollback rates must be in [0, 1]")
        if not 0.5 <= float(self.s2_endpoint_focus_fraction) <= 0.70:
            raise ValueError("S2 endpoint focus fraction must be in [0.5, 0.70]")
        if self.strum_spans[0] != 3 or self.strum_spans[-1] != 6 \
                or any(b <= a for a, b in zip(
                    self.strum_spans, self.strum_spans[1:])):
            raise ValueError("strum spans must increase from 3 to 6")
        if self.tempo_lambdas[0] != 0.0 or self.tempo_lambdas[-1] != 1.0 \
                or any(b <= a for a, b in zip(
                    self.tempo_lambdas, self.tempo_lambdas[1:])):
            raise ValueError("tempo lambdas must increase from 0 to 1")
        if (not math.isfinite(float(self.default_approach_lead_s))
                or self.default_approach_lead_s <= 0.0):
            raise ValueError("default approach lead must be positive")


_ALIASES = {
    "grip": "strike_grip_success_rate",
    "grip_quality_mean": "strike_grip_quality_mean",
    "grip_quality_p05": "strike_grip_quality_p05",
    "pinch_quality_mean": "strike_grip_pinch_quality_mean",
    "free_quality_mean": "strike_grip_free_quality_mean",
    "grip_bad_frame_rate": "strike_grip_bad_frame_rate",
    "grip_bad_streak": "strike_grip_bad_streak_max_frames",
    "ready": "strike_tip_ready_success_rate",
    "recall": "strike_release_recall",
    "fp": "strike_false_positive_rate",
    "f1": "strike_episode_f1",
    "timing": "strike_timing_p95_ms",
    "timing_pass": "strike_timing_pass_rate",
    "timing_signed_mean": "strike_timing_signed_mean_ms",
    "timing_signed_p10": "strike_timing_signed_p10_ms",
    "timing_signed_p90": "strike_timing_signed_p90_ms",
    "zone": "strike_zone_success_rate",
    "strum_completion": "strike_strum_completion_rate",
    "strum_traversal": "strike_strum_traversal_recall",
    "strum_order": "strike_strum_order_accuracy",
    "strum_direction": "strike_strum_direction_accuracy",
    "strum_events": "strike_strum_event_count",
    "strum_timing_rms": "strike_strum_timing_rms_ms",
    "strum_duration_mae": "strike_strum_sweep_duration_mae_ms",
    "strum_micro_samples": "strike_strum_microtiming_sample_count",
    "recovery_completion": "strike_recovery_completion_rate",
    "recovery_events": "strike_recovery_event_count",
    "scheduled_recovery_events": "strike_scheduled_recovery_event_count",
    "scheduled_recovery_completed": (
        "strike_scheduled_recovery_completed_count"),
    "conditional_recovery_completion": (
        "strike_conditional_recovery_completion_rate"),
    "end_to_end_recovery_completion": (
        "strike_end_to_end_recovery_completion_rate"),
    "full_recovery_events": "strike_full_recovery_event_count",
    "full_recovery_completed": "strike_full_recovery_completed_count",
    "handoff_recovery_events": "strike_handoff_recovery_event_count",
    "handoff_recovery_completed": (
        "strike_handoff_recovery_completed_count"),
    "recovery_resets": "strike_recovery_reset_rate",
    "blocked_crossings": "strike_blocked_crossing_rate",
    "blocked_crossing_count": "strike_blocked_crossing_count",
    "true_positive_count": "strike_true_positive_count",
    "false_positive_count": "strike_false_positive_count",
    "false_negative_count": "strike_false_negative_count",
    "down_events": "strike_down_event_count",
    "down_completed": "strike_down_completed_count",
    "up_events": "strike_up_event_count",
    "up_completed": "strike_up_completed_count",
    "worst_direction_completion": (
        "strike_worst_direction_completion_rate"),
    "failure": "failure_termination",
    "wrong_failure": "wrong_crossing_termination",
    "safety_failure": "irrecoverable_safety_failure",
}

_MINIMUM_EVIDENCE = frozenset((
    "grip_quality_p05", "pinch_quality_mean", "free_quality_mean",
))
_MAXIMUM_EVIDENCE = frozenset((
    "timing", "grip_bad_frame_rate", "grip_bad_streak",
))
_OPTIONAL_RAW_EVIDENCE = frozenset((
    "scheduled_recovery_events",
    "down_events", "down_completed", "up_events", "up_completed",
))
_DERIVED_EVIDENCE = frozenset((
    "conditional_recovery_completion",
    "end_to_end_recovery_completion",
    "worst_direction_completion",
))
_RAW_COUNT_EVIDENCE = frozenset(
    name for name, key in _ALIASES.items()
    if key in STRIKE_RAW_COUNT_METRIC_KEYS)


def _value(stats, name, default=None):
    value = stats.get(_ALIASES[name], default)
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


class StrikeCurriculum:
    STAGES = STRIKE_STAGES
    FINAL_STAGE = S3_SONG_INTEGRATION
    SCHEMA_VERSION = 16

    def __init__(
            self, config: StrikeCurriculumConfig, *, song_has_strum=True):
        if not isinstance(song_has_strum, bool):
            raise TypeError("song_has_strum must be bool")
        self.config = config
        self.song_has_strum = song_has_strum
        self.active_stages = strike_curriculum_stages(song_has_strum)
        self.stage = A0_PICK_GRIP
        self.stage_iteration = 0
        self.total_iteration = 0
        self.stalled = False
        self.promotion_streak = 0
        self.timing_level = 0
        self.s2_profile_index = 0
        self.rollback_streak = 0
        self.rollback_count = 0
        self.rollback_cooldown = 0
        self.s2_adaptation_remaining = 0
        self.s2_endpoint_failure_streak = 0
        self.s2_endpoint_recovery_active = False
        self.s2_focus_direction = "balanced"
        self.span_level = 0
        self.tempo_level = 0
        self.complete = False
        self._reset_original_tempo_holdout()
        self._evidence_episodes = 0
        self._evidence_sums = {name: 0.0 for name in _ALIASES}
        self._evidence_minimum = {
            name: 1.0 for name in _MINIMUM_EVIDENCE}
        self._evidence_maximum = {
            name: 0.0 for name in _MAXIMUM_EVIDENCE}
        self._evidence_presence = {
            name: 0 for name in _OPTIONAL_RAW_EVIDENCE}
        self.last_evidence_passed = False
        self.last_gate_failures = ("not_evaluated",)
        self.gate_evaluation_count = 0

    def _reset_s2_endpoint_recovery(self):
        self.s2_endpoint_failure_streak = 0
        self.s2_endpoint_recovery_active = False
        self.s2_focus_direction = "balanced"

    def _reset_original_tempo_holdout(self):
        self.original_tempo_holdout_f1 = None
        self.original_tempo_holdout_recall = None
        self.original_tempo_holdout_false_positive = None
        self.original_tempo_holdout_end_to_end_recovery = None
        self.original_tempo_holdout_reset_rate = None
        self.original_tempo_best_f1 = None
        self.original_tempo_best_iteration = None
        self.original_tempo_retention_drop = 0.0
        self.original_tempo_retention_passed = None
        self.original_tempo_holdout_iteration = None
        self.original_tempo_holdout_latest_passed = None
        self.original_tempo_holdout_pass_streak = 0
        self.original_tempo_holdout_fail_streak = 0
        self.original_tempo_case_quality = {}
        self.quality_evidence_iteration = None
        self.quality_evidence_pass_streak = 0
        self.quality_evidence_fail_streak = 0

    @property
    def original_tempo_holdout_status(self):
        if self.original_tempo_holdout_iteration is None:
            return "missing"
        if (self.total_iteration - self.original_tempo_holdout_iteration
                > self.config.s3_original_tempo_holdout_max_age_iterations):
            return "stale"
        if self.original_tempo_retention_passed is None:
            return "pending"
        return "passed" if self.original_tempo_retention_passed else "failed"

    @property
    def current_quality_passed(self):
        if not self.complete:
            return None
        if (self.quality_evidence_iteration is None
                or self.total_iteration - self.quality_evidence_iteration
                > self.config.s3_original_tempo_holdout_max_age_iterations
                or self.original_tempo_holdout_status
                in ("missing", "stale", "pending")):
            return None
        return bool(self.last_evidence_passed
                    and self.original_tempo_retention_passed)

    @property
    def quality_recovery_needed(self):
        recent_training_failure = (
            self.quality_evidence_iteration is not None
            and self.total_iteration - self.quality_evidence_iteration
            <= self.config.s3_original_tempo_holdout_max_age_iterations
            and self.quality_evidence_fail_streak >= self.config.promotion_windows)
        return bool(self.complete and (
            recent_training_failure
            or self.original_tempo_holdout_status == "failed"))

    @property
    def timing_tolerance_ms(self):
        if self.stage == S2_TIMED_STRUM:
            return int(self.s2_profile["tolerance_ms"])
        if self.stage == S3_SONG_INTEGRATION:
            return int(self.config.s2_profiles[-1]["tolerance_ms"])
        return int(self.config.timing_tolerances_ms[self.timing_level])

    @property
    def s2_profile(self):
        return self.config.s2_profiles[self.s2_profile_index]

    @property
    def s2_profile_name(self):
        return str(self.s2_profile["name"])

    @property
    def s2_endpoint_profile_active(self):
        return (
            self.stage == S2_TIMED_STRUM
            and self.s2_profile_index == 0
            and self.s2_profile_name == S2_ENDPOINT_PROFILE_NAME)

    @property
    def s2_focus_fraction(self):
        if not self.s2_endpoint_recovery_active:
            return 0.5
        return min(0.70, float(self.config.s2_endpoint_focus_fraction))

    @property
    def s2_gate_evidence_mode(self):
        return (
            "uniform_balanced"
            if self.s2_endpoint_recovery_active else "training_balanced")

    @property
    def zone_active(self):
        if self.stage == S2_TIMED_STRUM:
            return bool(self.s2_profile["zone_active"])
        return self.stage in (A3_TIMED_SINGLE, S3_SONG_INTEGRATION)

    @property
    def timing_reward_core_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["timing_reward_core_ms"])
        return 20.0

    @property
    def duration_reward_core_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["duration_reward_core_ms"])
        return 15.0

    @property
    def timing_center_mean_abs_gate_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["timing_center_mean_abs_ms"])
        return None

    @property
    def timing_center_tail_abs_gate_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["timing_center_tail_abs_ms"])
        return None

    @property
    def approach_lead_s(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["approach_lead_s"])
        return float(self.config.default_approach_lead_s)

    @property
    def timing_early_grace_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["timing_early_grace_ms"])
        if self.stage == A3_TIMED_SINGLE:
            return 0.2 * float(self.timing_tolerance_ms)
        return 0.0

    @property
    def timing_early_penalty_scale_ms(self):
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            profile = (self.s2_profile if self.stage == S2_TIMED_STRUM
                       else self.config.s2_profiles[-1])
            return float(profile["timing_early_penalty_scale_ms"])
        if self.stage == A3_TIMED_SINGLE:
            return max(30.0, 0.6 * float(self.timing_tolerance_ms))
        return 1.0

    @property
    def timing_applicable(self):
        return self.stage in TIMED_STAGES

    @property
    def strum_span(self):
        if self.stage == A4_STRUM_CONTEXT_RECOVERY:
            return 1
        if self.stage == S0_TWO_STRING_STRUM:
            return 2
        if self.stage == S1_STRUM_SPAN:
            return int(self.config.strum_spans[self.span_level])
        if self.stage == S3_SONG_INTEGRATION and not self.song_has_strum:
            return 1
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            return 6
        return 1

    @property
    def tempo_lambda(self):
        if self.stage != S3_SONG_INTEGRATION:
            return 1.0
        return float(self.config.tempo_lambdas[self.tempo_level])

    @property
    def original_tempo_reached(self):
        return self.stage == S3_SONG_INTEGRATION and self.tempo_lambda == 1.0

    @property
    def s3_original_tempo_rehearsal_active(self):
        return bool(
            self.stage == S3_SONG_INTEGRATION
            and self.stalled
            and self.tempo_level == len(self.config.tempo_lambdas) - 1
            and self.config.s3_stalled_original_tempo_recovery)

    @property
    def song_events_per_episode(self):
        return int(self.config.s3_episode_event_counts[self.tempo_level])

    @property
    def current_strike_f1_gate(self):
        if self.stage == A3_TIMED_SINGLE:
            return float(self.config.timed_f1_by_level[self.timing_level])
        if self.stage == S3_SONG_INTEGRATION:
            return float(self.current_s3_tempo_gate["f1"])
        return float(self.config.song_f1_gate)

    @property
    def current_s3_tempo_gate(self):
        if self.config.s3_tempo_gates:
            return self.config.s3_tempo_gates[self.tempo_level]
        return {
            "f1": float(self.config.song_f1_gate),
            "wrong_termination_rate": float(
                self.config.failure_rate_by_stage[S3_SONG_INTEGRATION]),
            "blocked_crossing_rate": float(
                self.config.blocked_crossing_rate_by_stage[
                    S3_SONG_INTEGRATION]),
        }

    @property
    def current_failure_rate_gate(self):
        if self.stage == S3_SONG_INTEGRATION:
            return float(
                self.current_s3_tempo_gate["wrong_termination_rate"])
        return float(self.config.failure_rate_by_stage[self.stage])

    @property
    def current_blocked_crossing_rate_gate(self):
        if self.stage == S3_SONG_INTEGRATION:
            return float(
                self.current_s3_tempo_gate["blocked_crossing_rate"])
        return float(self.config.blocked_crossing_rate_by_stage[self.stage])

    def state(self):
        return {
            "curriculum_schema_version": self.SCHEMA_VERSION,
            "curriculum_route": (
                "pick_and_strum" if self.song_has_strum else "pick_only"),
            "curriculum_song_has_strum": self.song_has_strum,
            "curriculum_active_stages": list(self.active_stages),
            "curriculum_active_stage_index": self.active_stages.index(
                self.stage),
            "curriculum_stage": self.stage,
            "curriculum_stage_index": self.STAGES.index(self.stage),
            "curriculum_stage_iteration": self.stage_iteration,
            "curriculum_total_iteration": self.total_iteration,
            "curriculum_stalled": self.stalled,
            "curriculum_promotion_streak": self.promotion_streak,
            "curriculum_timing_level": self.timing_level,
            "curriculum_timing_tolerance_ms": self.timing_tolerance_ms,
            "curriculum_timing_applicable": self.timing_applicable,
            "curriculum_timing_streak": 0,
            "curriculum_s2_profile_index": self.s2_profile_index,
            "curriculum_s2_profile_name": self.s2_profile_name,
            "curriculum_s2_endpoint_profile_active": (
                self.s2_endpoint_profile_active),
            "curriculum_s2_zone_active": self.zone_active,
            "curriculum_timing_reward_core_ms": self.timing_reward_core_ms,
            "curriculum_duration_reward_core_ms": self.duration_reward_core_ms,
            "curriculum_approach_lead_s": self.approach_lead_s,
            "curriculum_timing_early_grace_ms": self.timing_early_grace_ms,
            "curriculum_timing_early_penalty_scale_ms": (
                self.timing_early_penalty_scale_ms),
            "curriculum_s2_rollback_streak": self.rollback_streak,
            "curriculum_s2_rollback_count": self.rollback_count,
            "curriculum_s2_rollback_cooldown": self.rollback_cooldown,
            "curriculum_s2_adaptation_remaining": (
                self.s2_adaptation_remaining),
            "curriculum_s2_endpoint_failure_streak": (
                self.s2_endpoint_failure_streak),
            "curriculum_s2_endpoint_recovery_active": (
                self.s2_endpoint_recovery_active),
            "curriculum_s2_focus_direction": self.s2_focus_direction,
            "curriculum_s2_focus_fraction": self.s2_focus_fraction,
            "curriculum_s2_gate_evidence_mode": (
                self.s2_gate_evidence_mode),
            "curriculum_s2_endpoint_recovery_windows": int(
                self.config.s2_endpoint_recovery_windows),
            "curriculum_s2_endpoint_recovery_trigger_rate": float(
                self.config.s2_endpoint_recovery_trigger_rate),
            "curriculum_timing_center_mean_abs_gate_ms": (
                self.timing_center_mean_abs_gate_ms),
            "curriculum_timing_center_tail_abs_gate_ms": (
                self.timing_center_tail_abs_gate_ms),
            "curriculum_span_level": self.span_level,
            "curriculum_strum_span": self.strum_span,
            "curriculum_tempo_level": self.tempo_level,
            "curriculum_tempo_lambda": self.tempo_lambda,
            "curriculum_song_events_per_episode": (
                self.song_events_per_episode),
            "curriculum_original_tempo_reached": self.original_tempo_reached,
            "curriculum_s3_original_tempo_rehearsal_active": (
                self.s3_original_tempo_rehearsal_active),
            "curriculum_original_tempo_holdout_f1": (
                self.original_tempo_holdout_f1),
            "curriculum_original_tempo_holdout_recall": (
                self.original_tempo_holdout_recall),
            "curriculum_original_tempo_holdout_false_positive": (
                self.original_tempo_holdout_false_positive),
            "curriculum_original_tempo_holdout_end_to_end_recovery": (
                self.original_tempo_holdout_end_to_end_recovery),
            "curriculum_original_tempo_holdout_reset_rate": (
                self.original_tempo_holdout_reset_rate),
            "curriculum_original_tempo_best_f1": self.original_tempo_best_f1,
            "curriculum_original_tempo_best_iteration": (
                self.original_tempo_best_iteration),
            "curriculum_original_tempo_retention_drop": (
                self.original_tempo_retention_drop),
            "curriculum_original_tempo_retention_passed": (
                self.original_tempo_retention_passed),
            "curriculum_original_tempo_holdout_iteration": (
                self.original_tempo_holdout_iteration),
            "curriculum_original_tempo_holdout_status": (
                self.original_tempo_holdout_status),
            "curriculum_original_tempo_holdout_latest_passed": (
                self.original_tempo_holdout_latest_passed),
            "curriculum_original_tempo_holdout_pass_streak": (
                self.original_tempo_holdout_pass_streak),
            "curriculum_original_tempo_holdout_fail_streak": (
                self.original_tempo_holdout_fail_streak),
            "curriculum_original_tempo_holdout_max_age_iterations": (
                self.config.s3_original_tempo_holdout_max_age_iterations),
            "curriculum_original_tempo_absolute_f1_gate": float(
                self.config.s3_tempo_gates[-1]["f1"]
                if self.config.s3_tempo_gates else self.config.song_f1_gate),
            "curriculum_original_tempo_retention_drop_gate": float(
                self.config.s3_original_tempo_retention_drop_f1),
            "curriculum_grip_quality_mean_gate": float(
                self.config.grip_quality_mean_gate),
            "curriculum_grip_quality_p05_gate": float(
                self.config.grip_quality_p05_gate),
            "curriculum_pinch_quality_mean_gate": float(
                self.config.pinch_quality_mean_gate),
            "curriculum_free_quality_mean_gate": float(
                self.config.free_quality_mean_gate),
            "curriculum_max_grip_bad_frame_rate": float(
                self.config.max_grip_bad_frame_rate),
            "curriculum_max_grip_bad_streak_frames": int(
                self.config.max_grip_bad_streak_frames),
            "curriculum_strike_f1_gate": self.current_strike_f1_gate,
            "curriculum_false_positive_rate_gate": float(
                self.config.false_positive_rate_by_stage[self.stage]),
            "curriculum_failure_rate_gate": float(
                self.current_failure_rate_gate),
            "curriculum_strum_direction_accuracy_gate": float(
                self.config.strum_direction_gate_by_stage[self.stage]),
            "curriculum_worst_direction_completion_rate_gate": float(
                self.s2_profile["worst_direction_completion_rate"]),
            "curriculum_recovery_completion_rate_gate": float(
                self.config.recovery_completion_gate),
            "curriculum_end_to_end_recovery_completion_rate_gate": float(
                self.s2_profile["end_to_end_recovery_rate"]),
            "curriculum_full_recovery_completion_rate_gate": float(
                self.config.full_recovery_completion_gate),
            "curriculum_handoff_recovery_completion_rate_gate": float(
                self.config.handoff_recovery_completion_gate),
            "curriculum_recovery_reset_rate_gate": float(
                self.config.recovery_reset_rate_by_stage[self.stage]),
            "curriculum_blocked_crossing_rate_gate": float(
                self.current_blocked_crossing_rate_gate),
            "curriculum_last_evidence_passed": self.last_evidence_passed,
            "curriculum_last_gate_failures": ",".join(
                self.last_gate_failures),
            "curriculum_gate_evaluation_count": self.gate_evaluation_count,
            "curriculum_complete": self.complete,
            "curriculum_ever_mastered": self.complete,
            "curriculum_current_quality_passed": self.current_quality_passed,
            "curriculum_original_tempo_case_quality": dict(
                self.original_tempo_case_quality),
            "curriculum_quality_recovery_needed": self.quality_recovery_needed,
            "curriculum_quality_evidence_iteration": (
                self.quality_evidence_iteration),
            "curriculum_quality_evidence_pass_streak": (
                self.quality_evidence_pass_streak),
            "curriculum_quality_evidence_fail_streak": (
                self.quality_evidence_fail_streak),
            "curriculum_evidence_episodes": self._evidence_episodes,
            "curriculum_evidence_sums": dict(self._evidence_sums),
            "curriculum_evidence_minimum": dict(self._evidence_minimum),
            "curriculum_evidence_maximum": dict(self._evidence_maximum),
            "curriculum_evidence_presence": dict(self._evidence_presence),
        }

    def load_context(self, context):
        if (int(context.get("curriculum_schema_version", 0))
                != self.SCHEMA_VERSION):
            raise ValueError(
                "old strike checkpoints are incompatible with "
                "song-aware strike curriculum v16; use actor-only policy "
                "transfer for older checkpoints")
        saved_song_has_strum = context.get("curriculum_song_has_strum")
        if not isinstance(saved_song_has_strum, bool):
            raise ValueError(
                "checkpoint has no valid song-aware curriculum route")
        if saved_song_has_strum != self.song_has_strum:
            raise ValueError(
                "checkpoint curriculum route disagrees with the song plan")
        saved_active_stages = context.get("curriculum_active_stages")
        if (not isinstance(saved_active_stages, (tuple, list))
                or tuple(saved_active_stages) != self.active_stages):
            raise ValueError(
                "checkpoint active Strike stages disagree with the song plan")
        stage = context.get("curriculum_stage")
        if stage not in self.active_stages:
            raise ValueError(
                "checkpoint stage is not active for this song curriculum")
        self.stage = stage
        for attr, key in (
                ("stage_iteration", "curriculum_stage_iteration"),
                ("total_iteration", "curriculum_total_iteration"),
                ("promotion_streak", "curriculum_promotion_streak"),
                ("timing_level", "curriculum_timing_level"),
                ("s2_profile_index", "curriculum_s2_profile_index"),
                ("rollback_streak", "curriculum_s2_rollback_streak"),
                ("rollback_count", "curriculum_s2_rollback_count"),
                ("rollback_cooldown", "curriculum_s2_rollback_cooldown"),
                ("s2_adaptation_remaining",
                 "curriculum_s2_adaptation_remaining"),
                ("s2_endpoint_failure_streak",
                 "curriculum_s2_endpoint_failure_streak"),
                ("span_level", "curriculum_span_level"),
                ("tempo_level", "curriculum_tempo_level")):
            value = int(context.get(key, 0))
            if value < 0:
                raise ValueError(f"{key} must be non-negative")
            setattr(self, attr, value)
        self.s2_endpoint_recovery_active = bool(context.get(
            "curriculum_s2_endpoint_recovery_active", False))
        focus_direction = context.get(
            "curriculum_s2_focus_direction", "balanced")
        if focus_direction not in ("balanced", "down", "up"):
            raise ValueError("checkpoint contains an invalid S2 focus direction")
        self.s2_focus_direction = focus_direction
        if (not self.s2_endpoint_recovery_active
                and self.s2_focus_direction != "balanced"):
            raise ValueError("inactive endpoint recovery must be balanced")
        raw_focus_fraction = context.get(
            "curriculum_s2_focus_fraction", self.s2_focus_fraction)
        if isinstance(raw_focus_fraction, bool):
            raise ValueError("checkpoint S2 focus fraction is invalid")
        try:
            saved_focus_fraction = float(raw_focus_fraction)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "checkpoint S2 focus fraction is invalid") from exc
        if (not math.isfinite(saved_focus_fraction)
                or abs(saved_focus_fraction - self.s2_focus_fraction) > 1e-9):
            raise ValueError("checkpoint S2 focus fraction disagrees with config")
        self.stalled = bool(context.get("curriculum_stalled", False))
        self.complete = bool(context.get("curriculum_complete", False))
        for attr, key in (
                ("original_tempo_holdout_f1",
                 "curriculum_original_tempo_holdout_f1"),
                ("original_tempo_holdout_recall",
                 "curriculum_original_tempo_holdout_recall"),
                ("original_tempo_holdout_false_positive",
                 "curriculum_original_tempo_holdout_false_positive"),
                ("original_tempo_holdout_end_to_end_recovery",
                 "curriculum_original_tempo_holdout_end_to_end_recovery"),
                ("original_tempo_holdout_reset_rate",
                 "curriculum_original_tempo_holdout_reset_rate"),
                ("original_tempo_best_f1",
                 "curriculum_original_tempo_best_f1"),
                ("original_tempo_retention_drop",
                 "curriculum_original_tempo_retention_drop")):
            value = context.get(key)
            if value is not None:
                value = float(value)
                if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                    raise ValueError(f"{key} must be finite in [0, 1]")
            setattr(self, attr, value)
        for attr in ("original_tempo_retention_passed",
                     "original_tempo_holdout_latest_passed"):
            value = context.get("curriculum_" + attr)
            if value is not None and not isinstance(value, bool):
                raise ValueError(f"{attr} must be bool or null")
            setattr(self, attr, value)
        for attr in ("original_tempo_best_iteration",
                     "original_tempo_holdout_iteration",
                     "quality_evidence_iteration",
                     "original_tempo_holdout_pass_streak",
                     "original_tempo_holdout_fail_streak",
                     "quality_evidence_pass_streak",
                     "quality_evidence_fail_streak"):
            value = context.get("curriculum_" + attr,
                                0 if attr.endswith("streak") else None)
            if value is not None and (
                    isinstance(value, bool) or not isinstance(value, int)
                    or value < 0):
                raise ValueError(f"{attr} must be a non-negative integer")
            setattr(self, attr, value)
        case_quality = context.get("curriculum_original_tempo_case_quality", {})
        if not isinstance(case_quality, Mapping):
            raise ValueError("original-tempo case quality must be a mapping")
        if case_quality:
            self._validate_case_quality(case_quality)
        self.original_tempo_case_quality = dict(case_quality)
        self.last_evidence_passed = bool(
            context.get("curriculum_last_evidence_passed", False))
        raw_failures = context.get(
            "curriculum_last_gate_failures", "not_evaluated")
        if not isinstance(raw_failures, str):
            raise ValueError("curriculum gate failures must be a string")
        self.last_gate_failures = tuple(
            value for value in raw_failures.split(",") if value)
        self.gate_evaluation_count = int(
            context.get("curriculum_gate_evaluation_count", 0))
        if self.gate_evaluation_count < 0:
            raise ValueError("curriculum gate evaluation count must be non-negative")
        self._evidence_episodes = int(
            context.get("curriculum_evidence_episodes", 0))
        saved_sums = context.get("curriculum_evidence_sums", {})
        self._evidence_sums = {
            name: float(saved_sums.get(name, 0.0)) for name in _ALIASES}
        saved_minimum = context.get("curriculum_evidence_minimum", {})
        saved_maximum = context.get("curriculum_evidence_maximum", {})
        self._evidence_minimum = {
            name: float(saved_minimum.get(name, 1.0))
            for name in _MINIMUM_EVIDENCE}
        self._evidence_maximum = {
            name: float(saved_maximum.get(name, 0.0))
            for name in _MAXIMUM_EVIDENCE}
        saved_presence = context.get("curriculum_evidence_presence", {})
        self._evidence_presence = {
            name: int(saved_presence.get(name, 0))
            for name in _OPTIONAL_RAW_EVIDENCE}
        if any(value < 0 or value > self._evidence_episodes
               for value in self._evidence_presence.values()):
            raise ValueError("checkpoint raw evidence presence is invalid")
        if self.timing_level >= len(self.config.timing_tolerances_ms) \
                or self.s2_profile_index >= len(self.config.s2_profiles) \
                or self.span_level >= len(self.config.strum_spans) \
                or self.tempo_level >= len(self.config.tempo_lambdas):
            raise ValueError("checkpoint curriculum level is out of range")
        if (self.s2_endpoint_recovery_active
                and (self.stage != S2_TIMED_STRUM
                     or self.s2_profile_index != 0
                     or self.s2_focus_direction == "balanced")):
            raise ValueError(
                "endpoint recovery checkpoint state is inconsistent")
        return self.state()

    def record_original_tempo_evaluation(self, iteration, metrics,
                                         case_summary=None, case_protocol=None):
        """Record a diagnostic original-tempo holdout for retention gating."""
        if self.stage != S3_SONG_INTEGRATION:
            return self.state()
        if not isinstance(metrics, Mapping):
            raise TypeError("original-tempo metrics must be a mapping")
        if (isinstance(iteration, bool) or not isinstance(iteration, int)
                or iteration < 0):
            raise ValueError("holdout iteration must be a non-negative integer")
        if (self.original_tempo_holdout_iteration is not None
                and iteration <= self.original_tempo_holdout_iteration):
            raise ValueError("holdout iterations must increase")
        names = {
            "f1": "strike_f1",
            "recall": "release_recall",
            "false_positive": "false_positive_rate",
            "end_to_end_recovery": "end_to_end_recovery_completion_rate",
            "reset_rate": "recovery_reset_rate",
        }
        values = {}
        for name, key in names.items():
            value = metrics.get(key)
            if value is None:
                raise ValueError(
                    f"original-tempo evaluation is missing {key}")
            value = float(value)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"original-tempo evaluation {key} must be in [0, 1]")
            values[name] = value
        self._record_case_quality(case_summary, case_protocol)
        self.original_tempo_holdout_f1 = values["f1"]
        self.original_tempo_holdout_recall = values["recall"]
        self.original_tempo_holdout_false_positive = values["false_positive"]
        self.original_tempo_holdout_end_to_end_recovery = (
            values["end_to_end_recovery"])
        self.original_tempo_holdout_reset_rate = values["reset_rate"]
        if (self.original_tempo_best_f1 is None
                or values["f1"] > self.original_tempo_best_f1):
            self.original_tempo_best_f1 = values["f1"]
            self.original_tempo_best_iteration = int(iteration)
        self.original_tempo_retention_drop = max(
            0.0, float(self.original_tempo_best_f1) - values["f1"])
        if self.original_tempo_holdout_status in ("missing", "stale"):
            self.original_tempo_holdout_pass_streak = 0
            self.original_tempo_holdout_fail_streak = 0
            self.original_tempo_retention_passed = None
        self.original_tempo_holdout_iteration = iteration
        absolute_f1_gate = float(
            self.config.s3_tempo_gates[-1]["f1"]
            if self.config.s3_tempo_gates else self.config.song_f1_gate)
        passed = (
            values["f1"] >= absolute_f1_gate
            and
            self.original_tempo_retention_drop
            <= float(self.config.s3_original_tempo_retention_drop_f1))
        self.original_tempo_holdout_latest_passed = passed
        self.original_tempo_holdout_pass_streak = (
            self.original_tempo_holdout_pass_streak + 1 if passed else 0)
        self.original_tempo_holdout_fail_streak = (
            0 if passed else self.original_tempo_holdout_fail_streak + 1)
        if self.original_tempo_holdout_pass_streak >= self.config.promotion_windows:
            self.original_tempo_retention_passed = True
        elif self.original_tempo_holdout_fail_streak >= self.config.promotion_windows:
            self.original_tempo_retention_passed = False
        return self.state()

    def _validate_case_quality(self, quality):
        protocol = quality.get("protocol")
        if not isinstance(protocol, Mapping) or not protocol:
            raise ValueError("case quality protocol must be a non-empty mapping")
        try:
            json.dumps(dict(protocol), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("case quality protocol must be finite JSON data") from exc
        for name in ("same_protocol", "repeated_below_best_warning"):
            if not isinstance(quality.get(name), bool):
                raise ValueError(f"case quality {name} must be bool")
        warning = False
        for name in ("clean_full_song_rate", "f1_p10"):
            values = []
            for key in (name, "best_" + name, name + "_drop"):
                value = quality.get(key)
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not 0.0 <= value <= 1.0):
                    raise ValueError(f"case quality {key} must be finite in [0, 1]")
                values.append(value)
            current, best, drop = values
            if best < current or not math.isclose(drop, best - current, abs_tol=1e-12):
                raise ValueError("case quality best/current/drop are inconsistent")
            streak = quality.get(name + "_below_best_streak")
            if (isinstance(streak, bool) or not isinstance(streak, int) or streak < 0
                    or (drop <= 1e-12 and streak != 0)):
                raise ValueError("case quality below-best streak is invalid")
            warning |= streak >= self.config.promotion_windows
        if warning != quality["repeated_below_best_warning"]:
            raise ValueError("case quality warning is inconsistent with streaks")

    def _record_case_quality(self, summary, protocol):
        if summary is None or protocol is None:
            self.original_tempo_case_quality = {}
            return
        if not isinstance(summary, Mapping) or not isinstance(protocol, Mapping):
            raise ValueError("case summary and protocol must be mappings")
        values = {}
        for name in ("clean_full_song_rate", "f1_p10"):
            value = float(summary[name])
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"case quality {name} must be in [0, 1]")
            values[name] = value
        previous = self.original_tempo_case_quality
        same = previous.get("protocol") == dict(protocol)
        result = {"protocol": dict(protocol), "same_protocol": same}
        for name, value in values.items():
            best = max(value, float(previous["best_" + name])) if same else value
            drop = max(0.0, best - value)
            streak = (int(previous.get(name + "_below_best_streak", 0)) + 1
                      if same and drop > 1e-12 else 0)
            result[name] = value
            result["best_" + name] = best
            result[name + "_drop"] = drop
            result[name + "_below_best_streak"] = streak
        result["repeated_below_best_warning"] = any(
            result[name + "_below_best_streak"] >= self.config.promotion_windows
            for name in values)
        self._validate_case_quality(result)
        self.original_tempo_case_quality = result

    def _reset_evidence(self):
        self._evidence_episodes = 0
        self._evidence_sums = {name: 0.0 for name in _ALIASES}
        self._evidence_minimum = {
            name: 1.0 for name in _MINIMUM_EVIDENCE}
        self._evidence_maximum = {
            name: 0.0 for name in _MAXIMUM_EVIDENCE}
        self._evidence_presence = {
            name: 0 for name in _OPTIONAL_RAW_EVIDENCE}

    def _consume_evidence(self, stats):
        uniform_only = (
            (self.stage == S2_TIMED_STRUM
             and self.s2_profile_index == 0
             and self.s2_endpoint_recovery_active)
            or (self.stage == S3_SONG_INTEGRATION
                and self.config.s3_uniform_curriculum_evidence_only))
        if uniform_only:
            stats = stats.get("_uniform_evidence", {})
            if not isinstance(stats, Mapping) or not stats:
                self._reset_evidence()
                return None
        raw_count = stats.get("episodes", 0)
        if isinstance(raw_count, bool):
            return None
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            return None
        if count < 1 or float(raw_count) != count:
            return None
        values = {name: _value(stats, name) for name in _ALIASES}
        required = set(_ALIASES) - _OPTIONAL_RAW_EVIDENCE - _DERIVED_EVIDENCE
        if any(values[name] is None for name in required):
            self._reset_evidence()
            return None
        self._evidence_episodes += count
        for name, value in values.items():
            if name in _DERIVED_EVIDENCE or value is None:
                continue
            if name in _OPTIONAL_RAW_EVIDENCE:
                self._evidence_presence[name] += count
            if name in _MINIMUM_EVIDENCE:
                self._evidence_minimum[name] = min(
                    self._evidence_minimum[name], value)
            elif name in _MAXIMUM_EVIDENCE:
                self._evidence_maximum[name] = max(
                    self._evidence_maximum[name], value)
            else:
                self._evidence_sums[name] += value * count
        if self._evidence_episodes < self.config.terminal_evidence_episodes:
            return None
        pooled = {"episodes": self._evidence_episodes}
        for name, key in _ALIASES.items():
            if name in _DERIVED_EVIDENCE:
                continue
            if (name in _OPTIONAL_RAW_EVIDENCE
                    and self._evidence_presence[name]
                    != self._evidence_episodes):
                continue
            if name in _MINIMUM_EVIDENCE:
                pooled[key] = self._evidence_minimum[name]
            elif name in _MAXIMUM_EVIDENCE:
                pooled[key] = self._evidence_maximum[name]
            elif name in _RAW_COUNT_EVIDENCE:
                pooled[key] = self._evidence_sums[name]
            else:
                pooled[key] = (
                    self._evidence_sums[name] / self._evidence_episodes)
        tp = self._evidence_sums["true_positive_count"]
        fp = self._evidence_sums["false_positive_count"]
        fn = self._evidence_sums["false_negative_count"]
        precision = tp / max(tp + fp, 1e-8)
        recall = tp / max(tp + fn, 1e-8)
        pooled[_ALIASES["recall"]] = recall
        pooled[_ALIASES["fp"]] = fp / max(tp + fp + fn, 1.0)
        pooled[_ALIASES["f1"]] = (
            2.0 * precision * recall / max(precision + recall, 1e-8))
        if "strike_scheduled_recovery_event_count" not in pooled:
            pooled["strike_scheduled_recovery_event_count"] = tp + fn
        directional_raw_available = all(key in pooled for key in (
            "strike_down_event_count", "strike_down_completed_count",
            "strike_up_event_count", "strike_up_completed_count",
        ))
        if (self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION)
                or directional_raw_available):
            pool_strike_raw_count_rates(pooled)
        recovery_events = self._evidence_sums["recovery_events"]
        blocked_crossings = self._evidence_sums["blocked_crossing_count"]
        pooled[_ALIASES["blocked_crossings"]] = (
            blocked_crossings / max(recovery_events, 1.0))
        self._reset_evidence()
        return pooled

    def _gate_failures(self, stats):
        failures = []
        safety_failure_rate = _value(stats, "safety_failure")
        if safety_failure_rate is None or safety_failure_rate > 0.0:
            failures.append("safety_failure_rate")
        failure_name = (
            "wrong_failure"
            if self.stage == S3_SONG_INTEGRATION else "failure")
        failure_rate = _value(stats, failure_name)
        if (failure_rate is None
                or failure_rate > self.current_failure_rate_gate):
            failures.append("failure_rate")
        grip = _value(stats, "grip")
        if grip is None or grip < self.config.grip_success_gate:
            failures.append("grip")
        grip_quality_mean = _value(stats, "grip_quality_mean")
        if (grip_quality_mean is None
                or grip_quality_mean < self.config.grip_quality_mean_gate):
            failures.append("grip_quality_mean")
        grip_quality_p05 = _value(stats, "grip_quality_p05")
        if (grip_quality_p05 is None
                or grip_quality_p05 < self.config.grip_quality_p05_gate):
            failures.append("grip_quality_p05")
        pinch_quality_mean = _value(stats, "pinch_quality_mean")
        if (pinch_quality_mean is None
                or pinch_quality_mean < self.config.pinch_quality_mean_gate):
            failures.append("pinch_quality_mean")
        free_quality_mean = _value(stats, "free_quality_mean")
        if (free_quality_mean is None
                or free_quality_mean < self.config.free_quality_mean_gate):
            failures.append("free_quality_mean")
        grip_bad_frame_rate = _value(stats, "grip_bad_frame_rate")
        if (grip_bad_frame_rate is None
                or grip_bad_frame_rate
                > self.config.max_grip_bad_frame_rate):
            failures.append("grip_bad_frame_rate")
        grip_bad_streak = _value(stats, "grip_bad_streak")
        if (grip_bad_streak is None
                or grip_bad_streak
                > self.config.max_grip_bad_streak_frames):
            failures.append("grip_bad_streak")
        if self.stage == A0_PICK_GRIP:
            return tuple(failures)
        ready = _value(stats, "ready")
        if ready is None or ready < self.config.tip_ready_success_gate:
            failures.append("ready")
        if self.stage == A1_TIP_READY:
            return tuple(failures)
        recall, fp = _value(stats, "recall"), _value(stats, "fp")
        if recall is None or recall < self.config.release_recall_gate:
            failures.append("release_recall")
        if (fp is None
                or fp > self.config.false_positive_rate_by_stage[self.stage]):
            failures.append("false_positive_rate")
        recovery_events = _value(stats, "recovery_events", 0.0)
        if recovery_events <= 0.0:
            failures.append("recovery_events")
        if self.stage in (S2_TIMED_STRUM, S3_SONG_INTEGRATION):
            conditional_recovery = _value(
                stats, "conditional_recovery_completion", -1.0)
            if conditional_recovery < self.config.recovery_completion_gate:
                failures.append("conditional_recovery_completion")
            end_to_end_recovery = _value(
                stats, "end_to_end_recovery_completion", -1.0)
            recovery_profile = (
                self.s2_profile if self.stage == S2_TIMED_STRUM
                else self.config.s2_profiles[-1])
            if end_to_end_recovery < float(
                    recovery_profile["end_to_end_recovery_rate"]):
                failures.append("end_to_end_recovery_completion")
        if self.stage == S3_SONG_INTEGRATION:
            for mode, gate in (
                    ("full", self.config.full_recovery_completion_gate),
                    ("handoff", self.config.handoff_recovery_completion_gate)):
                events = _value(stats, f"{mode}_recovery_events", 0.0)
                completed = _value(
                    stats, f"{mode}_recovery_completed", 0.0)
                if events <= 0.0:
                    failures.append(f"{mode}_recovery_events")
                elif completed / events < gate:
                    failures.append(f"{mode}_recovery_completion")
            if self.original_tempo_reached:
                status = self.original_tempo_holdout_status
                if status != "passed":
                    failures.append("original_tempo_retention" if status == "failed"
                                    else "original_tempo_holdout_" + status)
        elif (self.stage != S2_TIMED_STRUM
              and _value(stats, "recovery_completion", -1.0)
              < self.config.recovery_completion_gate):
            failures.append("recovery_completion")
        if (_value(stats, "recovery_resets", math.inf)
                > self.config.recovery_reset_rate_by_stage[self.stage]):
            failures.append("recovery_reset_rate")
        if (_value(stats, "blocked_crossings", math.inf)
                > self.current_blocked_crossing_rate_gate):
            failures.append("blocked_crossing_rate")
        if self.stage == A2_SINGLE_CROSSING:
            return tuple(failures)
        if self.stage == A3_TIMED_SINGLE:
            if _value(stats, "f1", -1.0) < self.current_strike_f1_gate:
                failures.append("strike_f1")
            if _value(stats, "timing", math.inf) > self.timing_tolerance_ms:
                failures.append("timing")
            if (_value(stats, "zone", -1.0)
                    < self.config.zone_success_gate):
                failures.append("zone")
            return tuple(failures)
        strum_applicable = (
            self.stage != S3_SONG_INTEGRATION or self.song_has_strum)
        if strum_applicable:
            if _value(stats, "strum_events", 0.0) <= 0.0:
                failures.append("strum_events")
            if (_value(stats, "strum_completion", -1.0)
                    < (float(self.s2_profile["completion_rate"])
                       if self.stage == S2_TIMED_STRUM
                       else self.config.strum_completion_gate)):
                failures.append("strum_completion")
            if (_value(stats, "strum_traversal", -1.0)
                    < self.config.strum_traversal_gate):
                failures.append("strum_traversal")
            if (_value(stats, "strum_order", -1.0)
                    < self.config.strum_order_gate):
                failures.append("strum_order")
            if (_value(stats, "strum_direction", -1.0)
                    < self.config.strum_direction_gate_by_stage[self.stage]):
                failures.append("strum_direction")
        if self.stage == S2_TIMED_STRUM:
            if (_value(stats, "down_events", 0.0) <= 0.0
                    or _value(stats, "up_events", 0.0) <= 0.0
                    or _value(stats, "down_completed") is None
                    or _value(stats, "up_completed") is None):
                failures.append("direction_completion_evidence")
            elif (_value(stats, "worst_direction_completion", -1.0)
                  < float(self.s2_profile[
                      "worst_direction_completion_rate"])):
                failures.append("worst_direction_completion")
        if self.stage in (
                A4_STRUM_CONTEXT_RECOVERY, S0_TWO_STRING_STRUM,
                S1_STRUM_SPAN):
            return tuple(failures)
        if self.stage == S2_TIMED_STRUM:
            if not self.s2_endpoint_profile_active:
                if (_value(stats, "timing_pass", -1.0)
                        < float(self.s2_profile["timing_pass_rate"])):
                    failures.append("timing_pass_rate")
                signed_mean = _value(stats, "timing_signed_mean", math.inf)
                if (abs(signed_mean)
                        > float(self.s2_profile[
                            "timing_center_mean_abs_ms"])):
                    failures.append("timing_center_mean")
                signed_p10 = _value(stats, "timing_signed_p10", -math.inf)
                signed_p90 = _value(stats, "timing_signed_p90", math.inf)
                center_tail = float(
                    self.s2_profile["timing_center_tail_abs_ms"])
                if signed_p10 < -center_tail or signed_p90 > center_tail:
                    failures.append("timing_center_tail")
                if (self.zone_active and _value(stats, "zone", -1.0)
                        < float(self.s2_profile["zone_success_rate"])):
                    failures.append("zone")
        else:
            if _value(stats, "timing", math.inf) > self.timing_tolerance_ms:
                failures.append("timing")
            signed_mean = _value(stats, "timing_signed_mean", math.inf)
            center_mean = float(
                self.config.s2_profiles[-1]["timing_center_mean_abs_ms"])
            if abs(signed_mean) > center_mean:
                failures.append("timing_center_mean")
            signed_p10 = _value(stats, "timing_signed_p10", -math.inf)
            signed_p90 = _value(stats, "timing_signed_p90", math.inf)
            center_tail = float(
                self.config.s2_profiles[-1]["timing_center_tail_abs_ms"])
            if signed_p10 < -center_tail or signed_p90 > center_tail:
                failures.append("timing_center_tail")
            if _value(stats, "zone", -1.0) < self.config.zone_success_gate:
                failures.append("zone")
        if strum_applicable and not self.s2_endpoint_profile_active:
            if _value(stats, "strum_micro_samples", 0.0) <= 0.0:
                failures.append("strum_micro_samples")
            if (_value(stats, "strum_timing_rms", math.inf)
                    > (float(self.s2_profile["timing_rms_ms"])
                       if self.stage == S2_TIMED_STRUM
                       else self.config.strum_timing_rms_gate_ms)):
                failures.append("strum_timing_rms")
            if (_value(stats, "strum_duration_mae", math.inf)
                    > (float(self.s2_profile["duration_mae_ms"])
                       if self.stage == S2_TIMED_STRUM
                       else self.config.strum_duration_mae_gate_ms)):
                failures.append("strum_duration_mae")
        if self.stage == S2_TIMED_STRUM:
            return tuple(failures)
        if _value(stats, "f1", -1.0) < self.current_strike_f1_gate:
            failures.append("song_f1")
        return tuple(failures)

    def _passed(self, stats):
        return not self._gate_failures(stats)

    def _update_s2_endpoint_recovery(self, evidence, passed):
        if self.stage != S2_TIMED_STRUM or self.s2_profile_index != 0:
            self._reset_s2_endpoint_recovery()
            return
        down_rate = pooled_rate_from_counts(
            evidence,
            "strike_down_completed_count",
            "strike_down_event_count")
        up_rate = pooled_rate_from_counts(
            evidence,
            "strike_up_completed_count",
            "strike_up_event_count")
        if down_rate is None or up_rate is None:
            self.s2_endpoint_failure_streak = 0
            return
        worst_rate = min(down_rate, up_rate)
        if self.s2_endpoint_recovery_active:
            if down_rate < up_rate:
                self.s2_focus_direction = "down"
            elif up_rate < down_rate:
                self.s2_focus_direction = "up"
            elif self.s2_focus_direction == "balanced":
                self.s2_focus_direction = "down"
            return
        severe_endpoint_failure = (
            not passed
            and worst_rate
            < float(self.config.s2_endpoint_recovery_trigger_rate))
        self.s2_endpoint_failure_streak = (
            self.s2_endpoint_failure_streak + 1
            if severe_endpoint_failure else 0)
        if (self.s2_endpoint_failure_streak
                >= self.config.s2_endpoint_recovery_windows):
            self.s2_endpoint_recovery_active = True
            self.s2_focus_direction = (
                "down" if down_rate <= up_rate else "up")
            self.promotion_streak = 0
            self._reset_evidence()

    def _promote(self):
        index = self.active_stages.index(self.stage)
        if index == len(self.active_stages) - 1:
            self.complete = True
            return
        self.stage = self.active_stages[index + 1]
        self.stage_iteration = 0
        self.promotion_streak = 0
        self.stalled = False
        self._reset_evidence()
        self.last_evidence_passed = False
        self.last_gate_failures = ("not_evaluated",)
        if self.stage == A3_TIMED_SINGLE:
            self.timing_level = 0
        if self.stage == S2_TIMED_STRUM:
            self.s2_profile_index = 0
            self.rollback_streak = 0
            self.rollback_cooldown = 0
            self.s2_adaptation_remaining = 0
            self._reset_s2_endpoint_recovery()
        if self.stage == S1_STRUM_SPAN:
            self.span_level = 0
        if self.stage == S3_SONG_INTEGRATION:
            self.timing_level = len(self.config.timing_tolerances_ms) - 1
            self.s2_profile_index = len(self.config.s2_profiles) - 1
            self.tempo_level = 0
            self._reset_original_tempo_holdout()

    def initialize_song_integration_transfer(self, tempo_lambda=0.0):
        try:
            self.tempo_level = self.config.tempo_lambdas.index(
                float(tempo_lambda))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "initial transfer tempo must be one of tempo_lambdas") from exc
        self.stage = S3_SONG_INTEGRATION
        self.stage_iteration = 0
        self.total_iteration = 0
        self.stalled = False
        self.promotion_streak = 0
        self.timing_level = len(self.config.timing_tolerances_ms) - 1
        self.s2_profile_index = len(self.config.s2_profiles) - 1
        self.rollback_streak = 0
        self.rollback_count = 0
        self.rollback_cooldown = 0
        self.s2_adaptation_remaining = 0
        self._reset_s2_endpoint_recovery()
        self.span_level = len(self.config.strum_spans) - 1
        self.complete = False
        self._reset_evidence()
        self.last_evidence_passed = False
        self.last_gate_failures = ("policy_transfer",)
        self.gate_evaluation_count = 0
        self._reset_original_tempo_holdout()
        return self.state()

    def initialize_timed_strum_transfer(self):
        if not self.song_has_strum:
            raise ValueError(
                "timed-strum transfer is unavailable for a pick-only song")
        self.stage = S2_TIMED_STRUM
        self.stage_iteration = 0
        self.total_iteration = 0
        self.stalled = False
        self.promotion_streak = 0
        self.timing_level = 0
        self.s2_profile_index = 0
        self.rollback_streak = 0
        self.rollback_count = 0
        self.rollback_cooldown = 0
        self.s2_adaptation_remaining = 0
        self.span_level = len(self.config.strum_spans) - 1
        self.tempo_level = 0
        self.complete = False
        self._reset_s2_endpoint_recovery()
        self._reset_evidence()
        self.last_evidence_passed = False
        self.last_gate_failures = ("timed_strum_policy_transfer",)
        self.gate_evaluation_count = 0
        self._reset_original_tempo_holdout()
        return self.state()

    def after_iteration(self, stats):
        self.total_iteration += 1
        self.stage_iteration += 1
        adaptation_active = self.s2_adaptation_remaining > 0
        if adaptation_active:
            self.s2_adaptation_remaining -= 1
        if self.rollback_cooldown > 0:
            self.rollback_cooldown -= 1
        evidence = self._consume_evidence(stats)
        passed = False
        if evidence is not None:
            failures = self._gate_failures(evidence)
            passed = not failures
            self.last_evidence_passed = passed
            self.last_gate_failures = failures or ("none",)
            self.gate_evaluation_count += 1
            if self.stage == S3_SONG_INTEGRATION:
                training_passed = not any(
                    not name.startswith("original_tempo_")
                    for name in failures)
                self.quality_evidence_iteration = self.total_iteration
                self.quality_evidence_pass_streak = (
                    self.quality_evidence_pass_streak + 1
                    if training_passed else 0)
                self.quality_evidence_fail_streak = (
                    0 if training_passed
                    else self.quality_evidence_fail_streak + 1)
            self._update_s2_endpoint_recovery(evidence, passed)
        elif (self.stage == S2_TIMED_STRUM
              and self.s2_profile_index == 0
              and self.s2_endpoint_recovery_active):
            uniform = stats.get("_uniform_evidence")
            if not isinstance(uniform, Mapping) or not uniform:
                self.last_evidence_passed = False
                self.last_gate_failures = (
                    "uniform_direction_evidence_missing",)
        elif self.stage == S3_SONG_INTEGRATION:
            uniform = stats.get("_uniform_evidence")
            if (self.config.s3_uniform_curriculum_evidence_only
                    and (not isinstance(uniform, Mapping) or not uniform)):
                self.last_evidence_passed = False
                self.quality_evidence_iteration = None
                self.last_gate_failures = ("uniform_song_evidence_missing",)
        if self.complete:
            return self.state()
        rolled_back = False
        if (evidence is not None and self.stage == S2_TIMED_STRUM
                and self.s2_profile_index > 0
                and not adaptation_active
                and self.rollback_cooldown == 0):
            severe = (
                _value(evidence, "timing_pass", 0.0)
                < self.config.s2_rollback_timing_pass_rate
                or _value(evidence, "strum_completion", 0.0)
                < self.config.s2_rollback_completion_rate
                or _value(evidence, "strum_traversal", 0.0)
                < self.config.s2_rollback_traversal_rate
                or _value(evidence, "strum_direction", 0.0)
                < self.config.s2_rollback_direction_rate
                or _value(evidence, "fp", 1.0)
                > self.config.s2_rollback_false_positive_rate)
            self.rollback_streak = self.rollback_streak + 1 if severe else 0
            if self.rollback_streak >= self.config.s2_rollback_windows:
                self.s2_profile_index -= 1
                self.rollback_count += 1
                self.rollback_streak = 0
                self.rollback_cooldown = (
                    self.config.s2_rollback_cooldown_iterations)
                self.s2_adaptation_remaining = 0
                self.stage_iteration = 0
                self.promotion_streak = 0
                self.stalled = False
                self.last_gate_failures = ("s2_profile_rollback",)
                self._reset_evidence()
                if self.s2_profile_index == 0:
                    self._reset_s2_endpoint_recovery()
                rolled_back = True
        elif self.stage != S2_TIMED_STRUM:
            self.rollback_streak = 0
        minimum = self.config.min_iterations[self.stage]
        maximum = self.config.max_iterations[self.stage]
        if evidence is not None and not rolled_back:
            self.promotion_streak = self.promotion_streak + 1 if passed else 0
        if (not rolled_back and self.rollback_cooldown == 0
                and self.s2_adaptation_remaining == 0
                and self.stage_iteration >= minimum
                and self.promotion_streak >= self.config.promotion_windows):
            self.promotion_streak = 0
            self.stalled = False
            if self.stage == A3_TIMED_SINGLE \
                    and self.timing_level < len(self.config.timing_tolerances_ms) - 1:
                self.timing_level += 1
                self.stage_iteration = 0
            elif self.stage == S2_TIMED_STRUM \
                    and self.s2_profile_index < len(self.config.s2_profiles) - 1:
                self.s2_profile_index += 1
                self.stage_iteration = 0
                self.s2_adaptation_remaining = (
                    self.config.s2_profile_adaptation_iterations)
                self._reset_s2_endpoint_recovery()
            elif self.stage == S1_STRUM_SPAN \
                    and self.span_level < len(self.config.strum_spans) - 1:
                self.span_level += 1
                self.stage_iteration = 0
            elif self.stage == S3_SONG_INTEGRATION \
                    and self.tempo_level < len(self.config.tempo_lambdas) - 1:
                self.tempo_level += 1
                self.stage_iteration = 0
            else:
                self._promote()
        if not self.complete and self.stage_iteration >= maximum:
            if (self.stage == S3_SONG_INTEGRATION
                    and self.config.s3_stalled_original_tempo_recovery
                    and self.tempo_level < len(self.config.tempo_lambdas) - 1):
                self.tempo_level = len(self.config.tempo_lambdas) - 1
                self.stage_iteration = 0
                self.promotion_streak = 0
                self.stalled = True
                self._reset_evidence()
                self.last_evidence_passed = False
                self.last_gate_failures = (
                    "s3_original_tempo_rehearsal",)
            else:
                self.stalled = True
        return self.state()

    def apply(self, env):
        endpoint_supported = all(hasattr(env, name) for name in (
            "s2_endpoint_recovery_active",
            "s2_focus_direction",
            "s2_focus_fraction",
        ))
        endpoint_changed = endpoint_supported and (
            env.s2_endpoint_recovery_active
            != self.s2_endpoint_recovery_active
            or env.s2_focus_direction != self.s2_focus_direction
            or env.s2_focus_fraction != self.s2_focus_fraction)
        goal_count = int(getattr(
            getattr(env, "goals", None),
            "num_events", self.song_events_per_episode))
        expected_song_events = (
            goal_count if self.s3_original_tempo_rehearsal_active
            else min(self.song_events_per_episode, goal_count))
        changed = (
            getattr(env, "curriculum_stage", None) != self.stage
            or getattr(env, "timing_tolerance_ms", None)
            != self.timing_tolerance_ms
            or getattr(env, "tempo_lambda", None) != self.tempo_lambda
            or getattr(env, "song_events_per_episode", None)
            != expected_song_events
            or getattr(env, "strum_span", None) != self.strum_span
            or getattr(env, "s2_profile_name", None) != self.s2_profile_name
            or endpoint_changed
            or getattr(env, "zone_gate_active", None) != self.zone_active
            or getattr(env, "timing_reward_core_ms", None)
            != self.timing_reward_core_ms
            or getattr(env, "duration_reward_core_ms", None)
            != self.duration_reward_core_ms
            or getattr(env, "approach_lead_s", None)
            != self.approach_lead_s
            or getattr(env, "timing_early_grace_ms", None)
            != self.timing_early_grace_ms
            or getattr(env, "timing_early_penalty_scale_ms", None)
            != self.timing_early_penalty_scale_ms
            or getattr(env, "curriculum_stalled", None) != self.stalled
            or getattr(env, "curriculum_song_f1_gate", None)
            != self.current_strike_f1_gate)
        endpoint_kwargs = ({
            "s2_endpoint_recovery_active": (
                self.s2_endpoint_recovery_active),
            "s2_focus_direction": self.s2_focus_direction,
            "s2_focus_fraction": self.s2_focus_fraction,
        } if endpoint_supported else {})
        observation = env.set_curriculum_stage(
            self.stage, self.timing_tolerance_ms,
            tempo_lambda=self.tempo_lambda,
            song_events_per_episode=expected_song_events,
            strum_span=self.strum_span,
            s2_profile_name=self.s2_profile_name,
            **endpoint_kwargs,
            zone_active=self.zone_active,
            timing_reward_core_ms=self.timing_reward_core_ms,
            duration_reward_core_ms=self.duration_reward_core_ms,
            approach_lead_s=self.approach_lead_s,
            timing_early_grace_ms=self.timing_early_grace_ms,
            timing_early_penalty_scale_ms=(
                self.timing_early_penalty_scale_ms),
            song_f1_gate=self.current_strike_f1_gate,
            stalled=self.stalled,
            reset=changed)
        result = self.state()
        result["curriculum_training_song_events_per_episode"] = int(
            getattr(env, "song_events_per_episode", expected_song_events))
        result["curriculum_original_tempo_rehearsal_full_song"] = bool(
            self.s3_original_tempo_rehearsal_active)
        if observation is not None:
            result["_reset_observation"] = observation
        return result


__all__ = [
    "A0_PICK_GRIP", "A1_TIP_READY", "A2_SINGLE_CROSSING",
    "A3_TIMED_SINGLE", "A4_STRUM_CONTEXT_RECOVERY",
    "S0_TWO_STRING_STRUM", "S1_STRUM_SPAN",
    "S2_TIMED_STRUM", "S3_SONG_INTEGRATION", "STRIKE_STAGES",
    "S2_ENDPOINT_PROFILE_NAME",
    "StrikeCurriculumConfig", "StrikeCurriculum",
]
