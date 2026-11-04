"""기존 유한 지지 제어의 목표각에 전신 37축 잔차를 더한다.

잔차는 관절 목표에만 적용한다. 물리 상태·PD·힘 상한은 기존 제어기를 따른다.
발 IK의 반복 시작점과 정책을 더한 구동 목표를 분리하여 잔차 누적을 막는다.
"""
import copy

import torch

from guitar_learning.core.control import (
    HEAD_HELD_NAMES, LEFT_ARM_NAMES, LEFT_HAND_NAMES, RIGHT_GRIP_NAMES,
    RIGHT_STRIKE_NAMES, SUPPORT_HELD_NAMES,
)
from guitar_learning.gpu.control import BatchedController


LOWER_ACTION_NAMES = tuple(
    side+'_'+part+'_'+axis
    for side in ('L', 'R')
    for part, axes in (('Hip', 'xyz'), ('Knee', 'x'), ('Ankle', 'xyz'), ('Toe', 'x'))
    for axis in axes
)
ACTION_NAMES = SUPPORT_HELD_NAMES + HEAD_HELD_NAMES + LOWER_ACTION_NAMES
ZERO_NAMES = tuple(side+'_'+part+'_'+axis
                   for side in ('L', 'R') for part in ('Knee', 'Toe') for axis in 'yz')
SCHEMA = 'guitar_learning.whole_body_control.v1'
RESIDUAL_LIMIT_RAD = .10


class WholeBodyController:
    """상태 전용 정책의 37개 행동을 기존 native105 구동기에 배치한다."""

    def __init__(self, scene, base=None):
        if scene.hand != 'left':
            raise ValueError('Whole-body controller requires the left-hand baseline scene')
        self.base = BatchedController(scene) if base is None else base
        groups = tuple(map(set, (LEFT_ARM_NAMES + LEFT_HAND_NAMES,
                                RIGHT_GRIP_NAMES + RIGHT_STRIKE_NAMES,
                                ACTION_NAMES, ZERO_NAMES)))
        names = tuple(self.base.names)
        if (tuple(map(len, groups)) != (33, 27, 37, 8) or
                len(set().union(*groups)) != 105 or len(names) != 105 or
                set(names) != set().union(*groups)):
            raise ValueError('Exact disjoint left33/right27/body37/zero8 native105 partition required')
        expected_zero = {names.index(name) for name in ZERO_NAMES}
        actual_zero = set((self.base.lower == self.base.upper).nonzero().flatten().cpu().tolist())
        if (set(self.base.zero.cpu().tolist()) != expected_zero or actual_zero != expected_zero):
            raise ValueError('Original knee/toe zero-range8 ownership required')
        self.active = self.base.index([names.index(name) for name in ACTION_NAMES])
        self.baseline_target = self.base.target.clone()
        self._zero_action = torch.zeros(self.base.num_envs, 39,
                                       device=self.base.device, dtype=self.base.dtype)
        self.contract = dict(
            schema=SCHEMA, action_dim=37, target_dim=105,
            joint_names=list(names), action_order=list(ACTION_NAMES),
            action_indices=self.active.cpu().tolist(),
            action_meaning='bounded residual on the existing finite-support baseline target',
            residual_limit_rad=RESIDUAL_LIMIT_RAD, control_hz=60, physics_hz=240,
            rate_rad_s=self.base.rate.cpu().tolist(),
            native_lower_rad=self.base.lower.cpu().tolist(),
            native_upper_rad=self.base.upper.cpu().tolist(),
            target_request='baseline_target + 0.10 * action on body37; other axes unchanged',
            target_update='native clamp, rate limit from previous applied target, native clamp',
            baseline_memory='previous baseline target only; excludes policy residual',
            zero_action='return to the evolving finite-support baseline, rate limited',
            baseline_control=copy.deepcopy(self.base.contract),
        )
        self.metadata = self.contract

    def __getattr__(self, name):
        return getattr(self.base, name)

    def targets(self, action, snapshot):
        if (not isinstance(action, torch.Tensor) or not action.is_floating_point() or
                action.shape != (self.base.num_envs, 37) or action.device != self.base.device or
                not torch.isfinite(action).all() or (action.abs() > 1).any()):
            raise ValueError('Finite bounded device-aligned whole-body action[N,37] required')
        previous = self.base.target[:, self.active].clone()
        # 발 IK는 이전 정책 잔차를 다시 기준으로 삼아서는 안 된다.
        self.base.target.copy_(self.baseline_target)
        target = self.base.targets(self._zero_action, snapshot)
        self.baseline_target.copy_(target)
        low, high = self.base.lower[self.active], self.base.upper[self.active]
        request = target[:, self.active] + RESIDUAL_LIMIT_RAD * action
        request = torch.maximum(torch.minimum(request, high), low)
        step = self.base.rate[self.active] / 60.
        applied = torch.maximum(torch.minimum(request, previous+step), previous-step)
        target[:, self.active] = torch.maximum(torch.minimum(applied, high), low)
        return target

    def reset(self, indices, snapshot):
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.base.device).flatten()
        self.base.reset(indices, snapshot)
        self.baseline_target[indices] = self.base.target[indices]
