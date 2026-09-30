"""CPU checks for phase-gated goal-pair rollout diagnostics."""
from __future__ import annotations

from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch
import torch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.env.tasks.task_fret import (
    FretTask,
    goal_pair_phase_diagnostics,
    goal_pair_transfer_diagnostics,
)
from tab2body.learning.models import ActorCritic
from tab2body.learning.ppo import PPOConfig, PPOTrainer


def _phase_gate_checks():
    enabled = torch.tensor([True, True, True, True, False, True])
    rehearsal = torch.tensor([False, True, False, False, False, False])
    before = torch.tensor([10, 10, 0, 10, 10, 10])
    incoming = torch.tensor([1, 2, 3, 4, 4, 4])
    gate = torch.zeros(6, 4, dtype=torch.bool)
    gate[0, 0] = True
    gate[1, 1] = True
    gate[2, 2] = True
    gate[4, 3] = True
    gate[5, 3] = True
    preserved = torch.tensor([True, False, True, False, True, False])
    quality = torch.tensor([0.75, 0.90, 0.80, 0.70, 0.60, 0.25])
    distance = torch.arange(24, dtype=torch.float32).reshape(6, 4) / 100.0
    progress = -distance

    got = goal_pair_phase_diagnostics(
        "goal_pair", enabled, rehearsal, before, incoming, gate,
        preserved, quality, distance, progress)
    assert got["goal_pair_pretransition_active"].tolist() == [
        True, False, False, False, False, True]
    assert got[
        "goal_pair_pretransition_current_press_preserved"].tolist() == [
            True, False, False, False, False, False]
    assert got[
        "goal_pair_pretransition_current_press_quality"].tolist() == [
            0.75, 0.0, 0.0, 0.0, 0.0, 0.25]
    assert got["goal_pair_transition_finger_1_next_active"].tolist() == [
        True, False, False, False, False, False]
    assert got["goal_pair_transition_finger_4_next_active"].tolist() == [
        False, False, False, False, False, True]
    assert got["goal_pair_transition_finger_1_next_distance"][0] == distance[0, 0]
    assert got["goal_pair_transition_finger_4_next_progress"][5] == progress[5, 3]
    assert not got["goal_pair_transition_finger_2_next_distance"].any()
    assert goal_pair_phase_diagnostics(
        "frozen_context", enabled, rehearsal, before, incoming, gate,
        preserved, quality, distance, progress) == {}


def _transfer_phase_checks():
    enabled = torch.ones(6, dtype=torch.bool)
    rehearsal = torch.tensor([False, True, False, False, False, False])
    sequence = torch.tensor([False, False, True, True, False, False])
    full_song = torch.tensor([False, False, True, False, False, False])
    next_gate = torch.zeros(6, 4, dtype=torch.bool)
    next_gate[0, 0] = True
    next_gate[1, 1] = True
    next_gate[2, 2] = True
    next_gate[4, 3] = True
    next_gate[5, 0] = True
    progress_gate = next_gate.clone()
    progress_gate[4, 3] = False
    distance = torch.arange(24, dtype=torch.float32).reshape(6, 4) / 100.0
    progress = distance.neg()
    active = torch.zeros(6, 4, dtype=torch.bool)
    active[0, 1] = True
    active[1, 1] = True
    active[2, 2] = True
    active[4, 3] = True
    active[5, 0] = True
    preserved = active.clone()
    preserved[0, 1] = False
    quality = torch.where(active, torch.full_like(distance, 0.75),
                          torch.ones_like(distance))

    got = goal_pair_transfer_diagnostics(
        "goal_pair", enabled, rehearsal, sequence, full_song,
        next_gate, progress_gate, distance, progress, active,
        preserved, quality)
    assert "goal_pair_transition_finger_1_next_active" not in got
    assert "goal_pair_transition_finger_1_next_distance" not in got
    assert got["goal_pair_transition_finger_2_current_press_preserved"].tolist() == [
        False, False, False, False, False, False]
    assert got["goal_pair_rehearsal_finger_2_next_distance"][1] == 0.05
    assert got["goal_pair_full_song_finger_3_next_progress"][2] == -0.10
    assert got["goal_pair_rehearsal_finger_2_current_press_preservation_active"].tolist() == [
        False, True, False, False, False, False]
    assert not got[
        "goal_pair_transition_finger_2_current_press_preserved"][0]
    assert got[
        "goal_pair_transition_finger_2_current_press_preservation_quality"
    ][0] == 0.75

    full_got = goal_pair_transfer_diagnostics(
        "full_song", enabled, rehearsal, sequence, full_song,
        next_gate, progress_gate, distance, progress, active,
        preserved, quality)
    assert full_got["goal_pair_full_song_finger_1_next_active"].tolist() == [
        True, False, False, False, False, True]
    assert "goal_pair_transition_finger_1_next_active" not in full_got
    assert goal_pair_transfer_diagnostics(
        "frozen_context", enabled, rehearsal, sequence, full_song,
        next_gate, progress_gate, distance, progress, active,
        preserved, quality) == {}


