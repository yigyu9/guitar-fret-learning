"""Run the sealed E4 condition after the original sweep and baseline queue."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from run_improved_job import STUDY, ROOT, GPU_UUID, digest, inside, verify_manifest, readiness
from parallel_queue_v1 import stop_own_group


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def run(path):
    path = inside(path); manifest = verify_manifest(path); expected = digest(path)
    folder = STUDY/'로그/B2_queue'; folder.mkdir(parents=True, exist_ok=True)
    with (folder/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = folder/'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else dict(
            schema='multi_press.improvement_queue.v3', manifest_sha256=expected,
            completed=False, jobs={}, status='starting')
        if state['manifest_sha256'] != expected or state.get('child_pid'):
            raise ValueError('Queue identity or interrupted child requires audit')
        if state.get('completed'):
            return
        state['pid'] = os.getpid(); child = None
        try:
            for job in manifest['jobs']:
                if job['job_id'] in state['jobs']:
                    record = state['jobs'][job['job_id']]
                    if digest(record['report']) != record['report_sha256']:
                        raise ValueError('Completed improvement report changed')
                    continue
                if Path(job['out']).exists():
                    raise ValueError('Partial output requires audit; automatic retry forbidden')
                state['current_job'] = job['job_id']
                while True:
                    verify_manifest(path)
                    if digest(path) != expected:
                        raise ValueError('Improvement manifest identity changed')
                    ready, reason, resource = readiness()
                    state.update(status=reason, resource=resource, updated_epoch=time.time())
                    if resource.get('baseline_status') == 'error':
                        state['status'] = 'blocked_by_baseline_error'
                        write(state_path, state); return
                    write(state_path, state)
                    if ready:
                        break
                    time.sleep(30)
                command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'),
                    '--cache-root', str(ROOT/'.runtime/cache'), 'run', str(STUDY/'도구/run_improved_job.py'),
                    '--manifest', str(path), '--job', job['job_id']]
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
                           OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
                with (folder/(job['job_id']+'.stdout.log')).open('xb') as stream:
                    child = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                                             stderr=subprocess.STDOUT, start_new_session=True)
                    state.update(status='running', command=command, child_pid=child.pid,
                                 started_epoch=time.time()); write(state_path, state)
                    while child.poll() is None:
                        verify_manifest(path)
                        if digest(path) != expected:
                            raise ValueError('Improvement manifest changed during job')
                        state['updated_epoch'] = time.time(); write(state_path, state)
                        time.sleep(5)
                code = child.wait(); child = None; state.pop('child_pid', None)
                report_path = inside(job['out'])/'job_report.json'
                report = json.loads(report_path.read_text()) if report_path.exists() else {}
                if code != 0 or report.get('completed') is not True or report.get('job_id') != job['job_id']:
                    raise RuntimeError('Improvement job failed; inspect preserved stdout/report')
                state['jobs'][job['job_id']] = dict(completed=True, report=str(report_path),
                                                   report_sha256=digest(report_path))
                write(state_path, state)
            state.update(status='complete', completed=True, updated_epoch=time.time())
            state.pop('current_job', None); write(state_path, state)
        except BaseException as error:
            if child is not None:
                stop_own_group(child)
            state.update(status='error', completed=False, error=repr(error), updated_epoch=time.time())
            write(state_path, state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    run(parser.parse_args().manifest)
