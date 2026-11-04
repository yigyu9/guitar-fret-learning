"""오른팔 6축과 오른손 21축의 직접 목표각을 기존 물리 제어기에 연결한다."""
import copy

import torch

from guitar_learning.core.control import LEFT_ARM_NAMES, RIGHT_GRIP_NAMES, RIGHT_STRIKE_NAMES
from guitar_learning.gpu.control import BatchedController


ACTION_NAMES = LEFT_ARM_NAMES + RIGHT_GRIP_NAMES + RIGHT_STRIKE_NAMES
SCHEMA = 'guitar_learning.right27_control.v1'


class Right27Controller:
    """앞 12축은 비활성이고, 나머지 27축만 정책이 소유한다."""

    def __init__(self, scene, base=None):
        if scene.hand != 'right':
            raise ValueError('Right27 controller requires hand=right')
        self.base = BatchedController(scene) if base is None else base
        self.active = self.base.index([self.base.names.index(n) for n in ACTION_NAMES])
        self.finger_actions = self.base.index(range(12, 33))
        self.finger_indices = self.active[12:33]
        if not set(self.finger_indices.cpu().tolist()) <= set(self.base.position.cpu().tolist()):
            raise ValueError('All right21 joints must retain native POSITION ownership')
        self.action_low = self.base.action_low.clone()
        self.action_high = self.base.action_high.clone()
        self.action_low[12:33] = self.base.lower[self.finger_indices]
        self.action_high[12:33] = self.base.upper[self.finger_indices]
        self.rate = self.base.rate.clone()
        self.rate[self.finger_indices] = 4.
        self.alpha = self.base.alpha.clone()
        self.alpha[12:33] = 1.
        self.finger_action_mode = 'position'
        self.contract = copy.deepcopy(self.base.contract)
        self.contract.update(schema=SCHEMA, action_order=list(ACTION_NAMES),
            active_action_indices=list(range(12, 39)), inactive_action_indices=list(range(12)),
            action_lower_rad=self.action_low.cpu().tolist(),
            action_upper_rad=self.action_high.cpu().tolist(),
            smoothing_alpha=self.alpha.cpu().tolist(), rate_rad_s=self.rate.cpu().tolist(),
            action_codec=dict(schema='guitar_learning.right27_position.v1', mode='position',
                joint_names=list(RIGHT_GRIP_NAMES), action_indices=list(range(12, 33)),
                rate_rad_s=4., control_hz=60, smoothing='bypassed for right21',
                reference='prepared reference105; zero requests reference',
                target_request='signed affine reference-to-native-limit mapping',
                target_update='rate limit previous target by 4/60 then native clamp',
                remaining_actions='right elbow/wrist6 unchanged; first12 exactly zero'))
        self.metadata = self.contract

    def __getattr__(self, name):
        return getattr(self.base, name)

    def targets(self, action, snapshot):
        if (action.shape != (self.base.num_envs, 39) or action.device != self.base.device or
                not torch.isfinite(action).all() or (action.abs() > 1).any() or
                (action[:, :12] != 0).any()):
            raise ValueError('Finite bounded right27 action[N,39] with first12 zero required')
        # 기존 제어기는 RH 목표를 기준각으로 되돌리므로 호출 전에 이전값을 보관한다.
        previous = self.base.target[:, self.finger_indices].clone()
        original = action.clone()
        original[:, :33] = 0
        target = self.base.targets(original, snapshot)
        ref = self.base.reference[self.finger_indices]
        low, high = self.action_low[12:33], self.action_high[12:33]
        command = action[:, 12:33]
        request = ref + torch.where(command >= 0, high-ref, ref-low)*command
        applied = torch.maximum(torch.minimum(request, previous+4./60.), previous-4./60.)
        target[:, self.finger_indices] = torch.maximum(torch.minimum(applied, high), low)
        return target
