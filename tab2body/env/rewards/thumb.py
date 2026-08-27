from __future__ import annotations

import math
from typing import NamedTuple

import torch

from ..collision import THUMB_PAD_BODY
from ..safety import (
    NECK_BACK_Z,
    NECK_BODY_HALF_WIDTH,
    NECK_BODY_Y,
    NECK_NUT_HALF_WIDTH,
    NECK_NUT_Y,
)
from .common import smoothstep01

THUMB_GEOMETRY_OBS_DIM = 6


class NeckBackGeometry(NamedTuple):
    distance: torch.Tensor
    gap: torch.Tensor
    in_region: torch.Tensor
    dx: torch.Tensor
    dy: torch.Tensor


def update_contact_hysteresis(previous, force, on_force=0.5, off_force=0.1):
    """Binary contact with separate on/off thresholds to suppress solver flicker."""
    return (force >= on_force) | (previous & (force > off_force))


def thumb_approach_reward(distance, precision_scale=0.015, reach_scale=0.120):
    """Dense approach shaping that remains useful from the seated initial pose."""
    precision = torch.exp(-((distance / precision_scale) ** 2))
    broad = torch.exp(-((distance / reach_scale) ** 2))
    progress = smoothstep01(1.0 - distance / reach_scale)
    return (
        0.45 * precision + 0.35 * progress + 0.20 * broad
    ).clamp(0.0, 1.0)


def contact_force_quality(force, soft_limit=100.0, decay_scale=500.0):
    """Keep ordinary contact free and smoothly reject solver-force exploits.

    The net rigid-body force is not a pair-specific guitar force, so this is a
    conservative upper-load guard rather than a physical-force target.
    """
    if soft_limit < 0.0 or decay_scale <= 0.0:
        raise ValueError("force soft limit/decay scale must be non-negative/positive")
    excess = (force - soft_limit).clamp_min(0.0)
    return torch.exp(-((excess / decay_scale) ** 2))


def thumb_compression_quality(
        compression, free_depth=0.0005, decay_scale=0.002):
    """Convert neck-back pad overlap into a stable pressure proxy."""
    if free_depth < 0.0 or decay_scale <= 0.0:
        raise ValueError(
            "thumb compression free depth/decay must be non-negative/positive")
    excess = (compression - float(free_depth)).clamp_min(0.0)
    return torch.exp(-((excess / float(decay_scale)) ** 2))


def thumb_geometric_support_quality(
        dx, dy, gap, lateral_scale=0.008, length_scale=0.025,
        target_gap=0.0015, separation_scale=0.006,
        broad_separation_scale=0.020, penetration_scale=0.001):
    """넥 후면 정렬과 표면 간격을 연속적인 접촉 준비도로 바꾼다."""
    scales = (lateral_scale, length_scale, separation_scale,
              broad_separation_scale,
              penetration_scale)
    if any(not math.isfinite(float(value)) or float(value) <= 0.0
           for value in scales):
        raise ValueError("thumb geometric support scales must be positive")
    if not math.isfinite(float(target_gap)) or target_gap < 0.0:
        raise ValueError("thumb geometric support target gap must be non-negative")
    footprint = torch.exp(-(
        (dx / lateral_scale).square() + (dy / length_scale).square()))
    penetration = (-gap).clamp_min(0.0)
    separation = (
        0.70 * torch.exp(-((gap - target_gap) / separation_scale).square())
        + 0.30
        * torch.exp(-((gap - target_gap) / broad_separation_scale).square()))
    penetration_guard = torch.exp(-(
        penetration / penetration_scale).square())
    gap_quality = separation * penetration_guard
    return footprint * gap_quality, footprint, gap_quality


def thumb_support_reward(approach, geometry_ready, support_ready):
    """접근, 후면 정렬, 실제 지지를 하나의 연속 보상으로 묶는다."""
    return (
        0.20 * approach + 0.35 * geometry_ready + 0.45 * support_ready
    ).clamp(0.0, 1.0)


def thumb_press_readiness(approach, geometry_ready, support_ready, goal_gate):
    """압현 중 엄지 준비도를 접촉 전에도 학습 가능한 값으로 만든다."""
    return (
        0.10 * approach * goal_gate
        + 0.35 * geometry_ready
        + 0.55 * support_ready
    ).clamp(0.0, 1.0)


def thumb_press_reward_factor(readiness, goal_gate, weight=0.35):
    """엄지 준비가 부족한 근접 압현만 약하게 제한한다."""
    weight = float(weight)
    if not math.isfinite(weight) or not 0.0 <= weight < 1.0:
        raise ValueError("thumb press gate weight must be in [0, 1)")
    return (
        1.0 - weight * goal_gate * (1.0 - readiness)
    ).clamp(1.0 - weight, 1.0)


def neck_half_width(y):
    """Half-width of the tapered neck at guitar-local y."""
    alpha = ((NECK_NUT_Y - y) / (NECK_NUT_Y - NECK_BODY_Y)).clamp(0.0, 1.0)
    return NECK_NUT_HALF_WIDTH + alpha * (NECK_BODY_HALF_WIDTH - NECK_NUT_HALF_WIDTH)


