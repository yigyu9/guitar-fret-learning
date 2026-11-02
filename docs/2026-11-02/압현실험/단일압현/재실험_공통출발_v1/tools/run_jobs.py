"""새 운반 재실험의 직렬 실행·진행 기록. 음성 진단도 완료 결과로 보존한다."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat(timespec='seconds')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def check(pins):
    changed = [p for p, digest in pins.items() if not Path(p).is_file() or sha(p) != digest]
    if changed:
        raise RuntimeError('IDENTITY: 입력 또는 실행 소스 변경 '+str(changed))


def stop(child):
    if child is None:
        return
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text())
    pins = {str(args.queue.resolve()): sha(args.queue), str(Path(__file__)): sha(__file__)}
    pins.update(queue['pins'])
    state_path = args.out/'state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state['pins'] != pins:
            raise ValueError('재개 시 기존 실행 입력 유지 필요')
    else:
        state = dict(schema='single18.transport_jobs.v1', started_at=now(), jobs={}, pins=pins)
    child = None

    def interrupted(signum, frame):
        raise KeyboardInterrupt('실행기 종료 신호 '+str(signum))

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def save():
        state['heartbeat'] = now()
        write(state_path, state)

    try:
        check(pins)
        state.update(status='running', driver_pid=os.getpid(), error=None)
        save()
        for job in queue['jobs']:
            key = job['key']
            prior = state['jobs'].get(key, [])
            if prior and prior[-1]['status'] == 'complete':
                check(prior[-1]['evidence'])
                continue
            if len(prior) >= 2:
                raise RuntimeError('실패 시도 상한 도달: '+key)
            for attempt in range(len(prior), 2):
                check(pins)
                if subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
                        '--format=csv,noheader'], text=True).strip():
                    raise RuntimeError('GPU_BUSY: 다른 GPU 작업이 실행 중입니다')
                folder = args.out/'jobs'/key/('attempt%02d'%(attempt+1))
                if folder.exists():
                    raise FileExistsError(folder)
                folder.parent.mkdir(parents=True, exist_ok=True)
                command = job['argv']+['--out', str(folder.resolve())]
                record = dict(status='running', started_at=now(), out=str(folder.resolve()), command=command)
                state['jobs'].setdefault(key, []).append(record)
                state['current_job'] = key
                logfile = args.out/'stdout'/(key+'_a%d.log'%(attempt+1))
                logfile.parent.mkdir(parents=True, exist_ok=True)
                environment = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
                    MPLCONFIGDIR=str(ROOT/'.runtime/cache/matplotlib'),
                    VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/nvidia_icd.json')
                started = time.monotonic()
                try:
                    with logfile.open('x') as stream:
                        child = subprocess.Popen(command, cwd=ROOT, env=environment,
                            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                        record['pid'] = child.pid
                        save()
                        while child.poll() is None:
                            if time.monotonic()-started > job.get('timeout_s', 600):
                                raise TimeoutError('작업별 실행 시간 상한')
                            save()
                            time.sleep(10)
                        code = child.returncode
                    check(pins)
                    if code:
                        raise RuntimeError('종료코드 %d: '%code+logfile.read_text(errors='replace')[-2000:])
                    report_path = folder/'report.json'
                    report = json.loads(report_path.read_text())
                    if (report.get('completed') is not True or report.get('failure')
                            or report.get('changed_inputs') or report.get('cleanup_errors')):
                        raise RuntimeError('완료·정리·입력 검증 실패: '+str(report.get('failure')))
                    evidence = {str(report_path.resolve()): sha(report_path)}
                    for video in folder.glob('*.mp4'):
                        evidence[str(video.resolve())] = sha(video)
                    record.update(status='complete', finished_at=now(), wall_s=time.monotonic()-started,
                        evidence=evidence, transport_ready=report.get('transport_ready'),
                        result_scope=report.get('scope'))
                    save()
                    break
                except Exception as error:
                    record.update(status='failed', error=str(error), finished_at=now())
                    save()
                    if 'IDENTITY:' in str(error) or attempt == 1:
                        raise
                finally:
                    stop(child)
                    child = None
        state.update(status='complete', current_job=None, finished_at=now())
    except BaseException as error:
        state.update(status='failed', error=repr(error), current_job=None, finished_at=now())
        raise
    finally:
        stop(child)
        save()


if __name__ == '__main__':
    main()
