"""기존 압현 학습을 보존하는 상태443·목표16 전용 실행 도구.

기본 실행과 별개로 새 관측·정책 계약을 사용한다. 보상·물리·J33 직접 제어와
엄격한 소스/자산/체크포인트 검증은 기존 실행기의 동작을 그대로 사용한다.
"""
import argparse
import math
import os
from contextlib import contextmanager
from pathlib import Path
import sys
from types import SimpleNamespace

# Isaac Gym은 실제 실행에서 Torch보다 먼저 불러와야 한다.
if __name__ == '__main__' and not any(value in ('-h', '--help') for value in sys.argv):
    import isaacgym
import torch

from guitar_learning.gpu.compact_press import CompactPressEnvironment
from guitar_learning.training.compact_press import CompactPressPolicy

SCHEMA = 'guitar_learning.compact_press.v1'
RESUME_SCHEMA = 'guitar_learning.compact_press_resume.v1'
POLICY_SCHEMA = 'guitar_learning.compact_press_policy.v1'


def configuration(include_pelvis=False):
    """관측 차원과 고정 신경망 크기를 저장 계약으로 명시한다."""
    if type(include_pelvis) is not bool:
        raise ValueError('include_pelvis는 bool이어야 함')
    return dict(schema=SCHEMA, include_pelvis=include_pelvis,
        state_dim=452 if include_pelvis else 443, event_dim=16, priority_slots=8,
        state_hidden=[256, 256], goal_hidden=[64, 64],
        fusion_input=768, fusion_hidden=[256, 256])


def validate_settings(settings):
    """구형 설정의 암묵적 변환과 부분적인 차원 변경을 거부한다."""
    from guitar_learning.training.finger_skill_runner import _validate_joint_settings
    spec = settings.get('compact_press', {})
    if (not isinstance(spec, dict) or type(spec.get('include_pelvis')) is not bool or
            spec != configuration(spec['include_pelvis'])):
        raise ValueError('상태443/452·목표16 전용 compact_press 설정 필요')
    _validate_joint_settings(settings)
    if settings.get('song_training', {}).get('observation_dimension') != spec['state_dim']:
        raise ValueError('compact_press 관측 차원 설정 불일치')


def validate_metadata(metadata):
    if not isinstance(metadata, dict) or metadata.get('schema') != RESUME_SCHEMA:
        raise ValueError('compact_press 전용 checkpoint 필요; 기존 정책 변환은 지원하지 않음')
    validate_settings(metadata.get('settings', {}))


def read_checkpoint(checkpoint):
    """설정·소스 봉인을 먼저 검사하고, 실제 가중치는 기존 PPO가 엄격 복원한다."""
    from guitar_learning.portability import validate_checkpoint_inputs, localize
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError('PPO checkpoint 사전 필요')
    metadata = payload.get('metadata')
    validate_metadata(metadata)
    spec = metadata['settings']['compact_press']
    architecture = payload.get('identity', {}).get('architecture', {})
    if (architecture.get('schema') != POLICY_SCHEMA or
            architecture.get('state_dim') != spec['state_dim'] or
            architecture.get('event_dim') != 16):
        raise ValueError('compact_press checkpoint architecture 불일치')
    validate_checkpoint_inputs(metadata)
    return localize(metadata['settings'])


@contextmanager
def runtime():
    """명시 실행 범위에서만 factory를 바꾸고 예외 발생 시에도 원래 값으로 복원한다."""
    from guitar_learning.training import rollout, finger_skill_runner as runner
    import inspect
    original = (rollout.GpuPool, runner._policy, runner.resume_schema,
        runner._validate_metadata_schema, runner._pins, runner.SCHEMA)
    base_pool, base_pins = original[0], original[4]

    class CompactPool(base_pool):
        def __init__(self, settings, out):
            validate_settings(settings)
            # 환경 생성 전에 정하며, 공용 환경 클래스의 전역 속성은 변경하지 않는다.
            self.environment_class_override = type('SelectedCompactEnvironment',
                (CompactPressEnvironment,),
                dict(include_pelvis=settings['compact_press']['include_pelvis']))
            super().__init__(settings, out)

    def policy(settings, pool):
        validate_settings(settings)
        return CompactPressPolicy(pool.observation['state'].shape[-1], event_dim=16,
            size=settings['size'], contract=pool.contract).to(settings['device'])

    def resume_schema(settings):
        validate_settings(settings)
        return RESUME_SCHEMA

    def pins(settings, out, extra=()):
        paths = [Path(__file__).resolve(),
            Path(inspect.getsourcefile(CompactPressEnvironment)).resolve(),
            Path(inspect.getsourcefile(CompactPressPolicy)).resolve()]
        return base_pins(settings, out, list(extra) + paths)

    rollout.GpuPool, runner._policy = CompactPool, policy
    runner.resume_schema, runner._validate_metadata_schema = resume_schema, validate_metadata
    runner._pins, runner.SCHEMA = pins, SCHEMA
    try:
        yield
    finally:
        (rollout.GpuPool, runner._policy, runner.resume_schema,
            runner._validate_metadata_schema, runner._pins, runner.SCHEMA) = original