def _recovery_action_mask_checks():
    class Goals:
        goal_pair_preview_mask = torch.tensor([False, False])
        goal_pair_rehearsal_mask = torch.tensor([True, False])
        goal_pair_incoming_finger = torch.tensor([0, 0])

        @staticmethod
        def current():
            return {
                "fret": torch.tensor([
                    [0, 5, 0, 0, 0, 0],
                    [4, 0, 0, 0, 0, 0],
                ]),
                "finger": torch.tensor([
                    [0, 2, 0, 0, 0, 0],
                    [1, 0, 0, 0, 0, 0],
                ]),
            }

    task = object.__new__(FretTask)
    task.device = torch.device("cpu")
    task.num_envs = 2
    task.num_actions = 7
    task.curriculum_stage = "goal_pair"
    task.goal_pair_action_assist = False
    task.goal_pair_recovery_assist = True
    task.goal_pair_action_routing = False
    task.preparation_remaining = torch.zeros(2, dtype=torch.long)
    task._action_finger_ids = torch.tensor([0, 1, 2, -1, -1, -1, -1])
    task._action_is_wrist = torch.tensor(
        [False, False, False, True, False, False, False])
    task._action_is_transition_proximal = torch.tensor(
        [False, False, False, True, True, True, False])
    task._goal_pair_routed_fingers = torch.empty(
        2, 4, dtype=torch.bool)
    task.goals = Goals()
    mask = task.policy_action_mask()
    assert mask[0].all()
    assert mask[1].all()


def _integrated_press_progressive_mask_checks():
    class Goals:
        @staticmethod
        def current():
            return {
                "fret": torch.tensor([[0, 5, 0, 0, 0, 0]]),
                "finger": torch.tensor([[0, 2, 0, 0, 0, 0]]),
            }

    task = object.__new__(FretTask)
    task.device = torch.device("cpu")
    task.num_envs = 1
    task.num_actions = 8
    task.curriculum_stage = "integrated_press"
    task.integrated_press_control_phase = 0
    task.goal_pair_action_routing = False
    task._action_finger_ids = torch.tensor([0, 1, 2, 3, -1, -1, -1, -1])
    task._action_is_wrist = torch.tensor(
        [False, False, False, False, True, False, False, False])
    task._action_is_elbow = torch.tensor(
        [False, False, False, False, False, True, False, False])
    task._action_is_shoulder = torch.tensor(
        [False, False, False, False, False, False, True, False])
    task._goal_pair_routed_fingers = torch.ones(1, 4, dtype=torch.bool)
    task.goals = Goals()

    phase0 = task.policy_action_mask()[0]
    assert phase0.tolist() == [True, False, True, False,
                               True, False, False, False]
    task.integrated_press_control_phase = 1
    phase1 = task.policy_action_mask()[0]
    assert phase1[5] and not phase1[6] and not phase1[7]
    task.integrated_press_control_phase = 2
    phase2 = task.policy_action_mask()[0]
    assert phase2[5] and phase2[6] and not phase2[7]
    task.integrated_press_control_phase = 3
    assert task.policy_action_mask()[0].all()
    task.curriculum_stage = "fine_reach"
    fine = task.policy_action_mask()[0]
    assert fine.all()


def _isolated_press_time_lock_is_disabled_by_zero():
    class Goals:
        @staticmethod
        def current():
            return {
                "fret": torch.tensor([[0, 7, 0, 0, 0, 0]]),
                "finger": torch.tensor([[0, 4, 0, 0, 0, 0]]),
            }

    task = object.__new__(FretTask)
    task.device = torch.device("cpu")
    task.num_envs = 1
    task.num_actions = 7
    task.curriculum_stage = "isolated_press"
    task.isolated_press_lock_after_frames = 0
    task.progress_buf = torch.tensor([1000])
    task.goal_pair_action_routing = False
    task._action_finger_ids = torch.tensor([0, 1, 2, 3, 4, -1, -1])
    task._action_is_wrist = torch.tensor(
        [False, False, False, False, False, True, False])
    task._goal_pair_routed_fingers = torch.ones(1, 4, dtype=torch.bool)
    task.goals = Goals()
    assert task.policy_action_mask()[0].all()

    # A positive legacy setting remains available for a controlled ablation.
    task.isolated_press_lock_after_frames = 60
    legacy = task.policy_action_mask()[0]
    assert legacy.tolist() == [True, False, False, False, True, True, False]


