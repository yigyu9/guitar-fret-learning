"""압현 v5: 회복 경계464/473상태·26목표와 명시적0.15/0.35 탐색.

corrected는 v4 combined 보상을 유지하는 새 입력·초기화 기준이다.
preparation/full_hold/combined는 독립 비교 조건이며 성능 채택을 뜻하지 않는다.
"""
import math
import os
from contextlib import contextmanager, nullcontext
from pathlib import Path
import sys
from types import SimpleNamespace

if __name__ == '__main__' and not any(value in ('-h', '--help') for value in sys.argv):
    import isaacgym
import torch

from guitar_learning.training.compact_press_v5 import CompactPressV5Policy, POLICY_SCHEMA, initial_stds
from guitar_learning.gpu.compact_press_v5 import (
    CompactPressV5Environment, IMPROVEMENT_PROFILES, improvement_configuration, reward_configuration,
)

SCHEMA = 'guitar_learning.compact_press.v5'
RESUME_SCHEMA = 'guitar_learning.compact_press_resume.v5'


def configuration(include_pelvis=False, improvement_profile='corrected',
                  initial_support_std=.15, initial_finger_std=.35):
    """공통 폭을 보존하고 입력·개선 조건·실제 초기 탐색을 새 계약에 기록한다."""
    improvement_configuration(improvement_profile)
    std = initial_stds(initial_support_std, initial_finger_std)
    if type(include_pelvis) is not bool:
        raise ValueError('include_pelvis must be bool')
    return dict(schema=SCHEMA, include_pelvis=include_pelvis,
        state_dim=473 if include_pelvis else 464, event_dim=26, priority_slots=8,
        additional_state_dim=21, additional_goal_dim=10,
        state_hidden=[256, 256], goal_hidden=[64, 64],
        fusion_input=768, fusion_hidden=[512, 256], value_fusion_hidden=[256, 256],
        width_selection='fixed; --size is recorded and does not change layer widths',
        reward_profile='combined', improvement_profile=improvement_profile,
        initial_support_std=std['support17'], initial_finger_std=std['finger16'])


def validate_settings(settings):
    from guitar_learning.training.finger_skill_runner import _validate_joint_settings
    spec = settings.get('compact_press', {})
    if (not isinstance(spec, dict) or type(spec.get('include_pelvis')) is not bool or
            spec != configuration(spec['include_pelvis'], spec.get('improvement_profile'),
                spec.get('initial_support_std'), spec.get('initial_finger_std'))):
        raise ValueError('compact v5 상태464/473·목표26·초기 탐색 설정 필요')
    if (settings.get('compact_press_v4') != reward_configuration() or
            settings.get('compact_press_v5') != improvement_configuration(spec['improvement_profile'])):
        raise ValueError('compact v5 개선 조건 설정 불일치')
    # 공용 실행기의 log(initial_std)+3 후처리 shift를 정확히0으로 고정한다.
    if settings.get('initial_std') != math.exp(-3):
        raise ValueError('역할별 초기 탐색 보존을 위해 공용 initial_std=exp(-3) 필요')
    fraction = 1. if spec['improvement_profile'] in ('full_hold', 'combined') else .4
    if settings.get('song', {}).get('left_fraction') != fraction:
        raise ValueError('개선 조건과 song.left_fraction 설정 불일치')
    _validate_joint_settings(settings)
    if (settings.get('song_training', {}).get('observation_dimension') != spec['state_dim'] or
            settings.get('specialist', {}).get('role') != 'left'):
        raise ValueError('compact v5 왼손 관측 차원 불일치')


def validate_metadata(metadata):
    if not isinstance(metadata, dict) or metadata.get('schema') != RESUME_SCHEMA:
        raise ValueError('compact v5 checkpoint 필요; v2/v3/v4 checkpoint는 변환하지 않음')
    validate_settings(metadata.get('settings', {}))


