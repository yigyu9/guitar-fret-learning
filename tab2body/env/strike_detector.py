"""Goal-independent virtual-pick crossing detection.

The current guitar asset does not have a physical plectrum or colliding
strings.  ``RH:pick`` is a point marker rigidly attached below ``RH:index2``
and each string is represented by two finite marker bodies.  A strike is
therefore a kinematic event: the swept pick point crosses a finite string
segment during one control frame with sufficient across-string speed and
depth.

This module deliberately has no Isaac Gym dependency.  All public operations
are pure Torch tensor code and work on CPU or CUDA.  Goal matching and timing
windows belong to the task layer; the detector always reports every physical
crossing it sees.
"""
from __future__ import annotations

import math
from typing import Any

import torch


# Guitar-local direction convention.  The across-string normal constructed
# below is always oriented toward +x_g:
#   down: low-E -> high-e == +x_g
#   up:   high-e -> low-E == -x_g
DIRECTION_UP = -1
DIRECTION_NONE = 0
DIRECTION_DOWN = 1

DETECTOR_ARMED = 0
DETECTOR_WAIT_REARM = 1

DEFAULT_ALLOWED_ZONE_Y = (-0.385, -0.255)
DEFAULT_PREFERRED_ZONE_Y = (-0.355, -0.295)


def _require_float_tensor(name: str, value: torch.Tensor) -> None:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if not value.is_floating_point():
        raise TypeError(f"{name} must use a floating dtype")


