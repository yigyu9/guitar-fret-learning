"""CPU checks for R6 tapered-neck geometry and contact hysteresis."""
from __future__ import annotations

from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.rewards.thumb import (
    NECK_BACK_Z,
    THUMB_GEOMETRY_OBS_DIM,
    contact_force_quality,
    neck_back_geometry,
    neck_back_metrics,
    neck_half_width,
    thumb_approach_reward,
    thumb_base_action_saturation_penalty,
    thumb_compression_quality,
    thumb_geometric_support_quality,
    thumb_geometry_observation,
    thumb_press_readiness,
    thumb_press_reward_factor,
    thumb_segment_samples,
    thumb_support_reward,
    update_contact_hysteresis,
)


def main():
    assert abs(NECK_BACK_Z - (-0.016777)) < 1e-9
    y = torch.tensor([0.217197, -0.241803])
    width = neck_half_width(y)
    assert torch.allclose(width, torch.tensor([0.020419, 0.027908]), atol=1e-6)

    radius = 0.007
    ideal = torch.tensor([[[0.0, 0.0, NECK_BACK_Z - radius]]])
    distance, gap, region = neck_back_metrics(ideal, pad_radius=radius)
    assert distance < 2e-6 and gap.abs() < 1e-7 and region.item()

    side = torch.tensor([[[0.05, 0.0, NECK_BACK_Z - radius]]])
    distance, _, region = neck_back_metrics(side, pad_radius=radius)
    assert distance > 0.02 and not region.item()

    front = torch.tensor([[[0.0, 0.0, 0.02]]])
    _, _, region = neck_back_metrics(front, pad_radius=radius)
    assert not region.item()

    endpoints = torch.tensor([
        [[0.050, 0.0, NECK_BACK_Z - radius],
         [0.040, 0.0, NECK_BACK_Z - radius]],
        [[0.0, 0.250, NECK_BACK_Z - radius],
         [0.0, 0.260, NECK_BACK_Z - radius]],
    ])
    samples = thumb_segment_samples(endpoints, n_samples=3)
    geometry = neck_back_geometry(samples, pad_radius=radius)
    assert geometry.dx.shape == (2,) and geometry.dy.shape == (2,)
    assert geometry.dx[0] > 0.0 and geometry.dy[0] == 0.0
    assert geometry.dx[1] == 0.0 and geometry.dy[1] > 0.0
    observation = thumb_geometry_observation(
        endpoints, torch.tensor([True, False]),
        pad_radius=radius, n_samples=3)
    assert observation.shape == (2, THUMB_GEOMETRY_OBS_DIM)
    assert torch.allclose(observation[:, 0], geometry.dx / 0.03)
    assert torch.allclose(observation[:, 1], geometry.dy / 0.10)
    assert torch.allclose(
        observation[:, 2], (geometry.gap + 0.0005) / 0.06)
    assert torch.allclose(observation[:, 3], geometry.distance / 0.10)
    assert observation[:, 4].tolist() == [0.0, 0.0]
    assert observation[:, 5].tolist() == [1.0, 0.0]
    assert torch.isfinite(observation).all()

    previous = torch.tensor([False, False, True, True])
    force = torch.tensor([0.6, 0.2, 0.2, 0.05])
    state = update_contact_hysteresis(previous, force, on_force=0.5, off_force=0.1)
    assert state.tolist() == [True, False, True, False]

    actions = torch.tensor([
        [0.96, -0.96, 0.0],
        [1.0, -1.0, 1.0],
        [0.90, -0.50, 0.25],
    ])
    penalty = thumb_base_action_saturation_penalty(
        actions, torch.tensor([False, True, False]))
    assert torch.isclose(penalty[0], torch.tensor(0.0024), atol=1e-7)
    assert penalty[1] == 0.0 and penalty[2] == 0.0
    supported_penalty = thumb_base_action_saturation_penalty(
        actions, torch.tensor([False, True, False]),
        supported_fraction=0.25)
    assert torch.isclose(
        supported_penalty[1], torch.tensor(0.0025), atol=1e-7)

    distances = torch.tensor([0.0, 0.015, 0.05, 0.10, 0.20])
    approach = thumb_approach_reward(distances)
    assert torch.isclose(approach[0], torch.tensor(1.0))
    assert torch.all(approach[:-1] > approach[1:]) and approach[3] > 0.1
    quality = contact_force_quality(torch.tensor([0.0, 100.0, 600.0, 40000.0]))
    assert torch.allclose(quality[:2], torch.ones(2))
    assert 0.3 < quality[2] < 0.4 and quality[3] == 0.0
    compression = thumb_compression_quality(torch.tensor([0.0, 0.0005, 0.0025, 0.0045]))
    assert torch.allclose(compression[:2], torch.ones(2))
    assert torch.isclose(compression[2], torch.exp(torch.tensor(-1.0)))
    assert compression[3] < 0.02
    geometric, footprint, gap_quality = thumb_geometric_support_quality(
        torch.tensor([0.0, 0.008, 0.0]),
        torch.zeros(3),
        torch.tensor([0.0015, 0.0, -0.002]))
    assert torch.isclose(geometric[0], torch.tensor(1.0))
    assert torch.isclose(footprint[1], torch.exp(torch.tensor(-1.0)))
    assert gap_quality[2] < 0.02
    approach = torch.tensor([0.4, 1.0, 1.0])
    geometry_ready = torch.tensor([0.0, 1.0, 1.0])
    support_ready = torch.tensor([0.0, 0.0, 1.0])
    shaped = thumb_support_reward(
        approach, geometry_ready, support_ready)
    readiness = thumb_press_readiness(
        approach, geometry_ready, support_ready, torch.ones(3))
    assert shaped[0] < shaped[1] < shaped[2]
    assert readiness[0] < readiness[1] < readiness[2]
    assert shaped[2] == 1.0 and readiness[2] == 1.0
    factor = thumb_press_reward_factor(
        torch.tensor([0.0, 0.0, 1.0]),
        torch.tensor([0.0, 1.0, 1.0]), weight=0.35)
    assert torch.allclose(factor, torch.tensor([1.0, 0.65, 1.0]))
    print("PASS: R6 neck-back geometry and thumb contact hysteresis")


if __name__ == "__main__":
    main()
