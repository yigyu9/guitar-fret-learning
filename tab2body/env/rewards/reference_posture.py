"""사람 연주 데이터에서 얻은 약한 왼손 자세 사전분포."""
from __future__ import annotations

import json
import math
from pathlib import Path

import torch


FINGERS = ("index", "middle", "ring", "pinky")


def _axis_angle(quaternion, axis):
    value = quaternion[axis]
    return 2.0 * math.atan2(value, quaternion[3])


def _rotation_vector(quaternion):
    x, y, z, w = (float(value) for value in quaternion)
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-9:
        return 0.0, 0.0, 0.0
    angle = 2.0 * math.atan2(norm, w)
    return angle * x / norm, angle * y / norm, angle * z / norm


def load_reference_postures(path, max_exemplars=64):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"reference motion is missing: {path}")
    data = json.loads(path.read_text())
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("reference motion must contain frames")
    max_exemplars = int(max_exemplars)
    if max_exemplars < 2:
        raise ValueError("reference posture needs at least two exemplars")
    count = min(max_exemplars, len(frames))
    indices = torch.linspace(
        0, len(frames) - 1, count, dtype=torch.float64).round().long()
    finger_rows = []
    thumb_rows = []
    for index in indices.tolist():
        frame = frames[index]
        finger_rows.append([
            _axis_angle(frame[f"LH:{finger}{joint}"], 0)
            for finger in FINGERS for joint in (1, 2, 3)
        ])
        thumb1 = _rotation_vector(frame["LH:thumb1"])
        thumb_rows.append([
            *thumb1,
            _axis_angle(frame["LH:thumb2"], 2),
            _axis_angle(frame["LH:thumb3"], 2),
        ])
    return (torch.tensor(finger_rows, dtype=torch.float32).view(count, 4, 3),
            torch.tensor(thumb_rows, dtype=torch.float32))


