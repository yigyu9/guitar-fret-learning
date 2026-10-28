"""Small diagnostic subclasses; production defaults remain unchanged."""
import copy
import math
import torch

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.policy import FINGERS
from guitar_learning.song.finger_phrases import BalancedPhraseSampler
from guitar_learning.training.rollout import GpuPool
from guitar_learning.tool.validation.press_acquisition import trajectory_actions
from .spec import SCHEMA, selected_actions, subset
from .wrist import WRIST_CONTROL, interpolated_pose, wrist_error_and_jacobian, bounded_wrist_target, _wrist_position_groups
from guitar_learning.gpu.control import apply, conjugate, multiply


class ShortEnvironment(FingerSkillEnvironment):
    allowed_finger_action_modes = ('incremental', 'position')

    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        spec = copy.deepcopy(song['short_learning'])
        if spec.get('schema') != SCHEMA or spec['mode'] != song['finger_action_mode']:
            raise ValueError('Explicit matching short-task diagnostic contract required')
        super().__init__(metadata, bundle=bundle, song=song, skill=skill, device=device, hand=hand)
        self.selected_index, self.catalog, view = subset(self.task, spec['teacher'])
        if view != spec['view'] or spec['learned_action_indices'] != list(selected_actions(spec['finger'])):
            raise ValueError('Diagnostic source view/action mask mismatch')
        self.sampler = BalancedPhraseSampler(self.catalog)
        self.contract['task']['short_learning'] = spec
        self.contract['task']['finger_skill'].update(scope='fixed_source_subset',
            catalog_sha256=self.catalog.fingerprint, reset_selection='same single original note on every reset',
            planned_transitions=None, full_song_after=None)
        self.contract['diagnostics']['short_learning'] = dict(
            scope='teacher-supported fixed guitar; original predicates/rewards; no success inheritance')

    def _reset_scope(self, indices):
        # 이 진단은 노출 일정과 관계없이 원곡의 지정 음 하나만 선택한다.
        evaluation, full_song = self.evaluation, self.evaluation_full_song
        self.evaluation, self.evaluation_full_song = True, False
        try:
            super()._reset_scope(indices)
        finally:
            self.evaluation, self.evaluation_full_song = evaluation, full_song
            self.training_scope = 'fixed_source_subset'
        for value in (self.wrist_active, self.wrist_elapsed, self.wrist_severe_elapsed,
                      self.wrist_failure, self.wrist_severe_failure, self.failure_paid,
                      self.termination_remaining_time_cost, self.termination_note_budget):
            value[indices] = 0

    def set_evaluation(self, enabled=True, full_song=False):
        if full_song:
            raise ValueError('Short diagnostic cannot evaluate full song')
        super().set_evaluation(enabled, full_song=False)

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        result['finger_skill'].update(scope='fixed_source_subset', planned_transitions=None, full_song_after=None)
        result['short_learning'] = self.contract['task']['short_learning']['result_scope']
        return result


class ShortPolicy(FingerSkillPolicy):
    schema = 'guitar_learning.short_finger_policy.v2'

    def __init__(self, *, contract, size='small'):
        spec = contract['task']['short_learning']
        if spec.get('schema') != SCHEMA or spec['learned_action_indices'] != list(selected_actions(spec['finger'])):
            raise ValueError('Fixed named four-axis policy mask required')
        super().__init__(557, size=size, contract=contract)
        self.finger = spec['finger']
        self.architecture['learned_action_indices'] = spec['learned_action_indices']
        self.architecture['likelihood'] = 'selected_four_physical_tanh_latents_only'
        self.support_encoder.requires_grad_(False)
        self.support_head.requires_grad_(False)
        self.support_log_std.requires_grad_(False)
        for finger, head in self.finger_heads.items():
            head.requires_grad_(finger == FINGERS[self.finger-1])
        with torch.no_grad():
            self.finger_log_std.fill_(math.log(spec['initial_std']))

    def _active_mask(self):
        mask = torch.zeros(39, dtype=torch.bool, device=self.support_log_std.device)
        mask[list(selected_actions(self.finger))] = True
        return mask


def teacher_goal(reference, spec):
    goal = reference.clone()
    for name, angle in spec['teacher']['arm_targets_rad'].items():
        goal[ACTIVE_NAMES.index(name)] = angle
    for f, (bend, spread) in enumerate(zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES), 1):
        if f != spec['finger']:
            goal[17+4*(f-1):21+4*(f-1)] = goal.new_tensor((bend[0], spread, bend[1], bend[2]))*math.pi/180
    return goal


