"""Storage-safe watcher; verify the launched native process before one SIGINT."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io


def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def process_info(pid, proc=Path('/proc')):
    """Linux starttime is retained to reject PID reuse; no executable is run."""
    if type(pid) is not int or pid <= 0:
        return None
    try:
        fields = (proc/str(pid)/'stat').read_text().rsplit(')', 1)[1].split()
        command = (proc/str(pid)/'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    except (FileNotFoundError, ProcessLookupError):
        return None
    if fields[0] in ('Z', 'X'):
        return None
    return dict(pid=pid, ppid=int(fields[1]), starttime=int(fields[19]),
                command=[os.fsdecode(x) for x in command])


def native_command(command, run):
    return (bool(command) and Path(command[0]).name.startswith('python') and
            command.count('-m') == 1 and command.count('--out') == 1 and
            command[command.index('-m')+1:command.index('-m')+2] == ['guitar_learning.train'] and
            command[command.index('--out')+1:command.index('--out')+2] == [str(run)])


def owned_native(launch, run, cached=None, status=None, proc=Path('/proc')):
    expected = launch['command'][launch['command'].index('--args')+1:]
    if cached is not None:
        current = process_info(cached['pid'], proc)
        return current if (current and current['starttime'] == cached['starttime'] and
                           current['command'] == expected and native_command(current['command'], run)) else None
    # First discovery must come from this exact GDB launch, including its start time.
    debugger = process_info(launch['child_pid'], proc)
    if debugger is None or debugger['command'] != launch['command']:
        return None
    boot = next(int(row.split()[1]) for row in (proc/'stat').read_text().splitlines() if row.startswith('btime '))
    launched = datetime.datetime.fromisoformat(launch['started_utc']).timestamp()
    debugger_time = boot+debugger['starttime']/os.sysconf('SC_CLK_TCK')
    if not launched-1 <= debugger_time <= launched+60:
        return None
    try:
        children = [int(x) for x in (proc/str(debugger['pid'])/'task'/str(debugger['pid'])/'children').read_text().split()]
    except (FileNotFoundError, ProcessLookupError):
        children = []
    if status and type(status.get('parent_pid')) is int:
        children.insert(0, status['parent_pid'])
    for pid in dict.fromkeys(children):
        child = process_info(pid, proc)
        if (child and child['ppid'] == debugger['pid'] and child['starttime'] >= debugger['starttime'] and
                child['command'] == expected and native_command(child['command'], run)):
            return child
    return None


def interrupt_once(launch, run, state, row):
    if state['signal_attempted']:
        return
    native = owned_native(launch, run, state['native'])  # Recheck command AND starttime immediately before signal.
    if native is None:
        row['guard_action'] = 'No signal: launched native identity not verified'
        return
    state['signal_attempted'] = True
    try:
        os.kill(native['pid'], signal.SIGINT)
        row['guard_action'] = 'SIGINT verified native Python once; preserve all output'
    except OSError as error:
        row['guard_action'] = 'SIGINT attempt failed: '+str(error)


def append(path, row):
    with path.open('a') as stream:
        stream.write(json_io.dumps(row, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def cycle(launch, source, state, phase=PHASE):
    run = Path(launch['out'])
    now = time.monotonic()
    row = dict(run=str(run), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               unix_time=time.time(), elapsed_s=now-state['started'], warnings=[])
    problem, status, report, result = state.get('startup_problem'), None, None, None
    try:
        status = read(run/'status.json')
    except OSError as error:
        problem = 'status storage error: '+str(error)
    if status:
        row.update(status=status, phase=status.get('phase'), status_pid=status.get('parent_pid'))
    identity_read_ok = True
    try:
        native = owned_native(launch, run, state['native'], status)
        if native:
            state['native'] = native
        row['native_pid'] = native['pid'] if native else None
        row['native_starttime'] = native['starttime'] if native else None
    except OSError as error:
        native, identity_read_ok = None, False
        problem = 'process identity read error: '+str(error)
    try:
        disk = os.statvfs(run)
        row['disk_free_bytes'] = disk.f_bavail*disk.f_frsize
        if row['disk_free_bytes'] < 5*1024**3:
            problem = 'output storage below5GiB'
        with os.scandir(run) as entries:
            paths = sorted(run/e.name for e in entries if e.name.startswith('update_') and e.name.endswith('.json'))
        metric = read(paths[-1]) if paths else None
        if metric:
            update = metric['update_index']
            row.update(last_committed_update=update, optimizer_updates=metric['optimizer_updates'],
                reward_mean=metric['mean_reward'], cost_mean=metric['mean_cost'], curriculum=metric.get('left_curriculum'))
            if update != state['last_update']:
                state['last_update'], state['last_progress'] = update, now
        if state['count'] % 12 == 0:
            changed = [p for p, digest in source.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
            row['changed_source'] = changed
            if changed:
                problem = 'frozen training source changed'
        report = read(run/'report.json')
        result = read(phase/'launch_result.json')
        if result and any(result.get(k) != launch.get(k) for k in ('out', 'child_pid', 'started_utc')):
            row['warnings'].append('Ignoring launcher result from a different launch')
            result = None
    except OSError as error:
        problem = 'storage error: '+str(error)
    try:
        local = os.statvfs(ROOT)
        row['local_disk_free_bytes'] = local.f_bavail*local.f_frsize
    except OSError as error:
        row['warnings'].append('Local free-space query failed: '+str(error))
    try:
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.free', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=10)
        if gpu.returncode:
            row['warnings'].append('NVIDIA query failed: '+gpu.stderr.strip())
        else:
            row['gpu_memory_mib'] = gpu.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        row['warnings'].append('NVIDIA query unavailable: '+str(error))
    closed = bool(report and report.get('gpu_scene', {}).get('closed') is True)
    row['training_report_completed'] = report.get('completed') if report else None
    row['native_closed_report'] = closed
    row['launch_result'] = result
    stalled = now-state['last_progress'] > 600
    if stalled and not (native is None and (closed or result is not None)):
        problem = problem or 'no committed update for600s'
    row['guard_problem'] = problem
    if problem:
        try:
            interrupt_once(launch, run, state, row)
        except OSError as error:
            row['guard_action'] = 'No signal: identity recheck failed: '+str(error)
    row['finished'] = bool(identity_read_ok and native is None and (closed or result is not None or stalled))
    row['finish_reason'] = ('closed_report_native_gone' if closed else
        'launcher_ended_native_gone' if result is not None else 'native_gone_without_report_after600s') if row['finished'] else None
    external = run.parent/'monitor_v2_progress.jsonl'
    try:
        append(external, row)
    except OSError as error:
        row['guard_problem'] = 'external progress storage error: '+str(error)
        try:
            interrupt_once(launch, run, state, row)
        except OSError as identity_error:
            row['guard_action'] = 'No signal: identity recheck failed: '+str(identity_error)
        print(json_io.dumps(row, allow_nan=False), file=sys.stderr, flush=True)
    try:
        append(phase/'progress.jsonl', row)  # Preserve the original monitor's lines.
    except OSError as error:
        warning = dict(run=str(run), utc=row['utc'], event='local_progress_write_failed', warning=str(error))
        try:
            append(external, warning)
        except OSError as external_error:
            row['guard_problem'] = 'external warning storage error: '+str(external_error)
            try:
                interrupt_once(launch, run, state, row)
            except OSError as identity_error:
                row['guard_action'] = 'No signal: identity recheck failed: '+str(identity_error)
            print(json_io.dumps(row, allow_nan=False), file=sys.stderr, flush=True)
    state['count'] += 1
    return row


def main():
    launch = read(PHASE/'launch.json')
    startup_problem = None
    try:
        manifest = read(PHASE/'training_source_manifest.json')
        source = manifest['source'] if manifest else {}
        if not source:
            startup_problem = 'source manifest missing or unreadable JSON'
    except OSError as error:
        source, startup_problem = {}, 'source manifest storage error: '+str(error)
    started = time.monotonic()
    state = dict(started=started, last_update=-1, last_progress=started, count=0,
                 native=None, signal_attempted=False, startup_problem=startup_problem)
    while True:
        row = cycle(launch, source, state)
        if row['finished']:
            break
        time.sleep(50)
    result = dict(completed=row['finish_reason'] != 'native_gone_without_report_after600s',
        run=launch['out'], guard_signal_attempted=state['signal_attempted'],
        last_committed_update=state['last_update'], elapsed_s=time.monotonic()-started,
        finish_reason=row['finish_reason'], training_report_completed=row['training_report_completed'])
    for path in (Path(launch['out']).parent/'monitor_v2_result.json', PHASE/'monitor_v2_result.json'):
        try:
            with path.open('x') as stream:
                json_io.dump(result, stream, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        except OSError as error:
            print('Monitor result could not be written: '+str(error), file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()