def _batched_segments(
        string_start_g: torch.Tensor,
        string_end_g: torch.Tensor,
        *,
        batch_size: int,
        dtype: torch.dtype,
        device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return string endpoints with shape ``(N, S, 3)``.

    A shared ``(S, 3)`` string set, a singleton ``(1, S, 3)`` set, and a
    per-environment ``(N, S, 3)`` set are accepted.  The last form keeps this
    detector valid when the guitar is later allowed to move.
    """
    start = torch.as_tensor(string_start_g, dtype=dtype, device=device)
    end = torch.as_tensor(string_end_g, dtype=dtype, device=device)
    if start.shape != end.shape:
        raise ValueError(
            "string_start_g and string_end_g must have identical shapes")
    if start.ndim == 2:
        if start.shape[-1] != 3:
            raise ValueError("shared string endpoints must have shape (S, 3)")
        start = start.unsqueeze(0).expand(batch_size, -1, -1)
        end = end.unsqueeze(0).expand(batch_size, -1, -1)
    elif start.ndim == 3:
        if start.shape[-1] != 3:
            raise ValueError(
                "batched string endpoints must have shape (N, S, 3)")
        if start.shape[0] == 1:
            start = start.expand(batch_size, -1, -1)
            end = end.expand(batch_size, -1, -1)
        elif start.shape[0] != batch_size:
            raise ValueError(
                "string endpoint batch dimension must be 1 or match the "
                f"pick batch ({batch_size}), got {start.shape[0]}")
    else:
        raise ValueError(
            "string endpoints must have shape (S, 3) or (N, S, 3)")
    if start.shape[1] < 1:
        raise ValueError("at least one string segment is required")
    return start, end


def _positive_scalar(name: str, value: float, *, allow_zero: bool) -> float:
    result = float(value)
    valid = result >= 0.0 if allow_zero else result > 0.0
    if not math.isfinite(result) or not valid:
        relation = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be finite and {relation}")
    return result


def _cross2(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Two-dimensional scalar cross product on the final dimension."""
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def strike_zone_quality(
        y_g: torch.Tensor,
        *,
        allowed_y: tuple[float, float] = DEFAULT_ALLOWED_ZONE_Y,
        preferred_y: tuple[float, float] = DEFAULT_PREFERRED_ZONE_Y,
) -> torch.Tensor:
    """Smooth longitudinal strike-zone quality.

    Quality is one throughout the preferred core, zero outside the allowed
    interval, and follows a raised cosine on each edge.  The intervals are
    inclusive for membership; quality at the two outer boundaries is exactly
    zero.
    """
    _require_float_tensor("y_g", y_g)
    allowed_lo, allowed_hi = map(float, allowed_y)
    preferred_lo, preferred_hi = map(float, preferred_y)
    bounds = (allowed_lo, preferred_lo, preferred_hi, allowed_hi)
    if not all(math.isfinite(value) for value in bounds):
        raise ValueError("strike-zone bounds must be finite")
    if not allowed_lo < preferred_lo <= preferred_hi < allowed_hi:
        raise ValueError(
            "strike-zone bounds must satisfy "
            "allowed_lo < preferred_lo <= preferred_hi < allowed_hi")

    quality = torch.zeros_like(y_g)
    lower_edge = (y_g >= allowed_lo) & (y_g < preferred_lo)
    preferred = (y_g >= preferred_lo) & (y_g <= preferred_hi)
    upper_edge = (y_g > preferred_hi) & (y_g <= allowed_hi)

    lower_phase = (
        (y_g - allowed_lo) / (preferred_lo - allowed_lo)).clamp(0.0, 1.0)
    upper_phase = (
        (allowed_hi - y_g) / (allowed_hi - preferred_hi)).clamp(0.0, 1.0)
    lower_quality = 0.5 - 0.5 * torch.cos(math.pi * lower_phase)
    upper_quality = 0.5 - 0.5 * torch.cos(math.pi * upper_phase)
    quality = torch.where(lower_edge, lower_quality, quality)
    quality = torch.where(preferred, torch.ones_like(quality), quality)
    quality = torch.where(upper_edge, upper_quality, quality)
    return quality


def strike_lane_quality(
        crossing_y_g: torch.Tensor,
        target_lane_y_g: torch.Tensor,
        *,
        core_half_width: float,
        allowed_half_width: float,
) -> torch.Tensor:
    """Quality for a finite band around a sampled longitudinal lane.

    The target remains an area rather than a point: every crossing within the
    core half-width receives quality one.  A raised-cosine shoulder falls to
    zero at the outer half-width.
    """
    _require_float_tensor("crossing_y_g", crossing_y_g)
    _require_float_tensor("target_lane_y_g", target_lane_y_g)
    if crossing_y_g.device != target_lane_y_g.device:
        raise ValueError("crossing and target lane tensors must share a device")
    try:
        crossing_y_g, target_lane_y_g = torch.broadcast_tensors(
            crossing_y_g, target_lane_y_g)
    except RuntimeError as exc:
        raise ValueError(
            "crossing and target lane tensors must be broadcastable") from exc
    core = _positive_scalar(
        "core_half_width", core_half_width, allow_zero=True)
    outer = _positive_scalar(
        "allowed_half_width", allowed_half_width, allow_zero=False)
    if core >= outer:
        raise ValueError(
            "lane widths must satisfy 0 <= core_half_width < "
            "allowed_half_width")
    finite = torch.isfinite(crossing_y_g) & torch.isfinite(target_lane_y_g)
    error = (crossing_y_g - target_lane_y_g).abs()
    edge_phase = ((error - core) / (outer - core)).clamp(0.0, 1.0)
    edge_quality = 0.5 + 0.5 * torch.cos(math.pi * edge_phase)
    quality = torch.where(
        error <= core, torch.ones_like(error), edge_quality)
    quality = torch.where(
        finite & (error <= outer), quality, torch.zeros_like(quality))
    return quality


def strike_lane_gate(
        target_candidate: torch.Tensor,
        global_zone_allowed: torch.Tensor,
        crossing_y_g: torch.Tensor,
        target_lane_y_g: torch.Tensor,
        *,
        core_half_width: float,
        allowed_half_width: float,
) -> dict[str, torch.Tensor]:
    """Apply the A4 longitudinal-area gate without mutating its attempt mask.

    ``attempt`` intentionally records every otherwise valid target-string
    candidate before either zone restriction is applied.  Keeping it as
    separate storage from ``hit`` is important: zone success must be
    ``hits / attempts``, not the trivially perfect ``hits / hits``.
    """
    if not isinstance(target_candidate, torch.Tensor):
        raise TypeError("target_candidate must be a torch.Tensor")
    if not isinstance(global_zone_allowed, torch.Tensor):
        raise TypeError("global_zone_allowed must be a torch.Tensor")
    if target_candidate.dtype != torch.bool:
        raise TypeError("target_candidate must use torch.bool")
    if global_zone_allowed.dtype != torch.bool:
        raise TypeError("global_zone_allowed must use torch.bool")
    if target_candidate.shape != global_zone_allowed.shape:
        raise ValueError(
            "target_candidate and global_zone_allowed must share a shape")
    if target_candidate.device != global_zone_allowed.device:
        raise ValueError(
            "target_candidate and global_zone_allowed must share a device")

    quality = strike_lane_quality(
        crossing_y_g,
        target_lane_y_g,
        core_half_width=core_half_width,
        allowed_half_width=allowed_half_width,
    )
    if quality.shape != target_candidate.shape:
        raise ValueError(
            "broadcast crossing/target lane shape must match candidate shape")
    if quality.device != target_candidate.device:
        raise ValueError(
            "lane tensors and candidate mask must share a device")

    lane_allowed = (
        torch.isfinite(crossing_y_g)
        & torch.isfinite(target_lane_y_g)
        & ((crossing_y_g - target_lane_y_g).abs()
           <= float(allowed_half_width)))
    attempt = target_candidate.clone()
    hit = target_candidate & global_zone_allowed & lane_allowed
    return {
        "attempt": attempt,
        "hit": hit,
        "lane_allowed": lane_allowed,
        "lane_quality": quality,
    }


def point_to_finite_segments(
        point_g: torch.Tensor,
        string_start_g: torch.Tensor,
        string_end_g: torch.Tensor,
        *,
        epsilon: float = 1e-12,
) -> dict[str, torch.Tensor]:
    """Shortest 3-D distance from each point to each finite string segment.

    Invalid or degenerate string inputs are marked in ``finite`` and receive
    zero-valued coordinates and distance.  Callers must gate state changes
    with ``finite``; keeping diagnostics finite prevents one malformed
    environment from contaminating vectorized logging.
    """
    _require_float_tensor("point_g", point_g)
    if point_g.ndim != 2 or point_g.shape[1] != 3:
        raise ValueError("point_g must have shape (N, 3)")
    epsilon = _positive_scalar("epsilon", epsilon, allow_zero=False)
    start, end = _batched_segments(
        string_start_g, string_end_g,
        batch_size=point_g.shape[0], dtype=point_g.dtype,
        device=point_g.device)

    finite_point = torch.isfinite(point_g).all(dim=-1, keepdim=True)
    finite_segment = (
        torch.isfinite(start).all(dim=-1)
        & torch.isfinite(end).all(dim=-1))
    finite = finite_point & finite_segment
    safe_point = torch.where(
        torch.isfinite(point_g), point_g, torch.zeros_like(point_g))
    safe_start = torch.where(torch.isfinite(start), start, torch.zeros_like(start))
    safe_end = torch.where(torch.isfinite(end), end, torch.zeros_like(end))

    segment = safe_end - safe_start
    length_sq = (segment * segment).sum(dim=-1)
    nondegenerate = length_sq > epsilon * epsilon
    safe_length_sq = torch.where(
        nondegenerate, length_sq, torch.ones_like(length_sq))
    relative = safe_point[:, None, :] - safe_start
    segment_u = (
        (relative * segment).sum(dim=-1) / safe_length_sq).clamp(0.0, 1.0)
    closest = safe_start + segment_u[..., None] * segment
    distance = torch.linalg.vector_norm(
        safe_point[:, None, :] - closest, dim=-1)
    finite = finite & nondegenerate
    distance = torch.where(finite, distance, torch.zeros_like(distance))
    segment_u = torch.where(finite, segment_u, torch.zeros_like(segment_u))
    closest = torch.where(finite[..., None], closest, torch.zeros_like(closest))
    return {
        "distance": distance,
        "string_u": segment_u,
        "closest_pos_g": closest,
        "finite": finite,
    }


def swept_point_string_segments(
        previous_tip_g: torch.Tensor,
        current_tip_g: torch.Tensor,
        string_start_g: torch.Tensor,
        string_end_g: torch.Tensor,
        *,
        dt: float = 1.0 / 60.0,
        min_across_speed: float = 0.05,
        min_depth: float = 0.001,
        parallel_epsilon: float = 1e-9,
        segment_epsilon: float = 1e-9,
        allowed_y: tuple[float, float] = DEFAULT_ALLOWED_ZONE_Y,
        preferred_y: tuple[float, float] = DEFAULT_PREFERRED_ZONE_Y,
) -> dict[str, torch.Tensor]:
    """Intersect a swept pick point with every finite string segment.

    Args:
        previous_tip_g/current_tip_g:
            Guitar-local pick-tip points with shape ``(N, 3)``.
        string_start_g/string_end_g:
            Shared ``(S, 3)`` or batched ``(N, S, 3)`` finite endpoints.
        dt:
            One control-frame duration in seconds.
        min_across_speed:
            Minimum absolute velocity along the string's in-plane normal.
        min_depth:
            Required inward depth, ``string_z - pick_z``, at the crossing.

    Returns:
        A dictionary of tensors with shape ``(N, S)`` except positions/normals,
        which have shape ``(N, S, 3)``.  ``intersects`` contains pure finite
        xy segment intersections.  ``valid`` additionally applies speed and
        depth, but never timing, goal string, direction, or zone membership.
    """
    _require_float_tensor("previous_tip_g", previous_tip_g)
    _require_float_tensor("current_tip_g", current_tip_g)
    if previous_tip_g.shape != current_tip_g.shape:
        raise ValueError(
            "previous_tip_g and current_tip_g must have identical shapes")
    if previous_tip_g.ndim != 2 or previous_tip_g.shape[1] != 3:
        raise ValueError("pick-tip tensors must have shape (N, 3)")
    if previous_tip_g.device != current_tip_g.device:
        raise ValueError("pick-tip tensors must be on the same device")
    if previous_tip_g.dtype != current_tip_g.dtype:
        raise ValueError("pick-tip tensors must use the same dtype")

    dt = _positive_scalar("dt", dt, allow_zero=False)
    min_across_speed = _positive_scalar(
        "min_across_speed", min_across_speed, allow_zero=True)
    min_depth = _positive_scalar("min_depth", min_depth, allow_zero=True)
    parallel_epsilon = _positive_scalar(
        "parallel_epsilon", parallel_epsilon, allow_zero=False)
    segment_epsilon = _positive_scalar(
        "segment_epsilon", segment_epsilon, allow_zero=False)

    batch_size = previous_tip_g.shape[0]
    start, end = _batched_segments(
        string_start_g, string_end_g, batch_size=batch_size,
        dtype=previous_tip_g.dtype, device=previous_tip_g.device)

    finite_tip = (
        torch.isfinite(previous_tip_g).all(dim=-1)
        & torch.isfinite(current_tip_g).all(dim=-1))
    finite_segment = (
        torch.isfinite(start).all(dim=-1)
        & torch.isfinite(end).all(dim=-1))
    finite_input = finite_tip[:, None] & finite_segment

    p0 = torch.where(
        torch.isfinite(previous_tip_g), previous_tip_g,
        torch.zeros_like(previous_tip_g))
    p1 = torch.where(
        torch.isfinite(current_tip_g), current_tip_g,
        torch.zeros_like(current_tip_g))
    start = torch.where(torch.isfinite(start), start, torch.zeros_like(start))
    end = torch.where(torch.isfinite(end), end, torch.zeros_like(end))

    pick_delta = p1 - p0
    pick_delta_xy = pick_delta[:, None, :2]
    string_delta = end - start
    string_delta_xy = string_delta[..., :2]
    string_length_xy = torch.linalg.vector_norm(string_delta_xy, dim=-1)
    nondegenerate = string_length_xy > segment_epsilon

    denominator = _cross2(pick_delta_xy, string_delta_xy)
    nonparallel = denominator.abs() > parallel_epsilon
    safe_denominator = torch.where(
        nonparallel, denominator, torch.ones_like(denominator))
    start_from_pick = start[..., :2] - p0[:, None, :2]
    subframe_t_raw = (
        _cross2(start_from_pick, string_delta_xy) / safe_denominator)
    string_u_raw = (
        _cross2(start_from_pick, pick_delta_xy) / safe_denominator)

    # The previous endpoint belongs to the previous control interval, so t=0
    # is excluded.  The fresh current endpoint t=1 and both finite string
    # endpoints are included.
    within_pick = (subframe_t_raw > 0.0) & (subframe_t_raw <= 1.0)
    within_string = (string_u_raw >= 0.0) & (string_u_raw <= 1.0)
    intersects = (
        finite_input & nondegenerate & nonparallel
        & within_pick & within_string)

    safe_t = torch.where(
        finite_input & nonparallel, subframe_t_raw,
        torch.zeros_like(subframe_t_raw))
    safe_u = torch.where(
        finite_input & nonparallel, string_u_raw,
        torch.zeros_like(string_u_raw))
    crossing_pos = (
        p0[:, None, :] + safe_t[..., None] * pick_delta[:, None, :])
    string_pos = start + safe_u[..., None] * string_delta
    crossing_pos = torch.where(
        finite_input[..., None], crossing_pos, torch.zeros_like(crossing_pos))
    string_pos = torch.where(
        finite_input[..., None], string_pos, torch.zeros_like(string_pos))

    depth = string_pos[..., 2] - crossing_pos[..., 2]
    unit_tangent_xy = string_delta_xy / string_length_xy.clamp_min(
        segment_epsilon)[..., None]
    across_normal_xy = torch.stack(
        [-unit_tangent_xy[..., 1], unit_tangent_xy[..., 0]], dim=-1)
    # Orient every local across normal toward +x_g so its velocity sign has a
    # single musical meaning even though the authored string endpoints slope.
    normal_sign = torch.where(
        across_normal_xy[..., 0] < 0.0,
        -torch.ones_like(across_normal_xy[..., 0]),
        torch.ones_like(across_normal_xy[..., 0]))
    across_normal_xy = across_normal_xy * normal_sign[..., None]
    across_normal_g = torch.cat(
        [across_normal_xy,
         torch.zeros_like(across_normal_xy[..., :1])], dim=-1)
    across_speed = (
        pick_delta_xy * across_normal_xy).sum(dim=-1) / dt
    direction = torch.sign(across_speed).to(torch.int8)

    speed_ok = across_speed.abs() >= min_across_speed
    depth_ok = depth >= min_depth
    valid = intersects & speed_ok & depth_ok
    zone_quality = strike_zone_quality(
        crossing_pos[..., 1], allowed_y=allowed_y,
        preferred_y=preferred_y)
    zone_quality = torch.where(
        intersects, zone_quality, torch.zeros_like(zone_quality))
    allowed_lo, allowed_hi = allowed_y
    preferred_lo, preferred_hi = preferred_y
    zone_allowed = (
        intersects
        & (crossing_pos[..., 1] >= allowed_lo)
        & (crossing_pos[..., 1] <= allowed_hi))
    zone_preferred = (
        intersects
        & (crossing_pos[..., 1] >= preferred_lo)
        & (crossing_pos[..., 1] <= preferred_hi))

    # Keep diagnostic tensors finite so a malformed environment cannot poison
    # a vectorized reward or observation.  ``finite_input`` remains the
    # authoritative error mask.
    safe_t = torch.where(torch.isfinite(safe_t), safe_t, torch.zeros_like(safe_t))
    safe_u = torch.where(torch.isfinite(safe_u), safe_u, torch.zeros_like(safe_u))
    depth = torch.where(torch.isfinite(depth), depth, torch.zeros_like(depth))
    across_speed = torch.where(
        torch.isfinite(across_speed), across_speed,
        torch.zeros_like(across_speed))
    zone_quality = torch.where(
        torch.isfinite(zone_quality), zone_quality,
        torch.zeros_like(zone_quality))
    return {
        "finite_input": finite_input,
        "degenerate_string": finite_input & ~nondegenerate,
        "parallel": finite_input & nondegenerate & ~nonparallel,
        "intersects": intersects,
        "valid": valid,
        "speed_ok": speed_ok & finite_input & nondegenerate,
        "depth_ok": depth_ok & finite_input & nondegenerate,
        "subframe_t": safe_t,
        "string_u": safe_u,
        "crossing_pos_g": crossing_pos,
        "string_pos_g": string_pos,
        "depth": depth,
        "across_speed": across_speed,
        "across_normal_g": across_normal_g,
        "direction": direction,
        "zone_quality": zone_quality,
        "zone_allowed": zone_allowed,
        "zone_preferred": zone_preferred,
    }


class PickStrikeDetector:
    """Per-``(environment, string)`` release and debounce state.

    The public motor phases (READY/APPROACH/RELEASE_RECOVER) are intentionally
    not represented here.  This state machine only suppresses repeated
    detections from one physical crossing:

    ``ARMED -> RELEASE pulse -> WAIT_REARM -> ARMED``.

    A WAIT_REARM entry returns to ARMED only after both a minimum number of
    complete control frames and minimum 3-D point-to-finite-string separation.
    Crossings observed while waiting are reported as
    ``blocked_wait_rearm`` rather than silently becoming successful releases.
    """

    def __init__(
            self,
            num_envs: int,
            num_strings: int = 6,
            *,
            device: torch.device | str = "cpu",
            min_across_speed: float = 0.05,
            min_depth: float = 0.001,
            rearm_separation: float = 0.003,
            rearm_min_frames: int = 2,
            parallel_epsilon: float = 1e-9,
            segment_epsilon: float = 1e-9,
            allowed_y: tuple[float, float] = DEFAULT_ALLOWED_ZONE_Y,
            preferred_y: tuple[float, float] = DEFAULT_PREFERRED_ZONE_Y,
    ):
        if int(num_envs) != num_envs or int(num_envs) <= 0:
            raise ValueError("num_envs must be a positive integer")
        if int(num_strings) != num_strings or int(num_strings) <= 0:
            raise ValueError("num_strings must be a positive integer")
        if int(rearm_min_frames) != rearm_min_frames or rearm_min_frames < 1:
            raise ValueError("rearm_min_frames must be a positive integer")
        self.num_envs = int(num_envs)
        self.num_strings = int(num_strings)
        self.device = torch.device(device)
        self.min_across_speed = _positive_scalar(
            "min_across_speed", min_across_speed, allow_zero=True)
        self.min_depth = _positive_scalar(
            "min_depth", min_depth, allow_zero=True)
        self.rearm_separation = _positive_scalar(
            "rearm_separation", rearm_separation, allow_zero=True)
        self.rearm_min_frames = int(rearm_min_frames)
        self.parallel_epsilon = _positive_scalar(
            "parallel_epsilon", parallel_epsilon, allow_zero=False)
        self.segment_epsilon = _positive_scalar(
            "segment_epsilon", segment_epsilon, allow_zero=False)
        # Validate zone ordering immediately, not on the first training step.
        strike_zone_quality(
            torch.zeros((), device=self.device),
            allowed_y=allowed_y, preferred_y=preferred_y)
        self.allowed_y = tuple(map(float, allowed_y))
        self.preferred_y = tuple(map(float, preferred_y))
        self.state = torch.full(
            (self.num_envs, self.num_strings), DETECTOR_ARMED,
            dtype=torch.int8, device=self.device)
        self.wait_frames = torch.zeros(
            self.num_envs, self.num_strings,
            dtype=torch.long, device=self.device)

    def reset(self, env_ids: torch.Tensor | list[int] | None = None) -> None:
        """Reset all or selected environments to ARMED.

        The caller must also initialize its previous pick snapshot to the
        freshly simulated reset pose.  This explicit boundary prevents stale
        pre-reset positions from creating a fake swept crossing.
        """
        if env_ids is None:
            self.state.fill_(DETECTOR_ARMED)
            self.wait_frames.zero_()
            return
        ids = torch.as_tensor(
            env_ids, dtype=torch.long, device=self.device).reshape(-1)
        if ids.numel() == 0:
            return
        if torch.any(ids < 0) or torch.any(ids >= self.num_envs):
            raise IndexError("detector reset environment index is out of range")
        self.state[ids] = DETECTOR_ARMED
        self.wait_frames[ids] = 0

    def step(
            self,
            previous_tip_g: torch.Tensor,
            current_tip_g: torch.Tensor,
            string_start_g: torch.Tensor,
            string_end_g: torch.Tensor,
            *,
            dt: float = 1.0 / 60.0,
    ) -> dict[str, torch.Tensor]:
        """Detect releases and update the physical re-arm state once."""
        if previous_tip_g.device != self.device:
            raise ValueError(
                f"pick tensors must be on detector device {self.device}")
        if previous_tip_g.shape != (self.num_envs, 3):
            raise ValueError(
                "pick tensors must have shape "
                f"({self.num_envs}, 3), got {tuple(previous_tip_g.shape)}")
        geometry = swept_point_string_segments(
            previous_tip_g, current_tip_g, string_start_g, string_end_g,
            dt=dt, min_across_speed=self.min_across_speed,
            min_depth=self.min_depth,
            parallel_epsilon=self.parallel_epsilon,
            segment_epsilon=self.segment_epsilon,
            allowed_y=self.allowed_y, preferred_y=self.preferred_y)
        if geometry["valid"].shape != (self.num_envs, self.num_strings):
            raise ValueError(
                "string count changed after detector construction: expected "
                f"{self.num_strings}, got {geometry['valid'].shape[1]}")

        armed_before = self.state == DETECTOR_ARMED
        waiting_before = ~armed_before
        release = geometry["valid"] & armed_before
        blocked_wait_rearm = geometry["valid"] & waiting_before

        separation_result = point_to_finite_segments(
            current_tip_g, string_start_g, string_end_g,
            epsilon=self.segment_epsilon)
        separation = separation_result["distance"]
        separation_finite = separation_result["finite"]

        # Count only frames that began in WAIT_REARM.  A release frame starts
        # at zero regardless of how far the endpoint travelled past the line.
        self.wait_frames = torch.where(
            waiting_before, self.wait_frames + 1, self.wait_frames)
        self.state = torch.where(
            release,
            torch.full_like(self.state, DETECTOR_WAIT_REARM),
            self.state)
        self.wait_frames = torch.where(
            release, torch.zeros_like(self.wait_frames), self.wait_frames)

        eligible_rearm = (
            waiting_before
            & separation_finite
            & (self.wait_frames >= self.rearm_min_frames)
            & (separation >= self.rearm_separation))
        self.state = torch.where(
            eligible_rearm,
            torch.full_like(self.state, DETECTOR_ARMED),
            self.state)
        self.wait_frames = torch.where(
            eligible_rearm, torch.zeros_like(self.wait_frames),
            self.wait_frames)

        result: dict[str, Any] = dict(geometry)
        result.update({
            "armed_before": armed_before,
            "release": release,
            "blocked_wait_rearm": blocked_wait_rearm,
            "rearmed": eligible_rearm,
            "separation": separation,
            "detector_state": self.state.clone(),
            "wait_frames": self.wait_frames.clone(),
        })
        return result