class ShortPool(GpuPool):
    environment_class_override = ShortEnvironment

    def __init__(self, settings, out):
        self.spec = copy.deepcopy(settings['song']['short_learning'])
        if self.spec.get('wrist_control') != WRIST_CONTROL:
            raise ValueError('Exact wrist feedback contract required')
        self.initial_wrist_position = None
        super().__init__(settings, out)
        try:
            self.wrist_position_groups = _wrist_position_groups(
                self.controller, self.scene.metadata['body_names'], self.controller.active[:12])
        except ValueError:
            self.close()
            raise
        self.learn_mask = torch.zeros(39, dtype=torch.bool, device=self.scene.device)
        self.learn_mask[self.spec['learned_action_indices']] = True
        self.teacher_reference = self.controller.reference[self.controller.active]
        self.teacher_final = teacher_goal(self.teacher_reference, self.spec)
        if bool(((self.teacher_final < self.controller.action_low) |
                 (self.teacher_final > self.controller.action_high)).any()):
            self.close()
            raise ValueError('Teacher target exceeds actual controller bounds')
        self.incremental_mask = torch.zeros_like(self.learn_mask)
        self.incremental_mask[self.controller.incremental_actions] = True

    def reset(self, indices=None):
        result = super().reset(indices)
        ids = (torch.arange(self.num_envs, device=self.scene.device) if indices is None else
               torch.as_tensor(indices, device=self.scene.device, dtype=torch.long))
        if ids.numel() == 0:
            return result
        env = self.environment
        if self.initial_wrist_position is None:
            self.initial_wrist_position = torch.zeros(self.num_envs,3,device=self.scene.device)
            self.initial_wrist_quaternion = torch.zeros(self.num_envs,4,device=self.scene.device)
            self.wrist_correction = torch.zeros(self.num_envs,12,device=self.scene.device)
            self.previous_arm_request = torch.zeros_like(self.wrist_correction)
        self.initial_wrist_position[ids] = env.local_bodies[ids,env.wrist_index]
        self.initial_wrist_quaternion[ids] = multiply(conjugate(env.guitar_q[ids]), env.body[ids,env.wrist_index,3:7])
        self.wrist_correction[ids] = 0
        self.previous_arm_request[ids] = self.controller.reference[self.controller.active[:12]]
        return result

    def _wrist_feedback(self, desired, fraction):
        snapshot = self.scene.snapshot()
        env = self.environment
        target_G = desired.new_tensor(self.spec['teacher']['wrist_position_G_m'])
        rotation_G = desired.new_tensor(self.spec['teacher']['wrist_quaternion_G_xyzw'])
        position, quaternion = interpolated_pose(self.initial_wrist_position, self.initial_wrist_quaternion,
                                                 target_G, rotation_G, fraction)
        error, jacobian = wrist_error_and_jacobian(snapshot, env.wrist_index, env.guitar_index,
            self.scene.com[env.wrist_index], self.wrist_position_groups, position, quaternion)
        active = ~snapshot['reset_body_snapshot']
        arm, correction, delta, candidate = bounded_wrist_target(desired[:,:12], self.wrist_correction,
            self.previous_arm_request, snapshot['q'][:,self.controller.active[:12]], jacobian, error, active, self.controller.action_low[:12],
            self.controller.action_high[:12], self.controller.rate[self.controller.active[:12]])
        self.wrist_correction.copy_(correction)
        self.previous_arm_request.copy_(arm)
        desired[:,:12] = arm
        self.last_wrist_feedback = dict(active=active.clone(), pose_error_world=error.clone(),
            requested_delta_rad=delta.clone(), requested_arm_rad=arm.clone(), candidate_arm_rad=candidate.clone(),
            position_goal_G_m=position.clone(), quaternion_goal_G_xyzw=quaternion.clone())
        return desired

    def _create_scene(self, settings, out):
        from guitar_learning.gpu.scene import GpuScene
        return GpuScene(self.num_envs, 'left', device=settings['device'], out=out,
                        diagnostic_guitar_mode='fixed')

    def step(self, actions):
        # One physical tick per collector tick, including the preparation period.
        fraction = ((self.environment._local_time()+1/60)/self.spec['teacher']['ramp_s']).clamp(0, 1).to(actions.dtype)
        desired = self.teacher_reference+fraction[:, None]*(self.teacher_final-self.teacher_reference)
        desired = self._wrist_feedback(desired, fraction)
        teacher = trajectory_actions(desired, self.controller.target[:, self.controller.active],
            self.teacher_reference, self.controller.action_low, self.controller.action_high,
            self.incremental_mask, max_speed=4.)
        self.last_policy_action = actions.detach().clone()
        self.last_executed_action = torch.where(self.learn_mask[None], actions, teacher)
        self.last_executed_action[:, 33:] = 0
        return super().step(self.last_executed_action)
