"""C1 고정 조건 학습과 평가·분석·영상을 순차 감독한다. native 실행은 명시적 시작만 허용한다."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

SELF = Path(__file__).resolve()
STUDY = SELF.parents[1]
ROOT = next(p for p in SELF.parents if (p / 'guitar_learning/train.py').is_file())
RUNTIME_ROOT = Path(os.environ.get('C1_RUNTIME_ROOT', str(STUDY / '작업자료/runtime'))).resolve()
OUTPUT_ROOT = RUNTIME_ROOT / 'study_outputs'
PYTHON = Path('/home/ajou/miniconda3/envs/rl38/bin/python')
MODULE = 'guitar_learning.tool.experiments.press_sequence'
UPDATES, ENVS, HORIZON = 2000, 1024, 32
MIN_FREE = 8 * 1024**3
STALL_S, TRAIN_LIMIT_S = 600, 18 * 3600


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('비유한 학습 수치')
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    if isinstance(value, list):
        for item in value:
            finite(item)
    return value


def read(path):
    return finite(json.loads(Path(path).read_text()))


def write(path, value):
    finite(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def rows(path):
    """작성 중인 마지막 줄은 다음 감시 때 읽고, 완결된 줄의 오류는 즉시 중단한다."""
    if not Path(path).exists():
        return []
    return [finite(json.loads(line)) for line in Path(path).read_text().splitlines(keepends=True)
            if line.endswith('\n') and line.strip()]


def command(*args, render=False):
    result = [str(PYTHON), str(RUNTIME_ROOT / 'scripts/tab2body.py'), '--cache-root',
              str(RUNTIME_ROOT / '.runtime/cache'), 'run', '-m', MODULE, *map(str, args)]
    return ['/usr/bin/xvfb-run', '-a', *result] if render else result


def train_command(out, resume=None, committed=0):
    if not 0 <= committed < UPDATES:
        raise ValueError('재개 업데이트가 전체 예산 밖입니다.')
    common = ['train', '--out', str(out), '--updates', str(UPDATES - committed),
              '--checkpoint-every', '250']
    if resume is not None:
        common += ['--resume', str(resume)]
    else:
        common += ['C1', '--size', 'large', '--num-envs', str(ENVS), '--horizon', str(HORIZON), '--seed', '7',
                   '--improvement-profile', 'corrected', '--initial-support-std', '.15',
                   '--initial-finger-std', '.35']
    return command(*common)


def manifest_candidates(runs):
    """기록된 SHA가 맞는 모델만 후보로 인정하며 손상은 숨기지 않는다."""
    candidates = []
    for run in runs:
        for item in rows(Path(run) / 'J/checkpoint_manifest.jsonl'):
            path = Path(run) / 'J' / item['path']
            if path.parent != Path(run) / 'J' or not path.is_file() or sha(path) != item['sha256']:
                raise ValueError('checkpoint manifest SHA/위치 불일치: ' + str(path))
            candidates.append((int(item['optimizer_updates']), path, item['sha256']))
    return sorted(candidates, key=lambda row: row[0])


def inspect_checkpoint(path, expected_sha):
    """CPU 별도 프로세스에서 원본 strict reader와 합성 시계 검사를 모두 실행한다."""
    if sha(path) != expected_sha:
        raise ValueError('검사 직전 checkpoint SHA 불일치')
    sys.path.insert(0, str(RUNTIME_ROOT))
    from guitar_learning.tool.experiments import press_sequence as entry
    args = entry.parser().parse_args(['train', '--resume', str(path), '--out', '/tmp/unused-c1-inspection'])
    if entry.checked_selection(args) != 'C1':
        raise ValueError('C1 저장본만 허용됩니다.')
    settings = entry.native_entry().read_checkpoint(path)
    import torch
    payload = torch.load(path, map_location='cpu', weights_only=False)
    expected = dict(num_envs=ENVS, horizon=HORIZON, seed=7, size='large')
    if any(settings.get(key) != value for key, value in expected.items()):
        raise ValueError('고정 학습 조건 불일치')
    if settings['finger_skill']['planned_transitions'] != UPDATES * ENVS * HORIZON:
        raise ValueError('원래 전체 노출 일정이 변경되었습니다.')
    spec = settings['compact_press']
    if (spec.get('improvement_profile') != 'corrected' or
            spec.get('initial_support_std') != .15 or spec.get('initial_finger_std') != .35):
        raise ValueError('저장된 profile/초기 탐색 조건 불일치')
    if sha(path) != expected_sha:
        raise ValueError('검사 도중 checkpoint 변경')
    return dict(checkpoint=str(path), sha256=expected_sha, updates=payload['updates'])


def strict_check(path, digest):
    result = subprocess.run([str(PYTHON), str(SELF), '--inspect', str(path), '--sha', digest],
        cwd=RUNTIME_ROOT, capture_output=True, text=True, check=True, timeout=180)
    return json.loads(result.stdout.strip().splitlines()[-1])


def valid_report(out, kind, checkpoint=None):
    report = read(Path(out) / ('J/report.json' if kind == 'train' else 'report.json'))
    if not (report.get('completed') is True and report.get('failure') is None
            and report.get('lifecycle_verified') is True and report.get('changed_inputs') == []
            and not report.get('missing_import_pins') and report.get('cleanup_errors') == []):
        raise ValueError('원본 완료/소스/장면 정리 검증 실패: ' + str(out))
    if checkpoint is not None and report.get('checkpoint_sha256') != sha(checkpoint):
        raise ValueError('평가 checkpoint SHA 불일치')
    if kind == 'train':
        outer = read(Path(out) / 'report.json')
        if outer.get('completed') is not True or report['optimizer_updates'] != UPDATES:
            raise ValueError('전체 2000회 학습 미완료')
    if kind == 'evaluate' and not (report.get('scope') == 'full_song'
            and report.get('episodes') == 32 and report.get('batches') == 1
            and report.get('failed_episodes_in_denominator') is True):
        raise ValueError('고정32환경 전곡 평가 분모/범위 불일치')
    if kind == 'render' and not (report.get('scene_closed') is True
            and report.get('source_pins_unchanged') is True
            and report.get('source_checkpoint_pins_validated') is True
            and report.get('encoding_exit_codes') == {'hand': 0, 'fullbody': 0}):
        raise ValueError('영상 출처/인코딩 검증 실패')
    return report


def runtime_seal():
    """감독 중 코드·자산·목표 변경을 확인한다. 원본 실행기의 pin 검사는 별도로 유지한다."""
    paths = set((RUNTIME_ROOT / 'guitar_learning').rglob('*.py'))
    paths.update((SELF, SELF.parent / 'analyze.py'))
    for directory in ('guitar_learning/assets', 'data/song_bundles/press_sequence_c1_v1', 'scripts'):
        paths.update(p for p in (RUNTIME_ROOT / directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {str(p): sha(p) for p in sorted(paths)}


def retry_allowed(log, reason):
    """조건을 바꾸어 재시도하지 않는다. 명시적 일시 장애만 한 차례 복구한다."""
    text = Path(log).read_text(errors='replace').lower()
    fatal = ('kl guard', 'kl_guard', 'non-finite', 'nonfinite', 'nan', 'integrity',
             'sha256', 'contract', 'identity', 'changed input')
    # 감독기가 보낸 SIGINT의 KeyboardInterrupt traceback만 예외로 허용한다.
    traces = text.count('traceback (most recent call last):')
    interrupts = len(re.findall(r'^keyboardinterrupt\s*$', text, flags=re.MULTILINE))
    if 'traceback' in text and not (reason == 'stall' and traces > 0 and traces == interrupts):
        return False
    return reason in ('stall', 'process_exit') and not any(word in text for word in fatal)


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def execute(argv, name, state, *, out=None, training=False, limit=3600):
    log = STUDY / '로그' / (name.replace('/', '_') + '.log')
    log.parent.mkdir(exist_ok=True)
    if log.exists():
        raise ValueError('기존 실행 로그를 덮을 수 없습니다: ' + str(log))
    seal = state.get('runtime_seal')
    started = last_progress = time.monotonic()
    last_integrity_check = started
    previous = -1
    reason = None
    with log.open('x') as stream:
        process = subprocess.Popen(argv, cwd=RUNTIME_ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        task = dict(command=argv, log=str(log), started_at=now(), pid=process.pid)
        state.setdefault('tasks', {})[name] = task
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - started
                metrics = rows(Path(out) / 'J/learning_metrics.jsonl') if training else []
                update = int(metrics[-1]['optimizer_updates']) if metrics else 0
                if update > previous:
                    previous, last_progress = update, time.monotonic()
                if seal is not None and time.monotonic() - last_integrity_check >= 60:
                    if runtime_seal() != seal:
                        raise ValueError('감독 중 소스/입력 변경: 복구 금지')
                    last_integrity_check = time.monotonic()
                free = shutil.disk_usage(STUDY).free
                if free < MIN_FREE:
                    reason = 'disk_below_8GiB'
                elif elapsed > limit:
                    reason = 'hard_deadline'
                elif training and time.monotonic() - last_progress > STALL_S:
                    reason = 'stall'
                task.update(elapsed_s=elapsed, optimizer_updates=update, free_disk_bytes=free)
                if metrics:
                    durations = [m['collection_s'] + m['update_s'] for m in metrics[-30:]]
                    task['eta_seconds'] = (UPDATES-update)*sum(durations)/len(durations)
                state.update(current_task=name, updated_at=now())
                write(STUDY / '진행상황.json', state)
                if reason:
                    stop(process)
                    break
                time.sleep(5)
            code = process.wait()
        finally:
            stop(process)
    if seal is not None and runtime_seal() != seal:
        raise ValueError('실행 종료 시 소스/입력 변경: 복구 금지')
    task.update(returncode=code, stop_reason=reason, finished_at=now())
    write(STUDY / '진행상황.json', state)
    return code, reason or ('process_exit' if code else None), log


def supervise():
    STUDY.mkdir(parents=True, exist_ok=True)
    os.environ['C1_RUNTIME_ROOT'] = str(RUNTIME_ROOT)
    with (STUDY / 'supervisor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (STUDY / '진행상황.json').exists():
            raise ValueError('기존 감독 상태가 있습니다. 자동 중복 실행을 차단합니다.')
        state = dict(runtime_root=str(RUNTIME_ROOT), completed=False, started_at=now(), supervisor_pid=os.getpid(),
                     updates=UPDATES, num_envs=ENVS, horizon=HORIZON, recovery_limit=1)
        state['runtime_seal'] = runtime_seal()
        if not (RUNTIME_ROOT / 'guitar_learning/train.py').is_file():
            raise ValueError('봉인된 격리 runtime 사본이 먼저 필요합니다.')
        runs, resume, committed = [], None, 0
        try:
            training_started = time.monotonic()
            for attempt in (1, 2):
                remaining_s = TRAIN_LIMIT_S - (time.monotonic() - training_started)
                if remaining_s <= 0:
                    raise RuntimeError('복구 포함 전체 학습18시간 한도 초과')
                out = OUTPUT_ROOT / '학습' / ('attempt%02d' % attempt)
                if out.exists():
                    raise ValueError('기존 학습 산출물 덮기 금지')
                out.parent.mkdir(parents=True, exist_ok=True)
                runs.append(out)
                code, reason, log = execute(train_command(out, resume, committed),
                    '학습_attempt%02d' % attempt, state, out=out, training=True, limit=remaining_s)
                if code == 0 and reason is None:
                    valid_report(out, 'train')
                    break
                if attempt == 2 or not retry_allowed(log, reason):
                    raise RuntimeError('학습 중단, 자동 조건 변경 없음: ' + str(reason))
                candidates = [row for row in manifest_candidates(runs) if row[0] % 250 == 0]
                # 고정1000회 모델을 반드시 남기도록 주기 저장 경계에서만 복구한다.
                if not candidates:
                    raise ValueError('검증 가능한 복구 checkpoint 없음')
                committed, resume, digest = candidates[-1]
                checked = strict_check(resume, digest)
                if checked['updates'] != committed or committed >= UPDATES:
                    raise ValueError('복구 optimizer 횟수/예산 불일치')
                state['recovery'] = checked
            candidates = manifest_candidates(runs)
            chosen = {}
            for target, label in ((0, 'initial'), (1000, '1000'), (UPDATES, 'final')):
                matching = [row for row in candidates if row[0] == target]
                if not matching:
                    raise ValueError('고정 평가 모델 누락: ' + label)
                _, checkpoint, digest = matching[-1]
                strict_check(checkpoint, digest)
                chosen[label] = checkpoint
                out = OUTPUT_ROOT / '평가' / label
                out.parent.mkdir(parents=True, exist_ok=True)
                code, reason, _ = execute(command('evaluate', checkpoint, '--out', out,
                    '--num-envs', '32', '--scope', 'full_song'), '평가_' + label, state)
                if code or reason:
                    raise RuntimeError('평가 실행 실패: ' + label)
                valid_report(out, 'evaluate', checkpoint)
            write(STUDY / 'analysis_inputs.json', dict(
                training_runs=[str((p / 'J').resolve()) for p in runs],
                evaluation_runs=[str((OUTPUT_ROOT / '평가' / label).resolve()) for label in chosen]))
            code, reason, _ = execute([str(PYTHON), str(SELF.parent / 'analyze.py')], '분석', state)
            if code or reason:
                raise RuntimeError('분석 실행 실패')
            selected = Path(read(STUDY / '분석/분석.json')['selected_checkpoint'])
            selected = selected if selected.is_absolute() else STUDY / selected
            if selected.resolve() not in [p.resolve() for p in chosen.values()]:
                raise ValueError('분석이 고정 평가 밖 모델을 선택했습니다.')
            strict_check(selected, sha(selected))
            out = OUTPUT_ROOT / '영상원문'
            code, reason, _ = execute(command('render', selected, '--out', out, '--num-envs',
                '1', '--scope', 'full_song', render=True), '영상', state)
            if code or reason:
                raise RuntimeError('대표 영상 실행 실패')
            valid_report(out, 'render', selected)
            videos = STUDY / '동영상'
            videos.mkdir(exist_ok=True)
            for name in ('hand.mp4', 'fullbody.mp4'):
                shutil.copy2(out / name, videos / name)
            state.update(completed=True, selected_checkpoint=str(selected),
                         additional_training='자동 확장하지 않음. 분석 결과를 검토한 뒤 별도 결정')
        except BaseException as error:
            state['failure'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            state.update(finished_at=now(), current_task=None)
            write(STUDY / '진행상황.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', action='store_true', help='실제 GPU 학습과 후처리 시작')
    parser.add_argument('--inspect', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--sha', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect:
        print(json.dumps(inspect_checkpoint(args.inspect.resolve(), args.sha)))
    elif args.start:
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = '1'
        supervise()
    else:
        parser.print_help()
