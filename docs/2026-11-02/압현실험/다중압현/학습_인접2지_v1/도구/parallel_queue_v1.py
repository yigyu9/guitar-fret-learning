"""Guarded serial learning alongside the explicitly authorized existing sweep."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import time

from study_queue_v2 import STUDY, ROOT, GPU_UUID, atomic, inside, digest, verify_manifest, gpu_query
from parallel_resources_v1 import readiness, SINGLE_STATE


def full_native_times(state, excluded=()):
    return [float(r['elapsed_s']) for name, r in state['results'].items() if name not in excluded and
            r.get('status') == 'done' and r.get('outcome') in ('press_success', 'native_press_failed')
            and r.get('elapsed_s') is not None and math.isfinite(r['elapsed_s']) and r['elapsed_s'] > 0]


def impact(baseline, current):
    before = full_native_times(baseline)[-16:]
    after = full_native_times(current, baseline['results'])
    errors = [name for name, row in current['results'].items() if name not in baseline['results']
              and row.get('status') == 'inspection_error']
    ratio = max(after)/statistics.median(before) if after and len(before) >= 3 else None
    severe = bool(errors or current['status'] not in ('running', 'complete') or
                  (ratio is not None and ratio >= 1.50))
    return dict(baseline_median_s=statistics.median(before) if before else None,
        compared_completed_jobs=len(after), new_full_native_elapsed_s=after,
        maximum_elapsed_ratio=ratio, inspection_errors=errors, severe=severe,
        expansion_allowed=not severe and ratio is not None and ratio < 1.25,
        limitation='Different goals, CPU search cost and partial temporal overlap confound causality')


def assess_pilot(record, initial_baseline, current):
    stage = impact(record['baseline_single'], current)
    overall = impact(initial_baseline, current)
    approved = bool(stage['expansion_allowed'] and overall['expansion_allowed'])
    return stage, overall, approved


def stop_own_group(child):
    if child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=10)


def run(path, max_jobs=None):
    path = inside(path); manifest = verify_manifest(path); expected = digest(path)
    if manifest.get('parallel_policy', {}).get('user_authorized') is not True:
        raise ValueError('Explicit parallel authorization required')
    folder = STUDY/'로그/parallel_queue_v1'; folder.mkdir(parents=True, exist_ok=True)
    with (folder/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = folder/'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['manifest_sha256'] != expected:
                raise ValueError('Parallel manifest changed')
            if state.get('completed'):
                return
        else:
            state = dict(schema='multi_press.parallel_queue.v1', manifest_sha256=expected,
                pid=os.getpid(), completed=False, status='starting', jobs={},
                baseline_single=json.loads(SINGLE_STATE.read_text()))
        state['pid'] = os.getpid(); completed_now = 0; child = None
        try:
            for job in manifest['jobs']:
                if job['job_id'] in state['jobs']:
                    old = state['jobs'][job['job_id']]
                    if digest(old['report']) != old['report_sha256']:
                        raise ValueError('Completed parallel report changed')
                    if job.get('pilot') and not old.get('expansion_approved'):
                        stage, overall, approved = assess_pilot(old, state['baseline_single'],
                                                               json.loads(SINGLE_STATE.read_text()))
                        old.update(impact=stage, overall_impact=overall, expansion_approved=approved)
                        if not approved:
                            state['status'] = 'held_for_single_sweep_impact'
                            atomic(state_path, state); return
                    continue
                if Path(job['out']).exists():
                    raise ValueError('Partial output needs audit; automatic retries forbidden')
                if max_jobs is not None and completed_now >= max_jobs:
                    state['status'] = 'pilot_checkpoint'; atomic(state_path, state); return
                state['current_job'] = job['job_id']
                while True:
                    verify_manifest(path)
                    if digest(path) != expected:
                        raise ValueError('Parallel manifest changed')
                    ready, reason, resource = readiness()
                    state.update(status=reason, resource=resource, updated_epoch=time.time())
                    atomic(state_path, state)
                    if ready:
                        break
                    time.sleep(5)
                command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'),
                    '--cache-root', str(ROOT/'.runtime/cache'), 'run', str(STUDY/'도구/run_job_parallel_v1.py'),
                    '--manifest', str(path), '--job', job['job_id']]
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
                           OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
                state.update(status='running', command=command, started_epoch=time.time())
                job_baseline = json.loads(SINGLE_STATE.read_text())
                state['active_baseline_single'] = job_baseline
                with (folder/(job['job_id']+'.stdout.log')).open('xb') as stream:
                    child = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                                             stderr=subprocess.STDOUT, start_new_session=True)
                    state['child_pid'] = child.pid; atomic(state_path, state)
                    query_errors = 0
                    with (folder/(job['job_id']+'.resources.jsonl')).open('x') as resources:
                        while child.poll() is None:
                            verify_manifest(path)
                            single = json.loads(SINGLE_STATE.read_text())
                            measured = impact(job_baseline, single)
                            overall = impact(state['baseline_single'], single)
                            state['impact'] = measured
                            state['overall_impact'] = overall
                            if measured['severe'] or overall['severe']:
                                raise RuntimeError('Single sweep delay/error guard: '+repr(measured))
                            try:
                                gpu = gpu_query('uuid,memory.free,utilization.gpu', 'gpu')
                                row = next(r for r in gpu if r['uuid'] == GPU_UUID)
                                free = float(row['memory.free [MiB]'].split()[0])
                                if not math.isfinite(free) or free < 2048:
                                    raise MemoryError('Parallel free GPU memory below2GiB')
                                query_errors = 0
                                state['gpu_during_job'] = row
                                resources.write(json.dumps(dict(epoch=time.time(), gpu=row,
                                    single_finished=single['finished'], impact=measured))+'\n'); resources.flush()
                            except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
                                query_errors += 1
                                if query_errors >= 3:
                                    raise RuntimeError('Repeated GPU monitor query failure: '+str(exc))
                            state['updated_epoch'] = time.time(); atomic(state_path, state)
                            time.sleep(3)
                code = child.wait(); child = None; state.pop('child_pid', None)
                report_path = inside(job['out'])/'job_report.json'
                report = json.loads(report_path.read_text()) if report_path.exists() else {}
                if code != 0 or report.get('completed') is not True:
                    raise RuntimeError('Native parallel job error; see stdout: '+job['job_id'])
                verify_manifest(path)
                measured = impact(job_baseline, json.loads(SINGLE_STATE.read_text()))
                state['jobs'][job['job_id']] = dict(completed=True, report=str(report_path),
                    report_sha256=digest(report_path), impact=measured, baseline_single=job_baseline,
                    expansion_approved=False if job.get('pilot') else None)
                completed_now += 1; atomic(state_path, state)
                if job.get('pilot'):
                    # Wait for an observable completed baseline-comparable sweep job.
                    deadline = time.monotonic()+150
                    record = state['jobs'][job['job_id']]
                    while measured['maximum_elapsed_ratio'] is None and time.monotonic() < deadline:
                        state.update(status='observing_single_sweep', impact=measured)
                        atomic(state_path, state); time.sleep(5)
                        measured = impact(job_baseline, json.loads(SINGLE_STATE.read_text()))
                    state['impact'] = measured
                    stage, overall, approved = assess_pilot(record, state['baseline_single'],
                                                           json.loads(SINGLE_STATE.read_text()))
                    record.update(impact=stage, overall_impact=overall, expansion_approved=approved)
                    if not approved:
                        state['status'] = 'held_for_single_sweep_impact'; atomic(state_path, state); return
            state.update(completed=True, status='complete', updated_epoch=time.time())
            state.pop('current_job', None); atomic(state_path, state)
        except BaseException as exc:
            if child is not None:
                stop_own_group(child)
            state.update(status='error', completed=False, error=type(exc).__name__+': '+str(exc),
                         updated_epoch=time.time())
            atomic(state_path, state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--max-jobs', type=int)
    args = parser.parse_args()
    if args.max_jobs is not None and args.max_jobs < 1:
        parser.error('max-jobs must be positive')
    run(args.manifest, args.max_jobs)