def read_checkpoint(checkpoint):
    from guitar_learning.portability import validate_checkpoint_inputs, localize, portable
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError('PPO checkpoint dictionary required')
    metadata = payload.get('metadata')
    validate_metadata(metadata)
    validate_checkpoint_inputs(metadata)
    settings = localize(metadata['settings'])
    spec = settings['compact_press']
    architecture = payload.get('identity', {}).get('architecture', {})
    if (architecture.get('schema') != POLICY_SCHEMA or
            architecture.get('state_dim') != spec['state_dim'] or architecture.get('event_dim') != 26):
        raise ValueError('compact v5 checkpoint architecture 불일치')
    validate_contract(settings, architecture.get('contract', {}))
    with torch.random.fork_rng(devices=[]):
        expected = CompactPressV5Policy(spec['state_dim'], event_dim=26, size=settings['size'],
            contract=architecture.get('contract'), initial_support_std=spec['initial_support_std'],
            initial_finger_std=spec['initial_finger_std']).architecture
    if portable(expected) != portable(architecture):
        raise ValueError('compact v5 전체 architecture/contract 불일치')
    if settings['song_training']['song_id'].startswith('press_sequence_'):
        from guitar_learning.tool.experiments.press_sequence import BUNDLES, ROOT, checked_target, verify_checkpoint_clock
        case = next((case for case, bundle in BUNDLES.items()
            if bundle == settings['song_training']['song_id']), None)
        if case is None:
            raise ValueError('등록되지 않은 합성 압현 목표')
        if Path(settings['song_training']['bundle']).resolve() != ROOT / 'data/song_bundles' / BUNDLES[case]:
            raise ValueError('저장된 번들 경로가 등록된 목표와 다릅니다.')
        verify_checkpoint_clock(checkpoint, checked_target(case))
    return settings


def validate_contract(settings, contract):
    """같은 신경망 모양이라도 다른 보상 조건을 섞어 복원하지 않는다."""
    expected = settings['compact_press_v5']
    if (not isinstance(contract, dict) or
            contract.get('reward', {}).get('schema') != 'guitar_learning.compact_press_reward.v5' or
            contract.get('reward', {}).get('compact_press_v4') != settings['compact_press_v4'] or
            contract.get('reward', {}).get('compact_press_v5') != expected):
        raise ValueError('compact v5 개선 조건/환경 contract 불일치')


@contextmanager
def runtime():
    from guitar_learning.training import rollout, finger_skill_runner as runner
    import inspect
    original = (rollout.GpuPool, runner._policy, runner.resume_schema,
        runner._validate_metadata_schema, runner._pins, runner.SCHEMA)
    base_pool, base_pins = original[0], original[4]

    class CompactV5Pool(base_pool):
        def __init__(self, settings, out):
            validate_settings(settings)
            self.environment_class_override = type('SelectedCompactV5Environment',
                (CompactPressV5Environment,), dict(include_pelvis=settings['compact_press']['include_pelvis'],
                    reward_profile='combined', improvement_profile=settings['compact_press']['improvement_profile']))
            super().__init__(settings, out)

    def policy(settings, pool):
        validate_settings(settings)
        validate_contract(settings, pool.contract)
        return CompactPressV5Policy(pool.observation['state'].shape[-1], event_dim=26,
            size=settings['size'], contract=pool.contract,
            initial_support_std=settings['compact_press']['initial_support_std'],
            initial_finger_std=settings['compact_press']['initial_finger_std']).to(settings['device'])

    def resume_schema(settings):
        validate_settings(settings)
        return RESUME_SCHEMA

    def pins(settings, out, extra=()):
        paths = [Path(__file__).resolve(), Path(inspect.getsourcefile(CompactPressV5Environment)).resolve(),
                 Path(inspect.getsourcefile(CompactPressV5Policy)).resolve()]
        return base_pins(settings, out, list(extra)+paths)

    rollout.GpuPool, runner._policy = CompactV5Pool, policy
    runner.resume_schema, runner._validate_metadata_schema = resume_schema, validate_metadata
    runner._pins, runner.SCHEMA = pins, SCHEMA
    try:
        yield
    finally:
        (rollout.GpuPool, runner._policy, runner.resume_schema,
            runner._validate_metadata_schema, runner._pins, runner.SCHEMA) = original


