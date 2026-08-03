"""CPU contracts for the A0--A4 fingertip acquisition curriculum."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.goals import FretGoalSequence
from env.rewards.fret import approach_progress_reward, linear_approach_reward
from learning.curriculum import (
    FingertipApproachCurriculum,
    FingertipApproachCurriculumConfig,
)


class FakeGoals:
    practice_available_chord_finger_sets = (
        (1, 2), (1, 3), (1, 4))

    def __init__(self):
        self.focus_index = None
        self.focus_probability = 1.0
        self.frozen_context_real_probability = 1.0

    def set_random_start_probability(self, value):
        self.probability = value

    def set_chord_focus_index(self, value, focus_probability=1.0):
        changed = (
            value != self.focus_index
            or focus_probability != self.focus_probability)
        self.focus_index = value
        self.focus_probability = focus_probability
        return changed

    def set_frozen_context_real_probability(self, value):
        changed = value != self.frozen_context_real_probability
        self.frozen_context_real_probability = value
        return changed


class FakeEnv:
    def __init__(self):
        self.goals = FakeGoals()
        self.curriculum_stage = "full_song"
        self.reset_count = 0

    def set_curriculum_stage(self, stage, duration_frames=None, reset=False):
        changed = stage != self.curriculum_stage
        self.curriculum_stage = stage
        self.duration_frames = duration_frames
        return torch.zeros(1, 2) if reset and changed else None

    def reset(self):
        self.reset_count += 1
        return torch.zeros(1, 2)


def main():
    distance = torch.tensor([0.250, 0.130, 0.010])
    score = linear_approach_reward(distance)
    assert torch.allclose(score, torch.tensor([0.0, 0.5, 1.0]), atol=1e-6)
    progress = approach_progress_reward(
        torch.tensor([0.10, 0.10, 0.10]),
        torch.tensor([0.098, 0.102, 0.10]),
        torch.tensor([True, True, False]))
    assert torch.allclose(progress, torch.tensor([1.0, -1.0, 0.0]), atol=1e-5)

    goals = FretGoalSequence(FRET["goal_path"], 4096, device="cpu", seed=7)
    goals.set_curriculum_stage("coarse_reach")
    ids = torch.arange(goals.num_envs)
    goals.reset(ids)
    current = goals.current()
    assert torch.equal((current["fret"] > 0).sum(dim=1), torch.ones(4096, dtype=torch.long))
    active_fingers = current["finger"].amax(dim=1)
    counts = torch.bincount(active_fingers, minlength=5)[1:]
    available = counts > 0
    expected = 4096 / int(available.sum())
    assert torch.all((counts[available].float() - expected).abs() < 0.12 * expected), counts
    assert goals.observe().shape == (4096, goals.goal_dim)
    assert torch.equal(goals.practice_remaining, torch.full((4096,), 120))
    goals.advance(torch.ones(4096, dtype=torch.bool))
    assert torch.equal(goals.practice_remaining, torch.full((4096,), 119))
    sampler_state = goals.curriculum_sampler_state_dict()
    small_ids = torch.arange(32)
    goals.reset(small_ids)
    sampled_once = torch.stack(
        [goals.frame_idx[small_ids], goals.practice_string[small_ids]], dim=1)
    goals.load_curriculum_sampler_state_dict(sampler_state)
    goals.reset(small_ids)
    sampled_twice = torch.stack(
        [goals.frame_idx[small_ids], goals.practice_string[small_ids]], dim=1)
    assert torch.equal(sampled_once, sampled_twice)

    cfg = FingertipApproachCurriculumConfig(
        coarse_min_iterations=1, coarse_max_iterations=4,
        fine_min_iterations=1, fine_max_iterations=4,
        isolated_press_min_iterations=1, isolated_press_max_iterations=4,
        integrated_press_min_iterations=1, integrated_press_max_iterations=4,
        chord_reach_min_iterations=1, chord_reach_max_iterations=4,
        chord_fine_min_iterations=1, chord_fine_max_iterations=4,
        chord_fine_focus_min_iterations=1,
        chord_fine_focus_max_iterations=4,
        static_chord_min_iterations=1, static_chord_max_iterations=4,
        frozen_context_min_iterations=1,
        frozen_context_max_iterations=4,
        frozen_context_context_warmup_iterations=0,
        frozen_context_context_ramp_iterations=1,
        goal_pair_min_iterations=1, goal_pair_max_iterations=20,
        goal_pair_retention_min_iterations=1,
        goal_pair_mixed_min_iterations=1,
        goal_pair_full_min_iterations=1,
        goal_pair_phase_min_evidence=1,
        transition_min_iterations=1, transition_max_iterations=4,
        transition_window_seconds=(1.0,),
        transition_max_changes=(1,),
        static_chord_min_evidence_episodes=1,
        frozen_context_min_evidence_episodes=1,
        goal_pair_min_evidence_episodes=1,
        transition_min_evidence_episodes=1,
        coverage_min_evidence_episodes=1,
        integration_min_evidence_episodes=1,
        coverage_iterations=1, integration_iterations=1,
        promotion_success_rate=0.8, promotion_windows=3,
        bridge_window_episodes=1, bridge_promotion_windows=2,
        frozen_context_final_evaluation_iterations=0,
        late_stage_grace_iterations=2)
    curriculum = FingertipApproachCurriculum(cfg)
    assert curriculum.STAGES == (
        "coarse_reach", "fine_reach", "isolated_press",
        "integrated_press", "chord_reach", "chord_fine_reach",
        "static_chord", "frozen_context", "goal_pair",
        "transition_window",
        "coverage", "integration", "full_song")
    env = FakeEnv()
    state = curriculum.apply(env)
    assert state["curriculum_stage"] == "coarse_reach"
    assert "_reset_observation" in state and env.duration_frames == 120
    for _ in range(3):
        curriculum.after_iteration({
            "curriculum_success_rate": 0.9,
            "curriculum_p90_target_distance": 0.03,
            "curriculum_thumb_distance": 0.04,
        })
    assert curriculum.stage == "fine_reach"
    for _ in range(3):
        curriculum.after_iteration({
            "curriculum_success_rate": 0.9,
            "curriculum_p90_target_distance": 0.005,
            "curriculum_cell_alignment_rate": 0.95,
            "curriculum_thumb_distance": 0.02,
        })
    assert curriculum.stage == "isolated_press"
    for _ in range(3):
        curriculum.after_iteration({
            "curriculum_success_rate": 0.9,
            "curriculum_mean_position_quality": 0.8,
            "curriculum_mean_arch_quality": 0.8,
            "curriculum_thumb_support": 0.0,
            "curriculum_thumb_wrong_contact": 1.0,
        })
    assert curriculum.stage == "integrated_press"
    state = curriculum.apply(env)
    assert state["curriculum_stage"] == "integrated_press"
    assert env.duration_frames == 180
    for _ in range(3):
        curriculum.after_iteration({
            "curriculum_success_rate": 0.9,
            "curriculum_mean_position_quality": 0.8,
            "curriculum_thumb_distance": 0.010,
            "curriculum_thumb_support": 0.0,
            "curriculum_thumb_wrong_contact": 1.0,
        })
    assert curriculum.stage == "chord_reach"
    for _ in range(3):
        curriculum.after_iteration({
            "curriculum_success_rate": 0.9,
            "curriculum_p90_target_distance": 0.03,
        })
    assert curriculum.stage == "chord_fine_reach"
    chord_fine = {
            "curriculum_success_rate": 0.9,
            "curriculum_p90_target_distance": 0.005,
            "curriculum_cell_alignment_rate": 0.95,
            "failure_termination": 0.0,
    }
    for signature in (3, 5, 9):
        state = curriculum.apply(env)
        assert state["curriculum_chord_focus_label"] in (
            "1+2", "1+3", "1+4")
        focused = {
            **chord_fine,
            f"curriculum_chord_set_{signature}_success": 0.9,
            f"curriculum_chord_set_{signature}_count": 1.0,
        }
        for _ in range(3):
            curriculum.after_iteration(focused)
        assert curriculum.stage == "chord_fine_reach"
    state = curriculum.apply(env)
    assert state["curriculum_chord_focus_label"] == "mixed"
    mixed = dict(chord_fine)
    for signature in (3, 5, 9):
        mixed[f"curriculum_chord_set_{signature}_success"] = 0.3
        mixed[f"curriculum_chord_set_{signature}_count"] = 1.0 / 3.0
    for _ in range(3):
        curriculum.after_iteration(mixed)
    assert curriculum.stage == "static_chord"
    song_stats = {
        "episodes": 1,
        "f1_l": 0.96,
        "no_press_accuracy": 1.0,
        "no_press_correct_count": 99.5,
        "no_press_evidence_count": 100.0,
        "wrong_press_rate": 0.0,
        "sustain_hold_rate": 0.96,
        "sustain_event_success_rate": 0.95,
        "sustain_max_dropout_frames": 2.0,
        "sustain_event_count": 2.0,
        "press_dropout_rate": 0.02,
        "failure_termination": 0.0,
        "nonfinite": 0.0,
        "velocity_blowup": 0.0,
        **{
            f"press_finger_{finger}_{field}": value
            for finger in range(1, 5)
            for field, value in (("success", 9.5), ("count", 10.0))
        },
    }
    static_stats = {
        **song_stats,
        "chord_ready_rate": 0.95,
        "chord_hold_quality": 0.95,
        "curriculum_success_rate": 0.95,
        "curriculum_mean_position_quality": 0.80,
        "press_dropout_rate": 0.02,
        "press_max_dropout_frames": 2.0,
    }
    goal_pair_stats = dict(song_stats)
    goal_pair_stats.update({
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
        goal_pair_stats[f"{rehearsal}_target_active_count"] = 10.0
        goal_pair_stats[f"{rehearsal}_press_success"] = 0.90
        goal_pair_stats[f"{rehearsal}_target_distance"] = 0.005
        transition = (
            f"curriculum_goal_pair_transition_finger_{finger}")
        goal_pair_stats[f"{transition}_target_active_count"] = 10.0
        goal_pair_stats[f"{transition}_press_success"] = 0.90
        goal_pair_stats[f"{transition}_next_active_count"] = 10.0
        goal_pair_stats[f"{transition}_next_distance"] = 0.015
        goal_pair_stats[f"{transition}_next_progress"] = 0.001
    for _ in range(3):
        curriculum.after_iteration(static_stats)
    assert curriculum.stage == "frozen_context"
    curriculum.apply(env)
    curriculum.recent.extend((1.0, 1.0))
    curriculum.after_iteration(song_stats)
    assert curriculum.stage == "frozen_context"
    assert curriculum.state()["curriculum_frozen_context_final"]
    assert not curriculum.frozen_context_final_applied
    reset_count = env.reset_count
    state = curriculum.apply(env)
    assert state["curriculum_frozen_context_final_applied"]
    assert env.goals.frozen_context_real_probability == 1.0
    assert env.reset_count == reset_count + 1
    assert not curriculum.recent
    for _ in range(2):
        curriculum.after_iteration(song_stats)
    assert curriculum.stage == "goal_pair"
    for _ in range(3):
        curriculum.after_iteration(goal_pair_stats)
    assert curriculum.goal_pair_phase == "mixed"
    assert curriculum.goal_pair_mixed_level == 0
    for expected_level in (1, 2):
        for _ in range(3):
            curriculum.after_iteration(goal_pair_stats)
        assert curriculum.goal_pair_phase == "mixed"
        assert curriculum.goal_pair_mixed_level == expected_level
    for _ in range(3):
        curriculum.after_iteration(goal_pair_stats)
    assert curriculum.goal_pair_phase == "full"
    for _ in range(2):
        curriculum.after_iteration(goal_pair_stats)
    assert curriculum.stage == "transition_window"
    for _ in range(2):
        curriculum.after_iteration(song_stats)
    assert curriculum.stage == "coverage"
    for _ in range(2):
        curriculum.after_iteration(song_stats)
    assert curriculum.stage == "integration"
    for _ in range(2):
        curriculum.after_iteration(song_stats)
    assert curriculum.stage == "full_song"

    capped = FingertipApproachCurriculum(
        FingertipApproachCurriculumConfig(
            coarse_min_iterations=1, coarse_max_iterations=1,
            fine_min_iterations=1, fine_max_iterations=4,
            isolated_press_min_iterations=1, isolated_press_max_iterations=4,
            integrated_press_min_iterations=1, integrated_press_max_iterations=4,
            chord_reach_min_iterations=1, chord_reach_max_iterations=4,
            chord_fine_min_iterations=1, chord_fine_max_iterations=4,
            static_chord_min_iterations=1, static_chord_max_iterations=4,
            transition_min_iterations=1, transition_max_iterations=4,
            coverage_iterations=1, integration_iterations=1,
            promotion_success_rate=0.8, promotion_windows=3))
    state = capped.after_iteration({
        "curriculum_success_rate": 0.0,
        "curriculum_p90_target_distance": 1.0,
    })
    assert capped.stage == "coarse_reach"
    assert state["curriculum_stalled"] is True
    assert state["curriculum_forced_advance"] is False
    assert state["curriculum_forced_advance_count"] == 0
    assert state["curriculum_last_forced_advance_from"] == ""

    focus_cfg = FingertipApproachCurriculumConfig(
        chord_fine_min_iterations=1, chord_fine_max_iterations=2,
        chord_fine_focus_min_iterations=1,
        chord_fine_focus_max_iterations=2,
        promotion_windows=2)
    focused = FingertipApproachCurriculum(focus_cfg)
    focused.stage = "chord_fine_reach"
    focused.apply(env)
    for signature in (3, 5, 9):
        failed = {
            "curriculum_success_rate": 0.0,
            "curriculum_p90_target_distance": 1.0,
            "curriculum_cell_alignment_rate": 0.0,
            "failure_termination": 0.0,
            f"curriculum_chord_set_{signature}_success": 0.0,
            f"curriculum_chord_set_{signature}_count": 1.0,
        }
        focused.after_iteration(failed)
        state = focused.after_iteration(failed)
        assert focused.stage == "chord_fine_reach"
        assert state["curriculum_forced_advance"]
        focused.apply(env)
    assert focused.chord_focus_index == -1
    mixed_failed = {
        "curriculum_success_rate": 0.0,
        "curriculum_p90_target_distance": 1.0,
        "curriculum_cell_alignment_rate": 0.0,
        "failure_termination": 0.0,
    }
    for signature in (3, 5, 9):
        mixed_failed[
            f"curriculum_chord_set_{signature}_success"] = 0.0
        mixed_failed[
            f"curriculum_chord_set_{signature}_count"] = 1.0 / 3.0
    focused.after_iteration(mixed_failed)
    state = focused.after_iteration(mixed_failed)
    assert focused.stage == "chord_fine_reach"
    assert focused.chord_focus_cycle == 1
    assert focused.chord_focus_index == 0
    assert state["curriculum_forced_advance"]
    restored = FingertipApproachCurriculum(focus_cfg)
    restored.load_context({
        **state,
        "curriculum_schema_version": 3,
    })
    restored_state = restored.apply(env)
    assert restored_state["curriculum_chord_focus_index"] == 0
    assert restored_state["curriculum_chord_focus_cycle"] == 1
    forced_restored = FingertipApproachCurriculum(
        focus_cfg, forced_stage="chord_fine_reach")
    forced_restored.load_context({
        **state,
        "curriculum_schema_version": 3,
    })
    assert forced_restored.chord_focus_index == 0
    assert forced_restored.chord_focus_cycle == 1
    assert (forced_restored.chord_focus_total_iteration
            == focused.chord_focus_total_iteration)

    legacy = FingertipApproachCurriculum(cfg)
    legacy.load_context({
        "curriculum_stage": "finger_articulation",
        "curriculum_stage_iteration": 999,
        "curriculum_total_iteration": 1200,
    })
    assert legacy.stage == "isolated_press"
    assert legacy.stage_iteration == 0
    print("PASS: balanced goals, compact press stages, and bounded promotion")


if __name__ == "__main__":
    main()
