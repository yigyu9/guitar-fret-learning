"""Geometry and temporal filters shared by task safety rules."""
from __future__ import annotations

import torch


NECK_NUT_Y = 0.217197
NECK_BODY_Y = -0.241803
NECK_NUT_HALF_WIDTH = 0.020419
NECK_BODY_HALF_WIDTH = 0.027908
# guitar_neck1/2.obj의 실제 뒤쪽 충돌 표면이다. 이전 -8 mm 값은
# mesh 내부에 있어 엄지 pad 목표와 관통 판정이 물리 충돌과 어긋났다.
NECK_BACK_Z = -0.016777
NECK_FRONT_Z = 0.0093
GUITAR_BODY_CENTER = (0.0, -0.4, -0.0217)
GUITAR_BODY_HALF = (0.15, 0.17, 0.02)
PLUCK_SURFACE_CENTER = (0.0, -0.328, 0.0063)
PLUCK_SURFACE_HALF = (0.028, 0.086, 0.0075)


def dof_torque_limit(name):
    """Conservative per-joint safety cap; normal finger pressing stays well below it."""
    if name.startswith("LH:thumb"):
        return 4.0
    if name.startswith(("LH:", "RH:")):
        return 20.0
    if "Wrist" in name:
        return 60.0
    if "Elbow" in name:
        return 100.0
    if "Shoulder" in name or "Thorax" in name:
        return 150.0
    return 300.0


def _constant_like(points, values):
    return torch.as_tensor(values, dtype=points.dtype, device=points.device)


def box_inside_depth(points, center, half_size):
    """Positive distance to the nearest face for points inside an axis-aligned box."""
    margin = _constant_like(points, half_size) - (
        points - _constant_like(points, center)).abs()
    inside = (margin >= 0.0).all(dim=-1)
    return torch.where(inside, margin.amin(dim=-1), torch.zeros_like(margin[..., 0]))


def tapered_neck_inside_depth(points):
    """Approximate positive inside depth for the closed tapered neck prism."""
    x, y, z = points.unbind(dim=-1)
    alpha = ((NECK_NUT_Y - y) / (NECK_NUT_Y - NECK_BODY_Y)).clamp(0.0, 1.0)
    half_width = NECK_NUT_HALF_WIDTH + alpha * (
        NECK_BODY_HALF_WIDTH - NECK_NUT_HALF_WIDTH)
    margins = torch.stack([
        half_width - x.abs(),
        y - NECK_BODY_Y,
        NECK_NUT_Y - y,
        z - NECK_BACK_Z,
        NECK_FRONT_Z - z,
    ], dim=-1)
    inside = (margins >= 0.0).all(dim=-1)
    return torch.where(inside, margins.amin(dim=-1), torch.zeros_like(x))


def guitar_solid_inside_depth(points):
    """Return maximum inside depth and solid id: 0 neck, 1 body, 2 pluck surface."""
    depths = torch.stack([
        tapered_neck_inside_depth(points),
        box_inside_depth(points, GUITAR_BODY_CENTER, GUITAR_BODY_HALF),
        box_inside_depth(points, PLUCK_SURFACE_CENTER, PLUCK_SURFACE_HALF),
    ], dim=-1)
    return depths.max(dim=-1)


def palm_inward_normal(wrist, index, middle, pinky, eps=1e-8):
    """Return the fixed-sign anatomical palm inward normal and its validity.

    All inputs have shape ``(..., 3)`` in the same coordinate frame.  The
    ordering is deliberately fixed; flipping the sign from the current guitar
    direction would hide the inversion R13 is meant to detect.
    """
    across = index - pinky
    forward = middle - wrist
    raw = torch.linalg.cross(forward, across, dim=-1)
    magnitude = raw.norm(dim=-1)
    valid = magnitude > float(eps)
    normal = raw / magnitude.clamp_min(float(eps)).unsqueeze(-1)
    return normal, valid


def update_consecutive_violation(streak, violation, valid=None):
    """Increment a violation streak, resetting on a safe or invalid frame."""
    active = violation if valid is None else (violation & valid)
    return torch.where(active, streak + 1, torch.zeros_like(streak))


