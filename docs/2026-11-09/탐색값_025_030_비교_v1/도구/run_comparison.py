"""표준편차 0.25와 0.30의 학습·평가·영상 생성을 순서대로 실행한다.

기존 학습기를 수정하거나 가져오지 않는다. 각 단계의 봉인과 종료 보고서를
확인한 뒤에만 다음 단계로 넘어가며 실패한 출력은 그대로 보존한다.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

SELF = Path(__file__).resolve()
STUDY = SELF.parents[1]
ROOT = SELF.parents[4]
PROOF = STUDY / '검증/조건동일성.json'
STATE = STUDY / '진행상황.json'
PYTHON = Path('/home/ajou/miniconda3/envs/rl38/bin/python')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def verify(pins):
    changed = [path for path, expected in pins.items()
               if not Path(path).is_file() or sha(path) != expected]
    if changed:
        raise RuntimeError('봉인 불일치: ' + ', '.join(changed))


def initial_pins():
    proof = read(PROOF)
    if proof.get('completed') is not True:
        raise ValueError('조건 동일성 검증이 완료되지 않았습니다.')
    reference = Path(proof['reference_input_pins'])
    pins = read(reference)
    if len(pins) != 542:
        raise ValueError('기준 입력은 정확히 542개여야 합니다.')
    for label, value in [('std025', .25), ('std030', .30)]:
        case = proof['cases'][label]
        differences = case['settings_differences']
        if case['std_initial'] != value or len(differences) != 1:
            raise ValueError('단독 변수 검증이 일치하지 않습니다.')
        if differences[0]['field'] != '/natural_press/finger_initial_std':
            raise ValueError('표준편차 이외의 설정 변경이 있습니다.')
    pins.update({str(reference): proof['reference_input_pins_sha256'],
                 proof['runtime']: proof['runtime_sha256'],
                 proof['reference_checkpoint']: proof['reference_checkpoint_sha256'],
                 str(PROOF): sha(PROOF), str(SELF): sha(SELF),
                 str(ROOT / 'scripts/tab2body.py'): sha(ROOT / 'scripts/tab2body.py')})
    verify(pins)
    return proof, pins


def gpu_processes():
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name',
                             '--format=csv,noheader,nounits'], check=True,
                            text=True, capture_output=True, timeout=15)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def close_group(process):
    """주 프로세스가 끝났어도 같은 그룹의 자식 프로세스까지 정리한다."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def valid_report(out, kind, checkpoint=None):
    report_path = out / ('J/report.json' if kind == 'train' else 'report.json')
    report = read(report_path)
    if not (report.get('completed') is True and report.get('failure') is None
            and report.get('lifecycle_verified') is True
            and report.get('changed_inputs') == []
            and not report.get('missing_import_pins')
            and report.get('cleanup_errors') == []):
        raise ValueError('종료·봉인·정리 검증 실패: ' + str(report_path))
    if checkpoint is not None and report.get('checkpoint_sha256') != sha(checkpoint):
        raise ValueError('보고서의 체크포인트 SHA 불일치')
    if kind == 'train':
        outer = read(out / 'report.json')
        if not (outer.get('completed') is True and outer.get('failure') is None
                and outer.get('final_phase') == 'J'
                and len(outer.get('stages', [])) == 1
                and outer['stages'][0].get('report') == report
                and Path(outer['final_checkpoint']) == out / 'J/final.pt'):
            raise ValueError('최상위 학습 종료 보고서가 유효하지 않습니다.')
        metrics = [json.loads(line) for line in (out / 'J/learning_metrics.jsonl').read_text().splitlines()]
        if (report.get('optimizer_updates') != 100 or len(metrics) != 100
                or metrics[-1]['optimizer_updates'] != 100
                or not (out / 'J/final.pt').is_file()
                or not (out / 'J/checkpoint_000050.pt').is_file()):
            raise ValueError('100회 학습 및 50회/최종 체크포인트가 필요합니다.')
        return {'updates': 100, 'transitions': report['transitions']}
    if kind == 'render':
        if not (report.get('scene_closed') is True
                and report.get('source_pins_unchanged') is True
                and report.get('source_checkpoint_pins_validated') is True
                and report.get('encoding_exit_codes') == {'hand': 0, 'fullbody': 0}
                and all((out / name).stat().st_size > 0 for name in ('hand.mp4', 'fullbody.mp4'))):
            raise ValueError('영상 생성·장면 정리 검증 실패')
        return {'frames': report['frames'], 'episode': episode_metrics([report['episode']])}
    episodes = [json.loads(line)['episode'] for line in (out / 'episodes.jsonl').read_text().splitlines()]
    if len(episodes) != 16 or report.get('summary', {}).get('count') != 16:
        raise ValueError('평가 분모는 완료·실패를 포함한 16개여야 합니다.')
    return episode_metrics(episodes)


