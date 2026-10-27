"""Process-local v25 bindings; existing source files are never patched on disk."""
import copy
import math
from contextlib import contextmanager
from unittest.mock import patch

import torch

from guitar_learning.gpu.control import BatchedController
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.geometry import conjugate, multiply, rotvec
from guitar_learning.skills.finger_skill_policy import FingerSkillPolicy
from guitar_learning.training.policy import Encoder


SPEC = dict(schema='guitar_learning.active_press.v25', active_axes=33,
            arm_initial_std=.10, hold_ticks=3, thumb='reference_position',
            wrist_margin_m=.03, wrist_duration_s=.75, initial_grace_s=3.,
            transition_grace_s=.35, transition_center_change_m=.01,
            severe_wrist_margin_m=.10)
TIMER_FIELDS = ('wrist_exit.continuous_s', 'wrist_exit.grace_remaining_s')


class ActiveController(BatchedController):
    def __init__(self, scene, **kwargs):
        super().__init__(scene, **kwargs)
        if scene.hand != 'left' or self.finger_action_mode != 'incremental':
            raise ValueError('v25 requires left incremental finger control')
        # Removing thumb from the incremental set selects the existing native-
        # bounded affine position path, with LH alpha1/rate4 preserved.
        self.incremental_actions = self.finger_actions[5:]
        self.contract['schema'] = 'guitar_learning.gpu_active_press_control.v25'
        self.contract['action_codec'].update(
            schema='guitar_learning.thumb_position_fingers_incremental.v25',
            incremental_action_indices=self.incremental_actions.cpu().tolist(),
            thumb_action_indices=self.finger_actions[:5].cpu().tolist(),
            thumb_mode='reference_position', thumb_zero='request prepared reference target',
            thumb_request='native-bounded sign-asymmetric affine offset from prepared reference',
            thumb_rate_rad_s=4., nonthumb_mode='incremental',
            target_update='nonthumb: previous+action*4/60; thumb: bounded reference position, rate4',
            zero_action='nonthumb: hold previous target; thumb: request prepared reference')


class ActivePolicy(FingerSkillPolicy):
    schema = 'guitar_learning.active_press_policy.v25'

    def __init__(self, *args, **kwargs):
        if kwargs.get('phase') != 'J':
            raise ValueError('v25 learns all33 axes from the first decision')
        super().__init__(*args, **kwargs)
        fields = self.architecture['contract']['observation']['fields']
        if any(name not in fields for name in TIMER_FIELDS):
            raise ValueError('v25 requires explicit wrist exit and grace timer observations')
        self.architecture['support_fields'] += list(TIMER_FIELDS)
        self.support_indices = torch.cat((self.support_indices,
            torch.tensor([fields.index(name) for name in TIMER_FIELDS], device=self.support_indices.device)))
        self.support_encoder = Encoder(len(self.support_indices), 9, self.architecture['fusion'], priority_count=8)
        with torch.no_grad():
            self.support_log_std[:12] = math.log(SPEC['arm_initial_std'])
        self.architecture['active_press'] = copy.deepcopy(SPEC)


class WristExitState:
    """240Hz row-local timers, preserved across PPO cuts and selected resets."""
    def __init__(self, count, device):
        self.outside_s = torch.zeros(count, dtype=torch.float64, device=device)
        self.max_outside_s = self.outside_s.clone()
        self.grace_until = self.outside_s.clone()
        self.center = torch.zeros(count, 3, device=device)
        self.failed = torch.zeros(count, dtype=torch.bool, device=device)

    def reset(self, indices, center):
        self.outside_s[indices] = 0
        self.max_outside_s[indices] = 0
        self.grace_until[indices] = SPEC['initial_grace_s']
        self.center[indices] = center[indices]
        self.failed[indices] = False

    def step(self, delta, center, local_time):
        moved = (center-self.center).abs().amax(-1) >= SPEC['transition_center_change_m']
        self.grace_until = torch.where(moved,
            torch.maximum(self.grace_until, local_time+SPEC['transition_grace_s']), self.grace_until)
        self.center = torch.where(moved[:, None], center, self.center)
        enabled = local_time > self.grace_until
        excess = delta.abs().amax(-1)
        self.outside_s = torch.where(enabled & (excess > SPEC['wrist_margin_m']),
            self.outside_s+1/240., torch.zeros_like(self.outside_s))
        self.max_outside_s = torch.maximum(self.max_outside_s, self.outside_s)
        severe = (local_time > SPEC['initial_grace_s']) & (excess > SPEC['severe_wrist_margin_m'])
        self.failed |= severe | (self.outside_s+1e-12 >= SPEC['wrist_duration_s'])
        return self.failed