def neck_back_geometry(samples_local, pad_radius=0.007,
                       region_tolerance=0.006):
    """Return the closest signed error to the tapered neck-back support region.

    ``samples_local`` has shape ``(..., K, 3)`` along the thumb distal segment.
    Positive gap means separation, negative gap means the approximate pad overlaps
    the back plane.  A collision is accepted only near that plane and inside the
    tapered neck footprint, preventing body/side/front contacts from scoring.
    """
    if samples_local.ndim < 2 or samples_local.shape[-1] != 3:
        raise ValueError("thumb samples must have shape (..., K, 3)")
    pad_radius = float(pad_radius)
    region_tolerance = float(region_tolerance)
    if (not math.isfinite(pad_radius) or pad_radius <= 0.0
            or not math.isfinite(region_tolerance)
            or region_tolerance < 0.0):
        raise ValueError(
            "thumb pad radius/tolerance must be finite and positive/non-negative")

    x, y, z = samples_local.unbind(dim=-1)
    y_clamped = y.clamp(NECK_BODY_Y, NECK_NUT_Y)
    dy = y - y_clamped
    width = neck_half_width(y_clamped)
    dx = x - x.clamp(-width, width)
    target_center_z = NECK_BACK_Z - pad_radius
    pad_gap = target_center_z - z
    distance = torch.sqrt(
        dx.square() + dy.square() + pad_gap.square() + 1e-12)
    in_length = (y >= NECK_BODY_Y) & (y <= NECK_NUT_Y)
    in_width = x.abs() <= width
    near_back = pad_gap.abs() <= region_tolerance
    valid_region_by_sample = in_length & in_width & near_back

    best_distance, best_index = distance.min(dim=-1)

    def gather_best(value):
        return torch.gather(
            value, -1, best_index[..., None]).squeeze(-1)

    valid_region = valid_region_by_sample.any(dim=-1)
    return NeckBackGeometry(
        distance=best_distance,
        gap=gather_best(pad_gap),
        in_region=valid_region,
        dx=gather_best(dx),
        dy=gather_best(dy),
    )


def neck_back_metrics(samples_local, pad_radius=0.007, region_tolerance=0.006):
    """Compatibility tuple for neck-back reward and diagnostics."""
    geometry = neck_back_geometry(
        samples_local, pad_radius=pad_radius,
        region_tolerance=region_tolerance)
    return geometry.distance, geometry.gap, geometry.in_region


def thumb_segment_samples(endpoints_local, n_samples=7, sample_alpha=None):
    """Interpolate local points from thumb3 to thumb_top."""
    if (endpoints_local.ndim < 2
            or endpoints_local.shape[-2:] != (2, 3)):
        raise ValueError("thumb endpoints must have shape (..., 2, 3)")
    n_samples = int(n_samples)
    if n_samples < 2:
        raise ValueError("thumb segment requires at least two samples")
    if sample_alpha is None:
        alpha = torch.linspace(
            0.0, 1.0, n_samples,
            dtype=endpoints_local.dtype,
            device=endpoints_local.device)
    else:
        alpha = torch.as_tensor(
            sample_alpha, dtype=endpoints_local.dtype,
            device=endpoints_local.device).reshape(-1)
        if alpha.numel() != n_samples:
            raise ValueError(
                "thumb sample alpha count must match n_samples")
    shape = (1,) * (endpoints_local.ndim - 2) + (n_samples, 1)
    alpha = alpha.view(shape)
    start = endpoints_local[..., 0, :].unsqueeze(-2)
    end = endpoints_local[..., 1, :].unsqueeze(-2)
    return start + alpha * (end - start)


def thumb_geometry_observation(
        endpoints_local, contact, pad_radius=0.007,
        region_tolerance=0.006, n_samples=7, sample_alpha=None):
    """Build normalized signed neck-back geometry plus binary current contact."""
    geometry = neck_back_geometry(
        thumb_segment_samples(
            endpoints_local, n_samples=n_samples,
            sample_alpha=sample_alpha),
        pad_radius=pad_radius, region_tolerance=region_tolerance)
    contact = torch.as_tensor(contact, device=endpoints_local.device)
    if contact.shape != geometry.distance.shape:
        raise ValueError("thumb contact shape must match endpoint batch shape")
    return torch.stack((
        geometry.dx / 0.03,
        geometry.dy / 0.10,
        (geometry.gap + 0.0005) / 0.06,
        geometry.distance / 0.10,
        geometry.in_region.to(endpoints_local.dtype),
        contact.to(endpoints_local.dtype),
    ), dim=-1)


