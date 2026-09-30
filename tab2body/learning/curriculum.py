"""Per-song practice curriculum for trajectory optimization, not song generalization."""
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import math
import json


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
    early_min_evidence_episodes_per_finger: int = 0
    early_evidence_window_episodes_per_finger: int = 4096
    early_evidence_stall_iterations: int = 100
    early_evidence_recent_iterations: int = 100
    early_recovery_focus_min_iterations: int = 400
    early_recovery_switch_margin: float = 0.03
    early_recovery_focus_probability: float = 0.75
    early_recovery_max_focus_blocks: int = 2
    early_recovery_max_total_blocks: int = 24
    early_recovery_min_finger_probability: float = 0.15
    early_recovery_retention_drop_tolerance: float = 0.05
    practice_reset_watchdog_iterations: int = 25
    integrated_recovery_focus_probability: float = 0.75
    integrated_recovery_max_iterations: int = 1000
    integrated_recovery_block_iterations: int = 400
    integrated_recovery_min_finger_probability: float = 0.15
    integrated_recovery_max_blocks: int = 12
    integrated_recovery_min_improvement: float = 0.03
    integrated_recovery_retention_drop_tolerance: float = 0.05
    integrated_press_unlock_iterations: tuple[int, int, int] = (100, 200, 300)
    chord_reach_min_iterations: int = 300
    chord_reach_max_iterations: int = 2000
    chord_fine_min_iterations: int = 400
    chord_fine_max_iterations: int = 2000
    chord_fine_focus_min_iterations: int = 100
    chord_fine_focus_max_iterations: int = 1200
    chord_fine_max_cycles: int = 1
    chord_fine_focus_probability: float = 0.80
    chord_fine_success_rate: float = 0.80
    chord_fine_p90_distance: float = 0.015
    chord_fine_alignment_rate: float = 0.80
    chord_fine_min_phase_episodes: int = 256
    chord_evidence_stall_iterations: int = 300
    chord_fine_soft_success_rate: float = 0.10
    chord_fine_soft_p90_distance: float = 0.025
    chord_fine_soft_alignment_rate: float = 0.40
    static_chord_min_iterations: int = 400
    static_chord_max_iterations: int = 3000
    static_chord_retest_max_iterations: int = 1000
    static_chord_recovery_max_cycles: int = 3
    static_chord_recovery_focus_probability: float = 0.90
    frozen_context_min_iterations: int = 1000
    frozen_context_max_iterations: int = 4000
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
    # 회복 표본은 한 손가락에 고정하지 않고 모든 손가락을 유지한다.
    goal_pair_recovery_finger_weights: tuple[float, ...] = (
        0.15, 0.15, 0.30, 0.40)
    goal_pair_recovery_focus_min_iterations: int = 100
    goal_pair_recovery_min_iterations: int = 100
    goal_pair_recovery_max_iterations: int = 600
    goal_pair_recovery_windows: int = 2
    goal_pair_recovery_rehearsal_probability: float = 0.60
    goal_pair_uncovered_pose_probability: float = 0.10
    goal_pair_recovery_uncovered_pose_probability: float = 0.15
    goal_pair_recovery_sequence_probability: float = 0.40
    goal_pair_recovery_sequence_max_events: int = 4
    goal_pair_recovery_full_song_fraction: float = 0.10
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
    frozen_context_evaluation_fraction: float = 0.25
    frozen_context_initial_finger_weights: tuple[float, ...] = (
        0.20, 0.20, 0.30, 0.30)
    frozen_context_recovery_block_iterations: int = 500
    frozen_context_recovery_min_finger_probability: float = 0.20
    frozen_context_recovery_max_finger_probability: float = 0.40
    frozen_context_recovery_weight_smoothing: float = 1.0
    frozen_context_recovery_min_weight_change: float = 0.02
    frozen_context_recovery_retention_drop_tolerance: float = 0.05
    frozen_context_recovery_ready_blocks: int = 2
    frozen_context_recovery_max_blocks: int = 8
    frozen_context_evaluation_min_finger_frames: int = 1
    frozen_context_singleton_probability: float = 0.60
    frozen_context_chord_probability: float = 0.30
    frozen_context_uniform_probability: float = 0.10
    # schema 55 이전 checkpoint를 읽기 위한 deprecated 필드다.
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
        if (isinstance(self.early_min_evidence_episodes_per_finger, bool)
                or self.early_min_evidence_episodes_per_finger < 0):
            raise ValueError(
                "early-stage evidence per finger must be non-negative")
        if (isinstance(self.early_evidence_window_episodes_per_finger, bool)
                or self.early_evidence_window_episodes_per_finger < 1
                or self.early_evidence_window_episodes_per_finger
                < self.early_min_evidence_episodes_per_finger):
            raise ValueError(
                "early-stage evidence window must cover the minimum evidence")
        if (isinstance(self.early_evidence_stall_iterations, bool)
                or self.early_evidence_stall_iterations < 1):
            raise ValueError(
                "early-stage evidence watchdog must be positive")
        if (isinstance(self.early_evidence_recent_iterations, bool)
                or self.early_evidence_recent_iterations < 1):
            raise ValueError(
                "early-stage recent evidence window must be positive")
        if (isinstance(self.early_recovery_focus_min_iterations, bool)
                or self.early_recovery_focus_min_iterations < 1):
            raise ValueError(
                "early recovery focus block must be positive")
        if not 0.0 <= self.early_recovery_switch_margin <= 1.0:
            raise ValueError(
                "early recovery switch margin must be in [0, 1]")
        if not 0.0 < self.early_recovery_focus_probability <= 1.0:
            raise ValueError(
                "early recovery focus probability must be in (0, 1]")
        if (isinstance(self.early_recovery_max_focus_blocks, bool)
                or self.early_recovery_max_focus_blocks < 1):
            raise ValueError(
                "early recovery maximum focus blocks must be positive")
        if (isinstance(self.early_recovery_max_total_blocks, bool)
                or self.early_recovery_max_total_blocks < 1):
            raise ValueError(
                "early recovery maximum total blocks must be positive")
        if not 0.0 <= self.early_recovery_min_finger_probability <= 0.25:
            raise ValueError(
                "early recovery minimum finger probability must be in "
                "[0, 0.25]")
        if not 0.0 <= self.early_recovery_retention_drop_tolerance <= 1.0:
            raise ValueError(
                "early recovery retention tolerance must be in [0, 1]")
        if (isinstance(self.practice_reset_watchdog_iterations, bool)
                or self.practice_reset_watchdog_iterations < 2):
            raise ValueError(
                "practice reset watchdog must be at least two iterations")
        if not 0.0 < self.integrated_recovery_focus_probability <= 1.0:
            raise ValueError(
                "integrated recovery focus probability must be in (0, 1]")
        if self.integrated_recovery_max_iterations < 1:
            raise ValueError(
                "integrated recovery maximum iterations must be positive")
        if (isinstance(self.integrated_recovery_block_iterations, bool)
                or self.integrated_recovery_block_iterations < 1):
            raise ValueError(
                "integrated recovery block iterations must be positive")
        if not 0.0 <= self.integrated_recovery_min_finger_probability <= 0.25:
            raise ValueError(
                "integrated recovery minimum finger probability must be in [0, 0.25]")
        if (isinstance(self.integrated_recovery_max_blocks, bool)
                or self.integrated_recovery_max_blocks < 1):
            raise ValueError(
                "integrated recovery maximum blocks must be positive")
        if not 0.0 <= self.integrated_recovery_min_improvement <= 1.0:
            raise ValueError(
                "integrated recovery minimum improvement must be in [0, 1]")
        if not 0.0 <= self.integrated_recovery_retention_drop_tolerance <= 1.0:
            raise ValueError(
                "integrated recovery retention tolerance must be in [0, 1]")
        unlock = self.integrated_press_unlock_iterations
        if (len(unlock) != 3
                or any(isinstance(value, bool) or value < 0 for value in unlock)
                or any(right <= left for left, right in zip(unlock, unlock[1:]))):
            raise ValueError(
                "integrated press unlock iterations must be three increasing values")
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
        if self.chord_evidence_stall_iterations < 1:
            raise ValueError("chord evidence watchdog must be positive")
        if self.chord_fine_max_cycles < 1:
            raise ValueError("chord fine maximum cycles must be positive")
        if not 0.0 <= self.chord_fine_soft_success_rate <= 1.0:
            raise ValueError("chord fine soft success rate must be in [0, 1]")
        if self.chord_fine_soft_p90_distance <= 0.0:
            raise ValueError("chord fine soft p90 distance must be positive")
        if not 0.0 <= self.chord_fine_soft_alignment_rate <= 1.0:
            raise ValueError("chord fine soft alignment rate must be in [0, 1]")
        if self.static_chord_recovery_max_cycles < 1:
            raise ValueError("static chord recovery cycles must be positive")
        if self.static_chord_retest_max_iterations < 1:
            raise ValueError("static chord retest maximum must be positive")
        if not 0.0 < self.static_chord_recovery_focus_probability <= 1.0:
            raise ValueError(
                "static chord recovery focus probability must be in (0, 1]")
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
            self.goal_pair_recovery_focus_min_iterations,
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
        recovery_weights = tuple(self.goal_pair_recovery_finger_weights)
        if (len(recovery_weights) != 4
                or any(not math.isfinite(value) or value < 0.0
                       for value in recovery_weights)
                or sum(recovery_weights) <= 0.0):
            raise ValueError(
                "goal-pair recovery finger weights must have four "
                "non-negative values and positive mass")
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
        if not 0.0 < self.frozen_context_evaluation_fraction < 1.0:
            raise ValueError(
                "frozen-context evaluation fraction must be in (0, 1)")
        initial_weights = tuple(
            float(value) for value in self.frozen_context_initial_finger_weights)
        if (len(initial_weights) != 4
                or any(not math.isfinite(value) or value < 0.0
                       for value in initial_weights)
                or sum(initial_weights) <= 0.0):
            raise ValueError(
                "frozen-context initial finger weights must contain four "
                "finite non-negative values")
        if (isinstance(self.frozen_context_recovery_block_iterations, bool)
                or self.frozen_context_recovery_block_iterations < 1):
            raise ValueError(
                "frozen-context recovery block must be positive")
        minimum = self.frozen_context_recovery_min_finger_probability
        maximum = self.frozen_context_recovery_max_finger_probability
        if not 0.0 <= minimum <= 0.25:
            raise ValueError(
                "frozen-context minimum finger probability must be in [0, .25]")
        if not 0.25 <= maximum <= 1.0 or maximum < minimum:
            raise ValueError(
                "frozen-context maximum finger probability is invalid")
        if not 0.0 <= self.frozen_context_recovery_weight_smoothing <= 1.0:
            raise ValueError(
                "frozen-context recovery smoothing must be in [0, 1]")
        if not 0.0 <= self.frozen_context_recovery_min_weight_change <= 2.0:
            raise ValueError(
                "frozen-context minimum weight change must be in [0, 2]")
        if not 0.0 <= (
                self.frozen_context_recovery_retention_drop_tolerance) <= 1.0:
            raise ValueError(
                "frozen-context retention tolerance must be in [0, 1]")
        if (self.frozen_context_recovery_ready_blocks < 1
                or self.frozen_context_recovery_max_blocks
                    < self.frozen_context_recovery_ready_blocks):
            raise ValueError(
                "frozen-context recovery max blocks must cover ready blocks")
        if (isinstance(self.frozen_context_evaluation_min_finger_frames, bool)
                or self.frozen_context_evaluation_min_finger_frames < 1):
            raise ValueError(
                "frozen-context evaluation finger evidence must be positive")
        context_mix = (
            self.frozen_context_singleton_probability,
            self.frozen_context_chord_probability,
            self.frozen_context_uniform_probability,
        )
        if (any(not math.isfinite(value) or value < 0.0
                for value in context_mix)
                or abs(sum(context_mix) - 1.0) > 1e-6):
            raise ValueError(
                "frozen-context context mixture must be non-negative and sum to one")
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
    SCHEMA_VERSION = 58
    FROZEN_EVALUATION_SCHEMA_VERSION = 57
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
    EARLY_SINGLE_FINGER_STAGES = (
        "coarse_reach", "fine_reach",
        "isolated_press", "integrated_press")
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
    BRIDGE_FINGER_EVIDENCE_KEYS = tuple(
        f"finger_{finger}_frames" for finger in range(1, 5))
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
        if (source_schema < cls.FROZEN_EVALUATION_SCHEMA_VERSION
                and stage in {
                    "frozen_context", "goal_pair", "transition_window",
                    "coverage", "integration", "full_song",
                }):
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
        self.early_stage_evidence = self._empty_early_stage_evidence()
        self._early_stage_evidence_history = (
            self._empty_early_stage_evidence_history())
        self.early_stage_evidence_age = {
            finger: 0 for finger in range(1, 5)}
        self._early_stage_recent_targets = {
            finger: deque(maxlen=config.early_evidence_recent_iterations)
            for finger in range(1, 5)}
        self.early_recovery_focus_finger = 0
        self.early_recovery_focus_iteration = 0
        self.early_recovery_count = 0
        self.early_recovery_focus_blocks = 0
        self.early_recovery_total_blocks = 0
        self.early_recovery_exhausted = False
        self.early_recovery_weights = (0.25, 0.25, 0.25, 0.25)
        self.early_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.early_recovery_last_switch_reason = ""
        self.early_recovery_retention_max_drop = 0.0
        self.practice_focus_reset_count = 0
        self.practice_focus_reset_consecutive = 0
        self.integrated_recovery_active = False
        self.integrated_recovery_focus_finger = 0
        self.integrated_recovery_iteration = 0
        self.integrated_recovery_count = 0
        self.integrated_recovery_total_iteration = 0
        self.integrated_recovery_block_count = 0
        self.integrated_recovery_weights = (0.25, 0.25, 0.25, 0.25)
        self.integrated_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.integrated_recovery_block_start_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.integrated_recovery_retention_max_drop = 0.0
        self.integrated_recovery_min_rate_improvement = 0.0
        self.integrated_recovery_no_improvement_blocks = 0
        self.integrated_recovery_exhausted = False
        self.integrated_recovery_last_update_reason = ""
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
        self.chord_evidence_age = 0
        self.chord_evidence_stalled = False
        self.static_chord_recovery_active = False
        self.static_chord_recovery_count = 0
        self.static_chord_recovery_signatures = ()
        self.static_chord_recovery_reason = ""
        self.static_chord_blocked = False
        self.skipped_stages = []
        self.transition_difficulty_level = 0
        self.frozen_context_final_applied = False
        self.frozen_context_evaluation_started = False
        self.frozen_context_focus_finger = 0
        self.frozen_context_focus_evidence = (
            self._empty_frozen_context_focus_evidence())
        self.frozen_context_recovery_active = True
        self.frozen_context_recovery_iteration = 0
        self.frozen_context_recovery_block_count = 0
        self.frozen_context_recovery_ready_streak = 0
        self.frozen_context_recovery_exhausted = False
        self.frozen_context_recovery_failed = False
        self.frozen_context_recovery_completed_iteration = -1
        self.frozen_context_evaluation_started_iteration = -1
        self.frozen_context_recovery_weights = tuple(
            float(value)
            for value in config.frozen_context_initial_finger_weights)
        self.frozen_context_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_distances = {
            finger: float("inf") for finger in range(1, 5)}
        self.frozen_context_recovery_retention_max_drop = 0.0
        self.frozen_context_recovery_last_update_reason = "initial"
        self.frozen_context_sampler_update_count = 0
        self.frozen_context_evidence_reset_count = 0
        self.frozen_context_evidence_reset_reason = "initial"
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
        self.goal_pair_mastery_verified_since_recovery = [False] * 4
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

    @staticmethod
    def _empty_early_stage_evidence():
        return {
            finger: {"success": 0.0, "target": 0.0}
            for finger in range(1, 5)
        }

    @staticmethod
    def _empty_early_stage_evidence_history():
        return {finger: deque() for finger in range(1, 5)}

    def _reset_early_stage_evidence(self):
        self.early_stage_evidence = self._empty_early_stage_evidence()
        self._early_stage_evidence_history = (
            self._empty_early_stage_evidence_history())
        self.early_stage_evidence_age = {
            finger: 0 for finger in range(1, 5)}
        self._early_stage_recent_targets = {
            finger: deque(
                maxlen=self.config.early_evidence_recent_iterations)
            for finger in range(1, 5)}

    def _trim_early_stage_evidence(self, finger):
        capacity = float(
            self.config.early_evidence_window_episodes_per_finger)
        row = self.early_stage_evidence[finger]
        history = self._early_stage_evidence_history[finger]
        while row["target"] > capacity and history:
            excess = row["target"] - capacity
            success, target = history[0]
            if target <= excess + 1e-9:
                history.popleft()
                row["success"] -= success
                row["target"] -= target
                continue
            keep = (target - excess) / target
            removed_success = success * (1.0 - keep)
            history[0] = (success * keep, target - excess)
            row["success"] -= removed_success
            row["target"] -= excess
        row["success"] = min(max(row["success"], 0.0), row["target"])
        row["target"] = max(row["target"], 0.0)

    def _restore_early_stage_evidence_history(self):
        self._early_stage_evidence_history = (
            self._empty_early_stage_evidence_history())
        for finger, row in self.early_stage_evidence.items():
            target = float(row["target"])
            success = min(float(row["success"]), target)
            row["success"] = success
            if target > 0.0:
                self._early_stage_evidence_history[finger].append(
                    (success, target))
            self._trim_early_stage_evidence(finger)

    def _early_stage_rates(self):
        return {
            finger: (
                row["success"] / row["target"]
                if row["target"] > 0.0 else -1.0)
            for finger, row in self.early_stage_evidence.items()
        }

    def _early_recent_episode_counts(self):
        return {
            finger: sum(history)
            for finger, history in self._early_stage_recent_targets.items()
        }

    def _early_evidence_starved_fingers(self):
        if self.stage not in self.EARLY_SINGLE_FINGER_STAGES:
            return ()
        available = self.required_song_fingers or (1, 2, 3, 4)
        limit = self.config.early_evidence_stall_iterations
        return tuple(
            finger for finger in available
            if self.early_stage_evidence_age[finger] >= limit)

    def _accumulate_early_stage_evidence(self, stats):
        if self.stage not in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"):
            return
        for finger in range(1, 5):
            self.early_stage_evidence_age[finger] += 1
            self._early_stage_recent_targets[finger].append(0.0)
        episodes = float(stats.get("episodes", 0.0))
        if not math.isfinite(episodes) or episodes <= 0.0:
            return
        for finger, row in self.early_stage_evidence.items():
            target_key = f"curriculum_finger_{finger}_target_episodes"
            success_key = f"curriculum_finger_{finger}_success_episodes"
            target = float(stats.get(
                target_key,
                episodes * float(stats.get(
                    f"curriculum_finger_{finger}_count", 0.0))))
            success = float(stats.get(
                success_key,
                episodes * float(stats.get(
                    f"curriculum_finger_{finger}_success", 0.0))))
            if (not math.isfinite(target) or not math.isfinite(success)
                    or target < 0.0 or success < 0.0):
                continue
            if target <= 0.0:
                continue
            success = min(success, target)
            self._early_stage_evidence_history[finger].append(
                (success, target))
            self.early_stage_evidence_age[finger] = 0
            self._early_stage_recent_targets[finger][-1] += target
            row["target"] += target
            row["success"] += success
            self._trim_early_stage_evidence(finger)

    def _weakest_early_finger(self):
        available = self.required_song_fingers or (1, 2, 3, 4)
        rates = self._early_stage_rates()
        return min(
            available,
            key=lambda finger: (
                rates.get(finger, -1.0),
                self.early_stage_evidence[finger]["target"],
                finger))

    def _start_integrated_recovery(self):
        self.integrated_recovery_active = True
        self.integrated_recovery_iteration = 0
        self.integrated_recovery_total_iteration = 0
        self.integrated_recovery_block_count = 0
        self.integrated_recovery_count += 1
        rates = self._early_stage_rates()
        self.integrated_recovery_best_rates = dict(rates)
        self.integrated_recovery_block_start_rates = dict(rates)
        self.integrated_recovery_weights = (
            self._adaptive_integrated_recovery_weights(rates))
        self.integrated_recovery_focus_finger = (
            self._integrated_recovery_weighted_finger())
        self.integrated_recovery_retention_max_drop = 0.0
        self.integrated_recovery_min_rate_improvement = 0.0
        self.integrated_recovery_no_improvement_blocks = 0
        self.integrated_recovery_exhausted = False
        self.integrated_recovery_last_update_reason = "start"
        self.recent.clear()
        self.stalled = False

    def _balanced_integrated_recovery_weights(self):
        return self._balanced_recovery_weights()

    def _balanced_recovery_weights(self):
        available = self.required_song_fingers or (1, 2, 3, 4)
        weight = 1.0 / len(available)
        return tuple(
            weight if finger in available else 0.0
            for finger in range(1, 5))

    def _adaptive_recovery_weights(self, rates, best_rates, minimum):
        available = self.required_song_fingers or (1, 2, 3, 4)
        required_evidence = self.config.early_min_evidence_episodes_per_finger
        if any(
                self.early_stage_evidence[finger]["target"]
                < required_evidence
                for finger in available):
            return self._balanced_recovery_weights()
        floor = min(float(minimum), 1.0 / len(available))
        remaining = max(0.0, 1.0 - floor * len(available))
        deficits = {}
        for finger in available:
            rate = rates.get(finger, -1.0)
            if rate < 0.0:
                deficits[finger] = 1.0
                continue
            retention_drop = max(
                0.0, best_rates.get(finger, rate) - rate)
            deficits[finger] = max(
                0.0,
                self.config.promotion_success_rate - rate,
                retention_drop)
        deficit_total = sum(deficits.values())
        if deficit_total <= 1e-12:
            return self._balanced_recovery_weights()
        weights = [0.0] * 4
        for finger in available:
            weights[finger - 1] = (
                floor + remaining * deficits[finger] / deficit_total)
        return tuple(weights)

    def _adaptive_integrated_recovery_weights(self, rates):
        return self._adaptive_recovery_weights(
            rates, self.integrated_recovery_best_rates,
            self.config.integrated_recovery_min_finger_probability)

    def _adaptive_early_recovery_weights(self, rates):
        return self._adaptive_recovery_weights(
            rates, self.early_recovery_best_rates,
            self.config.early_recovery_min_finger_probability)

    @staticmethod
    def _weighted_recovery_finger(weights, available):
        return max(
            available,
            key=lambda finger: (weights[finger - 1], -finger))

    def _integrated_recovery_weighted_finger(self):
        available = self.required_song_fingers or (1, 2, 3, 4)
        return self._weighted_recovery_finger(
            self.integrated_recovery_weights, available)

    @staticmethod
    def _minimum_known_rate(rates, available):
        known = [rates.get(finger, -1.0) for finger in available]
        return min(known) if known and min(known) >= 0.0 else -1.0

    def _advance_integrated_recovery(self):
        if (self.stage != "integrated_press"
                or not self.integrated_recovery_active
                or self.integrated_recovery_exhausted
                or self.integrated_recovery_iteration
                < self.config.integrated_recovery_block_iterations):
            return
        available = self.required_song_fingers or (1, 2, 3, 4)
        rates = self._early_stage_rates()
        start_min = self._minimum_known_rate(
            self.integrated_recovery_block_start_rates, available)
        current_min = self._minimum_known_rate(rates, available)
        improvement = (
            current_min - start_min
            if start_min >= 0.0 and current_min >= 0.0 else 0.0)
        self.integrated_recovery_min_rate_improvement = improvement
        if improvement >= self.config.integrated_recovery_min_improvement:
            self.integrated_recovery_no_improvement_blocks = 0
        else:
            self.integrated_recovery_no_improvement_blocks += 1
        drops = {
            finger: max(
                0.0,
                self.integrated_recovery_best_rates.get(finger, -1.0)
                - rates.get(finger, -1.0))
            for finger in available
            if (self.integrated_recovery_best_rates.get(finger, -1.0) >= 0.0
                and rates.get(finger, -1.0) >= 0.0)
        }
        self.integrated_recovery_retention_max_drop = max(
            drops.values(), default=0.0)
        for finger, rate in rates.items():
            self.integrated_recovery_best_rates[finger] = max(
                self.integrated_recovery_best_rates.get(finger, -1.0), rate)
        self.integrated_recovery_block_count += 1
        self.integrated_recovery_iteration = 0
        self.integrated_recovery_block_start_rates = dict(rates)
        if (self.integrated_recovery_block_count
                >= self.config.integrated_recovery_max_blocks):
            self.integrated_recovery_exhausted = True
            self.integrated_recovery_weights = (
                self._balanced_integrated_recovery_weights())
            self.integrated_recovery_focus_finger = 0
            self.integrated_recovery_last_update_reason = "max_blocks"
            self.stalled = True
            return
        self.integrated_recovery_weights = (
            self._adaptive_integrated_recovery_weights(rates))
        self.integrated_recovery_focus_finger = (
            self._integrated_recovery_weighted_finger())
        self.integrated_recovery_last_update_reason = (
            "retention_drop"
            if self.integrated_recovery_retention_max_drop
            > self.config.integrated_recovery_retention_drop_tolerance
            else "deficit_update")

    def _start_early_recovery(self):
        rates = self._early_stage_rates()
        self.early_recovery_best_rates = dict(rates)
        self.early_recovery_weights = (
            self._adaptive_early_recovery_weights(rates)
            if self.stage == "isolated_press"
            else self._balanced_recovery_weights())
        available = self.required_song_fingers or (1, 2, 3, 4)
        self.early_recovery_focus_finger = (
            self._weighted_recovery_finger(
                self.early_recovery_weights, available)
            if self.stage == "isolated_press"
            else self._weakest_early_finger())
        self.early_recovery_focus_iteration = 0
        self.early_recovery_count += 1
        self.early_recovery_focus_blocks = 0
        self.early_recovery_total_blocks = 0
        self.early_recovery_exhausted = False
        self.early_recovery_last_switch_reason = (
            "adaptive_start"
            if self.stage == "isolated_press" else "start")
        self.early_recovery_retention_max_drop = 0.0
        self.recent.clear()
        self.stalled = True

    def _advance_early_recovery_focus(self):
        if (self.stage not in self.EARLY_SINGLE_FINGER_STAGES
                or self.stage == "integrated_press" or not self.stalled
                or self.early_recovery_exhausted):
            return
        available = self.required_song_fingers or (1, 2, 3, 4)
        if self.early_recovery_focus_finger not in available:
            self._start_early_recovery()
            return
        self.early_recovery_focus_iteration += 1
        if (self.early_recovery_focus_iteration
                < self.config.early_recovery_focus_min_iterations):
            return
        current = self.early_recovery_focus_finger
        rates = self._early_stage_rates()
        self.early_recovery_focus_blocks += 1
        self.early_recovery_total_blocks += 1
        recovery_exhausted = (
            self.early_recovery_total_blocks
            >= self.config.early_recovery_max_total_blocks)
        if recovery_exhausted and self.stage != "isolated_press":
            self.early_recovery_exhausted = True
            self.early_recovery_focus_finger = 0
            self.early_recovery_focus_iteration = 0
            self.early_recovery_weights = self._balanced_recovery_weights()
            self.early_recovery_last_switch_reason = "max_total_blocks"
            self.recent.clear()
            self.stalled = True
            return
        drops = {
            finger: (
                self.early_recovery_best_rates.get(finger, -1.0)
                - rates.get(finger, -1.0))
            for finger in available
            if ((self.stage == "isolated_press" or finger != current)
                and self.early_recovery_best_rates.get(finger, -1.0) >= 0.0
                and rates.get(finger, -1.0) >= 0.0)
        }
        self.early_recovery_retention_max_drop = max(
            drops.values(), default=0.0)
        if self.stage == "isolated_press":
            self.early_recovery_focus_iteration = 0
            for finger, rate in rates.items():
                self.early_recovery_best_rates[finger] = max(
                    self.early_recovery_best_rates.get(finger, -1.0), rate)
            previous = current
            self.early_recovery_weights = (
                self._adaptive_early_recovery_weights(rates))
            next_focus = (
                self._weighted_recovery_finger(
                    self.early_recovery_weights, available))
            if recovery_exhausted:
                self.early_recovery_exhausted = True
                self.early_recovery_focus_finger = 0
                self.early_recovery_last_switch_reason = "max_total_blocks"
            else:
                self.early_recovery_focus_finger = next_focus
            if not recovery_exhausted and next_focus != previous:
                self.early_recovery_count += 1
            self.early_recovery_focus_blocks = 0
            if not recovery_exhausted:
                self.early_recovery_last_switch_reason = (
                    "adaptive_retention"
                    if self.early_recovery_retention_max_drop
                    > self.config.early_recovery_retention_drop_tolerance
                    else "adaptive_deficit")
            self.recent.clear()
            return
        retention = [
            finger for finger, drop in drops.items()
            if drop > self.config.early_recovery_retention_drop_tolerance]
        candidate = None
        reason = "hold"
        if retention:
            candidate = max(retention, key=lambda finger: (drops[finger], -finger))
            reason = "retention_drop"
        elif (self.early_recovery_focus_blocks
              >= self.config.early_recovery_max_focus_blocks):
            unmastered = [
                finger for finger in available
                if (finger != current
                    and rates.get(finger, -1.0)
                    < self.config.promotion_success_rate)]
            if unmastered:
                candidate = min(
                    unmastered,
                    key=lambda finger: (rates.get(finger, -1.0), finger))
                reason = "block_limit"
        if candidate is None:
            weakest = self._weakest_early_finger()
            if (weakest != current
                    and (rates.get(weakest, -1.0) < 0.0
                         or rates.get(current, -1.0)
                         - rates.get(weakest, -1.0)
                         >= self.config.early_recovery_switch_margin)):
                candidate = weakest
                reason = "weaker_finger"
        self.early_recovery_focus_iteration = 0
        if candidate is not None and candidate != current:
            self.early_recovery_focus_finger = candidate
            self.early_recovery_count += 1
            self.early_recovery_focus_blocks = 0
            self.early_recovery_last_switch_reason = reason
            self.recent.clear()
        else:
            self.early_recovery_last_switch_reason = "hold"
        for finger, rate in rates.items():
            self.early_recovery_best_rates[finger] = max(
                self.early_recovery_best_rates.get(finger, -1.0), rate)

    def _early_recovery_focus_finger(self):
        if (self.stage in self.EARLY_SINGLE_FINGER_STAGES
                and self.stage != "integrated_press"
                and self.stalled
                and not self.early_recovery_exhausted):
            return self.early_recovery_focus_finger
        return 0

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

    def _normalize_frozen_context_weights(self, values):
        values = tuple(float(value) for value in values)
        if len(values) != 4:
            raise ValueError("frozen-context weights must contain four values")
        available = self.required_song_fingers or tuple(range(1, 5))
        normalized = [
            max(values[finger - 1], 0.0) if finger in available else 0.0
            for finger in range(1, 5)
        ]
        total = sum(normalized)
        if not math.isfinite(total) or total <= 0.0:
            uniform = 1.0 / len(available)
            return tuple(
                uniform if finger in available else 0.0
                for finger in range(1, 5))
        return tuple(value / total for value in normalized)

    def _initial_frozen_context_weights(self):
        return self._normalize_frozen_context_weights(
            self.config.frozen_context_initial_finger_weights)

    def _reset_frozen_context_recovery(self, reason):
        self.frozen_context_focus_finger = 0
        self._reset_frozen_context_focus_evidence()
        self.frozen_context_recovery_active = True
        self.frozen_context_recovery_iteration = 0
        self.frozen_context_recovery_block_count = 0
        self.frozen_context_recovery_ready_streak = 0
        self.frozen_context_recovery_exhausted = False
        self.frozen_context_recovery_failed = False
        self.frozen_context_recovery_completed_iteration = -1
        self.frozen_context_evaluation_started_iteration = -1
        self.frozen_context_recovery_weights = (
            self._initial_frozen_context_weights())
        self.frozen_context_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_distances = {
            finger: float("inf") for finger in range(1, 5)}
        self.frozen_context_recovery_retention_max_drop = 0.0
        self.frozen_context_recovery_last_update_reason = str(reason)
        self.frozen_context_sampler_update_count = 0

    def _reset_frozen_context_evaluation(self, reason):
        self._reset_bridge_evidence(reset_regression=True)
        self.frozen_context_evaluation_started = False
        self.frozen_context_evaluation_started_iteration = -1
        self.frozen_context_evidence_reset_count += 1
        self.frozen_context_evidence_reset_reason = str(reason)

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
        self.chord_evidence_age = 0
        self.chord_evidence_stalled = False

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
        self.goal_pair_mastery_verified_since_recovery = [False] * 4
        self.goal_pair_mastery_streaks = [0] * 4
        self.goal_pair_mastery_fail_streaks = [0] * 4
        self.goal_pair_focus_scores = [None] * 4
        self._reset_goal_pair_phase_evidence()

    def load_context(self, context):
        source_schema = int(
            context.get("curriculum_schema_version", 1))
        self._reset_early_stage_evidence()
        self.early_recovery_focus_finger = 0
        self.early_recovery_focus_iteration = 0
        self.early_recovery_count = 0
        self.early_recovery_focus_blocks = 0
        self.early_recovery_total_blocks = 0
        self.early_recovery_exhausted = False
        self.early_recovery_weights = (0.25, 0.25, 0.25, 0.25)
        self.early_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.early_recovery_last_switch_reason = ""
        self.early_recovery_retention_max_drop = 0.0
        self.practice_focus_reset_count = 0
        self.practice_focus_reset_consecutive = 0
        self.integrated_recovery_active = False
        self.integrated_recovery_focus_finger = 0
        self.integrated_recovery_iteration = 0
        self.integrated_recovery_count = 0
        self.integrated_recovery_total_iteration = 0
        self.integrated_recovery_block_count = 0
        self.integrated_recovery_weights = (0.25, 0.25, 0.25, 0.25)
        self.integrated_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.integrated_recovery_block_start_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.integrated_recovery_retention_max_drop = 0.0
        self.integrated_recovery_min_rate_improvement = 0.0
        self.integrated_recovery_no_improvement_blocks = 0
        self.integrated_recovery_exhausted = False
        self.integrated_recovery_last_update_reason = ""
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
        self.frozen_context_evaluation_started = False
        self.frozen_context_focus_finger = 0
        self._reset_frozen_context_focus_evidence()
        self.frozen_context_recovery_active = True
        self.frozen_context_recovery_iteration = 0
        self.frozen_context_recovery_block_count = 0
        self.frozen_context_recovery_ready_streak = 0
        self.frozen_context_recovery_exhausted = False
        self.frozen_context_recovery_failed = False
        self.frozen_context_recovery_completed_iteration = -1
        self.frozen_context_evaluation_started_iteration = -1
        self.frozen_context_recovery_weights = tuple(
            float(value)
            for value in self.config.frozen_context_initial_finger_weights)
        self.frozen_context_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.frozen_context_recovery_last_distances = {
            finger: float("inf") for finger in range(1, 5)}
        self.frozen_context_recovery_retention_max_drop = 0.0
        self.frozen_context_recovery_last_update_reason = "load"
        self.frozen_context_sampler_update_count = 0
        self.frozen_context_evidence_reset_count = 0
        self.frozen_context_evidence_reset_reason = "load"
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
        self.static_chord_recovery_active = False
        self.static_chord_recovery_count = 0
        self.static_chord_recovery_signatures = ()
        self.static_chord_recovery_reason = ""
        self.static_chord_blocked = False
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
            frozen_evaluation_migration = (
                source_schema < self.FROZEN_EVALUATION_SCHEMA_VERSION
                and self.stage == "frozen_context")
            static_chord_catalog_migration = (
                source_schema < self.STATIC_CHORD_CATALOG_SCHEMA_VERSION
                and stage in self.STATIC_CHORD_STAGES)
            self.stage_iteration = (
                0 if (legacy_stage or legacy_goal_pair_phase
                      or frozen_evaluation_migration
                      or static_chord_catalog_migration
                      or (source_schema < 3
                          and stage == "chord_fine_reach"))
                else int(context.get("curriculum_stage_iteration", 0)))
            self.total_iteration = int(context.get("curriculum_total_iteration", 0))
            self.stalled = (
                False if (legacy_stage or legacy_goal_pair_phase
                          or frozen_evaluation_migration)
                else bool(context.get("curriculum_stalled", False)))
            if source_schema >= 48:
                saved_evidence = context.get(
                    "curriculum_early_stage_evidence", {})
                for finger, row in self.early_stage_evidence.items():
                    saved = saved_evidence.get(
                        str(finger), saved_evidence.get(finger, {}))
                    if not isinstance(saved, dict):
                        continue
                    for key in ("success", "target"):
                        value = float(saved.get(key, 0.0))
                        if math.isfinite(value) and value >= 0.0:
                            row[key] = value
                self._restore_early_stage_evidence_history()
                if source_schema >= 52:
                    saved_age = context.get(
                        "curriculum_early_evidence_age", {})
                    saved_recent = context.get(
                        "curriculum_early_recent_episode_counts", {})
                    for finger in range(1, 5):
                        self.early_stage_evidence_age[finger] = max(0, int(
                            saved_age.get(
                                str(finger), saved_age.get(finger, 0))))
                        recent = max(0.0, float(saved_recent.get(
                            str(finger), saved_recent.get(finger, 0.0))))
                        if recent > 0.0:
                            self._early_stage_recent_targets[finger].append(
                                recent)
                    self.practice_focus_reset_count = max(0, int(
                        context.get(
                            "curriculum_practice_focus_reset_count", 0)))
                    self.practice_focus_reset_consecutive = max(0, int(
                        context.get(
                            "curriculum_practice_focus_reset_consecutive",
                            0)))
                if self.stage == "integrated_press":
                    self.integrated_recovery_active = bool(context.get(
                        "curriculum_integrated_recovery", False))
                    self.integrated_recovery_focus_finger = int(context.get(
                        "curriculum_integrated_recovery_focus_finger", 0))
                    self.integrated_recovery_iteration = max(0, int(
                        context.get(
                            "curriculum_integrated_recovery_iteration", 0)))
                    self.integrated_recovery_count = max(0, int(context.get(
                        "curriculum_integrated_recovery_count", 0)))
                    if source_schema >= 51:
                        self.integrated_recovery_total_iteration = max(0, int(
                            context.get(
                                "curriculum_integrated_recovery_total_iteration",
                                0)))
                        self.integrated_recovery_block_count = max(0, int(
                            context.get(
                                "curriculum_integrated_recovery_block_count",
                                0)))
                        saved_weights = tuple(float(value) for value in context.get(
                            "curriculum_integrated_recovery_weights",
                            (0.25, 0.25, 0.25, 0.25)))
                        if (len(saved_weights) != 4
                                or any(not math.isfinite(value) or value < 0.0
                                       for value in saved_weights)
                                or abs(sum(saved_weights) - 1.0) > 1e-6):
                            raise ValueError(
                                "saved integrated recovery weights are invalid")
                        self.integrated_recovery_weights = saved_weights
                        saved_best = context.get(
                            "curriculum_integrated_recovery_best_rates", {})
                        saved_start = context.get(
                            "curriculum_integrated_recovery_block_start_rates",
                            {})
                        self.integrated_recovery_best_rates = {
                            finger: float(saved_best.get(
                                str(finger), saved_best.get(finger, -1.0)))
                            for finger in range(1, 5)}
                        self.integrated_recovery_block_start_rates = {
                            finger: float(saved_start.get(
                                str(finger), saved_start.get(finger, -1.0)))
                            for finger in range(1, 5)}
                        self.integrated_recovery_retention_max_drop = max(
                            0.0, float(context.get(
                                "curriculum_integrated_recovery_retention_max_drop",
                                0.0)))
                        self.integrated_recovery_min_rate_improvement = float(
                            context.get(
                                "curriculum_integrated_recovery_min_rate_improvement",
                                0.0))
                        self.integrated_recovery_no_improvement_blocks = max(
                            0, int(context.get(
                                "curriculum_integrated_recovery_no_improvement_blocks",
                                0)))
                        self.integrated_recovery_exhausted = bool(context.get(
                            "curriculum_integrated_recovery_exhausted", False))
                        self.integrated_recovery_last_update_reason = str(
                            context.get(
                                "curriculum_integrated_recovery_last_update_reason",
                                ""))
                    elif self.integrated_recovery_active:
                        rates = self._early_stage_rates()
                        self.integrated_recovery_iteration = 0
                        self.integrated_recovery_best_rates = dict(rates)
                        self.integrated_recovery_block_start_rates = dict(rates)
                        self.integrated_recovery_weights = (
                            self._adaptive_integrated_recovery_weights(rates))
                        self.integrated_recovery_focus_finger = (
                            self._integrated_recovery_weighted_finger())
                elif (self.stage in self.EARLY_SINGLE_FINGER_STAGES
                      and self.stalled):
                    saved_focus = int(context.get(
                        "curriculum_early_recovery_focus_finger", 0))
                    self.early_recovery_focus_finger = (
                        saved_focus if 1 <= saved_focus <= 4
                        else self._weakest_early_finger())
                    if source_schema >= 49:
                        self.early_recovery_focus_iteration = max(0, int(
                            context.get(
                                "curriculum_early_recovery_focus_iteration",
                                0)))
                        self.early_recovery_count = max(0, int(context.get(
                            "curriculum_early_recovery_count", 0)))
                    if source_schema >= 50:
                        self.early_recovery_focus_blocks = max(0, int(
                            context.get(
                                "curriculum_early_recovery_focus_blocks", 0)))
                        self.early_recovery_total_blocks = max(0, int(
                            context.get(
                                "curriculum_early_recovery_total_blocks", 0)))
                        saved_best = context.get(
                            "curriculum_early_recovery_best_rates", {})
                        self.early_recovery_best_rates = {
                            finger: float(saved_best.get(
                                str(finger), saved_best.get(finger, -1.0)))
                            for finger in range(1, 5)}
                        self.early_recovery_last_switch_reason = str(
                            context.get(
                                "curriculum_early_recovery_last_switch_reason",
                                ""))
                        self.early_recovery_retention_max_drop = max(
                            0.0, float(context.get(
                                "curriculum_early_recovery_retention_max_drop",
                                0.0)))
                        if source_schema >= 53:
                            saved_weights = tuple(float(value) for value in
                                context.get(
                                    "curriculum_early_recovery_weights",
                                    (0.25, 0.25, 0.25, 0.25)))
                            if (len(saved_weights) != 4
                                    or any(not math.isfinite(value)
                                           or value < 0.0
                                           for value in saved_weights)
                                    or abs(sum(saved_weights) - 1.0) > 1e-6):
                                raise ValueError(
                                    "saved early recovery weights are invalid")
                            self.early_recovery_weights = saved_weights
                        elif (self.stage == "isolated_press"
                              and not self.early_recovery_exhausted):
                            self.early_recovery_weights = (
                                self._adaptive_early_recovery_weights(
                                    self._early_stage_rates()))
                        if source_schema >= 52:
                            self.early_recovery_exhausted = bool(context.get(
                                "curriculum_early_recovery_exhausted", False))
                            if self.early_recovery_exhausted:
                                self.early_recovery_focus_finger = 0
                                if source_schema < 54:
                                    self.early_recovery_weights = (
                                        self._balanced_recovery_weights())
                        elif (self.early_recovery_total_blocks
                              >= self.config.early_recovery_max_total_blocks):
                            self.early_recovery_exhausted = True
                            self.early_recovery_focus_finger = 0
                            self.early_recovery_weights = (
                                self._balanced_recovery_weights())
                            self.early_recovery_last_switch_reason = (
                                "migrated_max_total_blocks")
                    else:
                        self.early_recovery_best_rates = (
                            self._early_stage_rates())
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
                if source_schema >= 45:
                    self.static_chord_recovery_active = bool(context.get(
                        "curriculum_static_chord_recovery", False))
                    self.static_chord_recovery_count = max(0, int(
                        context.get(
                            "curriculum_static_chord_recovery_count", 0)))
                    self.static_chord_recovery_signatures = tuple(
                        int(value) for value in context.get(
                            "curriculum_static_chord_recovery_signatures", ()))
                    self.static_chord_recovery_reason = str(context.get(
                        "curriculum_static_chord_recovery_reason", ""))
                    self.static_chord_blocked = bool(context.get(
                        "curriculum_static_chord_blocked", False))
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
            if (source_schema >= self.FROZEN_EVALUATION_SCHEMA_VERSION
                    and self.stage == "frozen_context"
                    and not legacy_stage):
                self.frozen_context_final_applied = bool(context.get(
                    "curriculum_frozen_context_final_applied", False))
            if source_schema < 6 and self.stage in self.BRIDGE_STAGES:
                self.recent.clear()
            if (source_schema >= 6
                    and not legacy_stage
                    and not legacy_goal_pair_phase
                    and not frozen_evaluation_migration):
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
                    verified = context.get(
                        "curriculum_goal_pair_mastery_verified_since_recovery",
                        ())
                    if source_schema >= 58:
                        if len(verified) == 4:
                            self.goal_pair_mastery_verified_since_recovery = [
                                bool(value) for value in verified]
                        else:
                            self.goal_pair_mastery_verified_since_recovery = [
                                False] * 4
                    else:
                        self.goal_pair_mastery_verified_since_recovery = list(
                            self.goal_pair_mastered_fingers)
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
            if (source_schema >= self.FROZEN_EVALUATION_SCHEMA_VERSION
                    and self.stage == "frozen_context"
                    and not legacy_stage):
                self.frozen_context_focus_finger = 0
                saved_evidence = context.get(
                    "curriculum_frozen_context_focus_evidence", {})
                restored = self._empty_frozen_context_focus_evidence()
                for key in restored:
                    value = float(saved_evidence.get(key, 0.0))
                    if math.isfinite(value) and value >= 0.0:
                        restored[key] = value
                self.frozen_context_focus_evidence = restored
                self.frozen_context_evaluation_started = bool(context.get(
                    "curriculum_frozen_context_evaluation_started", False))
                self.frozen_context_recovery_active = bool(context.get(
                    "curriculum_frozen_context_recovery_active", True))
                self.frozen_context_recovery_iteration = max(0, int(
                    context.get(
                        "curriculum_frozen_context_recovery_iteration", 0)))
                self.frozen_context_recovery_block_count = max(0, int(
                    context.get(
                        "curriculum_frozen_context_recovery_block_count", 0)))
                self.frozen_context_recovery_ready_streak = max(0, int(
                    context.get(
                        "curriculum_frozen_context_recovery_ready_streak", 0)))
                self.frozen_context_recovery_exhausted = bool(context.get(
                    "curriculum_frozen_context_recovery_exhausted", False))
                self.frozen_context_recovery_failed = bool(context.get(
                    "curriculum_frozen_context_recovery_failed", False))
                self.frozen_context_recovery_completed_iteration = max(
                    -1, int(context.get(
                        "curriculum_frozen_context_recovery_completed_iteration",
                        -1)))
                self.frozen_context_evaluation_started_iteration = max(
                    -1, int(context.get(
                        "curriculum_frozen_context_evaluation_started_iteration",
                        self.stage_iteration
                        if self.frozen_context_evaluation_started else -1)))
                weights = tuple(float(value) for value in context.get(
                    "curriculum_frozen_context_recovery_weights",
                    self.config.frozen_context_initial_finger_weights))
                self.frozen_context_recovery_weights = (
                    self._normalize_frozen_context_weights(weights))
                for attribute, key in (
                        ("frozen_context_recovery_best_rates",
                         "curriculum_frozen_context_recovery_best_rates"),
                        ("frozen_context_recovery_last_rates",
                         "curriculum_frozen_context_recovery_last_rates")):
                    saved = context.get(key, {})
                    setattr(self, attribute, {
                        finger: float(saved.get(
                            str(finger), saved.get(finger, -1.0)))
                        for finger in range(1, 5)})
                saved_distances = context.get(
                    "curriculum_frozen_context_recovery_last_distances", {})
                self.frozen_context_recovery_last_distances = {}
                for finger in range(1, 5):
                    distance = float(saved_distances.get(
                        str(finger), saved_distances.get(
                            finger, float("inf"))))
                    self.frozen_context_recovery_last_distances[finger] = (
                        distance
                        if math.isfinite(distance) and distance >= 0.0
                        else float("inf"))
                self.frozen_context_recovery_retention_max_drop = max(
                    0.0, float(context.get(
                        "curriculum_frozen_context_recovery_retention_max_drop",
                        0.0)))
                self.frozen_context_recovery_last_update_reason = str(
                    context.get(
                        "curriculum_frozen_context_recovery_last_update_reason",
                        "restored"))
                self.frozen_context_sampler_update_count = max(0, int(
                    context.get(
                        "curriculum_frozen_context_sampler_update_count", 0)))
                self.frozen_context_evidence_reset_count = max(0, int(
                    context.get(
                        "curriculum_frozen_context_evidence_reset_count", 0)))
                self.frozen_context_evidence_reset_reason = str(context.get(
                    "curriculum_frozen_context_evidence_reset_reason", ""))
                if self.frozen_context_recovery_failed:
                    self.frozen_context_recovery_active = False
                    self.frozen_context_recovery_exhausted = True
                    self.stalled = True
        if (restore_saved_stage
                and self.stage in self.EARLY_SINGLE_FINGER_STAGES
                and self.stage != "integrated_press"
                and self.stalled):
            self.recent.clear()

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

    def _recovery_focus_indices(self):
        signatures = set(self.static_chord_recovery_signatures)
        return tuple(
            index for index, finger_set in enumerate(self.chord_available_sets)
            if self._finger_set_signature(finger_set) in signatures)

    def _chord_fine_soft_floor_passes(self, stats):
        p90 = float(stats.get(
            "curriculum_p90_target_distance", float("inf")))
        alignment = float(stats.get(
            "curriculum_cell_alignment_rate", -1.0))
        if (not math.isfinite(p90)
                or p90 > self.config.chord_fine_soft_p90_distance
                or alignment < self.config.chord_fine_soft_alignment_rate):
            return False
        rates = [
            self._chord_set_rate(stats, self._finger_set_signature(finger_set))
            for finger_set in self.chord_available_sets
        ]
        return bool(rates) and all(
            rate >= self.config.chord_fine_soft_success_rate
            for rate in rates)

    def _static_chord_failure_signatures(self, stats):
        failed = []
        for finger_set in self.chord_available_sets:
            signature = self._finger_set_signature(finger_set)
            rate = self._chord_set_rate(stats, signature)
            if rate < self.config.promotion_success_rate:
                failed.append(signature)
        return tuple(failed) or tuple(
            self._finger_set_signature(finger_set)
            for finger_set in self.chord_available_sets)

    def _start_static_chord_recovery(self, stats):
        if (self.forced_stage is not None
                or self.static_chord_recovery_count
                >= self.config.static_chord_recovery_max_cycles):
            self.static_chord_blocked = True
            self.static_chord_recovery_reason = "recovery_exhausted"
            self.stalled = True
            return False
        self.static_chord_recovery_signatures = (
            self._static_chord_failure_signatures(stats))
        self.chord_unresolved_signatures = list(
            self.static_chord_recovery_signatures)
        self.static_chord_recovery_active = True
        self.static_chord_recovery_count += 1
        self.static_chord_recovery_reason = "static_chord_timeout"
        self.static_chord_blocked = False
        self.stage = "chord_fine_reach"
        self.stage_iteration = 0
        self.chord_focus_cycle = 0
        indices = self._recovery_focus_indices()
        self.chord_focus_index = indices[0] if indices else -1
        self._reset_chord_focus_window()
        return True

    def _finish_static_chord_recovery(self):
        self.stage = "static_chord"
        self.stage_iteration = 0
        self.chord_focus_index = -1
        self.chord_focus_iteration = 0
        self.static_chord_recovery_active = False
        self.static_chord_recovery_reason = "retest"
        self.stalled = False
        self.recent.clear()
        self._reset_chord_phase_evidence()

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

    def _frozen_context_phase(self):
        if self.stage != "frozen_context":
            return ""
        if self.frozen_context_recovery_failed:
            return "recovery_failed"
        if self.frozen_context_evaluation_started:
            return "evaluation"
        if self.frozen_context_recovery_active:
            return "recovery"
        return "evaluation_settle"

    def _frozen_context_evaluation_settle_iteration(self):
        if (self.stage != "frozen_context"
                or self.frozen_context_recovery_completed_iteration < 0):
            return 0
        target = max(
            int(self.config.frozen_context_final_evaluation_iterations), 0)
        age = max(
            int(self.stage_iteration)
            - int(self.frozen_context_recovery_completed_iteration),
            0)
        return min(age, target)

    def _frozen_context_recovery_teacher_scale(self):
        if (self.stage != "frozen_context"
                or not self.frozen_context_recovery_active
                or self.frozen_context_recovery_failed):
            return 0.0
        fingers = self.required_song_fingers or tuple(range(1, 5))
        press_target = self.config.frozen_context_recovery_press_rate
        distance_target = self.config.frozen_context_recovery_distance
        distance_full_assist = 2.0 * distance_target
        worst_scale = 0.0
        for finger in fingers:
            rate = float(
                self.frozen_context_recovery_last_rates.get(finger, -1.0))
            if not math.isfinite(rate) or rate < 0.0 or rate <= 0.50:
                press_scale = 1.0
            elif rate >= press_target:
                press_scale = 0.0
            else:
                press_scale = (
                    (press_target - rate)
                    / max(press_target - 0.50, 1e-9))
            distance = float(
                self.frozen_context_recovery_last_distances.get(
                    finger, float("inf")))
            if not math.isfinite(distance) or distance < 0.0:
                distance_scale = 1.0
            elif distance <= distance_target:
                distance_scale = 0.0
            elif distance >= distance_full_assist:
                distance_scale = 1.0
            else:
                distance_scale = (
                    (distance - distance_target)
                    / max(distance_full_assist - distance_target, 1e-9))
            worst_scale = max(worst_scale, press_scale, distance_scale)
        return min(max(worst_scale, 0.0), 1.0)

    def _accumulate_frozen_context_recovery_stats(self, stats):
        evidence = self.frozen_context_focus_evidence
        fingers = self.required_song_fingers or range(1, 5)
        episodes = float(stats.get("episodes", 0.0))
        if not math.isfinite(episodes) or episodes < 0.0:
            episodes = 0.0
        for finger in fingers:
            count = float(stats.get(
                f"finger_{finger}_press_target_frames",
                episodes * float(stats.get(
                    f"press_finger_{finger}_count", 0.0))))
            success = float(stats.get(
                f"finger_{finger}_press_success_frames",
                episodes * float(stats.get(
                    f"press_finger_{finger}_success", 0.0))))
            if (math.isfinite(count) and math.isfinite(success)
                    and count > 0.0 and 0.0 <= success <= count):
                evidence[f"finger_{finger}_press_count"] += count
                evidence[f"finger_{finger}_press_success"] += success
        for finger in fingers:
            distance_count = float(stats.get(
                f"finger_{finger}_target_distance_active_frames", 0.0))
            distance_sum = float(stats.get(
                f"finger_{finger}_target_distance_sum", float("nan")))
            if (math.isfinite(distance_count) and distance_count > 0.0
                    and math.isfinite(distance_sum) and distance_sum >= 0.0):
                evidence[f"finger_{finger}_distance_count"] += (
                    distance_count)
                evidence[f"finger_{finger}_distance_sum"] += (
                    distance_sum)

    def _frozen_context_recovery_rates(self):
        evidence = self.frozen_context_focus_evidence
        return {
            finger: (
                evidence[f"finger_{finger}_press_success"]
                / evidence[f"finger_{finger}_press_count"]
                if evidence[f"finger_{finger}_press_count"] > 0.0
                else -1.0)
            for finger in range(1, 5)
        }

    def _frozen_context_recovery_focus_fingers(self):
        available = self.required_song_fingers or tuple(range(1, 5))
        baseline = 1.0 / len(available)
        focused = tuple(
            finger for finger in available
            if self.frozen_context_recovery_weights[finger - 1]
                > baseline + 0.025)
        if focused:
            return focused
        if not self.frozen_context_recovery_active:
            return ()
        rates = self.frozen_context_recovery_last_rates
        known = [
            (rates.get(finger, -1.0), finger)
            for finger in available
            if rates.get(finger, -1.0) >= 0.0]
        return (min(known)[1],) if known else ()

    def _adaptive_frozen_context_weights(
            self, rates, distances=None, retention=None):
        available = self.required_song_fingers or tuple(range(1, 5))
        floor = min(
            float(self.config.frozen_context_recovery_min_finger_probability),
            1.0 / len(available))
        cap = max(
            float(self.config.frozen_context_recovery_max_finger_probability),
            1.0 / len(available))
        current = self._normalize_frozen_context_weights(
            self.frozen_context_recovery_weights)

        def distance_ok(finger):
            if distances is None:
                return True
            distance = float(distances.get(finger, float("nan")))
            return (
                math.isfinite(distance)
                and distance <= self.config.frozen_context_recovery_distance)

        def recovered(finger):
            rate = float(rates.get(finger, -1.0))
            return (
                math.isfinite(rate)
                and rate >= self.config.frozen_context_recovery_press_rate
                and distance_ok(finger)
                and (retention is None
                     or bool(retention.get(finger, False))))

        if all(recovered(finger) for finger in available):
            uniform = 1.0 / len(available)
            return tuple(
                uniform if finger in available else 0.0
                for finger in range(1, 5))

        weights = {finger: floor for finger in available}
        remaining = max(0.0, 1.0 - floor * len(available))
        ranked = sorted(
            available,
            key=lambda finger: (
                recovered(finger),
                float(rates.get(finger, -1.0)),
                -float(distances.get(finger, 0.0))
                    if distances is not None
                    and math.isfinite(float(
                        distances.get(finger, float("nan"))))
                    else 0.0,
                current[finger - 1],
                finger,
            ))
        for finger in ranked:
            addition = min(
                remaining,
                max(0.0, cap - weights[finger]))
            weights[finger] += addition
            remaining -= addition
            if remaining <= 1e-12:
                break
        if remaining > 1e-12:
            share = remaining / len(available)
            for finger in available:
                weights[finger] += share
        proposal = tuple(
            weights.get(finger, 0.0) for finger in range(1, 5))
        return self._normalize_frozen_context_weights(proposal)

    def _sync_frozen_context_recovery(self):
        if (self.stage != "frozen_context"
                or not self.frozen_context_recovery_active
                or self.frozen_context_recovery_failed
                or self.frozen_context_evaluation_started):
            return False
        if (self.frozen_context_recovery_iteration
                < self.config.frozen_context_recovery_block_iterations):
            return False
        evidence = self.frozen_context_focus_evidence
        minimum = self.config.frozen_context_focus_min_evidence
        fingers = self.required_song_fingers or tuple(range(1, 5))

        rates = self._frozen_context_recovery_rates()
        distances = {}
        retained = {}
        missing_evidence = []
        maximum_drop = 0.0
        drop_tolerance = (
            self.config.frozen_context_recovery_retention_drop_tolerance)
        for finger in fingers:
            rate = rates[finger]
            best = self.frozen_context_recovery_best_rates.get(finger, -1.0)
            press_count = evidence[f"finger_{finger}_press_count"]
            distance_count = evidence[f"finger_{finger}_distance_count"]
            evidence_ready = (
                press_count >= minimum and distance_count >= minimum)
            if not evidence_ready:
                missing_evidence.append(finger)
            drop = (
                max(best - rate, 0.0)
                if evidence_ready and best >= 0.0 else 0.0)
            if evidence_ready and best >= 0.0:
                maximum_drop = max(maximum_drop, drop)
            if evidence_ready:
                self.frozen_context_recovery_best_rates[finger] = max(
                    best, rate)
            distance = (
                evidence[f"finger_{finger}_distance_sum"]
                / distance_count
                if evidence_ready else float("inf"))
            distances[finger] = distance
            distance_ok = (
                distance <= self.config.frozen_context_recovery_distance)
            retained[finger] = (
                evidence_ready
                and rate >= self.config.frozen_context_recovery_press_rate
                and distance_ok
                and drop <= drop_tolerance)
        self.frozen_context_recovery_last_rates = dict(rates)
        self.frozen_context_recovery_last_distances = {
            finger: float(distances.get(finger, float("inf")))
            for finger in range(1, 5)}
        self.frozen_context_recovery_retention_max_drop = max(
            0.0, maximum_drop)
        if all(retained.values()):
            self.frozen_context_recovery_ready_streak += 1
        else:
            self.frozen_context_recovery_ready_streak = 0
        completed = (
            self.frozen_context_recovery_ready_streak
            >= self.config.frozen_context_recovery_ready_blocks)

        proposal = self._adaptive_frozen_context_weights(
            rates, distances=distances, retention=retained)
        smoothing = self.config.frozen_context_recovery_weight_smoothing
        current = self._normalize_frozen_context_weights(
            self.frozen_context_recovery_weights)
        blended = self._normalize_frozen_context_weights(tuple(
            (1.0 - smoothing) * old + smoothing * new
            for old, new in zip(current, proposal)))
        change = sum(abs(left - right) for left, right in zip(current, blended))
        changed = (
            change >= self.config.frozen_context_recovery_min_weight_change)
        if changed:
            self.frozen_context_recovery_weights = blended
            self.frozen_context_sampler_update_count += 1
        focused = max(
            fingers,
            key=lambda finger: (
                self.frozen_context_recovery_weights[finger - 1],
                -finger))
        self.frozen_context_recovery_last_update_reason = (
            f"insufficient_evidence:{','.join(map(str, missing_evidence))}"
            if missing_evidence
            else (f"rank_focus:{focused}" if changed
                  else f"rank_stable:{focused}"))
        self.frozen_context_recovery_block_count += 1
        if completed:
            self.frozen_context_recovery_active = False
            self.frozen_context_recovery_exhausted = False
            self.frozen_context_recovery_failed = False
            self.frozen_context_recovery_completed_iteration = int(
                self.stage_iteration)
            self.frozen_context_recovery_last_update_reason = (
                "recovery_completed")
            self.stalled = False
        elif (self.frozen_context_recovery_block_count
                >= self.config.frozen_context_recovery_max_blocks):
            self.frozen_context_recovery_active = False
            self.frozen_context_recovery_exhausted = True
            self.frozen_context_recovery_failed = True
            self.frozen_context_recovery_last_update_reason = (
                "max_blocks")
            self.stalled = True
        else:
            self.frozen_context_recovery_active = True
            self.frozen_context_recovery_exhausted = False
            self.frozen_context_recovery_failed = False
            self.stalled = False
        self.frozen_context_recovery_iteration = 0
        self._reset_frozen_context_focus_evidence()
        self.frozen_context_focus_finger = 0
        return changed

    def _start_frozen_context_evaluation(self):
        if (self.stage != "frozen_context"
                or self.frozen_context_evaluation_started
                or not self._frozen_context_evaluation_ready_by_time()):
            return False
        self._reset_bridge_evidence(reset_regression=True)
        self.recent.clear()
        self.stalled = False
        self.frozen_context_evaluation_started = True
        self.frozen_context_evaluation_started_iteration = int(
            self.stage_iteration)
        self.frozen_context_evidence_reset_count += 1
        self.frozen_context_evidence_reset_reason = "evaluation_start"
        return True

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

    def _integrated_control_phase(self):
        if self.stage != "integrated_press":
            return 3
        first, second, third = self.config.integrated_press_unlock_iterations
        age = (
            self.integrated_recovery_iteration
            if self.integrated_recovery_active else self.stage_iteration)
        if age < first:
            return 0
        if age < second:
            return 1
        if age < third:
            return 2
        return 3

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
        early_rates = self._early_stage_rates()
        early_required = self.required_song_fingers or (1, 2, 3, 4)
        early_known = all(
            early_rates.get(finger, -1.0) >= 0.0
            for finger in early_required)
        early_bottleneck_finger = (
            min(
                early_required,
                key=lambda finger: (early_rates[finger], finger))
            if early_known else 0)
        early_min_success_rate = (
            early_rates[early_bottleneck_finger]
            if early_bottleneck_finger > 0 else -1.0)
        early_recent = self._early_recent_episode_counts()
        early_starved = self._early_evidence_starved_fingers()
        integrated_phase = self._integrated_control_phase()
        early_recovery_focus = self._early_recovery_focus_finger()
        frozen_gate_failures = (
            self._bridge_gate_failures(self.bridge_last_metrics)
            if self.stage == "frozen_context" else ())
        goal_pair_gate = getattr(self, "goal_pair_last_gate_diagnostics", {})
        frozen_last = (
            self.bridge_last_metrics
            if self.stage == "frozen_context" else {})
        frozen_settle_target = int(
            self.config.frozen_context_final_evaluation_iterations)
        frozen_settle_iteration = (
            self._frozen_context_evaluation_settle_iteration())
        frozen_settle_progress = (
            min(
                frozen_settle_iteration / float(frozen_settle_target),
                1.0)
            if frozen_settle_target > 0
            else float(
                self.frozen_context_recovery_completed_iteration >= 0))
        frozen_recovery_teacher_scale = (
            self._frozen_context_recovery_teacher_scale())
        frozen_last_distances = {
            finger: (
                float(distance)
                if math.isfinite(float(distance)) and float(distance) >= 0.0
                else -1.0)
            for finger, distance
            in self.frozen_context_recovery_last_distances.items()
        }
        return {
            "curriculum_schema_version": self.SCHEMA_VERSION,
            "curriculum_stage": self.stage,
            "curriculum_stage_iteration": int(self.stage_iteration),
            "curriculum_total_iteration": int(self.total_iteration),
            "curriculum_random_start_probability": float(probability),
            "curriculum_stage_progress": float(progress),
            "curriculum_stalled": bool(self.stalled),
            "curriculum_early_min_success_rate": float(
                early_min_success_rate),
            "curriculum_early_bottleneck_finger": int(
                early_bottleneck_finger),
            "curriculum_early_stage_evidence": {
                str(finger): dict(row)
                for finger, row in self.early_stage_evidence.items()
            },
            "curriculum_early_evidence_required_per_finger": int(
                self.config.early_min_evidence_episodes_per_finger),
            "curriculum_early_evidence_window_per_finger": int(
                self.config.early_evidence_window_episodes_per_finger),
            "curriculum_early_evidence_stall_iterations": int(
                self.config.early_evidence_stall_iterations),
            "curriculum_early_evidence_recent_iterations": int(
                self.config.early_evidence_recent_iterations),
            "curriculum_early_evidence_stalled": bool(early_starved),
            "curriculum_early_evidence_starved_fingers": list(
                early_starved),
            "curriculum_early_evidence_age": {
                str(finger): int(age)
                for finger, age in self.early_stage_evidence_age.items()
            },
            "curriculum_early_recent_episode_counts": {
                str(finger): float(count)
                for finger, count in early_recent.items()
            },
            "curriculum_early_recovery": bool(
                early_recovery_focus > 0),
            "curriculum_early_recovery_adaptive": bool(
                self.stage == "isolated_press"
                and self.stalled),
            "curriculum_early_recovery_consolidation": bool(
                self.stage == "isolated_press"
                and self.stalled
                and self.early_recovery_exhausted),
            "curriculum_early_recovery_focus_finger": int(
                early_recovery_focus),
            "curriculum_early_recovery_focus_iteration": int(
                self.early_recovery_focus_iteration),
            "curriculum_early_recovery_focus_min_iterations": int(
                self.config.early_recovery_focus_min_iterations),
            "curriculum_early_recovery_focus_probability": float(
                self.config.early_recovery_focus_probability),
            "curriculum_early_recovery_weights": tuple(
                float(value) for value in self.early_recovery_weights),
            **{
                f"curriculum_early_recovery_finger_{finger}_weight": float(
                    self.early_recovery_weights[finger - 1])
                for finger in range(1, 5)
            },
            "curriculum_early_recovery_min_finger_probability": float(
                self.config.early_recovery_min_finger_probability),
            "curriculum_early_recovery_focus_blocks": int(
                self.early_recovery_focus_blocks),
            "curriculum_early_recovery_total_blocks": int(
                self.early_recovery_total_blocks),
            "curriculum_early_recovery_max_total_blocks": int(
                self.config.early_recovery_max_total_blocks),
            "curriculum_early_recovery_exhausted": bool(
                self.early_recovery_exhausted),
            "curriculum_early_recovery_max_focus_blocks": int(
                self.config.early_recovery_max_focus_blocks),
            "curriculum_early_recovery_retention_drop_tolerance": float(
                self.config.early_recovery_retention_drop_tolerance),
            "curriculum_early_recovery_retention_max_drop": float(
                self.early_recovery_retention_max_drop),
            "curriculum_early_recovery_last_switch_reason": str(
                self.early_recovery_last_switch_reason),
            "curriculum_early_recovery_best_rates": {
                str(finger): float(rate)
                for finger, rate in self.early_recovery_best_rates.items()
            },
            "curriculum_early_recovery_count": int(
                self.early_recovery_count),
            "curriculum_practice_focus_reset_count": int(
                self.practice_focus_reset_count),
            "curriculum_practice_focus_reset_consecutive": int(
                self.practice_focus_reset_consecutive),
            "curriculum_practice_reset_watchdog_iterations": int(
                self.config.practice_reset_watchdog_iterations),
            **{
                f"curriculum_early_finger_{finger}_episodes": float(
                    self.early_stage_evidence[finger]["target"])
                for finger in range(1, 5)
            },
            **{
                f"curriculum_early_finger_{finger}_success_rate": float(
                    early_rates[finger])
                for finger in range(1, 5)
            },
            **{
                f"curriculum_early_finger_{finger}_evidence_age": int(
                    self.early_stage_evidence_age[finger])
                for finger in range(1, 5)
            },
            **{
                f"curriculum_early_finger_{finger}_recent_episodes": float(
                    early_recent[finger])
                for finger in range(1, 5)
            },
            "curriculum_integrated_control_phase": int(integrated_phase),
            "curriculum_integrated_control_phase_label": (
                "finger_wrist", "elbow", "shoulder", "full"
            )[integrated_phase],
            "curriculum_integrated_recovery": bool(
                self.integrated_recovery_active),
            "curriculum_integrated_recovery_focus_finger": int(
                self.integrated_recovery_focus_finger),
            "curriculum_integrated_recovery_iteration": int(
                self.integrated_recovery_iteration),
            "curriculum_integrated_recovery_total_iteration": int(
                self.integrated_recovery_total_iteration),
            "curriculum_integrated_recovery_count": int(
                self.integrated_recovery_count),
            "curriculum_integrated_recovery_max_iterations": int(
                self.config.integrated_recovery_max_iterations),
            "curriculum_integrated_recovery_block_iterations": int(
                self.config.integrated_recovery_block_iterations),
            "curriculum_integrated_recovery_block_count": int(
                self.integrated_recovery_block_count),
            "curriculum_integrated_recovery_max_blocks": int(
                self.config.integrated_recovery_max_blocks),
            "curriculum_integrated_recovery_weights": tuple(
                float(value) for value in self.integrated_recovery_weights),
            **{
                f"curriculum_integrated_recovery_finger_{finger}_weight": float(
                    self.integrated_recovery_weights[finger - 1])
                for finger in range(1, 5)
            },
            "curriculum_integrated_recovery_best_rates": {
                str(finger): float(rate)
                for finger, rate in self.integrated_recovery_best_rates.items()
            },
            "curriculum_integrated_recovery_block_start_rates": {
                str(finger): float(rate)
                for finger, rate
                in self.integrated_recovery_block_start_rates.items()
            },
            "curriculum_integrated_recovery_retention_max_drop": float(
                self.integrated_recovery_retention_max_drop),
            "curriculum_integrated_recovery_min_rate_improvement": float(
                self.integrated_recovery_min_rate_improvement),
            "curriculum_integrated_recovery_no_improvement_blocks": int(
                self.integrated_recovery_no_improvement_blocks),
            "curriculum_integrated_recovery_exhausted": bool(
                self.integrated_recovery_exhausted),
            "curriculum_integrated_recovery_last_update_reason": str(
                self.integrated_recovery_last_update_reason),
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
            "curriculum_static_chord_recovery": bool(
                self.static_chord_recovery_active),
            "curriculum_static_chord_recovery_count": int(
                self.static_chord_recovery_count),
            "curriculum_static_chord_recovery_max_cycles": int(
                self.config.static_chord_recovery_max_cycles),
            "curriculum_static_chord_retest_max_iterations": int(
                self.config.static_chord_retest_max_iterations),
            "curriculum_static_chord_recovery_signatures": list(
                self.static_chord_recovery_signatures),
            "curriculum_static_chord_recovery_reason": (
                self.static_chord_recovery_reason),
            "curriculum_static_chord_blocked": bool(
                self.static_chord_blocked),
            "curriculum_chord_phase_evidence": {
                signature: dict(row)
                for signature, row in self.chord_phase_evidence.items()
            },
            "curriculum_chord_phase_evidence_required": int(
                self.config.chord_fine_min_phase_episodes),
            "curriculum_chord_evidence_age": int(
                self.chord_evidence_age),
            "curriculum_chord_evidence_stalled": bool(
                self.chord_evidence_stalled),
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
            "curriculum_frozen_context_phase":
                self._frozen_context_phase(),
            "curriculum_frozen_context_evaluation_started":
                bool(self.frozen_context_evaluation_started),
            "curriculum_frozen_context_evaluation_started_iteration": int(
                self.frozen_context_evaluation_started_iteration),
            "curriculum_frozen_context_evaluation_iteration": (
                max(
                    0,
                    self.stage_iteration
                    - self.frozen_context_evaluation_started_iteration)
                if self.stage == "frozen_context"
                and self.frozen_context_evaluation_started
                and self.frozen_context_evaluation_started_iteration >= 0
                else 0),
            "curriculum_frozen_context_evaluation_settle_iteration": int(
                frozen_settle_iteration),
            "curriculum_frozen_context_evaluation_settle_progress": float(
                frozen_settle_progress),
            "curriculum_frozen_context_evaluation_settle_target": int(
                frozen_settle_target),
            "curriculum_frozen_context_recovery_active": (
                bool(self.frozen_context_recovery_active)
                if self.stage == "frozen_context" else False),
            "curriculum_frozen_context_recovery_teacher_scale": float(
                frozen_recovery_teacher_scale),
            "curriculum_frozen_context_recovery_completed_iteration": int(
                self.frozen_context_recovery_completed_iteration),
            "curriculum_frozen_context_recovery_iteration":
                int(self.frozen_context_recovery_iteration),
            "curriculum_frozen_context_recovery_block_iterations":
                int(self.config.frozen_context_recovery_block_iterations),
            "curriculum_frozen_context_recovery_block_count":
                int(self.frozen_context_recovery_block_count),
            "curriculum_frozen_context_recovery_max_blocks":
                int(self.config.frozen_context_recovery_max_blocks),
            "curriculum_frozen_context_recovery_ready_streak":
                int(self.frozen_context_recovery_ready_streak),
            "curriculum_frozen_context_recovery_exhausted":
                bool(self.frozen_context_recovery_exhausted),
            "curriculum_frozen_context_recovery_failed":
                bool(self.frozen_context_recovery_failed),
            "curriculum_frozen_context_recovery_weights":
                list(self.frozen_context_recovery_weights),
            "curriculum_frozen_context_recovery_focus_fingers":
                list(self._frozen_context_recovery_focus_fingers()),
            "curriculum_required_song_fingers":
                list(self.required_song_fingers),
            **{
                f"curriculum_frozen_context_recovery_finger_{finger}_weight":
                    float(self.frozen_context_recovery_weights[finger - 1])
                for finger in range(1, 5)
            },
            "curriculum_frozen_context_recovery_best_rates":
                dict(self.frozen_context_recovery_best_rates),
            "curriculum_frozen_context_recovery_last_rates":
                dict(self.frozen_context_recovery_last_rates),
            "curriculum_frozen_context_recovery_last_distances":
                dict(frozen_last_distances),
            **{
                f"curriculum_frozen_context_recovery_finger_{finger}_rate":
                    float(self.frozen_context_recovery_last_rates[finger])
                for finger in range(1, 5)
            },
            **{
                f"curriculum_frozen_context_recovery_finger_{finger}_distance":
                    float(frozen_last_distances[finger])
                for finger in range(1, 5)
            },
            "curriculum_frozen_context_recovery_retention_max_drop":
                float(self.frozen_context_recovery_retention_max_drop),
            "curriculum_frozen_context_recovery_last_update_reason":
                self.frozen_context_recovery_last_update_reason,
            "curriculum_frozen_context_sampler_update_count":
                int(self.frozen_context_sampler_update_count),
            "curriculum_frozen_context_evidence_reset_count":
                int(self.frozen_context_evidence_reset_count),
            "curriculum_frozen_context_evidence_reset_reason":
                self.frozen_context_evidence_reset_reason,
            "curriculum_frozen_context_bridge_window_count":
                len(self.bridge_windows),
            "curriculum_frozen_context_bridge_window_target":
                int(self.config.bridge_promotion_windows),
            "curriculum_frozen_context_bridge_episode_progress":
                float(self.bridge_accumulator["episodes"]),
            "curriculum_frozen_context_bridge_episode_target":
                int(self.config.bridge_window_episodes),
            "curriculum_frozen_context_evaluation_last_f1":
                float(frozen_last.get("f1", -1.0)),
            "curriculum_frozen_context_evaluation_last_finger_min":
                float(frozen_last.get("finger_min", -1.0)),
            "curriculum_frozen_context_evaluation_last_no_press":
                float(frozen_last.get("no_press", -1.0)),
            "curriculum_frozen_context_evaluation_last_wrong":
                float(frozen_last.get("wrong", -1.0)),
            "curriculum_frozen_context_evaluation_last_sustain":
                float(frozen_last.get("sustain", -1.0)),
            "curriculum_frozen_context_evaluation_last_event_success":
                float(frozen_last.get("event_success", -1.0)),
            "curriculum_frozen_context_evaluation_last_dropout":
                float(frozen_last.get("dropout", -1.0)),
            "curriculum_frozen_context_evaluation_last_failure":
                float(frozen_last.get("failure", -1.0)),
            "curriculum_frozen_context_evaluation_failed_gates": (
                ",".join(frozen_gate_failures)
                if frozen_gate_failures else "none"),
            "curriculum_last_gate_failures": (
                ",".join(
                    list(goal_pair_gate.get("failures", ()))
                    + [f"{name}:insufficient_evidence" for name in
                       goal_pair_gate.get("evidence_shortages", ())]) or "none"
                if self.stage == "goal_pair" else
                ",".join(frozen_gate_failures)
                if self.stage == "frozen_context" and frozen_gate_failures
                else "none"),
            "curriculum_goal_pair_gate_report": (
                json.dumps(goal_pair_gate, sort_keys=True)
                if self.stage == "goal_pair" else "{}"),
            "curriculum_goal_pair_gate_evidence_shortages": (
                ",".join(goal_pair_gate.get("evidence_shortages", ()))
                if self.stage == "goal_pair" else ""),
            **{
                f"curriculum_frozen_context_evaluation_finger_{finger}_rate":
                    float(frozen_last.get(
                        f"finger_{finger}_rate", -1.0))
                for finger in range(1, 5)
            },
            **{
                f"curriculum_frozen_context_evaluation_finger_{finger}_frames":
                    float(frozen_last.get(
                        f"finger_{finger}_frames", 0.0))
                for finger in range(1, 5)
            },
            "curriculum_frozen_context_focus_finger": (
                0),
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
            "curriculum_goal_pair_recovery_focus_min_iterations":
                int(self.config.goal_pair_recovery_focus_min_iterations),
            "curriculum_goal_pair_recovery_finger_weights": [
                float(value)
                for value in self.config.goal_pair_recovery_finger_weights],
            **{
                f"curriculum_goal_pair_recovery_finger_{finger}_weight":
                    float(self.config.goal_pair_recovery_finger_weights[
                        finger - 1])
                for finger in range(1, 5)
            },
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
            "curriculum_goal_pair_mastery_verified_since_recovery":
                list(self.goal_pair_mastery_verified_since_recovery),
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
        self.frozen_context_recovery_weights = (
            self._normalize_frozen_context_weights(
                self.frozen_context_recovery_weights))
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
                    (self.config.static_chord_recovery_focus_probability
                     if self.static_chord_recovery_active
                     else self.config.chord_fine_focus_probability))
        else:
            focus_changed = env.goals.set_chord_focus_index(None)
        state = self.state()
        recovery_active = bool(
            state["curriculum_frozen_context_recovery_active"])
        recovery_teacher_scale = float(
            state["curriculum_frozen_context_recovery_teacher_scale"])
        if hasattr(env, "set_frozen_context_recovery"):
            env.set_frozen_context_recovery(
                recovery_active,
                teacher_scale=recovery_teacher_scale)
        elif hasattr(env, "set_frozen_context_recovery_active"):
            env.set_frozen_context_recovery_active(recovery_active)
        practice_focus_changed = False
        adaptive_early_distribution = (
            self.stage == "isolated_press"
            and self.stalled)
        adaptive_distribution = (
            (self.stage == "integrated_press"
             and self.integrated_recovery_active)
            or adaptive_early_distribution)
        if (adaptive_distribution
                and hasattr(env.goals, "set_practice_finger_weights")):
            env.goals.set_practice_finger_weights(
                self.early_recovery_weights
                if adaptive_early_distribution
                else self.integrated_recovery_weights)
        if hasattr(env.goals, "set_practice_focus_finger"):
            if not adaptive_distribution:
                recovery_focus = self._early_recovery_focus_finger()
                practice_focus = (
                    recovery_focus if recovery_focus > 0 else None)
                practice_focus_changed = env.goals.set_practice_focus_finger(
                    practice_focus,
                    focus_probability=(
                        self.config.early_recovery_focus_probability
                        if practice_focus is not None else 1.0))
        if practice_focus_changed:
            self.practice_focus_reset_count += 1
            self.practice_focus_reset_consecutive += 1
        else:
            self.practice_focus_reset_consecutive = 0
        if (self.practice_focus_reset_consecutive
                >= self.config.practice_reset_watchdog_iterations):
            raise RuntimeError(
                "practice focus changed on consecutive training iterations; "
                "refusing repeated full-environment resets")
        if hasattr(env, "set_integrated_press_control"):
            env.set_integrated_press_control(
                state["curriculum_integrated_control_phase"],
                recovery=self.integrated_recovery_active,
                focus_finger=self.integrated_recovery_focus_finger)
        if hasattr(env, "set_fine_reach_control"):
            env.set_fine_reach_control(
                self.stage_iteration,
                recovery=(self.stage == "fine_reach" and self.stalled))
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
        if hasattr(env.goals, "set_frozen_context_finger_weights"):
            env.goals.set_frozen_context_finger_weights(
                self.frozen_context_recovery_weights)
            if hasattr(env.goals, "set_frozen_context_mix_weights"):
                env.goals.set_frozen_context_mix_weights((
                    self.config.frozen_context_singleton_probability,
                    self.config.frozen_context_chord_probability,
                    self.config.frozen_context_uniform_probability))
            if hasattr(
                    env.goals,
                    "set_frozen_context_evaluation_fraction"):
                env.goals.set_frozen_context_evaluation_fraction(
                    self.config.frozen_context_evaluation_fraction)
        elif hasattr(env.goals, "set_frozen_context_focus"):
            # 구형 goal sequence에서도 단일 focus를 끄되 reset 신호로 쓰지 않는다.
            env.goals.set_frozen_context_focus(None)
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
        if hasattr(env.goals, "set_goal_pair_finger_weights"):
            if self.stage == "goal_pair" and self.goal_pair_recovery_active:
                available = set(self.goal_pair_incoming_fingers)
                recovery_weights = tuple(
                    float(value) if finger in available else 0.0
                    for finger, value in enumerate(
                        self.config.goal_pair_recovery_finger_weights,
                        start=1))
            else:
                recovery_weights = None
            env.goals.set_goal_pair_finger_weights(
                recovery_weights)
        if hasattr(env.goals, "set_goal_pair_recovery_active"):
            env.goals.set_goal_pair_recovery_active(
                self.stage == "goal_pair" and self.goal_pair_recovery_active)
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
            self.stalled = False
            if reset_obs is None:
                reset_obs = env.reset()
            self.frozen_context_final_applied = True
        elif not frozen_final:
            self.frozen_context_final_applied = False
        if (reset_obs is None
                and (focus_changed or practice_focus_changed)):
            reset_obs = env.reset()
        state = self.state()
        if reset_obs is not None:
            state["_reset_observation"] = reset_obs
        return state

    def _practice_limits(self):
        limits = {
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
        if (self.stage == "static_chord"
                and self.static_chord_recovery_count > 0
                and self.static_chord_recovery_reason == "retest"):
            minimum, maximum = limits
            return minimum, max(
                minimum,
                min(maximum,
                    self.config.static_chord_retest_max_iterations))
        return limits

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
        if self.stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press"):
            if self._early_evidence_starved_fingers():
                return False
            minimum = self.config.early_min_evidence_episodes_per_finger
            if minimum <= 0:
                return True
            required = self.required_song_fingers or (1, 2, 3, 4)
            return all(
                self.early_stage_evidence[finger]["target"] >= minimum
                for finger in required)
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
        for key in (
                cls.BRIDGE_FINGER_RATE_KEYS
                + cls.BRIDGE_FINGER_EVIDENCE_KEYS):
            if key not in values:
                continue
            value = float(values[key])
            valid = (
                0.0 <= value <= 1.0
                if key in cls.BRIDGE_FINGER_RATE_KEYS else value >= 0.0)
            if math.isfinite(value) and valid:
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
            metrics[f"finger_{finger}_frames"] = count
        metrics["finger_min"] = (
            min(finger_rates) if finger_rates else -1.0)
        metrics["episodes"] = episodes
        result = {
            key: float(metrics[key])
            for key in self.BRIDGE_METRIC_KEYS
        }
        result.update({
            key: float(metrics[key])
            for key in (
                self.BRIDGE_FINGER_RATE_KEYS
                + self.BRIDGE_FINGER_EVIDENCE_KEYS)
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

    def _bridge_gate_failures(self, metrics, soft=False):
        metrics = self._restore_bridge_metrics(metrics)
        if not metrics:
            return ("not_evaluated",)
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
        failures = []
        if self.stage == "frozen_context":
            required = self.required_song_fingers or tuple(range(1, 5))
            for finger in required:
                if (float(metrics.get(f"finger_{finger}_frames", 0.0))
                        < self.config.frozen_context_evaluation_min_finger_frames):
                    failures.append(f"finger_{finger}_evidence")
        for name in ("f1", "finger_min", "no_press", "sustain",
                     "event_success"):
            if metrics[name] < thresholds[name]:
                failures.append(name)
        for name in ("wrong", "dropout", "failure"):
            if metrics[name] > thresholds[name]:
                failures.append(name)
        if metrics["event_count"] < self.config.song_min_sustain_events:
            failures.append("event_count")
        return tuple(failures)

    def _bridge_gate_passes(self, metrics, soft=False):
        return not self._bridge_gate_failures(metrics, soft=soft)

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

    def _frozen_context_evaluation_start_iteration(self):
        if self.frozen_context_evaluation_started_iteration >= 0:
            return int(self.frozen_context_evaluation_started_iteration)
        if self.frozen_context_recovery_completed_iteration < 0:
            return int(self.stage_iteration) + 1
        context_final = (
            self.config.frozen_context_context_warmup_iterations
            + self.config.frozen_context_context_ramp_iterations)
        return max(
            int(context_final),
            int(self.frozen_context_recovery_completed_iteration)
            + int(self.config.frozen_context_final_evaluation_iterations))

    def _frozen_context_evaluation_ready_by_time(self):
        if self.stage != "frozen_context":
            return True
        return (
            not self.frozen_context_recovery_active
            and not self.frozen_context_recovery_failed
            and self.frozen_context_recovery_completed_iteration >= 0
            and self._frozen_context_evaluation_settle_iteration()
                >= self.config.frozen_context_final_evaluation_iterations
            and self.frozen_context_final_applied
            and self._frozen_context_difficulty()["final"]
            and self.stage_iteration
                >= self._frozen_context_evaluation_start_iteration())

    def _frozen_context_evaluation_ready(self):
        return (
            self.stage != "frozen_context"
            or (self.frozen_context_evaluation_started
                and self._frozen_context_evaluation_ready_by_time()))

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
            early = self.stage in (
                "coarse_reach", "fine_reach",
                "isolated_press", "integrated_press")
            if (early
                    and self.config.early_min_evidence_episodes_per_finger > 0):
                required = self.required_song_fingers or (1, 2, 3, 4)
                rates = self._early_stage_rates()
                if any(rates[finger] < 0.0 for finger in required):
                    return -1.0
                score = min(rates[finger] for finger in required)
            else:
                overall = float(stats.get("curriculum_success_rate", -1.0))
                if overall < 0.0:
                    return -1.0
                per_finger = []
                for finger in range(1, 5):
                    count = float(stats.get(
                        f"curriculum_finger_{finger}_count", 0.0))
                    if count > 0.0:
                        success = float(stats.get(
                            f"curriculum_finger_{finger}_success", 0.0))
                        per_finger.append(success / count)
                score = min([overall] + per_finger)
            p90 = None
            if self.stage in (
                    "coarse_reach", "fine_reach",
                    "chord_reach", "chord_fine_reach"):
                p90_value = stats.get("curriculum_p90_target_distance")
                if p90_value is None:
                    return -1.0
                p90 = float(p90_value)
                if not math.isfinite(p90):
                    return -1.0
            if self.stage in ("coarse_reach", "chord_reach"):
                if p90 > 0.040:
                    return 0.0
            if self.stage == "fine_reach":
                alignment_value = stats.get(
                    "curriculum_cell_alignment_rate")
                if alignment_value is None:
                    return -1.0
                alignment = float(alignment_value)
                if not math.isfinite(alignment):
                    return -1.0
                if p90 > 0.010 or alignment < 0.90:
                    return 0.0
            if self.stage == "chord_fine_reach":
                alignment_value = stats.get(
                    "curriculum_cell_alignment_rate")
                if alignment_value is None:
                    return -1.0
                alignment = float(alignment_value)
                if not math.isfinite(alignment):
                    return -1.0
                if (p90 > self.config.chord_fine_p90_distance
                        or alignment
                        < self.config.chord_fine_alignment_rate):
                    return 0.0
            if self.stage in ("isolated_press", "integrated_press"):
                quality_value = stats.get(
                    "curriculum_mean_position_quality")
                if quality_value is None:
                    return -1.0
                quality = float(quality_value)
                if not math.isfinite(quality):
                    return -1.0
                if quality < 0.50:
                    return 0.0
            if self.stage == "isolated_press":
                arch_value = stats.get("curriculum_mean_arch_quality")
                if arch_value is None:
                    return -1.0
                arch = float(arch_value)
                if not math.isfinite(arch):
                    return -1.0
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
        self._reset_early_stage_evidence()
        self.early_recovery_focus_finger = 0
        self.early_recovery_focus_iteration = 0
        self.early_recovery_count = 0
        self.early_recovery_focus_blocks = 0
        self.early_recovery_total_blocks = 0
        self.early_recovery_exhausted = False
        self.early_recovery_weights = (0.25, 0.25, 0.25, 0.25)
        self.early_recovery_best_rates = {
            finger: -1.0 for finger in range(1, 5)}
        self.early_recovery_last_switch_reason = ""
        self.early_recovery_retention_max_drop = 0.0
        if previous == "integrated_press":
            self.integrated_recovery_active = False
            self.integrated_recovery_focus_finger = 0
            self.integrated_recovery_iteration = 0
            self.integrated_recovery_total_iteration = 0
            self.integrated_recovery_block_count = 0
            self.integrated_recovery_weights = (0.25, 0.25, 0.25, 0.25)
            self.integrated_recovery_best_rates = {
                finger: -1.0 for finger in range(1, 5)}
            self.integrated_recovery_block_start_rates = {
                finger: -1.0 for finger in range(1, 5)}
            self.integrated_recovery_retention_max_drop = 0.0
            self.integrated_recovery_min_rate_improvement = 0.0
            self.integrated_recovery_no_improvement_blocks = 0
            self.integrated_recovery_exhausted = False
            self.integrated_recovery_last_update_reason = ""
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
            self.frozen_context_final_applied = False
            self.frozen_context_evaluation_started = False
            self._reset_frozen_context_recovery("stage_entry")
            self.frozen_context_evidence_reset_count = 0
            self.frozen_context_evidence_reset_reason = "stage_entry"
        elif previous == "frozen_context":
            self.frozen_context_evaluation_started = False
            self._reset_frozen_context_recovery("stage_exit")
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
        rollout_count = float(stats.get(
            f"curriculum_chord_shape_{signature}_target_active_count", 0.0))
        if rollout_count > 0.0:
            return float(stats.get(
                f"curriculum_chord_shape_{signature}_success", 0.0))
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
        rollout_target = self._finite_nonnegative(stats.get(
            f"curriculum_chord_shape_{signature}_target_active_count", 0.0))
        if rollout_target > 0.0:
            rate = self._finite_nonnegative(stats.get(
                f"curriculum_chord_shape_{signature}_success", 0.0))
            return min(rate, 1.0) * rollout_target, rollout_target
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
        selected = (
            None if signatures is None
            else {int(signature) for signature in signatures})
        accumulated = 0.0
        for finger_set in self.chord_available_sets:
            signature = self._finger_set_signature(finger_set)
            if selected is not None and signature not in selected:
                continue
            success, target = self._chord_set_episode_totals(
                stats, signature)
            if target <= 0.0:
                continue
            accumulated += target
            p90 = float(stats.get(
                f"curriculum_chord_shape_{signature}_distance_p90",
                stats.get(
                    "curriculum_p90_target_distance", float("nan"))))
            alignment = float(stats.get(
                f"curriculum_chord_shape_{signature}_alignment",
                stats.get(
                    "curriculum_cell_alignment_rate", float("nan"))))
            geometry_valid = (
                math.isfinite(p90) and math.isfinite(alignment))
            row = self.chord_phase_evidence.setdefault(
                str(signature), self._empty_chord_phase_row())
            row["target"] += target
            row["success"] += success
            if geometry_valid:
                row["p90_sum"] += p90 * target
                row["alignment_sum"] += alignment * target
                row["geometry_weight"] += target
        if accumulated > 0.0:
            self.chord_evidence_age = 0
            self.chord_evidence_stalled = False
        else:
            self.chord_evidence_age += 1
            self.chord_evidence_stalled = (
                self.chord_evidence_age
                >= self.config.chord_evidence_stall_iterations)

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
        rollout_target = float(stats.get(
            f"curriculum_chord_shape_{signature}_target_active_count", 0.0))
        if rollout_target > 0.0:
            row = self.chord_phase_evidence.get(str(signature), {})
            return float(row.get("target", 0.0)) >= (
                self.config.chord_fine_min_phase_episodes)
        if "episodes" not in stats:
            return False
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
        has_rollout_evidence = any(
            f"curriculum_chord_shape_{signature}_target_active_count" in stats
            for signature in range(1, 16))
        if "episodes" not in stats and not has_rollout_evidence:
            p90 = float(stats.get(
                "curriculum_p90_target_distance", float("inf")))
            alignment = float(stats.get(
                "curriculum_cell_alignment_rate", -1.0))
            geometry = (
                math.isfinite(p90)
                and p90 <= self.config.chord_fine_p90_distance
                and alignment >= self.config.chord_fine_alignment_rate)
            if self.chord_focus_index >= 0:
                signature = self._finger_set_signature(
                    self.chord_available_sets[self.chord_focus_index])
                exact = self._chord_set_rate(stats, signature)
                return exact if geometry and exact >= 0.0 else (
                    0.0 if exact >= 0.0 else -1.0)
            score = self._promotion_sample(stats)
            exact_rates = [
                self._chord_set_rate(
                    stats, self._finger_set_signature(finger_set))
                for finger_set in self.chord_available_sets]
            if (score < 0.0 or not exact_rates
                    or any(value < 0.0 for value in exact_rates)):
                return -1.0
            return min([score] + exact_rates)
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
        if self.static_chord_recovery_active:
            indices = self._recovery_focus_indices()
            position = (
                indices.index(self.chord_focus_index)
                if self.chord_focus_index in indices else len(indices) - 1)
            self.chord_focus_index = (
                indices[position + 1]
                if position + 1 < len(indices) else -1)
        else:
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

    def _goal_pair_sequence_checks(self, stats):
        difficulty = self._goal_pair_difficulty()
        if difficulty["sequence_probability"] <= 0.0:
            return {}
        count = self._goal_pair_stat(
            stats, "curriculum_goal_pair_sequence_active_count")
        checks = {"sequence_evidence": self._gate_check(
            count, self.config.goal_pair_sequence_min_frames, evidence=True)}
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
            checks[f"sequence_{name}"] = self._gate_check(
                value, threshold, ">=" if lower_bound else "<=")
        return checks

    def _goal_pair_sequence_sample(self, stats):
        for check in self._goal_pair_sequence_checks(stats).values():
            if check["passed"] is None:
                return None
            if not check["passed"]:
                return None if check["evidence"] else False
        return True

    @staticmethod
    def _gate_check(value, threshold, comparison=">=", evidence=False,
                    blocks_promotion=True):
        passed = None if value is None else (
            value >= threshold if comparison == ">=" else value <= threshold)
        return dict(value=value, threshold=threshold, comparison=comparison,
                    passed=passed, evidence=evidence,
                    blocks_promotion=blocks_promotion)

    def _goal_pair_sequence_finger_checks(self, stats):
        """Check sequence quality per finger when the cohort exposes it.

        Older rollouts do not contain per-finger sequence rows, so the
        aggregate gate remains the source of truth until those rows are
        available.  Once a finger has enough samples, a strong aggregate
        score can no longer hide a collapsed finger.
        """
        fingers = self._goal_pair_fingers(stats)
        if not fingers:
            return {"sequence_required_fingers": self._gate_check(0, 1)}
        has_per_finger_metrics = any(
            key.startswith("curriculum_goal_pair_sequence_finger_")
            for key in stats)
        if not has_per_finger_metrics:
            # Checkpoints produced before per-finger sequence diagnostics
            # remain valid through the aggregate sequence gate.
            return {}
        level = self._goal_pair_level()
        if self.goal_pair_phase == "mixed":
            if level < self.config.goal_pair_preview_levels:
                return {}
            threshold = max(
                self.config.goal_pair_mixed_full_song_press_rates[level],
                0.5 * self.config.goal_pair_sequence_press_rate)
            wrong_threshold = (
                self.config.goal_pair_mixed_wrong_press_rates[level])
        else:
            threshold = self.config.goal_pair_sequence_press_rate
            wrong_threshold = self.config.goal_pair_sequence_wrong_press_rate
        minimum = self.config.goal_pair_full_song_focus_min_evidence
        checks = {}
        for finger in fingers:
            row = self._goal_pair_context_row(stats, "sequence", finger)
            prefix = f"sequence_finger_{finger}"
            checks[f"{prefix}_evidence"] = self._gate_check(
                row["count"] if row else None, minimum, evidence=True)
            checks[f"{prefix}_success"] = self._gate_check(
                row["success"] if row else None, threshold)
            checks[f"{prefix}_wrong_press"] = self._gate_check(
                row["wrong_press"] if row else None, wrong_threshold, "<=")
        return checks

    def _goal_pair_sequence_finger_sample(self, stats):
        # Preserve ordered short-circuit semantics, including missing evidence.
        for check in self._goal_pair_sequence_finger_checks(stats).values():
            if check["passed"] is None:
                return None
            if not check["passed"]:
                return None if check["evidence"] else False
        return True

    def goal_pair_gate_diagnostics(self, stats):
        """Explain the current phase using the same evaluators as advancement.

        ``stats`` must be the phase-aggregated decision input for an exact
        runtime snapshot. Calling this on a historical rollout alone is only
        a reconstruction; mastery streaks and accumulated evidence also matter.
        """
        checks = {}
        level = self._goal_pair_level()
        fingers = self._goal_pair_fingers(stats)
        minimum = (self.config.goal_pair_retention_min_iterations
                   if self.goal_pair_phase == "retention"
                   else self.config.goal_pair_mixed_min_iterations)
        age = (self.goal_pair_phase_iteration
               if self.goal_pair_phase == "retention"
               else self.goal_pair_mixed_level_iteration)
        checks["phase_age"] = self._gate_check(age, minimum)
        checks["required_fingers"] = self._gate_check(len(fingers), 1)
        for finger in fingers:
            index = finger - 1
            mastered = self.goal_pair_mastered_fingers[index]
            result = (self._goal_pair_mastery_retained(stats, finger)
                      if mastered else
                      self._goal_pair_focus_unresolved(stats, finger))
            checks[f"finger_{finger}_post_update_quality"] = self._gate_check(
                None if result is None else int(result[0]), 1,
                blocks_promotion=False)
            checks[f"finger_{finger}_mastered"] = self._gate_check(
                int(mastered), 1)
            checks[
                f"finger_{finger}_verified_since_recovery"
            ] = self._gate_check(
                int(self.goal_pair_mastery_verified_since_recovery[index]),
                1, evidence=True)
            checks[f"finger_{finger}_streak"] = self._gate_check(
                self.goal_pair_mastery_streaks[index],
                self.config.promotion_windows, blocks_promotion=False)
        if self.goal_pair_phase != "retention":
            preservation = self._goal_pair_preservation_row(stats)
            checks["preservation_evidence"] = self._gate_check(
                preservation["count"] if preservation else None,
                self.config.goal_pair_phase_min_evidence, evidence=True)
            checks["preservation"] = self._gate_check(
                preservation["value"] if preservation else None,
                self.config.goal_pair_mixed_preservation_rates[level])
            sequence = self._goal_pair_sequence_sample(stats)
            checks["sequence_aggregate"] = self._gate_check(
                None if sequence is None else int(sequence), 1)
            checks.update(self._goal_pair_sequence_checks(stats))
            checks.update(self._goal_pair_sequence_finger_checks(stats))
        if self.goal_pair_recovery_active:
            rates = self._goal_pair_full_song_rates(stats, fingers)
            checks = {
                "recovery_age": self._gate_check(
                    self.goal_pair_recovery_iteration,
                    self.config.goal_pair_recovery_min_iterations),
                "recovery_good_windows": self._gate_check(
                    self.goal_pair_recovery_good_windows,
                    self.config.goal_pair_recovery_windows),
                "recovery_song_ready": self._gate_check(
                    int(self._goal_pair_recovery_song_ready(stats)), 1),
                "recovery_song_min_success": self._gate_check(
                    min(rates.values()) if rates else None,
                    self.config.goal_pair_recovery_min_full_song_press_rate),
            }
        elif self.goal_pair_phase == "full":
            # Full-phase advancement uses bridge evaluation, not the earlier
            # per-finger mastery latch or mixed-level iteration counter.
            checks = {}
            minimum, _ = self._practice_limits()
            checks["stage_age"] = self._gate_check(
                self.stage_iteration, minimum)
            checks["difficulty_ready"] = self._gate_check(
                int(self._bridge_difficulty_ready()), 1)
            checks["promotion_diagnostics"] = self._gate_check(
                int(self._goal_pair_promotion_diagnostics_pass(stats)), 1)
            checks["thumb_geometry"] = self._gate_check(
                int(self._thumb_geometry_gate_passes(stats)), 1)
            checks["regression_clear"] = self._gate_check(
                int(not self.regression_hold), 1)
            checks["bridge_windows"] = self._gate_check(
                int(self._bridge_windows_pass()), 1)
            checks.update(self._goal_pair_sequence_checks(stats))
            checks.update(self._goal_pair_sequence_finger_checks(stats))
        shortages = [name for name, check in checks.items()
                     if check["blocks_promotion"] and (
                         check["passed"] is None
                         or (check["evidence"] and not check["passed"]))]
        failures = [name for name, check in checks.items()
                    if check["blocks_promotion"]
                    and check["passed"] is False and name not in shortages]
        scope = ("recovery_exit_conditions" if self.goal_pair_recovery_active
                 else "normal_stage_promotion_conditions"
                 if self.goal_pair_phase == "full"
                 else "phase_promotion_conditions")
        return dict(phase=self.goal_pair_phase, level=level, scope=scope,
                    recovery=bool(self.goal_pair_recovery_active),
                    iteration=self.total_iteration, checks=checks,
                    failures=failures, evidence_shortages=shortages)

    def _goal_pair_observed_finger_weakest(self, stats, fingers,
                                           rotate_from=0):
        """Return the weakest finger from any available sequence evidence."""
        rates = {}
        minimum = self.config.goal_pair_full_song_focus_min_evidence
        for finger in fingers:
            for cohort in ("sequence", "full_song"):
                row = self._goal_pair_context_row(stats, cohort, finger)
                if row is not None and row["count"] >= minimum:
                    rates[int(finger)] = float(row["success"])
                    break
            if finger not in rates:
                prefix = (
                    f"curriculum_goal_pair_sequence_finger_{finger}")
                value = self._goal_pair_stat(
                    stats, f"{prefix}_press_success")
                count = self._goal_pair_stat(
                    stats, f"{prefix}_target_active_count")
                if value is not None and (count is None or count >= minimum):
                    rates[int(finger)] = float(value)
        if not rates:
            return 0
        weakest = min(rates.values())
        tied = sorted(
            finger for finger, value in rates.items()
            if value <= weakest + 0.01)
        rotate_from = int(rotate_from)
        if rotate_from in tied and len(tied) > 1:
            return tied[(tied.index(rotate_from) + 1) % len(tied)]
        return tied[0]

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
                    self.goal_pair_mastery_verified_since_recovery[
                        index] = True
                    self.goal_pair_mastery_fail_streaks[index] = 0
                else:
                    self.goal_pair_mastery_verified_since_recovery[
                        index] = False
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
                    self.goal_pair_mastery_verified_since_recovery[
                        index] = True
                    self.goal_pair_mastery_fail_streaks[index] = 0
            else:
                self.goal_pair_mastery_verified_since_recovery[index] = False
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
            return self._goal_pair_observed_finger_weakest(
                stats, fingers, rotate_from=rotate_from)
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
            if (not self.goal_pair_mastered_fingers[finger - 1]
                or not self.goal_pair_mastery_verified_since_recovery[
                    finger - 1])]
        if self.goal_pair_recovery_active:
            full_song_rates = self._goal_pair_full_song_rates(
                stats, fingers)
            if full_song_rates:
                minimum_song_rate = (
                    self.config.goal_pair_recovery_min_full_song_press_rate)
                song_unresolved = {
                    finger for finger in fingers
                    if full_song_rates[finger] < minimum_song_rate}
                unresolved = [
                    finger for finger in fingers
                    if finger in unresolved or finger in song_unresolved]
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
        focus_min_iterations = max(
            self.config.goal_pair_focus_min_iterations,
            (self.config.goal_pair_recovery_focus_min_iterations
             if self.goal_pair_recovery_active else 0))
        rotate_from = (
            current
            if self.goal_pair_focus_iteration
                >= focus_min_iterations
            else 0)
        observed_weakest = (
            self._goal_pair_observed_finger_weakest(
                stats, unresolved, rotate_from=rotate_from)
            if self.goal_pair_recovery_active else 0)
        weakest = (
            (self._goal_pair_full_song_weakest(
                stats, unresolved, rotate_from=rotate_from)
             if self.goal_pair_recovery_active else 0)
            or (self._goal_pair_bridge_weakest(unresolved)
                if self.goal_pair_recovery_active else 0)
            or observed_weakest
            or rehearsal_weakest)
        focus_locked = (
            current in unresolved
            and self.goal_pair_focus_iteration
                < focus_min_iterations)
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
            for index, mastered in enumerate(
                    self.goal_pair_mastered_fingers):
                if not mastered:
                    self.goal_pair_mastery_streaks[index] = 0
                    self.goal_pair_mastery_fail_streaks[index] = 0
        else:
            self.goal_pair_phase_iteration = 0
        self.goal_pair_focus_scores = [None] * 4
        self.goal_pair_mastery_verified_since_recovery = [False] * 4
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
            self.frozen_context_evaluation_started = False
            self._reset_frozen_context_recovery("goal_pair_rollback")
            self.frozen_context_evidence_reset_count = 0
            self.frozen_context_evidence_reset_reason = "goal_pair_rollback"
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
        self.goal_pair_last_gate_diagnostics = (
            self.goal_pair_gate_diagnostics(stats))
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
        sequence_fingers = self._goal_pair_sequence_finger_sample(stats)
        if sequence_fingers is None:
            return None
        return (
            preservation["value"]
                >= self.config.goal_pair_mixed_preservation_rates[level]
            and sequence
            and sequence_fingers)

    def _reset_goal_pair_phase_window(self):
        self.goal_pair_mastered_fingers = [False] * 4
        self.goal_pair_mastery_verified_since_recovery = [False] * 4
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
            self.goal_pair_last_gate_diagnostics = (
                self.goal_pair_gate_diagnostics(stats))
            return False
        if self.goal_pair_phase == "full":
            self._update_goal_pair_focus(stats, {})
            return False
        evaluations = self._update_goal_pair_mastery(stats)
        self._update_goal_pair_focus(stats, evaluations)
        self.goal_pair_last_gate_diagnostics = (
            self.goal_pair_gate_diagnostics(stats))
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
            and self.goal_pair_mastery_verified_since_recovery[finger - 1]
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
        return (
            self._goal_pair_sequence_sample(stats) is True
            and self._goal_pair_sequence_finger_sample(stats) is True)

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
            allow_promotion=True, bridge_stats=None):
        if (self.stage == "frozen_context"
                and self.frozen_context_recovery_failed):
            self.stalled = True
            return self.state()
        evidence_allowed = (
            (self.stage != "frozen_context"
             or self.frozen_context_evaluation_started)
            and not transition_difficulty_changed)
        if evidence_allowed:
            self._accumulate_bridge_stats(
                stats if bridge_stats is None else bridge_stats)
        self.stalled = False
        if self.stage == "goal_pair":
            recovery_changed = self._sync_goal_pair_recovery(stats)
            if self.goal_pair_recovery_active:
                return self.state()
            if recovery_changed:
                return self.state()
            if self.goal_pair_phase == "full":
                self.goal_pair_last_gate_diagnostics = (
                    self.goal_pair_gate_diagnostics(stats))
        if not allow_promotion:
            return self.state()

        promotion_stats = (
            bridge_stats
            if self.stage == "frozen_context" and bridge_stats is not None
            else stats)

        if self.stage in self.SOFT_TIMEOUT_STAGES:
            if (self.stage == "frozen_context"
                    and not self.frozen_context_evaluation_started):
                self.stalled = False
                return self.state()
            stage_age = (
                max(
                    self.stage_iteration
                    - self.frozen_context_evaluation_started_iteration,
                    0)
                if self.stage == "frozen_context"
                else self.stage_iteration)
            minimum, maximum = self._practice_limits()
            difficulty_ready = self._bridge_difficulty_ready()
            goal_pair_diagnostics_ready = (
                self.stage != "goal_pair"
                or self._goal_pair_promotion_diagnostics_pass(stats))
            normal_passed = (
                stage_age >= minimum
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(promotion_stats)
                and not self.regression_hold
                and self._bridge_windows_pass())
            if normal_passed:
                self._promote()
                return self.state()
            soft_iteration = int(math.ceil(
                maximum
                * self.config.bridge_soft_timeout_fraction))
            soft_passed = (
                stage_age >= soft_iteration
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(promotion_stats)
                and not self.regression_hold
                and self._bridge_windows_pass(soft=True))
            if soft_passed:
                previous = self.stage
                self._force_promote(f"{previous}:soft_timeout")
                return self.state()
            hard_ready = (
                stage_age >= maximum
                and difficulty_ready
                and goal_pair_diagnostics_ready
                and self._thumb_geometry_gate_passes(promotion_stats)
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
                or stage_age >= maximum)
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
        if (self.stage == "integrated_press"
                and self.integrated_recovery_active
                and not self.integrated_recovery_exhausted):
            self.integrated_recovery_iteration += 1
            self.integrated_recovery_total_iteration += 1
        if (self.stage == "frozen_context"
                and self.frozen_context_recovery_active):
            self.frozen_context_recovery_iteration += 1
        self._accumulate_early_stage_evidence(stats)
        self._advance_integrated_recovery()
        self._advance_early_recovery_focus()
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
        frozen_eval_stats = None
        if self.stage == "frozen_context":
            frozen_train_stats = stats.get("_frozen_train", {})
            frozen_eval_stats = stats.get("_frozen_eval", {})
            if self.frozen_context_recovery_active:
                self._accumulate_frozen_context_recovery_stats(
                    frozen_train_stats)
                self._sync_frozen_context_recovery()
            self._start_frozen_context_evaluation()
            if self.frozen_context_recovery_failed:
                self.stalled = True
                return self.state()
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
                    or goal_pair_phase_changed,
                    allow_promotion=False,
                    bridge_stats=frozen_eval_stats)
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
                if self.static_chord_recovery_active:
                    self._finish_static_chord_recovery()
                elif self.forced_stage is None:
                    self._promote()
                else:
                    self.stalled = False
            elif self.chord_focus_iteration >= maximum:
                if self.static_chord_recovery_active:
                    self._finish_static_chord_recovery()
                elif self.forced_stage is not None:
                    self.stalled = True
                elif (self.chord_focus_cycle + 1
                      >= self.config.chord_fine_max_cycles):
                    self._record_unresolved_chord_catalog()
                    if (self._catastrophic_free(stats)
                            and self._chord_fine_soft_floor_passes(stats)):
                        self._force_promote(
                            "chord_fine_reach:soft_floor")
                    else:
                        self._force_promote(
                            "chord_fine_reach:bounded_unresolved")
                else:
                    self._retry_chord_focus_cycle()
            return self.state()
        if self.stage in self.BRIDGE_STAGES:
            return self._after_bridge_iteration(
                goal_pair_stats,
                transition_difficulty_changed
                or goal_pair_phase_changed,
                bridge_stats=frozen_eval_stats)
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
                if self.stage == "static_chord":
                    promising = bool(self.recent) and all(
                        value >= self.config.promotion_success_rate
                        for value in self.recent)
                    if not promising:
                        self._start_static_chord_recovery(stats)
                elif self.stage == "integrated_press":
                    if not self.integrated_recovery_active:
                        self._start_integrated_recovery()
                    elif self.integrated_recovery_exhausted:
                        self.stalled = True
                else:
                    if (self.stage in self.EARLY_SINGLE_FINGER_STAGES
                            and not self.stalled):
                        self._start_early_recovery()
                    else:
                        self.stalled = True
        state = self.state()
        return state
