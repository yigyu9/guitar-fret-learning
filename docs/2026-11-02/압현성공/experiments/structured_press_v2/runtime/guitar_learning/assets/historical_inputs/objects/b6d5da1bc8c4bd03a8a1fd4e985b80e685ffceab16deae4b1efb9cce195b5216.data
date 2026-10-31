"""CPU checks for goal-pair recovery finger quotas."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.goals import FretGoalSequence


def _goal_file(directory):
    empty = ([0] * 6, [0] * 6)
    states = [empty]
    for finger, fret in enumerate((4, 5, 6, 7), start=1):
        fret_goal = [0] * 6
        finger_goal = [0] * 6
        fret_goal[finger - 1] = fret
        finger_goal[finger - 1] = finger
        states.extend(((fret_goal, finger_goal), empty))
    frames = []
    for frame_idx in range(len(states) * 12):
        fret, finger = states[frame_idx // 12]
        frames.append({
            "frame": frame_idx,
            "t": frame_idx / 60.0,
            "fret_goal": list(fret),
            "finger_goal": list(finger),
            "barre_goal": [False] * 6,
            "hand_anchor_fret": 4.0,
            "hand_allowed_fret_range": [1.0, 8.0],
        })
    path = Path(directory) / "goal_pair_recovery.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _configure(goals):
    goals.set_goal_pair_recovery_active(True)
    goals.set_goal_pair_finger_weights(None)
    goals.set_goal_pair_rehearsal_probability(0.50)
    goals.set_goal_pair_sequence_sampling(
        0.60, duration_frames=60, full_song_fraction=0.25, max_events=4)
    goals.set_curriculum_stage("goal_pair", duration_frames=120)


def test_recovery_quota_covers_all_fingers_and_preserves_mix_setters():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(_goal_file(directory), 4096, device="cpu", seed=11)
        _configure(goals)
        ids = torch.arange(goals.num_envs)
        goals.reset(ids)

        diagnostics = goals.goal_pair_sampler_diagnostics()
        assert diagnostics["goal_pair_sampler_recovery_active"] == 1.0
        assert diagnostics["goal_pair_sampler_assignment_total"] > 0
        for finger, minimum in enumerate((0.15, 0.15, 0.30, 0.40), start=1):
            assert diagnostics[
                f"goal_pair_sampler_finger_{finger}_target_fraction"] >= (
                    0.15 - 1e-9)
            assert abs(
                diagnostics[
                    f"goal_pair_sampler_finger_{finger}_target_fraction"]
                - minimum) < 1e-9
            assert diagnostics[
                f"goal_pair_sampler_finger_{finger}_actual_fraction"] >= (
                    0.15 - 0.01)

        rehearsal_fingers = goals.goal_pair_rehearsal_anchor_finger[
            goals.goal_pair_rehearsal_mask]
        rehearsal_counts = torch.bincount(
            rehearsal_fingers, minlength=5).float()[1:]
        rehearsal_actual = rehearsal_counts / rehearsal_counts.sum()
        assert torch.all(rehearsal_actual >= 0.15 - 0.02)

        # Existing rehearsal/sequence/full-song controls remain authoritative.
        assert abs(goals.goal_pair_sequence_mask.float().mean().item() - 0.60) < 0.03
        rehearsal_rate = goals.goal_pair_rehearsal_mask.float().mean().item()
        assert 0.17 < rehearsal_rate < 0.23
        full_rate = goals.goal_pair_full_song_mask.float().mean().item()
        assert 0.12 < full_rate < 0.18


def test_focus_is_capped_and_changes_wait_for_next_reset():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(_goal_file(directory), 512, device="cpu", seed=13)
        _configure(goals)
        ids = torch.arange(goals.num_envs)
        goals.reset(ids)
        before = tuple(value.clone() for value in (
            goals.frame_idx, goals.practice_remaining,
            goals.goal_pair_rehearsal_mask, goals.goal_pair_sequence_mask))

        goals.set_goal_pair_transition_focus(2, focus_probability=0.95)
        goals.set_goal_pair_finger_weights(None)
        assert all(torch.equal(first, second) for first, second in zip(
            before, (goals.frame_idx, goals.practice_remaining,
                     goals.goal_pair_rehearsal_mask,
                     goals.goal_pair_sequence_mask)))
        diagnostics = goals.goal_pair_sampler_diagnostics()
        assert diagnostics[
            "goal_pair_sampler_finger_2_target_fraction"] <= 0.40 + 1e-9

        goals.reset(ids)
        diagnostics = goals.goal_pair_sampler_diagnostics()
        assert abs(diagnostics[
            "goal_pair_sampler_finger_2_target_fraction"] - 0.40) < 1e-9
        for finger in range(1, 5):
            assert diagnostics[
                f"goal_pair_sampler_finger_{finger}_target_fraction"] >= (
                    0.15 - 1e-9)


def test_recovery_sampler_state_round_trip_includes_quota():
    with tempfile.TemporaryDirectory() as directory:
        path = _goal_file(directory)
        source = FretGoalSequence(path, 512, device="cpu", seed=17)
        _configure(source)
        source.set_goal_pair_transition_focus(3, focus_probability=0.90)
        ids = torch.arange(source.num_envs)
        source.reset(ids)
        state = source.curriculum_sampler_state_dict()
        assert "goal_pair_sampler" in state
        assert state["goal_pair_sampler"]["recovery_active"]
        assert state["goal_pair_sampler"]["recovery_quota"]["total"] > 0

        restored = FretGoalSequence(path, 512, device="cpu", seed=999)
        _configure(restored)
        restored.load_curriculum_sampler_state_dict(state)
        assert restored.goal_pair_recovery_active
        assert restored.goal_pair_transition_focus_finger == 3
        assert restored.goal_pair_transition_focus_probability == 0.90
        source.reset(ids)
        restored.reset(ids)
        for name in (
                "goal_pair_previous_frame", "goal_pair_next_frame",
                "goal_pair_before_remaining", "goal_pair_group_index",
                "goal_pair_incoming_finger", "goal_pair_rehearsal_mask",
                "goal_pair_rehearsal_anchor_finger", "goal_pair_sequence_mask",
                "goal_pair_full_song_mask", "goal_pair_sequence_event_count",
                "practice_remaining"):
            assert torch.equal(getattr(source, name), getattr(restored, name))
        assert source.goal_pair_sampler_diagnostics() == (
            restored.goal_pair_sampler_diagnostics())


def main():
    test_recovery_quota_covers_all_fingers_and_preserves_mix_setters()
    test_focus_is_capped_and_changes_wait_for_next_reset()
    test_recovery_sampler_state_round_trip_includes_quota()
    print("PASS: goal-pair recovery quota covers fingers and preserves reset boundaries")


if __name__ == "__main__":
    main()