class ActiveEnvironment(FingerSkillEnvironment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.phase != 'J':
            raise ValueError('v25 has no R/F preparation gate')
        self.contract['task']['active_press'] = copy.deepcopy(SPEC)
        observation = self.contract['observation']
        observation['fields'][-5:-5] = list(TIMER_FIELDS)
        observation['scales'][-5:-5] = [SPEC['wrist_duration_s'], SPEC['initial_grace_s']]
        observation['dimension'] += len(TIMER_FIELDS)
        self.scales = self._tensor(observation['scales'])
        self.contract['reward']['schema'] = 'guitar_learning.active_press_reward.v25'
        self.contract['reward']['active_press'] = dict(wrist_continuous_reward=0.,
            all_other_terms='unchanged selected musical task, thumb and weak B')
        self.contract['termination']['active_press_wrist'] = copy.deepcopy(SPEC)
        self.contract['termination']['additional_failure_reasons'].append('wrist_region_exit')
        self.contract['diagnostics']['active_press'] = dict(
            thumb_action_sign='side of prepared reference; not velocity',
            nonthumb_action_sign='incremental target velocity direction')

    def _allocate(self, count):
        super()._allocate(count)
        self.failure = torch.cat((self.failure, torch.zeros(count, 1, dtype=torch.bool, device=self.device)), -1)
        self.wrist_exit = WristExitState(count, self.device)

    def reset(self, indices, snapshot):
        super().reset(indices, snapshot)
        self.wrist_exit.reset(indices, .5*(self.guide['lower_G_m']+self.guide['upper_G_m']))
        return self.observation()

    def _observation_state(self, state):
        base = super()._observation_state(state)
        timers = torch.stack((self.wrist_exit.outside_s,
            (self.wrist_exit.grace_until-self._local_time()).clamp_min(0)), -1).to(base)
        return torch.cat((base[:, :-5], timers, base[:, -5:]), -1)

    def begin_control(self, actions):
        super().begin_control(actions)
        self.tick_failure = torch.cat((self.tick_failure,
            torch.zeros(self.N, 1, dtype=torch.bool, device=self.device)), -1)
        self.finger_outward[:, :5] = 0  # Thumb is positional, not incremental.

    def invalidate_control(self, mask):
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('control invalidation requires an active tick')
        if mask.shape != (self.N,) or mask.dtype != torch.bool or mask.device != self.device:
            raise ValueError('aligned boolean invalid-control mask required')
        self.control_invalid |= mask
        self.tick_failure[:, 6] |= self.control_invalid

    def _safety(self):
        # Same six physical criteria and integrated cost as the base; append
        # wrist as its own eighth bit instead of reusing a physical-failure bit.
        self.guitar_delta = self.guitar_body[:, :3]-self.reference_guitar[:, :3]
        self.guitar_rotation = rotvec(multiply(conjugate(self.reference_guitar[:, 3:7]), self.guitar_q))
        self.foot_delta = self.body[:, self.feet_indices, :3]-self.reference_feet
        present = torch.cat((self.flags[:, :3].any(-1, keepdim=True), self.flags[:, -2:]), -1)
        self.loss = torch.where(present, 0., self.loss+1/240.)
        gd = torch.linalg.vector_norm(self.guitar_delta, dim=-1)
        ga = torch.linalg.vector_norm(self.guitar_rotation, dim=-1)
        fd = torch.linalg.vector_norm(self.foot_delta, dim=-1)
        speed = self.snapshot['qd'].abs().amax(-1)
        wrist = self.wrist_exit.step(self.guide['delta'],
            .5*(self.guide['lower_G_m']+self.guide['upper_G_m']), self._local_time())
        reasons = torch.stack((gd > .08, ga > .35, fd.amax(-1) > .04,
            self.loss[:, 0] > .25, (self.loss[:, 1:] > .25).any(-1), speed > 50.,
            self.control_invalid, wrist), -1)
        self.tick_failure |= reasons
        rate = ((gd/.02)**2+(ga/.15)**2+(fd/.02).square().mean(-1)+
                (~present[:, 0]).float()+(~present[:, 1:]).float().mean(-1))
        self.tick_cost += rate/240.

    def _reward_components(self, components):
        result = super()._reward_components(components)
        return dict(result, song_wrist_position=torch.zeros_like(result['song_wrist_position']))

    def plan_decisions(self, remaining_ticks):
        if type(remaining_ticks) is not int or remaining_ticks < 1:
            raise ValueError('positive remaining control ticks required')
        local = self.clock//4
        events = torch.stack((self.press, self.onset, self.end), -1)[None]-self.score_offset[:, None, None]
        ticks = events*60.
        boundaries = torch.stack((ticks.floor(), ticks.ceil()), -1)
        difference = boundaries-local[:, None, None, None]
        eligible = (difference > 0) & self.focus_mask[:, :, None, None]
        nearest = difference.masked_fill(~eligible, torch.inf).flatten(1).amin(-1)
        maximum = min(remaining_ticks, SPEC['hold_ticks'])
        duration = torch.minimum(torch.full_like(nearest, maximum), nearest).long()
        return torch.minimum(duration, (self.duration_ticks-local).clamp_min(1)).clamp_min(1)

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        if bool(self.failure[index, 7]):
            result['failure_reasons'].append('wrist_region_exit')
        result['active_press'] = dict(schema=SPEC['schema'],
            wrist_exit=bool(self.failure[index, 7]),
            maximum_continuous_outer_exit_s=float(self.wrist_exit.max_outside_s[index]),
            controller='thumb position; nonthumb incremental; arm reference offsets')
        result['left_finger_motion']['action_mode'] = 'mixed_thumb_position_nonthumb_incremental'
        return result


def policy_factory(settings, pool):
    if settings.get('active_press') != SPEC:
        raise ValueError('exact v25 settings required; old checkpoints cannot be reinterpreted')
    return ActivePolicy(pool.observation['state'].shape[-1], size=settings['size'],
        contract=pool.contract, phase='J', exploration='independent').to(settings['device'])


@contextmanager
def bindings():
    from guitar_learning.training import finger_skill_runner, finger_decisions
    from guitar_learning.gpu import control, finger_skill_environment
    from .collector import ActiveCollector
    with patch.object(control, 'BatchedController', ActiveController), \
            patch.object(finger_skill_environment, 'FingerSkillEnvironment', ActiveEnvironment), \
            patch.object(finger_skill_runner, '_policy', policy_factory), \
            patch.object(finger_decisions, 'DecisionCollector', ActiveCollector):
        yield