def thumb_base_action_saturation_penalty(
        actions, valid_support, threshold=0.90, weight=0.01):
    """Softly discourage unsupported thumb-base commands near hard limits."""
    if actions.ndim < 1 or actions.shape[-1] != 3:
        raise ValueError("thumb-base actions must have shape (..., 3)")
    valid_support = torch.as_tensor(
        valid_support, device=actions.device)
    if valid_support.shape != actions.shape[:-1]:
        raise ValueError("thumb support shape must match the action batch")
    threshold = float(threshold)
    weight = float(weight)
    if (not math.isfinite(threshold) or not 0.0 <= threshold < 1.0):
        raise ValueError("thumb saturation threshold must be finite and in [0, 1)")
    if not math.isfinite(weight) or weight < 0.0:
        raise ValueError(
            "thumb saturation penalty weight must be finite and non-negative")
    scale = 1.0 - threshold
    excess = ((actions.abs() - threshold) / scale).clamp_min(0.0)
    penalty = weight * excess.square().mean(dim=-1)
    return torch.where(
        valid_support.to(dtype=torch.bool),
        torch.zeros_like(penalty), penalty)


class ThumbSupportReward:
    N_SAMPLES = 7

    def __init__(self, env, pad_radius=0.007, approach_scale=0.015,
                 reach_scale=0.120,
                 contact_on_force=0.5, contact_off_force=0.1,
                 force_soft_limit=50000.0, force_decay_scale=100000.0,
                 compression_free_depth=0.0005,
                 compression_decay_scale=0.002):
        self.env = env
        self.pad_radius = float(pad_radius)
        self.approach_scale = float(approach_scale)
        self.reach_scale = float(reach_scale)
        self.contact_on_force = float(contact_on_force)
        self.contact_off_force = float(contact_off_force)
        self.force_soft_limit = float(force_soft_limit)
        self.force_decay_scale = float(force_decay_scale)
        self.compression_free_depth = float(compression_free_depth)
        self.compression_decay_scale = float(compression_decay_scale)
        if self.pad_radius <= 0 or self.approach_scale <= 0 or self.reach_scale <= 0:
            raise ValueError("thumb pad radius and approach scales must be positive")
        if not 0 <= self.contact_off_force < self.contact_on_force:
            raise ValueError("thumb contact thresholds must satisfy 0 <= off < on")
        if self.force_soft_limit < 0.0 or self.force_decay_scale <= 0.0:
            raise ValueError("thumb force guard values must be non-negative/positive")
        if (self.compression_free_depth < 0.0
                or self.compression_decay_scale <= 0.0):
            raise ValueError(
                "thumb compression values must be non-negative/positive")
        for name in ("LH:thumb3", "LH:thumb_top", THUMB_PAD_BODY):
            if name not in env.hbody_index:
                raise KeyError(f"missing thumb reward body: {name}")
        self._contact = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        self.sample_alpha = torch.linspace(
            0.0, 1.0, self.N_SAMPLES, device=env.device)

    def reset(self, env_ids):
        if env_ids.numel():
            self._contact[env_ids] = False

    def compute(self):
        start = self.env.hbody_pos("LH:thumb3")
        end = self.env.hbody_pos("LH:thumb_top")
        endpoints_local = self.env.to_guitar_frame(
            torch.stack((start, end), dim=1))
        geometry = neck_back_geometry(
            thumb_segment_samples(
                endpoints_local, self.N_SAMPLES, self.sample_alpha),
            pad_radius=self.pad_radius)
        distance = geometry.distance
        gap = geometry.gap
        in_back_region = geometry.in_region

        force = self.env.hbody_contact_force(THUMB_PAD_BODY).norm(dim=-1)
        self._contact = update_contact_hysteresis(
            self._contact, force, self.contact_on_force, self.contact_off_force)
        support = self._contact & in_back_region
        solver_force_quality = contact_force_quality(
            force, self.force_soft_limit, self.force_decay_scale)
        compression = (-gap).clamp_min(0.0)
        compression_quality = thumb_compression_quality(
            compression, self.compression_free_depth,
            self.compression_decay_scale)
        force_quality = compression_quality * solver_force_quality
        approach = thumb_approach_reward(
            distance, precision_scale=self.approach_scale, reach_scale=self.reach_scale)
        support_quality = support.float() * force_quality
        geometric_quality, footprint_quality, gap_quality = (
            thumb_geometric_support_quality(
                geometry.dx, geometry.dy, geometry.gap))
        reward = thumb_support_reward(
            approach, geometric_quality, support_quality)
        return reward, {
            "thumb_reward": reward,
            "thumb_approach_reward": approach,
            "thumb_distance": distance,
            "thumb_gap": gap,
            "thumb_contact_force": force,
            "thumb_contact": self._contact,
            "thumb_in_back_region": in_back_region,
            "thumb_support": support,
            "thumb_force_quality": force_quality,
            "thumb_compression_quality": compression_quality,
            "thumb_solver_force_quality": solver_force_quality,
            "thumb_support_quality": support_quality,
            "thumb_geometric_support_quality": geometric_quality,
            "thumb_footprint_quality": footprint_quality,
            "thumb_gap_quality": gap_quality,
            "thumb_overforce": (
                support.float() * (1.0 - compression_quality)),
            "thumb_solver_overforce": 1.0 - solver_force_quality,
            "thumb_wrong_contact": self._contact & ~in_back_region,
            "thumb_penetration": compression,
            "thumb_compression": compression,
        }
