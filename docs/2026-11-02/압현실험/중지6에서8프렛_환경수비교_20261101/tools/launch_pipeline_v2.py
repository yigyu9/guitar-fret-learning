"""진행 중 벤치 → 새 native 검증 → 학습을 GPU 중복 없이 연결한다."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE = Path(__file__).resolve().parents[1]
STATE = BASE/'pipeline_v2.json'
CHILD = None


def save(state):
    state['updated_at'] = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds')
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(STATE)


def run(state, label, command):
    global CHILD
    state.update(stage=label, command=list(map(str, command)))
    save(state)
    environment = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                       MPLCONFIGDIR=str(ROOT/'.runtime/cache/matplotlib'))
    with (BASE/(label+'_v2.log')).open('x') as stream:
        CHILD = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=environment,
                                 stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        state['child_pid'] = CHILD.pid
        save(state)
        code = CHILD.wait()
        CHILD = None
    if code:
        raise RuntimeError(label+' 종료코드 '+str(code))


def main():
    if STATE.exists():
        raise FileExistsError('기존 pipeline 보존: '+str(STATE))
    def stop(signum, frame):
        raise KeyboardInterrupt('종료 신호 '+str(signum))
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    state = dict(status='running', stage='benchmark_wait', driver_pid=os.getpid())
    save(state)
    try:
        progress = BASE/'benchmark/progress.json'
        while True:
            benchmark = json.loads(progress.read_text())
            if benchmark['status'] == 'complete':
                break
            if benchmark['status'] != 'running':
                raise RuntimeError('벤치 중단: '+str(benchmark.get('error')))
            os.kill(benchmark['driver_pid'], 0)
            if time.time()-progress.stat().st_mtime > 300:
                raise TimeoutError('벤치 진행 기록 5분 이상 정체')
            time.sleep(10)
        state['selected_envs'] = benchmark['selected_envs']
        launcher = [sys.executable, '-B', ROOT/'scripts/tab2body.py', '--cache-root', ROOT/'.runtime/cache', 'run']
        native = BASE/'validation/reference_native_v3'
        run(state, 'native_validation', launcher+[BASE/'tools/reference_native_settle030.py', '--candidate',
            BASE/'geometry/reference_v1/reference_candidates.json', '--gap', '.75', '--out', native, '--device', 'cuda:0'])
        report = json.loads((native/'report.json').read_text())
        if report.get('accepted') is not True:
            raise RuntimeError('native 참조 미통과: 새 학습 시작하지 않음; '+str(native/'report.json'))
        run(state, 'learning', [sys.executable, '-B', BASE/'tools/run_study.py', '--native-report', native/'report.json',
                               '--out', BASE/'learning_v1'])
        run(state, 'charts', [sys.executable, '-B', BASE/'tools/analyze_results.py',
                             '--study-progress', BASE/'learning_v1/progress.json', '--out', BASE/'learning_v1/analysis'])
        state.update(status='complete', stage='complete')
    except BaseException as error:
        state.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed', error=repr(error))
        raise
    finally:
        if CHILD is not None and CHILD.poll() is None:
            os.killpg(CHILD.pid, signal.SIGTERM)
            try:
                CHILD.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(CHILD.pid, signal.SIGKILL)
                CHILD.wait(timeout=30)
        save(state)


if __name__ == '__main__':
    main()
