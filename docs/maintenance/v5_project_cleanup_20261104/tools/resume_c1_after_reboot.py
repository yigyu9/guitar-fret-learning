"""재부팅으로 중단된 C1을 원본 runtime/계약 그대로 250→2000회 복구한다.

기존 run.py/analyze.py와 attempt01 원시 기록은 읽기 전용이다. --check는 CPU
검증만 수행하며 실제 실행은 --start를 명시한다. 복구 후 분석에서는 checkpoint에
반영되지 않은 attempt01의 251~256회 기록을 제외한다.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
SELF = Path(__file__).resolve()
MAINTENANCE = SELF.parents[1]
ROOT = next(path for path in SELF.parents if (path / 'guitar_learning/train.py').is_file())
STUDY = ROOT / 'docs/2026-11-09/압현_v5_C1_장기학습_v1'
RUNTIME = STUDY / '작업자료/runtime'
FIRST = RUNTIME / 'study_outputs/학습/attempt01'
SECOND = RUNTIME / 'study_outputs/학습/attempt02'
CHECKPOINT = FIRST / 'J/checkpoint_000250.pt'
EXPECTED_SHA = 'eddb749f0cc3ab0f011d10abdc6250e76668c12c6bcf33e02f70f2c8bc959d68'
COMMITTED, TOTAL = 250, 2000
BEFORE_STATE = MAINTENANCE / 'reboot_previous_state.json'
RECOVERY_STATE = STUDY / '복구진행상황.json'
os.environ['C1_RUNTIME_ROOT'] = str(RUNTIME)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = load_module('c1_original_supervisor', STUDY / '도구/run.py')


def completed_prefix(runs, reader):
    """원본 행을 복제하지 않고 복구 모델에 반영된 전역 update만 선택한다."""
    chosen = {}
    for run in runs:
        run = Path(run).resolve()
        local = set()
        for row in reader(run / 'learning_metrics.jsonl'):
            update = int(row['optimizer_updates'])
            if run == (FIRST / 'J').resolve() and update > COMMITTED:
                continue
            if update in local or update in chosen:
                raise ValueError('확정 업데이트 중복: ' + str(update))
            if int(row['update_index']) != update - 1:
                raise ValueError('전역 update_index/optimizer_updates 불일치')
            if int(row['transitions']) != old.ENVS * old.HORIZON:
                raise ValueError('확정 업데이트 전이 분모 불일치')
            local.add(update)
            chosen[update] = (run, row)
    return chosen


def protected_processes():
    """PID 재사용을 피하기 위해 실제 명령과 작업 디렉토리를 확인한다."""
    busy = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit() or int(path.name) == os.getpid():
            continue
        try:
            argv = (path / 'cmdline').read_bytes().replace(b'\x00', b' ').decode(errors='replace')
            executable = (path / 'exe').resolve().name
            cwd = (path / 'cwd').resolve()
        except (OSError, RuntimeError):
            continue
        if not executable.startswith('python'):
            continue
        active = ((str(old.SELF) in argv and '--start' in argv) or
                  (str(SELF) in argv and '--start' in argv) or
                  (cwd == RUNTIME and any(word in argv for word in
                    ('press_sequence', 'tab2body.py', 'compact_press_v5'))))
        if active:
            busy.append(dict(pid=int(path.name), command=argv, cwd=str(cwd)))
    return busy


def resources():
    busy = protected_processes()
    if busy:
        raise ValueError('기존 C1 실행 프로세스가 있습니다: ' + json.dumps(busy, ensure_ascii=False))
    gpu = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,used_gpu_memory',
        '--format=csv,noheader,nounits'], text=True, capture_output=True, check=True, timeout=15)
    if gpu.stdout.strip():
        raise ValueError('다른 GPU 계산이 실행 중입니다: ' + gpu.stdout.strip())
    info = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.free,memory.total',
        '--format=csv,noheader,nounits'], text=True, capture_output=True, check=True, timeout=15)
    free = shutil.disk_usage(STUDY).free
    if free < old.MIN_FREE:
        raise ValueError('남은 저장공간이 원래 8GiB 기준보다 작습니다.')
    return dict(gpu=info.stdout.strip(), compute_processes=[], free_disk_bytes=free)


def inspect_saved_state():
    """원본 strict reader/시계/SHA 검증에 더해 복구 노출 경계를 확인한다."""
    checked = old.strict_check(CHECKPOINT, EXPECTED_SHA)
    if checked['updates'] != COMMITTED:
        raise ValueError('복구 optimizer 업데이트는250이어야 합니다.')
    sys.path.insert(0, str(RUNTIME))
    import torch
    payload = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    expected = dict(schema='guitar_learning.finger_skill_exposure.v1',
        config=dict(planned_transitions=65536000, full_song_after=16384000),
        committed_transitions=8192000)
    if payload['metadata']['curriculum'] != expected:
        raise ValueError('원래 계획·노출 문턱·확정 노출이 다릅니다.')
    if payload['metadata']['exposure_transitions'] != dict(phrases=8192000, full_song=0):
        raise ValueError('확정 구간/전곡 노출 불일치')
    return dict(checked, curriculum=expected,
        remaining_updates=TOTAL-COMMITTED, remaining_transitions=(TOTAL-COMMITTED)*old.ENVS*old.HORIZON)


def preflight():
    if SECOND.exists():
        raise ValueError('attempt02가 이미 있습니다. 자동 덮기/중복 복구하지 않습니다.')
    previous = old.read(STUDY / '진행상황.json')
    if previous.get('completed') or previous.get('runtime_root') != str(RUNTIME):
        raise ValueError('원래 미완료 C1 감독 상태가 필요합니다.')
    if old.runtime_seal() != previous.get('runtime_seal'):
        raise ValueError('원래 runtime/감독 도구/입력 봉인이 변경되었습니다.')
    candidates = old.manifest_candidates([FIRST])
    if (COMMITTED, CHECKPOINT, EXPECTED_SHA) not in candidates:
        raise ValueError('원본 manifest의250회 모델과 SHA가 일치하지 않습니다.')
    checked = inspect_saved_state()
    metrics = completed_prefix([FIRST / 'J'], old.rows)
    if sorted(metrics) != list(range(1, COMMITTED + 1)):
        raise ValueError('원본 확정1~250회 로그 누락')
    all_rows = old.rows(FIRST / 'J/learning_metrics.jsonl')
    boot_line = next(line for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    boot_time = datetime.fromtimestamp(int(boot_line.split()[1]), timezone.utc).isoformat()
    return previous, dict(schema='press_v5_c1_reboot_recovery.v1', checked_at=old.now(),
        source_checkpoint=checked, original_state_sha256=old.sha(STUDY / '진행상황.json'),
        original_metrics_sha256=old.sha(FIRST / 'J/learning_metrics.jsonl'),
        original_metrics_rows=len(all_rows),
        excluded_uncommitted_updates=[int(row['optimizer_updates']) for row in all_rows
                                      if int(row['optimizer_updates']) > COMMITTED],
        boot_time=boot_time, resources=resources(),
        command=old.train_command(SECOND, CHECKPOINT, COMMITTED), recovery_source_sha256=old.sha(SELF))


def analyze_committed():
    """원본 분석기를 호출하되 첫 run은 checkpoint250의 확정 prefix만 읽는다."""
    original = load_module('c1_original_analysis', STUDY / '도구/analyze.py')
    original_metric_rows = original.json_rows
    original_episode_rows = original.iter_episode_rows
    inputs = old.read(STUDY / 'analysis_inputs.json')
    expected_runs = [str((path / 'J').resolve()) for path in (FIRST, SECOND)]
    if inputs['training_runs'] != expected_runs or inputs.get('committed_prefix') != {expected_runs[0]: COMMITTED}:
        raise ValueError('복구 분석의 원본 run/확정 prefix 명세 불일치')
    chosen = completed_prefix(expected_runs, original_metric_rows)
    if sorted(chosen) != list(range(1, TOTAL + 1)):
        raise ValueError('확정1~2000회 분석 분모 누락')
    accepted = {Path(run): {} for run in expected_runs}
    for run, row in chosen.values():
        accepted[run][int(row['update_index'])] = set(row['completed_episode_ids'])

    def episode_rows(run):
        run = Path(run).resolve()
        if run not in accepted:
            yield from original_episode_rows(run)
            return
        expected = {(update, episode_id) for update, ids in accepted[run].items() for episode_id in ids}
        seen = set()
        limit = max(accepted[run])
        for row in original_episode_rows(run):
            update = int(row['update_index'])
            if run == (FIRST / 'J').resolve() and update > limit:
                break
            key = (update, int(row['episode_id']))
            if key not in expected or key in seen:
                raise ValueError('확정 metrics/episode 참조가 다르거나 중복입니다.')
            seen.add(key)
            yield row
        if seen != expected:
            raise ValueError('확정 metrics가 참조한 episode 누락')

    original.metric_selection = lambda runs: completed_prefix(runs, original_metric_rows)
    original.iter_episode_rows = episode_rows
    result = original.analyze(STUDY)
    if (result['training']['unique_updates'] != TOTAL or
            result['training']['physical_transitions'] != TOTAL*old.ENVS*old.HORIZON):
        raise ValueError('최종 확정 분석의2000회/65,536,000전이 분모 불일치')
    print(json.dumps(dict(selected_checkpoint=result['selected_checkpoint'],
        unique_updates=TOTAL, physical_transitions=result['training']['physical_transitions']), ensure_ascii=False))


def supervise():
    previous, checked = preflight()
    if BEFORE_STATE.exists() or RECOVERY_STATE.exists():
        raise ValueError('기존 복구 상태가 있습니다. 중복 복구를 하지 않습니다.')
    shutil.copy2(STUDY / '진행상황.json', BEFORE_STATE)
    if old.sha(BEFORE_STATE) != checked['original_state_sha256']:
        raise ValueError('변경 전 감독 상태 보존 SHA 불일치')
    old.write(MAINTENANCE / 'reboot_preflight.json', checked)
    state = dict(runtime_root=str(RUNTIME), completed=False, started_at=old.now(), supervisor_pid=os.getpid(),
        updates=TOTAL, num_envs=old.ENVS, horizon=old.HORIZON,
        runtime_seal=previous['runtime_seal'], recovery=checked,
        previous_state=str(BEFORE_STATE), recovery_limit=0,
        resume_semantics='250회 optimizer/RNG/sampler/exposure 복원; 물리 episode는원래재개계약대로새로시작')
    old.write(STUDY / '진행상황.json', state)
    old.write(RECOVERY_STATE, state)
    try:
        SECOND.parent.mkdir(parents=True, exist_ok=True)
        code, reason, _ = old.execute(checked['command'], '재부팅복구_학습_attempt02', state,
            out=SECOND, training=True, limit=old.TRAIN_LIMIT_S)
        if code or reason:
            raise RuntimeError('동일 조건 복구 학습 중단: ' + str(reason))
        old.valid_report(SECOND, 'train')
        candidates = old.manifest_candidates([FIRST, SECOND])
        chosen = {}
        for target, label in ((0, 'initial'), (1000, '1000'), (TOTAL, 'final')):
            matching = [row for row in candidates if row[0] == target]
            if not matching:
                raise ValueError('원래 계획의 고정 평가 모델 누락: ' + label)
            _, checkpoint, digest = matching[-1]
            old.strict_check(checkpoint, digest)
            chosen[label] = checkpoint
            out = old.OUTPUT_ROOT / '평가' / label
            out.parent.mkdir(parents=True, exist_ok=True)
            code, reason, _ = old.execute(old.command('evaluate', checkpoint, '--out', out,
                '--num-envs', '32', '--scope', 'full_song'), '재부팅복구_평가_' + label, state)
            if code or reason:
                raise RuntimeError('고정 평가 실패: ' + label)
            old.valid_report(out, 'evaluate', checkpoint)
        manifest = STUDY / 'analysis_inputs.json'
        if manifest.exists():
            raise ValueError('기존 분석 입력 덮기 금지')
        old.write(manifest, dict(training_runs=[str((path / 'J').resolve()) for path in (FIRST, SECOND)],
            evaluation_runs=[str((old.OUTPUT_ROOT / '평가' / label).resolve()) for label in chosen],
            committed_prefix={str((FIRST / 'J').resolve()): COMMITTED},
            excluded_uncommitted_updates=checked['excluded_uncommitted_updates']))
        code, reason, _ = old.execute([str(old.PYTHON), '-B', str(SELF), '--analyze'],
            '재부팅복구_분석', state, limit=3600)
        if code or reason:
            raise RuntimeError('확정 prefix 분석 실패')
        selected = Path(old.read(STUDY / '분석/분석.json')['selected_checkpoint'])
        if selected.resolve() not in [path.resolve() for path in chosen.values()]:
            raise ValueError('고정 평가 밖의 모델을 선정했습니다.')
        old.strict_check(selected, old.sha(selected))
        out = old.OUTPUT_ROOT / '영상원문'
        code, reason, _ = old.execute(old.command('render', selected, '--out', out,
            '--num-envs', '1', '--scope', 'full_song', render=True), '재부팅복구_영상', state)
        if code or reason:
            raise RuntimeError('대표 영상 실패')
        old.valid_report(out, 'render', selected)
        videos = STUDY / '동영상'
        videos.mkdir(exist_ok=True)
        for name in ('hand.mp4', 'fullbody.mp4'):
            if (videos / name).exists():
                raise ValueError('기존 대표 영상 덮기 금지')
            shutil.copy2(out / name, videos / name)
        if old.sha(SELF) != checked['recovery_source_sha256']:
            raise ValueError('복구 감독 소스 변경')
        state.update(completed=True, selected_checkpoint=str(selected),
            additional_training='원래2000회만완료. 자동추가학습없음')
    except BaseException as error:
        state['failure'] = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        state.update(finished_at=old.now(), current_task=None)
        old.write(STUDY / '진행상황.json', state)
        old.write(RECOVERY_STATE, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', action='store_true', help='원본 strict checkpoint·봉인·자원·중복실행 검사만 수행')
    choice.add_argument('--start', action='store_true', help='같은 조건의1750회복구와원래후처리를명시시작')
    choice.add_argument('--analyze', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.analyze:
        return analyze_committed()
    with ExitStack() as stack:
        for path in (STUDY / 'supervisor.lock', MAINTENANCE / 'reboot_supervisor.lock'):
            lock = stack.enter_context(path.open('a'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.check:
            _, checked = preflight()
            old.write(MAINTENANCE / 'reboot_cpu_check.json', checked)
            print(json.dumps(checked, ensure_ascii=False, indent=2))
        else:
            supervise()


if __name__ == '__main__':
    main()
