"""Durably supervise the authorized fresh v20 A/large1024/H32/500 run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def write(name, value):
    path = PHASE/name
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    os.replace(temporary, path)


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--detach', action='store_true')
    args = parser.parse_args()
    env = dict(os.environ)
    env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    if args.detach:
        with (PHASE/'supervisor.log').open('x') as log:
            process = subprocess.Popen([PYTHON, '-B', str(Path(__file__).resolve())],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
        record = dict(supervisor_pid=process.pid, started_utc=now())
        write('detached_launch.json', record)
        print(json.dumps(record), flush=True)
        return
    # A duplicate supervisor must not overwrite an existing run's status.
    with (PHASE/'supervisor_claim.json').open('x') as claim:
        json.dump(dict(supervisor_pid=os.getpid(), claimed_utc=now()), claim)
        claim.write('\n')
    state = dict(phase='preflight', supervisor_pid=os.getpid(), started_utc=now(),
        requested_updates=500, requested_transitions=16_384_000, completed=False)
    write('pipeline_status.json', state)
    started = time.monotonic()
    try:
        manifest = json.loads((PHASE/'training_source_manifest.json').read_text())
        for name, expected in manifest['source'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
        previous = ROOT/'docs/2026-10-25/guitar_learning_finger_recovery_v20'
        assert json.loads((previous/'gpu_verification.json').read_text())['verified']
        assert json.loads((previous/'verification.json').read_text())['verified']
        assert not (PHASE/'train500').exists(), 'Preserve existing training run'
        command = [PYTHON, '-B', '-m', 'guitar_learning.train', '--hand', 'left',
            '--song', '05_BN2-131-B_solo', '--physics', 'gpu', '--device', 'cuda:0',
            '--size', 'large', '--num-envs', '1024', '--horizon', '32',
            '--updates', '500', '--checkpoint-every', '250', '--seed', '7',
            '--out', str(PHASE/'train500')]
        with (PHASE/'train500_console.log').open('x') as log:
            process = subprocess.Popen(command, cwd=ROOT, env=env,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            state.update(phase='training', training_pid=process.pid, command=command)
            write('pipeline_status.json', state)
            code = process.wait()
        if code:
            raise RuntimeError('Training exited with code '+str(code))
        report = json.loads((PHASE/'train500/report.json').read_text())
        assert report['completed'] and report['optimizer_updates'] == 500
        assert report['failure'] is None and report['lifecycle_verified']
        assert not report['changed_inputs'] and not report['missing_import_pins']
        assert not report['cleanup_errors']
        state.update(phase='auditing', training_completed=True)
        write('pipeline_status.json', state)
        with (PHASE/'log_inspection.json').open('x') as result:
            subprocess.run([PYTHON, '-B', '-m',
                'guitar_learning.tool.inspect_gpu_training_log', '--run', str(PHASE/'train500')],
                cwd=ROOT, env=env, stdout=result, stderr=subprocess.STDOUT, check=True)
        audit = json.loads((PHASE/'log_inspection.json').read_text())
        assert audit['verified'] and audit['transitions'] == 16_384_000
        state.update(phase='training_audited', completed=True, inspection_verified=True,
            ended_utc=now(), wall_s=time.monotonic()-started)
        write('pipeline_status.json', state)
    except BaseException as error:
        state.update(phase='failed', completed=False, error=repr(error), ended_utc=now(),
            wall_s=time.monotonic()-started)
        write('pipeline_status.json', state)
        raise


if __name__ == '__main__':
    main()
