"""Per-song practice curriculum for trajectory optimization, not song generalization."""
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import math
from typing import Optional


@dataclass(frozen=True)
class PerSongCurriculumConfig:
    """Iteration schedule for repeatedly learning one fixed song.

    All goals, rewards and safety rules stay enabled.  Only the episode start
    distribution changes: broad in-song coverage first, then integration, then
    complete takes from frame zero.
    """
    coverage_iterations: int = 1000
    integration_iterations: int = 1000

    def __post_init__(self):
        if self.coverage_iterations < 0 or self.integration_iterations < 0:
            raise ValueError("curriculum iteration counts must be non-negative")


class PerSongCurriculum:
    STAGES = ("coverage", "integration", "full_song")

    def __init__(self, config=PerSongCurriculumConfig(), forced_stage=None):
        self.config = config
        if forced_stage is not None and forced_stage not in self.STAGES:
            raise ValueError(f"unknown forced curriculum stage: {forced_stage}")
        self.forced_stage = forced_stage

    def state(self, iteration):
        iteration = max(1, int(iteration))
        if self.forced_stage == "coverage":
            stage, probability, progress = "coverage", 1.0, 0.0
        elif self.forced_stage == "integration":
            stage, probability, progress = "integration", 0.5, 0.5
        elif self.forced_stage == "full_song":
            stage, probability, progress = "full_song", 0.0, 1.0
        elif iteration <= self.config.coverage_iterations:
            stage, probability, progress = "coverage", 1.0, 0.0
        elif (self.config.integration_iterations > 0
              and iteration <= self.config.coverage_iterations
              + self.config.integration_iterations):
            offset = iteration - self.config.coverage_iterations
            progress = offset / float(self.config.integration_iterations)
            stage = "integration"
            probability = 1.0 - progress
        else:
            stage, probability, progress = "full_song", 0.0, 1.0
        return {
            "curriculum_stage": stage,
            "curriculum_random_start_probability": float(probability),
            "curriculum_stage_progress": float(progress),
        }

    def apply(self, env, iteration):
        state = self.state(iteration)
        env.goals.set_random_start_probability(
            state["curriculum_random_start_probability"])
        return state


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
    chord_fine_focus_probability: float = 0.95
    chord_fine_success_rate: float = 0.80
    chord_fine_p90_distance: float = 0.010
    chord_fine_alignment_rate: float = 0.80
    chord_fine_min_phase_episodes: int = 256
    static_chord_min_iterations: int = 400
    static_chord_max_iterations: int = 3000
    frozen_context_min_iterations: int = 1000
    frozen_context_max_iterations: int = 2500
    goal_pair_min_iterations: int = 400
    goal_pair_max_iterations: int = 2000
    transition_min_iterations: Optional[int] = None
    transition_max_iterations: Optional[int] = None
    # Kept as checkpoint/config aliases for runs created before transition_window.
    pair_min_iterations: int = 500
    pair_max_iterations: int = 3000
    frozen_context_duration_frames: int = 150
    goal_pair_duration_frames: int = 120
    goal_pair_retention_rehearsal_probability: float = 1.0
    goal_pair_mixed_rehearsal_probability: float = 0.65
    goal_pair_rehearsal_probability: float = 1.0 / 3.0
    goal_pair_mixed_transition_fractions: tuple[float, ...] = (
        0.10, 0.20, 0.35)
    goal_pair_mixed_preservation_rates: tuple[float, ...] = (
        0.50, 0.70, 0.90)
    goal_pair_mixed_press_rates: tuple[float, ...] = (
        0.10, 0.30, 0.50)
    goal_pair_mixed_distances: tuple[float, ...] = (
        0.050, 0.035, 0.025)
    goal_pair_mixed_sequence_probabilities: tuple[float, ...] = (
        0.0, 0.10, 0.25)
    goal_pair_full_sequence_probability: float = 0.35
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
    goal_pair_retention_focus_probability: float = 0.70
    goal_pair_mixed_focus_probability: float = 0.40
    goal_pair_retention_min_iterations: int = 100
    goal_pair_mixed_min_iterations: int = 200
    goal_pair_full_min_iterations: int = 100
    goal_pair_phase_min_evidence: int = 1024
    goal_pair_rehearsal_press_rate: float = 0.80
    goal_pair_rehearsal_distance: float = 0.010
    goal_pair_mixed_transition_press_rate: float = 0.50
    goal_pair_mixed_transition_distance: float = 0.025
    goal_pair_mixed_min_next_progress: float = -0.010
    goal_pair_pretransition_preservation_rate: float = 0.90
    goal_pair_promotion_transition_press_rate: float = 0.80
    frozen_context_initial_real_probability: float = 0.0
    frozen_context_context_warmup_iterations: int = 200
    frozen_context_context_ramp_iterations: int = 800
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
    regression_hold_windows: int = 2
    song_f1_rate: float = 0.85
    song_per_finger_press_rate: float = 0.80
    song_no_press_accuracy: float = 0.99
    song_wrong_press_rate: float = 0.01
    song_sustain_hold_rate: float = 0.90
    song_max_dropout_frames: float = 3.0
    song_press_dropout_rate: float = 0.05
    song_min_sustain_events: float = 1.0
    thumb_coarse_distance: float = 0.050
    thumb_fine_distance: float = 0.025
    thumb_integrated_distance: float = 0.015
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
                 (self.effective_transition_min_iterations,
                  self.effective_transition_max_iterations))
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
        if (self.frozen_context_duration_frames < 1
                or self.goal_pair_duration_frames < 1):
            raise ValueError(
                "frozen-context and goal-pair durations must be positive")
        goal_pair_probabilities = (
            self.goal_pair_retention_rehearsal_probability,
            self.goal_pair_mixed_rehearsal_probability,
            self.goal_pair_rehearsal_probability,
        )
        if (any(not 0.0 <= value <= 1.0
                for value in goal_pair_probabilities)
                or not (
                    self.goal_pair_retention_rehearsal_probability
                    >= self.goal_pair_mixed_rehearsal_probability
                    >= self.goal_pair_rehearsal_probability)):
            raise ValueError(
                "goal-pair rehearsal probabilities must be descending in [0, 1]")
        mixed_schedules = (
            self.goal_pair_mixed_transition_fractions,
            self.goal_pair_mixed_preservation_rates,
            self.goal_pair_mixed_press_rates,
            self.goal_pair_mixed_distances,
            self.goal_pair_mixed_sequence_probabilities,
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
                or not math.isclose(
                    self.goal_pair_mixed_transition_fractions[-1],
                    1.0 - self.goal_pair_mixed_rehearsal_probability,
                    rel_tol=0.0, abs_tol=1e-9)):
            raise ValueError(
                "goal-pair mixed transition fractions must increase to "
                "one minus the final rehearsal probability")
        if (any(
                not math.isfinite(value) or not 0.0 <= value <= 1.0
                for values in (
                    self.goal_pair_mixed_preservation_rates,
                    self.goal_pair_mixed_press_rates)
                for value in values)
                or any(
                    right < left
                    for values in (
                        self.goal_pair_mixed_preservation_rates,
                        self.goal_pair_mixed_press_rates)
                    for left, right in zip(values, values[1:]))):
            raise ValueError(
                "goal-pair mixed preservation and press rates must increase "
                "within [0, 1]")
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
        )
        if any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
                for value in phase_iterations):
            raise ValueError(
                "goal-pair phase minimum iterations must be positive integers")
        if (isinstance(self.goal_pair_phase_min_evidence, bool)
                or not isinstance(self.goal_pair_phase_min_evidence, int)
                or self.goal_pair_phase_min_evidence < 1):
            raise ValueError(
                "goal-pair phase evidence must be a positive integer")
        if (not math.isfinite(self.goal_pair_rehearsal_distance)
                or self.goal_pair_rehearsal_distance <= 0.0
                or not math.isfinite(
                    self.goal_pair_mixed_transition_distance)
                or self.goal_pair_mixed_transition_distance <= 0.0):
            raise ValueError(
                "goal-pair distance thresholds must be finite and positive")
        goal_pair_rates = (
            self.goal_pair_rehearsal_press_rate,
            self.goal_pair_mixed_transition_press_rate,
            self.goal_pair_pretransition_preservation_rate,
            self.goal_pair_promotion_transition_press_rate,
        )
        if any(not 0.0 <= value <= 1.0 for value in goal_pair_rates):
            raise ValueError("goal-pair rates must be in [0, 1]")
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
        if self.song_max_dropout_frames < 0.0:
            raise ValueError("song_max_dropout_frames must be non-negative")
        if self.song_min_sustain_events < 0.0:
            raise ValueError("song_min_sustain_events must be non-negative")
        if not (0.0 < self.thumb_integrated_distance
                <= self.thumb_fine_distance <= self.thumb_coarse_distance):
            raise ValueError(
                "thumb distances must satisfy 0 < integrated <= fine <= coarse")
        if not 0.0 <= self.thumb_support_rate <= 1.0:
            raise ValueError("thumb support rate must be in [0,1]")
        if not 0.0 <= self.thumb_wrong_contact_rate <= 1.0:
            raise ValueError("thumb wrong-contact rate must be in [0,1]")

    @property
    def effective_transition_min_iterations(self):
        return (self.pair_min_iterations
                if self.transition_min_iterations is None
                else self.transition_min_iterations)

    @property
    def effective_transition_max_iterations(self):
        return (self.pair_max_iterations
                if self.transition_max_iterations is None
                else self.transition_max_iterations)


