"""명시적으로 봉인한 단일 요인·조합 연구를 기존 J 실행기에서 격리 실행한다.

기본 학습을 바꾸지 않고 이 프로세스 안에서만 연구 클래스 factory를 연결한다.
확률 계산·입력 SHA·체크포인트 identity 검증은 기존 엄격한 검사를 그대로 쓴다.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCHEMA = 'guitar_learning.finger_ablation.v1'


def flags(names=()):
    from guitar_learning.tool.experiments.finger_ablation_learning import FACTORS
    if len(set(names)) != len(names) or not set(names) <= set(FACTORS):
        raise ValueError('unique known research factors required')
    return {name: name in names for name in FACTORS}


def get_config(settings):
    from guitar_learning.tool.experiments.finger_ablation_learning import validate_research_config
    spec = settings.get('finger_ablation')
    if not isinstance(spec, dict) or set(spec) != {'schema', 'factors'} or spec['schema'] != SCHEMA:
        raise ValueError('explicit finger_ablation.v1 settings required')
    return validate_research_config(spec['factors'])


def make_settings(config, *, updates=200, seed=7, num_envs=1024, size='large'):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.tool.experiments.finger_ablation_learning import validate_research_config
    config = validate_research_config(config)
    settings = settings_document(size=size, num_envs=num_envs, horizon=32, updates=updates,
        seed=seed, checkpoint_every=max(updates, 1))
    settings['finger_ablation'] = dict(schema=SCHEMA, factors=config)
    settings['ppo']['advantage_normalization'] = 'separate' if config['separate'] else 'joint'
    return settings


@contextmanager
def research_runtime(config):
    """단일 프로세스의 연구 설정만 허용하고 종료 시 모든 factory를 복원한다."""
    import guitar_learning.training.finger_skill_runner as runner
    import guitar_learning.training.rollout as rollout
    import guitar_learning.training.ppo as ppo
    from guitar_learning.tool.experiments.finger_ablation_learning import (
        LearningPolicy, LearningTrainer, validate_research_config)
    from guitar_learning.tool.experiments.finger_ablation_contact import ResearchEnvironment
    config = validate_research_config(config)
    original_validate = runner._validate_joint_settings
    original_pool = rollout.GpuPool

    def validate(settings):
        if get_config(settings) != config:
            raise ValueError('research factors differ from active runtime')
        expected = 'separate' if config['separate'] else 'joint'
        if settings['ppo'].get('advantage_normalization') != expected:
            raise ValueError('research normalization differs from exact factors')
        # 연구에서 허용한 정규화 차이만 분리하고 나머지 J 제약을 원 검증기로 확인한다.
        reference = copy.deepcopy(settings)
        reference['ppo']['advantage_normalization'] = 'joint'
        original_validate(reference)

    class ResearchPool(original_pool):
        environment_class_override = ResearchEnvironment

        def _create_scene(self, settings, out):
            validate(settings)
            scene = super()._create_scene(settings, out)
            scene.metadata['finger_ablation'] = copy.deepcopy(config)
            return scene

    def policy(settings, pool):
        validate(settings)
        if pool.contract['reward']['finger_ablation']['flags'] != config:
            raise ValueError('environment and policy factors differ')
        return LearningPolicy(pool.observation['state'].shape[-1], size=settings['size'],
            contract=pool.contract, research_config=config).to(settings['device'])

    with ExitStack() as stack:
        stack.enter_context(patch.object(runner, '_validate_joint_settings', validate))
        stack.enter_context(patch.object(runner, '_policy', policy))
        stack.enter_context(patch.object(rollout, 'GpuPool', ResearchPool))
        stack.enter_context(patch.object(ppo, 'DecisionPPOTrainer',
            partial(LearningTrainer, research_config=config)))
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('train', 'evaluate', 'render'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--factors', nargs='*', default=[])
    parser.add_argument('--updates', type=int, default=200)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--num-envs', type=int)
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='large')
    parser.add_argument('--checkpoint', type=Path)
    args = parser.parse_args()
    import isaacgym  # native 확장을 Torch보다 먼저 초기화한다.
    import torch
    from guitar_learning.training.launch import run
    from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
    if args.mode == 'train':
        if args.checkpoint is not None:
            raise ValueError('controlled fresh experiments do not resume checkpoints')
        config = flags(args.factors)
        settings = make_settings(config, updates=args.updates, seed=args.seed,
            num_envs=1024 if args.num_envs is None else args.num_envs, size=args.size)
        with research_runtime(config):
            report = run(settings, SimpleNamespace(out=args.out, resume=None))
    else:
        if args.checkpoint is None or args.factors:
            raise ValueError('evaluation/render read exact factors from their checkpoint')
        payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
        config = get_config(payload['metadata']['settings'])
        del payload
        with research_runtime(config):
            if args.mode == 'evaluate':
                report, _ = evaluate_checkpoint(args.checkpoint, args.out,
                    num_envs=128 if args.num_envs is None else args.num_envs, scope='full_song')
            else:
                from guitar_learning.tool.demonstration.render_finger_skill import render
                report = render(args.checkpoint, args.out, scope='full_song',
                    num_envs=4 if args.num_envs is None else args.num_envs)
    if not report['completed'] or report.get('failure') is not None:
        raise RuntimeError('research run/evaluation incomplete; see report.json')


if __name__ == '__main__':
    main()