def exclude_thumb_from_generic_penetration(
        depth_by_chain, tunneled_by_chain, termination_by_chain,
        penetration_threshold, thumb_chain_index=1):
    """엄지 체인은 일반 관통 대신 압축·과힘·접촉 위치 규칙에 맡긴다."""
    if (depth_by_chain.ndim != 2
            or tunneled_by_chain.shape != depth_by_chain.shape
            or termination_by_chain.shape != depth_by_chain.shape):
        raise ValueError("penetration chain tensors must share shape [N,C]")
    _, chains = depth_by_chain.shape
    if (not 0 <= int(thumb_chain_index) < chains
            or penetration_threshold <= 0.0):
        raise ValueError("thumb penetration filter thresholds are invalid")
    unsafe_by_chain = (
        (depth_by_chain > float(penetration_threshold))
        | tunneled_by_chain.bool())
    unsafe_by_chain = unsafe_by_chain.clone()
    termination_by_chain = termination_by_chain.bool().clone()
    raw_thumb_unsafe = unsafe_by_chain[:, int(thumb_chain_index)].clone()
    unsafe_by_chain[:, int(thumb_chain_index)] = False
    termination_by_chain[:, int(thumb_chain_index)] = False
    effective_depth = depth_by_chain.clone()
    effective_depth[:, int(thumb_chain_index)] = 0.0
    return {
        "raw_thumb_unsafe": raw_thumb_unsafe,
        "effective_depth": effective_depth.amax(dim=-1),
        "unsafe_by_chain": unsafe_by_chain,
        "unsafe": unsafe_by_chain.any(dim=-1),
        "termination_by_chain": termination_by_chain,
        "termination": termination_by_chain.any(dim=-1),
    }


def wrist_box_violation(local_wrist, bounds_min, bounds_max):
    """Return per-axis and aggregate violations of a guitar-local safety box."""
    lo = _constant_like(local_wrist, bounds_min)
    hi = _constant_like(local_wrist, bounds_max)
    if lo.shape[-1] != 3 or hi.shape[-1] != 3:
        raise ValueError("wrist safety bounds must be ordered xyz triples")
    ordered = (lo < hi).all()
    # Runtime monitors validate their tuple bounds once in __init__.  Rechecking
    # their constant CUDA tensor here would synchronize every control frame.
    if local_wrist.device.type == "cpu" and not bool(ordered):
        raise ValueError("wrist safety bounds must be ordered xyz triples")
    by_axis = (local_wrist < lo) | (local_wrist > hi)
    return by_axis, by_axis.any(dim=-1)


def finger_back_limit_violation(local_samples, limit_z=-0.050,
                                min_fraction=0.25):
    """Return robust per-finger violations of the sampled-link back plane."""
    if local_samples.shape[-1] != 3:
        raise ValueError("finger back-limit samples must end in xyz")
    if not 0.0 < float(min_fraction) <= 1.0:
        raise ValueError("R8 minimum sample fraction must be in (0, 1]")
    fraction = (local_samples[..., 2] < float(limit_z)).flatten(2).float().mean(dim=-1)
    by_finger = fraction >= float(min_fraction)
    return by_finger, by_finger.any(dim=-1), fraction


class WristSafetyBoxMonitor:
    """R7 hard termination outside a deliberately broad guitar-local box."""

    def __init__(self, env, bounds_min=(-0.20, -0.35, -0.30),
                 bounds_max=(0.30, 0.35, 0.25), frames=3):
        self.env = env
        self.bounds_min = tuple(float(x) for x in bounds_min)
        self.bounds_max = tuple(float(x) for x in bounds_max)
        self.frames = int(frames)
        if len(self.bounds_min) != 3 or len(self.bounds_max) != 3:
            raise ValueError("R7 wrist bounds must contain three coordinates")
        if any(lo >= hi for lo, hi in zip(self.bounds_min, self.bounds_max)):
            raise ValueError("R7 wrist bounds must be strictly ordered")
        if self.frames < 1:
            raise ValueError("R7 wrist safety frames must be at least 1")
        self.streak = torch.zeros(
            env.num_envs, dtype=torch.long, device=env.device)

    def reset(self, env_ids):
        if env_ids.numel():
            self.streak[env_ids] = 0

    def compute(self):
        local = self.env.to_guitar_frame(
            self.env.hbody_pos("L_Wrist")[:, None])[:, 0]
        by_axis, violation = wrist_box_violation(
            local, self.bounds_min, self.bounds_max)
        self.streak.copy_(update_consecutive_violation(self.streak, violation))
        termination = self.streak >= self.frames
        return {
            "wrist_safety_local_position": local,
            "wrist_safety_violation_by_axis": by_axis,
            "wrist_safety_violation": violation,
            "wrist_safety_streak": self.streak.clone(),
            "wrist_safety_termination": termination,
        }


