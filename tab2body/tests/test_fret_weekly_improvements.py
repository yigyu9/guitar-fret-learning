"""CPU contracts for late wrong-press termination and joint-limit logs."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from env.metrics import (
    adjacent_finger_motion_correlations,
    normalized_joint_limit_usage,
    summarize_joint_trajectory,
    update_wrong_press_termination,
    update_wrong_crossing_termination,
)


def main():
    position = torch.tensor([
        [-1.0, 0.0, 2.0],
        [0.0, 1.0, 3.0],
    ])
    lower = torch.tensor([[-1.0, -1.0, 1.0]]).expand_as(position)
    upper = torch.tensor([[1.0, 1.0, 3.0]]).expand_as(position)
    usage = normalized_joint_limit_usage(position, lower, upper)
    assert torch.allclose(usage, torch.tensor([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 1.0],
    ]))
    summary = summarize_joint_trajectory(
        position, lower[0], upper[0], ("a", "b", "c"))
    assert summary["a"]["max_limit_usage"] == 1.0
    assert summary["b"]["near_limit_rate"] == 0.5

    t = torch.arange(5, dtype=torch.float32).square()
    flexion = torch.stack((t, t, -t, -t), dim=1)
    flexion = flexion[:, :, None].expand(-1, -1, 3)
    correlation = adjacent_finger_motion_correlations(flexion)
    assert abs(correlation["index_middle"] - 1.0) < 1e-6
    assert abs(correlation["middle_ring"] + 1.0) < 1e-6

    streak = torch.zeros(2, dtype=torch.long)
    enabled = torch.tensor([True, True])
    wrong = torch.tensor([True, False])
    for expected in (1, 2):
        streak, terminated = update_wrong_press_termination(
            streak, wrong, enabled, stage="goal_pair", frames=3,
            stages=("goal_pair",))
        assert streak.tolist() == [expected, 0]
        assert not terminated.any()
    streak, terminated = update_wrong_press_termination(
        streak, wrong, enabled, stage="goal_pair", frames=3,
        stages=("goal_pair",))
    assert streak.tolist() == [3, 0]
    assert terminated.tolist() == [True, False]

    streak, terminated = update_wrong_press_termination(
        streak, wrong, enabled, stage="coarse_reach", frames=3,
        stages=("goal_pair",))
    assert streak.tolist() == [0, 0] and not terminated.any()

    state = {
        "total_wrong": torch.zeros(2),
        "consecutive_wrong_events": torch.zeros(2, dtype=torch.long),
        "event_had_wrong": torch.zeros(2, dtype=torch.bool),
        "resolved_events": torch.zeros(2, dtype=torch.long),
    }
    for wrong in (torch.tensor([1.0, 0.0]), torch.tensor([1.0, 0.0])):
        result = update_wrong_crossing_termination(
            state["total_wrong"], state["consecutive_wrong_events"],
            state["event_had_wrong"], wrong,
            torch.tensor([True, True]), state["resolved_events"],
            torch.tensor([True, True]), minimum_resolved_events=2,
            max_count=3, max_rate=0.75, consecutive_event_limit=2)
        state = {key: result[key] for key in state}
    assert result["termination"].tolist() == [True, False]
    streak, terminated = update_wrong_press_termination(
        torch.ones(2, dtype=torch.long), wrong, enabled,
        stage="goal_pair", frames=0, stages=("goal_pair",))
    assert streak.tolist() == [0, 0] and not terminated.any()
    print("PASS: joint-limit diagnostics and late wrong-press termination")


if __name__ == "__main__":
    main()
