"""CPU checks for balanced goal-pair sampling and static rehearsal."""
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

from cfg import FRET
from env.goals import FretGoalSequence
from learning.curriculum import FingertipApproachCurriculumConfig


def _balanced_goal_file(directory):
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
    path = Path(directory) / "balanced_goal.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _sample(path, seed, focus_finger=None, focus_probability=1.0):
    goals = FretGoalSequence(path, 12000, device="cpu", seed=seed)
    goals.set_goal_pair_rehearsal_probability(1.0 / 3.0)
    if focus_finger is not None:
        goals.set_goal_pair_transition_focus(
            focus_finger, focus_probability=focus_probability)
    goals.set_curriculum_stage("goal_pair", duration_frames=120)
    goals.reset(torch.arange(goals.num_envs))
    return goals


def main():
    config = FingertipApproachCurriculumConfig()
    assert config.goal_pair_rehearsal_probability == 1.0 / 3.0
    assert config.goal_pair_mixed_sequence_probabilities[-1] == 0.25
    assert (
        FRET["curriculum"]["goal_pair_rehearsal_probability"]
        == 1.0 / 3.0)
    for invalid in (-0.01, 1.01):
        try:
            replace(config, goal_pair_rehearsal_probability=invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "invalid goal-pair rehearsal probability was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = _balanced_goal_file(directory)
        goals = _sample(path, seed=23)
        repeated = _sample(path, seed=23)
        for name in (
                "goal_pair_previous_frame", "goal_pair_next_frame",
                "goal_pair_before_remaining", "goal_pair_group_index",
                "goal_pair_incoming_finger", "goal_pair_rehearsal_mask",
                "goal_pair_sequence_mask", "goal_pair_full_song_mask",
                "practice_remaining"):
            assert torch.equal(getattr(goals, name), getattr(repeated, name))

        rehearsal = goals.goal_pair_rehearsal_mask
        rehearsal_rate = rehearsal.float().mean().item()
        assert 0.32 < rehearsal_rate < 0.35, rehearsal_rate
        assert (goals.goal_pair_group_index[rehearsal] == -1).all()
        assert (goals.goal_pair_incoming_finger[rehearsal] == 0).all()
        assert torch.equal(
            goals.goal_pair_previous_frame[rehearsal],
            goals.goal_pair_next_frame[rehearsal])
        assert torch.equal(
            goals.goal_pair_before_remaining[rehearsal],
            goals.practice_remaining[rehearsal])

        transition = ~rehearsal
        assert torch.equal(
            goals.goal_pair_next_frame[transition],
            goals.goal_pair_previous_frame[transition] + 1)
        incoming = goals.goal_pair_incoming_finger[transition]
        incoming_mask = incoming > 0
        incoming_rate = incoming_mask.float().mean().item()
        assert 0.77 < incoming_rate < 0.83, incoming_rate
        counts = torch.bincount(
            incoming[incoming_mask], minlength=5)[1:].float()
        expected = counts.mean()
        assert torch.all((counts - expected).abs() < 0.07 * expected), counts

        current = goals.current()
        active = current["fret"] > 0
        rehearsal_active = torch.stack([
            ((current["finger"] == finger) & active).any(dim=1)
            for finger in range(1, 5)
        ], dim=1)
        rehearsal_counts = rehearsal_active[rehearsal].sum(dim=0).float()
        rehearsal_expected = rehearsal_counts.mean()
        assert torch.all(
            (rehearsal_counts - rehearsal_expected).abs()
            < 0.07 * rehearsal_expected), rehearsal_counts
        assert torch.equal(
            current["finger_event"][rehearsal],
            goals.finger_events[goals.frame_idx[rehearsal]])

        focused = _sample(
            path, seed=31, focus_finger=4, focus_probability=0.70)
        assert focused.device == torch.device("cpu")
        assert focused.goal_pair_transition_focus_finger == 4
        assert focused.goal_pair_transition_focus_probability == 0.70
        focused_rehearsal = focused.goal_pair_rehearsal_mask
        focused_current = focused.current()
        focused_active = torch.stack([
            ((focused_current["finger"] == finger)
             & (focused_current["fret"] > 0)).any(dim=1)
            for finger in range(1, 5)
        ], dim=1)
        focused_counts = focused_active[focused_rehearsal].sum(dim=0).float()
        focused_rehearsal_rate = (
            focused_counts[3] / focused_counts.sum()).item()
        assert focused_rehearsal_rate > 0.70, focused_counts
        focused_expected = focused_counts[:3].mean()
        assert torch.all(
            (focused_counts[:3] - focused_expected).abs()
            < 0.12 * focused_expected), focused_counts

        focused_transition = ~focused_rehearsal
        focused_incoming = focused.goal_pair_incoming_finger[focused_transition]
        focused_incoming = focused_incoming[focused_incoming > 0]
        focused_transition_counts = torch.bincount(
            focused_incoming, minlength=5)[1:].float()
        focused_transition_rate = (
            focused_transition_counts[3]
            / focused_transition_counts.sum()).item()
        assert 0.68 < focused_transition_rate < 0.72, (
            focused_transition_counts)
        nonfocus_counts = focused_transition_counts[:3]
        focused_transition_expected = nonfocus_counts.mean()
        assert torch.all(
            (nonfocus_counts - focused_transition_expected).abs()
            < 0.12 * focused_transition_expected), focused_transition_counts

        replay = FretGoalSequence(path, 512, device="cpu", seed=47)
        replay.set_goal_pair_rehearsal_probability(1.0 / 3.0)
        assert replay.set_goal_pair_transition_focus(
            4, focus_probability=0.70)
        assert not replay.set_goal_pair_transition_focus(
            4, focus_probability=0.70)
        replay.set_curriculum_stage("goal_pair", duration_frames=120)
        replay_ids = torch.arange(replay.num_envs)
        sampler_state = replay.curriculum_sampler_state_dict()
        replay.reset(replay_ids)
        sampled_once = tuple(
            getattr(replay, name).clone()
            for name in (
                "goal_pair_previous_frame", "goal_pair_next_frame",
                "goal_pair_before_remaining", "goal_pair_group_index",
                "goal_pair_incoming_finger", "goal_pair_rehearsal_mask",
                "goal_pair_sequence_mask", "goal_pair_full_song_mask",
                "practice_remaining"))
        replay.load_curriculum_sampler_state_dict(sampler_state)
        replay.reset(replay_ids)
        sampled_twice = tuple(
            getattr(replay, name).clone()
            for name in (
                "goal_pair_previous_frame", "goal_pair_next_frame",
                "goal_pair_before_remaining", "goal_pair_group_index",
                "goal_pair_incoming_finger", "goal_pair_rehearsal_mask",
                "goal_pair_sequence_mask", "goal_pair_full_song_mask",
                "practice_remaining"))
        assert all(
            first.device.type == "cpu" and torch.equal(first, second)
            for first, second in zip(sampled_once, sampled_twice))
        assert replay.set_goal_pair_transition_focus(None)

        for invalid_finger in (True, 0, 5, 1.5):
            try:
                replay.set_goal_pair_transition_focus(invalid_finger)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid goal-pair rehearsal focus finger was accepted")
        for invalid_probability in (0.0, 1.01, float("nan")):
            try:
                replay.set_goal_pair_transition_focus(
                    4, focus_probability=invalid_probability)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid goal-pair rehearsal focus probability was accepted")

        exact = FretGoalSequence(path, 512, device="cpu", seed=59)
        exact.set_goal_pair_rehearsal_probability(1.0)
        exact.set_goal_pair_rehearsal_duration(150)
        exact.set_curriculum_stage("goal_pair", duration_frames=120)
        exact.reset(torch.arange(exact.num_envs))
        assert exact.goal_pair_rehearsal_mask.all()
        assert (exact.practice_remaining == 150).all()
        assert torch.equal(
            exact.current()["finger_event"],
            exact.finger_events[exact.frame_idx])
        for offset in exact.lookahead:
            expected = (
                exact.frame_idx + offset).clamp(max=exact.n_frames - 1)
            assert torch.equal(
                exact._lookahead_indices(offset, False), expected)
        frozen = FretGoalSequence(path, 512, device="cpu", seed=61)
        frozen.set_frozen_context_real_probability(1.0)
        frozen.set_curriculum_stage("frozen_context", duration_frames=150)
        frozen.frame_idx.copy_(exact.frame_idx)
        frozen.frozen_context_context_blend.fill_(1.0)
        assert torch.equal(exact.observe(), frozen.observe())

        sequence = FretGoalSequence(path, 4096, device="cpu", seed=67)
        assert sequence.set_goal_pair_sequence_sampling(
            1.0, duration_frames=60, full_song_fraction=0.20)
        assert not sequence.set_goal_pair_sequence_sampling(
            1.0, duration_frames=60, full_song_fraction=0.20)
        sequence.set_goal_pair_rehearsal_probability(1.0)
        sequence.set_curriculum_stage("goal_pair", duration_frames=120)
        sequence_ids = torch.arange(sequence.num_envs)
        sequence.reset(sequence_ids)
        assert sequence.goal_pair_sequence_mask.all()
        assert not sequence.goal_pair_rehearsal_mask.any()
        full_rate = sequence.goal_pair_full_song_mask.float().mean().item()
        assert 0.18 < full_rate < 0.22, full_rate
        full = sequence.goal_pair_full_song_mask
        window = ~full
        assert (sequence.frame_idx[full] == 0).all()
        assert (sequence.practice_remaining[full] == sequence.n_frames).all()
        assert (sequence.practice_remaining[window] == 60).all()
        assert torch.equal(
            sequence.current()["finger_event"],
            sequence.finger_events[sequence.frame_idx])
        previous = sequence.frame_idx.clone()
        sequence.advance(torch.ones(
            sequence.num_envs, dtype=torch.bool))
        assert torch.equal(
            sequence.frame_idx,
            (previous + 1).clamp(max=sequence.n_frames - 1))
        for probability, duration, fraction in (
                (-0.1, 60, 0.0), (1.1, 60, 0.0),
                (0.5, 0, 0.0), (0.5, 60, 1.1)):
            try:
                sequence.set_goal_pair_sequence_sampling(
                    probability, duration, fraction)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid goal-pair sequence sampling was accepted")

    print("PASS: goal-pair replay, sequence bridge, and weak-finger focus")


if __name__ == "__main__":
    main()