class FingerBackLimitMonitor:
    """비엄지 손가락이 넥 뒤로 우회하는 동작을 감점하고 종료한다."""

    FINGERS = ("index", "middle", "ring", "pinky")

    def __init__(self, env, limit_z=-0.050, proximal_limit_z=None,
                 soft_limit_z=-0.035, proximal_soft_limit_z=None,
                 soft_scale=0.015, frames=3,
                 samples_per_segment=5, min_fraction=0.25):
        self.env = env
        self.limit_z = float(limit_z)
        self.proximal_limit_z = (
            self.limit_z - 0.010 if proximal_limit_z is None
            else float(proximal_limit_z))
        self.soft_limit_z = float(soft_limit_z)
        self.proximal_soft_limit_z = (
            0.5 * (self.proximal_limit_z + self.soft_limit_z)
            if proximal_soft_limit_z is None
            else float(proximal_soft_limit_z))
        self.soft_scale = float(soft_scale)
        self.frames = int(frames)
        self.samples_per_segment = int(samples_per_segment)
        self.min_fraction = float(min_fraction)
        if not (self.proximal_limit_z < self.proximal_soft_limit_z
                < self.soft_limit_z
                and self.proximal_limit_z < self.limit_z
                < self.soft_limit_z):
            raise ValueError(
                "R8 hard limits must be behind their soft limits")
        if self.soft_scale <= 0.0:
            raise ValueError("R8 soft scale must be positive")
        if self.frames < 1 or self.samples_per_segment < 2:
            raise ValueError("R8 frames>=1 and samples_per_segment>=2 are required")
        if not 0.0 < self.min_fraction <= 1.0:
            raise ValueError("R8 minimum sample fraction must be in (0, 1]")
        self.chains = tuple(
            tuple([f"LH:{finger}{i}" for i in range(1, 4)]
                  + [f"LH:{finger}_top"])
            for finger in self.FINGERS)
        missing = sorted({name for chain in self.chains for name in chain}
                         - set(env.hbody_index))
        if missing:
            raise KeyError(f"missing R8 finger bodies: {missing}")
        self.alpha = torch.linspace(
            0.0, 1.0, self.samples_per_segment,
            device=env.device).view(1, 1, 1, -1, 1)
        # Debounce each finger independently.  Alternating one-frame excursions
        # by different fingers must not add up to a three-frame violation.
        self.streak = torch.zeros(
            env.num_envs, len(self.FINGERS), dtype=torch.long, device=env.device)

    def reset(self, env_ids):
        if env_ids.numel():
            self.streak[env_ids] = 0

    def compute(self):
        points = torch.stack([
            torch.stack([self.env.hbody_pos(name) for name in chain], dim=1)
            for chain in self.chains
        ], dim=1)  # N x four fingers x four chain points x xyz
        starts, ends = points[:, :, :-1], points[:, :, 1:]
        world_samples = (starts[:, :, :, None]
                         + self.alpha * (ends - starts)[:, :, :, None])
        flat = world_samples.flatten(1, 3)
        local = self.env.to_guitar_frame(flat).reshape_as(world_samples)
        proximal_fraction = (
            local[:, :, :2, :, 2] < self.proximal_limit_z
        ).flatten(2).float().mean(dim=-1)
        distal_fraction = (
            local[:, :, 2:, :, 2] < self.limit_z
        ).flatten(2).float().mean(dim=-1)
        by_finger = (
            (proximal_fraction >= self.min_fraction)
            | (distal_fraction >= self.min_fraction))
        violation = by_finger.any(dim=-1)
        fraction_by_finger = torch.maximum(
            proximal_fraction, distal_fraction)
        proximal_depth = (
            self.proximal_soft_limit_z - local[:, :, :2, :, 2]
        ).clamp_min(0.0)
        distal_depth = (
            self.soft_limit_z - local[:, :, 2:, :, 2]
        ).clamp_min(0.0)
        proximal_soft_depth_by_finger = (
            proximal_depth.square().flatten(2).mean(dim=-1).sqrt())
        soft_depth_by_finger = distal_depth.square().flatten(2).mean(
            dim=-1).sqrt()
        combined_soft_depth_by_finger = torch.maximum(
            proximal_soft_depth_by_finger, soft_depth_by_finger)
        soft_penalty_by_finger = (
            1.0 - torch.exp(
                -((combined_soft_depth_by_finger / self.soft_scale) ** 2))
        ).clamp(0.0, 1.0)
        soft_penalty = soft_penalty_by_finger.amax(dim=-1)
        self.streak.copy_(update_consecutive_violation(self.streak, by_finger))
        termination_by_finger = self.streak >= self.frames
        termination = termination_by_finger.any(dim=-1)
        return {
            "finger_back_min_local_z": local[..., 2].flatten(2).amin(dim=-1),
            "finger_back_proximal_min_local_z":
                local[:, :, :2, :, 2].flatten(2).amin(dim=-1),
            "finger_back_distal_min_local_z":
                local[:, :, 2:, :, 2].flatten(2).amin(dim=-1),
            "finger_back_fraction_by_finger": fraction_by_finger,
            "finger_back_proximal_fraction_by_finger": proximal_fraction,
            "finger_back_distal_fraction_by_finger": distal_fraction,
            "finger_back_soft_depth_by_finger": soft_depth_by_finger,
            "finger_back_proximal_soft_depth_by_finger":
                proximal_soft_depth_by_finger,
            "finger_back_soft_penalty_by_finger": soft_penalty_by_finger,
            "finger_back_soft_penalty": soft_penalty,
            "finger_back_violation_by_finger": by_finger,
            "finger_back_violation": violation,
            "finger_back_streak": self.streak.clone(),
            "finger_back_termination_by_finger": termination_by_finger,
            "finger_back_termination": termination,
        }