def build_settings(*, include_pelvis=False, **options):
    from guitar_learning.training.launch import settings_document
    settings = settings_document(**options)
    settings['compact_press'] = configuration(include_pelvis)
    settings['song_training']['observation_dimension'] = settings['compact_press']['state_dim']
    return settings


def train(args):
    from guitar_learning.training import finger_skill_runner as runner
    if args.resume:
        settings = read_checkpoint(args.resume)
        for key in ('song', 'size', 'num_envs', 'horizon', 'seed'):
            requested = getattr(args, key)
            saved = settings['song_training']['song_id'] if key == 'song' else settings[key]
            if requested is not None and requested != saved:
                raise ValueError('재개에서는 저장된 ' + key + '을 유지해야 함')
        if args.include_pelvis is not None and args.include_pelvis != settings['compact_press']['include_pelvis']:
            raise ValueError('재개에서는 저장된 include_pelvis를 유지해야 함')
        settings['updates'] = args.updates
        if args.checkpoint_every is not None:
            settings['checkpoint_every'] = args.checkpoint_every
    else:
        options = {key: getattr(args, key) for key in
            ('song', 'size', 'num_envs', 'horizon', 'seed', 'checkpoint_every')
            if getattr(args, key) is not None}
        settings = build_settings(updates=args.updates,
            include_pelvis=bool(args.include_pelvis), **options)
    if args.max_wall_seconds is not None:
        settings['max_wall_seconds'] = args.max_wall_seconds
    validate_settings(settings)
    with runtime():
        return runner.run(settings, SimpleNamespace(out=args.out, resume=args.resume))


def evaluate(checkpoint, out, *, num_envs=None, scope='full_song'):
    from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
    read_checkpoint(checkpoint)
    with runtime():
        return evaluate_checkpoint(checkpoint, out, num_envs=num_envs, scope=scope)


def render(checkpoint, out, *, num_envs=None, scope='full_song'):
    from guitar_learning.tool.demonstration.render_finger_skill import render as native_render
    read_checkpoint(checkpoint)
    with runtime():
        return native_render(checkpoint, out, num_envs=num_envs, scope=scope)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    command = commands.add_parser('train')
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--song')
    command.add_argument('--size', choices=('small', 'medium', 'large'))
    command.add_argument('--num-envs', type=int)
    command.add_argument('--updates', type=int, default=100)
    command.add_argument('--horizon', type=int)
    command.add_argument('--seed', type=int)
    command.add_argument('--checkpoint-every', type=int)
    command.add_argument('--resume', type=Path)
    command.add_argument('--max-wall-seconds', type=float)
    # None과 False를 구분하여 재개 시 옵션 생략은 저장 설정을 따르게 한다.
    pelvis = command.add_mutually_exclusive_group()
    pelvis.add_argument('--include-pelvis', dest='include_pelvis', action='store_true')
    pelvis.add_argument('--no-include-pelvis', dest='include_pelvis', action='store_false')
    command.set_defaults(include_pelvis=None)
    for name in ('evaluate', 'render'):
        command = commands.add_parser(name)
        command.add_argument('checkpoint', type=Path)
        command.add_argument('--out', type=Path, required=True)
        command.add_argument('--num-envs', type=int)
        command.add_argument('--scope', choices=('full_song', 'phrases'), default='full_song')
    return result


def main():
    args = parser().parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    if args.command == 'train':
        if args.updates < 1 or (args.checkpoint_every is not None and args.checkpoint_every < 1):
            raise ValueError('반복과 저장 간격은 양수 필요')
        if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0):
            raise ValueError('시간 예산은 유한 양수 필요')
        return train(args)
    return globals()[args.command](args.checkpoint, args.out, num_envs=args.num_envs, scope=args.scope)


if __name__ == '__main__':
    main()