def _precision_funnel_accumulator_checks():
    task = object.__new__(FretTask)
    task.curriculum_stage = "isolated_press"
    task.num_envs = 2
    for name in (
            "evidence", "press", "position", "arch", "precise"):
        setattr(
            task, f"metric_precision_{name}_frames",
            torch.zeros(2, 4))
    active = torch.zeros(2, 6, dtype=torch.bool)
    active[:, 0] = True
    assignment = torch.zeros(2, 6, 4, dtype=torch.bool)
    assignment[:, 0, 2] = True
    metrics = {
        "active": active,
        "finger_assignment": assignment,
        "precision_press_pass": active.clone(),
        "precision_position_pass": torch.zeros_like(active),
        "precision_arch_pass": active.clone(),
        "precision_precise_pass": torch.zeros_like(active),
    }
    task._accumulate_precision_funnel(
        metrics, torch.tensor([True, False]))
    assert task.metric_precision_evidence_frames[0, 2] == 1
    assert task.metric_precision_press_frames[0, 2] == 1
    assert task.metric_precision_position_frames[0, 2] == 0
    assert task.metric_precision_arch_frames[0, 2] == 1
    assert task.metric_precision_precise_frames[0, 2] == 0
    assert task.metric_precision_evidence_frames[1].sum() == 0


class _Goals:
    fret = torch.tensor([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])


class _DiagnosticEnv:
    def __init__(self):
        self.device = "cpu"
        self.num_envs = 3
        self.num_obs = 4
        self.num_actions = 2
        self.value_dim = 6
        self.reward_weights = torch.full((6,), 1.0 / 6.0)
        self.goals = _Goals()
        self.rollout_diagnostic_keys = (
            "goal_pair_pretransition_active",
            "goal_pair_pretransition_current_press_preserved",
            "goal_pair_pretransition_current_press_quality",
            "next_goal_current_press_preservation_quality",
            "next_goal_current_press_preservation_gate",
            "goal_pair_transition_finger_4_next_active",
            "goal_pair_transition_finger_4_next_distance",
            "goal_pair_transition_finger_4_next_progress",
            "goal_pair_transition_finger_4_target_active",
            "goal_pair_transition_finger_4_target_distance",
            "goal_pair_transition_finger_4_hold_quality",
            "goal_pair_transition_finger_4_hold_acquired_frame_rate",
            "goal_pair_transition_finger_4_full_hold_frame_rate",
            "goal_pair_transition_finger_4_dropout_rate",
            "goal_pair_full_song_finger_4_target_active",
            "goal_pair_full_song_finger_4_press_success",
        )
        self.step_index = 0

    def reset(self):
        self.step_index = 0
        return torch.zeros(self.num_envs, self.num_obs)

    def step(self, action):
        del action
        first = self.step_index == 0
        self.step_index += 1
        if first:
            settled = torch.tensor([False, True, True])
            pre_active = torch.tensor([True, False, False])
            preserved = torch.tensor([True, False, False])
            quality = torch.tensor([0.75, 9.0, 9.0])
            generic_quality = torch.tensor([0.8, 9.0, 9.0])
            generic_gate = torch.tensor([True, False, False])
            next_active = torch.tensor([True, False, False])
            next_distance = torch.tensor([0.04, 9.0, 9.0])
            next_progress = torch.tensor([0.01, 9.0, 9.0])
            target_active = torch.tensor([True, True, False])
            target_distance = torch.tensor([0.30, 0.05, 9.0])
            hold_quality = torch.tensor([0.90, 0.80, 9.0])
            hold_acquired = torch.tensor([1.0, 0.0, 9.0])
            full_hold = torch.tensor([0.0, 1.0, 9.0])
            dropout_rate = torch.tensor([0.10, 0.20, 9.0])
        else:
            settled = torch.tensor([False, False, True])
            pre_active = torch.tensor([False, True, False])
            preserved = torch.tensor([False, False, False])
            quality = torch.tensor([9.0, 0.25, 9.0])
            generic_quality = torch.tensor([9.0, 0.4, 9.0])
            generic_gate = torch.tensor([False, True, False])
            next_active = torch.tensor([False, True, False])
            next_distance = torch.tensor([9.0, 0.06, 9.0])
            next_progress = torch.tensor([9.0, -0.02, 9.0])
            target_active = torch.tensor([False, False, True])
            target_distance = torch.tensor([9.0, 9.0, 0.07])
            hold_quality = torch.tensor([9.0, 9.0, 0.70])
            hold_acquired = torch.tensor([9.0, 9.0, 1.0])
            full_hold = torch.tensor([9.0, 9.0, 0.0])
            dropout_rate = torch.tensor([9.0, 9.0, 0.30])
        info = {
            "diagnostic_active": torch.ones(3, dtype=torch.bool),
            "curriculum_diagnostic_enabled": settled,
            "goal_pair_pretransition_active": pre_active,
            "goal_pair_pretransition_current_press_preserved": preserved,
            "goal_pair_pretransition_current_press_quality": quality,
            "next_goal_current_press_preservation_quality":
                generic_quality,
            "next_goal_current_press_preservation_gate": generic_gate,
            "goal_pair_transition_finger_4_next_active": next_active,
            "goal_pair_transition_finger_4_next_distance": next_distance,
            "goal_pair_transition_finger_4_next_progress": next_progress,
            "goal_pair_transition_finger_4_target_active": target_active,
            "goal_pair_transition_finger_4_target_distance": target_distance,
            "goal_pair_transition_finger_4_hold_quality": hold_quality,
            "goal_pair_transition_finger_4_hold_acquired_frame_rate": (
                hold_acquired),
            "goal_pair_transition_finger_4_full_hold_frame_rate": full_hold,
            "goal_pair_transition_finger_4_dropout_rate": dropout_rate,
            "goal_pair_full_song_active": (
                torch.tensor([False, True, True]) if first
                else torch.tensor([False, False, True])),
            "goal_pair_full_song_finger_4_target_active": target_active,
            "goal_pair_full_song_finger_4_press_success": hold_quality,
        }
        obs = torch.full(
            (self.num_envs, self.num_obs), float(self.step_index))
        reward = torch.zeros(self.num_envs, self.value_dim)
        done = torch.zeros(self.num_envs, dtype=torch.bool)
        return obs, reward, done, info


