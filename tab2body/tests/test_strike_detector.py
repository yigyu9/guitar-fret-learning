"""CPU/CUDA tensor contracts for the marker-pick strike detector."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strike_detector import (
    DETECTOR_ARMED,
    DETECTOR_WAIT_REARM,
    DIRECTION_DOWN,
    DIRECTION_UP,
    PickStrikeDetector,
    point_to_finite_segments,
    strike_lane_gate,
    strike_lane_quality,
    strike_zone_quality,
    swept_point_string_segments,
)


def _strings(device="cpu", dtype=torch.float32):
    """Six y-aligned finite segments centered in the preferred zone."""
    x = torch.tensor(
        [-0.025, -0.015, -0.005, 0.005, 0.015, 0.025],
        device=device, dtype=dtype)
    start = torch.stack(
        [x, torch.full_like(x, -0.40), torch.zeros_like(x)], dim=-1)
    end = torch.stack(
        [x, torch.full_like(x, -0.25), torch.zeros_like(x)], dim=-1)
    return start, end


def test_finite_sweep_and_subframe_order(device="cpu"):
    start, end = _strings(device)
    previous = torch.tensor(
        [[-0.040, -0.325, -0.002]], device=device)
    current = torch.tensor(
        [[0.040, -0.325, -0.002]], device=device)
    result = swept_point_string_segments(
        previous, current, start, end, dt=1.0 / 60.0)
    assert result["intersects"].all()
    assert result["valid"].all()
    assert result["direction"].eq(DIRECTION_DOWN).all()
    assert torch.all(result["subframe_t"][:, :-1]
                     < result["subframe_t"][:, 1:])
    assert torch.allclose(
        result["string_u"], torch.full((1, 6), 0.5, device=device),
        atol=1e-6)
    assert torch.allclose(
        result["depth"], torch.full((1, 6), 0.002, device=device),
        atol=1e-7)
    assert torch.allclose(
        result["crossing_pos_g"][..., 1],
        torch.full((1, 6), -0.325, device=device), atol=1e-6)
    assert result["zone_preferred"].all()
    assert torch.allclose(
        result["zone_quality"], torch.ones(1, 6, device=device))
    assert torch.isfinite(result["crossing_pos_g"]).all()
    assert torch.isfinite(result["across_speed"]).all()


def test_current_guitar_asset_six_string_order():


    start = torch.tensor([
        [0.01765, 0.21650, 0.01230],
        [0.01050, 0.21650, 0.01230],
        [0.00360, 0.21650, 0.01230],
        [-0.00360, 0.21650, 0.01230],
        [-0.01050, 0.21650, 0.01230],
        [-0.01765, 0.21650, 0.01230],
    ])
    end = torch.tensor([
        [0.02544, -0.40345, 0.01230],
        [0.01527, -0.40500, 0.01230],
        [0.00523, -0.40670, 0.01230],
        [-0.005223, -0.40350, 0.01230],
        [-0.01529, -0.40748, 0.01230],
        [-0.02550, -0.40905, 0.01230],
    ])
    result = swept_point_string_segments(
        torch.tensor([[-0.040, -0.325, 0.01030]]),
        torch.tensor([[0.040, -0.325, 0.01030]]),
        start, end)
    assert result["valid"].all()
    assert result["direction"].eq(DIRECTION_DOWN).all()
    assert torch.argsort(result["subframe_t"][0]).tolist() == [5, 4, 3, 2, 1, 0]
    assert result["zone_preferred"].all()
    assert torch.allclose(
        result["depth"], torch.full((1, 6), 0.002), atol=1e-7)


def test_t_endpoint_and_finite_string_contract():
    start = torch.tensor([[0.0, -1.0, 0.0]])
    end = torch.tensor([[0.0, 1.0, 0.0]])

    t_zero = swept_point_string_segments(
        torch.tensor([[0.0, 0.0, -0.002]]),
        torch.tensor([[1.0, 0.0, -0.002]]), start, end)
    assert not t_zero["intersects"].item()

    t_one = swept_point_string_segments(
        torch.tensor([[-1.0, 0.0, -0.002]]),
        torch.tensor([[0.0, 0.0, -0.002]]), start, end)
    assert t_one["intersects"].item()
    assert torch.isclose(t_one["subframe_t"], torch.tensor([[1.0]])).item()

    extension = swept_point_string_segments(
        torch.tensor([[-1.0, 2.0, -0.002]]),
        torch.tensor([[1.0, 2.0, -0.002]]), start, end)
    assert not extension["intersects"].item()
    assert extension["string_u"].item() > 1.0

    parallel = swept_point_string_segments(
        torch.tensor([[0.1, -0.5, -0.002]]),
        torch.tensor([[0.1, 0.5, -0.002]]), start, end)
    assert parallel["parallel"].item()
    assert not parallel["intersects"].item()

    degenerate = swept_point_string_segments(
        torch.tensor([[-1.0, 0.0, -0.002]]),
        torch.tensor([[1.0, 0.0, -0.002]]),
        torch.zeros(1, 3), torch.zeros(1, 3))
    assert degenerate["degenerate_string"].item()
    assert not degenerate["parallel"].item()
    assert not degenerate["intersects"].item()

    string_endpoint = swept_point_string_segments(
        torch.tensor([[-1.0, 1.0, -0.002]]),
        torch.tensor([[1.0, 1.0, -0.002]]), start, end)
    assert string_endpoint["intersects"].item()
    assert torch.isclose(
        string_endpoint["string_u"], torch.tensor([[1.0]])).item()


def test_speed_depth_direction_and_nonfinite_rejection():
    start = torch.tensor([[0.0, -1.0, 0.0]])
    end = torch.tensor([[0.0, 1.0, 0.0]])
    slow = swept_point_string_segments(
        torch.tensor([[-0.01, 0.0, -0.002]]),
        torch.tensor([[0.01, 0.0, -0.002]]),
        start, end, dt=1.0, min_across_speed=0.05)
    assert slow["intersects"].item()
    assert not slow["speed_ok"].item()
    assert not slow["valid"].item()

    shallow = swept_point_string_segments(
        torch.tensor([[-0.01, 0.0, -0.0005]]),
        torch.tensor([[0.01, 0.0, -0.0005]]), start, end)
    assert shallow["intersects"].item()
    assert not shallow["depth_ok"].item()
    assert not shallow["valid"].item()

    upward = swept_point_string_segments(
        torch.tensor([[0.01, 0.0, -0.002]]),
        torch.tensor([[-0.01, 0.0, -0.002]]), start, end)
    assert upward["valid"].item()
    assert upward["direction"].item() == DIRECTION_UP
    assert upward["across_speed"].item() < 0.0

    nonfinite = swept_point_string_segments(
        torch.tensor([[float("nan"), 0.0, -0.002]]),
        torch.tensor([[0.01, 0.0, -0.002]]), start, end)
    assert not nonfinite["finite_input"].item()
    assert not nonfinite["intersects"].item()
    assert not nonfinite["valid"].item()
    for key in ("subframe_t", "string_u", "crossing_pos_g", "depth",
                "across_speed", "zone_quality"):
        assert torch.isfinite(nonfinite[key]).all(), key


def test_zone_quality_contract():
    y = torch.tensor([
        -0.390, -0.385, -0.370, -0.355, -0.325,
        -0.295, -0.275, -0.255, -0.250,
    ])
    quality = strike_zone_quality(y)
    assert torch.allclose(
        quality,
        torch.tensor([0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0]),
        atol=1e-6)


def test_sampled_lane_is_a_band_not_a_point():
    target = torch.full((7,), -0.325)
    crossing = target + torch.tensor([
        -0.013, -0.0125, -0.006, 0.0, 0.006, 0.0125, 0.013])
    quality = strike_lane_quality(
        crossing, target,
        core_half_width=0.006,
        allowed_half_width=0.0125)
    assert quality[0] == 0.0 and quality[-1] == 0.0
    assert quality[1] == 0.0 and quality[-2] == 0.0
    assert torch.allclose(quality[2:5], torch.ones(3))
    shoulder = strike_lane_quality(
        torch.tensor([-0.31575]), torch.tensor([-0.325]),
        core_half_width=0.006,
        allowed_half_width=0.0125)
    assert 0.0 < shoulder.item() < 1.0


def test_lane_gate_preserves_attempt_denominator():
    candidate = torch.tensor([True, True, True, False])
    global_allowed = torch.tensor([True, False, True, True])
    target = torch.full((4,), -0.325)
    crossing = torch.tensor([-0.325, -0.325, -0.300, -0.325])
    result = strike_lane_gate(
        candidate,
        global_allowed,
        crossing,
        target,
        core_half_width=0.006,
        allowed_half_width=0.0125,
    )
    assert torch.equal(result["attempt"], candidate)
    assert torch.equal(
        result["hit"], torch.tensor([True, False, False, False]))
    assert result["attempt"].data_ptr() != result["hit"].data_ptr()



    result["hit"].fill_(False)
    assert torch.equal(result["attempt"], candidate)


def test_point_to_finite_segment_distance():
    start = torch.tensor([[0.0, -1.0, 0.0]])
    end = torch.tensor([[0.0, 1.0, 0.0]])
    point = torch.tensor([[0.003, 0.0, 0.004]])
    result = point_to_finite_segments(point, start, end)
    assert torch.allclose(result["distance"], torch.tensor([[0.005]]))
    assert torch.allclose(result["string_u"], torch.tensor([[0.5]]))

    beyond = point_to_finite_segments(
        torch.tensor([[0.0, 2.0, 0.0]]), start, end)
    assert torch.allclose(beyond["distance"], torch.tensor([[1.0]]))
    assert torch.allclose(beyond["string_u"], torch.tensor([[1.0]]))


def test_goal_independent_release_and_rearm_state():
    start = torch.tensor([[0.0, -1.0, 0.0]])
    end = torch.tensor([[0.0, 1.0, 0.0]])
    detector = PickStrikeDetector(
        num_envs=1, num_strings=1, min_across_speed=0.05,
        min_depth=0.001, rearm_separation=0.003,
        rearm_min_frames=2)

    first = detector.step(
        torch.tensor([[-0.010, 0.0, -0.002]]),
        torch.tensor([[0.010, 0.0, -0.002]]), start, end)
    assert first["release"].item()
    assert not first["blocked_wait_rearm"].item()
    assert first["detector_state"].item() == DETECTOR_WAIT_REARM
    assert first["wait_frames"].item() == 0



    duplicate = detector.step(
        torch.tensor([[0.010, 0.0, -0.002]]),
        torch.tensor([[-0.010, 0.0, -0.002]]), start, end)
    assert duplicate["valid"].item()
    assert duplicate["blocked_wait_rearm"].item()
    assert not duplicate["release"].item()
    assert not duplicate["rearmed"].item()
    assert duplicate["wait_frames"].item() == 1

    rearm = detector.step(
        torch.tensor([[-0.010, 0.0, -0.002]]),
        torch.tensor([[-0.010, 0.0, -0.002]]), start, end)
    assert rearm["rearmed"].item()
    assert rearm["detector_state"].item() == DETECTOR_ARMED
    assert rearm["wait_frames"].item() == 0

    second = detector.step(
        torch.tensor([[-0.010, 0.0, -0.002]]),
        torch.tensor([[0.010, 0.0, -0.002]]), start, end)
    assert second["release"].item()
    assert second["detector_state"].item() == DETECTOR_WAIT_REARM

    detector.reset(torch.tensor([0]))
    assert detector.state.item() == DETECTOR_ARMED
    assert detector.wait_frames.item() == 0


def test_per_string_state_is_independent():
    start, end = _strings()
    detector = PickStrikeDetector(num_envs=1, num_strings=6)
    result = detector.step(
        torch.tensor([[-0.040, -0.325, -0.002]]),
        torch.tensor([[0.040, -0.325, -0.002]]), start, end)
    assert result["release"].all()
    assert result["detector_state"].eq(DETECTOR_WAIT_REARM).all()


def test_cpu_cuda_equivalence_when_available():
    if not torch.cuda.is_available():
        return
    start, end = _strings()
    previous = torch.tensor([
        [-0.040, -0.325, -0.002],
        [0.040, -0.325, -0.002],
    ])
    current = torch.tensor([
        [0.040, -0.325, -0.002],
        [-0.040, -0.325, -0.002],
    ])
    cpu = swept_point_string_segments(previous, current, start, end)
    cuda = swept_point_string_segments(
        previous.cuda(), current.cuda(), start.cuda(), end.cuda())
    for key in cpu:
        actual = cuda[key].cpu()
        expected = cpu[key]
        if expected.dtype == torch.bool or not expected.is_floating_point():
            assert torch.equal(actual, expected), key
        else:
            assert torch.allclose(actual, expected, atol=1e-6), key


def main():
    test_finite_sweep_and_subframe_order()
    test_current_guitar_asset_six_string_order()
    test_t_endpoint_and_finite_string_contract()
    test_speed_depth_direction_and_nonfinite_rejection()
    test_zone_quality_contract()
    test_sampled_lane_is_a_band_not_a_point()
    test_lane_gate_preserves_attempt_denominator()
    test_point_to_finite_segment_distance()
    test_goal_independent_release_and_rearm_state()
    test_per_string_state_is_independent()
    test_cpu_cuda_equivalence_when_available()
    device_note = "CPU+CUDA" if torch.cuda.is_available() else "CPU"
    print(
        f"PASS ({device_note}): finite swept pick crossing, zone quality, "
        "and physical re-arm")


if __name__ == "__main__":
    main()