def point_segment_distance(point, start, end):
    """Euclidean distance from broadcast points to finite line segments."""
    segment = end - start
    denom = segment.square().sum(dim=-1).clamp_min(1e-12)
    t = ((point - start) * segment).sum(dim=-1) / denom
    closest = start + t.clamp(0.0, 1.0)[..., None] * segment
    return (point - closest).norm(dim=-1)


def segment_segment_distance(start_a, end_a, start_b, end_b):
    """Exact minimum centerline distance for broadcast 3-D finite segments."""
    u = end_a - start_a
    v = end_b - start_b
    w = start_a - start_b
    a = (u * u).sum(dim=-1)
    b = (u * v).sum(dim=-1)
    c = (v * v).sum(dim=-1)
    d = (u * w).sum(dim=-1)
    e = (v * w).sum(dim=-1)
    denom = a * c - b * b
    safe = denom.abs() > 1e-12
    safe_denom = torch.where(safe, denom, torch.ones_like(denom))
    s = (b * e - c * d) / safe_denom
    t = (a * e - b * d) / safe_denom
    interior = safe & (s >= 0.0) & (s <= 1.0) & (t >= 0.0) & (t <= 1.0)
    interior_distance = (
        (start_a + s[..., None] * u) - (start_b + t[..., None] * v)
    ).norm(dim=-1)
    endpoint_distance = torch.stack([
        point_segment_distance(start_a, start_b, end_b),
        point_segment_distance(end_a, start_b, end_b),
        point_segment_distance(start_b, start_a, end_a),
        point_segment_distance(end_b, start_a, end_a),
    ], dim=-1).amin(dim=-1)
    return torch.where(interior, interior_distance, endpoint_distance)


