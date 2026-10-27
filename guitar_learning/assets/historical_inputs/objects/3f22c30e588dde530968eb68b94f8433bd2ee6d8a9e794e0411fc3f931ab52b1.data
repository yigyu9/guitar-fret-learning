"""CPU regression checks for weighted frozen-context sampling."""
from __future__ import annotations

import copy
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

    def singleton(finger, string, fret):
        fret_goal = [0] * 6
        finger_goal = [0] * 6
        fret_goal[string] = fret
        finger_goal[string] = finger
        return fret_goal, finger_goal

    def chord(rows):
        fret_goal = [0] * 6
        finger_goal = [0] * 6
        for finger, string, fret in rows:
            fret_goal[string] = fret
            finger_goal[string] = finger
        return fret_goal, finger_goal

    states = [empty]
    for finger, string, fret in (
            (1, 0, 4), (2, 1, 5), (3, 2, 6), (4, 3, 7)):
        states.extend((singleton(finger, string, fret), empty))
    states.extend((
        chord(((1, 0, 4), (2, 1, 5))), empty,
        chord(((1, 0, 4), (3, 2, 6))), empty,
    ))
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
    path = Path(directory) / "frozen_context_goal.json"
    path.write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))
    return path


def _assert_anchor_matches_group(goals, env_ids):
    for env_id in env_ids.tolist():
        slot = int(goals.frozen_context_group_index[env_id])
        anchor = int(goals.frozen_context_anchor_finger[env_id])
        assert anchor in goals.practice_frozen_context_group_keys[slot]


def test_weighted_sampler_and_calibration_cohort():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 64, device="cpu", seed=101)
        expected_calibration = torch.arange(64).remainder(4) == 0
        assert torch.equal(
            goals.frozen_context_calibration_mask, expected_calibration)

        goals.set_curriculum_stage("frozen_context", duration_frames=150)
        ids = torch.arange(goals.num_envs)
        goals.reset(ids)
        before = tuple(value.clone() for value in (
            goals.frame_idx, goals.practice_remaining,
            goals.frozen_context_group_index,
            goals.frozen_context_anchor_finger,
            goals.frozen_context_calibration_sample,
        ))
        assert goals.set_frozen_context_finger_weights((2, 2, 3, 3))
        assert goals.frozen_context_finger_weights == (
            0.2, 0.2, 0.3, 0.3)
        assert not goals.set_frozen_context_finger_weights((2, 2, 3, 3))
        after = (
            goals.frame_idx, goals.practice_remaining,
            goals.frozen_context_group_index,
            goals.frozen_context_anchor_finger,
            goals.frozen_context_calibration_sample,
        )
        assert all(torch.equal(first, second)
                   for first, second in zip(before, after))

        goals.reset(ids)
        assert torch.equal(
            goals.frozen_context_calibration_sample,
            goals.frozen_context_calibration_mask)
        current = goals.current()
        assert torch.equal(
            current["frozen_context_calibration"],
            goals.frozen_context_calibration_sample)
        assert torch.equal(
            current["frozen_context_anchor_finger"],
            goals.frozen_context_anchor_finger)
        _assert_anchor_matches_group(goals, ids)

        calibration = goals.frozen_context_calibration_sample
        calibration_counts = torch.bincount(
            goals.frozen_context_anchor_finger[calibration],
            minlength=5)[1:]
        assert calibration_counts.tolist() == [4, 4, 4, 4]

        diagnostics = goals.frozen_context_sampler_diagnostics()
        assert diagnostics[
            "frozen_context_sampler_adaptive_assignment_total"] == 48
        assert diagnostics[
            "frozen_context_sampler_calibration_assignment_total"] == 16
        assert diagnostics[
            "frozen_context_sampler_adaptive_max_quota_error"] <= 1.0
        assert diagnostics[
            "frozen_context_sampler_calibration_max_quota_error"] <= 1.0
        for finger, expected in enumerate((0.2, 0.2, 0.3, 0.3), start=1):
            assert abs(diagnostics[
                f"frozen_context_sampler_adaptive_finger_{finger}"
                "_target_fraction"] - expected) < 1e-9
            assert abs(diagnostics[
                f"frozen_context_sampler_adaptive_finger_{finger}_fraction"
            ] - expected) <= 0.02

        # Pinky has no stable multi-finger source group in this fixture.
        # Its 30% unavailable mix mass is redistributed between singleton and
        # coverage without starving either available category.
        assert diagnostics[
            "frozen_context_sampler_mix_stable_multi_fraction"] < 0.30
        assert diagnostics[
            "frozen_context_sampler_mix_singleton_fraction"] > 0.60
        assert diagnostics[
            "frozen_context_sampler_mix_coverage_fraction"] > 0.0

        episode_before = tuple(value.clone() for value in (
            goals.frame_idx, goals.practice_remaining,
            goals.frozen_context_group_index,
            goals.frozen_context_anchor_finger,
            goals.frozen_context_calibration_sample,
        ))
        assert goals.set_frozen_context_finger_weights((1, 2, 3, 4))
        assert all(torch.equal(first, second) for first, second in zip(
            episode_before,
            (goals.frame_idx, goals.practice_remaining,
             goals.frozen_context_group_index,
             goals.frozen_context_anchor_finger,
             goals.frozen_context_calibration_sample)))


