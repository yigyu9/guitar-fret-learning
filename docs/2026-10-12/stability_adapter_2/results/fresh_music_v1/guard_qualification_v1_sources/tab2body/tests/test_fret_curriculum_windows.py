"""CPU checks for real-song chord and transition curriculum stages."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.goals import (
    FINGER_EVENT_TIME_SCALE_S,
    FretGoalSequence,
    fine_reach_action_scales,
    integrated_press_action_permissions,
)
from learning.curriculum import (
    FingertipApproachCurriculum,
    FingertipApproachCurriculumConfig,
)


def test_static_chord_timeout_enters_failed_chord_recovery():
    config = FingertipApproachCurriculumConfig(
        static_chord_min_iterations=1,
        static_chord_max_iterations=1,
        static_chord_recovery_max_cycles=2,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "static_chord"
    curriculum.chord_available_sets = ((1, 2), (1, 4))
    curriculum.chord_focus_count = 2
    stats = {
        "curriculum_chord_set_3_count": 1.0,
        "curriculum_chord_set_3_success": 0.9,
        "curriculum_chord_set_9_count": 1.0,
        "curriculum_chord_set_9_success": 0.0,
    }
    state = curriculum.after_iteration(stats)
    assert state["curriculum_stage"] == "chord_fine_reach"
    assert state["curriculum_static_chord_recovery"]
    assert state["curriculum_static_chord_recovery_signatures"] == [9]
    assert state["curriculum_chord_focus_index"] == 1

    curriculum.chord_focus_iteration = config.chord_fine_focus_max_iterations
    curriculum.after_iteration(stats)
    curriculum.chord_focus_iteration = config.chord_fine_max_iterations
    state = curriculum.after_iteration(stats)
    assert state["curriculum_stage"] == "static_chord"
    assert not state["curriculum_static_chord_recovery"]
    assert state["curriculum_static_chord_recovery_reason"] == "retest"


def _goal_file(directory):
    states = (
        ([1, 2, -1, -1, -1, -1], [1, 2, 0, 0, 0, 0]),
        ([1, 2, 3, -1, -1, -1], [1, 2, 3, 0, 0, 0]),
        ([1, 2, 3, 4, -1, -1], [1, 2, 3, 4, 0, 0]),
        ([2, 3, -1, -1, -1, -1], [1, 3, 0, 0, 0, 0]),
    )
    frames = []
    for frame_idx in range(240):
        fret, finger = states[frame_idx // 60]
        frames.append({
            "frame": frame_idx,
            "t": frame_idx / 60.0,
            "fret_goal": fret,
            "finger_goal": finger,
            "barre_goal": [False] * 6,
            "hand_anchor_fret": 2.5,
            "hand_allowed_fret_range": [1.0, 5.0],
        })
    path = Path(directory) / "goal.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def test_integrated_press_uses_pooled_evidence_and_weak_finger_recovery():
    config = FingertipApproachCurriculumConfig(
        integrated_press_min_iterations=1,
        integrated_press_max_iterations=2,
        integrated_recovery_max_iterations=2,
        early_min_evidence_episodes_per_finger=2,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "integrated_press"
    curriculum.required_song_fingers = (1, 2, 3, 4)

    weak_middle = {
        "episodes": 8,
        "curriculum_mean_position_quality": 0.8,
    }
    for finger in range(1, 5):
        weak_middle[f"curriculum_finger_{finger}_count"] = 0.25
        weak_middle[f"curriculum_finger_{finger}_success"] = (
            0.0 if finger == 2 else 0.25)
    curriculum.after_iteration(weak_middle)
    state = curriculum.after_iteration(weak_middle)
    assert state["curriculum_integrated_recovery"]
    assert state["curriculum_integrated_recovery_focus_finger"] == 2
    assert state["curriculum_integrated_recovery_count"] == 1
    assert state["curriculum_integrated_control_phase"] == 0
    assert not state["curriculum_stalled"]

    resumed = FingertipApproachCurriculum(config)
    resumed.load_context(state)
    assert resumed.integrated_recovery_active
    assert resumed.integrated_recovery_focus_finger == 2
    assert resumed.integrated_recovery_count == 1
    assert resumed.integrated_recovery_weights == (
        curriculum.integrated_recovery_weights)
    assert all(
        resumed.early_stage_evidence[finger]["target"] == 4
        for finger in range(1, 5))
    curriculum = resumed

    recovered = dict(weak_middle)
    for finger in range(1, 5):
        recovered[f"curriculum_finger_{finger}_success"] = 0.25
    for _ in range(8):
        state = curriculum.after_iteration(recovered)
        if state["curriculum_stage"] == "chord_reach":
            break
    assert state["curriculum_stage"] == "chord_reach"


def test_integrated_press_progressively_unlocks_proximal_actions():
    finger_ids = torch.tensor([0, 1, 2, 3, -1, -1, -1, -1])
    wrist = torch.tensor([False, False, False, False, True, False, False, False])
    elbow = torch.tensor([False, False, False, False, False, True, False, False])
    shoulder = torch.tensor([False, False, False, False, False, False, True, False])
    target = torch.tensor([2])
    phase0 = integrated_press_action_permissions(
        finger_ids, wrist, elbow, shoulder, target, 0)[0]
    assert phase0.tolist() == [True, False, True, False,
                               True, False, False, False]
    phase1 = integrated_press_action_permissions(
        finger_ids, wrist, elbow, shoulder, target, 1)[0]
    assert phase1[5] and not phase1[6] and not phase1[7]
    phase2 = integrated_press_action_permissions(
        finger_ids, wrist, elbow, shoulder, target, 2)[0]
    assert phase2[5] and phase2[6] and not phase2[7]
    phase3 = integrated_press_action_permissions(
        finger_ids, wrist, elbow, shoulder, target, 3)[0]
    assert phase3.all()


def test_early_promotion_ignores_iterations_without_diagnostic_evidence():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=20,
        early_min_evidence_episodes_per_finger=1,
        promotion_windows=2)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1,)
    evidence = {
        "episodes": 4,
        "curriculum_finger_1_success_episodes": 4,
        "curriculum_finger_1_target_episodes": 4,
        "curriculum_p90_target_distance": 0.005,
        "curriculum_cell_alignment_rate": 0.95,
    }
    curriculum.after_iteration(evidence)
    assert list(curriculum.recent) == [1.0]
    curriculum.after_iteration({})
    assert list(curriculum.recent) == [1.0]
    state = curriculum.after_iteration({
        "curriculum_p90_target_distance": 0.005,
        "curriculum_cell_alignment_rate": 0.95,
    })
    assert state["curriculum_stage"] == "isolated_press"


def test_early_evidence_keeps_only_the_recent_episode_window():
    config = FingertipApproachCurriculumConfig(
        early_min_evidence_episodes_per_finger=1,
        early_evidence_window_episodes_per_finger=4)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1,)
    curriculum.after_iteration({
        "episodes": 4,
        "curriculum_finger_1_target_episodes": 4,
        "curriculum_finger_1_success_episodes": 0,
    })
    state = curriculum.after_iteration({
        "episodes": 4,
        "curriculum_finger_1_target_episodes": 4,
        "curriculum_finger_1_success_episodes": 4,
    })
    assert state["curriculum_early_finger_1_episodes"] == 4
    assert state["curriculum_early_finger_1_success_rate"] == 1.0


def test_early_recovery_focus_is_latched_for_a_complete_block():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=1,
        early_min_evidence_episodes_per_finger=1,
        early_evidence_window_episodes_per_finger=100,
        early_recovery_focus_min_iterations=2,
        early_recovery_switch_margin=0.10,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2)

    def evidence(finger_1_success, finger_2_success):
        return {
            "episodes": 40,
            "curriculum_finger_1_target_episodes": 20,
            "curriculum_finger_1_success_episodes": finger_1_success,
            "curriculum_finger_2_target_episodes": 20,
            "curriculum_finger_2_success_episodes": finger_2_success,
            "curriculum_p90_target_distance": 0.020,
            "curriculum_cell_alignment_rate": 0.50,
        }

    state = curriculum.after_iteration(evidence(20, 0))
    assert state["curriculum_early_recovery_focus_finger"] == 2
    assert state["curriculum_early_recovery_focus_iteration"] == 0
    state = curriculum.after_iteration(evidence(0, 20))
    assert state["curriculum_early_recovery_focus_finger"] == 2
    assert state["curriculum_early_recovery_focus_iteration"] == 1
    state = curriculum.after_iteration(evidence(0, 20))
    assert state["curriculum_early_recovery_focus_finger"] == 1
    assert state["curriculum_early_recovery_focus_iteration"] == 0


def test_stalled_early_stage_focuses_weakest_finger_with_bounded_history():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=1,
        early_min_evidence_episodes_per_finger=2,
        early_evidence_window_episodes_per_finger=8,
        promotion_windows=2)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2, 3, 4)
    stats = {
        "episodes": 80,
        "curriculum_p90_target_distance": 0.020,
        "curriculum_cell_alignment_rate": 0.50,
    }
    for finger in range(1, 5):
        stats[f"curriculum_finger_{finger}_target_episodes"] = 20
        stats[f"curriculum_finger_{finger}_success_episodes"] = (
            0 if finger == 2 else 20)
    state = curriculum.after_iteration(stats)
    assert state["curriculum_stalled"]
    assert state["curriculum_early_recovery"]
    assert state["curriculum_early_recovery_focus_finger"] == 2
    assert state["curriculum_recent"] == []
    assert all(
        state[f"curriculum_early_finger_{finger}_episodes"] == 8
        for finger in range(1, 5))

    state["curriculum_recent"] = [0.0, 1.0]
    for row in state["curriculum_early_stage_evidence"].values():
        row["success"] *= 1000
        row["target"] *= 1000
    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    assert list(restored.recent) == []
    assert max(
        row["target"]
        for row in restored.early_stage_evidence.values()) == 8


def test_integrated_recovery_sampler_focuses_without_dropping_rehearsal():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 4096, device="cpu", seed=79)
        goals.set_curriculum_stage("integrated_press")
        goals.set_practice_focus_finger(2, focus_probability=0.75)
        goals.reset(torch.arange(goals.num_envs))
        active = goals.current()["finger"].amax(dim=1)
        focus_rate = (active == 2).float().mean()
        assert 0.70 < focus_rate < 0.80
        for finger in (1, 3, 4):
            assert (active == finger).any()


def test_recovery_sampler_preserves_quota_across_small_reset_batches():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 8, device="cpu", seed=83)
        goals.set_curriculum_stage("isolated_press")
        goals.set_practice_focus_finger(2, focus_probability=0.75)
        sizes = (1, 2, 1, 3, 1, 1, 2)
        total = 0
        while total < 4096:
            size = min(sizes[total % len(sizes)], 4096 - total)
            goals.reset(torch.arange(size))
            total += size
        diagnostics = goals.practice_sampler_diagnostics()
        assert diagnostics["practice_sampler_assignment_total"] == 4096
        assert diagnostics["practice_sampler_max_quota_error"] <= 1.0
        assert abs(
            diagnostics["practice_sampler_focus_actual_fraction"] - 0.75
        ) <= 0.01
        for finger in (1, 3, 4):
            assert abs(
                diagnostics[
                    f"practice_sampler_finger_{finger}_fraction"]
                - 1.0 / 12.0) <= 0.01
        assert diagnostics[
            "practice_sampler_singleton_reset_fraction"] > 0.0


def test_practice_sampler_setters_are_idempotent():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 8, device="cpu", seed=85)
        assert goals.set_practice_focus_finger(
            2, focus_probability=0.75)
        assert not goals.set_practice_focus_finger(
            2, focus_probability=0.75)
        assert goals.set_practice_finger_weights(None)
        assert goals.practice_focus_finger is None
        assert not goals.set_practice_finger_weights(None)


def test_adaptive_sampler_preserves_all_finger_weight_quotas():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 8, device="cpu", seed=87)
        goals.set_curriculum_stage("integrated_press")
        target = (0.34, 0.29, 0.22, 0.15)
        goals.set_practice_finger_weights(target)
        sizes = (1, 3, 2, 1, 4)
        total = 0
        while total < 4096:
            size = min(sizes[total % len(sizes)], 4096 - total)
            goals.reset(torch.arange(size))
            total += size
        diagnostics = goals.practice_sampler_diagnostics()
        assert diagnostics["practice_sampler_max_quota_error"] <= 1.0
        for finger, expected in enumerate(target, start=1):
            assert abs(diagnostics[
                f"practice_sampler_finger_{finger}_target_fraction"
            ] - expected) <= 1e-6
            assert abs(diagnostics[
                f"practice_sampler_finger_{finger}_fraction"
            ] - expected) <= 0.01


def test_recovery_sampler_checkpoint_restores_quota_and_rng():
    with tempfile.TemporaryDirectory() as directory:
        path = _goal_file(directory)
        source = FretGoalSequence(path, 8, device="cpu", seed=89)
        source.set_curriculum_stage("isolated_press")
        source.set_practice_finger_weights((0.34, 0.29, 0.22, 0.15))
        for size in (1, 2, 3, 1, 4, 2):
            source.reset(torch.arange(size))
        state = source.curriculum_sampler_state_dict()

        restored = FretGoalSequence(path, 8, device="cpu", seed=7)
        restored.set_curriculum_stage("isolated_press")
        restored.load_curriculum_sampler_state_dict(state)
        for size in (1, 1, 2, 5, 3):
            env_ids = torch.arange(size)
            source.reset(env_ids)
            restored.reset(env_ids)
            assert torch.equal(
                source.frame_idx[env_ids], restored.frame_idx[env_ids])
            assert torch.equal(
                source.practice_string[env_ids],
                restored.practice_string[env_ids])
        assert (source.practice_sampler_diagnostics()
                == restored.practice_sampler_diagnostics())


def test_integrated_recovery_adapts_weights_without_resetting_evidence():
    config = FingertipApproachCurriculumConfig(
        integrated_press_min_iterations=1,
        integrated_press_max_iterations=1,
        early_min_evidence_episodes_per_finger=10,
        early_evidence_window_episodes_per_finger=100,
        integrated_recovery_block_iterations=1,
        integrated_recovery_max_blocks=2,
        integrated_recovery_min_finger_probability=0.15,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "integrated_press"
    curriculum.required_song_fingers = (1, 2, 3, 4)

    def evidence(rates):
        stats = {
            "episodes": 400,
            "curriculum_mean_position_quality": 0.8,
        }
        for finger, rate in enumerate(rates, start=1):
            stats[f"curriculum_finger_{finger}_target_episodes"] = 100
            stats[f"curriculum_finger_{finger}_success_episodes"] = 100 * rate
        return stats

    state = curriculum.after_iteration(evidence((0.55, 0.65, 0.75, 0.95)))
    assert state["curriculum_integrated_recovery"]
    weights = [
        state[f"curriculum_integrated_recovery_finger_{finger}_weight"]
        for finger in range(1, 5)]
    assert min(weights) >= 0.15 - 1e-6
    assert weights[0] == max(weights)
    assert all(
        state[f"curriculum_early_finger_{finger}_episodes"] == 100
        for finger in range(1, 5))

    state = curriculum.after_iteration(evidence((0.55, 0.20, 0.75, 0.95)))
    weights = [
        state[f"curriculum_integrated_recovery_finger_{finger}_weight"]
        for finger in range(1, 5)]
    assert state["curriculum_integrated_recovery_block_count"] == 1
    assert state[
        "curriculum_integrated_recovery_last_update_reason"] == (
            "retention_drop")
    assert weights[1] == max(weights)
    assert all(
        state[f"curriculum_early_finger_{finger}_episodes"] == 100
        for finger in range(1, 5))

    recovery_count = state["curriculum_integrated_recovery_count"]
    state = curriculum.after_iteration(evidence((0.55, 0.20, 0.75, 0.95)))
    assert state["curriculum_integrated_recovery_exhausted"]
    assert state["curriculum_stalled"]
    assert all(abs(state[
        f"curriculum_integrated_recovery_finger_{finger}_weight"
    ] - 0.25) <= 1e-6 for finger in range(1, 5))
    state = curriculum.after_iteration(evidence((0.55, 0.20, 0.75, 0.95)))
    assert state["curriculum_integrated_recovery_count"] == recovery_count


def test_integrated_weight_update_does_not_force_global_reset():
    class Goals:
        practice_available_fingers = (0, 1, 2, 3)
        practice_goal_pair_available_incoming_fingers = ()

        def set_chord_focus_index(self, index, focus_probability=1.0):
            return False

        def set_practice_finger_weights(self, weights):
            self.weights = tuple(weights) if weights is not None else None
            return True

        def set_practice_focus_finger(self, finger, focus_probability=1.0):
            raise AssertionError("adaptive recovery must not use single focus")

        def set_random_start_probability(self, probability):
            self.random_start_probability = probability

    class Env:
        def __init__(self):
            self.goals = Goals()
            self.reset_count = 0

        def set_integrated_press_control(self, phase, recovery=False,
                                         focus_finger=0):
            self.recovery = recovery

        def set_fine_reach_control(self, iteration, recovery=False):
            pass

        def set_curriculum_stage(self, stage, duration_frames=None,
                                 reset=False):
            return None

        def reset(self):
            self.reset_count += 1
            return None

    curriculum = FingertipApproachCurriculum()
    curriculum.stage = "integrated_press"
    curriculum.integrated_recovery_active = True
    curriculum.integrated_recovery_weights = (0.34, 0.29, 0.22, 0.15)
    env = Env()
    curriculum.apply(env)
    assert env.goals.weights == curriculum.integrated_recovery_weights
    assert env.reset_count == 0


def test_repeated_early_focus_application_resets_only_once():
    class Goals:
        practice_available_fingers = (0, 1, 2, 3)
        practice_goal_pair_available_incoming_fingers = ()

        def __init__(self):
            self.focus = None
            self.probability = 1.0
            self.weights = None

        def set_chord_focus_index(self, index, focus_probability=1.0):
            return False

        def set_practice_finger_weights(self, weights):
            normalized = tuple(weights) if weights is not None else None
            changed = (
                normalized != self.weights
                or (normalized is None
                    and (self.focus is not None
                         or self.probability != 1.0)))
            if not changed:
                return False
            self.weights = normalized
            if normalized is None:
                self.focus = None
                self.probability = 1.0
            return True

        def set_practice_focus_finger(self, finger, focus_probability=1.0):
            changed = (
                finger != self.focus
                or focus_probability != self.probability
                or self.weights is not None)
            self.focus = finger
            self.probability = focus_probability
            self.weights = None
            return changed

        def set_random_start_probability(self, probability):
            pass

    class Env:
        def __init__(self):
            self.goals = Goals()
            self.reset_count = 0

        def set_integrated_press_control(self, *args, **kwargs):
            pass

        def set_fine_reach_control(self, *args, **kwargs):
            pass

        def set_curriculum_stage(self, *args, **kwargs):
            return None

        def reset(self):
            self.reset_count += 1
            return None

    curriculum = FingertipApproachCurriculum()
    curriculum.stage = "fine_reach"
    curriculum.stalled = True
    curriculum.early_recovery_focus_finger = 2
    env = Env()
    curriculum.apply(env)
    assert env.reset_count == 1
    curriculum.apply(env)
    assert env.reset_count == 1
    assert env.goals.focus == 2
    assert env.goals.weights is None
    assert curriculum.practice_focus_reset_count == 1
    assert curriculum.practice_focus_reset_consecutive == 0


def test_adaptive_to_single_focus_transition_resets_once():
    config = FingertipApproachCurriculumConfig(
        practice_reset_watchdog_iterations=3)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "integrated_press"
    curriculum.integrated_recovery_active = True
    curriculum.integrated_recovery_weights = (0.34, 0.29, 0.22, 0.15)

    class Goals:
        practice_available_fingers = (0, 1, 2, 3)
        practice_goal_pair_available_incoming_fingers = ()

        def __init__(self):
            self.focus = None
            self.probability = 1.0
            self.weights = None

        def set_chord_focus_index(self, *args, **kwargs):
            return False

        def set_practice_finger_weights(self, weights):
            normalized = tuple(weights)
            changed = normalized != self.weights
            self.weights = normalized
            self.focus = max(range(4), key=normalized.__getitem__) + 1
            self.probability = max(normalized)
            return changed

        def set_practice_focus_finger(self, finger, focus_probability=1.0):
            changed = (
                finger != self.focus
                or focus_probability != self.probability
                or self.weights is not None)
            self.focus = finger
            self.probability = focus_probability
            self.weights = None
            return changed

        def set_random_start_probability(self, probability):
            pass

    class Env:
        def __init__(self):
            self.goals = Goals()
            self.reset_count = 0

        def set_integrated_press_control(self, *args, **kwargs):
            pass

        def set_fine_reach_control(self, *args, **kwargs):
            pass

        def set_curriculum_stage(self, *args, **kwargs):
            return None

        def reset(self):
            self.reset_count += 1
            return None

    env = Env()
    curriculum.apply(env)
    assert env.reset_count == 0
    curriculum.stage = "fine_reach"
    curriculum.stalled = True
    curriculum.early_recovery_focus_finger = 2
    curriculum.apply(env)
    assert env.reset_count == 1
    curriculum.apply(env)
    assert env.reset_count == 1


def test_repeated_practice_reset_watchdog_fails_closed():
    config = FingertipApproachCurriculumConfig(
        practice_reset_watchdog_iterations=3)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.stalled = True
    curriculum.early_recovery_focus_finger = 2

    class Goals:
        practice_available_fingers = (0, 1, 2, 3)
        practice_goal_pair_available_incoming_fingers = ()

        def set_chord_focus_index(self, *args, **kwargs):
            return False

        def set_practice_focus_finger(self, *args, **kwargs):
            return True

        def set_random_start_probability(self, probability):
            pass

    class Env:
        def __init__(self):
            self.goals = Goals()

        def set_integrated_press_control(self, *args, **kwargs):
            pass

        def set_fine_reach_control(self, *args, **kwargs):
            pass

        def set_curriculum_stage(self, *args, **kwargs):
            return None

        def reset(self):
            return None

    env = Env()
    curriculum.apply(env)
    curriculum.apply(env)
    try:
        curriculum.apply(env)
    except RuntimeError as exc:
        assert "consecutive training iterations" in str(exc)
    else:
        raise AssertionError("repeated full reset watchdog did not fire")


def test_early_recovery_has_a_total_block_limit():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=1,
        early_min_evidence_episodes_per_finger=1,
        early_recovery_focus_min_iterations=1,
        early_recovery_max_total_blocks=3,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.stalled = True
    curriculum.early_recovery_focus_finger = 2
    stats = {"episodes": 4, "curriculum_mean_position_quality": 0.8}
    for finger in range(1, 5):
        stats[f"curriculum_finger_{finger}_target_episodes"] = 1
        stats[f"curriculum_finger_{finger}_success_episodes"] = (
            0 if finger == 2 else 1)
    for _ in range(3):
        state = curriculum.after_iteration(stats)
    assert state["curriculum_early_recovery_exhausted"]
    assert state["curriculum_early_recovery_total_blocks"] == 3
    assert state["curriculum_early_recovery_focus_finger"] == 0
    assert state["curriculum_early_recovery_last_switch_reason"] == (
        "max_total_blocks")
    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    assert restored.early_recovery_exhausted
    assert restored.early_recovery_total_blocks == 3
    assert restored.early_recovery_focus_finger == 0
    curriculum.after_iteration(stats)
    assert curriculum.early_recovery_total_blocks == 3


def test_isolated_recovery_uses_balanced_adaptive_finger_weights():
    config = FingertipApproachCurriculumConfig(
        isolated_press_min_iterations=1,
        isolated_press_max_iterations=1,
        early_min_evidence_episodes_per_finger=1,
        early_evidence_window_episodes_per_finger=100,
        early_recovery_focus_min_iterations=1,
        early_recovery_max_total_blocks=3,
        early_recovery_min_finger_probability=0.15,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "isolated_press"
    curriculum.required_song_fingers = (1, 2, 3, 4)
    stats = {
        "episodes": 40,
        "curriculum_mean_position_quality": 0.8,
        "curriculum_mean_arch_quality": 0.9,
    }
    rates = (0.9, 0.85, 0.2, 0.9)
    for finger, rate in enumerate(rates, start=1):
        stats[f"curriculum_finger_{finger}_target_episodes"] = 10
        stats[f"curriculum_finger_{finger}_success_episodes"] = 10 * rate

    state = curriculum.after_iteration(stats)
    weights = state["curriculum_early_recovery_weights"]
    assert state["curriculum_early_bottleneck_finger"] == 3
    assert abs(state["curriculum_early_min_success_rate"] - 0.2) < 1e-6
    assert state["curriculum_early_recovery"]
    assert state["curriculum_early_recovery_focus_finger"] == 3
    assert abs(sum(weights) - 1.0) < 1e-6
    assert all(weight >= 0.15 for weight in weights)
    assert weights[2] == max(weights)

    state = curriculum.after_iteration(stats)
    assert state["curriculum_early_recovery_total_blocks"] == 1
    assert state["curriculum_early_recovery_focus_iteration"] == 0
    assert state["curriculum_early_recovery_last_switch_reason"].startswith(
        "adaptive_")
    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    assert restored.early_recovery_weights == tuple(
        state["curriculum_early_recovery_weights"])

    state = curriculum.after_iteration(stats)
    state = curriculum.after_iteration(stats)
    exhausted_weights = state["curriculum_early_recovery_weights"]
    assert state["curriculum_early_recovery_exhausted"]
    assert state["curriculum_early_recovery_consolidation"]
    assert exhausted_weights[2] == max(exhausted_weights)
    assert exhausted_weights != (0.25, 0.25, 0.25, 0.25)
    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    assert restored.early_recovery_weights == tuple(exhausted_weights)


def test_isolated_adaptive_recovery_applies_weights_without_single_focus():
    class Goals:
        practice_available_fingers = (0, 1, 2, 3)
        practice_goal_pair_available_incoming_fingers = ()

        def __init__(self):
            self.weights = None

        def set_chord_focus_index(self, *args, **kwargs):
            return False

        def set_practice_finger_weights(self, weights):
            self.weights = tuple(weights)
            return True

        def set_practice_focus_finger(self, *args, **kwargs):
            raise AssertionError(
                "isolated adaptive recovery must not use single focus")

        def set_random_start_probability(self, _probability):
            pass

    class Env:
        def __init__(self):
            self.goals = Goals()
            self.reset_count = 0

        def set_integrated_press_control(self, *args, **kwargs):
            pass

        def set_fine_reach_control(self, *args, **kwargs):
            pass

        def set_curriculum_stage(self, *args, **kwargs):
            return None

        def reset(self):
            self.reset_count += 1
            return None

    curriculum = FingertipApproachCurriculum()
    curriculum.stage = "isolated_press"
    curriculum.stalled = True
    curriculum.early_recovery_exhausted = True
    curriculum.early_recovery_focus_finger = 3
    curriculum.early_recovery_weights = (0.15, 0.15, 0.55, 0.15)
    env = Env()
    curriculum.apply(env)
    curriculum.apply(env)
    assert env.goals.weights == curriculum.early_recovery_weights
    assert env.reset_count == 0


def test_early_evidence_age_detects_and_recovers_from_starvation():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=200,
        fine_max_iterations=300,
        early_min_evidence_episodes_per_finger=1,
        early_evidence_stall_iterations=3,
        early_evidence_recent_iterations=5,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2)
    evidence = {
        "episodes": 2,
        "curriculum_mean_position_quality": 0.8,
        "curriculum_finger_1_target_episodes": 1,
        "curriculum_finger_1_success_episodes": 1,
        "curriculum_finger_2_target_episodes": 1,
        "curriculum_finger_2_success_episodes": 1,
    }
    state = curriculum.after_iteration(evidence)
    assert not state["curriculum_early_evidence_stalled"]
    for _ in range(3):
        state = curriculum.after_iteration({})
    assert state["curriculum_early_evidence_stalled"]
    assert state["curriculum_early_evidence_starved_fingers"] == [1, 2]
    assert not curriculum._has_minimum_stage_evidence({})
    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    restored.required_song_fingers = (1, 2)
    assert restored._early_evidence_starved_fingers() == (1, 2)
    state = curriculum.after_iteration(evidence)
    assert not state["curriculum_early_evidence_stalled"]
    assert state["curriculum_early_finger_1_recent_episodes"] == 2
    assert state["curriculum_early_finger_2_recent_episodes"] == 2


def test_early_recovery_switches_for_retention_before_block_rotation():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=1,
        early_min_evidence_episodes_per_finger=1,
        early_evidence_window_episodes_per_finger=10,
        early_recovery_focus_min_iterations=1,
        early_recovery_max_focus_blocks=10,
        early_recovery_retention_drop_tolerance=0.05,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2, 3)

    def evidence(rates):
        stats = {
            "episodes": 30,
            "curriculum_p90_target_distance": 0.020,
            "curriculum_cell_alignment_rate": 0.50,
        }
        for finger, rate in enumerate(rates, start=1):
            stats[f"curriculum_finger_{finger}_target_episodes"] = 10
            stats[f"curriculum_finger_{finger}_success_episodes"] = 10 * rate
        return stats

    state = curriculum.after_iteration(evidence((0.9, 0.2, 0.8)))
    assert state["curriculum_early_recovery_focus_finger"] == 2
    state = curriculum.after_iteration(evidence((0.4, 0.4, 0.8)))
    assert state["curriculum_early_recovery_focus_finger"] == 1
    assert state[
        "curriculum_early_recovery_last_switch_reason"] == "retention_drop"


def test_early_recovery_rotates_after_maximum_focus_blocks():
    config = FingertipApproachCurriculumConfig(
        fine_min_iterations=1,
        fine_max_iterations=1,
        early_min_evidence_episodes_per_finger=1,
        early_evidence_window_episodes_per_finger=10,
        early_recovery_focus_min_iterations=1,
        early_recovery_max_focus_blocks=1,
        early_recovery_retention_drop_tolerance=1.0,
        early_recovery_switch_margin=1.0,
        promotion_windows=1)
    curriculum = FingertipApproachCurriculum(config)
    curriculum.stage = "fine_reach"
    curriculum.required_song_fingers = (1, 2, 3)
    stats = {
        "episodes": 30,
        "curriculum_p90_target_distance": 0.020,
        "curriculum_cell_alignment_rate": 0.50,
        "curriculum_finger_1_target_episodes": 10,
        "curriculum_finger_1_success_episodes": 5,
        "curriculum_finger_2_target_episodes": 10,
        "curriculum_finger_2_success_episodes": 1,
        "curriculum_finger_3_target_episodes": 10,
        "curriculum_finger_3_success_episodes": 9,
    }
    state = curriculum.after_iteration(stats)
    assert state["curriculum_early_recovery_focus_finger"] == 2
    state = curriculum.after_iteration(stats)
    assert state["curriculum_early_recovery_focus_finger"] == 1
    assert state[
        "curriculum_early_recovery_last_switch_reason"] == "block_limit"


def test_early_recovery_block_state_survives_checkpoint_context():
    config = FingertipApproachCurriculumConfig()
    source = FingertipApproachCurriculum(config)
    source.stage = "isolated_press"
    source.stalled = True
    source.required_song_fingers = (1, 2, 3, 4)
    source.early_recovery_focus_finger = 2
    source.early_recovery_focus_iteration = 123
    source.early_recovery_focus_blocks = 1
    source.early_recovery_total_blocks = 3
    source.early_recovery_count = 4
    source.early_recovery_best_rates = {
        1: 0.70, 2: 0.45, 3: 0.85, 4: 0.80}
    source.early_recovery_last_switch_reason = "retention_drop"
    source.early_recovery_retention_max_drop = 0.07
    state = source.state()

    restored = FingertipApproachCurriculum(config)
    restored.load_context(state)
    assert restored.early_recovery_focus_finger == 2
    assert restored.early_recovery_focus_iteration == 123
    assert restored.early_recovery_focus_blocks == 1
    assert restored.early_recovery_total_blocks == 3
    assert restored.early_recovery_count == 4
    assert restored.early_recovery_best_rates == source.early_recovery_best_rates
    assert restored.early_recovery_last_switch_reason == "retention_drop"
    assert restored.early_recovery_retention_max_drop == 0.07


def test_fine_reach_action_scales_use_warmup_ramp_and_recovery_assist():
    finger_ids = torch.tensor([0, 1, 2, 3, -1, -1, -1])
    wrist = torch.tensor([False, False, False, False, True, False, False])
    elbow = torch.tensor([False, False, False, False, False, True, False])
    shoulder = torch.tensor([False, False, False, False, False, False, True])
    target = torch.tensor([2])
    warm = fine_reach_action_scales(
        finger_ids, wrist, elbow, shoulder, target, 200)
    assert warm[0].tolist() == [1.0] * 7
    precise = fine_reach_action_scales(
        finger_ids, wrist, elbow, shoulder, target, 500)
    assert torch.allclose(
        precise[0], torch.tensor([1.0, 0.15, 1.0, 0.15,
                                  1.0, 1.0, 0.15]))
    recovery = fine_reach_action_scales(
        finger_ids, wrist, elbow, shoulder, target, 500,
        recovery=True)
    assert torch.allclose(recovery[0, 6:], torch.tensor([0.35]))


def _single_transition_goal_file(directory):
    frames = []
    for frame_idx in range(300):
        fret = 4 if frame_idx < 150 else 6
        frames.append({
            "frame": frame_idx,
            "t": frame_idx / 60.0,
            "fret_goal": [fret, -1, -1, -1, -1, -1],
            "finger_goal": [1, 0, 0, 0, 0, 0],
            "barre_goal": [False] * 6,
            "hand_anchor_fret": 5.0,
            "hand_allowed_fret_range": [3.0, 7.0],
        })
    path = Path(directory) / "single_transition.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _transient_chord_goal_file(directory):
    states = (
        ([4, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], 12),
        ([4, 7, 0, 0, 0, 0], [1, 4, 0, 0, 0, 0], 2),
        ([0, 7, 0, 0, 0, 0], [0, 4, 0, 0, 0, 0], 16),
    )
    frames = []
    for fret, finger, duration in states:
        for _ in range(duration):
            frame_idx = len(frames)
            frames.append({
                "frame": frame_idx,
                "t": frame_idx / 60.0,
                "fret_goal": fret,
                "finger_goal": finger,
                "barre_goal": [False] * 6,
                "hand_anchor_fret": 5.5,
                "hand_allowed_fret_range": [3.0, 8.0],
            })
    path = Path(directory) / "transient_chord.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _duration_weighted_chord_goal_file(directory):
    states = (
        ([4, 5, 0, 0, 0, 0], [1, 2, 0, 0, 0, 0], 12),
        ([6, 7, 0, 0, 0, 0], [1, 2, 0, 0, 0, 0], 48),
    )
    frames = []
    for fret, finger, duration in states:
        for _ in range(duration):
            frame_idx = len(frames)
            frames.append({
                "frame": frame_idx,
                "t": frame_idx / 60.0,
                "fret_goal": fret,
                "finger_goal": finger,
                "barre_goal": [False] * 6,
                "hand_anchor_fret": 5.5,
                "hand_allowed_fret_range": [3.0, 8.0],
            })
    path = Path(directory) / "duration_weighted_chord.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _bridge_goal_file(directory):
    states = (
        ([0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]),
        ([4, -1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]),
        ([4, 4, -1, 0, 0, 0], [1, 2, 0, 0, 0, 0]),
        ([-1, 4, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0]),
        ([6, -1, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0]),
        ([0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]),
    )
    frames = []
    for frame_idx in range(72):
        fret, finger = states[frame_idx // 12]
        frames.append({
            "frame": frame_idx,
            "t": frame_idx / 60.0,
            "fret_goal": fret,
            "finger_goal": finger,
            "barre_goal": [False] * 6,
            "hand_anchor_fret": 4.5,
            "hand_allowed_fret_range": [1.0, 8.0],
        })
    path = Path(directory) / "bridge_goal.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _song_stats(passed):
    if passed:
        stats = {
            "episodes": 1,
            "f1_l": 0.96,
            "no_press_accuracy": 0.995,
            "no_press_correct_count": 99.5,
            "no_press_evidence_count": 100.0,
            "wrong_press_rate": 0.005,
            "sustain_hold_rate": 0.96,
            "sustain_event_success_rate": 0.95,
            "sustain_max_dropout_frames": 2.0,
            "sustain_event_count": 2.0,
            "press_dropout_rate": 0.02,
            "failure_termination": 0.0,
            "nonfinite": 0.0,
            "velocity_blowup": 0.0,
        }
    else:
        stats = {
            "episodes": 1,
            "f1_l": 0.20,
            "no_press_accuracy": 0.80,
            "no_press_correct_count": 80.0,
            "no_press_evidence_count": 100.0,
            "wrong_press_rate": 0.20,
            "sustain_hold_rate": 0.30,
            "sustain_event_success_rate": 0.20,
            "sustain_max_dropout_frames": 20.0,
            "sustain_event_count": 2.0,
            "press_dropout_rate": 0.20,
            "failure_termination": 0.20,
            "nonfinite": 0.0,
            "velocity_blowup": 0.0,
        }
    rate = 0.95 if passed else 0.20
    for finger in range(1, 5):
        stats[f"press_finger_{finger}_success"] = 10.0 * rate
        stats[f"press_finger_{finger}_count"] = 10.0
        stats[f"curriculum_finger_{finger}_target_active_count"] = 10.0
        stats[f"curriculum_finger_{finger}_target_distance"] = (
            0.005 if passed else 0.040)
        stats[f"finger_{finger}_target_distance_active_frames"] = 10.0
        stats[f"finger_{finger}_target_distance_sum"] = (
            0.05 if passed else 0.40)
        full_song = (
            f"curriculum_goal_pair_full_song_finger_{finger}")
        stats[f"{full_song}_target_active_count"] = 256.0
        stats[f"{full_song}_press_success"] = rate
        stats[f"{full_song}_target_distance"] = (
            0.006 if passed else 0.040)
        stats[f"{full_song}_hold_quality"] = rate
        stats[f"{full_song}_dropout_rate"] = (
            0.02 if passed else 0.20)
    return stats


def _frozen_stats(stats):
    return {
        **stats,
        "_frozen_train": dict(stats),
        "_frozen_eval": dict(stats),
    }


def _static_chord_stats(passed):
    stats = _song_stats(passed)
    stats.update({
        "chord_ready_rate": 0.95 if passed else 0.30,
        "chord_hold_quality": 0.95 if passed else 0.30,
        "curriculum_success_rate": 0.95 if passed else 0.30,
        "curriculum_mean_position_quality": 0.80 if passed else 0.20,
        "press_dropout_rate": 0.02 if passed else 0.20,
        "press_max_dropout_frames": 2.0 if passed else 20.0,
    })
    return stats


def _soft_bridge_stats():
    stats = _song_stats(True)
    stats.update({
        "f1_l": 0.94,
        "no_press_accuracy": 0.91,
        "no_press_correct_count": 91.0,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.045,
        "sustain_hold_rate": 0.93,
        "sustain_event_success_rate": 0.80,
        "press_dropout_rate": 0.05,
        "failure_termination": 0.025,
    })
    for finger in range(1, 5):
        stats[f"press_finger_{finger}_success"] = 8.8
    return stats


def _goal_pair_stats():
    stats = _song_stats(True)
    stats.update({
        "curriculum_goal_pair_pretransition_current_press_preserved": 0.95,
        "curriculum_goal_pair_pretransition_current_press_preserved_count":
            10.0,
        "curriculum_goal_pair_sequence_active_count": 2048.0,
        "curriculum_goal_pair_sequence_press_success": 0.90,
        "curriculum_goal_pair_sequence_no_press_success": 0.95,
        "curriculum_goal_pair_sequence_wrong_press": 0.01,
        "curriculum_goal_pair_sequence_penetration": 0.0,
        "curriculum_goal_pair_sequence_thumb_support": 0.80,
    })
    for finger in range(1, 5):
        rehearsal = (
            f"curriculum_goal_pair_rehearsal_finger_{finger}")
        stats[f"{rehearsal}_target_active_count"] = 10.0
        stats[f"{rehearsal}_press_success"] = 0.90
        stats[f"{rehearsal}_target_distance"] = 0.005
        transition = (
            f"curriculum_goal_pair_transition_finger_{finger}")
        stats[f"{transition}_target_active_count"] = 10.0
        stats[f"{transition}_press_success"] = 0.90
        stats[f"{transition}_next_active_count"] = 10.0
        stats[f"{transition}_next_distance"] = 0.015
        stats[f"{transition}_next_progress"] = 0.001
    return stats


def main():
    test_static_chord_timeout_enters_failed_chord_recovery()
    test_integrated_press_uses_pooled_evidence_and_weak_finger_recovery()
    test_integrated_press_progressively_unlocks_proximal_actions()
    test_integrated_recovery_sampler_focuses_without_dropping_rehearsal()
    test_recovery_sampler_preserves_quota_across_small_reset_batches()
    test_practice_sampler_setters_are_idempotent()
    test_adaptive_sampler_preserves_all_finger_weight_quotas()
    test_recovery_sampler_checkpoint_restores_quota_and_rng()
    test_integrated_recovery_adapts_weights_without_resetting_evidence()
    test_integrated_weight_update_does_not_force_global_reset()
    test_repeated_early_focus_application_resets_only_once()
    test_adaptive_to_single_focus_transition_resets_once()
    test_repeated_practice_reset_watchdog_fails_closed()
    test_early_recovery_has_a_total_block_limit()
    test_isolated_recovery_uses_balanced_adaptive_finger_weights()
    test_isolated_adaptive_recovery_applies_weights_without_single_focus()
    test_early_evidence_age_detects_and_recovers_from_starvation()
    test_early_promotion_ignores_iterations_without_diagnostic_evidence()
    test_early_evidence_keeps_only_the_recent_episode_window()
    test_early_recovery_focus_is_latched_for_a_complete_block()
    test_early_recovery_switches_for_retention_before_block_rotation()
    test_early_recovery_rotates_after_maximum_focus_blocks()
    test_early_recovery_block_state_survives_checkpoint_context()
    test_stalled_early_stage_focuses_weakest_finger_with_bounded_history()
    test_fine_reach_action_scales_use_warmup_ramp_and_recovery_assist()
    for stage in (
            "static_chord", "frozen_context", "goal_pair",
            "transition_window",
            "coverage", "integration", "full_song"):
        assert FingertipApproachCurriculum.migrate_stage(
            stage, source_schema=1) == "chord_reach"
    for stage in (
            "static_chord", "frozen_context", "goal_pair",
            "transition_window",
            "coverage", "integration", "full_song"):
        assert FingertipApproachCurriculum.migrate_stage(
            stage, source_schema=2) == "chord_fine_reach"
    assert FingertipApproachCurriculum.migrate_stage(
        "static_chord", source_schema=3) == "static_chord"
    assert FingertipApproachCurriculum.migrate_stage(
        "frozen_context", source_schema=3) == "frozen_context"
    for stage in (
            "goal_pair", "transition_window",
            "coverage", "integration", "full_song"):
        assert FingertipApproachCurriculum.migrate_stage(
            stage, source_schema=3) == "frozen_context"
    assert FingertipApproachCurriculum.migrate_stage(
        "static_chord", source_schema=4) == "static_chord"
    for stage in (
            "frozen_context", "goal_pair", "transition_window",
            "coverage", "integration", "full_song"):
        assert FingertipApproachCurriculum.migrate_stage(
            stage, source_schema=4) == "frozen_context"
    frozen_migration_stages = {
        "frozen_context", "goal_pair", "transition_window",
        "coverage", "integration", "full_song",
    }
    for source_schema in (5, 6, 7):
        for stage in FingertipApproachCurriculum.STAGES:
            expected = (
                "frozen_context"
                if stage in frozen_migration_stages else stage)
            assert FingertipApproachCurriculum.migrate_stage(
                stage, source_schema=source_schema) == expected

    with tempfile.TemporaryDirectory() as directory:
        transient = FretGoalSequence(
            _transient_chord_goal_file(directory), 32,
            device="cpu", seed=5)
        assert transient.static_chord_min_duration_frames == 12
        assert not transient.practice_available_chord_finger_sets
        assert transient.practice_transient_chord_finger_sets == ((1, 4),)
        assert transient.practice_transient_chord_run_count == 1
        assert 12 in transient.practice_transition_frames.tolist()
        assert 12 not in transient.practice_frozen_context_frames.tolist()
        assert 13 not in transient.practice_frozen_context_frames.tolist()

        skip = FingertipApproachCurriculum()
        skip.stage = "chord_reach"
        skip._bind_chord_catalog(transient)
        skip._skip_unavailable_chord_stages()
        assert skip.stage == "frozen_context"
        assert skip.skipped_stages == [
            "chord_reach", "chord_fine_reach", "static_chord"]

        weighted = FretGoalSequence(
            _duration_weighted_chord_goal_file(directory), 4000,
            device="cpu", seed=17)
        assert weighted.practice_available_chord_finger_sets == ((1, 2),)
        assert weighted.practice_static_chord_run_count == 2
        weighted.set_curriculum_stage("static_chord", duration_frames=150)
        weighted.reset(torch.arange(weighted.num_envs))
        short_pose_rate = (weighted.current()["fret"][:, 0] == 4).float().mean()
        assert 0.17 < short_pose_rate < 0.23, short_pose_rate

        goals = FretGoalSequence(
            _goal_file(directory), 3000, device="cpu", seed=7)
        ids = torch.arange(goals.num_envs)

        for stage in ("chord_reach", "chord_fine_reach"):
            goals.set_curriculum_stage(stage, duration_frames=180)
            goals.reset(ids)
            current = goals.current()
            active_fingers = torch.stack([
                ((current["finger"] == finger)
                 & (current["fret"] > 0)).any(dim=1)
                for finger in range(1, 5)
            ], dim=1)
            assert (active_fingers.sum(dim=1) >= 2).all()
            assert torch.equal(
                current["finger_event"][..., 10] > 0.5,
                active_fingers)

        for focus_index, finger_set in enumerate(
                goals.practice_available_chord_finger_sets):
            goals.set_chord_focus_index(focus_index)
            goals.set_curriculum_stage(
                "chord_fine_reach", duration_frames=180)
            goals.reset(ids)
            current = goals.current()
            sampled = torch.stack([
                ((current["finger"] == finger)
                 & (current["fret"] > 0)).any(dim=1)
                for finger in range(1, 5)
            ], dim=1)
            expected = torch.tensor(
                [finger in finger_set for finger in range(1, 5)])
            assert torch.equal(
                sampled, expected[None].expand_as(sampled))
        goals.set_chord_focus_index(0, focus_probability=0.95)
        goals.reset(ids)
        current = goals.current()
        sampled_signature = sum(
            (1 << (finger - 1))
            * (((current["finger"] == finger)
                & (current["fret"] > 0)).any(dim=1)).long()
            for finger in range(1, 5))
        focus_signature = sum(
            1 << (finger - 1)
            for finger in goals.practice_available_chord_finger_sets[0])
        focus_rate = (
            sampled_signature == focus_signature).float().mean()
        assert 0.93 < focus_rate < 0.97
        assert (sampled_signature != focus_signature).any()
        goals.set_chord_focus_index(None)
        try:
            goals.set_chord_focus_index(
                len(goals.practice_available_chord_finger_sets))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid chord focus index was accepted")

        goals.set_curriculum_stage("static_chord", duration_frames=150)
        goals.reset(ids)
        current = goals.current()
        active_finger = torch.stack([
            ((current["finger"] == finger) & (current["fret"] > 0)).any(dim=1)
            for finger in range(1, 5)
        ], dim=1)
        signatures = active_finger.long() * torch.tensor([1, 2, 4, 8])
        signature_counts = torch.bincount(
            signatures.sum(dim=1), minlength=16)
        expected_signatures = torch.tensor([3, 5, 7, 15])
        counts = signature_counts[expected_signatures]
        assert torch.all((counts.float() - 750.0).abs() < 100.0), counts
        active_strings = current["fret"] > 0
        assert torch.equal(current["sustain_eligible"], active_strings)
        assert torch.all(
            current["sustain_event_id"][active_strings] >= 0)
        assert torch.equal(
            current["finger_event"][..., 10] > 0.5, active_finger)
        assert not (current["finger_event"][..., 11] > 0.5).any()
        event_offset = len(goals.lookahead) * goals.per_lookahead_dim
        observed_static = goals.observe()[
            :, event_offset:event_offset + goals.finger_event_dim].reshape(
                goals.num_envs, 4, -1)
        assert torch.equal(observed_static, current["finger_event"])
        assert torch.equal(
            goals.practice_remaining, torch.full((3000,), 150))
        frozen = goals.frame_idx.clone()
        goals.advance(torch.ones(3000, dtype=torch.bool))
        assert torch.equal(goals.frame_idx, frozen)
        assert torch.equal(
            goals.practice_remaining, torch.full((3000,), 149))

        goals.set_transition_max_changes(2)
        goals.set_curriculum_stage("transition_window", duration_frames=180)
        goals.reset(ids)
        start = goals.frame_idx.clone()
        duration = goals.practice_remaining.clone()
        assert int(duration.min()) >= 60
        assert int(duration.max()) <= 180
        assert int(goals.practice_transition_count.max()) <= 2
        observed = goals.observe()[
            :, event_offset:event_offset + goals.finger_event_dim].reshape(
                goals.num_envs, 4, -1)
        assert torch.allclose(observed, goals.finger_events[start])
        goals.advance(torch.ones(3000, dtype=torch.bool))
        assert torch.equal(goals.frame_idx, start + 1)
        assert torch.equal(goals.practice_remaining, duration - 1)

        bridge = FretGoalSequence(
            _bridge_goal_file(directory), 4096, device="cpu", seed=19)
        bridge_ids = torch.arange(bridge.num_envs)
        bridge_event_offset = (
            len(bridge.lookahead) * bridge.per_lookahead_dim)
        assert bridge.practice_frozen_context_frames.unique().numel() == (
            bridge.practice_frozen_context_frames.numel())
        assert torch.equal(
            bridge.practice_frozen_context_frames,
            torch.tensor([12, 23, 24, 35, 36, 47, 48, 59]))

        bridge.set_curriculum_stage(
            "frozen_context", duration_frames=80)
        bridge.reset(bridge_ids)
        frozen_start = bridge.frame_idx.clone()
        sampled_frames = torch.unique(frozen_start)
        assert torch.equal(
            sampled_frames, bridge.practice_frozen_context_frames)
        frozen_group_counts = torch.bincount(
            bridge.frozen_context_group_index,
            minlength=len(bridge.practice_frozen_context_groups))
        expected_group_count = (
            bridge.num_envs
            / len(bridge.practice_frozen_context_groups))
        assert torch.all(
            (frozen_group_counts.float() - expected_group_count).abs()
            < 0.12 * expected_group_count), frozen_group_counts
        frozen_current = bridge.current()
        active_count = (frozen_current["fret"] > 0).sum(dim=1)
        assert set(active_count.unique().tolist()) == {1, 2}
        assert torch.equal(
            frozen_current["sustain_eligible"],
            frozen_current["fret"] > 0)
        observed_frozen = bridge.observe()
        lookahead_slot = bridge.lookahead.index(15)
        lookahead_start = lookahead_slot * bridge.per_lookahead_dim
        source_lookahead = bridge.fret[
            (frozen_start + 15).clamp(max=bridge.n_frames - 1)] / 22.0
        assert torch.equal(
            observed_frozen[:, lookahead_start:lookahead_start + 6],
            source_lookahead)
        assert (
            source_lookahead != frozen_current["fret"] / 22.0
        ).any()
        assert torch.equal(
            observed_frozen[
                :, bridge_event_offset:
                bridge_event_offset + bridge.finger_event_dim].reshape(
                    bridge.num_envs, 4, -1),
            bridge.finger_events[frozen_start])
        bridge.advance(torch.ones(bridge.num_envs, dtype=torch.bool))
        assert torch.equal(bridge.frame_idx, frozen_start)
        assert torch.equal(
            bridge.practice_remaining,
            torch.full((bridge.num_envs,), 79))

        bridge.set_frozen_context_real_probability(0.0)
        bridge.reset(bridge_ids)
        assert not bridge.frozen_context_context_blend.any()
        static_current = bridge.current()
        static_observed = bridge.observe()
        assert torch.equal(
            static_observed[
                :, lookahead_start:lookahead_start + 6],
            static_current["fret"] / 22.0)
        static_active_fingers = torch.stack([
            ((static_current["finger"] == finger)
             & (static_current["fret"] > 0)).any(dim=1)
            for finger in range(1, 5)
        ], dim=1)
        assert torch.equal(
            static_current["finger_event"][..., 10] > 0.5,
            static_active_fingers)

        assert bridge.set_frozen_context_focus(
            2, focus_probability=0.65)
        bridge.reset(bridge_ids)
        focus_slots = torch.tensor([
            2 in finger_set
            for finger_set in bridge.practice_frozen_context_group_keys],
            dtype=torch.bool)
        focus_rate = focus_slots[
            bridge.frozen_context_group_index].float().mean().item()
        assert 0.64 < focus_rate < 0.66, focus_rate
        assert bridge.set_frozen_context_focus(None)
        assert not bridge.set_frozen_context_focus(None)

        bridge.set_curriculum_stage("goal_pair", duration_frames=120)
        bridge.reset(bridge_ids)
        assert bridge.curriculum_stage == "goal_pair"
        group_counts = torch.bincount(
            bridge.goal_pair_group_index,
            minlength=len(bridge.practice_goal_pair_groups))
        expected_group_count = (
            bridge.num_envs / len(bridge.practice_goal_pair_groups))
        assert torch.all(
            (group_counts.float() - expected_group_count).abs()
            < 0.12 * expected_group_count), group_counts
        assert torch.equal(
            bridge.goal_pair_next_frame,
            bridge.goal_pair_previous_frame + 1)
        before = bridge.goal_pair_before_remaining.clone()
        total = bridge.practice_remaining.clone()
        after = total - before
        assert int(before.min()) >= 45 and int(before.max()) <= 60
        assert int(after.min()) >= 45 and int(after.max()) <= 60
        pair_start = bridge.frame_idx.clone()
        pair_event = bridge.current()["finger_event"]
        observed_pair_event = bridge.observe()[
            :, bridge_event_offset:
            bridge_event_offset + bridge.finger_event_dim].reshape(
                bridge.num_envs, 4, -1)
        assert torch.equal(observed_pair_event, pair_event)
        changes = torch.zeros(
            bridge.num_envs, dtype=torch.long)
        for _ in range(int(total.max())):
            active = bridge.practice_remaining > 0
            previous = bridge.frame_idx.clone()
            bridge.advance(active)
            changes += active & (bridge.frame_idx != previous)
        assert torch.equal(
            changes, torch.ones_like(changes))
        assert torch.equal(
            bridge.frame_idx, bridge.goal_pair_next_frame)
        assert torch.equal(
            bridge.practice_remaining,
            torch.zeros_like(bridge.practice_remaining))
        assert (pair_start == bridge.goal_pair_previous_frame).all()

        exact = FretGoalSequence(
            _single_transition_goal_file(directory), 512,
            device="cpu", seed=11)
        exact_ids = torch.arange(exact.num_envs)
        exact.set_curriculum_stage(
            "goal_pair", duration_frames=120)
        exact.reset(exact_ids)
        assert torch.equal(
            exact.goal_pair_previous_frame,
            torch.full_like(exact.frame_idx, 149))
        assert torch.equal(
            exact.goal_pair_next_frame,
            torch.full_like(exact.frame_idx, 150))
        event = exact.current()["finger_event"][:, 0]
        expected_time = (
            exact.goal_pair_before_remaining.float() / 60.0
        ).clamp(max=FINGER_EVENT_TIME_SCALE_S) / FINGER_EVENT_TIME_SCALE_S
        assert (event[:, 0] > 0.5).all()
        assert torch.allclose(
            event[:, 6], torch.full_like(event[:, 6], 6.0 / 22.0))
        assert torch.allclose(event[:, 7], expected_time)
        assert (event[:, 8] > 0.5).all()
        assert (event[:, 11] > 0.5).all()
        assert not (event[:, 10] > 0.5).any()
        offset = int(exact.goal_pair_before_remaining[0])
        only_first = torch.zeros(
            exact.num_envs, dtype=torch.bool)
        only_first[0] = True
        for _ in range(offset - 1):
            exact.advance(only_first)
            assert int(exact.frame_idx[0]) == 149
        exact.advance(only_first)
        assert int(exact.frame_idx[0]) == 150
        assert int(exact.current()["fret"][0, 0]) == 6
        arrived = exact.current()["finger_event"][0, 0]
        assert arrived[0] > 0.5
        assert torch.allclose(arrived[6], arrived.new_tensor(6.0 / 22.0))
        assert arrived[8] > 0.5
        assert arrived[10] > 0.5
        assert arrived[12] < 0.5

        exact.set_goal_pair_preview_only(True)
        exact.reset(exact_ids)
        assert exact.goal_pair_preview_mask.all()
        assert torch.equal(
            exact.practice_remaining,
            exact.goal_pair_before_remaining)
        first = torch.zeros(exact.num_envs, dtype=torch.bool)
        first[0] = True
        while int(exact.practice_remaining[0]) > 1:
            assert int(exact.frame_idx[0]) == 149
            preview_event = exact.current()["finger_event"][0, 0]
            assert preview_event[8] > 0.5
            assert preview_event[11] > 0.5
            exact.advance(first)
        assert exact.done[0]
        assert int(exact.frame_idx[0]) == 149
        assert int(exact.current()["fret"][0, 0]) == 4

    config = FingertipApproachCurriculumConfig(
        coarse_min_iterations=1, coarse_max_iterations=1,
        fine_min_iterations=1, fine_max_iterations=2,
        isolated_press_min_iterations=1, isolated_press_max_iterations=2,
        integrated_press_min_iterations=1, integrated_press_max_iterations=2,
        chord_reach_min_iterations=1, chord_reach_max_iterations=2,
        chord_fine_min_iterations=1, chord_fine_max_iterations=2,
        static_chord_min_iterations=1, static_chord_max_iterations=2,
        frozen_context_min_iterations=1,
        frozen_context_max_iterations=2,
        frozen_context_context_warmup_iterations=0,
        frozen_context_recovery_block_iterations=1,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_ready_blocks=1,
        frozen_context_recovery_max_blocks=2,
        goal_pair_min_iterations=1, goal_pair_max_iterations=2,
        goal_pair_retention_min_iterations=1,
        goal_pair_mixed_min_iterations=1,
        goal_pair_full_min_iterations=1,
        goal_pair_phase_min_evidence=1,
        frozen_context_context_ramp_iterations=1,
        transition_min_iterations=1, transition_max_iterations=2,
        transition_window_seconds=(1.0,),
        transition_max_changes=(1,),
        static_chord_min_evidence_episodes=1,
        frozen_context_min_evidence_episodes=1,
        goal_pair_min_evidence_episodes=1,
        transition_min_evidence_episodes=1,
        coverage_min_evidence_episodes=1,
        integration_min_evidence_episodes=1,
        coverage_iterations=1, integration_iterations=1,
        promotion_success_rate=0.8, promotion_windows=2,
        bridge_window_episodes=1, bridge_promotion_windows=2,
        frozen_context_final_evaluation_iterations=0,
        late_stage_grace_iterations=2,
        thumb_contact_gate_enabled=False)
    curriculum = FingertipApproachCurriculum(config)
    no_evidence = _song_stats(True)
    no_evidence.update({
        "no_press_accuracy": 0.0,
        "no_press_correct_count": 0.0,
        "no_press_evidence_count": 0.0,
    })
    assert curriculum._song_performance_sample(no_evidence) == 1.0
    pooled_failure = _song_stats(True)
    pooled_failure.update({
        "no_press_accuracy": 1.0,
        "no_press_correct_count": 9.0,
        "no_press_evidence_count": 10.0,
    })
    assert curriculum._song_performance_sample(pooled_failure) == 0.0
    curriculum.required_song_fingers = (1, 2, 3, 4)
    missing_finger = _song_stats(True)
    missing_finger["press_finger_4_success"] = 0.0
    missing_finger["press_finger_4_count"] = 0.0
    assert curriculum._song_performance_sample(missing_finger) == -1.0
    curriculum.stage = "static_chord"
    curriculum.chord_available_sets = ((1, 2), (1, 3))
    assert curriculum._song_performance_sample(missing_finger) == 1.0
    curriculum.stage = "frozen_context"
    assert curriculum._song_performance_sample(missing_finger) == -1.0
    curriculum.stage = "coarse_reach"
    curriculum.chord_available_sets = ()

    recovery_config = replace(
        config,
        frozen_context_focus_min_evidence=1,
        frozen_context_recovery_block_iterations=1,
        frozen_context_recovery_min_weight_change=0.0,
        frozen_context_max_iterations=10)
    recovery = FingertipApproachCurriculum(
        recovery_config, forced_stage="frozen_context")
    recovery.required_song_fingers = (1, 2, 3, 4)
    weak_middle = _song_stats(True)
    for finger in range(1, 5):
        weak_middle[f"curriculum_finger_{finger}_target_active_count"] = 10.0
        weak_middle[f"curriculum_finger_{finger}_target_distance"] = 0.005
    weak_middle["press_finger_2_success"] = 1.0
    weak_middle["curriculum_finger_2_target_distance"] = 0.100
    prior_bridge = dict(recovery.bridge_accumulator)
    state = recovery.after_iteration(_frozen_stats(weak_middle))
    weights = state["curriculum_frozen_context_recovery_weights"]
    assert weights[1] == max(weights)
    assert all(weight >= 0.20 for weight in weights)
    assert abs(sum(weights) - 1.0) < 1e-9
    assert state["curriculum_frozen_context_recovery_focus_fingers"] == [2]
    assert recovery.bridge_accumulator == prior_bridge
    restored_recovery = FingertipApproachCurriculum(
        recovery_config, forced_stage="frozen_context")
    restored_recovery.load_context(recovery.state())
    assert (
        restored_recovery.frozen_context_recovery_weights
        == recovery.frozen_context_recovery_weights)
    assert (
        restored_recovery.frozen_context_focus_evidence
        == recovery.frozen_context_focus_evidence)
    recovered = _song_stats(True)
    for finger in range(1, 5):
        recovered[f"curriculum_finger_{finger}_target_active_count"] = 10.0
        recovered[f"curriculum_finger_{finger}_target_distance"] = 0.005
    state = recovery.after_iteration(_frozen_stats(recovered))
    assert state["curriculum_frozen_context_focus_finger"] == 0
    recovery.bridge_last_metrics = {"finger_min": 0.64}
    assert not recovery._hard_timeout_quality_floor_passes()
    recovery.bridge_last_metrics = {
        "finger_min": 0.75,
        "f1": 0.80,
        "no_press": 0.92,
        "wrong": 0.04,
        "sustain": 0.75,
        "event_success": 0.45,
        "failure": 0.01,
    }
    assert recovery._hard_timeout_quality_floor_passes()
    recovery.bridge_last_metrics["event_success"] = 0.39
    assert not recovery._hard_timeout_quality_floor_passes()
    recovery.bridge_last_metrics = {"finger_min": 0.64}
    recovery.stage = "goal_pair"
    assert recovery._hard_timeout_quality_floor_passes()
    assert curriculum.STAGES == (
        "coarse_reach", "fine_reach", "isolated_press",
        "integrated_press", "chord_reach", "chord_fine_reach",
        "static_chord", "frozen_context", "goal_pair",
        "transition_window",
        "coverage", "integration", "full_song")

    state = curriculum.after_iteration({
        "curriculum_success_rate": 0.0,
        "curriculum_p90_target_distance": 1.0,
    })
    assert curriculum.stage == "coarse_reach"
    assert state["curriculum_stalled"]
    assert not state["curriculum_forced_advance"]
    assert state["curriculum_forced_advance_count"] == 0

    passing_reach = {
        "curriculum_success_rate": 0.9,
        "curriculum_p90_target_distance": 0.03,
        "curriculum_finger_1_success": 0.9,
        "curriculum_finger_1_count": 1.0,
        # Coarse reach is distance-gated; physical press diagnostics must not
        # block promotion before the press stage begins.
        "press_finger_1_success": 0.0,
        "press_finger_1_count": 100.0,
    }
    curriculum.after_iteration(passing_reach)
    curriculum.after_iteration(passing_reach)
    assert curriculum.stage == "fine_reach"

    curriculum.stage = "static_chord"
    curriculum.stage_iteration = 0
    curriculum.stalled = False
    curriculum.recent.clear()
    curriculum.after_iteration(_song_stats(True))
    assert curriculum.stage == "static_chord"
    curriculum.after_iteration(_static_chord_stats(True))
    curriculum.after_iteration(_static_chord_stats(True))
    assert curriculum.stage == "frozen_context"
    weak_finger = _song_stats(True)
    weak_finger["press_finger_4_success"] = 2.0
    curriculum.after_iteration(_frozen_stats(weak_finger))
    state = curriculum.after_iteration(_frozen_stats(weak_finger))
    assert curriculum.stage == "frozen_context"
    assert state["curriculum_stalled"]
    assert state["curriculum_frozen_context_recovery_failed"]
    curriculum._reset_frozen_context_recovery("test_restart")
    curriculum.frozen_context_final_applied = True
    curriculum.recent.clear()
    curriculum.stalled = False
    curriculum.after_iteration(_frozen_stats(_song_stats(True)))
    curriculum.after_iteration(_frozen_stats(_song_stats(True)))
    assert curriculum.stage == "goal_pair"
    curriculum.goal_pair_incoming_fingers = (1, 2, 3, 4)
    curriculum.after_iteration(_goal_pair_stats())
    curriculum.after_iteration(_goal_pair_stats())
    assert curriculum.goal_pair_phase == "mixed"
    for expected_level in (1, 2):
        curriculum.after_iteration(_goal_pair_stats())
        curriculum.after_iteration(_goal_pair_stats())
        assert curriculum.goal_pair_phase == "mixed"
        assert curriculum.goal_pair_mixed_level == expected_level
    curriculum.after_iteration(_goal_pair_stats())
    curriculum.after_iteration(_goal_pair_stats())
    assert curriculum.goal_pair_phase == "full"
    curriculum.after_iteration(_goal_pair_stats())
    curriculum.after_iteration(_goal_pair_stats())
    assert curriculum.stage == "transition_window"
    curriculum.after_iteration(_song_stats(True))
    curriculum.after_iteration(_song_stats(True))
    assert curriculum.stage == "coverage"

    curriculum.stage_iteration = 0
    curriculum.stalled = False
    curriculum.recent.clear()
    curriculum.after_iteration(_song_stats(False))
    state = curriculum.after_iteration(_song_stats(False))
    assert curriculum.stage == "coverage" and state["curriculum_stalled"]
    curriculum.after_iteration(_song_stats(True))
    curriculum.after_iteration(_song_stats(True))
    assert curriculum.stage == "integration"
    curriculum.after_iteration(_song_stats(True))
    curriculum.after_iteration(_song_stats(True))
    assert curriculum.stage == "full_song"

    bridge_only = _song_stats(True)
    bridge_only.update({
        "no_press_accuracy": 0.94,
        "no_press_correct_count": 94.0,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.03,
        "sustain_event_success_rate": 0.86,
        "press_dropout_rate": 0.03,
        "failure_termination": 0.01,
    })
    strict_probe = FingertipApproachCurriculum(config)
    strict_probe.required_song_fingers = (1, 2, 3, 4)
    assert strict_probe._song_performance_sample(bridge_only) == 0.0
    strict_probe.stage = "goal_pair"
    strict_probe._accumulate_bridge_stats(bridge_only)
    assert strict_probe._bridge_gate_passes(
        strict_probe.bridge_last_metrics)

    raw_pool = FingertipApproachCurriculum(
        replace(config, bridge_window_episodes=4))
    raw_pool.stage = "goal_pair"
    raw_pool.required_song_fingers = (1, 2, 3, 4)
    sparse = dict(bridge_only, episodes=1,
                  no_press_correct_count=1.0,
                  no_press_evidence_count=1.0)
    dense = dict(bridge_only, episodes=3,
                 no_press_correct_count=9.0,
                 no_press_evidence_count=10.0)
    for finger in range(1, 5):
        sparse[f"press_finger_{finger}_success"] = 1.0
        sparse[f"press_finger_{finger}_count"] = 1.0
        dense[f"press_finger_{finger}_success"] = 9.0
        dense[f"press_finger_{finger}_count"] = 10.0
    raw_pool._accumulate_bridge_stats(sparse)
    raw_pool._accumulate_bridge_stats(dense)
    expected_raw_rate = 28.0 / 31.0
    assert abs(
        raw_pool.bridge_last_metrics["no_press"]
        - expected_raw_rate) < 1e-9
    assert abs(
        raw_pool.bridge_last_metrics["finger_min"]
        - expected_raw_rate) < 1e-9

    split_pool = FingertipApproachCurriculum(
        replace(config, bridge_window_episodes=4))
    split_pool.stage = "goal_pair"
    split_pool.required_song_fingers = (1, 2, 3, 4)
    assert split_pool._accumulate_bridge_stats(
        dict(bridge_only, episodes=10)) == 2
    assert len(split_pool.bridge_windows) == 2
    assert split_pool.bridge_accumulator["episodes"] == 2.0

    pooled_config = replace(
        config, bridge_window_episodes=4,
        goal_pair_min_iterations=1, goal_pair_max_iterations=20)
    pooled = FingertipApproachCurriculum(pooled_config)
    pooled.stage = "goal_pair"
    pooled.goal_pair_phase = "full"
    pooled.goal_pair_phase_iteration = 1
    pooled.required_song_fingers = (1, 2, 3, 4)
    pooled_row = dict(bridge_only, episodes=2)
    pooled.after_iteration(pooled_row)
    assert not pooled.bridge_windows
    pooled.after_iteration(pooled_row)
    assert len(pooled.bridge_windows) == 1
    assert pooled.stage == "goal_pair"
    pooled.after_iteration(pooled_row)
    assert len(pooled.bridge_windows) == 1
    pooled.after_iteration(pooled_row)
    assert pooled.stage == "transition_window"
    assert pooled.stage_entry_baseline_source == "goal_pair"
    assert pooled.stage_entry_baseline["episodes"] == 4.0

    soft_config = replace(
        config, goal_pair_min_iterations=1,
        goal_pair_max_iterations=5)
    soft = FingertipApproachCurriculum(soft_config)
    soft.stage = "goal_pair"
    soft.goal_pair_phase = "full"
    soft.goal_pair_phase_iteration = 1
    soft.required_song_fingers = (1, 2, 3, 4)
    for _ in range(3):
        state = soft.after_iteration(_soft_bridge_stats())
        assert soft.stage == "goal_pair"
        assert not state["curriculum_forced_advance"]
    state = soft.after_iteration(_soft_bridge_stats())
    assert soft.stage == "transition_window"
    assert state["curriculum_forced_advance"]
    assert state["curriculum_last_forced_advance_from"] == (
        "goal_pair:soft_timeout")

    hard_config = replace(
        config, goal_pair_min_iterations=1,
        goal_pair_max_iterations=2)
    hard = FingertipApproachCurriculum(hard_config)
    hard.stage = "goal_pair"
    hard.goal_pair_phase = "full"
    hard.goal_pair_phase_iteration = 1
    catastrophic = _song_stats(False)
    catastrophic["nonfinite"] = 1.0
    hard.after_iteration(_song_stats(False))
    state = hard.after_iteration(catastrophic)
    assert hard.stage == "goal_pair"
    assert state["curriculum_stalled"]
    state = hard.after_iteration(_song_stats(False))
    assert hard.stage == "transition_window"
    assert state["curriculum_forced_advance"]
    assert state["curriculum_last_forced_advance_from"] == (
        "goal_pair:hard_timeout")

    hard_floor = FingertipApproachCurriculum(hard_config)
    hard_floor.stage = "goal_pair"
    hard_floor.goal_pair_phase = "full"
    hard_floor.goal_pair_phase_iteration = 1
    below_floor = _song_stats(False)
    below_floor["press_finger_4_success"] = 0.0
    hard_floor.after_iteration(below_floor)
    state = hard_floor.after_iteration(below_floor)
    assert hard_floor.stage == "goal_pair"
    assert state["curriculum_stalled"]

    coverage_config = replace(
        config, coverage_iterations=1,
        late_stage_grace_iterations=2)
    coverage = FingertipApproachCurriculum(coverage_config)
    coverage.stage = "coverage"
    coverage.after_iteration(_song_stats(False))
    state = coverage.after_iteration(_song_stats(False))
    assert coverage.stage == "coverage"
    assert state["curriculum_stalled"]
    state = coverage.after_iteration(_song_stats(False))
    assert coverage.stage == "integration"
    assert state["curriculum_forced_advance"]
    assert state["curriculum_last_forced_advance_from"] == (
        "coverage:hard_timeout")

    regression = FingertipApproachCurriculum(
        replace(
            config,
            goal_pair_max_iterations=10,
            goal_pair_recovery_min_iterations=1,
            goal_pair_recovery_windows=2,
            goal_pair_phase_baseline_warmup_iterations=0))
    regression.stage = "frozen_context"
    regression.required_song_fingers = (1, 2, 3, 4)
    regression._accumulate_bridge_stats(_song_stats(True))
    regression._promote()
    assert regression.stage == "goal_pair"
    regressed = dict(bridge_only)
    regressed.update({
        "f1_l": 0.90,
        "no_press_correct_count": 90.0,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.03,
        "sustain_event_success_rate": 0.86,
        "failure_termination": 0.03,
    })
    regression.after_iteration(_song_stats(True))
    assert regression.goal_pair_phase_baseline_label == "retention"
    regression.after_iteration(regressed)
    state = regression.after_iteration(regressed)
    assert state["curriculum_regression_hold"]
    assert set(state["curriculum_regression_metrics"]) == {
        "f1", "no_press", "wrong_press", "sustain_event", "failure"}
    assert state["curriculum_goal_pair_recovery"]
    assert state["curriculum_goal_pair_recovery_reason"] == (
        "performance_regression")
    assert state["curriculum_goal_pair_rehearsal_probability"] == 0.60
    assert state["curriculum_goal_pair_sequence_probability"] == 0.40
    regression.goal_pair_mastered_fingers = [True] * 4
    state = regression.after_iteration(_song_stats(True))
    assert state["curriculum_regression_hold"]
    assert state["curriculum_goal_pair_recovery_good_windows"] == 1
    state = regression.after_iteration(_song_stats(True))
    assert not state["curriculum_regression_hold"]
    assert not state["curriculum_goal_pair_recovery"]

    legacy = FingertipApproachCurriculum(config)
    legacy.load_context({
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 99,
        "curriculum_total_iteration": 500,
        "curriculum_schema_version": 3,
        "curriculum_stalled": True,
        "curriculum_recent": [1.0, 1.0],
    })
    assert legacy.stage == "frozen_context"
    assert legacy.stage_iteration == 0
    assert not legacy.stalled
    assert not legacy.recent
    schema4 = FingertipApproachCurriculum(config)
    schema4.load_context({
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 99,
        "curriculum_total_iteration": 500,
        "curriculum_schema_version": 4,
        "curriculum_stalled": True,
        "curriculum_recent": [1.0, 1.0],
    })
    assert schema4.stage == "frozen_context"
    assert schema4.stage_iteration == 0
    assert not schema4.stalled
    assert not schema4.recent
    schema4_frozen = FingertipApproachCurriculum(config)
    schema4_frozen.load_context({
        "curriculum_stage": "frozen_context",
        "curriculum_stage_iteration": 99,
        "curriculum_total_iteration": 500,
        "curriculum_schema_version": 4,
        "curriculum_frozen_context_final_applied": True,
        "curriculum_recent": [1.0, 1.0],
    })
    assert schema4_frozen.stage == "frozen_context"
    assert schema4_frozen.stage_iteration == 0
    assert not schema4_frozen.frozen_context_final_applied
    assert not schema4_frozen.recent
    schema5_frozen = FingertipApproachCurriculum(config)
    schema5_frozen.load_context({
        "curriculum_stage": "frozen_context",
        "curriculum_stage_iteration": 2,
        "curriculum_total_iteration": 500,
        "curriculum_schema_version": 5,
        "curriculum_frozen_context_final_applied": True,
        "curriculum_recent": [1.0],
    })
    assert schema5_frozen.stage == "frozen_context"
    assert schema5_frozen.stage_iteration == 0
    assert not schema5_frozen.frozen_context_final_applied
    assert not schema5_frozen.frozen_context_evaluation_started
    assert not schema5_frozen.recent
    assert not schema5_frozen.bridge_windows
    assert schema5_frozen.bridge_accumulator["episodes"] == 0.0
    schema5_checkpoint = FingertipApproachCurriculum(
        replace(
            config,
            frozen_context_context_warmup_iterations=200,
            frozen_context_context_ramp_iterations=800,
            frozen_context_final_evaluation_iterations=200))
    schema5_checkpoint.load_context({
        "curriculum_stage": "frozen_context",
        "curriculum_stage_iteration": 1500,
        "curriculum_total_iteration": 1500,
        "curriculum_schema_version": 5,
        "curriculum_frozen_context_final_applied": True,
        "curriculum_recent": [0.0, 0.0, 0.0],
    })
    assert schema5_checkpoint.stage_iteration == 0
    assert not schema5_checkpoint._frozen_context_evaluation_ready()
    assert not schema5_checkpoint.bridge_windows
    assert schema5_checkpoint.state()[
        "curriculum_schema_version"] == FingertipApproachCurriculum.SCHEMA_VERSION
    schema41_chord = FingertipApproachCurriculum(config)
    schema41_chord.load_context({
        "curriculum_stage": "chord_fine_reach",
        "curriculum_stage_iteration": 4074,
        "curriculum_total_iteration": 6256,
        "curriculum_schema_version": 41,
        "curriculum_chord_focus_index": -1,
        "curriculum_chord_focus_iteration": 1938,
        "curriculum_chord_focus_total_iteration": 4074,
        "curriculum_chord_available_sets": [[1, 2], [1, 3], [1, 4]],
        "curriculum_chord_unresolved_signatures": [3, 9],
        "curriculum_recent": [0.0, 0.0, 0.0],
    })
    assert schema41_chord.stage == "chord_fine_reach"
    assert schema41_chord.stage_iteration == 0
    assert schema41_chord.chord_focus_index == 0
    assert not schema41_chord.chord_available_sets
    assert not schema41_chord.chord_unresolved_signatures
    current = FingertipApproachCurriculum(config)
    current.load_context({
        "curriculum_stage": "goal_pair",
        "curriculum_stage_iteration": 99,
        "curriculum_total_iteration": 500,
        "curriculum_schema_version": 5,
    })
    assert current.stage == "frozen_context"
    assert current.stage_iteration == 0
    assert not current.frozen_context_evaluation_started

    schema6_source = FingertipApproachCurriculum(config)
    schema6_source.stage = "goal_pair"
    schema6_source.required_song_fingers = (1, 2, 3, 4)
    schema6_source._accumulate_bridge_stats(_song_stats(True))
    partial = dict(_song_stats(True), episodes=0.5)
    schema6_source._accumulate_bridge_stats(partial)
    schema6_source.stage_entry_baseline = dict(
        schema6_source.bridge_last_metrics)
    schema6_source.stage_entry_baseline_source = "frozen_context"
    schema6_state = schema6_source.state()
    schema6_restored = FingertipApproachCurriculum(config)
    schema6_restored.load_context(schema6_state)
    assert schema6_restored.stage == "goal_pair"
    assert len(schema6_restored.bridge_windows) == 1
    assert schema6_restored.bridge_accumulator["episodes"] == 0.5
    assert schema6_restored.bridge_last_metrics == (
        schema6_source.bridge_last_metrics)
    assert schema6_restored.stage_entry_baseline == (
        schema6_source.stage_entry_baseline)
    assert schema6_restored.stage_entry_baseline_source == "frozen_context"
    evidence_config = replace(
        config,
        chord_fine_min_phase_episodes=250,
        promotion_windows=2)
    evidence = FingertipApproachCurriculum(evidence_config)
    evidence.stage = "chord_fine_reach"
    evidence.chord_available_sets = ((1, 2), (1, 3))
    evidence.chord_focus_count = 2
    evidence.chord_focus_index = 0
    batch = {
        "episodes": 100,
        "failure_termination": 0.0,
        "curriculum_p90_target_distance": 0.005,
        "curriculum_cell_alignment_rate": 0.95,
        "chord_set_3_success_episodes": 90,
        "chord_set_3_target_episodes": 100,
        "chord_set_5_success_episodes": 100,
        "chord_set_5_target_episodes": 100,
    }
    assert evidence._chord_fine_phase_sample(batch) < 0.0
    assert "5" not in evidence.chord_phase_evidence
    assert evidence._chord_fine_phase_sample(batch) < 0.0
    saved = evidence.state()
    restored_evidence = FingertipApproachCurriculum(evidence_config)
    restored_evidence.load_context(saved)
    assert restored_evidence.chord_phase_evidence["3"]["target"] == 200
    assert restored_evidence._chord_fine_phase_sample(batch) == 0.9
    assert "3" not in restored_evidence.chord_phase_evidence

    rollout_evidence = FingertipApproachCurriculum(evidence_config)
    rollout_evidence.stage = "chord_fine_reach"
    rollout_evidence.chord_available_sets = ((1, 3),)
    rollout_evidence.chord_focus_count = 1
    rollout_evidence.chord_focus_index = 0
    rollout_batch = {
        "failure_termination": 0.0,
        "curriculum_chord_shape_5_target_active_count": 128.0,
        "curriculum_chord_shape_5_success": 0.75,
        "curriculum_chord_shape_5_distance_p90": 0.005,
        "curriculum_chord_shape_5_alignment": 0.95,
    }
    assert rollout_evidence._chord_fine_phase_sample(rollout_batch) < 0.0
    assert rollout_evidence._chord_fine_phase_sample(rollout_batch) == 0.75
    assert not rollout_evidence.chord_evidence_stalled

    bounded_config = replace(
        config,
        chord_fine_min_iterations=1,
        chord_fine_max_iterations=1,
        chord_fine_focus_min_iterations=1,
        chord_fine_focus_max_iterations=1,
        chord_fine_max_cycles=1,
        promotion_windows=2)
    bounded = FingertipApproachCurriculum(bounded_config)
    bounded.stage = "chord_fine_reach"
    bounded.chord_available_sets = ((1, 2), (1, 3))
    bounded.chord_focus_count = 2
    bounded.chord_focus_index = -1
    bounded_state = bounded.after_iteration({
        "nonfinite": 0.0,
        "nonfinite_count": 0.0,
        "velocity_blowup": 0.0,
        "velocity_blowup_count": 0.0,
        "failure_termination": 0.0,
    })
    assert bounded.stage == "static_chord"
    assert bounded_state["curriculum_last_forced_advance_from"] == (
        "chord_fine_reach:bounded_unresolved")
    assert bounded_state["curriculum_chord_unresolved_signatures"] == [3, 5]
    assert bounded_state["curriculum_chord_max_cycles"] == 1
    assert not bounded_state["curriculum_stalled"]

    retest = FingertipApproachCurriculum(replace(
        config,
        static_chord_min_iterations=1,
        static_chord_max_iterations=10,
        static_chord_retest_max_iterations=3))
    retest.stage = "static_chord"
    assert retest._practice_limits() == (1, 10)
    retest.static_chord_recovery_count = 1
    retest.static_chord_recovery_reason = "retest"
    assert retest._practice_limits() == (1, 3)
    assert retest.state()[
        "curriculum_static_chord_retest_max_iterations"] == 3

    print(
        "PASS: current-schema chord recovery and stage-specific evidence")


if __name__ == "__main__":
    main()
