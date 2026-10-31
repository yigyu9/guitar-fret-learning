"""격리 사본에서 탐색·학습률·관측 기반 압현 단계만 비교한다.

물리/보상/시계는 공식 실행기를 사용한다. 순차 조건의 실행 행동은 잠재 Gaussian
표본의 결정적 함수이며, PPO는 실행 행동이 아닌 원래 잠재 행동의 확률을 사용한다.
"""
if __name__ == '__main__':
    import isaacgym  # GPU 라이브러리는 torch보다 먼저 로드한다.

import argparse
import copy
import math
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import torch
from torch.distributions import Normal
from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.ppo import DecisionPPOTrainer

MODES = ('baseline', 'exploration', 'lr', 'combined', 'sequential')
SCHEMA = 'guitar_learning.press_research.v1'


def configuration(mode):
    if mode not in MODES:
        raise ValueError('unknown press research mode')
    return dict(schema=SCHEMA, mode=mode,
        path_adapter='nested_copy_v2: provenance mappings first; local runtime and sibling smoke/runs/rendering outputs unchanged; other inputs use official resolver',
        finger_initial_std=.15 if mode in ('exploration', 'combined', 'sequential') else math.exp(-3),
        finger_std_floor=.10 if mode in ('exploration', 'combined', 'sequential') else None,
        support_initial_std=math.exp(-3),
        lr_recovery=mode in ('lr', 'combined', 'sequential'),
        lr_floor=7.5e-6, lr_cap=3e-5, retry_factor=.5,
        recovery_factor=1.25, stable_updates=10, stable_kl_below=.005,
        sequential=mode == 'sequential',
        gate=dict(wrist_axis_excess_m=.010, tangent_error_m=.008,
            signed_height_m=[-.001, .030], normal_cos_min=.1,
            wrist='all three absolute nearest-region deltas <= threshold',
            alignment='guitar XY tangent norm; press normal must equal +/-Z',
            slots='valid tracking slot 2*f only; no target leaves action unchanged',
            actions='wrist not ready: target4 zero; aligning: target PIP/DIP zero; pressing: all free',
            recomputed='every observation, no clock fallback or persistent stage; arms always free'),
        likelihood=('Gaussian latent33; execution T(state,tanh(latent)); all latent axes included, '
                    'including gated axes; no executed-action density; gated latent variance may add noise'
                    if mode == 'sequential' else 'unchanged physical tanh latent33'))