def build_settings(*, include_pelvis=False, improvement_profile='corrected',
                   initial_support_std=.15, initial_finger_std=.35, **options):
    from guitar_learning.training.launch import build_settings as common_settings
    # settings_document는 V5 기본 facade이므로 공통 생성기를 직접 호출한다.
    song = options.get('song')
    with clock_runtime(song):
        settings = common_settings('left', learning_family='finger-skill', **options)
    settings['compact_press'] = configuration(include_pelvis, improvement_profile,
        initial_support_std, initial_finger_std)
    settings['compact_press_v4'] = reward_configuration()
    settings['compact_press_v5'] = improvement_configuration(improvement_profile)
    settings['initial_std'] = math.exp(-3)
    settings['song']['left_fraction'] = 1. if improvement_profile in ('full_hold', 'combined') else .4
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
                raise ValueError('Resume must preserve saved '+key)
        if args.include_pelvis is not None and args.include_pelvis != settings['compact_press']['include_pelvis']:
            raise ValueError('Resume must preserve saved include_pelvis')
        for key in ('improvement_profile', 'initial_support_std', 'initial_finger_std'):
            if getattr(args, key) is not None and getattr(args, key) != settings['compact_press'][key]:
                raise ValueError('재개에서는 저장된 ' + key + '을 유지해야 함')
        settings['updates'] = args.updates
        if args.checkpoint_every is not None:
            settings['checkpoint_every'] = args.checkpoint_every
    else:
        options = {key: getattr(args, key) for key in
            ('song', 'size', 'num_envs', 'horizon', 'seed', 'checkpoint_every') if getattr(args, key) is not None}
        settings = build_settings(updates=args.updates, include_pelvis=bool(args.include_pelvis),
            improvement_profile=args.improvement_profile or 'corrected',
            initial_support_std=.15 if args.initial_support_std is None else args.initial_support_std,
            initial_finger_std=.35 if args.initial_finger_std is None else args.initial_finger_std, **options)
    if args.max_wall_seconds is not None:
        settings['max_wall_seconds'] = args.max_wall_seconds
    validate_settings(settings)
    with clock_runtime(settings['song_training']['song_id']), runtime():
        return runner.run(settings, SimpleNamespace(out=args.out, resume=args.resume))


def evaluate(checkpoint, out, *, num_envs=None, scope='full_song'):
    from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
    settings = read_checkpoint(checkpoint)
    with clock_runtime(settings['song_training']['song_id']), runtime():
        return evaluate_checkpoint(checkpoint, out, num_envs=num_envs, scope=scope)


def render(checkpoint, out, *, num_envs=None, scope='full_song'):
    from guitar_learning.tool.demonstration.render_finger_skill import _render as native_render
    settings = read_checkpoint(checkpoint)
    with clock_runtime(settings['song_training']['song_id']), runtime():
        return native_render(checkpoint, out, num_envs=num_envs, scope=scope)


def parser():
    import argparse
    from guitar_learning.training.launch import add_train_arguments
    result = argparse.ArgumentParser(description=__doc__,
        epilog='고정 폭768→512→256→33. 기본corrected는 보상 변경 대조 기준입니다.')
    commands = result.add_subparsers(dest='command', required=True)
    add_train_arguments(commands.add_parser('train'))
    for name in ('evaluate', 'render'):
        command = commands.add_parser(name)
        command.add_argument('checkpoint', type=Path)
        command.add_argument('--out', type=Path, required=True)
        command.add_argument('--num-envs', type=int)
        command.add_argument('--scope', choices=('full_song', 'phrases'), default='full_song')
    return result


def clock_runtime(song):
    """C1~C6만 검증된 원본 압현 시계를 사용하고 일반 곡의 시계는 보존한다."""
    if song is None or not song.startswith('press_sequence_'):
        return nullcontext()
    from guitar_learning.tool.experiments.press_sequence import BUNDLES, checked_target
    case = next((case for case, bundle in BUNDLES.items() if bundle == song), None)
    if case is None:
        raise ValueError('등록되지 않은 합성 압현 목표')
    checked_target(case)
    from guitar_learning.song import task
    from guitar_learning.gpu import environment
    from guitar_learning.tool.prepare_press_targets import source_clock_task, source_clock_runtime
    # C 전용 CLI가 이미 설치한 동일 adapter는 중첩해서 설치하지 않는다.
    already_installed = task.make_task is source_clock_task and environment.make_task is source_clock_task
    return nullcontext() if already_installed else source_clock_runtime()


def main():
    args = parser().parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    if args.command == 'train':
        if args.updates < 1 or (args.checkpoint_every is not None and args.checkpoint_every < 1):
            raise ValueError('Positive update count and checkpoint interval required')
        if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0):
            raise ValueError('Positive finite time budget required')
        return train(args)
    return globals()[args.command](args.checkpoint, args.out, num_envs=args.num_envs, scope=args.scope)


if __name__ == '__main__':
    main()