class FingerSelfIntersectionMonitor:
    """R22 diagnostic-only capsule proxy for inter-finger intersections.

    Mesh self-collision remains disabled.  Each of the five fingers is represented
    by its three joint-to-joint centerline segments.  The proxy deliberately has
    no reward or termination side effect until rollout distributions calibrate it.
    """
    FINGERS = ("thumb", "index", "middle", "ring", "pinky")

    def __init__(self, env, capsule_radius=0.006, overlap_tolerance=0.002):
        self.env = env
        self.capsule_radius = float(capsule_radius)
        self.overlap_tolerance = float(overlap_tolerance)
        if self.capsule_radius <= 0.0 or self.overlap_tolerance < 0.0:
            raise ValueError("R22 capsule radius must be positive and tolerance non-negative")
        self.chains = tuple(
            tuple([f"LH:{finger}{i}" for i in range(1, 4)]
                  + [f"LH:{finger}_top"])
            for finger in self.FINGERS)
        missing = sorted({name for chain in self.chains for name in chain}
                         - set(env.hbody_index))
        if missing:
            raise KeyError(f"missing R22 finger bodies: {missing}")
        self.pairs = tuple(
            (i, j) for i in range(len(self.FINGERS))
            for j in range(i + 1, len(self.FINGERS)))
        self.pair_names = tuple(
            f"{self.FINGERS[i]}-{self.FINGERS[j]}" for i, j in self.pairs)
        self.streak = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)

    def reset(self, env_ids):
        if env_ids.numel():
            self.streak[env_ids] = 0

    def _points(self):
        return torch.stack([
            torch.stack([self.env.hbody_pos(name) for name in chain], dim=1)
            for chain in self.chains
        ], dim=1)  # N x five fingers x four points x xyz

    def compute(self, progress_buf):
        points = self._points()
        pair_center_distance = []
        for finger_a, finger_b in self.pairs:
            a0 = points[:, finger_a, :-1, None]
            a1 = points[:, finger_a, 1:, None]
            b0 = points[:, finger_b, None, :-1]
            b1 = points[:, finger_b, None, 1:]
            distance = segment_segment_distance(a0, a1, b0, b1)
            pair_center_distance.append(distance.amin(dim=(1, 2)))
        pair_center_distance = torch.stack(pair_center_distance, dim=-1)
        pair_surface_gap = pair_center_distance - 2.0 * self.capsule_radius
        pair_penetration = (-pair_surface_gap).clamp_min(0.0)
        pair_overlap = pair_penetration > self.overlap_tolerance
        any_overlap = pair_overlap.any(dim=-1)
        self.streak.copy_(update_consecutive_violation(self.streak, any_overlap))
        return {
            "finger_pair_surface_gap": pair_surface_gap,
            "finger_pair_penetration": pair_penetration,
            "finger_pair_overlap": pair_overlap,
            "finger_min_surface_gap": pair_surface_gap.amin(dim=-1),
            "finger_max_penetration": pair_penetration.amax(dim=-1),
            "finger_overlapping_pair_count": pair_overlap.sum(dim=-1),
            "finger_intersection_streak": self.streak.clone(),
            "finger_initial_overlap": (progress_buf <= 1) & any_overlap,
        }