def _rollout_aggregation_checks():
    env = _DiagnosticEnv()
    model = ActorCritic(
        env.num_obs, env.num_actions, value_dim=env.value_dim,
        init_std=0.02, init_mean=torch.zeros(env.num_actions))
    trainer = PPOTrainer(
        env, model, PPOConfig(horizon=2, epochs=1, minibatch_size=6))
    stats = trainer.collect()["diagnostics"]
    assert abs(
        stats["curriculum_goal_pair_pretransition_active"] - 1.0 / 3.0
    ) < 1e-7
    assert stats[
        "curriculum_goal_pair_pretransition_active_count"] == 2.0
    assert stats[
        "curriculum_goal_pair_pretransition_current_press_preserved_count"
    ] == 2.0
    assert stats[
        "curriculum_goal_pair_pretransition_current_press_preserved"] == 0.5
    assert stats[
        "curriculum_goal_pair_pretransition_current_press_quality"] == 0.5
    assert abs(
        stats["curriculum_next_goal_current_press_preservation_quality"] - 0.6
    ) < 1e-7
    assert stats[
        "curriculum_goal_pair_transition_finger_4_next_active_count"] == 2.0
    assert abs(
        stats["curriculum_goal_pair_transition_finger_4_next_distance"] - 0.05
    ) < 1e-7
    assert abs(
        stats["curriculum_goal_pair_transition_finger_4_next_progress"] + 0.005
    ) < 1e-7
    # Existing post-transition cohort diagnostics remain settling-gated while
    # gaining an explicit active-evidence count.
    assert stats[
        "curriculum_goal_pair_transition_finger_4_target_active_count"] == 2.0
    assert abs(
        stats["curriculum_goal_pair_transition_finger_4_target_distance"] - 0.06
    ) < 1e-7
    assert abs(
        stats["curriculum_goal_pair_transition_finger_4_hold_quality"] - 0.75
    ) < 1e-7
    assert stats[
        "curriculum_goal_pair_transition_finger_4_hold_acquired_frame_rate"
    ] == 0.5
    assert stats[
        "curriculum_goal_pair_transition_finger_4_full_hold_frame_rate"
    ] == 0.5
    assert abs(
        stats["curriculum_goal_pair_transition_finger_4_dropout_rate"] - 0.25
    ) < 1e-7
    assert stats[
        "curriculum_goal_pair_full_song_finger_4_target_active_count"] == 2.0
    assert abs(
        stats["curriculum_goal_pair_full_song_finger_4_press_success"] - 0.75
    ) < 1e-7


def main():
    _phase_gate_checks()
    _transfer_phase_checks()
    _recovery_action_mask_checks()
    _integrated_press_progressive_mask_checks()
    _isolated_press_time_lock_is_disabled_by_zero()
    _precision_funnel_accumulator_checks()
    _rollout_aggregation_checks()
    print("PASS: phase-gated goal-pair diagnostics and active evidence counts")


if __name__ == "__main__":
    main()
