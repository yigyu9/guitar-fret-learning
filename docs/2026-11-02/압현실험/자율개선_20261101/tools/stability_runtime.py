"""성공 모델의 보존성을 비교한다. 모델만 이전하고 Adam·RNG·노출은 새로 시작한다."""
if __name__ == '__main__':
    import isaacgym  # native 초기화는 Torch보다 먼저 수행한다.

import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0, str(ROOT))
SOURCE_RUNTIME = ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/tools/runtime.py'
spec = importlib.util.spec_from_file_location('stability_original_transition', SOURCE_RUNTIME)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
torch = runtime.torch
OriginalPolicy = runtime.TransitionPolicy
OriginalTrainer = runtime.natural.NaturalTrainer
SCHEMA = 'guitar_learning.transition_stability_policy.v1'
VARIANTS = {'control': 3e-5, 'conservative': 1e-5}


class StabilityPolicy(OriginalPolicy):
    """행동·관측은 동일하며 실험의 출처와 학습률 계약만 identity에 추가한다."""
    schema = SCHEMA


def experiment(variant, checkpoint):
    checkpoint = Path(checkpoint).resolve()
    checkpoint.relative_to(ROOT)
    return dict(schema='guitar_learning.transition_stability.v1', variant=variant,
                actor_lr=VARIANTS[variant], actor_lr_cap=VARIANTS[variant],
                source_checkpoint=str(checkpoint), source_sha256=runtime.natural.digest(checkpoint),
                source_runtime_sha256=runtime.natural.digest(SOURCE_RUNTIME),
                transfer='model only, including learned std and critic; fresh Adam/RNG/updates/exposure')


def validate_experiment(settings, variant=None):
    from guitar_learning.portability import portable
    config = settings.get('stability_experiment', {})
    name = config.get('variant')
    if name not in VARIANTS or variant is not None and name != variant:
        raise ValueError('저장된 보존성 비교 조건 불일치')
    if portable(config) != portable(experiment(name, config['source_checkpoint'])):
        raise ValueError('명시 이전 원본 SHA 또는 실험 계약 변경')
    if settings['ppo']['actor_lr'] != VARIANTS[name]:
        raise ValueError('저장된 초기 actor 학습률 불일치')
    runtime.validate(settings)
    return config


def initialize_policy(policy, config):
    """이전 원본을 원래 클래스·PPO identity로 검증하고 가중치만 복사한다."""
    from guitar_learning.portability import localize, portable
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.training.ppo import PPOConfig
    source = Path(config['source_checkpoint'])
    if runtime.natural.digest(source) != config['source_sha256']:
        raise ValueError('이전 원본 체크포인트 SHA 불일치')
    payload = torch.load(source, map_location='cpu', weights_only=False)
    runner._validate_pins(payload['metadata'])
    saved = localize(payload['metadata']['settings'])
    runtime.validate(saved)
    architecture = payload['identity']['architecture']
    if architecture['schema'] != OriginalPolicy.schema:
        raise ValueError('원래 전환 v3 모델만 명시 이전 가능')
    with torch.random.fork_rng(devices=[]):
        original = OriginalPolicy(architecture['state_dim'], size=saved['size'],
            contract=localize(architecture['contract']), natural_press=saved['natural_press'],
            transition=saved['transition'])
        trainer = OriginalTrainer(original, PPOConfig(**saved['ppo']))
        if trainer._identity() != payload['identity']:
            raise ValueError('이전 원본 정책/PPO identity 불일치')
        original.load_state_dict(payload['model'], strict=True)
    target = copy.deepcopy(policy.architecture)
    target.pop('stability_experiment')
    target['schema'] = OriginalPolicy.schema
    if portable(target) != portable(original.architecture):
        raise ValueError('이전 원본과 새 모델의 관측·제어·구조 불일치')
    if not all(torch.isfinite(value).all() for value in payload['model'].values()):
        raise ValueError('비유한 이전 모델 가중치')
    policy.load_state_dict(payload['model'], strict=True)
    if runtime.natural.digest(source) != config['source_sha256']:
        raise ValueError('이전 중 원본 체크포인트 변경')


