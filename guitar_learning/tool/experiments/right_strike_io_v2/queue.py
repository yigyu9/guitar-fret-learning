"""Wait for an idle GPU, then guard one own native diagnostic child."""
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

from guitar_learning.tool.experiments.right_strike.runtime import ROOT, GPU_UUID, sha, readiness, gpu_rows
from . import verify_manifest


def atomic(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=10)


def queue_probe(manifest, out, queue_out):
    manifest, out, queue_out = map(lambda p: Path(p).resolve(), (manifest, out, queue_out))
    out.relative_to(ROOT/'runs'); queue_out.relative_to(ROOT/'runs')
    verify_manifest(manifest); expected = sha(manifest)
    if out.exists() or queue_out.exists():
        raise FileExistsError('Fresh queue and probe outputs required; no implicit retry')
    queue_out.mkdir(parents=True)
    state = dict(schema='guitar_learning.right_strike_queue.v1', completed=False,
                 manifest=str(manifest), manifest_sha256=expected, pid=os.getpid(), out=str(out))
    child = None
    with (queue_out/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            while True:
                verify_manifest(manifest, expected)
                ready, reason, resource = readiness()
                state.update(status=reason, resource=resource, updated_epoch=time.time())
                atomic(queue_out/'state.json', state)
                if ready:
                    break
                time.sleep(30)
            command = ['/home/ajou/miniconda3/envs/rl38/bin/python3.8', '-B',
                str(ROOT/'scripts/tab2body.py'), '--cache-root', str(ROOT/'.runtime/cache'),
                'run', '-m', 'guitar_learning.tool.experiments.right_strike_io_v2', 'probe',
                '--manifest', str(manifest), '--out', str(out)]
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
                       OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
            started = time.monotonic()
            with (queue_out/'native.stdout.log').open('xb') as stream:
                child = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                state.update(status='running', child_pid=child.pid, command=command)
                atomic(queue_out/'state.json', state)
                while child.poll() is None:
                    verify_manifest(manifest, expected)
                    if time.monotonic()-started > 240:
                        raise TimeoutError('One native diagnostic exceeded240s')
                    devices = [r for r in gpu_rows('uuid,memory.free', 'gpu') if r['uuid'] == GPU_UUID]
                    if len(devices) != 1:
                        raise RuntimeError('Verified GPU disappeared')
                    free = float(devices[0]['memory.free [MiB]'].split()[0])
                    if not math.isfinite(free) or free < 2048:
                        raise MemoryError('Native diagnostic free memory below2GiB')
                    for row in gpu_rows('pid,gpu_uuid,process_name', 'compute-apps'):
                        if row['gpu_uuid'] != GPU_UUID:
                            continue
                        try:
                            group = os.getpgid(int(row['pid']))
                        except ProcessLookupError:
                            continue
                        if group != child.pid:
                            raise RuntimeError('Another GPU process appeared; stopping own diagnostic only')
                    state['updated_epoch'] = time.time()
                    atomic(queue_out/'state.json', state)
                    time.sleep(3)
            code = child.wait(); state.pop('child_pid', None)
            if code != 0:
                raise RuntimeError('Diagnostic child failed; see preserved stdout')
            verify_manifest(manifest, expected)
            report = out/'report.json'
            result = json.loads(report.read_text())
            if result.get('completed') is not True:
                raise RuntimeError('Native diagnostic lifecycle incomplete')
            state.update(status='complete', completed=True, report=str(report), report_sha256=sha(report),
                         outcome=result['outcome'], wall_s=time.monotonic()-started)
            atomic(queue_out/'state.json', state)
        except BaseException as error:
            if child is not None:
                stop(child)
            state.update(status='error', completed=False, error=repr(error), updated_epoch=time.time())
            atomic(queue_out/'state.json', state)
            raise
    return state
