"""기존 연구 프로세스에만 연속 무접촉 종료를 연결하는 독립 실행기.

사용: termination_runtime.py --threshold 5 --threads 1 train --out NEW ...
0/5/3 비교군 모두 같은 두 관측을 사용한다. 평가에서는 신규 종료만 비활성화한다.
"""
import argparse
import copy
import hashlib
from pathlib import Path
import runpy
import sys


def update_streak(streak, opportunities, contacted):
    """종료시각 순 기회를 GPU에서 처리하고 최종·구간 최대 연속 실패를 반환한다.

    opportunities/contacted는 [환경, 종료시각 그룹] 불리언이다. 접촉이 있는
    기회는 연속 실패를 초기화하며, 기회가 아닌 열은 계산에 영향을 주지 않는다.
    """
    import torch
    if opportunities.shape[1] == 0:
        return streak.clone(), streak.clone()
    bad = (opportunities & ~contacted).long().cumsum(-1)
    good = opportunities & contacted
    latest_reset = torch.where(good, bad, 0).cummax(-1).values
    had_reset = good.long().cumsum(-1) > 0
    running = bad-latest_reset+torch.where(had_reset, 0, streak[:, None])
    return running[:, -1], torch.maximum(streak, running.amax(-1))


def termination_spec(threshold):
    """종료 조건의 판정·평가·소스 동일성을 하나의 완전한 계약으로 기록한다."""
    module_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return dict(
        schema='guitar_learning.no_contact_termination.v1', threshold=threshold,
        module_sha256=module_sha, preparation_s=3.,
        criterion='selected focus notes after their end; note.clean>0 at any audible 240Hz sample; '
            'same-end notes form one opportunity; any clean contact resets streak; '
            'only note ends strictly after local preparation 3s are eligible',
        simultaneous='process end-time groups chronologically; threshold crossing latches even if a later group contacts',
        cost='reuse existing unified failure cost exactly once; no added duplicate penalty',
        eval_new_termination='disabled in explicit evaluation view',
        observation='all arms including threshold 0 expose min(streak,5)/5 and threshold/5')


def environment_class(base, threshold):
    """원래 환경의 제어·비용·성공 판정은 유지하는 연구 전용 자식 클래스를 만든다."""
    if type(threshold) is not int or threshold not in (0, 3, 5):
        raise ValueError('threshold must be exactly 0, 3 or 5')
    import torch

    class NoContactEnvironment(base):
        def __init__(self, metadata, **kwargs):
            self.no_contact_threshold = threshold
            super().__init__(metadata, **kwargs)
            self.no_contact_ends, self.no_contact_groups = torch.unique(
                self.end, sorted=True, return_inverse=True)
            observation = self.contract['observation']
            observation['fields'] += ['no_contact.streak', 'no_contact.threshold']
            observation['scales'] += [5., 5.]
            observation['dimension'] += 2
            self.scales = self._tensor(observation['scales'])
            self.contract['termination']['no_contact_experiment'] = termination_spec(threshold)
            self.contract['termination']['additional_failure_reasons'] += ['no_contact']

        def _allocate(self, count):
            super()._allocate(count)
            self.no_contact_streak = torch.zeros(count, dtype=torch.long, device=self.device)
            self.no_contact_opportunities = torch.zeros_like(self.no_contact_streak)
            self.no_contact_seen = torch.zeros(count, self.no_contact_ends.numel(),
                dtype=torch.bool, device=self.device)
            self.no_contact_crossed = torch.zeros(count, dtype=torch.bool, device=self.device)

        def reset(self, indices, snapshot):
            # 부모 reset 안에서 반환 관측을 만들기 전에 연구 카운터를 초기화한다.
            if self.initialized:
                indices = torch.as_tensor(indices, dtype=torch.long, device=self.device)
                self.no_contact_streak[indices] = 0
                self.no_contact_opportunities[indices] = 0
                self.no_contact_seen[indices] = False
                self.no_contact_crossed[indices] = False
            return super().reset(indices, snapshot)

        def _control_failures(self):
            original = super()._control_failures()
            group = self.no_contact_groups[None].expand(self.N, -1)
            shape = self.no_contact_seen.shape
            count = torch.zeros(shape, dtype=torch.long, device=self.device)
            contact = torch.zeros_like(count)
            selected = self.focus_mask & (self.end[None]-self.score_offset[:, None] > 3.)
            count.scatter_add_(1, group, selected.long())
            contact.scatter_add_(1, group, (selected & (self.note['clean'] > 0)).long())
            eligible = ((count > 0) & ~self.no_contact_seen &
                (self.no_contact_ends[None] <= self._score_time()[:, None]+1e-12) &
                (self._local_time()[:, None] >= 3.))
            self.no_contact_streak, maximum = update_streak(
                self.no_contact_streak, eligible, contact > 0)
            self.no_contact_seen |= eligible
            self.no_contact_opportunities += eligible.sum(-1)
            if threshold:
                self.no_contact_crossed |= maximum >= threshold
            return original | (self.no_contact_crossed & (not self.evaluation))

        def _observation_state(self, state):
            state = super()._observation_state(state)
            extra = torch.stack((self.no_contact_streak.clamp_max(5),
                torch.full_like(self.no_contact_streak, threshold)), -1).to(state.dtype)
            return torch.cat((state, extra), -1)

        def _episode(self, index, failed):
            result = super()._episode(index, failed)
            crossed = bool(self.no_contact_crossed[index])
            active_failure = crossed and not self.evaluation
            if active_failure:
                result['failure_reasons'].append('no_contact')
                termination = result['termination']
                if not (termination['physical_failure'] or termination['wrist_failure']):
                    termination['primary_reason'] = 'no_contact'
            result['termination']['no_contact_failure'] = active_failure
            result['no_contact_termination'] = dict(
                threshold=threshold, streak=int(self.no_contact_streak[index]),
                completed_opportunities=int(self.no_contact_opportunities[index]),
                threshold_crossed=crossed, evaluation_disabled=bool(self.evaluation))
            return result

    return NoContactEnvironment


