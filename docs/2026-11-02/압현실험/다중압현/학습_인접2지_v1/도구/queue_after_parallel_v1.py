"""Serial study queue. Waits for the existing sweep and an idle verified GPU.

This process never loads Torch or creates a simulator. Every native job gets its
own child process and must recheck the same resource gate before importing Gym.
"""
import argparse
import csv
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

STUDY = Path(__file__).resolve().parents[1]
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
SINGLE = STUDY.parents[1]/'단일압현/전수검증_1-14_v1/로그/sweep_v1/state.json'
GPU_UUID = 'GPU-c1a0b65b-52a2-9067-4bba-0bc383d0f731'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(path):
    path = Path(path).resolve(); path.relative_to(STUDY)
    return path


def atomic(path, value):
    path = inside(path); path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(payload, encoding='utf-8'); temporary.replace(path)


def verify_manifest(path):
    path = inside(path)
    document = json.loads(path.read_text())
    if document.get('schema') != 'multi_press.training_queue.v1':
        raise ValueError('Unexpected queue contract')
    if document.get('gpu_uuid') != GPU_UUID or document.get('single_state') != str(SINGLE):
        raise ValueError('Unexpected resource identity')
    if not document.get('pins'):
        raise ValueError('Nonempty immutable input pins required')
    for filename, expected in document['pins'].items():
        source = Path(filename).resolve(); source.relative_to(ROOT)
        if digest(source) != expected:
            raise ValueError('Pinned source/input changed: '+str(source))
    jobs = document['jobs']
    if not jobs or len({j['job_id'] for j in jobs}) != len(jobs):
        raise ValueError('Nonempty unique jobs required')
    for job in jobs:
        inside(job['out']); inside(job['bundle'])
        if job['mode'] not in ('train', 'evaluate'):
            raise ValueError('Unexpected native job kind')
    return document


def gate(state, gpu_rows, compute_rows, uuid=GPU_UUID):
    """Fail closed: 'no process' cannot replace a completed 336-case ledger."""
    results = state.get('results', {})
    if (state.get('schema') != 'guitar_learning.range336.state.v1' or
            state.get('completed') is not True or state.get('status') != 'complete' or
            state.get('total') != 336 or state.get('finished') != 336 or state.get('remaining') != 0 or
            len(results) != 336 or any(r.get('status') not in ('done', 'inspection_error') for r in results.values())):
        return False, 'waiting_for_single_sweep'
    matches = [r for r in gpu_rows if r['uuid'] == uuid]
    if len(matches) != 1:
        return False, 'waiting_for_verified_gpu'
    if any(r['gpu_uuid'] == uuid for r in compute_rows):
        return False, 'waiting_for_gpu_process_exit'
    free_mib = float(matches[0]['memory.free [MiB]'].split()[0])
    if not math.isfinite(free_mib) or free_mib < 4096:
        return False, 'waiting_for_gpu_memory'
    return True, 'ready'


def gpu_query(fields, kind):
    command = ['nvidia-smi', '--query-'+kind+'='+fields, '--format=csv']
    completed = subprocess.run(command, capture_output=True, text=True, timeout=20)
    if completed.returncode:
        raise RuntimeError('GPU query unavailable: '+completed.stderr.strip()[:300])
    rows = csv.DictReader(io.StringIO(completed.stdout), skipinitialspace=True)
    return [{k.strip(): v.strip() for k, v in r.items()} for r in rows]


def readiness():
    state = json.loads(SINGLE.read_text())
    # Check state->manifest identity without changing either live file.
    source_manifest = SINGLE.with_name('manifest.json')
    if state.get('manifest_sha256') != digest(source_manifest):
        raise ValueError('Existing sweep manifest identity changed')
    gpu = gpu_query('uuid,name,memory.free', 'gpu')
    compute = gpu_query('pid,gpu_uuid,process_name', 'compute-apps')
    ready, reason = gate(state, gpu, compute)
    return ready, reason, dict(single_finished=state.get('finished'), single_remaining=state.get('remaining'),
                               single_status=state.get('status'), gpu=gpu, compute=compute)


def run(manifest_path, poll_s):
    manifest_path = inside(manifest_path)
    manifest = verify_manifest(manifest_path); manifest_sha = digest(manifest_path)
    folder = inside(STUDY/'로그/queue_after_parallel_v1'); folder.mkdir(parents=True, exist_ok=True)
    with (folder/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = folder/'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['manifest_sha256'] != manifest_sha:
                raise ValueError('Queue manifest identity changed')
            if state.get('status') == 'complete':
                return
        else:
            state = dict(schema='multi_press.training_queue_state.v1', manifest_sha256=manifest_sha,
                         pid=os.getpid(), status='waiting', jobs={}, completed=False)
        state['pid'] = os.getpid()
        try:
            for job in manifest['jobs']:
                if state['jobs'].get(job['job_id'], {}).get('completed'):
                    report = inside(job['out'])/'job_report.json'
                    if digest(report) != state['jobs'][job['job_id']]['report_sha256']:
                        raise ValueError('Completed job report changed')
                    continue
                if Path(job['out']).exists():
                    raise ValueError('Unverified partial output exists; manual audit required: '+job['out'])
                state['current_job'] = job['job_id']
                while True:
                    verify_manifest(manifest_path)
                    if digest(manifest_path) != manifest_sha:
                        raise ValueError('Queue manifest changed')
                    try:
                        ready, reason, resource = readiness()
                        state['resource'] = resource; state.pop('resource_error', None)
                    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                        ready, reason = False, 'waiting_for_resource_query'
                        state['resource_error'] = str(exc)
                    state.update(status=reason, updated_epoch=time.time())
                    atomic(state_path, state)
                    if ready:
                        break
                    time.sleep(poll_s)
                command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'),
                           '--cache-root', str(ROOT/'.runtime/cache'), 'run', str(STUDY/'도구/run_job_v2.py'),
                           '--manifest', str(manifest_path), '--job', job['job_id']]
                environment = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
                                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
                state.update(status='running', updated_epoch=time.time(), command=command)
                atomic(state_path, state)
                with (folder/(job['job_id']+'.stdout.log')).open('xb') as stream:
                    child = subprocess.Popen(command, cwd=str(ROOT), env=environment, stdout=stream,
                                             stderr=subprocess.STDOUT)
                    state['child_pid'] = child.pid; atomic(state_path, state)
                    code = child.wait()
                report_path = inside(job['out'])/'job_report.json'
                report = json.loads(report_path.read_text()) if report_path.exists() else {}
                if code != 0 or report.get('completed') is not True:
                    raise RuntimeError('Job failed; no automatic retry: '+job['job_id'])
                verify_manifest(manifest_path)
                state['jobs'][job['job_id']] = dict(completed=True, report=str(report_path),
                                                  report_sha256=digest(report_path))
                state.pop('child_pid', None); atomic(state_path, state)
            state.update(completed=True, status='complete', updated_epoch=time.time())
            state.pop('current_job', None); atomic(state_path, state)
        except BaseException as exc:
            state.update(completed=False, status='error', error=type(exc).__name__+': '+str(exc),
                         updated_epoch=time.time())
            atomic(state_path, state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--poll-s', type=float, default=30.)
    args = parser.parse_args()
    if not 5 <= args.poll_s <= 60:
        parser.error('poll-s must be 5..60')
    run(args.manifest, args.poll_s)