class FingertipApproachCurriculum:
    """A0--A4 curriculum whose early stages cannot earn easy baseline reward."""
    SCHEMA_VERSION = 11
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
        self.transition_difficulty_level = 0
        self.frozen_context_final_applied = False
        self.required_song_fingers = ()
        self.goal_pair_phase = "retention"
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_focus_finger = 0
        self.goal_pair_incoming_fingers = ()
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
                f"transition_{finger}_next_count": 0.0,
                f"transition_{finger}_target_count": 0.0,
                f"transition_{finger}_success_sum": 0.0,
                f"transition_{finger}_distance_sum": 0.0,
                f"transition_{finger}_progress_sum": 0.0,
            })
        return evidence

    def _reset_goal_pair_phase_evidence(self):
        self.goal_pair_phase_evidence = (
            self._empty_goal_pair_phase_evidence())

    def load_context(self, context):
        source_schema = int(
            context.get("curriculum_schema_version", 1))
        source_stage = context.get("curriculum_stage")
        stage = self.migrate_stage(source_stage, source_schema)
        legacy_stage = (
            stage != source_stage
            or (source_schema == 4
                and source_stage
                in self.PRE_INTERPOLATION_SCHEMA_LATE_STAGES))
        legacy_goal_pair_phase = (
            stage == "goal_pair" and source_schema < self.SCHEMA_VERSION)
        self.frozen_context_final_applied = False
        self.goal_pair_phase = "retention"
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_focus_finger = 0
        self.goal_pair_incoming_fingers = ()
        self._reset_goal_pair_phase_evidence()
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
            self.stage_iteration = (
                0 if (legacy_stage or legacy_goal_pair_phase
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
                if not legacy_stage and not legacy_goal_pair_phase:
                    self.recent.extend(
                        float(value) for value in context.get(
                            "curriculum_recent", ()))
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
            if (source_schema >= self.SCHEMA_VERSION
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
                saved_evidence = context.get(
                    "curriculum_goal_pair_phase_evidence", {})
                restored_evidence = self._empty_goal_pair_phase_evidence()
                for key in restored_evidence:
                    value = float(saved_evidence.get(key, 0.0))
                    if math.isfinite(value) and value >= 0.0:
                        restored_evidence[key] = value
                self.goal_pair_phase_evidence = restored_evidence

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
        if self.chord_focus_index >= self.chord_focus_count:
            self.chord_focus_index = -1

    def _transition_level_for_iteration(self, iteration):
        levels = len(self.config.transition_window_seconds)
        minimum = max(self.config.effective_transition_min_iterations, 1)
        progress = min(max(int(iteration), 0) / float(minimum), 1.0)
        return min(int(progress * levels), levels - 1)

    def _transition_difficulty(self):
        levels = len(self.config.transition_window_seconds)
        level = min(max(self.transition_difficulty_level, 0), levels - 1)
        minimum = max(self.config.effective_transition_min_iterations, 1)
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
        elif phase == "mixed":
            level = min(
                max(int(self.goal_pair_mixed_level), 0),
                len(self.config.goal_pair_mixed_transition_fractions) - 1)
            rehearsal_probability = (
                1.0
                - self.config.goal_pair_mixed_transition_fractions[level])
            focus_probability = (
                self.config.goal_pair_mixed_focus_probability)
            sequence_probability = (
                self.config.goal_pair_mixed_sequence_probabilities[level])
        else:
            rehearsal_probability = (
                self.config.goal_pair_rehearsal_probability)
            focus_probability = 0.0
            sequence_probability = (
                self.config.goal_pair_full_sequence_probability)
        phase_index = self.GOAL_PAIR_PHASES.index(phase)
        preview_only = (
            phase == "mixed"
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
            "sequence_full_song_fraction": float(
                self.config.goal_pair_sequence_full_song_fraction),
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
            "curriculum_chord_focus_probability":
                float(self.config.chord_fine_focus_probability),
            "curriculum_chord_available_sets": [
                list(finger_set)
                for finger_set in self.chord_available_sets],
            "curriculum_chord_unresolved_signatures": list(
                self.chord_unresolved_signatures),
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
            "curriculum_goal_pair_focus_probability": (
                float(goal_pair["focus_probability"])
                 if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_sequence_probability": (
                float(goal_pair["sequence_probability"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_sequence_duration_frames": (
                int(goal_pair["sequence_duration_frames"])
                if self.stage == "goal_pair" else 0),
            "curriculum_goal_pair_sequence_full_song_fraction": (
                float(goal_pair["sequence_full_song_fraction"])
                if self.stage == "goal_pair" else 0.0),
            "curriculum_goal_pair_final": (
                bool(goal_pair["final"])
                if self.stage == "goal_pair" else False),
            "curriculum_goal_pair_phase_evidence":
                dict(self.goal_pair_phase_evidence),
            "curriculum_recent": list(self.recent),
            "curriculum_bridge_windows": [
                dict(metrics) for metrics in self.bridge_windows],
            "curriculum_bridge_accumulator":
                dict(self.bridge_accumulator),
            "curriculum_bridge_last_metrics":
                dict(self.bridge_last_metrics),
            "curriculum_bridge_normal_recent": [
                self._bridge_gate_passes(metrics)
                for metrics in self.bridge_windows],
            "curriculum_bridge_soft_recent": [
                self._bridge_gate_passes(metrics, soft=True)
                for metrics in self.bridge_windows],
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

    def apply(self, env, iteration=None):
        self.required_song_fingers = tuple(
            index + 1
            for index in getattr(
                env.goals, "practice_available_fingers", range(4)))
        self.goal_pair_incoming_fingers = tuple(
            int(finger) for finger in getattr(
                env.goals,
                "practice_goal_pair_available_incoming_fingers", ()))
        focus_changed = False
        if self.stage == "chord_fine_reach":
            self._bind_chord_catalog(env.goals)
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
                    self.config.goal_pair_sequence_full_song_fraction)
        if hasattr(env.goals, "set_goal_pair_preview_only"):
            env.goals.set_goal_pair_preview_only(
                state["curriculum_goal_pair_preview_only"])
        if hasattr(env, "set_goal_pair_action_assist"):
            env.set_goal_pair_action_assist(
                state["curriculum_goal_pair_preview_only"])
        goal_pair_focus_changed = False
        if hasattr(env.goals, "set_goal_pair_transition_focus"):
            focus_finger = (
                state["curriculum_goal_pair_focus_finger"]
                if self.stage == "goal_pair"
                and state["curriculum_goal_pair_focus_finger"] > 0
                else None)
            goal_pair_focus_changed = (
                env.goals.set_goal_pair_transition_focus(
                    focus_finger,
                    focus_probability=(
                        state["curriculum_goal_pair_focus_probability"]
                        if focus_finger is not None else 1.0)))
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
                and (focus_changed or goal_pair_focus_changed)):
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
                self.config.effective_transition_min_iterations,
                self.config.effective_transition_max_iterations),
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
            finger_rates.append(
                float(accumulator[
                    f"press_finger_{finger}_success"]) / count)
        metrics["finger_min"] = (
            min(finger_rates) if finger_rates else -1.0)
        metrics["episodes"] = episodes
        return {
            key: float(metrics[key])
            for key in self.BRIDGE_METRIC_KEYS
        }

    def _regression_failures(self, metrics):
        baseline = self.stage_entry_baseline
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
        return tuple(failures)

    def _update_regression(self, metrics):
        failures = self._regression_failures(metrics)
        self.regression_metrics = failures
        if failures:
            self.regression_bad_windows += 1
        else:
            self.regression_bad_windows = 0
        self.regression_hold = (
            self.regression_bad_windows
            >= self.config.regression_hold_windows)

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
                metrics = self._finalize_bridge_window()
                self.bridge_accumulator = self._empty_bridge_accumulator()
                if metrics:
                    self.bridge_windows.append(metrics)
                    self.bridge_last_metrics = dict(metrics)
                    self._update_regression(metrics)
                    completed += 1
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
                metrics = self._finalize_bridge_window()
                self.bridge_accumulator = self._empty_bridge_accumulator()
                if metrics:
                    self.bridge_windows.append(metrics)
                    self.bridge_last_metrics = dict(metrics)
                    self._update_regression(metrics)
                    completed += 1
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
        return (
            bool(self.bridge_last_metrics)
            and float(self.bridge_last_metrics.get("finger_min", -1.0))
            >= self.config.bridge_hard_timeout_min_per_finger_rate)

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
            self.required_song_fingers
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
            and self._thumb_gate_passes(
                stats, self.config.thumb_integrated_distance)
        )
        return 1.0 if passed else 0.0

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
            self.chord_unresolved_signatures = []
        if self.stage == "transition_window":
            self.transition_difficulty_level = 0
        elif previous == "transition_window":
            self.transition_difficulty_level = (
                len(self.config.transition_window_seconds) - 1)
        if self.stage == "goal_pair":
            self.goal_pair_phase = "retention"
            self.goal_pair_phase_iteration = 0
            self.goal_pair_mixed_level = 0
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_focus_finger = 0
            self._reset_goal_pair_phase_evidence()
        elif previous == "goal_pair":
            self.goal_pair_phase = "full"
            self.goal_pair_phase_iteration = 0
            self.goal_pair_mixed_level = (
                len(self.config.goal_pair_mixed_transition_fractions) - 1)
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_focus_finger = 0
            self._reset_goal_pair_phase_evidence()
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
        self.chord_focus_iteration = 0
        self.stalled = False
        self.recent.clear()

    def _retry_chord_focus_cycle(self):
        self.forced_advance = True
        self.forced_advance_count += 1
        self.last_forced_advance_from = "chord_fine_reach:mixed"
        self.chord_focus_cycle += 1
        self.chord_focus_index = 0
        self.chord_focus_iteration = 0
        self.stalled = False
        self.recent.clear()

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

    def _goal_pair_rehearsal_row(self, stats, finger):
        prefix = f"curriculum_goal_pair_rehearsal_finger_{finger}"
        count = self._goal_pair_stat(
            stats, f"{prefix}_target_active_count")
        if count is None:
            active = self._goal_pair_stat(stats, f"{prefix}_target_active")
            episodes = self._goal_pair_stat(stats, "episodes")
            if active is not None and episodes is not None:
                count = active * episodes
        success = self._goal_pair_stat(stats, f"{prefix}_press_success")
        distance = self._goal_pair_stat(stats, f"{prefix}_target_distance")
        if count is None or success is None or distance is None:
            return None
        return {
            "count": max(0.0, count),
            "success": success,
            "distance": distance,
        }

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
        if (next_count is None or target_count is None
                or success is None or distance is None or progress is None):
            return None
        return {
            "next_count": max(0.0, next_count),
            "target_count": max(0.0, target_count),
            "success": success,
            "distance": distance,
            "progress": progress,
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
            rehearsal = self._goal_pair_rehearsal_row(stats, finger)
            if rehearsal is not None:
                count = rehearsal["count"]
                evidence[f"rehearsal_{finger}_count"] += count
                evidence[f"rehearsal_{finger}_success_sum"] += (
                    rehearsal["success"] * count)
                evidence[f"rehearsal_{finger}_distance_sum"] += (
                    rehearsal["distance"] * count)
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
            rehearsal = (
                f"curriculum_goal_pair_rehearsal_finger_{finger}")
            rehearsal_count = evidence[f"rehearsal_{finger}_count"]
            if rehearsal_count > 0.0:
                combined[f"{rehearsal}_target_active_count"] = (
                    rehearsal_count)
                combined[f"{rehearsal}_press_success"] = (
                    evidence[f"rehearsal_{finger}_success_sum"]
                    / rehearsal_count)
                combined[f"{rehearsal}_target_distance"] = (
                    evidence[f"rehearsal_{finger}_distance_sum"]
                    / rehearsal_count)
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
        return combined

    def _goal_pair_retention_sample(self, stats):
        fingers = self._goal_pair_fingers(stats)
        if not fingers:
            return None
        rows = [
            self._goal_pair_rehearsal_row(stats, finger)
            for finger in fingers]
        minimum = self.config.goal_pair_phase_min_evidence
        if any(row is None or row["count"] < minimum for row in rows):
            return None
        return all(
            row["success"] >= self.config.goal_pair_rehearsal_press_rate
            and row["distance"] <= self.config.goal_pair_rehearsal_distance
            for row in rows)

    def _goal_pair_mixed_sample(self, stats):
        fingers = self._goal_pair_fingers(stats)
        preservation = self._goal_pair_preservation_row(stats)
        transition_rows = [
            self._goal_pair_transition_row(stats, finger)
            for finger in fingers]
        rehearsal_rows = [
            self._goal_pair_rehearsal_row(stats, finger)
            for finger in fingers]
        minimum = self.config.goal_pair_phase_min_evidence
        level = min(
            max(int(self.goal_pair_mixed_level), 0),
            len(self.config.goal_pair_mixed_transition_fractions) - 1)
        preview_only = level < self.config.goal_pair_preview_levels
        if (not fingers or preservation is None
                or preservation["count"] < minimum
                or any(
                    row is None
                    or row["next_count"] < minimum
                    or (not preview_only
                        and row["target_count"] < minimum)
                    for row in transition_rows)
                or any(
                    row is None or row["count"] < minimum
                    for row in rehearsal_rows)):
            return None
        sequence_sample = self._goal_pair_sequence_sample(stats)
        if sequence_sample is None:
            return None
        return (
            preservation["value"]
                >= self.config.goal_pair_mixed_preservation_rates[level]
            and sequence_sample
            and all(
                row["success"]
                    >= self.config.goal_pair_rehearsal_press_rate
                and row["distance"]
                    <= self.config.goal_pair_rehearsal_distance
                for row in rehearsal_rows)
            and all(
                (preview_only
                 or row["success"]
                    >= self.config.goal_pair_mixed_press_rates[level])
                and row["distance"]
                    <= self.config.goal_pair_mixed_distances[level]
                and row["progress"]
                    >= self.config.goal_pair_mixed_min_next_progress
                for row in transition_rows))

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
        if self.goal_pair_phase == "retention":
            row = self._goal_pair_rehearsal_row(stats, finger)
            if row is None or row["count"] < minimum:
                return None
            passed = (
                row["success"] >= self.config.goal_pair_rehearsal_press_rate
                and row["distance"]
                    <= self.config.goal_pair_rehearsal_distance)
            score = (row["success"], -row["distance"], finger)
            return passed, score
        row = self._goal_pair_transition_row(stats, finger)
        rehearsal = self._goal_pair_rehearsal_row(stats, finger)
        level = min(
            max(int(self.goal_pair_mixed_level), 0),
            len(self.config.goal_pair_mixed_transition_fractions) - 1)
        preview_only = level < self.config.goal_pair_preview_levels
        if (row is None or rehearsal is None
                or row["next_count"] < minimum
                or (not preview_only and row["target_count"] < minimum)
                or rehearsal["count"] < minimum):
            return None
        rehearsal_passed = (
            rehearsal["success"]
                >= self.config.goal_pair_rehearsal_press_rate
            and rehearsal["distance"]
                <= self.config.goal_pair_rehearsal_distance)
        transition_passed = (
            (preview_only
             or row["success"]
                >= self.config.goal_pair_mixed_press_rates[level])
            and row["distance"]
                <= self.config.goal_pair_mixed_distances[level]
            and row["progress"]
                >= self.config.goal_pair_mixed_min_next_progress)
        transition_score = (
            row["progress"] if preview_only else row["success"])
        score = (
            min(rehearsal["success"], transition_score),
            -max(
                rehearsal["distance"]
                    / self.config.goal_pair_rehearsal_distance,
                row["distance"]
                    / self.config.goal_pair_mixed_distances[level]),
            finger)
        return rehearsal_passed and transition_passed, score

    def _update_goal_pair_focus(self, stats):
        if self.goal_pair_phase == "full":
            changed = self.goal_pair_focus_finger != 0
            self.goal_pair_focus_finger = 0
            return changed
        fingers = self._goal_pair_fingers(stats)
        results = {}
        candidates = {}
        for finger in fingers:
            result = self._goal_pair_focus_unresolved(stats, finger)
            results[finger] = result
            if result is not None and not result[0]:
                candidates[finger] = result[1]
        current = self.goal_pair_focus_finger
        if current > 0:
            current_result = results.get(current)
            if current_result is None or not current_result[0]:
                return False
        if any(results.get(finger) is None for finger in fingers):
            return False
        selected = min(candidates, key=candidates.get) if candidates else 0
        changed = selected != current
        self.goal_pair_focus_finger = selected
        return changed

    def _sync_goal_pair_phase(self, stats):
        if self.stage != "goal_pair":
            return False
        focus_changed = self._update_goal_pair_focus(stats)
        if focus_changed:
            self.recent.clear()
            self._reset_goal_pair_phase_evidence()
            return True
        if self.goal_pair_phase == "full":
            return False
        sample = (
            self._goal_pair_retention_sample(stats)
            if self.goal_pair_phase == "retention"
            else self._goal_pair_mixed_sample(stats))
        if sample is not None:
            self.recent.append(1.0 if sample else 0.0)
            self._reset_goal_pair_phase_evidence()
        minimum = (
            self.config.goal_pair_retention_min_iterations
            if self.goal_pair_phase == "retention"
            else self.config.goal_pair_mixed_min_iterations)
        phase_iteration = (
            self.goal_pair_phase_iteration
            if self.goal_pair_phase == "retention"
            else self.goal_pair_mixed_level_iteration)
        passed = (
            phase_iteration >= minimum
            and len(self.recent) == self.config.promotion_windows
            and all(value >= 1.0 for value in self.recent))
        if not passed:
            return False
        if (self.goal_pair_phase == "mixed"
                and self.goal_pair_mixed_level + 1
                    < len(
                        self.config.goal_pair_mixed_transition_fractions)):
            self.goal_pair_mixed_level += 1
            self.goal_pair_mixed_level_iteration = 0
            self.goal_pair_focus_finger = 0
            self.recent.clear()
            self._reset_goal_pair_phase_evidence()
            self._reset_bridge_evidence(reset_regression=True)
            self.stalled = False
            return True
        index = self.GOAL_PAIR_PHASES.index(self.goal_pair_phase)
        self.goal_pair_phase = self.GOAL_PAIR_PHASES[index + 1]
        self.goal_pair_phase_iteration = 0
        self.goal_pair_mixed_level = 0
        self.goal_pair_mixed_level_iteration = 0
        self.goal_pair_focus_finger = 0
        self.recent.clear()
        self._reset_goal_pair_phase_evidence()
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
                        < self.config.goal_pair_promotion_transition_press_rate):
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
            self, stats, transition_difficulty_changed=False):
        evidence_allowed = (
            (self.stage != "frozen_context"
             or self.frozen_context_final_applied)
            and not transition_difficulty_changed)
        if evidence_allowed:
            self._accumulate_bridge_stats(stats)
        self.stalled = False

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
            and not self.regression_hold
            and self._bridge_windows_pass())
        if normal_passed:
            self._promote()
            return self.state()
        hard_iteration = (
            minimum + self.config.late_stage_grace_iterations)
        if (self.stage_iteration >= hard_iteration
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
        self.total_iteration += 1
        self.stage_iteration += 1
        if self.stage == "chord_fine_reach":
            self.chord_focus_iteration += 1
            self.chord_focus_total_iteration += 1
        if self.stage == "goal_pair":
            self.goal_pair_phase_iteration += 1
            if self.goal_pair_phase == "mixed":
                self.goal_pair_mixed_level_iteration += 1
            self._accumulate_goal_pair_phase_stats(stats)
            goal_pair_stats = self._goal_pair_aggregated_stats(stats)
        else:
            goal_pair_stats = stats
        transition_difficulty_changed = (
            self._sync_transition_difficulty())
        goal_pair_phase_changed = self._sync_goal_pair_phase(
            goal_pair_stats)
        if (self.forced_stage is not None
                and self.stage != "chord_fine_reach"):
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
                elif self.chord_focus_cycle == 0:
                    self._retry_chord_focus_cycle()
                else:
                    self.stalled = True
            return self.state()
        if self.stage in self.BRIDGE_STAGES:
            return self._after_bridge_iteration(
                goal_pair_stats,
                transition_difficulty_changed or goal_pair_phase_changed)
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
