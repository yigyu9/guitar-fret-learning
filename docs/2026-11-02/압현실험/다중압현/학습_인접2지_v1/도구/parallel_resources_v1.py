"""Read-only resource gate for the explicitly authorized same-GPU pilot.

No Torch/Gym imports and no process mutation. A successful sample is evidence of
current capacity, not a reservation; the pilot runner must monitor its own job.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess

STUDY = Path(__file__).resolve().parents[1]
SINGLE_ROOT = STUDY.parents[1] / '단일압현/전수검증_1-14_v1'
SINGLE_STATE = SINGLE_ROOT / '로그/sweep_v1/state.json'
SINGLE_MANIFEST = SINGLE_STATE.with_name('manifest.json')
SINGLE_GEOMETRY = SINGLE_STATE.with_name('geometry_frozen.json')
SINGLE_SCRIPT = SINGLE_ROOT / '도구/native_check.py'
SINGLE_MANIFEST_SHA256 = 'c71224054042eef2c3ea1a53f005a3caa53e6155135797865deb9209746e2a3f'
GPU_UUID = 'GPU-c1a0b65b-52a2-9067-4bba-0bc383d0f731'
MIN_FREE_MIB = 4096


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gpu_query(fields, kind):
    result = subprocess.run(['nvidia-smi', '--query-' + kind + '=' + fields,
                             '--format=csv'], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError('GPU query unavailable: ' + result.stderr.strip()[:300])
    reader = csv.DictReader(io.StringIO(result.stdout), skipinitialspace=True)
    return [{key.strip(): value.strip() for key, value in row.items()} for row in reader]


def memory_mib(value):
    """Accept NVML CSV numeric MiB and explicit MiB, never guess other units."""
    match = re.fullmatch(r'\s*([^\s]+)(?:\s+MiB)?\s*', str(value))
    if match is None:
        raise ValueError('Invalid GPU memory units')
    number = float(match.group(1))
    if not math.isfinite(number) or number < 0:
        raise ValueError('Invalid GPU memory value')
    return number


def read_process_identity(pid):
    """Guard cmdline reads with Linux start ticks to detect PID reuse/exit."""
    folder = Path('/proc') / str(pid)

    def started():
        # comm may contain spaces or parentheses, so split after its final ')'.
        return (folder / 'stat').read_text().rsplit(')', 1)[1].split()[19]

    before = started()
    raw = (folder / 'cmdline').read_bytes()
    after = started()
    if before != after or not raw or not raw.endswith(b'\0'):
        raise ValueError('Process changed during identity read')
    return {'pid': pid, 'start_ticks': before,
            'argv': [part.decode('utf-8') for part in raw[:-1].split(b'\0')]}


def _option(argv, name):
    if argv.count(name) != 1:
        return None
    at = argv.index(name)
    return argv[at + 1] if at + 1 < len(argv) else None


def _allowed_process(identity, state):
    argv = identity['argv']
    if not argv or not re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(argv[0]).name):
        return False
    index = 1
    while index < len(argv):
        if argv[index] in ('-B', '-u'):
            index += 1
        elif argv[index] in ('-X', '-W'):
            index += 2
        else:
            break
    if index >= len(argv) or argv[index] != str(SINGLE_SCRIPT):
        return False
    current = state.get('current', {})
    if state.get('status') != 'running' or not current.get('out'):
        return False
    arguments = argv[index + 1:]
    return (_option(arguments, '--geometry') == str(SINGLE_GEOMETRY)
            and _option(arguments, '--out') == current['out']
            and _option(arguments, '--case') == current.get('case'))


def _state():
    state = json.loads(SINGLE_STATE.read_text())
    sha = digest(SINGLE_MANIFEST)
    if sha != SINGLE_MANIFEST_SHA256 or state.get('manifest_sha256') != sha:
        raise ValueError('Existing sweep manifest identity changed')
    manifest = json.loads(SINGLE_MANIFEST.read_text())
    if not manifest.get('pins'):
        raise ValueError('Existing sweep pins missing')
    for filename, expected in manifest['pins'].items():
        if digest(filename) != expected:
            raise ValueError('Existing sweep pinned input changed: ' + filename)
    if (state.get('schema') != 'guitar_learning.range336.state.v1'
            or state.get('total') != 336
            or state.get('status') not in ('running', 'complete')
            or type(state.get('finished')) is not int
            or not 0 <= state['finished'] <= 336
            or state.get('remaining') != 336 - state['finished']):
        raise ValueError('Unexpected existing sweep state')
    return state


def _compute(rows):
    """Only target GPU processes compete for this pilot's resources."""
    if any(not isinstance(row.get('gpu_uuid'), str) or not row['gpu_uuid'] for row in rows):
        raise ValueError('GPU process identity missing')
    selected = [row for row in rows if row.get('gpu_uuid') == GPU_UUID]
    for row in selected:
        if not str(row.get('pid', '')).isdigit() or int(row['pid']) <= 0:
            raise ValueError('Invalid GPU process PID')
    return sorted(selected, key=lambda row: int(row['pid']))


def readiness():
    """Return (ready, reason, JSON-safe evidence) without changing live files."""
    resource = {'gpu_uuid': GPU_UUID, 'minimum_free_mib': MIN_FREE_MIB}
    try:
        state = _state()
        resource.update(single_finished=state['finished'], single_remaining=state['remaining'],
                        single_status=state['status'], single_current=state.get('current'),
                        single_manifest_sha256=SINGLE_MANIFEST_SHA256)
        gpu = gpu_query('uuid,name,memory.free', 'gpu')
        resource['gpu'] = gpu
        matches = [row for row in gpu if row.get('uuid') == GPU_UUID]
        if len(matches) != 1:
            return False, 'waiting_for_verified_gpu', resource
        free = memory_mib(matches[0]['memory.free [MiB]'])
        resource['free_mib'] = free
        if free < MIN_FREE_MIB:
            return False, 'waiting_for_gpu_memory', resource
        compute = _compute(gpu_query('pid,gpu_uuid,process_name', 'compute-apps'))
        resource['compute'] = compute
        if len(compute) > 1:
            return False, 'waiting_for_other_gpu_processes', resource
        identity = None
        if compute:
            identity = read_process_identity(int(compute[0]['pid']))
            resource['allowed_single_process'] = identity
            if not _allowed_process(identity, state):
                return False, 'waiting_for_unknown_gpu_process', resource
        # A second sample rejects observed process turnover, PID reuse, or a new case.
        compute_again = _compute(gpu_query('pid,gpu_uuid,process_name', 'compute-apps'))
        resource['compute_recheck'] = compute_again
        if compute != compute_again:
            return False, 'waiting_for_process_race', resource
        if identity is not None and read_process_identity(identity['pid']) != identity:
            return False, 'waiting_for_process_race', resource
        state_again = _state()
        if (state_again.get('current') != state.get('current')
                or state_again['status'] != state['status']):
            return False, 'waiting_for_single_state_race', resource
        return True, 'ready_parallel' if compute else 'ready_idle', resource
    except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError,
            subprocess.TimeoutExpired) as error:
        resource['error'] = type(error).__name__ + ': ' + str(error)
        return False, 'waiting_for_resource_verification', resource