def episode_metrics(episodes):
    """달성, 안전, 누적 clean과 연속 유지의 서로 다른 분모를 보존한다."""
    values = [episode['left_note_ledger']['values'] for episode in episodes]
    def safe(episode):
        termination = episode['termination']
        return (episode['valid'] and episode['song']['stage_success']
                and not episode['song']['safety_invalidated']
                and not termination['physical_failure'] and not termination['wrist_failure'])
    return {
        'denominator': len(episodes),
        'invalid_episodes': sum(not e['valid'] for e in episodes),
        'safe_success': sum(safe(e) and e['song']['left_success_count'] == e['song']['target_count'] for e in episodes),
        'achieved_notes': sum(e['song']['left_success_count'] for e in episodes),
        'mean_clean_fraction': sum(e['song']['mean_clean_audible_fraction'] for e in episodes) / len(episodes),
        'mean_cumulative_clean_s': sum(sum(v['clean']) for v in values) / len(values),
        'mean_best_clean_streak_s': sum(max(v['best_clean_streak']) for v in values) / len(values),
        'max_best_clean_streak_s': max(max(v['best_clean_streak']) for v in values),
        'full_1p5s_episodes': sum(safe(e) and max(v['best_clean_streak']) >= 1.5 - 1e-6
                                 for e, v in zip(episodes, values)),
        'wrong_s': sum(sum(v['wrong']) for v in values),
        'missing_s': sum(sum(v['missing']) for v in values),
        'physical_failure': sum(e['termination']['physical_failure'] for e in episodes),
        'wrist_failure': sum(e['termination']['wrist_failure'] for e in episodes),
    }


def manifest(out):
    return {str(path): sha(path) for path in sorted(out.rglob('*')) if path.is_file()}


def next_output(label):
    output = STUDY / '실행' / label
    attempt = 1
    while output.exists() or (STUDY / '실행/작업로그' / (output.name + '.log')).exists():
        attempt += 1
        output = STUDY / '실행' / (label + '_attempt%02d' % attempt)
    return output, attempt


def command(proof, label, kind, out, train_out):
    base = [str(PYTHON), '-B', str(ROOT / 'scripts/tab2body.py'),
            '--cache-root', str(ROOT / '.runtime/cache'), 'run', '-B', proof['runtime']]
    if kind == 'train':
        return base + ['train', '--out', str(out), '--updates', '100', '--num-envs', '64',
                       '--size', 'large', '--horizon', '32', '--seed', '7',
                       '--checkpoint-every', '50', '--std-initial', str(proof['cases'][label]['std_initial'])], None
    checkpoint = train_out / 'J' / ('checkpoint_000050.pt' if kind == 'eval50' else 'final.pt')
    action = 'render' if kind == 'render' else 'evaluate'
    return base + [action, '--checkpoint', str(checkpoint), '--out', str(out),
                   '--num-envs', '1' if kind == 'render' else '16'], checkpoint