class ReferenceHandPosturePrior:
    """활성 압현을 방해하지 않고 비활성 손가락과 엄지의 자세만 제한한다."""

    def __init__(self, env, path, max_exemplars=64, scale_floor_deg=10.0):
        finger, thumb = load_reference_postures(
            path, max_exemplars=max_exemplars)
        self.finger_reference = finger.to(env.device)
        self.thumb_reference = thumb.to(env.device)
        floor = math.radians(float(scale_floor_deg))
        if floor <= 0.0:
            raise ValueError("reference posture scale floor must be positive")
        self.finger_scale = self.finger_reference.std(
            dim=0, unbiased=False).clamp_min(floor)
        self.thumb_scale = self.thumb_reference.std(
            dim=0, unbiased=False).clamp_min(floor)
        finger_names = [
            (f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3")
            for finger in FINGERS
        ]
        thumb_names = (
            "LH:thumb1_x", "LH:thumb1_y", "LH:thumb1_z",
            "LH:thumb2", "LH:thumb3",
        )
        missing = [
            name for names in (*finger_names, thumb_names)
            for name in names if name not in env.dof_names
        ]
        if missing:
            raise KeyError(f"reference posture DOFs are missing: {missing}")
        self.finger_indices = torch.tensor([
            [env.dof_names.index(name) for name in names]
            for names in finger_names
        ], dtype=torch.long, device=env.device)
        self.thumb_indices = torch.tensor([
            env.dof_names.index(name) for name in thumb_names
        ], dtype=torch.long, device=env.device)
        self.env = env

    @staticmethod
    def _nearest_quality(current, reference, scale, feature_mask=None):
        delta = (current[:, None] - reference[None]) / scale
        error = delta.square()
        if feature_mask is None:
            mean_error = error.mean(dim=-1)
        else:
            mask = feature_mask[:, None].to(error.dtype)
            mean_error = (error * mask).sum(dim=-1) / mask.sum(
                dim=-1).clamp_min(1.0)
        return torch.exp(-0.5 * mean_error.amin(dim=1)).clamp(0.0, 1.0)

    def compute(self, active_fingers):
        if active_fingers.shape != (self.env.num_envs, 4):
            raise ValueError("active_fingers must have shape [N,4]")
        q = self.env.dof_state.view(
            self.env.num_envs, self.env.n_dof, 2)[:, :, 0]
        current_finger = q[:, self.finger_indices]
        inactive = (~active_fingers).unsqueeze(-1).expand(-1, -1, 3)
        finger_quality = self._nearest_quality(
            current_finger.flatten(1), self.finger_reference.flatten(1),
            self.finger_scale.flatten(), inactive.flatten(1))
        finger_quality = torch.where(
            inactive.flatten(1).any(dim=1), finger_quality,
            torch.ones_like(finger_quality))
        thumb_quality = self._nearest_quality(
            q[:, self.thumb_indices], self.thumb_reference,
            self.thumb_scale)
        return finger_quality, thumb_quality


class HumanJointRangePrior:
    """기타 연주 데이터 기반 soft range를 벗어난 정도만 계산한다."""

    def __init__(self, env, path, decay_scale_deg=15.0,
                 active_finger_fraction=0.25, thumb_fraction=0.10):
        profile = json.loads(Path(path).read_text(encoding="utf-8"))
        if profile.get("schema") != "tab2body.fret-human-joint-profile.v1":
            raise ValueError("unsupported human joint profile schema")
        joints = profile.get("joints")
        if not isinstance(joints, dict) or not joints:
            raise ValueError("human joint profile must contain joints")
        missing = [name for name in joints if name not in env.dof_names]
        if missing:
            raise KeyError(f"human joint profile DOFs are missing: {missing}")
        self.names = tuple(joints)
        self.indices = torch.tensor(
            [env.dof_names.index(name) for name in self.names],
            dtype=torch.long, device=env.device)
        self.lower = torch.deg2rad(torch.tensor(
            [float(joints[name]["lower_deg"]) for name in self.names],
            device=env.device))
        self.upper = torch.deg2rad(torch.tensor(
            [float(joints[name]["upper_deg"]) for name in self.names],
            device=env.device))
        if not torch.all(self.lower < self.upper):
            raise ValueError("human joint soft ranges must be increasing")
        hard_lower = env.dof_lower[:env.n_dof][self.indices]
        hard_upper = env.dof_upper[:env.n_dof][self.indices]
        if torch.any(self.lower < hard_lower - 1e-6) \
                or torch.any(self.upper > hard_upper + 1e-6):
            raise ValueError("human joint soft range exceeds simulator hard limits")
        self.scale = math.radians(float(decay_scale_deg))
        self.active_finger_fraction = float(active_finger_fraction)
        self.thumb_fraction = float(thumb_fraction)
        if self.scale <= 0.0:
            raise ValueError("human joint range decay scale must be positive")
        if not 0.0 <= self.active_finger_fraction <= 1.0 \
                or not 0.0 <= self.thumb_fraction <= 1.0:
            raise ValueError("human joint range fractions must be in [0, 1]")
        finger_ids = []
        for name in self.names:
            finger_id = -1
            if name.startswith("LH:thumb"):
                finger_id = 0
            else:
                for index, finger in enumerate(FINGERS, start=1):
                    if name.startswith(f"LH:{finger}"):
                        finger_id = index
                        break
            finger_ids.append(finger_id)
        self.finger_ids = torch.tensor(
            finger_ids, dtype=torch.long, device=env.device)
        self.env = env

    def compute(self, active_fingers):
        if active_fingers.shape != (self.env.num_envs, 4):
            raise ValueError("active_fingers must have shape [N,4]")
        q = self.env.dof_state.view(
            self.env.num_envs, self.env.n_dof, 2)[:, self.indices, 0]
        excess = (self.lower[None] - q).clamp_min(0.0) \
            + (q - self.upper[None]).clamp_min(0.0)
        weights = torch.ones_like(excess)
        thumb = self.finger_ids == 0
        weights[:, thumb] = self.thumb_fraction
        for finger_index in range(4):
            selected = self.finger_ids == finger_index + 1
            weights[:, selected] = torch.where(
                active_fingers[:, finger_index, None],
                torch.full_like(weights[:, selected],
                                self.active_finger_fraction),
                torch.ones_like(weights[:, selected]))
        denominator = weights.sum(dim=1).clamp_min(1e-6)
        normalized_error = (
            weights * (excess / self.scale).square()).sum(dim=1) / denominator
        quality = torch.exp(-0.5 * normalized_error).clamp(0.0, 1.0)
        violation_rate = (
            weights * (excess > 0.0).float()).sum(dim=1) / denominator
        max_excess_deg = torch.rad2deg(excess).amax(dim=1)
        return quality, violation_rate, max_excess_deg
