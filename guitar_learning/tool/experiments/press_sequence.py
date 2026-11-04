"""C1~C6 합성 압현 목표를 선택하고 기존 v5 실행기에 전달한다.

목표 목록·검사는 CPU에서 처리한다. 학습·재개·평가·영상은 별도 프로세스에서
목표 전용 시계를 적용한 기존 v5 CLI를 사용하며 설정·정책·보상은 복제하지 않는다.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CASES = tuple('C' + str(i) for i in range(1, 7))
BUNDLES = {case: 'press_sequence_' + case.lower() + '_v1' for case in CASES}
NATIVE_MODULE = 'guitar_learning.tool.experiments.compact_press_v5'
WRAPPER_MODULE = 'guitar_learning.tool.experiments.press_sequence'


def native_entry():
    # 부모 프로세스에서는 CPU parser/검증만 사용한다. native는 새 프로세스다.
    from guitar_learning.tool.experiments import compact_press_v5
    return compact_press_v5


def command_parsers(value):
    return next(action.choices for action in value._actions
        if isinstance(action, argparse._SubParsersAction))


def parser():
    value = native_entry().parser()
    value.description = __doc__
    value.epilog = '목표를 바꾸어 재개하거나 여러 목표를 섞어 학습하지 않습니다.'
    commands = command_parsers(value)
    train = commands['train']
    train.add_argument('target', nargs='?', choices=CASES,
        help='새 학습은 C1~C6 필수. 재개에서는 저장 목표를 사용')
    # 원본 parser는 보존하고 이 parser에서만 직접 song 우회 선택을 숨긴다.
    next(action for action in train._actions if action.dest == 'song').help = argparse.SUPPRESS
    subparsers = next(action for action in value._actions if isinstance(action, argparse._SubParsersAction))
    subparsers.add_parser('list', help='여섯 목표의 등록 상태 확인')
    check = subparsers.add_parser('check', help='목표 번들과 원시 입력 정합성을 CPU로 검사')
    check.add_argument('target', nargs='?', choices=CASES)
    check.add_argument('--all', action='store_true', help='여섯 목표 모두 검사')
    return value


def checked_target(target):
    from guitar_learning.tool.prepare_press_targets import check_target
    report = check_target(target)
    if (report.get('completed') is not True or report.get('case_id') != target or
            report.get('bundle_id') != BUNDLES[target]):
        raise ValueError('완료된 등록 목표 검사 결과가 필요합니다: ' + target)
    return report


def selected_target(args, *, native=False):
    """기존 strict reader로 출처·모델을 검사한 뒤 저장 목표에 실행을 묶는다."""
    requested = getattr(args, 'target', None)
    song = getattr(args, 'song', None)
    if song is not None:
        if not native:
            raise ValueError('--song 직접 선택은 지원하지 않습니다. C1~C6로 선택하세요.')
        requested = next((case for case, bundle in BUNDLES.items() if bundle == song), None)
        if requested is None:
            raise ValueError('등록된 C1~C6 번들만 실행할 수 있습니다.')
    checkpoint = args.resume if args.command == 'train' else args.checkpoint
    if checkpoint is None:
        if requested is None:
            raise ValueError('새 학습에는 C1~C6 목표를 지정해야 합니다.')
        return requested
    settings = native_entry().read_checkpoint(checkpoint)
    bundle_id = settings.get('song_training', {}).get('song_id')
    saved = next((case for case, bundle in BUNDLES.items() if bundle == bundle_id), None)
    if saved is None:
        raise ValueError('C1~C6 합성 목표의 v5 checkpoint만 실행할 수 있습니다.')
    expected_bundle = ROOT / 'data/song_bundles' / BUNDLES[saved]
    if Path(settings['song_training']['bundle']).resolve() != expected_bundle:
        raise ValueError('저장된 번들 경로가 등록된 목표와 다릅니다.')
    if requested is not None and requested != saved:
        raise ValueError('목표를 바꾸어 재개할 수 없습니다. 저장 목표는 ' + saved + '입니다.')
    return saved


def verify_checkpoint_clock(checkpoint, report):
    """원래 v5 검증 뒤에도 합성 목표 전용 시계의 명시적 출처를 별도로 요구한다."""
    import torch
    from guitar_learning.tool.prepare_press_targets import SCHEMA
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    clock = payload.get('identity', {}).get('architecture', {}).get('contract', {}).get(
        'task', {}).get('provenance', {}).get('left_press_clock', {})
    expected = dict(schema=SCHEMA, bundle_id=report['bundle_id'],
        clock_contract_sha256=report['clock_contract_sha256'],
        onset_mapping_sha256=report['onset_mapping_sha256'])
    if (report.get('clock_schema') != SCHEMA or not isinstance(clock, dict) or
            any(clock.get(key) != value for key, value in expected.items())):
        raise ValueError('합성 목표의 명시적 압현 시계 계약이 checkpoint와 다릅니다.')


def checked_selection(args, *, native=False):
    target = selected_target(args, native=native)
    report = checked_target(target)
    checkpoint = args.resume if args.command == 'train' else args.checkpoint
    if checkpoint is not None:
        verify_checkpoint_clock(checkpoint, report)
    return target


def native_command(args):
    """원본 parser 명세로 argv를 생성해 기존 v5 옵션과 검사 동작을 재사용한다."""
    target = checked_selection(args)
    forwarded = copy.copy(args)
    if args.command == 'train' and args.resume is None:
        forwarded.song = BUNDLES[target]
    command = [sys.executable, '-m', WRAPPER_MODULE, '_native', args.command]
    original = command_parsers(native_entry().parser())[args.command]
    for action in original._actions:
        if action.dest == 'help':
            continue
        value = getattr(forwarded, action.dest)
        if value is None:
            continue
        if isinstance(value, Path):
            value = value.resolve()
        if not action.option_strings:
            command.append(str(value))
        elif action.nargs == 0:
            if value == action.const:
                command.append(action.option_strings[0])
        elif action.nargs is None:
            command.extend((action.option_strings[0], str(value)))
        else:
            raise ValueError('지원하지 않는 원본 CLI 인자 형식: ' + action.dest)
    return command


def native_main(argv):
    """새 프로세스에서만 원래 import 순서와 명시적 합성 목표 시계를 적용한다."""
    import isaacgym
    from guitar_learning.tool.prepare_press_targets import source_clock_runtime
    original = native_entry()
    args = original.parser().parse_args(argv)
    checked_selection(args, native=True)
    previous_argv = sys.argv
    try:
        sys.argv = [NATIVE_MODULE, *argv]
        with source_clock_runtime():
            original.main()
        return 0
    finally:
        sys.argv = previous_argv


def main(argv=None):
    value = parser()
    args = value.parse_args(argv)
    try:
        if args.command == 'list':
            from guitar_learning.tool.prepare_press_targets import catalog
            print(json.dumps(catalog(), ensure_ascii=False, indent=2))
            return 0
        if args.command == 'check':
            if bool(args.target) == bool(args.all):
                raise ValueError('check C1 또는 check --all 중 하나로 지정하세요.')
            selected = CASES if args.all else (args.target,)
            print(json.dumps([checked_target(case) for case in selected], ensure_ascii=False, indent=2))
            return 0
        command = native_command(args)
    except (ValueError, FileNotFoundError) as error:
        value.error(str(error))
    # shell을 사용하지 않으며 오류 코드·표준 출력·오류 출력을 그대로 전달한다.
    return subprocess.run(command, cwd=ROOT, shell=False).returncode


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '_native':
        raise SystemExit(native_main(sys.argv[2:]))
    raise SystemExit(main())
