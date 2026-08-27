"""Per-song practice curriculum for trajectory optimization, not song generalization."""
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import math


@dataclass(frozen=True)
class FingertipApproachCurriculumConfig:
    """Performance-gated acquisition stages followed by the song schedule."""
    coarse_min_iterations: int = 100
    coarse_max_iterations: int = 1000
    fine_min_iterations: int = 200
    fine_max_iterations: int = 1500
    isolated_press_min_iterations: int = 300
    isolated_press_max_iterations: int = 2000
    integrated_press_min_iterations: int = 300
    integrated_press_max_iterations: int = 2500
    chord_reach_min_iterations: int = 300
    chord_reach_max_iterations: int = 2000
    chord_fine_min_iterations: int = 400
    chord_fine_max_iterations: int = 2000
    chord_fine_focus_min_iterations: int = 100
    chord_fine_focus_max_iterations: int = 1200
    chord_fine_max_cycles: int = 1
    chord_fine_focus_probability: float = 0.80
    chord_fine_success_rate: float = 0.80
    chord_fine_p90_distance: float = 0.010
    chord_fine_alignment_rate: float = 0.80
    chord_fine_min_phase_episodes: int = 256
    static_chord_min_iterations: int = 400
    static_chord_max_iterations: int = 3000
    frozen_context_min_iterations: int = 1000
    frozen_context_max_iterations: int = 2500
    goal_pair_min_iterations: int = 400
    goal_pair_max_iterations: int = 8000
    transition_min_iterations: int = 800
    transition_max_iterations: int = 3000
    frozen_context_duration_frames: int = 150
    goal_pair_duration_frames: int = 120
    goal_pair_retention_rehearsal_probability: float = 1.0
    goal_pair_rehearsal_probability: float = 1.0 / 3.0
    goal_pair_mixed_transition_fractions: tuple[float, ...] = (
        0.10, 0.20, 0.35)
    goal_pair_mixed_preservation_rates: tuple[float, ...] = (
        0.50, 0.70, 0.90)
    goal_pair_mixed_press_rates: tuple[float, ...] = (
        0.10, 0.30, 0.50)
    goal_pair_mixed_full_song_press_rates: tuple[float, ...] = (
        0.10, 0.30, 0.50)
    goal_pair_mixed_wrong_press_rates: tuple[float, ...] = (
        0.10, 0.08, 0.06)
    goal_pair_mixed_distances: tuple[float, ...] = (
        0.050, 0.035, 0.025)
    goal_pair_mixed_sequence_probabilities: tuple[float, ...] = (
        0.15, 0.25, 0.35)
    goal_pair_mixed_sequence_max_events: tuple[int, ...] = (2, 4, 8)
    goal_pair_full_sequence_probability: float = 0.50
    goal_pair_full_sequence_max_events: int = 12
    goal_pair_sequence_duration_frames: int = 240
    goal_pair_sequence_full_song_fraction: float = 0.20
    goal_pair_sequence_min_frames: int = 1024
    goal_pair_sequence_press_rate: float = 0.75
    goal_pair_sequence_no_press_rate: float = 0.90
    goal_pair_sequence_wrong_press_rate: float = 0.08
    goal_pair_sequence_penetration_rate: float = 0.01
    goal_pair_sequence_thumb_support_rate: float = 0.20
    goal_pair_preview_levels: int = 1
    goal_pair_focus_lateral_exploration_std: float = 0.055
    goal_pair_retention_focus_probability: float = 0.0
    goal_pair_mixed_focus_probability: float = 0.25
    goal_pair_retention_min_iterations: int = 100
    goal_pair_mixed_min_iterations: int = 200
    goal_pair_full_min_iterations: int = 100
    goal_pair_phase_max_iterations: int = 1600
    goal_pair_phase_min_evidence: int = 1024
    goal_pair_focus_min_iterations: int = 50
    goal_pair_timeout_focus_probability: float = 0.35
    goal_pair_recovery_min_iterations: int = 100
    goal_pair_recovery_max_iterations: int = 600
    goal_pair_recovery_windows: int = 2
    goal_pair_recovery_rehearsal_probability: float = 0.50
    goal_pair_uncovered_pose_probability: float = 0.10
    goal_pair_recovery_uncovered_pose_probability: float = 0.35
    goal_pair_recovery_sequence_probability: float = 0.50
    goal_pair_recovery_sequence_max_events: int = 16
    goal_pair_recovery_full_song_fraction: float = 0.20
    goal_pair_full_song_focus_min_evidence: int = 128
    goal_pair_recovery_min_full_song_press_rate: float = 0.20
    goal_pair_phase_baseline_warmup_iterations: int = 40
    goal_pair_mastery_retain_press_rate: float = 0.70
    goal_pair_mastery_retain_distance: float = 0.020
    goal_pair_mastery_retain_hold_quality: float = 0.75
    goal_pair_mastery_retain_dropout_rate: float = 0.15
    goal_pair_mastery_regression_windows: int = 2
    goal_pair_rehearsal_press_rate: float = 0.80
    goal_pair_rehearsal_distance: float = 0.010
    goal_pair_rehearsal_hold_quality: float = 0.80
    goal_pair_rehearsal_dropout_rate: float = 0.12
    goal_pair_mixed_min_next_progress: float = -0.010
    goal_pair_pretransition_preservation_rate: float = 0.90
    goal_pair_promotion_transition_press_rate: float = 0.80
    frozen_context_initial_real_probability: float = 0.0
    frozen_context_context_warmup_iterations: int = 200
    frozen_context_context_ramp_iterations: int = 800
    frozen_context_focus_probability: float = 0.65
    frozen_context_focus_min_evidence: int = 1024
    frozen_context_recovery_press_rate: float = 0.70
    frozen_context_recovery_distance: float = 0.025
    frozen_context_hard_min_per_finger_rate: float = 0.70
    frozen_context_hard_min_f1_rate: float = 0.75
    frozen_context_hard_min_no_press_accuracy: float = 0.90
    frozen_context_hard_max_wrong_press_rate: float = 0.05
    frozen_context_hard_min_sustain_hold_rate: float = 0.70
    frozen_context_hard_min_sustain_event_rate: float = 0.40
    frozen_context_hard_max_failure_rate: float = 0.03
    transition_window_seconds: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)
    transition_max_changes: tuple[int, ...] = (4, 6, 8, 12)
    static_chord_min_evidence_episodes: int = 128
    frozen_context_min_evidence_episodes: int = 128
    goal_pair_min_evidence_episodes: int = 128
    transition_min_evidence_episodes: int = 128
    coverage_min_evidence_episodes: int = 128
    integration_min_evidence_episodes: int = 128
    coverage_iterations: int = 1000
    integration_iterations: int = 1000
    promotion_success_rate: float = 0.80
    promotion_windows: int = 3
    bridge_window_episodes: int = 4096
    bridge_promotion_windows: int = 2
    frozen_context_final_evaluation_iterations: int = 200
    bridge_soft_timeout_fraction: float = 0.80
    bridge_hard_timeout_min_per_finger_rate: float = 0.20
    late_stage_grace_iterations: int = 500
    bridge_f1_rate: float = 0.95
    bridge_per_finger_press_rate: float = 0.90
    bridge_no_press_accuracy: float = 0.93
    bridge_wrong_press_rate: float = 0.035
    bridge_sustain_hold_rate: float = 0.95
    bridge_sustain_event_rate: float = 0.85
    bridge_press_dropout_rate: float = 0.04
    bridge_failure_termination_rate: float = 0.02
    bridge_soft_f1_rate: float = 0.93
    bridge_soft_per_finger_press_rate: float = 0.85
    bridge_soft_no_press_accuracy: float = 0.90
    bridge_soft_wrong_press_rate: float = 0.05
    bridge_soft_sustain_hold_rate: float = 0.92
    bridge_soft_sustain_event_rate: float = 0.78
    bridge_soft_press_dropout_rate: float = 0.06
    bridge_soft_failure_termination_rate: float = 0.03
    regression_f1_drop: float = 0.04
    regression_no_press_drop: float = 0.03
    regression_wrong_press_increase: float = 0.015
    regression_sustain_event_drop: float = 0.07
    regression_per_finger_drop: float = 0.05
    regression_failure_increase: float = 0.01
    regression_hold_windows: int = 2
    song_f1_rate: float = 0.85
    song_per_finger_press_rate: float = 0.80
    song_no_press_accuracy: float = 0.99
    song_wrong_press_rate: float = 0.01
    song_sustain_hold_rate: float = 0.90
    song_press_dropout_rate: float = 0.05
    song_min_sustain_events: float = 1.0
    thumb_coarse_distance: float = 0.050
    thumb_fine_distance: float = 0.025
    thumb_integrated_distance: float = 0.015
    thumb_geometry_gate_enabled: bool = False
    thumb_press_readiness_rate: float = 0.35
    thumb_contact_gate_enabled: bool = False
    thumb_support_rate: float = 0.80
    thumb_wrong_contact_rate: float = 0.05

    def __post_init__(self):
        pairs = ((self.coarse_min_iterations, self.coarse_max_iterations),
                 (self.fine_min_iterations, self.fine_max_iterations),
                 (self.isolated_press_min_iterations,
                  self.isolated_press_max_iterations),
                 (self.integrated_press_min_iterations,
                  self.integrated_press_max_iterations),
                 (self.chord_reach_min_iterations,
                  self.chord_reach_max_iterations),
                 (self.chord_fine_min_iterations,
                  self.chord_fine_max_iterations),
                 (self.chord_fine_focus_min_iterations,
                  self.chord_fine_focus_max_iterations),
                 (self.static_chord_min_iterations,
                  self.static_chord_max_iterations),
                 (self.frozen_context_min_iterations,
                  self.frozen_context_max_iterations),
                 (self.goal_pair_min_iterations,
                  self.goal_pair_max_iterations),
                 (self.transition_min_iterations,
                  self.transition_max_iterations))
        if any(minimum < 0 or maximum < minimum for minimum, maximum in pairs):
            raise ValueError("curriculum min/max iterations are invalid")
        if self.coverage_iterations < 0 or self.integration_iterations < 0:
            raise ValueError("song curriculum durations must be non-negative")
        if not 0.0 <= self.promotion_success_rate <= 1.0:
            raise ValueError("promotion success rate must be in [0, 1]")
        if not 0.0 <= self.chord_fine_success_rate <= 1.0:
            raise ValueError("chord fine success rate must be in [0, 1]")
        if not 0.0 < self.chord_fine_focus_probability <= 1.0:
            raise ValueError(
                "chord fine focus probability must be in (0, 1]")
        if self.chord_fine_p90_distance <= 0.0:
            raise ValueError("chord fine p90 distance must be positive")
        if not 0.0 <= self.chord_fine_alignment_rate <= 1.0:
            raise ValueError("chord fine alignment rate must be in [0, 1]")
        if self.chord_fine_min_phase_episodes < 1:
            raise ValueError(
                "chord fine minimum phase episodes must be positive")
        if self.chord_fine_max_cycles < 1:
            raise ValueError("chord fine maximum cycles must be positive")
        if (self.frozen_context_duration_frames < 1
                or self.goal_pair_duration_frames < 1):
            raise ValueError(
                "frozen-context and goal-pair durations must be positive")
        mixed_rehearsal_probability = (
            1.0 - self.goal_pair_mixed_transition_fractions[-1]
            if self.goal_pair_mixed_transition_fractions else float("nan"))
        goal_pair_probabilities = (
            self.goal_pair_retention_rehearsal_probability,
            mixed_rehearsal_probability,
            self.goal_pair_rehearsal_probability,
        )
        if (any(not 0.0 <= value <= 1.0
                for value in goal_pair_probabilities)
                or not (
                    self.goal_pair_retention_rehearsal_probability
                    >= mixed_rehearsal_probability
                    >= self.goal_pair_rehearsal_probability)):
            raise ValueError(
                "goal-pair rehearsal probabilities must be descending in [0, 1]")
        mixed_schedules = (
            self.goal_pair_mixed_transition_fractions,
            self.goal_pair_mixed_preservation_rates,
            self.goal_pair_mixed_press_rates,
            self.goal_pair_mixed_full_song_press_rates,
            self.goal_pair_mixed_wrong_press_rates,
            self.goal_pair_mixed_distances,
            self.goal_pair_mixed_sequence_probabilities,
            self.goal_pair_mixed_sequence_max_events,
        )
        if (not self.goal_pair_mixed_transition_fractions
                or any(
                    len(values)
                    != len(self.goal_pair_mixed_transition_fractions)
                    for values in mixed_schedules)):
            raise ValueError(
                "goal-pair mixed schedules must have equal non-zero length")
        if (any(
                not math.isfinite(value) or not 0.0 < value < 1.0
                for value in self.goal_pair_mixed_transition_fractions)
                or any(
                    right <= left for left, right in zip(
                        self.goal_pair_mixed_transition_fractions,
                        self.goal_pair_mixed_transition_fractions[1:]))
                ):
            raise ValueError(
                "goal-pair mixed transition fractions must increase within "
                "(0, 1)")
        if (any(
                not math.isfinite(value) or not 0.0 <= value <= 1.0
                for values in (
                    self.goal_pair_mixed_preservation_rates,
                    self.goal_pair_mixed_press_rates,
                    self.goal_pair_mixed_full_song_press_rates,
                    self.goal_pair_mixed_wrong_press_rates)
                for value in values)
                or any(
                    right < left
                    for values in (
                        self.goal_pair_mixed_preservation_rates,
                        self.goal_pair_mixed_press_rates,
                        self.goal_pair_mixed_full_song_press_rates)
                    for left, right in zip(values, values[1:]))):
            raise ValueError(
                "goal-pair mixed preservation and press rates must increase "
                "within [0, 1]")
        if any(
                right > left for left, right in zip(
                    self.goal_pair_mixed_wrong_press_rates,
                    self.goal_pair_mixed_wrong_press_rates[1:])):
            raise ValueError(
                "goal-pair mixed wrong-press rates must decrease")
        if (any(
                not math.isfinite(value) or value <= 0.0
                for value in self.goal_pair_mixed_distances)
                or any(
                    right >= left for left, right in zip(
                        self.goal_pair_mixed_distances,
                        self.goal_pair_mixed_distances[1:]))):
            raise ValueError(
                "goal-pair mixed distances must be positive and decrease")
        if (any(
                not math.isfinite(value) or not 0.0 <= value <= 1.0
                for value in self.goal_pair_mixed_sequence_probabilities)
                or any(
                    right < left for left, right in zip(
                        self.goal_pair_mixed_sequence_probabilities,
                        self.goal_pair_mixed_sequence_probabilities[1:]))
                or not 0.0 <= self.goal_pair_full_sequence_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_sequence_full_song_fraction <= 1.0):
            raise ValueError(
                "goal-pair sequence probabilities must increase within [0, 1]")
        if (isinstance(self.goal_pair_sequence_duration_frames, bool)
                or not isinstance(
                    self.goal_pair_sequence_duration_frames, int)
                or self.goal_pair_sequence_duration_frames < 1):
            raise ValueError(
                "goal-pair sequence duration must be a positive integer")
        if (any(
                isinstance(value, bool) or not isinstance(value, int)
                or value < 2
                for value in self.goal_pair_mixed_sequence_max_events)
                or any(
                    right < left for left, right in zip(
                        self.goal_pair_mixed_sequence_max_events,
                        self.goal_pair_mixed_sequence_max_events[1:]))
                or isinstance(self.goal_pair_full_sequence_max_events, bool)
                or not isinstance(self.goal_pair_full_sequence_max_events, int)
                or self.goal_pair_full_sequence_max_events
                    < self.goal_pair_mixed_sequence_max_events[-1]):
            raise ValueError(
                "goal-pair sequence event counts must increase from at least 2")
        if (isinstance(self.goal_pair_sequence_min_frames, bool)
                or not isinstance(self.goal_pair_sequence_min_frames, int)
                or self.goal_pair_sequence_min_frames < 1):
            raise ValueError(
                "goal-pair sequence evidence must be a positive integer")
        sequence_rates = (
            self.goal_pair_sequence_press_rate,
            self.goal_pair_sequence_no_press_rate,
            self.goal_pair_sequence_wrong_press_rate,
            self.goal_pair_sequence_penetration_rate,
            self.goal_pair_sequence_thumb_support_rate,
        )
        if any(
                not math.isfinite(value) or not 0.0 <= value <= 1.0
                for value in sequence_rates):
            raise ValueError(
                "goal-pair sequence thresholds must be in [0, 1]")
        if (isinstance(self.goal_pair_preview_levels, bool)
                or not isinstance(self.goal_pair_preview_levels, int)
                or not 0 <= self.goal_pair_preview_levels
                    < len(self.goal_pair_mixed_transition_fractions)):
            raise ValueError(
                "goal-pair preview levels must leave at least one full "
                "transition level")
        if (not math.isfinite(
                self.goal_pair_focus_lateral_exploration_std)
                or self.goal_pair_focus_lateral_exploration_std <= 0.0):
            raise ValueError(
                "goal-pair lateral exploration std must be positive")
        if any(
                not 0.0 <= value <= 1.0
                for value in (
                    self.goal_pair_retention_focus_probability,
                    self.goal_pair_mixed_focus_probability)):
            raise ValueError(
                "goal-pair focus probabilities must be in [0, 1]")
        phase_iterations = (
            self.goal_pair_retention_min_iterations,
            self.goal_pair_mixed_min_iterations,
            self.goal_pair_full_min_iterations,
            self.goal_pair_phase_max_iterations,
            self.goal_pair_focus_min_iterations,
            self.goal_pair_recovery_min_iterations,
            self.goal_pair_recovery_max_iterations,
            self.goal_pair_recovery_windows,
            self.goal_pair_recovery_sequence_max_events,
            self.goal_pair_full_song_focus_min_evidence,
        )
        if any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
                for value in phase_iterations):
            raise ValueError(
                "goal-pair phase iterations must be positive integers")
        if self.goal_pair_phase_max_iterations < max(
                self.goal_pair_retention_min_iterations,
                self.goal_pair_mixed_min_iterations):
            raise ValueError(
                "goal-pair phase maximum must cover phase minimums")
        if (self.goal_pair_recovery_max_iterations
                < self.goal_pair_recovery_min_iterations):
            raise ValueError(
                "goal-pair recovery maximum must cover its minimum")
        if (isinstance(
                self.goal_pair_phase_baseline_warmup_iterations, bool)
                or not isinstance(
                    self.goal_pair_phase_baseline_warmup_iterations, int)
                or self.goal_pair_phase_baseline_warmup_iterations < 0):
            raise ValueError(
                "goal-pair baseline warmup must be a non-negative integer")
        if (isinstance(self.goal_pair_phase_min_evidence, bool)
                or not isinstance(self.goal_pair_phase_min_evidence, int)
                or self.goal_pair_phase_min_evidence < 1):
            raise ValueError(
                "goal-pair phase evidence must be a positive integer")
        if (not 0.0 <= self.goal_pair_timeout_focus_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_recovery_rehearsal_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_uncovered_pose_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_recovery_uncovered_pose_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_recovery_sequence_probability <= 1.0
                or not 0.0
                    <= self.goal_pair_recovery_full_song_fraction <= 1.0
                or not 0.0
                    <= self.goal_pair_recovery_min_full_song_press_rate <= 1.0
                or not 0.0
                    <= self.goal_pair_mastery_retain_press_rate <= 1.0):
            raise ValueError(
                "goal-pair recovery probabilities must be in [0, 1]")
        if (not math.isfinite(self.goal_pair_mastery_retain_distance)
                or self.goal_pair_mastery_retain_distance <= 0.0):
            raise ValueError(
                "goal-pair mastery retention distance must be positive")
        if (isinstance(self.goal_pair_mastery_regression_windows, bool)
                or not isinstance(
                    self.goal_pair_mastery_regression_windows, int)
                or self.goal_pair_mastery_regression_windows < 1):
            raise ValueError(
                "goal-pair regression windows must be a positive integer")
        if (not math.isfinite(self.goal_pair_rehearsal_distance)
                or self.goal_pair_rehearsal_distance <= 0.0):
            raise ValueError(
                "goal-pair distance thresholds must be finite and positive")
        goal_pair_rates = (
            self.goal_pair_rehearsal_press_rate,
            self.goal_pair_rehearsal_hold_quality,
            self.goal_pair_rehearsal_dropout_rate,
            self.goal_pair_mastery_retain_hold_quality,
            self.goal_pair_mastery_retain_dropout_rate,
            self.goal_pair_pretransition_preservation_rate,
            self.goal_pair_promotion_transition_press_rate,
        )
        if any(not 0.0 <= value <= 1.0 for value in goal_pair_rates):
            raise ValueError("goal-pair rates must be in [0, 1]")
        if (self.goal_pair_rehearsal_press_rate
                < self.goal_pair_mastery_retain_press_rate
                or self.goal_pair_rehearsal_hold_quality
                < self.goal_pair_mastery_retain_hold_quality
                or self.goal_pair_rehearsal_dropout_rate
                > self.goal_pair_mastery_retain_dropout_rate
                or self.goal_pair_rehearsal_distance
                > self.goal_pair_mastery_retain_distance):
            raise ValueError(
                "goal-pair acquisition thresholds must be stricter than retention")
        if (not math.isfinite(self.goal_pair_mixed_min_next_progress)
                or not -1.0 <= self.goal_pair_mixed_min_next_progress <= 1.0):
            raise ValueError(
                "goal-pair next progress threshold must be in [-1, 1]")
        if not 0.0 <= self.frozen_context_initial_real_probability <= 1.0:
            raise ValueError(
                "frozen-context initial probability must be in [0, 1]")
        if self.frozen_context_context_warmup_iterations < 0:
            raise ValueError(
                "frozen-context context warmup must be non-negative")
        if self.frozen_context_context_ramp_iterations < 1:
            raise ValueError(
                "frozen-context context ramp must be positive")
        frozen_rates = (
            self.frozen_context_focus_probability,
            self.frozen_context_recovery_press_rate,
            self.frozen_context_hard_min_per_finger_rate,
            self.frozen_context_hard_min_f1_rate,
            self.frozen_context_hard_min_no_press_accuracy,
            self.frozen_context_hard_max_wrong_press_rate,
            self.frozen_context_hard_min_sustain_hold_rate,
            self.frozen_context_hard_min_sustain_event_rate,
            self.frozen_context_hard_max_failure_rate,
        )
        if any(not 0.0 <= value <= 1.0 for value in frozen_rates):
            raise ValueError(
                "frozen-context focus and recovery rates must be in [0, 1]")
        if (isinstance(self.frozen_context_focus_min_evidence, bool)
                or not isinstance(self.frozen_context_focus_min_evidence, int)
                or self.frozen_context_focus_min_evidence < 1):
            raise ValueError(
                "frozen-context focus evidence must be a positive integer")
        if (not math.isfinite(self.frozen_context_recovery_distance)
                or self.frozen_context_recovery_distance <= 0.0):
            raise ValueError(
                "frozen-context recovery distance must be positive")
        if (not self.transition_window_seconds
                or len(self.transition_window_seconds)
                != len(self.transition_max_changes)):
            raise ValueError(
                "transition window/change schedules must have equal non-zero length")
        if any(
                not math.isfinite(float(seconds)) or float(seconds) <= 0.0
                for seconds in self.transition_window_seconds):
            raise ValueError("transition window seconds must be finite and positive")
        if any(
                right < left
                for left, right in zip(
                    self.transition_window_seconds,
                    self.transition_window_seconds[1:])):
            raise ValueError("transition window seconds must be non-decreasing")
        if any(
                isinstance(changes, bool)
                or not isinstance(changes, int)
                or changes < 1
                for changes in self.transition_max_changes):
            raise ValueError(
                "transition maximum changes must contain positive integers")
        if any(
                right < left
                for left, right in zip(
                    self.transition_max_changes,
                    self.transition_max_changes[1:])):
            raise ValueError(
                "transition maximum changes must be non-decreasing")
        evidence = (
            self.static_chord_min_evidence_episodes,
            self.frozen_context_min_evidence_episodes,
            self.goal_pair_min_evidence_episodes,
            self.transition_min_evidence_episodes,
            self.coverage_min_evidence_episodes,
            self.integration_min_evidence_episodes,
        )
        if any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
                for value in evidence):
            raise ValueError(
                "stage promotion evidence must contain positive episode counts")
        if self.promotion_windows < 1:
            raise ValueError("promotion windows must be positive")
        if self.bridge_window_episodes < 1:
            raise ValueError("bridge window episodes must be positive")
        if self.bridge_promotion_windows < 1:
            raise ValueError("bridge promotion windows must be positive")
        if self.frozen_context_final_evaluation_iterations < 0:
            raise ValueError(
                "frozen-context final evaluation iterations must be non-negative")
        if not 0.0 < self.bridge_soft_timeout_fraction <= 1.0:
            raise ValueError(
                "bridge soft timeout fraction must be in (0, 1]")
        if self.late_stage_grace_iterations < 0:
            raise ValueError("late-stage grace iterations must be non-negative")
        if self.regression_hold_windows < 1:
            raise ValueError("regression hold windows must be positive")
        bridge_rates = (
            self.bridge_f1_rate,
            self.bridge_per_finger_press_rate,
            self.bridge_no_press_accuracy,
            self.bridge_wrong_press_rate,
            self.bridge_sustain_hold_rate,
            self.bridge_sustain_event_rate,
            self.bridge_press_dropout_rate,
            self.bridge_failure_termination_rate,
            self.bridge_soft_f1_rate,
            self.bridge_soft_per_finger_press_rate,
            self.bridge_soft_no_press_accuracy,
            self.bridge_soft_wrong_press_rate,
            self.bridge_soft_sustain_hold_rate,
            self.bridge_soft_sustain_event_rate,
            self.bridge_soft_press_dropout_rate,
            self.bridge_soft_failure_termination_rate,
            self.bridge_hard_timeout_min_per_finger_rate,
            self.regression_f1_drop,
            self.regression_no_press_drop,
            self.regression_wrong_press_increase,
            self.regression_sustain_event_drop,
            self.regression_per_finger_drop,
            self.regression_failure_increase,
        )
        if any(not 0.0 <= value <= 1.0 for value in bridge_rates):
            raise ValueError(
                "bridge and regression rates must be in [0, 1]")
        if any(soft > normal for soft, normal in (
                (self.bridge_soft_f1_rate, self.bridge_f1_rate),
                (self.bridge_soft_per_finger_press_rate,
                 self.bridge_per_finger_press_rate),
                (self.bridge_soft_no_press_accuracy,
                 self.bridge_no_press_accuracy),
                (self.bridge_soft_sustain_hold_rate,
                 self.bridge_sustain_hold_rate),
                (self.bridge_soft_sustain_event_rate,
                 self.bridge_sustain_event_rate))):
            raise ValueError(
                "soft bridge minimums cannot exceed normal minimums")
        if any(soft < normal for soft, normal in (
                (self.bridge_soft_wrong_press_rate,
                 self.bridge_wrong_press_rate),
                (self.bridge_soft_press_dropout_rate,
                 self.bridge_press_dropout_rate),
                (self.bridge_soft_failure_termination_rate,
                 self.bridge_failure_termination_rate))):
            raise ValueError(
                "soft bridge maximums cannot be below normal maximums")
        for name, value in (
                ("song_f1_rate", self.song_f1_rate),
                ("song_per_finger_press_rate",
                 self.song_per_finger_press_rate),
                ("song_no_press_accuracy", self.song_no_press_accuracy),
                ("song_wrong_press_rate", self.song_wrong_press_rate),
                ("song_sustain_hold_rate", self.song_sustain_hold_rate),
                ("song_press_dropout_rate",
                 self.song_press_dropout_rate)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.song_min_sustain_events < 0.0:
            raise ValueError("song_min_sustain_events must be non-negative")
        if not (0.0 < self.thumb_integrated_distance
                <= self.thumb_fine_distance <= self.thumb_coarse_distance):
            raise ValueError(
                "thumb distances must satisfy 0 < integrated <= fine <= coarse")
        if not 0.0 <= self.thumb_support_rate <= 1.0:
            raise ValueError("thumb support rate must be in [0,1]")
        if not 0.0 <= self.thumb_press_readiness_rate <= 1.0:
            raise ValueError("thumb press-readiness rate must be in [0,1]")
        if not 0.0 <= self.thumb_wrong_contact_rate <= 1.0:
            raise ValueError("thumb wrong-contact rate must be in [0,1]")

class FingertipApproachCurriculum:
    """A0--A4 curriculum whose early stages cannot earn easy baseline reward."""
    SCHEMA_VERSION = 44
    GOAL_PAIR_PHASE_SCHEMA_VERSION = 11
    STATIC_CHORD_CATALOG_SCHEMA_VERSION = 42
    CHORD_PHASE_EVIDENCE_SCHEMA_VERSION = 43
    STAGES = ("coarse_reach", "fine_reach",
              "isolated_press", "integrated_press",
              "chord_reach", "chord_fine_reach",
              "static_chord", "frozen_context", "goal_pair",
              "transition_window",
              "coverage", "integration", "full_song")
    PRACTICE_STAGES = STAGES[:10]
    BRIDGE_STAGES = (
        "frozen_context", "goal_pair", "transition_window",
        "coverage", "integration",
    )
    SOFT_TIMEOUT_STAGES = (
        "frozen_context", "goal_pair", "transition_window",
    )
    STATIC_CHORD_STAGES = (
        "chord_reach", "chord_fine_reach", "static_chord")
    GOAL_PAIR_PHASES = ("retention", "mixed", "full")
    BRIDGE_WEIGHTED_KEYS = {
        "f1": "f1_l",
        "wrong": "wrong_press_rate",
        "sustain": "sustain_hold_rate",
        "event_success": "sustain_event_success_rate",
        "event_count": "sustain_event_count",
        "dropout": "press_dropout_rate",
        "failure": "failure_termination",
    }
    BRIDGE_COUNT_KEYS = (
        "no_press_correct_count",
        "no_press_evidence_count",
    ) + tuple(
        name
        for finger in range(1, 5)
        for name in (
            f"press_finger_{finger}_success",
            f"press_finger_{finger}_count",
        )
    )
    BRIDGE_METRIC_KEYS = (
        "episodes", "f1", "finger_min", "no_press", "wrong",
        "sustain", "event_success", "event_count", "dropout", "failure",
    )
    BRIDGE_FINGER_RATE_KEYS = tuple(
        f"finger_{finger}_rate" for finger in range(1, 5))
    LEGACY_STAGE_MAP = {
        "finger_articulation": "isolated_press",
        "wrist_articulation": "isolated_press",
        "elbow_articulation": "integrated_press",
        "static_press": "integrated_press",
    }
    PRE_CHORD_SCHEMA_LATE_STAGES = {
        "static_chord", "frozen_context", "goal_pair", "transition_window",
        "coverage", "integration", "full_song",
    }
    PRE_CONTEXT_SCHEMA_LATE_STAGES = {
        "transition_window", "coverage", "integration", "full_song",
    }
    PRE_INTERPOLATION_SCHEMA_LATE_STAGES = {
        "frozen_context", "goal_pair", "transition_window",
        "coverage", "integration", "full_song",
    }

    @classmethod
    def migrate_stage(cls, stage, source_schema=1):
        if stage is None:
            return None
        source_schema = int(source_schema)
        if stage == "goal_pair" and source_schema < 4:
            stage = "transition_window"
        stage = cls.LEGACY_STAGE_MAP.get(stage, stage)
        if (source_schema < 2
                and stage in cls.PRE_CHORD_SCHEMA_LATE_STAGES):
            return "chord_reach"
        if (source_schema == 2
                and stage in cls.PRE_CHORD_SCHEMA_LATE_STAGES):
            return "chord_fine_reach"
        if (source_schema == 3
                and stage in cls.PRE_CONTEXT_SCHEMA_LATE_STAGES):
            return "frozen_context"
        if (source_schema == 4
                and stage in cls.PRE_INTERPOLATION_SCHEMA_LATE_STAGES):
            return "frozen_context"
        return stage

    def __init__(self, config=FingertipApproachCurriculumConfig(),
                 forced_stage=None):
        self.config = config
        forced_stage = self.LEGACY_STAGE_MAP.get(forced_stage, forced_stage)
        if forced_stage is not None and forced_stage not in self.STAGES:
            raise ValueError(f"unknown forced curriculum stage: {forced_stage}")
        self.forced_stage = forced_stage
        self.stage = forced_stage or "coarse_reach"
        self.stage_iteration = 0
        self.total_iteration = 0
        self.stalled = False
        self.forced_advance_count = 0
        self.last_forced_advance_from = ""
        self.forced_advance = False
        self.chord_focus_index = 0
        self.chord_focus_iteration = 0
        self.chord_focus_total_iteration = 0
        self.chord_focus_count = 0
        self.chord_available_sets = ()
        self.chord_unresolved_signatures = []
        self.chord_focus_cycle = 0
        self.chord_catalog_min_duration_frames = 0
        self.chord_catalog_static_run_count = 0
        self.chord_catalog_transient_run_count = 0
        self.chord_catalog_transient_sets = ()
        self.chord_phase_evidence = {}
        self.skipped_stages = []
        self.transition_difficulty_level = 0
        self.frozen_context_final_applied = False
        self.frozen_context_focus_finger = 0
        self.frozen_context_focus_evidence = (
            self._empty_frozen_context_focus_evidence())
        self.required_song_fingers = ()
        self.goal_pair_phase = "retention"
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_focus_finger = 0
        self.goal_pair_focus_iteration = 0
        self.goal_pair_focus_scores = [None] * 4
        self.goal_pair_incoming_fingers = ()
        self.goal_pair_mastered_fingers = [False] * 4
        self.goal_pair_mastery_streaks = [0] * 4
        self.goal_pair_mastery_fail_streaks = [0] * 4
        self.goal_pair_phase_timeout_count = 0
        self.goal_pair_recovery_active = False
        self.goal_pair_recovery_iteration = 0
        self.goal_pair_recovery_good_windows = 0
        self.goal_pair_recovery_count = 0
        self.goal_pair_recovery_reason = ""
        self.goal_pair_phase_baseline = {}
        self.goal_pair_phase_baseline_label = ""
        self.goal_pair_recovery_failures = ()
        self.goal_pair_recovery_rollback = False
        self.goal_pair_recovery_rollback_count = 0
        self.goal_pair_last_recovery_rollback = ""
        self.goal_pair_phase_evidence = (
            self._empty_goal_pair_phase_evidence())
        self.recent = deque(maxlen=config.promotion_windows)
        self.bridge_windows = deque(
            maxlen=config.bridge_promotion_windows)
        self.bridge_accumulator = self._empty_bridge_accumulator()
        self.bridge_last_metrics = {}
        self.stage_entry_baseline = {}
        self.stage_entry_baseline_source = ""
        self.regression_bad_windows = 0
        self.regression_hold = False
        self.regression_metrics = ()

    @classmethod
    def _empty_bridge_accumulator(cls):
        accumulator = {"episodes": 0.0}
        accumulator.update({
            f"{name}_sum": 0.0
            for name in cls.BRIDGE_WEIGHTED_KEYS
        })
        accumulator.update({
            name: 0.0 for name in cls.BRIDGE_COUNT_KEYS
        })
        return accumulator

    @staticmethod
    def _empty_frozen_context_focus_evidence():
        evidence = {}
        for finger in range(1, 5):
            evidence.update({
                f"finger_{finger}_press_success": 0.0,
                f"finger_{finger}_press_count": 0.0,
                f"finger_{finger}_distance_sum": 0.0,
                f"finger_{finger}_distance_count": 0.0,
            })
        return evidence

    def _reset_frozen_context_focus_evidence(self):
        self.frozen_context_focus_evidence = (
            self._empty_frozen_context_focus_evidence())

    @staticmethod
    def _empty_chord_phase_row():
        return {
            "target": 0.0,
            "success": 0.0,
            "p90_sum": 0.0,
            "alignment_sum": 0.0,
            "geometry_weight": 0.0,
        }

    def _reset_chord_phase_evidence(self):
        self.chord_phase_evidence = {}

    @staticmethod
    def _empty_goal_pair_phase_evidence():
        evidence = {
            "preservation_count": 0.0,
            "preservation_sum": 0.0,
        }
        for finger in range(1, 5):
            evidence.update({
                f"rehearsal_{finger}_count": 0.0,
                f"rehearsal_{finger}_success_sum": 0.0,
                f"rehearsal_{finger}_distance_sum": 0.0,
                f"rehearsal_{finger}_hold_sum": 0.0,
                f"rehearsal_{finger}_dropout_sum": 0.0,
                f"rehearsal_{finger}_wrong_sum": 0.0,
                f"full_song_{finger}_count": 0.0,
                f"full_song_{finger}_success_sum": 0.0,
                f"full_song_{finger}_distance_sum": 0.0,
                f"full_song_{finger}_hold_sum": 0.0,
                f"full_song_{finger}_dropout_sum": 0.0,
                f"full_song_{finger}_wrong_sum": 0.0,
                f"transition_{finger}_next_count": 0.0,
                f"transition_{finger}_target_count": 0.0,
                f"transition_{finger}_success_sum": 0.0,
                f"transition_{finger}_distance_sum": 0.0,
                f"transition_{finger}_progress_sum": 0.0,
                f"transition_{finger}_wrong_count": 0.0,
                f"transition_{finger}_wrong_sum": 0.0,
            })
        return evidence

    def _reset_goal_pair_phase_evidence(self):
        self.goal_pair_phase_evidence = (
            self._empty_goal_pair_phase_evidence())

    def _reset_goal_pair_finger_evidence(self, finger):
        empty = self._empty_goal_pair_phase_evidence()
        marker = f"_{int(finger)}_"
        for key in self.goal_pair_phase_evidence:
            if marker in key:
                self.goal_pair_phase_evidence[key] = empty[key]

    def _reset_goal_pair_global_evidence(self):
        self.goal_pair_phase_evidence["preservation_count"] = 0.0
        self.goal_pair_phase_evidence["preservation_sum"] = 0.0

    def _reset_goal_pair_mastery(self):
        self.goal_pair_mastered_fingers = [False] * 4
        self.goal_pair_mastery_streaks = [0] * 4
        self.goal_pair_mastery_fail_streaks = [0] * 4
        self.goal_pair_focus_scores = [None] * 4
        self._reset_goal_pair_phase_evidence()

    def load_context(self, context):
        source_schema = int(
            context.get("curriculum_schema_version", 1))
        self.skipped_stages = (
            [str(value) for value in context.get(
                "curriculum_skipped_stages", ())]
            if source_schema >= self.STATIC_CHORD_CATALOG_SCHEMA_VERSION
            else [])
        self.chord_catalog_min_duration_frames = max(0, int(context.get(
            "curriculum_chord_catalog_min_duration_frames", 0)))
        self.chord_catalog_static_run_count = max(0, int(context.get(
            "curriculum_chord_catalog_static_run_count", 0)))
        self.chord_catalog_transient_run_count = max(0, int(context.get(
            "curriculum_chord_catalog_transient_run_count", 0)))
        self.chord_catalog_transient_sets = tuple(
            tuple(int(value) for value in finger_set)
            for finger_set in context.get(
                "curriculum_chord_catalog_transient_sets", ()))
        source_stage = context.get("curriculum_stage")
        stage = self.migrate_stage(source_stage, source_schema)
        legacy_stage = (
            stage != source_stage
            or (source_schema == 4
                and source_stage
                in self.PRE_INTERPOLATION_SCHEMA_LATE_STAGES))
        legacy_goal_pair_phase = (
            stage == "goal_pair"
            and source_schema < self.GOAL_PAIR_PHASE_SCHEMA_VERSION)
        self.frozen_context_final_applied = False
        self.frozen_context_focus_finger = 0
        self._reset_frozen_context_focus_evidence()
        self.goal_pair_phase = "retention"
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_focus_finger = 0
        self.goal_pair_focus_iteration = 0
        self.goal_pair_incoming_fingers = ()
        self.goal_pair_phase_timeout_count = 0
        self.goal_pair_recovery_active = False
        self.goal_pair_recovery_iteration = 0
        self.goal_pair_recovery_good_windows = 0
        self.goal_pair_recovery_count = 0
        self.goal_pair_recovery_reason = ""
        self.goal_pair_phase_baseline = {}
        self.goal_pair_phase_baseline_label = ""
        self.goal_pair_recovery_failures = ()
        self.goal_pair_recovery_rollback = False
        self.goal_pair_recovery_rollback_count = 0
        self.goal_pair_last_recovery_rollback = ""
        self._reset_goal_pair_mastery()
        self._reset_chord_phase_evidence()
        self.bridge_windows.clear()
        self.bridge_accumulator = self._empty_bridge_accumulator()
        self.bridge_last_metrics = {}
        self.stage_entry_baseline = {}
        self.stage_entry_baseline_source = ""
        self.regression_bad_windows = 0
        self.regression_hold = False
        self.regression_metrics = ()
        restore_saved_stage = (
            stage in self.STAGES
            and (self.forced_stage is None
                 or self.forced_stage == stage))
        if restore_saved_stage:
            self.stage = self.forced_stage or stage
            static_chord_catalog_migration = (
                source_schema < self.STATIC_CHORD_CATALOG_SCHEMA_VERSION
                and stage in self.STATIC_CHORD_STAGES)
            self.stage_iteration = (
                0 if (legacy_stage or legacy_goal_pair_phase
                      or static_chord_catalog_migration
                      or (source_schema < 3
                          and stage == "chord_fine_reach"))
                else int(context.get("curriculum_stage_iteration", 0)))
            self.total_iteration = int(context.get("curriculum_total_iteration", 0))
            self.stalled = (
                False if (legacy_stage or legacy_goal_pair_phase)
                else bool(context.get("curriculum_stalled", False)))
            self.forced_advance_count = int(
                context.get("curriculum_forced_advance_count", 0))
            self.last_forced_advance_from = str(
                context.get("curriculum_last_forced_advance_from", ""))
            if source_schema >= 3:
                if static_chord_catalog_migration:
                    self.chord_focus_index = 0
                    self.chord_focus_iteration = 0
                    self.chord_focus_total_iteration = 0
                    self.chord_focus_cycle = 0
                    self.chord_available_sets = ()
                    self.chord_focus_count = 0
                    self.chord_unresolved_signatures = []
                else:
                    self.chord_focus_index = int(
                        context.get("curriculum_chord_focus_index", 0))
                    self.chord_focus_iteration = int(
                        context.get("curriculum_chord_focus_iteration", 0))
                    self.chord_focus_total_iteration = int(
                        context.get(
                            "curriculum_chord_focus_total_iteration", 0))
                    self.chord_focus_cycle = int(
                        context.get("curriculum_chord_focus_cycle", 0))
                    self.chord_available_sets = tuple(
                        tuple(int(value) for value in finger_set)
                        for finger_set in context.get(
                            "curriculum_chord_available_sets", ()))
                    self.chord_focus_count = len(self.chord_available_sets)
                    self.chord_unresolved_signatures = [
                        int(value) for value in context.get(
                            "curriculum_chord_unresolved_signatures", ())]
                self.recent.clear()
                if (not legacy_stage and not legacy_goal_pair_phase
                        and not static_chord_catalog_migration):
                    self.recent.extend(
                        float(value) for value in context.get(
                            "curriculum_recent", ()))
            if (source_schema >= self.CHORD_PHASE_EVIDENCE_SCHEMA_VERSION
                    and self.stage == "chord_fine_reach"
                    and not static_chord_catalog_migration):
                saved_evidence = context.get(
                    "curriculum_chord_phase_evidence", {})
                for signature, saved_row in saved_evidence.items():
                    row = self._empty_chord_phase_row()
                    if not isinstance(saved_row, dict):
                        continue
                    for key in row:
                        value = float(saved_row.get(key, 0.0))
                        if math.isfinite(value) and value >= 0.0:
                            row[key] = value
                    self.chord_phase_evidence[str(signature)] = row
            elif self.stage == "chord_fine_reach":
                self.chord_focus_iteration = 0
                self.stalled = False
                self.recent.clear()
            if source_schema >= 4 and self.stage == "transition_window":
                saved_level = int(context.get(
                    "curriculum_transition_difficulty_level",
                    self._transition_level_for_iteration(
                        self.stage_iteration)))
                self.transition_difficulty_level = min(
                    max(saved_level, 0),
                    len(self.config.transition_window_seconds) - 1)
            else:
                self.transition_difficulty_level = 0
            if (source_schema >= 5
                    and self.stage == "frozen_context"
                    and not legacy_stage):
                self.frozen_context_final_applied = bool(context.get(
                    "curriculum_frozen_context_final_applied", False))
            if source_schema < 6 and self.stage in self.BRIDGE_STAGES:
                self.recent.clear()
            if (source_schema >= 6
                    and not legacy_stage
                    and not legacy_goal_pair_phase):
                for metrics in context.get(
                        "curriculum_bridge_windows", ()):
                    restored = self._restore_bridge_metrics(metrics)
                    if restored:
                        self.bridge_windows.append(restored)
                saved_accumulator = context.get(
                    "curriculum_bridge_accumulator", {})
                accumulator = self._empty_bridge_accumulator()
                for key in accumulator:
                    value = float(saved_accumulator.get(key, 0.0))
                    if math.isfinite(value) and value >= 0.0:
                        accumulator[key] = value
                self.bridge_accumulator = accumulator
                self.bridge_last_metrics = self._restore_bridge_metrics(
                    context.get("curriculum_bridge_last_metrics", {}))
                self.stage_entry_baseline = self._restore_bridge_metrics(
                    context.get(
                        "curriculum_stage_entry_baseline", {}))
                self.stage_entry_baseline_source = str(context.get(
                    "curriculum_stage_entry_baseline_source", ""))
                self.regression_bad_windows = max(0, int(context.get(
                    "curriculum_regression_bad_windows", 0)))
                self.regression_hold = bool(context.get(
                    "curriculum_regression_hold", False))
                self.regression_metrics = tuple(
                    str(value) for value in context.get(
                        "curriculum_regression_metrics", ()))
            if (source_schema >= self.GOAL_PAIR_PHASE_SCHEMA_VERSION
                    and self.stage == "goal_pair"
                    and not legacy_stage
                    and not legacy_goal_pair_phase):
                phase = str(context.get(
                    "curriculum_goal_pair_phase", "retention"))
                if phase not in self.GOAL_PAIR_PHASES:
                    phase = "retention"
                self.goal_pair_phase = phase
                self.goal_pair_phase_iteration = max(0, int(context.get(
                    "curriculum_goal_pair_phase_iteration", 0)))
                maximum_mixed_level = (
                    len(self.config.goal_pair_mixed_transition_fractions) - 1)
                self.goal_pair_mixed_level = min(max(0, int(context.get(
                    "curriculum_goal_pair_mixed_level", 0))),
                    maximum_mixed_level)
                self.goal_pair_mixed_level_iteration = max(0, int(
                    context.get(
                        "curriculum_goal_pair_mixed_level_iteration", 0)))
                focus = int(context.get(
                    "curriculum_goal_pair_focus_finger", 0))
                self.goal_pair_focus_finger = (
                    focus if 1 <= focus <= 4 else 0)
                if source_schema >= 14:
                    self.goal_pair_focus_iteration = max(0, int(context.get(
                        "curriculum_goal_pair_focus_iteration", 0)))
                if source_schema >= 17:
                    saved_scores = context.get(
                        "curriculum_goal_pair_focus_scores", ())
                    if len(saved_scores) == 4:
                        restored_scores = []
                        for score in saved_scores:
                            if (not isinstance(score, (list, tuple))
                                    or len(score) != 3):
                                restored_scores.append(None)
                                continue
                            values = tuple(float(value) for value in score)
                            restored_scores.append(
                                values if all(map(math.isfinite, values))
                                else None)
                        self.goal_pair_focus_scores = restored_scores
                saved_evidence = context.get(
                    "curriculum_goal_pair_phase_evidence", {})
                restored_evidence = self._empty_goal_pair_phase_evidence()
                for key in restored_evidence:
                    value = float(saved_evidence.get(key, 0.0))
                    if math.isfinite(value) and value >= 0.0:
                        restored_evidence[key] = value
                self.goal_pair_phase_evidence = restored_evidence
                if source_schema >= 12:
                    mastered = context.get(
                        "curriculum_goal_pair_mastered_fingers", ())
                    streaks = context.get(
                        "curriculum_goal_pair_mastery_streaks", ())
                    if len(mastered) == 4:
                        self.goal_pair_mastered_fingers = [
                            bool(value) for value in mastered]
                    if len(streaks) == 4:
                        self.goal_pair_mastery_streaks = [
                            max(0, int(value)) for value in streaks]
                    self.goal_pair_phase_timeout_count = max(0, int(
                        context.get(
                            "curriculum_goal_pair_phase_timeout_count", 0)))
                    if source_schema >= 13:
                        fail_streaks = context.get(
                            "curriculum_goal_pair_mastery_fail_streaks", ())
                        if len(fail_streaks) == 4:
                            self.goal_pair_mastery_fail_streaks = [
                                max(0, int(value))
                                for value in fail_streaks]
                    if source_schema >= 14:
                        self.goal_pair_recovery_active = bool(context.get(
                            "curriculum_goal_pair_recovery", False))
                        self.goal_pair_recovery_iteration = max(0, int(
                            context.get(
                                "curriculum_goal_pair_recovery_iteration", 0)))
                        self.goal_pair_recovery_good_windows = max(0, int(
                            context.get(
                                "curriculum_goal_pair_recovery_good_windows", 0)))
                        self.goal_pair_recovery_count = max(0, int(context.get(
                            "curriculum_goal_pair_recovery_count", 0)))
                        self.goal_pair_recovery_reason = str(context.get(
                            "curriculum_goal_pair_recovery_reason", ""))
                        if self.goal_pair_recovery_active:
                            self.regression_hold = True
                    elif self.regression_hold:
                        self.goal_pair_recovery_active = True
                        self.goal_pair_recovery_count = 1
                        self.goal_pair_recovery_reason = "migrated_regression"
                if source_schema >= 15:
                    self.goal_pair_phase_baseline = (
                        self._restore_bridge_metrics(context.get(
                            "curriculum_goal_pair_phase_baseline", {})))
                    self.goal_pair_phase_baseline_label = str(context.get(
                        "curriculum_goal_pair_phase_baseline_label", ""))
                    self.goal_pair_recovery_failures = tuple(
                        str(value) for value in context.get(
                            "curriculum_goal_pair_recovery_failures", ()))
                    self.goal_pair_recovery_rollback_count = max(0, int(
                        context.get(
                            "curriculum_goal_pair_recovery_rollback_count", 0)))
                    self.goal_pair_last_recovery_rollback = str(context.get(
                        "curriculum_goal_pair_last_recovery_rollback", ""))
                elif self.bridge_last_metrics:
                    self.goal_pair_phase_baseline = dict(
                        self.bridge_last_metrics)
                    self.goal_pair_phase_baseline_label = (
                        self._goal_pair_phase_label())
                if source_schema < 25 and self.goal_pair_recovery_active:
                    self.goal_pair_recovery_iteration = 0
                    self.goal_pair_recovery_good_windows = 0
                    self.goal_pair_focus_finger = 0
                    self.goal_pair_focus_iteration = 0
            if (source_schema >= 13
                    and self.stage == "frozen_context"
                    and not legacy_stage):
                focus = int(context.get(
                    "curriculum_frozen_context_focus_finger", 0))
                self.frozen_context_focus_finger = (
                    focus if 1 <= focus <= 4 else 0)
                saved_evidence = context.get(
                    "curriculum_frozen_context_focus_evidence", {})
                restored = self._empty_frozen_context_focus_evidence()
                for key in restored:
                    value = float(saved_evidence.get(key, 0.0))
                    if math.isfinite(value) and value >= 0.0:
                        restored[key] = value
                self.frozen_context_focus_evidence = restored

    @staticmethod
    def _finger_set_signature(finger_set):
        return sum(1 << (int(finger) - 1) for finger in finger_set)

    def _chord_focus_label(self):
        if self.stage != "chord_fine_reach":
            return ""
        if 0 <= self.chord_focus_index < self.chord_focus_count:
            return "+".join(
                str(value)
                for value in self.chord_available_sets[
                    self.chord_focus_index])
        return "mixed"

    def _bind_chord_catalog(self, goals):
        available = tuple(
            tuple(int(value) for value in finger_set)
            for finger_set in goals.practice_available_chord_finger_sets)
        if self.chord_available_sets and available != self.chord_available_sets:
            raise ValueError(
                "checkpoint chord focus catalog does not match the goal")
        self.chord_available_sets = available
        self.chord_focus_count = len(available)
        self.chord_catalog_min_duration_frames = int(getattr(
            goals, "static_chord_min_duration_frames", 0))
        self.chord_catalog_static_run_count = int(getattr(
            goals, "practice_static_chord_run_count", 0))
        self.chord_catalog_transient_run_count = int(getattr(
            goals, "practice_transient_chord_run_count", 0))
        self.chord_catalog_transient_sets = tuple(
            tuple(int(value) for value in finger_set)
            for finger_set in getattr(
                goals, "practice_transient_chord_finger_sets", ()))
        if self.chord_focus_index >= self.chord_focus_count:
            self.chord_focus_index = -1

    def _skip_unavailable_chord_stages(self):
        while (self.stage in self.STATIC_CHORD_STAGES
               and not self.chord_available_sets):
            if self.forced_stage is not None:
                raise ValueError(
                    "forced static-chord stage has no stable chord goals")
            skipped = self.stage
            self._promote()
            self.skipped_stages.append(skipped)

    def _transition_level_for_iteration(self, iteration):
        levels = len(self.config.transition_window_seconds)
        minimum = max(self.config.transition_min_iterations, 1)
        progress = min(max(int(iteration), 0) / float(minimum), 1.0)
        return min(int(progress * levels), levels - 1)

    def _transition_difficulty(self):
        levels = len(self.config.transition_window_seconds)
        level = min(max(self.transition_difficulty_level, 0), levels - 1)
        minimum = max(self.config.transition_min_iterations, 1)
        progress = (
            min(max(self.stage_iteration, 0) / float(minimum), 1.0)
            if self.stage == "transition_window" else 0.0)
        return {
            "level": level,
            "levels": levels,
            "progress": progress,
            "window_seconds": float(
                self.config.transition_window_seconds[level]),
            "max_changes": int(
                self.config.transition_max_changes[level]),
            "final_level": level == levels - 1,
        }

    def _frozen_context_difficulty(self):
        if self.stage != "frozen_context":
            progress = 1.0
        else:
            ramp_iteration = max(
                self.stage_iteration
                - self.config.frozen_context_context_warmup_iterations,
                0)
            progress = min(
                ramp_iteration
                / float(self.config.frozen_context_context_ramp_iterations),
                1.0)
        initial = self.config.frozen_context_initial_real_probability
        probability = initial + (1.0 - initial) * progress
        return {
            "progress": progress,
            "real_probability": probability,
            "final": progress >= 1.0,
        }

    def _accumulate_frozen_context_focus_stats(self, stats):
        evidence = self.frozen_context_focus_evidence
        fingers = self.required_song_fingers or range(1, 5)
        for finger in fingers:
            count = float(stats.get(
                f"press_finger_{finger}_count", 0.0))
            success = float(stats.get(
                f"press_finger_{finger}_success", 0.0))
            if (math.isfinite(count) and math.isfinite(success)
                    and count > 0.0 and 0.0 <= success <= count):
                evidence[f"finger_{finger}_press_count"] += count
                evidence[f"finger_{finger}_press_success"] += success
            distance_count = float(stats.get(
                f"curriculum_finger_{finger}_target_active_count", 0.0))
            distance = float(stats.get(
                f"curriculum_finger_{finger}_target_distance",
                float("nan")))
            if (math.isfinite(distance_count) and distance_count > 0.0
                    and math.isfinite(distance) and distance >= 0.0):
                evidence[f"finger_{finger}_distance_count"] += (
                    distance_count)
                evidence[f"finger_{finger}_distance_sum"] += (
                    distance * distance_count)

    def _reset_frozen_context_finger_evidence(self, finger):
        prefix = f"finger_{int(finger)}_"
        for key in self.frozen_context_focus_evidence:
            if key.startswith(prefix):
                self.frozen_context_focus_evidence[key] = 0.0

    def _sync_frozen_context_focus(self):
        if self.stage != "frozen_context":
            return False
        evidence = self.frozen_context_focus_evidence
        minimum = self.config.frozen_context_focus_min_evidence
        fingers = self.required_song_fingers or tuple(range(1, 5))
        evaluated = {}
        for finger in fingers:
            press_count = evidence[f"finger_{finger}_press_count"]
            distance_count = evidence[f"finger_{finger}_distance_count"]
            if min(press_count, distance_count) < minimum:
                continue
            press_rate = (
                evidence[f"finger_{finger}_press_success"] / press_count)
            distance = (
                evidence[f"finger_{finger}_distance_sum"] / distance_count)
            retained = (
                press_rate >= self.config.frozen_context_recovery_press_rate
                and distance <= self.config.frozen_context_recovery_distance)
            score = min(
                press_rate
                    / max(self.config.frozen_context_recovery_press_rate, 1e-6),
                self.config.frozen_context_recovery_distance
                    / max(distance, 1e-6))
            evaluated[finger] = (retained, score)
            self._reset_frozen_context_finger_evidence(finger)
        failed = {
            finger: result[1]
            for finger, result in evaluated.items()
            if not result[0]
        }
        current = self.frozen_context_focus_finger
        if failed:
            selected = min(failed, key=failed.get)
        elif current > 0 and current not in evaluated:
            selected = current
        else:
            selected = 0
        changed = selected != current
        if changed:
            self.frozen_context_focus_finger = selected
            self.recent.clear()
            self._reset_bridge_evidence(reset_regression=True)
            self.stalled = False
        return changed

    def _goal_pair_level(self):
        return min(
            max(int(self.goal_pair_mixed_level), 0),
            len(self.config.goal_pair_mixed_transition_fractions) - 1)

    def _goal_pair_difficulty(self):
        phase = (
            self.goal_pair_phase
            if self.goal_pair_phase in self.GOAL_PAIR_PHASES
            else "retention")
        level = -1
        if phase == "retention":
            rehearsal_probability = (
                self.config.goal_pair_retention_rehearsal_probability)
            focus_probability = (
                self.config.goal_pair_retention_focus_probability)
            sequence_probability = 0.0
            sequence_max_events = 2
        elif phase == "mixed":
            level = self._goal_pair_level()
            rehearsal_probability = (
                1.0
                - self.config.goal_pair_mixed_transition_fractions[level])
            focus_probability = (
                self.config.goal_pair_mixed_focus_probability)
            sequence_probability = (
                self.config.goal_pair_mixed_sequence_probabilities[level])
            sequence_max_events = (
                self.config.goal_pair_mixed_sequence_max_events[level])
        else:
            rehearsal_probability = (
                self.config.goal_pair_rehearsal_probability)
            focus_probability = 0.0
            sequence_probability = (
                self.config.goal_pair_full_sequence_probability)
            sequence_max_events = (
                self.config.goal_pair_full_sequence_max_events)
        phase_index = self.GOAL_PAIR_PHASES.index(phase)
        recovery = bool(self.goal_pair_recovery_active)
        full_song_fraction = (
            self.config.goal_pair_sequence_full_song_fraction)
        uncovered_pose_probability = (
            self.config.goal_pair_uncovered_pose_probability)
        if recovery:
            rehearsal_probability = (
                self.config.goal_pair_recovery_rehearsal_probability)
            sequence_probability = (
                self.config.goal_pair_recovery_sequence_probability)
            sequence_max_events = (
                self.config.goal_pair_recovery_sequence_max_events)
            full_song_fraction = (
                self.config.goal_pair_recovery_full_song_fraction)
            uncovered_pose_probability = (
                self.config.goal_pair_recovery_uncovered_pose_probability)
            focus_probability = max(
                focus_probability,
                self.config.goal_pair_timeout_focus_probability)
        preview_only = (
            phase == "mixed"
            and not recovery
            and level < self.config.goal_pair_preview_levels)
        return {
            "phase": phase,
            "phase_index": phase_index,
            "phase_iteration": int(self.goal_pair_phase_iteration),
            "progress": phase_index / float(len(self.GOAL_PAIR_PHASES) - 1),
            "rehearsal_probability": float(rehearsal_probability),
            "focus_finger": int(self.goal_pair_focus_finger),
            "focus_probability": (
                float(focus_probability)
                if self.goal_pair_focus_finger > 0 else 0.0),
            "recovery": bool(recovery),
            "mixed_level": (
                int(self.goal_pair_mixed_level)
                if phase == "mixed" else -1),
            "mixed_levels":
                len(self.config.goal_pair_mixed_transition_fractions),
            "mixed_level_iteration": (
                int(self.goal_pair_mixed_level_iteration)
                if phase == "mixed" else 0),
            "preview_only": bool(preview_only),
            "focus_lateral_exploration_std": float(
                self.config.goal_pair_focus_lateral_exploration_std),
            "sequence_probability": float(sequence_probability),
            "sequence_duration_frames": int(
                self.config.goal_pair_sequence_duration_frames),
            "sequence_max_events": int(sequence_max_events),
            "sequence_full_song_fraction": float(
                full_song_fraction),
            "uncovered_pose_probability": float(
                uncovered_pose_probability),
            "final": (
                phase == "full"
                and self.goal_pair_phase_iteration
                    >= self.config.goal_pair_full_min_iterations),
        }

    def _sync_transition_difficulty(self):
        if self.stage != "transition_window":
            return False
        if self.regression_hold:
            return False
        level = self._transition_level_for_iteration(self.stage_iteration)
        changed = level != self.transition_difficulty_level
        if changed:
            self.transition_difficulty_level = level
            self.recent.clear()
            self._reset_bridge_evidence(reset_regression=True)
            self.stalled = False
        return changed

    def _duration(self):
        if self.stage in ("coarse_reach", "fine_reach"):
            return 120
        if self.stage in ("chord_reach", "chord_fine_reach"):
            return 180
        if self.stage == "static_chord":
            return 150
        if self.stage == "frozen_context":
            return self.config.frozen_context_duration_frames
        if self.stage == "goal_pair":
            return self.config.goal_pair_duration_frames
        if self.stage == "transition_window":
            difficulty = self._transition_difficulty()
            return max(1, int(round(
                difficulty["window_seconds"] * 60.0)))
        return 180

    def state(self):
        probability = 0.0
        progress = 0.0
        if self.stage == "coverage":
            probability = 1.0
        elif self.stage == "frozen_context":
            progress = self._frozen_context_difficulty()["progress"]
        elif self.stage == "goal_pair":
            progress = self._goal_pair_difficulty()["progress"]
        elif self.stage == "integration":
            duration = max(self.config.integration_iterations, 1)
            progress = min(self.stage_iteration / float(duration), 1.0)
            probability = 1.0 - progress
        elif self.stage == "transition_window":
            progress = self._transition_difficulty()["progress"]
        elif self.stage == "full_song":
            progress = 1.0
        transition = self._transition_difficulty()
        frozen_context = self._frozen_context_difficulty()
        goal_pair = self._goal_pair_difficulty()
        aggregated_goal_pair = self._goal_pair_aggregated_stats({})
        chord_evidence_summary = {}
        for signature, row in self.chord_phase_evidence.items():
            target = float(row.get("target", 0.0))
            success = float(row.get("success", 0.0))
            prefix = f"curriculum_chord_set_{signature}_evidence"
            chord_evidence_summary[f"{prefix}_episodes"] = target
            chord_evidence_summary[f"{prefix}_success_rate"] = (
                success / target if target > 0.0 else -1.0)
        return {
            "curriculum_schema_version": self.SCHEMA_VERSION,
            "curriculum_stage": self.stage,
            "curriculum_stage_iteration": int(self.stage_iteration),
            "curriculum_total_iteration": int(self.total_iteration),
            "curriculum_random_start_probability": float(probability),
            "curriculum_stage_progress": float(progress),
            "curriculum_stalled": bool(self.stalled),
            "curriculum_forced_advance": bool(self.forced_advance),
            "curriculum_forced_advance_count":
                int(self.forced_advance_count),
            "curriculum_last_forced_advance_from":
                self.last_forced_advance_from,
            "curriculum_chord_focus_count": int(self.chord_focus_count),
            "curriculum_chord_focus_index": int(self.chord_focus_index),
            "curriculum_chord_focus_iteration":
                int(self.chord_focus_iteration),
            "curriculum_chord_focus_total_iteration":
                int(self.chord_focus_total_iteration),
            "curriculum_chord_focus_label": self._chord_focus_label(),
            "curriculum_chord_focus_cycle": int(self.chord_focus_cycle),
            "curriculum_chord_max_cycles": int(
                self.config.chord_fine_max_cycles),
            "curriculum_chord_focus_probability":
                float(self.config.chord_fine_focus_probability),
            "curriculum_chord_available_sets": [
                list(finger_set)
                for finger_set in self.chord_available_sets],
            "curriculum_chord_unresolved_signatures": list(
                self.chord_unresolved_signatures),
            "curriculum_chord_phase_evidence": {
                signature: dict(row)
                for signature, row in self.chord_phase_evidence.items()
            },
            "curriculum_chord_phase_evidence_required": int(
                self.config.chord_fine_min_phase_episodes),
            **chord_evidence_summary,
            "curriculum_chord_catalog_min_duration_frames": int(
                self.chord_catalog_min_duration_frames),
            "curriculum_chord_catalog_static_run_count": int(
                self.chord_catalog_static_run_count),
            "curriculum_chord_catalog_transient_run_count": int(
                self.chord_catalog_transient_run_count),
            "curriculum_chord_catalog_transient_sets": [
                list(finger_set)
                for finger_set in self.chord_catalog_transient_sets],
            "curriculum_skipped_stages": list(self.skipped_stages),
            "curriculum_transition_difficulty_level":
                int(transition["level"]),
            "curriculum_transition_difficulty_levels":
                int(transition["levels"]),
            "curriculum_transition_difficulty_progress":
                float(transition["progress"]),
            "curriculum_transition_window_seconds":
                float(transition["window_seconds"]),
            "curriculum_transition_max_changes":
                int(transition["max_changes"]),
            "curriculum_transition_final_level":
                bool(transition["final_level"]),
            "curriculum_frozen_context_progress":
                float(frozen_context["progress"]),
            "curriculum_frozen_context_real_probability":
                float(frozen_context["real_probability"]),
            "curriculum_frozen_context_final":
                bool(frozen_context["final"]),
            "curriculum_frozen_context_final_applied":
                bool(self.frozen_context_final_applied),
            "curriculum_frozen_context_focus_finger": (
                int(self.frozen_context_focus_finger)
                if self.stage == "frozen_context" else 0),
            "curriculum_frozen_context_focus_probability": (
                float(self.config.frozen_context_focus_probability)
                if self.stage == "frozen_context"
                and self.frozen_context_focus_finger > 0 else 0.0),
            "curriculum_frozen_context_focus_evidence":
                dict(self.frozen_context_focus_evidence),
            "curriculum_goal_pair_rehearsal_probability":
                (float(goal_pair["rehearsal_probability"])
                 if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_phase": (
                goal_pair["phase"] if self.stage == "goal_pair" else ""),
            "curriculum_goal_pair_phase_index": (
                int(goal_pair["phase_index"])
                if self.stage == "goal_pair" else -1),
            "curriculum_goal_pair_phase_iteration": (
                int(goal_pair["phase_iteration"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_mixed_level": (
                int(goal_pair["mixed_level"])
                if self.stage == "goal_pair" else -1),
            "curriculum_goal_pair_mixed_levels": (
                int(goal_pair["mixed_levels"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_mixed_level_iteration": (
                int(goal_pair["mixed_level_iteration"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_preview_only": (
                bool(goal_pair["preview_only"])
                if self.stage == "goal_pair" else False),
            "curriculum_goal_pair_focus_lateral_exploration_std": (
                float(goal_pair["focus_lateral_exploration_std"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_focus_finger": (
                int(goal_pair["focus_finger"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_focus_iteration": (
                int(self.goal_pair_focus_iteration)
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_focus_scores": [
                list(score) if score is not None else None
                for score in self.goal_pair_focus_scores],
            "curriculum_goal_pair_focus_probability": (
                float(goal_pair["focus_probability"])
                 if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_recovery": (
                bool(goal_pair["recovery"])
                if self.stage == "goal_pair" else False),
            "curriculum_goal_pair_recovery_iteration": (
                int(self.goal_pair_recovery_iteration)
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_recovery_max_iterations":
                int(self.config.goal_pair_recovery_max_iterations),
            "curriculum_goal_pair_recovery_good_windows": (
                int(self.goal_pair_recovery_good_windows)
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_recovery_count":
                int(self.goal_pair_recovery_count),
            "curriculum_goal_pair_recovery_reason": (
                self.goal_pair_recovery_reason
                if self.stage == "goal_pair" else ""),
            "curriculum_goal_pair_recovery_failures": (
                list(self.goal_pair_recovery_failures)
                if self.stage == "goal_pair" else []),
            "curriculum_goal_pair_phase_baseline": (
                dict(self.goal_pair_phase_baseline)
                if self.stage == "goal_pair" else {}),
            "curriculum_goal_pair_phase_baseline_label": (
                self.goal_pair_phase_baseline_label
                if self.stage == "goal_pair" else ""),
            "curriculum_goal_pair_phase_baseline_warmup_remaining": (
                max(
                    0,
                    int(self.config.goal_pair_phase_baseline_warmup_iterations)
                    - self._goal_pair_phase_age())
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_recovery_rollback": (
                bool(self.goal_pair_recovery_rollback)),
            "curriculum_goal_pair_recovery_rollback_count":
                int(self.goal_pair_recovery_rollback_count),
            "curriculum_goal_pair_last_recovery_rollback": (
                self.goal_pair_last_recovery_rollback),
            "curriculum_goal_pair_sequence_probability": (
                float(goal_pair["sequence_probability"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_sequence_duration_frames": (
                int(goal_pair["sequence_duration_frames"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_sequence_max_events": (
                int(goal_pair["sequence_max_events"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_sequence_full_song_fraction": (
                float(goal_pair["sequence_full_song_fraction"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_uncovered_pose_probability": (
                float(goal_pair["uncovered_pose_probability"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_recovery_song_ready": (
                self._goal_pair_recovery_song_ready(
                    aggregated_goal_pair)
                if self.stage == "goal_pair" else False),
            "curriculum_goal_pair_final": (
                bool(goal_pair["final"])
                if self.stage == "goal_pair" else False),
            "curriculum_goal_pair_mastered_fingers":
                list(self.goal_pair_mastered_fingers),
            "curriculum_goal_pair_mastered_count":
                sum(self.goal_pair_mastered_fingers),
            "curriculum_goal_pair_mastery_streaks":
                list(self.goal_pair_mastery_streaks),
            "curriculum_goal_pair_mastery_fail_streaks":
                list(self.goal_pair_mastery_fail_streaks),
            "curriculum_goal_pair_phase_timeout_count":
                int(self.goal_pair_phase_timeout_count),
            "curriculum_goal_pair_phase_evidence":
                dict(self.goal_pair_phase_evidence),
            "curriculum_recent": list(self.recent),
            "curriculum_bridge_windows": [
                dict(metrics) for metrics in self.bridge_windows],
            "curriculum_bridge_accumulator":
                dict(self.bridge_accumulator),
            "curriculum_bridge_last_metrics":
                dict(self.bridge_last_metrics),
            "curriculum_stage_entry_baseline":
                dict(self.stage_entry_baseline),
            "curriculum_stage_entry_baseline_source":
                self.stage_entry_baseline_source,
            "curriculum_regression_bad_windows":
                int(self.regression_bad_windows),
            "curriculum_regression_hold":
                bool(self.regression_hold),
            "curriculum_regression_metrics":
                list(self.regression_metrics),
        }

    def apply(self, env):
        self.required_song_fingers = tuple(
            index + 1
            for index in getattr(
                env.goals, "practice_available_fingers", range(4)))
        self.goal_pair_incoming_fingers = tuple(
            int(finger) for finger in getattr(
                env.goals,
                "practice_goal_pair_available_incoming_fingers", ()))
        if self.stage in self.STATIC_CHORD_STAGES:
            self._bind_chord_catalog(env.goals)
            self._skip_unavailable_chord_stages()
        focus_changed = False
        if self.stage == "chord_fine_reach":
            focus_index = (
                self.chord_focus_index
                if 0 <= self.chord_focus_index < self.chord_focus_count
                else None)
            focus_changed = env.goals.set_chord_focus_index(
                focus_index,
                focus_probability=
                    self.config.chord_fine_focus_probability)
        else:
            focus_changed = env.goals.set_chord_focus_index(None)
        state = self.state()
        env.goals.set_random_start_probability(
            state["curriculum_random_start_probability"])
        if hasattr(env.goals, "set_transition_max_changes"):
            env.goals.set_transition_max_changes(
                state["curriculum_transition_max_changes"]
                if self.stage == "transition_window" else None)
        if hasattr(env.goals, "set_frozen_context_real_probability"):
            env.goals.set_frozen_context_real_probability(
                state["curriculum_frozen_context_real_probability"]
                if self.stage == "frozen_context" else 1.0)
        frozen_focus_changed = False
        if hasattr(env.goals, "set_frozen_context_focus"):
            frozen_focus = (
                state["curriculum_frozen_context_focus_finger"]
                if self.stage == "frozen_context"
                and state["curriculum_frozen_context_focus_finger"] > 0
                else None)
            frozen_focus_changed = env.goals.set_frozen_context_focus(
                frozen_focus,
                focus_probability=(
                    state["curriculum_frozen_context_focus_probability"]
                    if frozen_focus is not None else 1.0))
        if hasattr(env.goals, "set_goal_pair_rehearsal_probability"):
            env.goals.set_goal_pair_rehearsal_probability(
                state["curriculum_goal_pair_rehearsal_probability"])
        if hasattr(env.goals, "set_goal_pair_rehearsal_duration"):
            env.goals.set_goal_pair_rehearsal_duration(
                self.config.frozen_context_duration_frames)
        if hasattr(env.goals, "set_goal_pair_sequence_sampling"):
            env.goals.set_goal_pair_sequence_sampling(
                state["curriculum_goal_pair_sequence_probability"],
                duration_frames=
                    self.config.goal_pair_sequence_duration_frames,
                full_song_fraction=
                    state[
                        "curriculum_goal_pair_sequence_full_song_fraction"],
                max_events=
                    state["curriculum_goal_pair_sequence_max_events"]
                    if self.stage == "goal_pair" else 2)
        if hasattr(env.goals, "set_goal_pair_uncovered_pose_probability"):
            env.goals.set_goal_pair_uncovered_pose_probability(
                state[
                    "curriculum_goal_pair_uncovered_pose_probability"])
        if hasattr(env.goals, "set_goal_pair_preview_only"):
            env.goals.set_goal_pair_preview_only(
                state["curriculum_goal_pair_preview_only"])
        if hasattr(env, "set_goal_pair_action_assist"):
            env.set_goal_pair_action_assist(
                state["curriculum_goal_pair_preview_only"])
        if hasattr(env, "set_goal_pair_recovery_assist"):
            env.set_goal_pair_recovery_assist(
                state["curriculum_goal_pair_recovery"])
        if hasattr(env.goals, "set_goal_pair_transition_focus"):
            focus_probability = state[
                "curriculum_goal_pair_focus_probability"]
            focus_finger = (
                state["curriculum_goal_pair_focus_finger"]
                if self.stage == "goal_pair"
                and state["curriculum_goal_pair_focus_finger"] > 0
                and focus_probability > 0.0
                else None)
            env.goals.set_goal_pair_transition_focus(
                focus_finger,
                focus_probability=(
                    focus_probability
                    if focus_finger is not None else 1.0))
        reset_obs = env.set_curriculum_stage(
            self.stage,
            duration_frames=self._duration() if self.stage in self.PRACTICE_STAGES else 0,
            reset=True)
        frozen_final = (
            self.stage == "frozen_context"
            and bool(state["curriculum_frozen_context_final"]))
        if frozen_final and not self.frozen_context_final_applied:
            self.recent.clear()
            self._reset_bridge_evidence(reset_regression=True)
            self.stalled = False
            if reset_obs is None:
                reset_obs = env.reset()
            self.frozen_context_final_applied = True
        elif not frozen_final:
            self.frozen_context_final_applied = False
        if (reset_obs is None
                and (focus_changed or frozen_focus_changed)):
            reset_obs = env.reset()
        state = self.state()
        if reset_obs is not None:
            state["_reset_observation"] = reset_obs
        return state

    def _practice_limits(self):
        return {
            "coarse_reach": (self.config.coarse_min_iterations,
                             self.config.coarse_max_iterations),
            "fine_reach": (self.config.fine_min_iterations,
                           self.config.fine_max_iterations),
            "isolated_press": (
                self.config.isolated_press_min_iterations,
                self.config.isolated_press_max_iterations),
            "integrated_press": (
                self.config.integrated_press_min_iterations,
                self.config.integrated_press_max_iterations),
            "chord_reach": (
                self.config.chord_reach_min_iterations,
                self.config.chord_reach_max_iterations),
            "chord_fine_reach": (
                self.config.chord_fine_min_iterations,
                self.config.chord_fine_max_iterations),
            "static_chord": (
                self.config.static_chord_min_iterations,
                self.config.static_chord_max_iterations),
            "frozen_context": (
                self.config.frozen_context_min_iterations,
                self.config.frozen_context_max_iterations),
            "goal_pair": (
                self.config.goal_pair_min_iterations,
                self.config.goal_pair_max_iterations),
            "transition_window": (
                self.config.transition_min_iterations,
                self.config.transition_max_iterations),
        }[self.stage]

    def _minimum_evidence_episodes(self):
        return {
            "static_chord":
                self.config.static_chord_min_evidence_episodes,
            "frozen_context":
                self.config.frozen_context_min_evidence_episodes,
            "goal_pair":
                self.config.goal_pair_min_evidence_episodes,
            "transition_window":
                self.config.transition_min_evidence_episodes,
            "coverage":
                self.config.coverage_min_evidence_episodes,
            "integration":
                self.config.integration_min_evidence_episodes,
        }.get(self.stage, 0)

    def _has_minimum_stage_evidence(self, stats):
        minimum = self._minimum_evidence_episodes()
        if minimum <= 0 or "episodes" not in stats:
            return True
        episodes = float(stats.get("episodes", 0.0))
        return math.isfinite(episodes) and episodes >= minimum

    @classmethod
    def _restore_bridge_metrics(cls, values):
        if not isinstance(values, dict):
            return {}
        restored = {}
        for key in cls.BRIDGE_METRIC_KEYS:
            if key not in values:
                return {}
            value = float(values[key])
            if not math.isfinite(value):
                return {}
            restored[key] = value
        for key in cls.BRIDGE_FINGER_RATE_KEYS:
            if key not in values:
                continue
            value = float(values[key])
            if math.isfinite(value) and 0.0 <= value <= 1.0:
                restored[key] = value
        return restored

    def _reset_bridge_evidence(self, reset_regression=False):
        self.bridge_windows.clear()
        self.bridge_accumulator = self._empty_bridge_accumulator()
        self.bridge_last_metrics = {}
        if reset_regression:
            self.regression_bad_windows = 0
            self.regression_hold = False
            self.regression_metrics = ()

    def _bridge_row(self, stats):
        episodes = float(stats.get("episodes", 0.0))
        if not math.isfinite(episodes) or episodes <= 0.0:
            return None
        row = {"episodes": episodes}
        for name, source in self.BRIDGE_WEIGHTED_KEYS.items():
            value = float(stats.get(source, float("nan")))
            if not math.isfinite(value) or value < 0.0:
                return None
            row[name] = value
        for name in self.BRIDGE_COUNT_KEYS:
            value = float(stats.get(name, float("nan")))
            if not math.isfinite(value) or value < 0.0:
                return None
            row[name] = value
        return row

    def _finalize_bridge_window(self):
        accumulator = self.bridge_accumulator
        episodes = float(accumulator["episodes"])
        if episodes <= 0.0:
            return {}
        metrics = {
            name: float(accumulator[f"{name}_sum"]) / episodes
            for name in self.BRIDGE_WEIGHTED_KEYS
        }
        evidence = float(accumulator["no_press_evidence_count"])
        metrics["no_press"] = (
            float(accumulator["no_press_correct_count"]) / evidence
            if evidence > 0.0 else 1.0)
        required_fingers = (
            self.required_song_fingers
            or tuple(
                finger for finger in range(1, 5)
                if float(accumulator[
                    f"press_finger_{finger}_count"]) > 0.0))
        finger_rates = []
        for finger in required_fingers:
            count = float(accumulator[
                f"press_finger_{finger}_count"])
            if count <= 0.0:
                finger_rates = []
                break
            rate = (
                float(accumulator[
                    f"press_finger_{finger}_success"]) / count)
            finger_rates.append(rate)
            metrics[f"finger_{finger}_rate"] = rate
        metrics["finger_min"] = (
            min(finger_rates) if finger_rates else -1.0)
        metrics["episodes"] = episodes
        result = {
            key: float(metrics[key])
            for key in self.BRIDGE_METRIC_KEYS
        }
        result.update({
            key: float(metrics[key])
            for key in self.BRIDGE_FINGER_RATE_KEYS
            if key in metrics
        })
        return result

    def _goal_pair_phase_label(self):
        if self.goal_pair_phase == "mixed":
            return f"mixed:{int(self.goal_pair_mixed_level)}"
        return self.goal_pair_phase

    def _goal_pair_phase_age(self):
        if self.goal_pair_phase == "mixed":
            return int(self.goal_pair_mixed_level_iteration)
        return int(self.goal_pair_phase_iteration)

    def _reset_goal_pair_phase_baseline(self):
        self.goal_pair_phase_baseline = {}
        self.goal_pair_phase_baseline_label = ""

    def _regression_failures(self, metrics, baseline=None):
        baseline = self.stage_entry_baseline if baseline is None else baseline
        if not baseline:
            return ()
        failures = []
        if metrics["f1"] < baseline["f1"] - self.config.regression_f1_drop:
            failures.append("f1")
        if (metrics["no_press"]
                < baseline["no_press"]
                - self.config.regression_no_press_drop):
            failures.append("no_press")
        if (metrics["wrong"]
                > baseline["wrong"]
                + self.config.regression_wrong_press_increase):
            failures.append("wrong_press")
        if (metrics["event_success"]
                < baseline["event_success"]
                - self.config.regression_sustain_event_drop):
            failures.append("sustain_event")
        if (metrics["finger_min"]
                < baseline["finger_min"]
                - self.config.regression_per_finger_drop):
            failures.append("per_finger")
        baseline_failure = baseline.get("failure")
        if (baseline_failure is not None
                and metrics["failure"]
                    > baseline_failure
                    + self.config.regression_failure_increase):
            failures.append("failure")
        return tuple(failures)

    def _goal_pair_recovery_quality_failures(self, metrics):
        return self._regression_failures(
            metrics, self.goal_pair_phase_baseline)

    def _update_regression(self, metrics):
        if self.stage == "goal_pair" and self.goal_pair_recovery_active:
            failures = self._goal_pair_recovery_quality_failures(metrics)
            self.goal_pair_recovery_failures = failures
        elif self.stage == "goal_pair":
            label = self._goal_pair_phase_label()
            if (not self.goal_pair_phase_baseline
                    or self.goal_pair_phase_baseline_label != label):
                warmup = int(
                    self.config.goal_pair_phase_baseline_warmup_iterations)
                if self._goal_pair_phase_age() < warmup:
                    self.goal_pair_recovery_failures = ()
                    self.regression_metrics = ()
                    self.regression_bad_windows = 0
                    self.regression_hold = False
                    return
                self.goal_pair_phase_baseline = dict(metrics)
                self.goal_pair_phase_baseline_label = label
                self.goal_pair_recovery_failures = ()
                self.regression_metrics = ()
                self.regression_bad_windows = 0
                self.regression_hold = False
                return
            failures = self._regression_failures(
                metrics, self.goal_pair_phase_baseline)
            self.goal_pair_recovery_failures = ()
        else:
            failures = self._regression_failures(metrics)
        self.regression_metrics = failures
        if failures:
            self.regression_bad_windows += 1
            if self.goal_pair_recovery_active:
                self.goal_pair_recovery_good_windows = 0
        else:
            self.regression_bad_windows = 0
            if self.goal_pair_recovery_active:
                self.goal_pair_recovery_good_windows += 1
        if self.goal_pair_recovery_active:
            self.regression_hold = True
            return
        self.regression_hold = (
            self.regression_bad_windows
            >= self.config.regression_hold_windows)

    def _commit_bridge_window(self):
        metrics = self._finalize_bridge_window()
        self.bridge_accumulator = self._empty_bridge_accumulator()
        if not metrics:
            return False
        self.bridge_windows.append(metrics)
        self.bridge_last_metrics = dict(metrics)
        self._update_regression(metrics)
        return True

    def _accumulate_bridge_stats(self, stats):
        row = self._bridge_row(stats)
        if row is None:
            return 0
        target = float(self.config.bridge_window_episodes)
        remaining = float(row["episodes"])
        completed = 0
        while remaining > 1e-9:
            capacity = target - float(
                self.bridge_accumulator["episodes"])
            if capacity <= 1e-9:
                completed += int(self._commit_bridge_window())
                continue
            take = min(remaining, capacity)
            self.bridge_accumulator["episodes"] += take
            for name in self.BRIDGE_WEIGHTED_KEYS:
                self.bridge_accumulator[f"{name}_sum"] += (
                    row[name] * take)
            for name in self.BRIDGE_COUNT_KEYS:
                self.bridge_accumulator[name] += row[name] * take
            remaining -= take
            if self.bridge_accumulator["episodes"] >= target - 1e-9:
                completed += int(self._commit_bridge_window())
        return completed

    def _bridge_gate_passes(self, metrics, soft=False):
        metrics = self._restore_bridge_metrics(metrics)
        if not metrics:
            return False
        prefix = "bridge_soft_" if soft else "bridge_"
        thresholds = {
            "f1": getattr(self.config, f"{prefix}f1_rate"),
            "finger_min": getattr(
                self.config, f"{prefix}per_finger_press_rate"),
            "no_press": getattr(
                self.config, f"{prefix}no_press_accuracy"),
            "wrong": getattr(
                self.config, f"{prefix}wrong_press_rate"),
            "sustain": getattr(
                self.config, f"{prefix}sustain_hold_rate"),
            "event_success": getattr(
                self.config, f"{prefix}sustain_event_rate"),
            "dropout": getattr(
                self.config, f"{prefix}press_dropout_rate"),
            "failure": getattr(
                self.config, f"{prefix}failure_termination_rate"),
        }
        return (
            metrics["f1"] >= thresholds["f1"]
            and metrics["finger_min"] >= thresholds["finger_min"]
            and metrics["no_press"] >= thresholds["no_press"]
            and metrics["wrong"] <= thresholds["wrong"]
            and metrics["sustain"] >= thresholds["sustain"]
            and metrics["event_success"] >= thresholds["event_success"]
            and metrics["event_count"]
                >= self.config.song_min_sustain_events
            and metrics["dropout"] <= thresholds["dropout"]
            and metrics["failure"] <= thresholds["failure"]
        )

    def _bridge_windows_pass(self, soft=False):
        return (
            len(self.bridge_windows)
            == self.config.bridge_promotion_windows
            and all(
                self._bridge_gate_passes(metrics, soft=soft)
                for metrics in self.bridge_windows)
        )

    def _hard_timeout_quality_floor_passes(self):
        metrics = self.bridge_last_metrics
        if not metrics:
            return False
        if self.stage != "frozen_context":
            return (
                float(metrics.get("finger_min", -1.0))
                >= self.config.bridge_hard_timeout_min_per_finger_rate)
        return (
            float(metrics.get("finger_min", -1.0))
                >= self.config.frozen_context_hard_min_per_finger_rate
            and float(metrics.get("f1", -1.0))
                >= self.config.frozen_context_hard_min_f1_rate
            and float(metrics.get("no_press", -1.0))
                >= self.config.frozen_context_hard_min_no_press_accuracy
            and float(metrics.get("wrong", 1.0))
                <= self.config.frozen_context_hard_max_wrong_press_rate
            and float(metrics.get("sustain", -1.0))
                >= self.config.frozen_context_hard_min_sustain_hold_rate
            and float(metrics.get("event_success", -1.0))
                >= self.config.frozen_context_hard_min_sustain_event_rate
            and float(metrics.get("failure", 1.0))
                <= self.config.frozen_context_hard_max_failure_rate)

    def _frozen_context_evaluation_ready(self):
        if self.stage != "frozen_context":
            return True
        final_start = (
            self.config.frozen_context_context_warmup_iterations
            + self.config.frozen_context_context_ramp_iterations)
        return (
            self.frozen_context_final_applied
            and self._frozen_context_difficulty()["final"]
            and self.stage_iteration
                >= final_start
                + self.config.frozen_context_final_evaluation_iterations
        )

    @staticmethod
    def _catastrophic_free(stats):
        for name in ("nonfinite", "velocity_blowup"):
            rate = float(stats.get(name, 0.0))
            count = float(stats.get(f"{name}_count", 0.0))
            if (not math.isfinite(rate) or not math.isfinite(count)
                    or rate > 0.0 or count > 0.0):
                return False
        return True

    def _force_promote(self, reason):
        self.forced_advance = True
        self.forced_advance_count += 1
        self.last_forced_advance_from = str(reason)
        self._promote()

    def _thumb_contact_gate_passes(self, stats):
        if not self.config.thumb_contact_gate_enabled:
            return True
        support = float(stats.get("curriculum_thumb_support", -1.0))
        wrong = float(
            stats.get("curriculum_thumb_wrong_contact", 1.0))
        return (support >= self.config.thumb_support_rate
                and wrong <= self.config.thumb_wrong_contact_rate)

    def _thumb_geometry_gate_passes(self, stats):
        if not self.config.thumb_geometry_gate_enabled:
            return True
        readiness = float(stats.get(
            "curriculum_thumb_press_readiness", -1.0))
        return (
            math.isfinite(readiness)
            and readiness >= self.config.thumb_press_readiness_rate)

    def _promotion_sample(self, stats):
        if self.stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press",
                "chord_reach", "chord_fine_reach"):
            overall = float(stats.get("curriculum_success_rate", -1.0))
            if overall < 0.0:
                return -1.0
            per_finger = []
            for finger in range(1, 5):
                count = float(stats.get(f"curriculum_finger_{finger}_count", 0.0))
                if count > 0.0:
                    success = float(stats.get(
                        f"curriculum_finger_{finger}_success", 0.0))
                    per_finger.append(success / count)
            score = min([overall] + per_finger)
            p90 = float(stats.get("curriculum_p90_target_distance", float("inf")))
            if self.stage in ("coarse_reach", "chord_reach"):
                if p90 > 0.040:
                    return 0.0
            if self.stage == "fine_reach":
                alignment = float(stats.get("curriculum_cell_alignment_rate", 0.0))
                if p90 > 0.010 or alignment < 0.90:
                    return 0.0
            if self.stage == "chord_fine_reach":
                alignment = float(
                    stats.get("curriculum_cell_alignment_rate", 0.0))
                if (p90 > self.config.chord_fine_p90_distance
                        or alignment
                        < self.config.chord_fine_alignment_rate):
                    return 0.0
            if self.stage in ("isolated_press", "integrated_press"):
                quality = float(stats.get("curriculum_mean_position_quality", 0.0))
                if quality < 0.50:
                    return 0.0
            if self.stage == "isolated_press":
                arch = float(stats.get("curriculum_mean_arch_quality", 0.0))
                if arch < 0.65:
                    return 0.0
            if self.stage == "integrated_press":
                if not self._thumb_gate_passes(
                        stats, self.config.thumb_integrated_distance):
                    return 0.0
            if (self.config.thumb_contact_gate_enabled
                    and self.stage in ("coarse_reach", "fine_reach")):
                limit = (self.config.thumb_coarse_distance
                         if self.stage == "coarse_reach"
                         else self.config.thumb_fine_distance)
                if not self._thumb_gate_passes(stats, limit):
                    return 0.0
            return score
        if self.stage == "static_chord":
            return self._static_chord_performance_sample(stats)
        if self.stage in (
                "frozen_context", "goal_pair", "transition_window",
                "coverage", "integration"):
            return self._song_performance_sample(stats)
        return -1.0

    def _thumb_gate_passes(self, stats, distance_limit):
        if not self.config.thumb_contact_gate_enabled:
            return True
        distance = float(
            stats.get("curriculum_thumb_distance", float("inf")))
        return (distance <= distance_limit
                and self._thumb_contact_gate_passes(stats))

    def _song_performance_sample(self, stats):
        no_press_evidence = float(
            stats.get("no_press_evidence_count", -1.0))
        no_press_correct = float(
            stats.get("no_press_correct_count", -1.0))
        if no_press_evidence >= 0.0 and no_press_correct >= 0.0:
            no_press_accuracy = (
                no_press_correct / no_press_evidence
                if no_press_evidence > 0.0 else 1.0)
        else:
            no_press_accuracy = float(
                stats.get("no_press_accuracy", -1.0))
        values = {
            "f1": float(stats.get("f1_l", -1.0)),
            "no_press": no_press_accuracy,
            "wrong": float(stats.get("wrong_press_rate", -1.0)),
            "sustain": float(stats.get("sustain_hold_rate", -1.0)),
            "event_success": float(
                stats.get("sustain_event_success_rate", -1.0)),
            "event_count": float(stats.get("sustain_event_count", -1.0)),
        }
        if any(value < 0.0 for value in values.values()):
            return -1.0
        finger_rates = []
        required_fingers = (
            self._required_fingers_for_stage()
            or tuple(
                finger for finger in range(1, 5)
                if float(stats.get(
                    f"press_finger_{finger}_count", 0.0)) > 0.0))
        if not required_fingers:
            return -1.0
        for finger in required_fingers:
            count = float(stats.get(
                f"press_finger_{finger}_count", 0.0))
            if count <= 0.0:
                return -1.0
            success = float(stats.get(
                f"press_finger_{finger}_success", 0.0))
            finger_rates.append(success / count)
        passed = (
            values["f1"] >= self.config.song_f1_rate
            and min(finger_rates)
                >= self.config.song_per_finger_press_rate
            and values["no_press"] >= self.config.song_no_press_accuracy
            and values["wrong"] <= self.config.song_wrong_press_rate
            and values["sustain"] >= self.config.song_sustain_hold_rate
            and values["event_success"]
                >= self.config.song_sustain_hold_rate
            and values["event_count"] >= self.config.song_min_sustain_events
            and self._thumb_geometry_gate_passes(stats)
            and self._thumb_gate_passes(
                stats, self.config.thumb_integrated_distance)
        )
        return 1.0 if passed else 0.0

    def _required_fingers_for_stage(self):
        if self.stage == "static_chord" and self.chord_available_sets:
            return tuple(sorted({
                finger
                for finger_set in self.chord_available_sets
                for finger in finger_set
            }))
        return self.required_song_fingers

    def _static_chord_performance_sample(self, stats):
        song_sample = self._song_performance_sample(stats)
        if song_sample < 0.0:
            return -1.0
        chord_ready = float(stats.get("chord_ready_rate", -1.0))
        hold_quality = float(stats.get("chord_hold_quality", -1.0))
        precise_success = float(
            stats.get("curriculum_success_rate", -1.0))
        press_dropout = float(stats.get("press_dropout_rate", -1.0))
        if min(chord_ready, hold_quality, precise_success,
               press_dropout) < 0.0:
            return -1.0
        passed = (
            song_sample >= 1.0
            and chord_ready >= self.config.song_sustain_hold_rate
            and hold_quality >= self.config.song_sustain_hold_rate
            and precise_success >= self.config.promotion_success_rate
            and press_dropout <= self.config.song_press_dropout_rate
        )
        return 1.0 if passed else 0.0

    def _promote(self):
        previous = self.stage
        baseline = (
            dict(self.bridge_last_metrics)
            if previous in self.BRIDGE_STAGES
            and self.bridge_last_metrics else {})
        index = self.STAGES.index(self.stage)
        self.stage = self.STAGES[index + 1]
        self.stage_iteration = 0
        self.stalled = False
        self.recent.clear()
        self._reset_chord_phase_evidence()
        self._reset_bridge_evidence(reset_regression=True)
        self.stage_entry_baseline = baseline
        self.stage_entry_baseline_source = (
            previous if baseline else "")
        if self.stage == "chord_fine_reach":
            self.chord_focus_index = 0
            self.chord_focus_iteration = 0
            self.chord_focus_total_iteration = 0
            self.chord_focus_count = 0
            self.chord_available_sets = ()
            self.chord_unresolved_signatures = []
            self.chord_focus_cycle = 0
        elif previous == "chord_fine_reach":
            self.chord_focus_index = -1
            self.chord_focus_iteration = 0
            self.chord_focus_count = 0
            self.chord_available_sets = ()
        if self.stage == "transition_window":
            self.transition_difficulty_level = 0
        elif previous == "transition_window":
            self.transition_difficulty_level = (
                len(self.config.transition_window_seconds) - 1)
        if self.stage == "frozen_context":
            self.frozen_context_focus_finger = 0
            self._reset_frozen_context_focus_evidence()
        elif previous == "frozen_context":
            self.frozen_context_focus_finger = 0
            self._reset_frozen_context_focus_evidence()
        if self.stage == "goal_pair":
            self.goal_pair_phase = "retention"
            self.goal_pair_phase_iteration = 0
            self.goal_pair_mixed_level = 0
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_focus_finger = 0
            self.goal_pair_focus_iteration = 0
            self.goal_pair_phase_timeout_count = 0
            self.goal_pair_recovery_active = False
            self.goal_pair_recovery_iteration = 0
            self.goal_pair_recovery_good_windows = 0
            self.goal_pair_recovery_count = 0
            self.goal_pair_recovery_reason = ""
            self.goal_pair_phase_baseline = {}
            self.goal_pair_phase_baseline_label = ""
            self.goal_pair_recovery_failures = ()
            self.goal_pair_recovery_rollback = False
            self._reset_goal_pair_mastery()
        elif previous == "goal_pair":
            self.goal_pair_phase = "full"
            self.goal_pair_phase_iteration = 0
            self.goal_pair_mixed_level = (
                len(self.config.goal_pair_mixed_transition_fractions) - 1)
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_focus_finger = 0
            self.goal_pair_focus_iteration = 0
            self.goal_pair_recovery_active = False
            self.goal_pair_recovery_iteration = 0
            self.goal_pair_recovery_good_windows = 0
            self.goal_pair_recovery_reason = ""
            self.goal_pair_phase_baseline = {}
            self.goal_pair_phase_baseline_label = ""
            self.goal_pair_recovery_failures = ()
            self.goal_pair_recovery_rollback = False
            self._reset_goal_pair_mastery()
        if previous == "frozen_context":
            self.frozen_context_final_applied = False

    def _chord_set_rate(self, stats, signature):
        count = float(stats.get(
            f"curriculum_chord_set_{signature}_count", 0.0))
        if count <= 0.0:
            return -1.0
        success = float(stats.get(
            f"curriculum_chord_set_{signature}_success", 0.0))
        return success / count

    @staticmethod
    def _finite_nonnegative(value, default=0.0):
        value = float(value)
        return value if math.isfinite(value) and value >= 0.0 else default

    def _chord_set_episode_totals(self, stats, signature):
        prefix = f"chord_set_{signature}"
        target_key = f"{prefix}_target_episodes"
        success_key = f"{prefix}_success_episodes"
        if target_key in stats:
            target = self._finite_nonnegative(stats[target_key])
            success = self._finite_nonnegative(
                stats.get(success_key, 0.0))
            return min(success, target), target
        episodes = self._finite_nonnegative(stats.get("episodes", 0.0))
        count = self._finite_nonnegative(stats.get(
            f"curriculum_chord_set_{signature}_count", 0.0))
        success = self._finite_nonnegative(stats.get(
            f"curriculum_chord_set_{signature}_success", 0.0))
        target = episodes * count
        return min(episodes * success, target), target

    def _accumulate_chord_phase_evidence(self, stats, signatures=None):
        p90 = float(stats.get(
            "curriculum_p90_target_distance", float("nan")))
        alignment = float(stats.get(
            "curriculum_cell_alignment_rate", float("nan")))
        geometry_valid = math.isfinite(p90) and math.isfinite(alignment)
        selected = (
            None if signatures is None
            else {int(signature) for signature in signatures})
        for finger_set in self.chord_available_sets:
            signature = self._finger_set_signature(finger_set)
            if selected is not None and signature not in selected:
                continue
            success, target = self._chord_set_episode_totals(
                stats, signature)
            if target <= 0.0:
                continue
            row = self.chord_phase_evidence.setdefault(
                str(signature), self._empty_chord_phase_row())
            row["target"] += target
            row["success"] += success
            if geometry_valid:
                row["p90_sum"] += p90 * target
                row["alignment_sum"] += alignment * target
                row["geometry_weight"] += target

    def _chord_phase_row_sample(self, signature):
        row = self.chord_phase_evidence.get(str(signature))
        if not row:
            return None
        minimum = float(self.config.chord_fine_min_phase_episodes)
        target = float(row["target"])
        geometry_weight = float(row["geometry_weight"])
        if target < minimum or geometry_weight < minimum:
            return None
        rate = float(row["success"]) / max(target, 1.0)
        p90 = float(row["p90_sum"]) / max(geometry_weight, 1.0)
        alignment = (
            float(row["alignment_sum"]) / max(geometry_weight, 1.0))
        geometry = (
            p90 <= self.config.chord_fine_p90_distance
            and alignment >= self.config.chord_fine_alignment_rate)
        return rate if geometry else 0.0

    def _chord_set_has_evidence(self, stats, signature):
        if "episodes" not in stats:
            return True
        episodes = float(stats.get("episodes", 0.0))
        count = float(stats.get(
            f"curriculum_chord_set_{signature}_count", 0.0))
        return (
            episodes * count
            >= self.config.chord_fine_min_phase_episodes)

    def _chord_fine_phase_sample(self, stats):
        failure = float(stats.get("failure_termination", 0.0))
        if failure > 0.01:
            return 0.0
        if "episodes" in stats:
            if self.chord_focus_index >= 0:
                signature = self._finger_set_signature(
                    self.chord_available_sets[self.chord_focus_index])
                self._accumulate_chord_phase_evidence(
                    stats, signatures=(signature,))
                sample = self._chord_phase_row_sample(signature)
                if sample is None:
                    return -1.0
                self.chord_phase_evidence.pop(str(signature), None)
                return sample
            self._accumulate_chord_phase_evidence(stats)
            signatures = [
                self._finger_set_signature(finger_set)
                for finger_set in self.chord_available_sets
            ]
            samples = [
                self._chord_phase_row_sample(signature)
                for signature in signatures
            ]
            if not samples or any(sample is None for sample in samples):
                return -1.0
            self._reset_chord_phase_evidence()
            return min(samples)
        if self.chord_focus_index >= 0:
            signature = self._finger_set_signature(
                self.chord_available_sets[self.chord_focus_index])
            if not self._chord_set_has_evidence(stats, signature):
                return -1.0
            p90 = float(stats.get(
                "curriculum_p90_target_distance", float("inf")))
            alignment = float(stats.get(
                "curriculum_cell_alignment_rate", -1.0))
            if alignment < 0.0 or not math.isfinite(p90):
                return -1.0
            geometry = (
                p90 <= self.config.chord_fine_p90_distance
                and alignment >= self.config.chord_fine_alignment_rate)
            exact = self._chord_set_rate(stats, signature)
            return exact if geometry and exact >= 0.0 else (
                0.0 if exact >= 0.0 else -1.0)
        score = self._promotion_sample(stats)
        if score < 0.0:
            return score
        exact_rates = [
            self._chord_set_rate(
                stats, self._finger_set_signature(finger_set))
            for finger_set in self.chord_available_sets
        ]
        if not exact_rates or any(value < 0.0 for value in exact_rates):
            return -1.0
        if any(
                not self._chord_set_has_evidence(
                    stats, self._finger_set_signature(finger_set))
                for finger_set in self.chord_available_sets):
            return -1.0
        return min([score] + exact_rates)

    def _reset_chord_focus_window(self):
        self.chord_focus_iteration = 0
        self.stalled = False
        self.recent.clear()
        self._reset_chord_phase_evidence()

    def _advance_chord_focus(self, forced=False):
        signature = self._finger_set_signature(
            self.chord_available_sets[self.chord_focus_index])
        label = self._chord_focus_label()
        if forced:
            if signature not in self.chord_unresolved_signatures:
                self.chord_unresolved_signatures.append(signature)
            self.forced_advance = True
            self.forced_advance_count += 1
            self.last_forced_advance_from = (
                f"chord_fine_reach:{label}")
        elif signature in self.chord_unresolved_signatures:
            self.chord_unresolved_signatures.remove(signature)
        self.chord_focus_index += 1
        if self.chord_focus_index >= self.chord_focus_count:
            self.chord_focus_index = -1
        self._reset_chord_focus_window()

    def _retry_chord_focus_cycle(self):
        self.forced_advance = True
        self.forced_advance_count += 1
        self.last_forced_advance_from = "chord_fine_reach:mixed"
        self.chord_focus_cycle += 1
        self.chord_focus_index = 0
        self._reset_chord_focus_window()

    def _record_unresolved_chord_catalog(self):
        for finger_set in self.chord_available_sets:
            signature = self._finger_set_signature(finger_set)
            if signature not in self.chord_unresolved_signatures:
                self.chord_unresolved_signatures.append(signature)

    @staticmethod
    def _goal_pair_stat(stats, key, default=None):
        if key not in stats:
            return default
        value = float(stats[key])
        return value if math.isfinite(value) else default

    def _goal_pair_fingers(self, stats):
        if self.goal_pair_incoming_fingers:
            return self.goal_pair_incoming_fingers
        detected = tuple(
            finger for finger in range(1, 5)
            if any(
                key in stats for key in (
                    f"curriculum_goal_pair_rehearsal_finger_{finger}"
                    "_target_active_count",
                    f"curriculum_goal_pair_transition_finger_{finger}"
                    "_next_active_count",
                    f"curriculum_goal_pair_transition_finger_{finger}"
                    "_press_success",
                )))
        return detected or self.required_song_fingers

    def _goal_pair_context_row(self, stats, cohort, finger):
        prefix = f"curriculum_goal_pair_{cohort}_finger_{finger}"
        count = self._goal_pair_stat(
            stats, f"{prefix}_target_active_count")
        if count is None:
            active = self._goal_pair_stat(stats, f"{prefix}_target_active")
            episodes = self._goal_pair_stat(stats, "episodes")
            if active is not None and episodes is not None:
                count = active * episodes
        success = self._goal_pair_stat(stats, f"{prefix}_press_success")
        distance = self._goal_pair_stat(stats, f"{prefix}_target_distance")
        hold_quality = self._goal_pair_stat(
            stats, f"{prefix}_hold_quality")
        if hold_quality is None:
            hold_quality = self._goal_pair_stat(
                stats, "chord_hold_quality")
        if hold_quality is None:
            hold_quality = self._goal_pair_stat(
                stats, "sustain_hold_rate")
        dropout_rate = self._goal_pair_stat(
            stats, f"{prefix}_dropout_rate")
        if dropout_rate is None:
            dropout_rate = self._goal_pair_stat(
                stats, "press_dropout_rate")
        wrong_press = self._goal_pair_stat(
            stats, f"{prefix}_wrong_press")
        if wrong_press is None:
            wrong_press = self._goal_pair_stat(
                stats, "wrong_press_rate", 0.0)
        if (count is None or success is None or distance is None
                or hold_quality is None or dropout_rate is None
                or wrong_press is None):
            return None
        return {
            "count": max(0.0, count),
            "success": success,
            "distance": distance,
            "hold_quality": hold_quality,
            "dropout_rate": dropout_rate,
            "wrong_press": wrong_press,
        }

    def _goal_pair_rehearsal_row(self, stats, finger):
        return self._goal_pair_context_row(
            stats, "rehearsal", finger)

    def _goal_pair_full_song_row(self, stats, finger):
        return self._goal_pair_context_row(
            stats, "full_song", finger)

    def _goal_pair_transition_row(self, stats, finger):
        prefix = f"curriculum_goal_pair_transition_finger_{finger}"
        next_count = self._goal_pair_stat(
            stats, f"{prefix}_next_active_count")
        target_count = self._goal_pair_stat(
            stats, f"{prefix}_target_active_count")
        if target_count is None:
            active = self._goal_pair_stat(stats, f"{prefix}_target_active")
            episodes = self._goal_pair_stat(stats, "episodes")
            if active is not None and episodes is not None:
                target_count = active * episodes
        success = self._goal_pair_stat(stats, f"{prefix}_press_success")
        distance = self._goal_pair_stat(stats, f"{prefix}_next_distance")
        progress = self._goal_pair_stat(stats, f"{prefix}_next_progress")
        incoming_prefix = (
            f"curriculum_goal_pair_incoming_finger_{finger}")
        wrong_count = self._goal_pair_stat(
            stats, f"{incoming_prefix}_active_count")
        wrong_press = self._goal_pair_stat(
            stats, f"{incoming_prefix}_wrong_press")
        if wrong_count is None:
            wrong_count = target_count
        if wrong_press is None:
            wrong_press = self._goal_pair_stat(
                stats, f"{prefix}_wrong_press", 0.0)
        if (next_count is None or target_count is None
                or success is None or distance is None or progress is None
                or wrong_count is None or wrong_press is None):
            return None
        return {
            "next_count": max(0.0, next_count),
            "target_count": max(0.0, target_count),
            "success": success,
            "distance": distance,
            "progress": progress,
            "wrong_count": max(0.0, wrong_count),
            "wrong_press": wrong_press,
        }

    def _goal_pair_preservation_row(self, stats):
        for suffix in (
                "current_press_quality", "current_press_preserved"):
            key = f"curriculum_goal_pair_pretransition_{suffix}"
            value = self._goal_pair_stat(stats, key)
            count = self._goal_pair_stat(stats, f"{key}_count")
            if value is not None and count is not None:
                return {"value": value, "count": max(0.0, count)}
        return None

    def _accumulate_goal_pair_phase_stats(self, stats):
        evidence = self.goal_pair_phase_evidence
        preservation = self._goal_pair_preservation_row(stats)
        if preservation is not None:
            count = preservation["count"]
            evidence["preservation_count"] += count
            evidence["preservation_sum"] += preservation["value"] * count
        for finger in range(1, 5):
            for cohort, row in (
                    ("rehearsal", self._goal_pair_rehearsal_row(
                        stats, finger)),
                    ("full_song", self._goal_pair_full_song_row(
                        stats, finger))):
                if row is None:
                    continue
                count = row["count"]
                evidence[f"{cohort}_{finger}_count"] += count
                for metric, key in (
                        ("success", "success_sum"),
                        ("distance", "distance_sum"),
                        ("hold_quality", "hold_sum"),
                        ("dropout_rate", "dropout_sum"),
                        ("wrong_press", "wrong_sum")):
                    evidence[f"{cohort}_{finger}_{key}"] += (
                        row[metric] * count)
            transition = self._goal_pair_transition_row(stats, finger)
            if transition is None:
                continue
            next_count = transition["next_count"]
            target_count = transition["target_count"]
            evidence[f"transition_{finger}_next_count"] += next_count
            evidence[f"transition_{finger}_target_count"] += target_count
            evidence[f"transition_{finger}_success_sum"] += (
                transition["success"] * target_count)
            evidence[f"transition_{finger}_distance_sum"] += (
                transition["distance"] * next_count)
            evidence[f"transition_{finger}_progress_sum"] += (
                transition["progress"] * next_count)
            wrong_count = transition["wrong_count"]
            evidence[f"transition_{finger}_wrong_count"] += wrong_count
            evidence[f"transition_{finger}_wrong_sum"] += (
                transition["wrong_press"] * wrong_count)

    def _goal_pair_aggregated_stats(self, stats):
        combined = dict(stats)
        evidence = self.goal_pair_phase_evidence
        preservation_count = evidence["preservation_count"]
        if preservation_count > 0.0:
            key = (
                "curriculum_goal_pair_pretransition_"
                "current_press_quality")
            combined[f"{key}_count"] = preservation_count
            combined[key] = (
                evidence["preservation_sum"] / preservation_count)
        for finger in range(1, 5):
            for cohort in ("rehearsal", "full_song"):
                prefix = (
                    f"curriculum_goal_pair_{cohort}_finger_{finger}")
                count = evidence[f"{cohort}_{finger}_count"]
                if count <= 0.0:
                    continue
                combined[f"{prefix}_target_active_count"] = count
                for suffix, key in (
                        ("press_success", "success_sum"),
                        ("target_distance", "distance_sum"),
                        ("hold_quality", "hold_sum"),
                        ("dropout_rate", "dropout_sum"),
                        ("wrong_press", "wrong_sum")):
                    combined[f"{prefix}_{suffix}"] = (
                        evidence[f"{cohort}_{finger}_{key}"] / count)
            transition = (
                f"curriculum_goal_pair_transition_finger_{finger}")
            next_count = evidence[f"transition_{finger}_next_count"]
            target_count = evidence[f"transition_{finger}_target_count"]
            if next_count > 0.0:
                combined[f"{transition}_next_active_count"] = next_count
                combined[f"{transition}_next_distance"] = (
                    evidence[f"transition_{finger}_distance_sum"]
                    / next_count)
                combined[f"{transition}_next_progress"] = (
                    evidence[f"transition_{finger}_progress_sum"]
                    / next_count)
            if target_count > 0.0:
                combined[f"{transition}_target_active_count"] = (
                    target_count)
                combined[f"{transition}_press_success"] = (
                    evidence[f"transition_{finger}_success_sum"]
                    / target_count)
            wrong_count = evidence[f"transition_{finger}_wrong_count"]
            if wrong_count > 0.0:
                incoming = (
                    f"curriculum_goal_pair_incoming_finger_{finger}")
                combined[f"{incoming}_active_count"] = wrong_count
                combined[f"{incoming}_wrong_press"] = (
                    evidence[f"transition_{finger}_wrong_sum"]
                    / wrong_count)
        return combined

    def _goal_pair_sequence_sample(self, stats):
        difficulty = self._goal_pair_difficulty()
        if difficulty["sequence_probability"] <= 0.0:
            return True
        count = self._goal_pair_stat(
            stats, "curriculum_goal_pair_sequence_active_count")
        if count is None or count < self.config.goal_pair_sequence_min_frames:
            return None
        required = {
            "press_success": (
                self.config.goal_pair_sequence_press_rate, True),
            "no_press_success": (
                self.config.goal_pair_sequence_no_press_rate, True),
            "wrong_press": (
                self.config.goal_pair_sequence_wrong_press_rate, False),
            "penetration": (
                self.config.goal_pair_sequence_penetration_rate, False),
            "thumb_support": (
                self.config.goal_pair_sequence_thumb_support_rate, True),
        }
        for name, (threshold, lower_bound) in required.items():
            value = self._goal_pair_stat(
                stats, f"curriculum_goal_pair_sequence_{name}")
            if value is None:
                return None
            if lower_bound and value < threshold:
                return False
            if not lower_bound and value > threshold:
                return False
        return True

    def _goal_pair_focus_unresolved(self, stats, finger):
        minimum = self.config.goal_pair_phase_min_evidence
        if (self.goal_pair_phase == "retention"
                or self.goal_pair_recovery_active):
            row = self._goal_pair_rehearsal_row(stats, finger)
            if row is None or row["count"] < minimum:
                return None
            passed = (
                row["success"] >= self.config.goal_pair_rehearsal_press_rate
                and row["distance"]
                    <= self.config.goal_pair_rehearsal_distance
                and row["hold_quality"]
                    >= self.config.goal_pair_rehearsal_hold_quality
                and row["dropout_rate"]
                    <= self.config.goal_pair_rehearsal_dropout_rate)
            score = (
                min(row["success"], row["hold_quality"],
                    1.0 - row["dropout_rate"]),
                -row["distance"], finger)
            return passed, score
        row = self._goal_pair_transition_row(stats, finger)
        rehearsal = self._goal_pair_rehearsal_row(stats, finger)
        full_song = self._goal_pair_full_song_row(stats, finger)
        level = self._goal_pair_level()
        preview_only = level < self.config.goal_pair_preview_levels
        if (row is None or rehearsal is None
                or row["next_count"] < minimum
                or (not preview_only and row["target_count"] < minimum)
                or rehearsal["count"] < minimum
                or full_song is None
                or full_song["count"]
                    < self.config.goal_pair_full_song_focus_min_evidence):
            return None
        rehearsal_passed = (
            rehearsal["success"]
                >= self.config.goal_pair_rehearsal_press_rate
            and rehearsal["distance"]
                <= self.config.goal_pair_rehearsal_distance
            and rehearsal["hold_quality"]
                >= self.config.goal_pair_rehearsal_hold_quality
            and rehearsal["dropout_rate"]
                <= self.config.goal_pair_rehearsal_dropout_rate)
        transition_passed = (
            (preview_only
             or row["success"]
                >= self.config.goal_pair_mixed_press_rates[level])
            and row["distance"]
                <= self.config.goal_pair_mixed_distances[level]
            and row["progress"]
                >= self.config.goal_pair_mixed_min_next_progress
            and row["wrong_press"]
                <= self.config.goal_pair_mixed_wrong_press_rates[level])
        transfer_passed = (
            full_song["success"]
                >= self.config.goal_pair_mixed_full_song_press_rates[level]
            and full_song["wrong_press"]
                <= self.config.goal_pair_mixed_wrong_press_rates[level])
        transition_score = (
            row["progress"] if preview_only else row["success"])
        score = (
            min(rehearsal["success"], rehearsal["hold_quality"],
                1.0 - rehearsal["dropout_rate"], transition_score,
                full_song["success"], 1.0 - row["wrong_press"],
                1.0 - full_song["wrong_press"]),
            -max(
                rehearsal["distance"]
                    / self.config.goal_pair_rehearsal_distance,
                row["distance"]
                    / self.config.goal_pair_mixed_distances[level]),
            finger)
        return rehearsal_passed and transition_passed and transfer_passed, score

    def _goal_pair_mastery_retained(self, stats, finger):
        row = self._goal_pair_rehearsal_row(stats, finger)
        if (row is None
                or row["count"]
                    < self.config.goal_pair_phase_min_evidence):
            return None
        retained = (
            row["success"]
                >= self.config.goal_pair_mastery_retain_press_rate
            and row["distance"]
                <= self.config.goal_pair_mastery_retain_distance
            and row["hold_quality"]
                >= self.config.goal_pair_mastery_retain_hold_quality
            and row["dropout_rate"]
                <= self.config.goal_pair_mastery_retain_dropout_rate)
        if self.goal_pair_phase == "mixed":
            full_song = self._goal_pair_full_song_row(stats, finger)
            if (full_song is None
                    or full_song["count"]
                        < self.config.goal_pair_full_song_focus_min_evidence):
                return None
            level = self._goal_pair_level()
            retained = (
                retained
                and full_song["success"] >= max(
                    0.0,
                    self.config.goal_pair_mixed_full_song_press_rates[level]
                    - 0.10)
                and full_song["wrong_press"] <= min(
                    1.0,
                    self.config.goal_pair_mixed_wrong_press_rates[level]
                    + 0.02))
        return retained, (
            min(
                row["success"], row["hold_quality"],
                1.0 - row["dropout_rate"],
                (full_song["success"]
                 if self.goal_pair_phase == "mixed" else 1.0)),
            -row["distance"], finger)

    def _update_goal_pair_mastery(self, stats):
        evaluations = {}
        for finger in self._goal_pair_fingers(stats):
            index = finger - 1
            if self.goal_pair_mastered_fingers[index]:
                retained = self._goal_pair_mastery_retained(stats, finger)
                if retained is None:
                    continue
                passed, score = retained
                if passed:
                    self.goal_pair_mastery_fail_streaks[index] = 0
                else:
                    self.goal_pair_mastery_fail_streaks[index] += 1
                    if (self.goal_pair_mastery_fail_streaks[index]
                            >= self.config.goal_pair_mastery_regression_windows):
                        self.goal_pair_mastered_fingers[index] = False
                        self.goal_pair_mastery_streaks[index] = 0
                        self.goal_pair_mastery_fail_streaks[index] = 0
                        evaluations[finger] = (False, score)
                self._reset_goal_pair_finger_evidence(finger)
                continue
            result = self._goal_pair_focus_unresolved(stats, finger)
            if result is None:
                continue
            passed, score = result
            evaluations[finger] = (passed, score)
            if passed:
                self.goal_pair_mastery_streaks[index] += 1
                if (self.goal_pair_mastery_streaks[index]
                        >= self.config.promotion_windows):
                    self.goal_pair_mastered_fingers[index] = True
                    self.goal_pair_mastery_fail_streaks[index] = 0
            else:
                self.goal_pair_mastery_streaks[index] = 0
            self._reset_goal_pair_finger_evidence(finger)
        return evaluations

    def _goal_pair_bridge_weakest(self, fingers):
        fingers = tuple(int(finger) for finger in fingers)
        if not fingers:
            return 0
        rates = {
            finger: self.bridge_last_metrics.get(
                f"finger_{finger}_rate")
            for finger in fingers
        }
        if any(value is None for value in rates.values()):
            return 0
        return min(rates, key=rates.get)

    def _goal_pair_full_song_rates(self, stats, fingers):
        rates = {}
        minimum = self.config.goal_pair_full_song_focus_min_evidence
        for finger in fingers:
            row = self._goal_pair_full_song_row(stats, finger)
            if row is None or row["count"] < minimum:
                return {}
            rates[int(finger)] = float(row["success"])
        return rates

    def _goal_pair_full_song_weakest(
            self, stats, fingers, rotate_from=0):
        rates = self._goal_pair_full_song_rates(stats, fingers)
        if not rates:
            return 0
        minimum = min(rates.values())
        tied = sorted(
            finger for finger, rate in rates.items()
            if rate <= minimum + 0.01)
        rotate_from = int(rotate_from)
        if rotate_from in tied and len(tied) > 1:
            return tied[(tied.index(rotate_from) + 1) % len(tied)]
        return tied[0]

    def _goal_pair_recovery_song_ready(self, stats):
        fingers = self._goal_pair_fingers(stats)
        rates = self._goal_pair_full_song_rates(stats, fingers)
        return bool(rates) and min(rates.values()) >= (
            self.config.goal_pair_recovery_min_full_song_press_rate)

    def _update_goal_pair_focus(self, stats, evaluations):
        for finger, (_, score) in evaluations.items():
            self.goal_pair_focus_scores[finger - 1] = tuple(
                float(value) for value in score)
        focus_enabled = max(
            self.config.goal_pair_retention_focus_probability,
            self.config.goal_pair_mixed_focus_probability,
            self.config.goal_pair_timeout_focus_probability,
        ) > 0.0
        if not focus_enabled:
            changed = self.goal_pair_focus_finger != 0
            self.goal_pair_focus_finger = 0
            if changed:
                self.goal_pair_focus_iteration = 0
            return changed
        if (self.goal_pair_phase == "full"
                and not self.goal_pair_recovery_active):
            changed = self.goal_pair_focus_finger != 0
            self.goal_pair_focus_finger = 0
            if changed:
                self.goal_pair_focus_iteration = 0
            return changed
        fingers = self._goal_pair_fingers(stats)
        unresolved = [
            finger for finger in fingers
            if not self.goal_pair_mastered_fingers[finger - 1]]
        if self.goal_pair_recovery_active:
            full_song_rates = self._goal_pair_full_song_rates(
                stats, fingers)
            if full_song_rates:
                minimum_song_rate = (
                    self.config.goal_pair_recovery_min_full_song_press_rate)
                unresolved = [
                    finger for finger in fingers
                    if full_song_rates[finger] < minimum_song_rate]
        scores_ready = bool(unresolved) and all(
            self.goal_pair_focus_scores[finger - 1] is not None
            for finger in unresolved)
        rehearsal_weakest = (
            min(
                unresolved,
                key=lambda finger:
                    self.goal_pair_focus_scores[finger - 1])
            if scores_ready else 0)
        current = self.goal_pair_focus_finger
        rotate_from = (
            current
            if self.goal_pair_focus_iteration
                >= self.config.goal_pair_focus_min_iterations
            else 0)
        weakest = (
            (self._goal_pair_full_song_weakest(
                stats, unresolved, rotate_from=rotate_from)
             if self.goal_pair_recovery_active else 0)
            or (self._goal_pair_bridge_weakest(unresolved)
                if self.goal_pair_recovery_active else 0)
            or rehearsal_weakest)
        focus_locked = (
            current in unresolved
            and self.goal_pair_focus_iteration
                < self.config.goal_pair_focus_min_iterations)
        if focus_locked:
            selected = current
        elif weakest > 0:
            selected = weakest
        elif current in unresolved:
            selected = current
        else:
            selected = 0
        changed = selected != current
        self.goal_pair_focus_finger = selected
        if changed:
            self.goal_pair_focus_iteration = 0
        return changed

    def _start_goal_pair_recovery(self, stats, reason):
        if self.stage != "goal_pair":
            return False
        if not self.goal_pair_phase_baseline and self.bridge_last_metrics:
            self.goal_pair_phase_baseline = dict(self.bridge_last_metrics)
            self.goal_pair_phase_baseline_label = (
                self._goal_pair_phase_label())
        fingers = self._goal_pair_fingers(stats)
        scores_ready = bool(fingers) and all(
            self.goal_pair_focus_scores[finger - 1] is not None
            for finger in fingers)
        full_song_weakest = self._goal_pair_full_song_weakest(
            stats, fingers)
        bridge_weakest = self._goal_pair_bridge_weakest(fingers)
        rehearsal_weakest = (
            min(
                fingers,
                key=lambda finger:
                    self.goal_pair_focus_scores[finger - 1])
            if scores_ready else 0)
        selected = (
            full_song_weakest or bridge_weakest or rehearsal_weakest
            if self.config.goal_pair_timeout_focus_probability > 0.0
            else 0)
        focus_changed = selected != self.goal_pair_focus_finger
        self.goal_pair_focus_finger = selected
        self.goal_pair_focus_iteration = 0
        if self.goal_pair_recovery_active:
            return focus_changed
        self.goal_pair_recovery_active = True
        self.goal_pair_recovery_iteration = 0
        self.goal_pair_recovery_good_windows = 0
        self.goal_pair_recovery_count += 1
        self.goal_pair_recovery_reason = str(reason)
        self.goal_pair_recovery_failures = ()
        self.stalled = True
        self.recent.clear()
        self._reset_goal_pair_phase_evidence()
        self._reset_bridge_evidence(reset_regression=False)
        self.regression_hold = True
        return True

    def _finish_goal_pair_recovery(self):
        self.goal_pair_recovery_active = False
        self.goal_pair_recovery_iteration = 0
        self.goal_pair_recovery_good_windows = 0
        self.goal_pair_recovery_reason = ""
        self.goal_pair_recovery_failures = ()
        self.regression_bad_windows = 0
        self.regression_hold = False
        self.regression_metrics = ()
        self.stalled = False
        self._reset_bridge_evidence(reset_regression=False)
        if self.goal_pair_phase == "mixed":
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_mastered_fingers = [False] * 4
            self.goal_pair_mastery_streaks = [0] * 4
            self.goal_pair_mastery_fail_streaks = [0] * 4
        else:
            self.goal_pair_phase_iteration = 0
        self.goal_pair_focus_scores = [None] * 4
        self._reset_goal_pair_phase_evidence()

    def _rollback_goal_pair_recovery(self):
        previous = self._goal_pair_phase_label()
        reason = self.goal_pair_recovery_reason or "quality_timeout"
        fallback_stage = False
        if self.goal_pair_phase == "full":
            self.goal_pair_phase = "mixed"
            self.goal_pair_mixed_level = (
                len(self.config.goal_pair_mixed_transition_fractions) - 1)
        elif (self.goal_pair_phase == "mixed"
                and self.goal_pair_mixed_level > 0):
            self.goal_pair_mixed_level -= 1
        elif self.goal_pair_phase == "mixed":
            self.goal_pair_phase = "retention"
            self.goal_pair_mixed_level = 0
        else:
            self.stage = "frozen_context"
            self.stage_iteration = 0
            self.frozen_context_final_applied = False
            self.frozen_context_focus_finger = 0
            self._reset_frozen_context_focus_evidence()
            fallback_stage = True
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_recovery_active = False
        self.goal_pair_recovery_iteration = 0
        self.goal_pair_recovery_good_windows = 0
        self.goal_pair_recovery_reason = ""
        self.goal_pair_recovery_failures = ()
        self.goal_pair_recovery_rollback = True
        self.goal_pair_recovery_rollback_count += 1
        current = (
            "frozen_context" if fallback_stage
            else self._goal_pair_phase_label())
        self.goal_pair_last_recovery_rollback = (
            f"{previous}->{current}:{reason}")
        self.regression_bad_windows = 0
        self.regression_hold = False
        self.regression_metrics = ()
        self.stalled = False
        self._reset_goal_pair_phase_window()
        self._reset_bridge_evidence(reset_regression=True)
        return True

    def _sync_goal_pair_recovery(self, stats):
        if self.stage != "goal_pair":
            return False
        if not self.goal_pair_recovery_active:
            if self.regression_hold:
                return self._start_goal_pair_recovery(
                    stats, "performance_regression")
            return False
        ready = (
            self.goal_pair_recovery_iteration
                >= self.config.goal_pair_recovery_min_iterations
            and self.goal_pair_recovery_good_windows
                >= self.config.goal_pair_recovery_windows
            and self._goal_pair_recovery_song_ready(stats))
        if ready:
            self._finish_goal_pair_recovery()
            return True
        if (self.goal_pair_recovery_iteration
                >= self.config.goal_pair_recovery_max_iterations):
            return self._rollback_goal_pair_recovery()
        self.regression_hold = True
        self.stalled = True
        return False

    def _goal_pair_global_sample(self, stats):
        if self.goal_pair_phase == "retention":
            return True
        preservation = self._goal_pair_preservation_row(stats)
        minimum = self.config.goal_pair_phase_min_evidence
        if preservation is None or preservation["count"] < minimum:
            return None
        level = self._goal_pair_level()
        sequence = self._goal_pair_sequence_sample(stats)
        if sequence is None:
            return None
        return (
            preservation["value"]
                >= self.config.goal_pair_mixed_preservation_rates[level]
            and sequence)

    def _reset_goal_pair_phase_window(self):
        self.goal_pair_mastered_fingers = [False] * 4
        self.goal_pair_mastery_streaks = [0] * 4
        self.goal_pair_mastery_fail_streaks = [0] * 4
        self.goal_pair_focus_finger = 0
        self.goal_pair_focus_iteration = 0
        self.goal_pair_focus_scores = [None] * 4
        self.recent.clear()
        self._reset_goal_pair_phase_evidence()
        self._reset_goal_pair_phase_baseline()

    def _sync_goal_pair_phase(self, stats):
        if self.stage != "goal_pair":
            return False
        if self.goal_pair_recovery_active:
            evaluations = self._update_goal_pair_mastery(stats)
            self._update_goal_pair_focus(stats, evaluations)
            return False
        if self.goal_pair_phase == "full":
            self._update_goal_pair_focus(stats, {})
            return False
        evaluations = self._update_goal_pair_mastery(stats)
        self._update_goal_pair_focus(stats, evaluations)
        minimum = (
            self.config.goal_pair_retention_min_iterations
            if self.goal_pair_phase == "retention"
            else self.config.goal_pair_mixed_min_iterations)
        phase_iteration = (
            self.goal_pair_phase_iteration
            if self.goal_pair_phase == "retention"
            else self.goal_pair_mixed_level_iteration)
        fingers = self._goal_pair_fingers(stats)
        all_mastered = bool(fingers) and all(
            self.goal_pair_mastered_fingers[finger - 1]
            for finger in fingers)
        global_sample = self._goal_pair_global_sample(stats)
        if (self.goal_pair_phase == "mixed"
                and global_sample is not None):
            self._reset_goal_pair_global_evidence()
        passed = (
            phase_iteration >= minimum
            and all_mastered
            and global_sample is True)
        if not passed:
            if phase_iteration >= self.config.goal_pair_phase_max_iterations:
                self.goal_pair_phase_timeout_count += 1
                if self.goal_pair_phase == "retention":
                    self.goal_pair_phase_iteration = 0
                else:
                    self.goal_pair_mixed_level_iteration = 0
                self.goal_pair_mastery_streaks = [
                    0 if not mastered else streak
                    for mastered, streak in zip(
                        self.goal_pair_mastered_fingers,
                        self.goal_pair_mastery_streaks)]
                for finger in fingers:
                    if not self.goal_pair_mastered_fingers[finger - 1]:
                        self._reset_goal_pair_finger_evidence(finger)
                self._start_goal_pair_recovery(
                    stats, f"{self.goal_pair_phase}_timeout")
                return True
            return False
        if (self.goal_pair_phase == "mixed"
                and self.goal_pair_mixed_level + 1
                    < len(
                        self.config.goal_pair_mixed_transition_fractions)):
            self.goal_pair_mixed_level += 1
            self.goal_pair_mixed_level_iteration = 0
            self._reset_goal_pair_phase_window()
            self._reset_bridge_evidence(reset_regression=True)
            self.stalled = False
            return True
        index = self.GOAL_PAIR_PHASES.index(self.goal_pair_phase)
        self.goal_pair_phase = self.GOAL_PAIR_PHASES[index + 1]
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self._reset_goal_pair_phase_window()
        self._reset_bridge_evidence(reset_regression=True)
        self.stalled = False
        return True

    def _goal_pair_promotion_diagnostics_pass(self, stats):
        preservation_key = (
            "curriculum_goal_pair_pretransition_current_press_quality")
        available = (
            preservation_key in stats
            or "curriculum_goal_pair_pretransition_current_press_preserved"
                in stats
            or any(
                f"curriculum_goal_pair_transition_finger_{finger}"
                "_press_success" in stats
                for finger in range(1, 5)))
        if not available:
            return True
        preservation = self._goal_pair_preservation_row(stats)
        minimum = self.config.goal_pair_phase_min_evidence
        if (preservation is None or preservation["count"] < minimum
                or preservation["value"]
                    < self.config.goal_pair_pretransition_preservation_rate):
            return False
        fingers = self._goal_pair_fingers(stats)
        if not fingers:
            return False
        for finger in fingers:
            rehearsal = self._goal_pair_rehearsal_row(stats, finger)
            row = self._goal_pair_transition_row(stats, finger)
            full_song = self._goal_pair_full_song_row(stats, finger)
            if (rehearsal is None
                    or rehearsal["count"] < minimum
                    or rehearsal["success"]
                        < self.config.goal_pair_rehearsal_press_rate
                    or rehearsal["distance"]
                        > self.config.goal_pair_rehearsal_distance
                    or row is None
                    or min(row["next_count"], row["target_count"])
                        < minimum
                    or row["success"]
                        < self.config.goal_pair_promotion_transition_press_rate
                    or row["wrong_press"]
                        > self.config.goal_pair_mixed_wrong_press_rates[-1]
                    or full_song is None
                    or full_song["count"]
                        < self.config.goal_pair_full_song_focus_min_evidence
                    or full_song["success"]
                        < self.config.goal_pair_mixed_full_song_press_rates[-1]
                    or full_song["wrong_press"]
                        > self.config.goal_pair_mixed_wrong_press_rates[-1]):
                return False
        return self._goal_pair_sequence_sample(stats) is True

    def _bridge_difficulty_ready(self):
        return (
            self._frozen_context_evaluation_ready()
            and (self.stage != "goal_pair"
                 or self._goal_pair_difficulty()["final"])
            and (self.stage != "transition_window"
                 or self._transition_difficulty()["final_level"])
        )

    def _after_bridge_iteration(
            self, stats, transition_difficulty_changed=False,
            allow_promotion=True):
        evidence_allowed = (
            (self.stage != "frozen_context"
             or self.frozen_context_final_applied)
            and not transition_difficulty_changed)
        if evidence_allowed:
            self._accumulate_bridge_stats(stats)
        self.stalled = False
        if self.stage == "goal_pair":
            recovery_changed = self._sync_goal_pair_recovery(stats)
            if self.goal_pair_recovery_active:
                return self.state()
            if recovery_changed:
                return self.state()
        if not allow_promotion:
            return self.state()

        if self.stage in self.SOFT_TIMEOUT_STAGES:
            minimum, maximum = self._practice_limits()
            difficulty_ready = self._bridge_difficulty_ready()
            goal_pair_diagnostics_ready = (
                self.stage != "goal_pair"
                or self._goal_pair_promotion_diagnostics_pass(stats))
            normal_passed = (
                self.stage_iteration >= minimum
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(stats)
                and not self.regression_hold
                and self._bridge_windows_pass())
            if normal_passed:
                self._promote()
                return self.state()
            soft_iteration = int(math.ceil(
                maximum
                * self.config.bridge_soft_timeout_fraction))
            soft_passed = (
                self.stage_iteration >= soft_iteration
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(stats)
                and not self.regression_hold
                and self._bridge_windows_pass(soft=True))
            if soft_passed:
                previous = self.stage
                self._force_promote(f"{previous}:soft_timeout")
                return self.state()
            hard_ready = (
                self.stage_iteration >= maximum
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(stats)
                and not self.regression_hold
                and (self.stage != "frozen_context"
                     or (self.frozen_context_final_applied
                         and self._frozen_context_difficulty()["final"]))
                and self._catastrophic_free(stats))
            hard_ready = (
                hard_ready
                and self._hard_timeout_quality_floor_passes())
            if hard_ready:
                previous = self.stage
                self._force_promote(f"{previous}:hard_timeout")
                return self.state()
            self.stalled = (
                self.regression_hold
                or self.stage_iteration >= maximum)
            return self.state()

        minimum = (
            self.config.coverage_iterations
            if self.stage == "coverage"
            else self.config.integration_iterations)
        normal_passed = (
            self.stage_iteration >= minimum
            and self._thumb_geometry_gate_passes(stats)
            and not self.regression_hold
            and self._bridge_windows_pass())
        if normal_passed:
            self._promote()
            return self.state()
        hard_iteration = (
            minimum + self.config.late_stage_grace_iterations)
        if (self.stage_iteration >= hard_iteration
                and self._thumb_geometry_gate_passes(stats)
                and self._catastrophic_free(stats)):
            previous = self.stage
            self._force_promote(f"{previous}:hard_timeout")
            return self.state()
        self.stalled = (
            self.regression_hold
            or self.stage_iteration >= minimum)
        return self.state()

    def after_iteration(self, stats):
        self.forced_advance = False
        self.goal_pair_recovery_rollback = False
        self.total_iteration += 1
        self.stage_iteration += 1
        if self.stage == "chord_fine_reach":
            self.chord_focus_iteration += 1
            self.chord_focus_total_iteration += 1
        if self.stage == "goal_pair":
            self.goal_pair_focus_iteration += 1
            if self.goal_pair_recovery_active:
                self.goal_pair_recovery_iteration += 1
            else:
                self.goal_pair_phase_iteration += 1
                if self.goal_pair_phase == "mixed":
                    self.goal_pair_mixed_level_iteration += 1
            self._accumulate_goal_pair_phase_stats(stats)
            goal_pair_stats = self._goal_pair_aggregated_stats(stats)
        else:
            goal_pair_stats = stats
        frozen_context_focus_changed = False
        if self.stage == "frozen_context":
            self._accumulate_frozen_context_focus_stats(stats)
            frozen_context_focus_changed = (
                self._sync_frozen_context_focus())
        transition_difficulty_changed = (
            self._sync_transition_difficulty())
        goal_pair_phase_changed = self._sync_goal_pair_phase(
            goal_pair_stats)
        if (self.forced_stage is not None
                and self.stage != "chord_fine_reach"):
            if self.stage in self.BRIDGE_STAGES:
                return self._after_bridge_iteration(
                    goal_pair_stats,
                    transition_difficulty_changed
                    or goal_pair_phase_changed
                    or frozen_context_focus_changed,
                    allow_promotion=False)
            return self.state()
        if self.stage == "chord_fine_reach":
            sample = self._chord_fine_phase_sample(stats)
            if sample >= 0.0:
                self.recent.append(sample)
            if self.chord_focus_index >= 0:
                minimum = self.config.chord_fine_focus_min_iterations
                maximum = self.config.chord_fine_focus_max_iterations
            else:
                minimum = self.config.chord_fine_min_iterations
                maximum = self.config.chord_fine_max_iterations
            passed = (
                self.chord_focus_iteration >= minimum
                and len(self.recent) == self.config.promotion_windows
                and all(
                    value >= self.config.chord_fine_success_rate
                    for value in self.recent))
            if self.chord_focus_index >= 0:
                if passed:
                    self._advance_chord_focus()
                elif self.chord_focus_iteration >= maximum:
                    self._advance_chord_focus(forced=True)
            elif passed:
                if self.forced_stage is None:
                    self._promote()
                else:
                    self.stalled = False
            elif self.chord_focus_iteration >= maximum:
                if self.forced_stage is not None:
                    self.stalled = True
                elif (self.chord_focus_cycle + 1
                      >= self.config.chord_fine_max_cycles):
                    self._record_unresolved_chord_catalog()
                    if self._catastrophic_free(stats):
                        self._force_promote(
                            "chord_fine_reach:max_cycles")
                    else:
                        self.stalled = True
                else:
                    self._retry_chord_focus_cycle()
            return self.state()
        if self.stage in self.BRIDGE_STAGES:
            return self._after_bridge_iteration(
                goal_pair_stats,
                transition_difficulty_changed
                or goal_pair_phase_changed
                or frozen_context_focus_changed)
        if self.stage in self.PRACTICE_STAGES:
            final_context_evidence = (
                self.stage != "frozen_context"
                or self.frozen_context_final_applied)
            sample = (
                self._promotion_sample(stats)
                if (final_context_evidence
                    and self._has_minimum_stage_evidence(stats))
                else -1.0)
            if sample >= 0.0:
                self.recent.append(sample)
            minimum, maximum = self._practice_limits()
            passed = (self.stage_iteration >= minimum
                      and len(self.recent) == self.config.promotion_windows
                      and all(value >= self.config.promotion_success_rate
                              for value in self.recent)
                      and (self.stage != "frozen_context"
                           or (self._frozen_context_difficulty()["final"]
                               and self.frozen_context_final_applied))
                      and (self.stage != "transition_window"
                           or self._transition_difficulty()["final_level"]))
            if passed:
                self._promote()
            elif self.stage_iteration >= maximum:
                self.stalled = True
        state = self.state()
        return state