def test_small_resets_and_sampler_state_round_trip():
    with tempfile.TemporaryDirectory() as directory:
        path = _goal_file(directory)
        source = FretGoalSequence(path, 16, device="cpu", seed=103)
        source.set_curriculum_stage("frozen_context", duration_frames=150)
        source.set_frozen_context_finger_weights((0.20, 0.20, 0.30, 0.30))
        assert source.set_frozen_context_evaluation_fraction(0.50)
        assert torch.equal(
            source.frozen_context_calibration_mask,
            torch.arange(16).remainder(2) == 0)
        adaptive_id = torch.tensor([1])
        calibration_id = torch.tensor([0])
        for _ in range(257):
            source.reset(adaptive_id)
        for _ in range(129):
            source.reset(calibration_id)
        diagnostics = source.frozen_context_sampler_diagnostics()
        assert diagnostics[
            "frozen_context_sampler_adaptive_max_quota_error"] <= 1.0
        assert diagnostics[
            "frozen_context_sampler_calibration_max_quota_error"] <= 1.0
        assert diagnostics[
            "frozen_context_sampler_adaptive_singleton_reset_fraction"] == 1.0

        state = source.curriculum_sampler_state_dict()
        restored = FretGoalSequence(path, 16, device="cpu", seed=999)
        restored.set_curriculum_stage("frozen_context", duration_frames=150)
        restored.load_curriculum_sampler_state_dict(state)
        assert restored.frozen_context_finger_weights == (
            0.20, 0.20, 0.30, 0.30)
        assert restored.frozen_context_mix_weights == (0.60, 0.30, 0.10)
        assert restored.frozen_context_evaluation_fraction == 0.50
        assert torch.equal(
            restored.frozen_context_calibration_mask,
            source.frozen_context_calibration_mask)
        for env_ids in (
                torch.tensor([1, 2, 3]),
                torch.tensor([0, 4, 8]),
                torch.tensor([5]),
                torch.arange(16)):
            source.reset(env_ids)
            restored.reset(env_ids)
            for name in (
                    "frame_idx", "frozen_context_group_index",
                    "frozen_context_anchor_finger",
                    "frozen_context_calibration_sample"):
                assert torch.equal(
                    getattr(source, name)[env_ids],
                    getattr(restored, name)[env_ids])
        source_diagnostics = source.frozen_context_sampler_diagnostics()
        restored_diagnostics = restored.frozen_context_sampler_diagnostics()
        for key in source_diagnostics:
            if key != "frozen_context_sampler_calibration_active_fraction":
                assert source_diagnostics[key] == restored_diagnostics[key]

        legacy_state = copy.deepcopy(state)
        legacy_state.pop("frozen_context_sampler")
        restored.load_curriculum_sampler_state_dict(legacy_state)
        assert restored.frozen_context_finger_weights is None


def test_coverage_mix_is_uniform_and_missing_categories_fall_back():
    with tempfile.TemporaryDirectory() as directory:
        path = _goal_file(directory)
        goals = FretGoalSequence(path, 2400, device="cpu", seed=105)
        goals.set_curriculum_stage("frozen_context", duration_frames=150)
        goals.set_frozen_context_finger_weights((1, 1, 1, 1))
        goals.set_frozen_context_mix_weights((0, 0, 1))
        goals.reset(torch.arange(goals.num_envs))
        adaptive = ~goals.frozen_context_calibration_sample
        group_counts = torch.bincount(
            goals.frozen_context_group_index[adaptive],
            minlength=len(goals.practice_frozen_context_group_keys))
        expected = int(adaptive.sum()) / len(
            goals.practice_frozen_context_group_keys)
        assert torch.all(
            (group_counts.float() - expected).abs() <= 1.0), group_counts
        _assert_anchor_matches_group(
            goals, torch.nonzero(adaptive, as_tuple=False).squeeze(-1))

        # Pinky has no stable multi-finger group. A mix that requests only
        # that unavailable category must still choose valid source groups.
        goals.set_frozen_context_mix_weights((0, 1, 0))
        goals.reset(torch.arange(goals.num_envs))
        _assert_anchor_matches_group(goals, torch.arange(goals.num_envs))
        diagnostics = goals.frozen_context_sampler_diagnostics()
        assert diagnostics[
            "frozen_context_sampler_mix_assignment_total"] > 0


def test_legacy_focus_and_invalid_weights():
    with tempfile.TemporaryDirectory() as directory:
        goals = FretGoalSequence(
            _goal_file(directory), 4096, device="cpu", seed=107)
        goals.set_curriculum_stage("frozen_context", duration_frames=150)
        assert goals.set_frozen_context_focus(2, focus_probability=0.65)
        goals.reset(torch.arange(goals.num_envs))
        focus_slots = torch.tensor([
            2 in finger_set
            for finger_set in goals.practice_frozen_context_group_keys])
        focus_rate = focus_slots[
            goals.frozen_context_group_index].float().mean().item()
        assert 0.64 < focus_rate < 0.66
        assert not goals.frozen_context_calibration_sample.any()

        assert goals.set_frozen_context_finger_weights((1, 1, 1, 1))
        assert goals.frozen_context_focus_finger is None
        assert goals.set_frozen_context_focus(2, focus_probability=0.65)
        assert goals.frozen_context_finger_weights is None

        for invalid in (
                (1, 2, 3),
                (1, 1, 1, -1),
                (1, 1, 1, float("nan")),
                (0, 0, 0, 0)):
            try:
                goals.set_frozen_context_finger_weights(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid frozen-context finger weights were accepted")
        for invalid in (
                (1, 2),
                (1, -1, 1),
                (1, float("nan"), 1),
                (0, 0, 0)):
            try:
                goals.set_frozen_context_mix_weights(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid frozen-context mix weights were accepted")


def main():
    test_weighted_sampler_and_calibration_cohort()
    test_small_resets_and_sampler_state_round_trip()
    test_coverage_mix_is_uniform_and_missing_categories_fall_back()
    test_legacy_focus_and_invalid_weights()


if __name__ == "__main__":
    main()