def policy_class(base, threshold):
    """557열 기본 계약을 원 검증기로 확인한 뒤 명시적 559열 정책을 구성한다."""
    if type(threshold) is not int or threshold not in (0, 3, 5):
        raise ValueError('threshold must be exactly 0, 3 or 5')
    import torch
    from torch import nn
    extra_fields = ['no_contact.streak', 'no_contact.threshold']
    expected_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    class NoContactPolicy(base):
        schema = 'guitar_learning.no_contact_policy.v1'

        def __init__(self, state_dim, event_dim=24, size='medium', contract=None,
                     research_config=None):
            if not isinstance(contract, dict):
                raise ValueError('explicit no-contact training contract required')
            observation = contract.get('observation', {})
            termination = contract.get('termination', {}).get('no_contact_experiment', {})
            if (state_dim != 559 or observation.get('dimension') != 559 or
                    observation.get('fields', [])[-2:] != extra_fields or
                    len(observation.get('fields', [])) != 559 or
                    len(set(observation.get('fields', []))) != 559 or
                    observation.get('scales', [])[-2:] != [5., 5.] or
                    len(observation.get('scales', [])) != 559 or
                    termination != termination_spec(threshold)):
                raise ValueError('exact no-contact559 fields/scales/threshold/source contract required')
            reference = copy.deepcopy(contract)
            reference['observation']['fields'] = reference['observation']['fields'][:-2]
            reference['observation']['scales'] = reference['observation']['scales'][:-2]
            reference['observation']['dimension'] = 557
            # 필드 순서·행동·GPU·J33 등 원래 557열의 모든 검증을 그대로 수행한다.
            super().__init__(557, event_dim=event_dim, size=size, contract=reference,
                research_config=research_config)

            def extend(encoder):
                old = encoder.state[0]
                layer = nn.Linear(old.in_features+2, old.out_features,
                    device=old.weight.device, dtype=old.weight.dtype)
                with torch.no_grad():
                    layer.weight[:, :-2].copy_(old.weight)
                    layer.weight[:, -2:].zero_()
                    layer.bias.copy_(old.bias)
                encoder.state[0] = layer

            for encoder in (self.support_encoder, self.finger_encoder, self.value_encoder):
                extend(encoder)
            self.support_indices = torch.cat((self.support_indices,
                self.support_indices.new_tensor([557, 558])))
            self.architecture['state_dim'] = 559
            self.architecture['support_fields'] += extra_fields
            self.architecture['contract'] = copy.deepcopy(contract)
            self.architecture['no_contact_extension'] = dict(
                fields=extra_fields, source_sha256=expected_sha,
                initialization='existing557 columns preserved; two new columns zero initialized in all encoders')

    return NoContactPolicy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threshold', required=True, type=int, choices=(0, 3, 5))
    parser.add_argument('--threads', required=True, type=int, choices=(1, 2, 4))
    args, remainder = parser.parse_known_args()
    import isaacgym  # Torch보다 먼저 native 확장을 초기화한다.
    import torch
    import guitar_learning.tool.experiments.finger_ablation_contact as contact
    import guitar_learning.tool.experiments.finger_ablation_learning as learning
    original_threads = torch.set_num_threads
    original_environment = contact.ResearchEnvironment
    original_policy = learning.LearningPolicy

    def selected_threads(requested):
        original_threads(args.threads)
        if torch.get_num_threads() != args.threads:
            raise RuntimeError('Torch thread selection failed')

    selected_threads(args.threads)
    torch.set_num_threads = selected_threads
    contact.ResearchEnvironment = environment_class(original_environment, args.threshold)
    learning.LearningPolicy = policy_class(original_policy, args.threshold)
    sys.argv = ['guitar_learning.tool.experiments.finger_ablation']+remainder
    print('[no-contact] threshold=%d; torch_threads=%d; evaluation termination disabled' %
        (args.threshold, args.threads), flush=True)
    try:
        runpy.run_module('guitar_learning.tool.experiments.finger_ablation', run_name='__main__')
    finally:
        contact.ResearchEnvironment = original_environment
        learning.LearningPolicy = original_policy
        torch.set_num_threads = original_threads


if __name__ == '__main__':
    main()