class ContactLoadMonitor:
    """R24 diagnostic-only body contact and controlled-joint load recorder.

    Isaac Gym exposes net force per rigid body, not a reliable contact-pair label.
    Therefore these are deliberately raw anatomical channels.  They support
    rollout calibration but never imply that a force came from the guitar.
    """
    FINGERS = ("thumb", "index", "middle", "ring", "pinky")
    SUPPORT_BODIES = ("LH:palm", "L_Wrist", "L_Elbow")

    def __init__(self, env):
        self.env = env
        self.distal_bodies = tuple(f"LH:{finger}3" for finger in self.FINGERS)
        self.middle_bodies = tuple(f"LH:{finger}2" for finger in self.FINGERS)
        self.proximal_bodies = tuple(f"LH:{finger}1" for finger in self.FINGERS)
        required = set(self.distal_bodies + self.middle_bodies
                       + self.proximal_bodies + self.SUPPORT_BODIES)
        missing = sorted(required - set(env.hbody_index))
        if missing:
            raise KeyError(f"missing R24 contact-load bodies: {missing}")

    def _force_norms(self, names):
        return torch.stack([
            self.env.hbody_contact_force(name).norm(dim=-1) for name in names
        ], dim=-1)

    def compute(self, goal):
        distal = self._force_norms(self.distal_bodies)
        middle = self._force_norms(self.middle_bodies)
        proximal = self._force_norms(self.proximal_bodies)
        support = self._force_norms(self.SUPPORT_BODIES)

        finger_numbers = torch.arange(1, 5, device=self.env.device).view(1, 1, 4)
        active_fretting = (
            (goal["fret"] > 0)[..., None]
            & (goal["finger"].long()[..., None] == finger_numbers)
        ).any(dim=1)
        target_distal = distal[:, 1:] * active_fretting.float()
        inactive_distal = distal[:, 1:] * (~active_fretting).float()

        torque = self.env.applied_tau[:, self.env.ctrl_idx].abs()
        torque_limit = self.env.tau_limit.view(
            self.env.num_envs, self.env.n_dof)[:, self.env.ctrl_idx]
        torque_fraction = torque / torque_limit.clamp_min(1e-8)
        return {
            "r24_distal_contact_force": distal,
            "r24_middle_contact_force": middle,
            "r24_proximal_contact_force": proximal,
            "r24_support_contact_force": support,
            "r24_target_distal_force": target_distal,
            "r24_inactive_distal_force": inactive_distal,
            "r24_active_fretting_finger": active_fretting,
            "r24_control_torque": torque,
            "r24_control_torque_fraction": torque_fraction,
            "r24_max_control_torque": torque.amax(dim=-1),
            "r24_max_control_torque_fraction": torque_fraction.amax(dim=-1),
        }