def run(state, key, args, out, timeout, pins):
    log = STUDY / '실행/작업로그' / (out.name + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[name] = '1'
    verify(pins)
    process = None
    started = time.monotonic()
    try:
        with log.open('xb') as stream:
            process = subprocess.Popen(args, cwd=ROOT, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True, shell=False)
            state.update(status='실행 중', current_task=key, child_pid=process.pid,
                         log=str(log), command=args, started_at=stamp())
            while process.poll() is None:
                state['updated_at'] = stamp()
                save(STATE, state)
                if time.monotonic() - started >= timeout:
                    raise TimeoutError('작업 시간 제한 초과: ' + key)
                time.sleep(5)
            if process.returncode != 0:
                raise RuntimeError('작업 종료 코드 %s: %s' % (process.returncode, log))
    finally:
        if process is not None:
            close_group(process)
        state.update(child_pid=None, updated_at=stamp())
        save(STATE, state)
        verify(pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    proof, pins = initial_pins()
    if args.plan:
        print(json.dumps({'순서': ['std025 학습100/평가50/평가100/영상', 'std030 학습100/평가50/평가100/영상'],
                          '기준_입력_수': 542, '전체_봉인_수': len(pins), 'GPU_실행': False}, ensure_ascii=False))
        return
    lock_path = STUDY / '실행/driver.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = lock_path.open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = read(STATE) if STATE.exists() else {}
    if state.get('driver_pins') and state['driver_pins'] != pins:
        raise ValueError('이전 드라이버/입력 봉인과 달라 재사용할 수 없습니다.')
    state.update(schema='std025_std030_sequential.v1', driver_pid=os.getpid(),
                 driver_pins=pins, updated_at=stamp(), completed=False, failure=None)
    state.setdefault('tasks', {})
    def interrupted(signum, frame):
        raise KeyboardInterrupt('중단 신호 %s' % signum)
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, interrupted)
    try:
        for label in ('std025', 'std030'):
            train_out = None
            for kind, suffix in [('train', '_s7'), ('eval50', '_eval50'), ('eval100', '_eval100'), ('render', '_render100')]:
                key = label + suffix
                item = state['tasks'].get(key)
                verify(pins)
                if item and item.get('completed'):
                    verify(item['artifacts'])
                    out = Path(item['out'])
                    _, checkpoint = command(proof, label, kind, out, train_out)
                    valid_report(out, kind if kind == 'train' else ('render' if kind == 'render' else 'evaluate'), checkpoint)
                else:
                    out, attempt = next_output(key)
                    state['tasks'][key] = {'completed': False, 'out': str(out), 'attempt': attempt}
                    while True:
                        verify(pins)
                        occupied = gpu_processes()
                        if not occupied:
                            break
                        state.update(status='GPU 대기', current_task=key, gpu_processes=occupied, updated_at=stamp())
                        save(STATE, state)
                        time.sleep(10)
                    cmd, checkpoint = command(proof, label, kind, out, train_out)
                    run(state, key, cmd, out, 3600 if kind == 'train' else 1200, pins)
                    result = valid_report(out, kind if kind == 'train' else ('render' if kind == 'render' else 'evaluate'), checkpoint)
                    state['tasks'][key].update(completed=True, result=result, artifacts=manifest(out), finished_at=stamp())
                    save(STATE, state)
                if kind == 'train':
                    train_out = out
                if kind == 'render':
                    videos = STUDY / '동영상'
                    videos.mkdir(exist_ok=True)
                    for name in ('hand', 'fullbody'):
                        source = out / (name + '.mp4')
                        target = videos / (label + '_' + name + '.mp4')
                        if target.exists():
                            if sha(target) != sha(source):
                                raise ValueError('대표 영상이 기존 원본과 다릅니다: ' + str(target))
                        else:
                            os.link(source, target)
            state['updated_at'] = stamp()
            save(STATE, state)
        verify(pins)
        state.update(status='완료', completed=True, current_task=None, finished_at=stamp())
    except BaseException as error:
        state.update(status='중단 또는 오류', failure=repr(error), completed=False, updated_at=stamp())
        raise
    finally:
        state.update(driver_pid=None, child_pid=None, updated_at=stamp())
        save(STATE, state)
        lock.close()


def self_test():
    """GPU 없이 원자 저장, 변조 거부, 보고서 거부, 프로세스 정리를 검사한다."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / '상태.json'
        save(path, {'completed': False})
        assert read(path) == {'completed': False}
        pins = {str(path): sha(path)}
        verify(pins)
        save(path, {'completed': True})
        try:
            verify(pins)
        except RuntimeError:
            pass
        else:
            raise AssertionError('변조 검출 실패')
        save(root / 'report.json', {'completed': False})
        try:
            valid_report(root, 'evaluate')
        except ValueError:
            pass
        else:
            raise AssertionError('미완료 보고서 거부 실패')
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
        close_group(process)
        assert process.poll() is not None
        global STUDY
        original = STUDY
        try:
            STUDY = root
            (root / '실행/작업로그').mkdir(parents=True)
            (root / '실행/작업로그/검사.log').touch()
            assert next_output('검사')[1] == 2
        finally:
            STUDY = original
        with (root / '중복실행.lock').open('a') as first, (root / '중복실행.lock').open('a') as second:
            fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise AssertionError('중복 실행 잠금 실패')
    reference = ROOT / 'docs/2026-11-09/탐색값_015_020_비교_v1/실행'
    checkpoint = reference / 'std020_s7/J/final.pt'
    valid_report(reference / 'std020_s7', 'train')
    for update in (50, 100):
        selected = reference / 'std020_s7/J' / ('checkpoint_000050.pt' if update == 50 else 'final.pt')
        result = valid_report(reference / ('std020_eval%d' % update), 'evaluate', selected)
        assert result['denominator'] == 16
    result = valid_report(reference / 'std020_render100', 'render', checkpoint)
    assert result['episode']['denominator'] == 1
    invalid = read(reference / 'std020_render100/report.json')['episode']
    invalid['valid'] = False
    invalid['left_note_ledger']['values']['best_clean_streak'] = [1.5]
    result = episode_metrics([invalid])
    assert result['denominator'] == 1 and result['invalid_episodes'] == 1
    assert result['safe_success'] == 0 and result['full_1p5s_episodes'] == 0
    print('CPU 검사 통과: 원자 저장, SHA 변조·미완료 보고서 거부, 프로세스 그룹 정리, 로그만 남은 실패 재시도, 실제 기준 학습·평가50/100·렌더 보고서 수용. GPU 실행 없음.')


if __name__ == '__main__':
    main()