def trainer_class(config, diagnostic_path):
    from guitar_learning.training.ppo import KLGuardError
    cap = config['actor_lr_cap']

    class StabilityTrainer(OriginalTrainer):
        """기존 KL 검사·재시도를 유지하며 회복 학습률의 상한만 비교한다."""
        def _update(self, buffer, completed_episodes):
            before = [group['lr'] for group in self.actor_optimizer.param_groups]
            if any(lr > cap*(1+1e-12) for lr in before):
                raise ValueError('actor 학습률이 저장된 실험 상한을 초과')
            try:
                result = super()._update(buffer, completed_episodes)
            except KLGuardError as error:
                raw = copy.deepcopy(error.diagnostic)
                attempted = float(raw['attempted_kl'])
                # 표준 JSON으로 읽을 수 있도록 비유한 값은 문자열과 유한성으로 구분한다.
                raw['attempted_kl'] = attempted if math.isfinite(attempted) else str(attempted)
                row = dict(schema='guitar_learning.KL_failure.v1', variant=config['variant'],
                    committed_updates=self.updates, actor_lr_before=before,
                    actor_lr_at_exception=[g['lr'] for g in self.actor_optimizer.param_groups],
                    finite=math.isfinite(attempted), attempted_kl_finite=math.isfinite(attempted), diagnostic=raw,
                    scope='exception observed inside _update; inherited update restores model/Adam/RNG and re-raises')
                diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
                diagnostic_path.write_text(json.dumps(row, allow_nan=False, indent=2)+'\n')
                raise
            for group in self.actor_optimizer.param_groups:
                group['lr'] = min(cap, group['lr'])
            result['natural_press_lr']['next_lr'] = self.actor_optimizer.param_groups[0]['lr']
            result['stability_experiment'] = dict(variant=config['variant'], actor_lr_cap=cap)
            return result
    return StabilityTrainer


@contextmanager
def stability_runtime(settings, *, initialize=False, out):
    from guitar_learning.training import finger_skill_runner as runner, ppo
    config = validate_experiment(settings)
    with ORIGINAL_CONTEXT(settings):
        original = runner._policy, runner._pins, ppo.DecisionPPOTrainer
        def factory(current, pool):
            if validate_experiment(current) != config:
                raise ValueError('환경/정책 보존성 실험 계약 불일치')
            policy = original[0](current, pool)
            policy.architecture['stability_experiment'] = copy.deepcopy(config)
            if initialize:
                initialize_policy(policy, config)
            return policy
        def pins(current, directory, extra=()):
            return original[1](current, directory, list(extra)+[
                Path(__file__).resolve(), SOURCE_RUNTIME, Path(config['source_checkpoint'])])
        runner._policy, runner._pins = factory, pins
        ppo.DecisionPPOTrainer = trainer_class(config, Path(out)/'kl_failure.json')
        try:
            yield
        finally:
            runner._policy, runner._pins, ppo.DecisionPPOTrainer = original


ORIGINAL_CONTEXT = runtime.transition_runtime


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--variant', choices=tuple(VARIANTS))
    parser.add_argument('--initialize-from', type=Path)
    known, remaining = parser.parse_known_args(argv)
    operation = remaining[0] if remaining else None
    fresh = operation == 'train' and '--resume' not in remaining
    if fresh and (known.variant is None or known.initialize_from is None):
        parser.error('새 학습에는 --variant 및 --initialize-from 필요')
    if not fresh and known.initialize_from is not None:
        parser.error('strict resume/평가는 모델 재초기화 금지')
    original = runtime.build_settings, runtime.transition_runtime, runtime.TransitionPolicy, sys.argv
    def build(*args, **kwargs):
        settings = original[0](*args, **kwargs)
        settings['stability_experiment'] = experiment(known.variant, known.initialize_from)
        settings['ppo']['actor_lr'] = VARIANTS[known.variant]
        return settings
    @contextmanager
    def context(settings):
        validate_experiment(settings, known.variant)
        out = Path(remaining[remaining.index('--out')+1])
        with stability_runtime(settings, initialize=fresh, out=out):
            yield
    runtime.build_settings, runtime.transition_runtime, runtime.TransitionPolicy = build, context, StabilityPolicy
    sys.argv = [str(Path(__file__).resolve())]+remaining
    try:
        runtime.main()
    finally:
        runtime.build_settings, runtime.transition_runtime, runtime.TransitionPolicy, sys.argv = original


if __name__ == '__main__':
    main()
