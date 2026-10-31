"""GPU 작업을 하나씩 실행하고 실제 시작·종료를 기록한다. 중복 실행은 거부한다."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
KEYS = ('PATH', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'CUDA_VISIBLE_DEVICES',
        'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'PYTHONUNBUFFERED')


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def pins():
    seal = json.loads((HERE/'preparation_seal.json').read_text())
    result = dict(seal['input_pins'])
    result.update(seal['review_documents_sha256'])
    result[str(HERE/'preparation_seal.json')] = hashlib.sha256((HERE/'preparation_seal.json').read_bytes()).hexdigest()
    for name, expected in result.items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Execution input changed: '+name)
    return result


def main():
    def stop(signum, frame):
        raise KeyboardInterrupt('Supervisor received signal %d'%signum)
    signal.signal(signal.SIGTERM, stop)
    folder = HERE/'execution_schedule'
    folder.mkdir(exist_ok=True)
    environment = {key: os.environ[key] for key in KEYS if key in os.environ}
    write(folder/'launch_lock.json', dict(supervisor_pid=os.getpid(),
        start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]),
        started_utc=datetime.datetime.utcnow().isoformat(), argv=sys.argv, cwd=str(ROOT)))
    jobs = [(name, ['--phase', 'preflight', '--control', name]) for name in ('reference', 'zero')]
    jobs += [('train', ['--phase', 'train'])]
    jobs += [('evaluation_%06d'%update, ['--phase', 'evaluate', '--update', str(update), '--sampling', 'mean'])
             for update in (0, 50, 100, 150, 200, 250, 300)]
    jobs += [('evaluation_000300_stochastic', ['--phase', 'evaluate', '--update', '300', '--sampling', 'stochastic'])]
    for name, arguments in jobs:
        before = pins()
        subprocess.run([sys.executable, '-B', str(HERE/'experiment.py'), 'gate'], cwd=str(ROOT), env=environment, check=True)
        command = [sys.executable, '-B', str(HERE/'experiment.py'), 'execute']+arguments
        child, failure, cleanup, code = None, None, [], None
        try:
            with (folder/(name+'.log')).open('x') as log:
                child = subprocess.Popen(command, cwd=str(ROOT), env=environment, stdout=log, stderr=subprocess.STDOUT)
                start = int(Path('/proc/%d/stat'%child.pid).read_text().rsplit(')', 1)[1].split()[19])
                write(folder/(name+'_process.json'), dict(pid=child.pid, start_ticks=start, argv=command,
                    cwd=str(ROOT), environment=environment, started_utc=datetime.datetime.utcnow().isoformat(), input_pins=before))
                code = child.wait()
            if code != 0:
                raise RuntimeError('%s exited %s'%(name, code))
            if pins() != before:
                raise RuntimeError('Execution seal changed')
        except BaseException as error:
            failure = repr(error)
            raise
        finally:
            try:
                if child is not None:
                    if child.poll() is None:
                        child.terminate()
                    try:
                        code = child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        code = child.wait(timeout=10)
            except BaseException as error:
                cleanup.append(repr(error))
            try:
                write(folder/(name+'_exit.json'), dict(returncode=code, failure=failure, cleanup_errors=cleanup,
                    process_terminal=child is None or child.poll() is not None, finished_utc=datetime.datetime.utcnow().isoformat()))
            except BaseException as error:
                if failure is None:
                    raise
                print('Exit record failed while preserving original failure: '+repr(error), file=sys.stderr)
        if cleanup:
            raise RuntimeError('Child cleanup failed: '+repr(cleanup))
    write(folder/'completed.json', dict(completed=True, jobs=len(jobs), finished_utc=datetime.datetime.utcnow().isoformat()))


if __name__ == '__main__':
    main()