class GuitarPenetrationMonitor:
    """GPU diagnostic for deep left-arm/hand entry into analytical guitar solids.

    This intentionally starts as a monitor.  Physics collision remains the primary
    prevention layer; termination should only be enabled after rollout depth
    distributions show that the threshold does not reject valid fretting contact.
    """
    CHAINS = (
        ("L_Shoulder", "L_Elbow", "L_Wrist", "LH:palm"),
        ("LH:palm", "LH:thumb1", "LH:thumb2", "LH:thumb3", "LH:thumb_top"),
        ("LH:palm", "LH:index1", "LH:index2", "LH:index3", "LH:index_top"),
        ("LH:palm", "LH:middle1", "LH:middle2", "LH:middle3", "LH:middle_top"),
        ("LH:palm", "LH:ring1", "LH:ring2", "LH:ring3", "LH:ring_top"),
        ("LH:palm", "LH:pinky1", "LH:pinky2", "LH:pinky3", "LH:pinky_top"),
    )
    CHAIN_NAMES = ("arm", "thumb", "index", "middle", "ring", "pinky")

    def __init__(self, env, threshold=0.005, frames=3, spatial_samples=4,
                 temporal_samples=9, termination_enabled=False):
        self.env = env
        self.threshold = float(threshold)
        self.frames = int(frames)
        self.termination_enabled = bool(termination_enabled)
        if self.threshold <= 0.0 or self.frames < 1:
            raise ValueError("penetration threshold must be positive and frames >= 1")
        if spatial_samples < 2 or temporal_samples < 2:
            raise ValueError("penetration spatial/temporal samples must be >= 2")
        missing = sorted({name for chain in self.CHAINS for name in chain}
                         - set(env.hbody_index))
        if missing:
            raise KeyError(f"missing R14 penetration bodies: {missing}")
        self._spatial_alpha = torch.linspace(
            0.0, 1.0, int(spatial_samples), device=env.device).view(1, -1, 1)
        self._temporal_alpha = torch.linspace(
            0.0, 1.0, int(temporal_samples), device=env.device).view(1, -1, 1, 1)
        samples_per_chain = tuple(
            (len(chain) - 1) * int(spatial_samples)
            for chain in self.CHAINS)
        self.n_samples = sum(samples_per_chain)
        self._point_chain = torch.repeat_interleave(
            torch.arange(len(self.CHAINS), device=env.device),
            torch.tensor(samples_per_chain, device=env.device))
        self.previous_local = torch.zeros(
            env.num_envs, self.n_samples, 3, device=env.device)
        self.has_previous = torch.zeros(
            env.num_envs, dtype=torch.bool, device=env.device)
        self.streak = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)
        self.chain_streak = torch.zeros(
            env.num_envs, len(self.CHAINS),
            dtype=torch.long, device=env.device)

    def reset(self, env_ids):
        if env_ids.numel():
            self.previous_local[env_ids] = 0.0
            self.has_previous[env_ids] = False
            self.streak[env_ids] = 0
            self.chain_streak[env_ids] = 0

    def _sample_world(self):
        segments = []
        for chain in self.CHAINS:
            for start_name, end_name in zip(chain[:-1], chain[1:]):
                start = self.env.hbody_pos(start_name)
                end = self.env.hbody_pos(end_name)
                segments.append(start[:, None] + self._spatial_alpha * (end - start)[:, None])
        return torch.cat(segments, dim=1)

    def current_depth_by_chain(self):
        """Return current analytical penetration depth for every chain.

        This query is side-effect free so actor observations can use a compact
        safety margin without advancing the monitor's temporal debounce state.
        """
        current = self.env.to_guitar_frame(self._sample_world())
        depth_by_point, _ = guitar_solid_inside_depth(current)
        return torch.stack([
            depth_by_point[:, self._point_chain == chain].amax(dim=-1)
            for chain in range(len(self.CHAINS))
        ], dim=-1)

    def compute(self, progress_buf):
        current = self.env.to_guitar_frame(self._sample_world())
        current_depth_by_point, current_solid_by_point = guitar_solid_inside_depth(current)
        current_depth, current_point = current_depth_by_point.max(dim=-1)
        current_depth_by_chain = torch.stack([
            current_depth_by_point[:, self._point_chain == chain].amax(dim=-1)
            for chain in range(len(self.CHAINS))
        ], dim=-1)
        current_solid = torch.gather(
            current_solid_by_point, 1, current_point[:, None]).squeeze(1)
        current_chain = self._point_chain[current_point]

        swept_points = (self.previous_local[:, None]
                        + self._temporal_alpha * (current - self.previous_local)[:, None])
        swept_depth_by_time_point, _ = guitar_solid_inside_depth(swept_points)
        swept_depth_by_point = swept_depth_by_time_point.max(dim=1).values
        swept_depth = swept_depth_by_point.max(dim=-1).values
        swept_depth = torch.where(self.has_previous, swept_depth, current_depth)

        previous_depth_by_point, _ = guitar_solid_inside_depth(self.previous_local)
        tunneled_by_point = ((previous_depth_by_point <= 0.0)
                             & (current_depth_by_point <= 0.0)
                             & (swept_depth_by_point > self.threshold))
        tunneled = self.has_previous & tunneled_by_point.any(dim=-1)
        tunneled_by_chain = torch.stack([
            tunneled_by_point[:, self._point_chain == chain].any(dim=-1)
            for chain in range(len(self.CHAINS))
        ], dim=-1)
        tunneled_by_chain &= self.has_previous[:, None]
        violation = current_depth > self.threshold
        violation_by_chain = current_depth_by_chain > self.threshold
        self.streak.copy_(update_consecutive_violation(self.streak, violation))
        self.chain_streak.copy_(update_consecutive_violation(
            self.chain_streak, violation_by_chain))
        termination_by_chain = (
            self.termination_enabled
            & ((self.chain_streak >= self.frames) | tunneled_by_chain))
        termination = (self.termination_enabled
                       & termination_by_chain.any(dim=-1))
        initial_overlap = (~self.has_previous) & (progress_buf <= 1) & violation

        self.previous_local.copy_(current)
        self.has_previous.fill_(True)
        return {
            "guitar_penetration_depth": current_depth,
            "guitar_penetration_depth_by_chain": current_depth_by_chain,
            "guitar_swept_penetration_depth": swept_depth,
            "guitar_penetration_point": current_point,
            "guitar_penetration_chain": current_chain,
            "guitar_penetration_solid": current_solid,
            "guitar_penetration_streak": self.streak.clone(),
            "guitar_penetration_streak_by_chain": self.chain_streak.clone(),
            "guitar_penetration": violation,
            "guitar_tunneled": tunneled,
            "guitar_tunneled_by_chain": tunneled_by_chain,
            "guitar_initial_overlap": initial_overlap,
            "guitar_penetration_termination": termination,
            "guitar_penetration_termination_by_chain":
                termination_by_chain,
        }
