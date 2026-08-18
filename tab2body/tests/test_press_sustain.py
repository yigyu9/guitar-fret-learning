"""CPU checks for R27 event-level press sustain diagnostics."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from env.goals import build_sustain_event_raster
from env.metrics import PressSustainTracker, update_live_dropout_streak


def frame(fret=4, finger=1):
    return {
        "fret_goal": [fret, 0, 0, 0, 0, 0],
        "finger_goal": [finger, 0, 0, 0, 0, 0],
    }


def feed(tracker, successes):
    for success in successes:
        tracker.update(
            torch.tensor([[0, -1, -1, -1, -1, -1]]),
            torch.tensor([[True, False, False, False, False, False]]),
            torch.tensor([[success, False, False, False, False, False]]),
        )


def main():
    event_id, eligible, events = build_sustain_event_raster(
        [frame() for _ in range(12)], boundary_grace_frames=3)
    assert len(events) == 1 and events[0]["eligible_frames"] == 6
    assert eligible[:, 0].tolist() == [False] * 3 + [True] * 6 + [False] * 3
    assert (event_id[:, 0] == 0).all()

    _, short_eligible, short_events = build_sustain_event_raster(
        [frame() for _ in range(5)], boundary_grace_frames=3)
    assert short_events[0]["boundary_grace_frames"] == 0
    assert short_eligible[:, 0].all()

    tracker = PressSustainTracker(1, 1, "cpu", hold_threshold=0.90,
                                  max_dropout_frames=3)
    feed(tracker, [True] * 9 + [False])
    metrics = tracker.episode_metrics(torch.tensor([True]))
    assert metrics["sustain_event_success_count"].item() == 1.0
    assert abs(float(metrics["sustain_hold_rate"][0]) - 0.9) < 1e-6
    assert float(metrics["sustain_event_success_rate"][0]) == 1.0

    tracker.reset(torch.tensor([0]))
    feed(tracker, [True] * 23 + [False] * 4 + [True] * 23)
    metrics = tracker.episode_metrics(torch.tensor([True]))
    assert float(metrics["sustain_hold_rate"][0]) > 0.9
    assert float(metrics["sustain_max_dropout_frames"][0]) == 4.0
    assert float(metrics["sustain_event_success_rate"][0]) == 0.0

    tracker.reset(torch.tensor([0]))
    feed(tracker, [False] * 20 + [True] * 5 + [False] * 4)
    metrics = tracker.episode_metrics(torch.tensor([True]))
    assert float(metrics["sustain_max_dropout_frames"][0]) == 4.0

    tracker.reset(torch.tensor([0]))
    feed(tracker, [False] * 20)
    metrics = tracker.episode_metrics(torch.tensor([True]))
    assert float(metrics["sustain_max_dropout_frames"][0]) == 0.0
    assert float(metrics["sustain_hold_rate"][0]) == 0.0

    streak = torch.full((1, 2), 60)
    dropout = torch.tensor([[True, False]])
    assert update_live_dropout_streak(
        streak, dropout, torch.tensor([False])).tolist() == [[0, 0]]
    assert update_live_dropout_streak(
        torch.zeros_like(streak), dropout,
        torch.tensor([True])).tolist() == [[1, 0]]
    print("PASS: R27 boundary grace, hold ratio, and dropout gate")


if __name__ == "__main__":
    main()