class ResearchPolicy(FingerSkillPolicy):
    """출력 분포와 순차 조건의 행동 변환만 변경하는 정책."""
    def __init__(self, *args, research, **kwargs):
        super().__init__(*args, **kwargs)
        self.research = copy.deepcopy(research)
        # 진단은 저장본/정책 입력에 포함하지 않으며 난수를 소비하지 않는다.
        self._stage_counts = None
        self.architecture['press_research'] = copy.deepcopy(research)
        with torch.no_grad():
            self.finger_log_std.fill_(math.log(research['finger_initial_std']))
        if research['sequential']:
            observation = self.architecture['contract']['observation']
            fields, scales = observation['fields'], observation['scales']
            self.wrist_indices = [fields.index('wrist_region.delta_'+axis) for axis in 'xyz']
            self.wrist_scales = [scales[i] for i in self.wrist_indices]
            event_fields = observation['event_fields']
            names = ['surface_error_x', 'surface_error_y', 'pad_signed_height', 'pad_normal_cos']
            self.gate_columns = [event_fields.index(name) for name in names]
            self.gate_scales = [observation['event_scales'][i] for i in self.gate_columns]
            plane = observation['surface_geometry']['press_surface']['plane_G']
            if abs(plane[0]) > 1e-10 or abs(plane[1]) > 1e-10 or abs(abs(plane[2])-1) > 1e-10:
                raise ValueError('sequential XY tangent contract requires +/-Z unit press plane')
            self.architecture['press_research']['gate_observation'] = dict(
                wrist_indices=self.wrist_indices, wrist_scales=self.wrist_scales,
                event_columns=self.gate_columns, event_scales=self.gate_scales,
                press_plane_G=plane)
            self.architecture['likelihood'] = 'joint33_augmented_gaussian_latent_state_gate_v1'

    def forward(self, *inputs):
        result = super().forward(*inputs)
        floor = self.research['finger_std_floor']
        if floor is not None:
            log_std = result['log_std']
            result['log_std'] = torch.cat((log_std[:, :17],
                log_std[:, 17:33].clamp_min(math.log(floor)), log_std[:, 33:]), -1)
        return result

    def log_probability(self, mean, log_std, latent):
        if not self.research['sequential']:
            return super().log_probability(mean, log_std, latent)
        return Normal(mean[..., :33], log_std[..., :33].exp()).log_prob(latent[..., :33]).sum(-1)

    def gate_stages(self, state, priority_events, priority_mask):
        """-1: 목표 없음, 0: 손목 이동, 1: 정렬, 2: 손가락 굽힘 허용."""
        scale = state.new_tensor(self.wrist_scales)
        ready = ((state[:, self.wrist_indices]*scale).abs() <= .010).all(-1)
        values = priority_events[:, ::2, self.gate_columns]*state.new_tensor(self.gate_scales)
        x, y, height, normal = values.unbind(-1)
        aligned = ((x.square()+y.square() <= .008**2) & (height >= -.001) &
                   (height <= .030) & (normal >= .1))
        valid = priority_mask[:, ::2]
        return torch.where(valid, torch.where(ready[:, None],
            torch.where(aligned, 2, 1), 0), -1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = super().act(state, events, mask, priority_events, priority_mask, deterministic)
        if self.research['sequential']:
            stages = self.gate_stages(state, priority_events, priority_mask)
            with torch.no_grad():
                counts = torch.stack([(stages == stage).sum(0) for stage in (-1, 0, 1, 2)], -1)
                if self._stage_counts is None:
                    self._stage_counts = counts
                else:
                    self._stage_counts.add_(counts)
            action = result['action'].clone()
            for finger in range(4):
                start = 17+4*finger
                action[:, start:start+2] *= (stages[:, finger] != 0)[:, None]
                action[:, start+2:start+4] *= ((stages[:, finger] == -1) | (stages[:, finger] == 2))[:, None]
            result.update(action=action, press_research_stages=stages)
        return result


    def stage_diagnostics(self, reset=False):
        """실제 act 호출별 손가락-환경 결정 수와 60Hz 환산 노출 시간을 반환한다."""
        if not self.research['sequential']:
            return dict(enabled=False)
        counts = ([[0]*4 for _ in range(4)] if self._stage_counts is None else
                  self._stage_counts.detach().cpu().tolist())
        result = dict(enabled=True, schema='guitar_learning.press_research_stages.v1',
            columns=['no_target', 'wrist_move', 'alignment', 'finger_bend'],
            fingers=['index', 'middle', 'ring', 'pinky'], counts=counts,
            exposure_s=[[value/60. for value in row] for row in counts],
            scope='finger-environment decisions at policy act, K1/60Hz; excludes PPO forward/evaluate',
            unit='summed finger-environment time, not wall time',
            persistent=False)
        if reset and self._stage_counts is not None:
            self._stage_counts.zero_()
        return result


class ResearchTrainer(DecisionPPOTrainer):
    """재시도 하한과 안정 갱신 후 복구를 Adam 저장 상태에 함께 기록한다."""
    def _identity(self):
        identity = super()._identity()
        identity['press_research'] = copy.deepcopy(self.policy.research)
        return identity

    def _retry_actor_lr(self, retry):
        if not self.policy.research['lr_recovery']:
            return super()._retry_actor_lr(retry)
        # 부모는 각 재시도 전에 동일 minibatch 스냅샷으로 복원한다.
        for group in self.actor_optimizer.param_groups:
            group['lr'] = max(7.5e-6, group['lr']*.5**(retry+1))
            group['press_research_stable_updates'] = 0

    def recover_learning_rate(self, result):
        used = result['actor_lr']
        stable = result['kl_retries'] == 0 and result['analytic_kl'] < .005
        reason = 'disabled'
        if self.policy.research['lr_recovery']:
            reason = 'stable_accumulation' if stable else 'retry_or_kl_reset'
            for group in self.actor_optimizer.param_groups:
                count = group.get('press_research_stable_updates', 0)+1 if stable else 0
                if count >= 10:
                    group['lr'] = min(3e-5, group['lr']*1.25)
                    count = 0
                    reason = 'ten_stable_updates_recover' if group['lr'] > used else 'already_at_cap'
                group['press_research_stable_updates'] = count
        result['press_research_lr'] = dict(used_lr=used,
            next_lr=self.actor_optimizer.param_groups[0]['lr'], recovery_reason=reason,
            stable_updates=self.actor_optimizer.param_groups[0].get('press_research_stable_updates', 0))
        return result

    def _update(self, buffer, completed_episodes):
        result = self.recover_learning_rate(super()._update(buffer, completed_episodes))
        result['press_research_stages'] = self.policy.stage_diagnostics(reset=True)
        return result


@contextmanager
def research_runtime(research):
    """공식 native 바이트를 유지하며 사본 경로와 정책/PPO factory를 한시 교체한다."""
    from guitar_learning.native import paths as native_paths
    original_resolver = native_paths.resolve_input_path
    def local_resolver(path):
        lexical = native_paths._lexical(path)
        # paper/docs의 역사 경로는 먼저 내부 CAS 매핑을 보존해야 한다.
        if str(lexical) in native_paths._mapping()[0]:
            return original_resolver(path)
        if lexical == native_paths.ROOT or native_paths.ROOT in lexical.parents:
            return lexical.resolve()
        output_roots = [native_paths.ROOT.parent/name for name in ('smoke', 'runs', 'rendering')]
        if any(lexical == root or root in lexical.parents for root in output_roots):
            return lexical.resolve()
        return original_resolver(path)
    native_paths.resolve_input_path = local_resolver
    try:
        # prepared_reset/launch보다 먼저 adapter를 설치한다.
        from guitar_learning.training import finger_skill_runner, ppo
        original_policy, original_trainer = finger_skill_runner._policy, ppo.DecisionPPOTrainer
        policies = []
        def factory(settings, pool):
            if settings.get('press_research') != research:
                raise ValueError('strict research settings/mode mismatch')
            policy = ResearchPolicy(pool.observation['state'].shape[-1], size=settings['size'],
                contract=pool.contract, research=research).to(settings['device'])
            policies.append(policy)
            return policy
        finger_skill_runner._policy = factory
        ppo.DecisionPPOTrainer = ResearchTrainer
        try:
            yield policies
        finally:
            finger_skill_runner._policy, ppo.DecisionPPOTrainer = original_policy, original_trainer
    finally:
        native_paths.resolve_input_path = original_resolver


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('train', 'evaluate', 'render'))
    parser.add_argument('--mode', required=True, choices=MODES)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--song')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--num-envs', type=int, default=None)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--horizon', type=int, default=32)
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='large')
    args = parser.parse_args()
    research = configuration(args.mode)
    with research_runtime(research) as policies:
        if args.operation == 'train':
            if not args.song or args.checkpoint:
                parser.error('train requires --song and fresh initialization')
            from guitar_learning.training.launch import settings_document, run
            settings = settings_document(song=args.song, size=args.size,
                num_envs=args.num_envs or 64, horizon=args.horizon, updates=args.updates,
                seed=args.seed, checkpoint_every=1000)
            settings['press_research'] = research
            if research['lr_recovery']:
                settings['ppo']['retry_lr_factor'] = .5
            run(settings, SimpleNamespace(out=args.out, resume=None))
        else:
            if args.checkpoint is None:
                parser.error('evaluate/render require --checkpoint')
            if args.operation == 'evaluate':
                from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
                evaluate_checkpoint(args.checkpoint, args.out, num_envs=args.num_envs or 16, scope='full_song')
            else:
                from guitar_learning.tool.demonstration.render_finger_skill import render
                render(args.checkpoint, args.out, num_envs=args.num_envs or 4, scope='full_song')
            from guitar_learning.training.training_log_io import write
            write(args.out/'press_research_diagnostics.json', dict(
                schema='guitar_learning.press_research_diagnostics.v1', mode=args.mode,
                operation=args.operation, policy_stages=[policy.stage_diagnostics() for policy in policies]))


if __name__ == '__main__':
    main()
