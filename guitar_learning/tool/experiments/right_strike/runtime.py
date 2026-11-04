"""Source identity, exclusive GPU admission and the official environment hook."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
GPU_UUID = 'GPU-c1a0b65b-52a2-9067-4bba-0bc383d0f731'
SCHEMA = 'guitar_learning.right_strike_execution.v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def verify_pins(pins):
    if not pins:
        raise ValueError('Nonempty source/input pins required')
    for name, expected in pins.items():
        path = Path(name).resolve()
        path.relative_to(ROOT)
        if sha(path) != expected:
            raise ValueError('Right strike input changed: '+name)


def verify_manifest(path, expected=None):
    path = Path(path).resolve()
    path.relative_to(ROOT/'data/diagnostic_inputs')
    if expected is not None and sha(path) != expected:
        raise ValueError('Right strike manifest changed')
    data = read(path)
    if (data.get('schema') != SCHEMA or data.get('sealed') is not True or
            data.get('gpu_uuid') != GPU_UUID or data.get('condition') != 'single_down_string3_v1'):
        raise ValueError('Sealed single-string right strike identity required')
    bundle = Path(data['bundle']).resolve()
    bundle.relative_to(ROOT/'data/diagnostic_inputs')
    required = [Path(__file__), ROOT/'guitar_learning/gpu/right_strike_environment.py']
    required += list(Path(__file__).parent.glob('*.py'))
    required += [p for p in bundle.rglob('*') if p.is_file() and p != path]
    if any(str(p.resolve()) not in data.get('pins', {}) for p in required):
        raise ValueError('Every execution source and target input must be pinned')
    verify_pins(data['pins'])
    return data


def gpu_rows(fields, kind):
    import csv
    import io
    result = subprocess.run(['nvidia-smi', '--query-'+kind+'='+fields, '--format=csv'],
                            text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError('GPU inventory unavailable: '+result.stderr[:200])
    return [{k.strip(): v.strip() for k, v in row.items()}
            for row in csv.DictReader(io.StringIO(result.stdout), skipinitialspace=True)]


def readiness():
    import math
    devices = [r for r in gpu_rows('uuid,name,memory.free', 'gpu') if r['uuid'] == GPU_UUID]
    jobs = [r for r in gpu_rows('pid,gpu_uuid,process_name', 'compute-apps') if r['gpu_uuid'] == GPU_UUID]
    if len(devices) != 1:
        return False, 'waiting_for_verified_gpu', dict(gpu=devices, processes=jobs)
    free = float(devices[0]['memory.free [MiB]'].split()[0])
    resource = dict(gpu=devices[0], processes=jobs)
    if jobs:
        return False, 'waiting_for_gpu_idle', resource
    if not math.isfinite(free) or free < 4096:
        return False, 'waiting_for_gpu_memory', resource
    return True, 'ready', resource


@contextmanager
def environment_runtime():
    # Caller must import Gym before this hook imports the Torch-based pool.
    from guitar_learning.training import rollout
    from guitar_learning.gpu.right_strike_environment import RightStrikeEnvironment
    original = rollout.GpuPool
    class RightPool(original):
        environment_class_override = RightStrikeEnvironment
    rollout.GpuPool = RightPool
    try:
        yield RightPool
    finally:
        rollout.GpuPool = original


@contextmanager
def admitted(manifest_path):
    """Same-host lock and a fresh idle inventory before any simulator import."""
    import fcntl
    import os
    manifest = verify_manifest(manifest_path)
    expected = sha(manifest_path)
    with (ROOT/'.runtime/right_strike_gpu.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ready, reason, resource = readiness()
        if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
            raise RuntimeError('Right strike refused before Gym import: '+reason)
        try:
            yield manifest, resource
        finally:
            verify_manifest(manifest_path, expected)
