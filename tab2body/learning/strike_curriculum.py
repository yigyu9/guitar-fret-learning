"""Performance-gated curriculum for the pick-only strike task.

The curriculum deliberately separates acquisition stages from song timing:

``A0_PICK_GRIP``
    Hold the reference thumb/index grip and natural free-finger shape.
``A1_TIP_READY``
    Move the virtual ``RH:pick`` point to the entry side of a target string.
``A2_FREE_CROSSING``
    Cross the requested finite string segment without a timing gate.
``A3_TIMED_CROSSING``
    Learn timed crossing with a 100 -> 67 -> 50 ms tolerance curriculum.
``A4_ZONE_CONTROL``
    Retain the final 50 ms timing tolerance and control longitudinal position.
``X0_MINI_STRUM``
    First multi-string extension: an ordered, adjacent-string down mini-strum
    at A4's tempo and timing tolerance (see
    ``strike/RIGHT_HAND_EXTENSIONS.md`` section 10). Uses the same event-goal
    machinery as A4 (``StrikeGoalSequence`` gesture/traversal/protected
    masks, the ordered multi-string matcher) and additionally gates
    promotion on strum order/direction/protected-crossing accuracy.
 

Every transition is performance-gated.  Reaching a stage's maximum iteration
count marks the curriculum as stalled; it never promotes the policy merely
because enough iterations elapsed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Optional, Tuple

try:
    from tab2body.strike_contract import (
        A0_PICK_GRIP,
        A1_TIP_READY,
        A2_FREE_CROSSING,
        A3_TIMED_CROSSING,
        A4_ZONE_CONTROL,
        X0_MINI_STRUM,
        SONG_GOAL_STAGES,
        STRIKE_STAGES,
        TERMINAL_EVIDENCE_STAGES,
    )
except ModuleNotFoundError as exc:
    if exc.name != "tab2body":
        raise
    from strike_contract import (
        A0_PICK_GRIP,
        A1_TIP_READY,
        A2_FREE_CROSSING,
        A3_TIMED_CROSSING,
        A4_ZONE_CONTROL,
        X0_MINI_STRUM,
        SONG_GOAL_STAGES,
        STRIKE_STAGES,
        TERMINAL_EVIDENCE_STAGES,
    )


@dataclass(frozen=True)
class StrikeCurriculumConfig:
    """Thresholds and iteration bounds for :class:`StrikeCurriculum`."""

    grip_min_iterations: int = 100
    grip_max_iterations: int = 1000
    ready_min_iterations: int = 100
    ready_max_iterations: int = 1000
    crossing_min_iterations: int = 200
    crossing_max_iterations: int = 2000
    timed_min_iterations: int = 300
    timed_max_iterations: int = 3000
    zone_min_iterations: int = 300
    zone_max_iterations: int = 5000
    x0_min_iterations: int = 300
    x0_max_iterations: int = 5000

    promotion_windows: int = 3
    terminal_evidence_episodes: int = 1
    grip_success_gate: float = 0.90
    tip_ready_success_gate: float = 0.90
    release_recall_gate: float = 0.98
    false_positive_rate_gate: float = 0.02
    strike_f1_gate: float = 0.98
    timing_tolerances_ms: Tuple[int, ...] = (100, 67, 50)
    tempo_lambdas: Tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)
    timed_f1_by_level: Optional[Tuple[float, ...]] = None
    zone_f1_gate: float = 0.98
    zone_success_gate: float = 0.95
    x0_completion_rate_gate: float = 0.95
    x0_traversal_recall_gate: float = 0.99
    x0_order_accuracy_gate: float = 0.99
    x0_direction_accuracy_gate: float = 0.99
    x0_max_protected_rate_gate: float = 0.01

    def __post_init__(self):
        limits = (
            (self.grip_min_iterations, self.grip_max_iterations),
            (self.ready_min_iterations, self.ready_max_iterations),
            (self.crossing_min_iterations, self.crossing_max_iterations),
            (self.timed_min_iterations, self.timed_max_iterations),
            (self.zone_min_iterations, self.zone_max_iterations),
            (self.x0_min_iterations, self.x0_max_iterations),
        )
        if any(
                isinstance(value, bool) or not isinstance(value, int)
                for pair in limits for value in pair):
            raise ValueError(
                "strike curriculum min/max iterations must be integers")
        if any(minimum < 0 or maximum < minimum
               for minimum, maximum in limits):
            raise ValueError("strike curriculum min/max iterations are invalid")
        if (isinstance(self.promotion_windows, bool)
                or not isinstance(self.promotion_windows, int)
                or self.promotion_windows < 1):
            raise ValueError("promotion_windows must be a positive integer")
        if (isinstance(self.terminal_evidence_episodes, bool)
                or not isinstance(self.terminal_evidence_episodes, int)
                or self.terminal_evidence_episodes < 1):
            raise ValueError(
                "terminal_evidence_episodes must be a positive integer")
        for name in (
                "grip_success_gate",
                "tip_ready_success_gate",
                "release_recall_gate",
                "false_positive_rate_gate",
                "strike_f1_gate",
                "zone_f1_gate",
                "zone_success_gate"
                "x0_completion_rate_gate",
                "x0_traversal_recall_gate",
                "x0_order_accuracy_gate",
                "x0_direction_accuracy_gate",
                "x0_max_protected_rate_gate"
                ):
            value = float(getattr(self, name))
            if (isinstance(getattr(self, name), bool)
                    or not math.isfinite(value)
                    or not 0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be finite and in [0, 1]")
        tolerances = tuple(self.timing_tolerances_ms)
        if len(tolerances) < 1:
            raise ValueError("timing_tolerances_ms must not be empty")
        if any(isinstance(value, bool) or not isinstance(value, int)
               or value <= 0 for value in tolerances):
            raise ValueError(
                "timing_tolerances_ms must contain positive integer milliseconds")
        if any(later >= earlier
               for earlier, later in zip(tolerances, tolerances[1:])):
            raise ValueError(
                "timing_tolerances_ms must be strictly decreasing")
        tempo_lambdas = tuple(float(value) for value in self.tempo_lambdas)
        if len(tempo_lambdas) < 2:
            raise ValueError("tempo_lambdas must contain at least two levels")
        if tempo_lambdas[0] != 0.0 or tempo_lambdas[-1] != 1.0:
            raise ValueError("tempo_lambdas must start at 0 and end at 1")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0
               for value in tempo_lambdas):
            raise ValueError("tempo_lambdas must be finite and in [0, 1]")
        if any(later <= earlier
               for earlier, later in zip(tempo_lambdas, tempo_lambdas[1:])):
            raise ValueError("tempo_lambdas must be strictly increasing")
        f1_gates = self.timed_f1_gates
        if len(f1_gates) != len(tolerances):
            raise ValueError(
                "timed_f1_by_level must match timing_tolerances_ms")
        raw_f1_gates = (
            (self.strike_f1_gate,) * len(tolerances)
            if self.timed_f1_by_level is None
            else tuple(self.timed_f1_by_level))
        if any(isinstance(value, bool) for value in raw_f1_gates):
            raise ValueError(
                "timed_f1_by_level values must be finite and in [0, 1]")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0
               for value in f1_gates):
            raise ValueError(
                "timed_f1_by_level values must be finite and in [0, 1]")
        if any(later < earlier
               for earlier, later in zip(f1_gates, f1_gates[1:])):
            raise ValueError(
                "timed_f1_by_level must be non-decreasing")

    @property
    def timed_f1_gates(self) -> Tuple[float, ...]:
        if self.timed_f1_by_level is None:
            return tuple(
                float(self.strike_f1_gate)
                for _ in self.timing_tolerances_ms)
        return tuple(float(value) for value in self.timed_f1_by_level)


_STAT_ALIASES = {
    "grip_success_rate": (
        "strike_grip_success_rate",
        "curriculum_grip_success_rate", "grip_success_rate"),
    "tip_ready_success_rate": (
        "strike_tip_ready_success_rate",
        "curriculum_tip_ready_success_rate", "tip_ready_success_rate"),
    "release_recall": (
        "strike_release_recall",
        "curriculum_release_recall", "release_recall"),
    "false_positive_rate": (
        "strike_false_positive_rate",
        "curriculum_false_positive_rate", "false_positive_rate",
        "release_false_positive_rate"),
    "strike_f1": (
        "strike_episode_f1",
        "curriculum_strike_f1", "strike_f1"),
    "timing_p95_ms": (
        "strike_timing_p95_ms",
        "curriculum_timing_p95_ms", "timing_p95_ms"),
    "zone_success_rate": (
        "strike_zone_success_rate",
        "curriculum_zone_success_rate", "zone_success_rate"),
    "failure_termination_rate": (
        "failure_termination",
        "curriculum_failure_termination_rate"),
    "strum_completion_rate": (
        "strike_strum_completion_rate",),
    "strum_traversal_recall": (
        "strike_strum_traversal_recall",),
    "strum_order_accuracy": (
        "strike_strum_order_accuracy",),
    "strum_direction_accuracy": (
        "strike_strum_direction_accuracy",),
    "strum_protected_crossing_rate": (
        "strike_strum_protected_crossing_rate",),
}

_EPISODE_STAT_KEYS = {
    "grip_success_rate": "strike_grip_success_rate",
    "tip_ready_success_rate": "strike_tip_ready_success_rate",
    "release_recall": "strike_release_recall",
    "false_positive_rate": "strike_false_positive_rate",
    "strike_f1": "strike_episode_f1",
    "timing_p95_ms": "strike_timing_p95_ms",
    "zone_success_rate": "strike_zone_success_rate",
    "failure_termination_rate": "failure_termination",
    "strum_completion_rate": "strike_strum_completion_rate",
    "strum_traversal_recall": "strike_strum_traversal_recall",
    "strum_order_accuracy": "strike_strum_order_accuracy",
    "strum_direction_accuracy": "strike_strum_direction_accuracy",
    "strum_protected_crossing_rate": "strike_strum_protected_crossing_rate",
}

_STAGE_REQUIRED_EPISODE_STATS = {
    A0_PICK_GRIP: (
        "grip_success_rate",
        "failure_termination_rate",
    ),
    A1_TIP_READY: (
        "grip_success_rate",
        "tip_ready_success_rate",
        "failure_termination_rate",
    ),
    A2_FREE_CROSSING: (
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "failure_termination_rate",
    ),
    A3_TIMED_CROSSING: (
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "strike_f1",
        "timing_p95_ms",
        "failure_termination_rate",
    ),
    A4_ZONE_CONTROL: (
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "strike_f1",
        "timing_p95_ms",
        "zone_success_rate",
        "failure_termination_rate",
    ),
    X0_MINI_STRUM: (
        "grip_success_rate",
        "tip_ready_success_rate",
        "release_recall",
        "false_positive_rate",
        "strike_f1",
        "timing_p95_ms",
        "zone_success_rate",
        "strum_completion_rate",
        "strum_traversal_recall",
        "strum_order_accuracy",
        "strum_direction_accuracy",
        "strum_protected_crossing_rate",
        "failure_termination_rate",
    ),
}

_EVIDENCE_RATE_STATS = tuple(
    name for name in _EPISODE_STAT_KEYS
    if name != "timing_p95_ms")


def _validated_stat_value(name: str, value: float) -> Optional[float]:
    """Return a domain-valid curriculum statistic or fail closed with ``None``."""
    if name == "timing_p95_ms":
        return value if value >= 0.0 else None
    return value if 0.0 <= value <= 1.0 else None


def _finite_stat(stats: Mapping[str, object], name: str) -> Optional[float]:
    """Read one bounded scalar statistic; invalid values fail closed."""
    for key in _STAT_ALIASES[name]:
        if key not in stats:
            continue
        if isinstance(stats[key], bool):
            return None
        try:
            value = float(stats[key])
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        return _validated_stat_value(name, value)
    return None


def _finite_episode_stat(
        stats: Mapping[str, object], name: str) -> Optional[float]:
    """Read a domain-valid completed-episode metric, never a live alias."""
    key = _EPISODE_STAT_KEYS[name]
    if key not in stats:
        return None
    if isinstance(stats[key], bool):
        return None
    try:
        value = float(stats[key])
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return _validated_stat_value(name, value)


def _has_completed_episode(stats: Mapping[str, object]) -> bool:
    """Return whether this statistics window contains terminal evidence."""
    value = stats.get("episodes")
    if isinstance(value, bool):
        return False
    try:
        count = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(count) and count >= 1.0 and count.is_integer()


def _completed_episode_count(stats: Mapping[str, object]) -> int:
    """Return a validated episode count, or zero for no usable evidence."""
    if not _has_completed_episode(stats):
        return 0
    return int(float(stats["episodes"]))


class StrikeCurriculum:
    """Five-stage, performance-gated strike acquisition curriculum."""
    """ +) Performance-gated strike acquisition curriculum (A0-A4, then X0)."""

    STAGES = STRIKE_STAGES
    TIMED_STAGE = A3_TIMED_CROSSING
    # FINAL_STAGE = A4_ZONE_CONTROL
    FINAL_STAGE = X0_MINI_STRUM

    def __init__(self, config: StrikeCurriculumConfig = StrikeCurriculumConfig()):
        self.config = config
        self.stage = A0_PICK_GRIP
        self.stage_iteration = 0
        self.total_iteration = 0
        self.stalled = False
        self.promotion_streak = 0
        self.timing_level = 0
        self.timing_streak = 0
        self.tempo_level = 0
        self.complete = False
        self._evidence_episodes = 0
        self._evidence_rate_sums = {
            name: 0.0 for name in _EVIDENCE_RATE_STATS}
        self._evidence_timing_p95_max_ms = 0.0

    @property
    def timing_tolerance_ms(self) -> int:
        """Current numeric task tolerance.

        Before A3 the task receives the widest value but must keep timing
        inapplicable.  A4 and X0 (which continues at A4's final tempo/
+       tolerance) always retain the final, narrowest tolerance.
        """
        #if self.stage == A4_ZONE_CONTROL:
        if self.stage in SONG_GOAL_STAGES:
            return int(self.config.timing_tolerances_ms[-1])
        return int(self.config.timing_tolerances_ms[self.timing_level])

    @property
    def timing_applicable(self) -> bool:
        #return self.stage in (A3_TIMED_CROSSING, A4_ZONE_CONTROL)
        return self.stage in (A3_TIMED_CROSSING,) + SONG_GOAL_STAGES

    @property
    def tempo_lambda(self) -> float:
        if self.stage != A4_ZONE_CONTROL:
            return 1.0
        return float(self.config.tempo_lambdas[self.tempo_level])

    @property
    def original_tempo_reached(self) -> bool:
        return self.tempo_lambda == 1.0

    @property
    def current_timed_f1_gate(self) -> float:
        return float(self.config.timed_f1_gates[self.timing_level])

    @property
    def current_strike_f1_gate(self) -> float:
        #if self.stage == A4_ZONE_CONTROL:
        if self.stage in SONG_GOAL_STAGES: 
            return float(self.config.zone_f1_gate)
        return self.current_timed_f1_gate

    def state(self):
        """Return a JSON/checkpoint-friendly snapshot."""
        state = {
            "curriculum_stage": self.stage,
            "curriculum_stage_index": self.STAGES.index(self.stage),
            "curriculum_stage_iteration": int(self.stage_iteration),
            "curriculum_total_iteration": int(self.total_iteration),
            "curriculum_stalled": bool(self.stalled),
            "curriculum_promotion_streak": int(self.promotion_streak),
            "curriculum_timing_level": int(self.timing_level),
            "curriculum_timing_tolerance_ms": self.timing_tolerance_ms,
            "curriculum_timing_applicable": self.timing_applicable,
            "curriculum_timing_streak": int(self.timing_streak),
            "curriculum_tempo_level": int(self.tempo_level),
            "curriculum_tempo_lambda": self.tempo_lambda,
            "curriculum_original_tempo_reached": self.original_tempo_reached,
            "curriculum_strike_f1_gate": self.current_strike_f1_gate,
            "curriculum_complete": bool(self.complete),
            "curriculum_evidence_episode_target": int(
                self.config.terminal_evidence_episodes),
            "curriculum_evidence_episodes": int(self._evidence_episodes),
            "curriculum_evidence_timing_p95_max_ms": float(
                self._evidence_timing_p95_max_ms),
        }
        state.update({
            f"curriculum_evidence_{name}_sum": float(value)
            for name, value in self._evidence_rate_sums.items()
        })
        return state

    def load_context(self, context: Mapping[str, object]):
        """Restore an exact curriculum snapshot from training context."""
        stage = context.get("curriculum_stage", A0_PICK_GRIP)
        if stage not in self.STAGES:
            raise ValueError(f"unknown strike curriculum stage: {stage!r}")

        def nonnegative_integer(key, default=0):
            value = context.get(key, default)
            if isinstance(value, bool):
                raise ValueError(f"{key} must be a non-negative integer")
            try:
                integer = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{key} must be a non-negative integer") from exc
            if integer < 0 or integer != value:
                raise ValueError(f"{key} must be a non-negative integer")
            return integer

        def strict_boolean(key, default=False):
            value = context.get(key, default)
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be bool")
            return value

        stage_iteration = nonnegative_integer(
            "curriculum_stage_iteration")
        total_iteration = nonnegative_integer(
            "curriculum_total_iteration")
        if total_iteration < stage_iteration:
            raise ValueError(
                "curriculum_total_iteration cannot precede stage iteration")

        promotion_streak = nonnegative_integer(
            "curriculum_promotion_streak")
        timing_streak = nonnegative_integer(
            "curriculum_timing_streak")
        if promotion_streak >= self.config.promotion_windows:
            raise ValueError(
                "saved promotion streak should already have caused a transition")
        if timing_streak >= self.config.promotion_windows:
            raise ValueError(
                "saved timing streak should already have caused a transition")

        timing_level = nonnegative_integer("curriculum_timing_level")
        last_level = len(self.config.timing_tolerances_ms) - 1
        if timing_level > last_level:
            raise ValueError("curriculum_timing_level is outside the schedule")
        if stage in self.STAGES[:3] and timing_level != 0:
            raise ValueError("pre-timing stages must use timing level zero")
        if stage == A4_ZONE_CONTROL and timing_level != last_level:
            raise ValueError("A4 must use the final timing tolerance")
        tempo_level = nonnegative_integer("curriculum_tempo_level")
        last_tempo_level = len(self.config.tempo_lambdas) - 1
        if tempo_level > last_tempo_level:
            raise ValueError("curriculum_tempo_level is outside the schedule")
        if stage != A4_ZONE_CONTROL and tempo_level != 0:
            raise ValueError("pre-A4 stages must use tempo level zero")

        self.stage = str(stage)
        self.stage_iteration = stage_iteration
        self.total_iteration = total_iteration
        self.stalled = strict_boolean("curriculum_stalled")
        self.promotion_streak = promotion_streak
        self.timing_level = timing_level
        self.timing_streak = timing_streak
        self.tempo_level = tempo_level
        self.complete = strict_boolean("curriculum_complete")
        if self.complete and self.stage != A4_ZONE_CONTROL:
            raise ValueError("only A4 may be a complete strike curriculum")
        if self.complete and (promotion_streak or timing_streak):
            raise ValueError("a complete curriculum cannot retain a streak")
        if self.complete and not self.original_tempo_reached:
            raise ValueError("a complete curriculum must pass original tempo")

        saved_evidence_target = context.get(
            "curriculum_evidence_episode_target",
            self.config.terminal_evidence_episodes)
        if (isinstance(saved_evidence_target, bool)
                or int(saved_evidence_target)
                != self.config.terminal_evidence_episodes):
            raise ValueError(
                "saved terminal evidence target disagrees with config")
        evidence_episodes = nonnegative_integer(
            "curriculum_evidence_episodes")
        if evidence_episodes >= self.config.terminal_evidence_episodes:
            raise ValueError(
                "saved terminal evidence should have been consumed already")
        evidence_sums = {}
        for name in _EVIDENCE_RATE_STATS:
            key = f"curriculum_evidence_{name}_sum"
            try:
                value = float(context.get(key, 0.0))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{key} must be finite") from exc
            if (not math.isfinite(value) or value < 0.0
                    or value > evidence_episodes + 1e-6):
                raise ValueError(
                    f"{key} must be in [0, accumulated episodes]")
            evidence_sums[name] = value
        timing_p95_max = context.get(
            "curriculum_evidence_timing_p95_max_ms", 0.0)
        try:
            timing_p95_max = float(timing_p95_max)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "curriculum evidence timing p95 must be finite") from exc
        if not math.isfinite(timing_p95_max) or timing_p95_max < 0.0:
            raise ValueError(
                "curriculum evidence timing p95 must be non-negative")
        if evidence_episodes == 0 and (
                any(evidence_sums.values()) or timing_p95_max != 0.0):
            raise ValueError(
                "empty curriculum evidence cannot retain metric sums")
        self._evidence_episodes = evidence_episodes
        self._evidence_rate_sums = evidence_sums
        self._evidence_timing_p95_max_ms = timing_p95_max

        saved_tolerance = context.get("curriculum_timing_tolerance_ms")
        if (saved_tolerance is not None
                and float(saved_tolerance) != self.timing_tolerance_ms):
            raise ValueError(
                "saved timing tolerance disagrees with timing level/config")
        saved_f1_gate = context.get("curriculum_strike_f1_gate")
        if (saved_f1_gate is not None
                and float(saved_f1_gate) != self.current_strike_f1_gate):
            raise ValueError(
                "saved strike F1 gate disagrees with timing level/config")
        saved_tempo = context.get("curriculum_tempo_lambda")
        if (saved_tempo is not None
                and float(saved_tempo) != self.tempo_lambda):
            raise ValueError(
                "saved tempo lambda disagrees with tempo level/config")
        return self.state()

    def _reset_terminal_evidence(self):
        self._evidence_episodes = 0
        for name in self._evidence_rate_sums:
            self._evidence_rate_sums[name] = 0.0
        self._evidence_timing_p95_max_ms = 0.0

    def _consume_terminal_evidence(
            self, stats: Mapping[str, object]):
        """Pool a full non-overlapping cohort before evaluating a gate.

        Successful A1 episodes used to finish early while failures arrived in
        a later timeout burst.  Treating each PPO rollout as an independent
        gate window therefore let tiny success-only batches advance a streak.
        Rates are now weighted by completed episode count until at least one
        configured cohort is available.  Timing p95 uses the conservative
        maximum of contributing rollout p95 values.
        """
        count = _completed_episode_count(stats)
        if count == 0:
            return False, {}
        required = _STAGE_REQUIRED_EPISODE_STATS[self.stage]
        values = {
            name: _finite_episode_stat(stats, name)
            for name in required
        }
        if any(value is None for value in values.values()):
            self._reset_terminal_evidence()
            return True, {"episodes": count}

        self._evidence_episodes += count
        for name, value in values.items():
            if name == "timing_p95_ms":
                self._evidence_timing_p95_max_ms = max(
                    self._evidence_timing_p95_max_ms, value)
            else:
                self._evidence_rate_sums[name] += value * count

        if (self._evidence_episodes
                < self.config.terminal_evidence_episodes):
            return False, {}

        episodes = self._evidence_episodes
        pooled = {"episodes": episodes}
        for name in required:
            if name == "timing_p95_ms":
                pooled[_EPISODE_STAT_KEYS[name]] = (
                    self._evidence_timing_p95_max_ms)
            else:
                pooled[_EPISODE_STAT_KEYS[name]] = (
                    self._evidence_rate_sums[name] / episodes)
        self._reset_terminal_evidence()
        return True, pooled

    def apply(self, env):
        """Apply stage/tolerance and reset only when either value changed."""
        tolerance = self.timing_tolerance_ms
        tempo_lambda = self.tempo_lambda
        changed = (
            getattr(env, "curriculum_stage", None) != self.stage
            or getattr(env, "timing_tolerance_ms", None) != tolerance
            or (hasattr(env, "tempo_lambda")
                and getattr(env, "tempo_lambda") != tempo_lambda)
        )
        if hasattr(env, "tempo_lambda"):
            reset_observation = env.set_curriculum_stage(
                self.stage, tolerance,
                tempo_lambda=tempo_lambda, reset=changed)
        else:
            reset_observation = env.set_curriculum_stage(
                self.stage, tolerance, reset=changed)
        state = self.state()
        if reset_observation is not None:
            state["_reset_observation"] = reset_observation
        return state

    def _limits(self):
        if self.stage == A0_PICK_GRIP:
            return (self.config.grip_min_iterations,
                    self.config.grip_max_iterations)
        if self.stage == A1_TIP_READY:
            return (self.config.ready_min_iterations,
                    self.config.ready_max_iterations)
        if self.stage == A2_FREE_CROSSING:
            return (self.config.crossing_min_iterations,
                    self.config.crossing_max_iterations)
        if self.stage == A3_TIMED_CROSSING:
            return (self.config.timed_min_iterations,
                    self.config.timed_max_iterations)
        if self.stage == A4_ZONE_CONTROL:
            return (self.config.zone_min_iterations,
                    self.config.zone_max_iterations)
        if self.stage == X0_MINI_STRUM:
            return (self.config.x0_min_iterations,
                    self.config.x0_max_iterations)
        raise RuntimeError("unknown strike curriculum stage")

    def _performance_passed(self, stats: Mapping[str, object]) -> bool:
        episode_stage = self.stage in TERMINAL_EVIDENCE_STAGES
        if episode_stage and not _has_completed_episode(stats):
            return False
        read_stat = _finite_episode_stat if episode_stage else _finite_stat

        grip = read_stat(stats, "grip_success_rate")
        if grip is None or grip < self.config.grip_success_gate:
            return False

        failure_rate = read_stat(stats, "failure_termination_rate")
        if failure_rate is None or failure_rate > 0.0:
            return False
        if self.stage == A0_PICK_GRIP:
            return True

        ready = read_stat(stats, "tip_ready_success_rate")
        if ready is None or ready < self.config.tip_ready_success_gate:
            return False
        if self.stage == A1_TIP_READY:
            return True

        recall = read_stat(stats, "release_recall")
        false_positive = read_stat(stats, "false_positive_rate")
        if (recall is None or false_positive is None
                or recall < self.config.release_recall_gate
                or false_positive > self.config.false_positive_rate_gate):
            return False
        if self.stage == A2_FREE_CROSSING:
            return True

        f1 = read_stat(stats, "strike_f1")
        timing_p95 = read_stat(stats, "timing_p95_ms")
        passed = bool(
            f1 is not None
            and timing_p95 is not None
            and f1 >= (
                self.config.zone_f1_gate
                #if self.stage == A4_ZONE_CONTROL
                if self.stage in SONG_GOAL_STAGES
                else self.current_timed_f1_gate)
            and 0.0 <= timing_p95 <= self.timing_tolerance_ms
        )
        #if not passed or self.stage != A4_ZONE_CONTROL:
        if not passed or self.stage not in SONG_GOAL_STAGES:
            return passed
        zone_rate = read_stat(stats, "zone_success_rate")
        if zone_rate is None or zone_rate < self.config.zone_success_gate:
            return False
        if self.stage != X0_MINI_STRUM:
            return True

        completion = read_stat(stats, "strum_completion_rate")
        traversal_recall = read_stat(stats, "strum_traversal_recall")
        order_accuracy = read_stat(stats, "strum_order_accuracy")
        direction_accuracy = read_stat(stats, "strum_direction_accuracy")
        protected_rate = read_stat(stats, "strum_protected_crossing_rate")
        if (completion is None or traversal_recall is None
                or order_accuracy is None or direction_accuracy is None
                or protected_rate is None):
            return False
        return bool(
            #zone_rate is not None
            #and zone_rate >= self.config.zone_success_gate)
            completion >= self.config.x0_completion_rate_gate
            and traversal_recall >= self.config.x0_traversal_recall_gate
            and order_accuracy >= self.config.x0_order_accuracy_gate
            and direction_accuracy >= self.config.x0_direction_accuracy_gate
            and protected_rate <= self.config.x0_max_protected_rate_gate)

    def _promote_stage(self):
        index = self.STAGES.index(self.stage)
        if index >= len(self.STAGES) - 1:
            return
        self._reset_terminal_evidence()
        self.stage = self.STAGES[index + 1]
        self.stage_iteration = 0
        self.stalled = False
        self.promotion_streak = 0
        self.timing_streak = 0
        self.complete = False
        if self.stage == A3_TIMED_CROSSING:
            self.timing_level = 0
        elif self.stage == A4_ZONE_CONTROL:
            self.timing_level = len(self.config.timing_tolerances_ms) - 1
            self.tempo_level = 0
        elif self.stage == X0_MINI_STRUM:
            self.timing_level = len(self.config.timing_tolerances_ms) - 1

    def after_iteration(self, stats: Mapping[str, object]):
        """Consume one iteration's statistics and update curriculum state."""
        self.total_iteration += 1
        self.stage_iteration += 1
        if self.complete:
            return self.state()

        if self.stage in TERMINAL_EVIDENCE_STAGES:
            has_evidence, evaluated_stats = (
                self._consume_terminal_evidence(stats))
        else:
            has_evidence, evaluated_stats = True, stats
        passed = (
            self._performance_passed(evaluated_stats)
            if has_evidence else False)
        minimum, maximum = self._limits()
        before_minimum_cap = max(self.config.promotion_windows - 1, 0)

        def next_streak(current):
            if not has_evidence:
                return current
            if not passed:
                return 0
            cap = (
                self.config.promotion_windows
                if self.stage_iteration >= minimum
                else before_minimum_cap)
            return min(current + 1, cap)

        if self.stage == A3_TIMED_CROSSING:
            self.promotion_streak = 0
            self.timing_streak = next_streak(self.timing_streak)
            if (self.stage_iteration >= minimum
                    and self.timing_streak >= self.config.promotion_windows):
                self.timing_streak = 0
                if self.timing_level < (
                        len(self.config.timing_tolerances_ms) - 1):
                    self.timing_level += 1
                    self.stalled = False
                else:
                    self._promote_stage()
        # elif self.stage != A4_ZONE_CONTROL:
        #     self.timing_streak = 0
        #     self.promotion_streak = next_streak(self.promotion_streak)
        #     if (self.stage_iteration >= minimum
        #             and self.promotion_streak >=
        #             self.config.promotion_windows):
        #         self._promote_stage()
        # else:
        elif self.stage == A4_ZONE_CONTROL:    
            self.timing_streak = 0
            self.promotion_streak = next_streak(self.promotion_streak)
            if (self.stage_iteration >= minimum
                    and self.promotion_streak
                    >= self.config.promotion_windows):
                self.promotion_streak = 0
                self._reset_terminal_evidence()
                if self.tempo_level < len(self.config.tempo_lambdas) - 1:
                    self.tempo_level += 1
                    self.stage_iteration = 0
                    self.stalled = False
                else:
                    # self.complete = True
                    # self.stalled = False
                    # Original tempo mastered at the final timing tolerance:
                    # advance into the multi-string extension curriculum
                    # (X0_MINI_STRUM) instead of terminating.
                    self._promote_stage()
        elif self.stage == X0_MINI_STRUM:
            self.timing_streak = 0
            self.promotion_streak = next_streak(self.promotion_streak)
            if (self.stage_iteration >= minimum
                    and self.promotion_streak
                    >= self.config.promotion_windows):
                self.promotion_streak = 0
                self.complete = True
                self.stalled = False
        else:
            self.timing_streak = 0
            self.promotion_streak = next_streak(self.promotion_streak)
            if (self.stage_iteration >= minimum
                    and self.promotion_streak >=
                    self.config.promotion_windows):
                self._promote_stage()

        if not self.complete and self.stage_iteration >= maximum:


            self.stalled = True
        return self.state()


__all__ = [
    "A0_PICK_GRIP",
    "A1_TIP_READY",
    "A2_FREE_CROSSING",
    "A3_TIMED_CROSSING",
    "A4_ZONE_CONTROL",
    "X0_MINI_STRUM",
    "STRIKE_STAGES",
    "StrikeCurriculumConfig",
    "StrikeCurriculum",
]
