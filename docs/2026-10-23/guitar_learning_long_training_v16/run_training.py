"""Durable launcher for the authorized v16 smoke/resume/fresh-long runs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/ajou/yigyu/3')
PHASE = Path(__file__).resolve().parent
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('smoke', 'resume', 'train'), required=True)
    parser.add_argument('--detach', action='store_true')
    args = parser.parse_args()
    name, updates, save = dict(smoke=('smoke_1024', 12, 6),
                               resume=('resume_1024', 1, 1),
                               train=('train2000', 2000, 100))[args.stage]
    out = PHASE/name
    assert not out.exists(), 'Preserve existing run; never overwrite it'
    if args.detach:
        with (PHASE/(name+'_supervisor.log')).open('x') as log:
            child = subprocess.Popen([PYTHON, '-B', str(Path(__file__).resolve()), '--stage', args.stage],
                cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
        record = dict(stage=args.stage, launcher_pid=child.pid,
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (PHASE/(name+'_detached.json')).write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps(record))
        return
    pins = json.loads((PHASE/'training_source_manifest.json').read_text())['source']
    for path, digest in pins.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
    command = ['gdb', '-q', '-batch', '-x',
        str(ROOT/'docs/2026-10-22/guitar_learning_long_training_v6/native_trace.gdb'),
        '--args', PYTHON, '-B', '-m', 'guitar_learning.train',
        '--hand', 'left', '--song', '05_BN2-131-B_solo',
        '--device', 'cuda:0', '--physics', 'gpu', '--size', 'large',
        '--num-envs', '1024', '--horizon', '32', '--updates', str(updates),
        '--checkpoint-every', str(save), '--seed', '7', '--out', str(out)]
    if args.stage == 'resume':
        checkpoint = PHASE/'smoke_1024/final.pt'
        assert checkpoint.is_file()
        command += ['--resume', str(checkpoint)]
    if args.stage == 'train':
        for stage in ('smoke_1024', 'resume_1024'):
            report = json.loads((PHASE/stage/'report.json').read_text())
            assert report['completed'] and not report['failure']
            assert not report['changed_inputs'] and not report['missing_import_pins']
            assert report['lifecycle_verified']
    env = dict(os.environ)
    env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', OMP_NUM_THREADS='1')
    begin = time.monotonic()
    metadata = dict(stage=args.stage, command=command, out=str(out), launcher_pid=os.getpid(),
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        log=str(PHASE/(name+'_console.log')), fresh=args.stage != 'resume')
    with Path(metadata['log']).open('x') as log:
        process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT)
        metadata['child_pid'] = process.pid
        (PHASE/(name+'_launch.json')).write_text(json.dumps(metadata, indent=2)+'\n')
        result = process.wait()
        log.flush(); os.fsync(log.fileno())
    metadata.update(returncode=result, wall_s=time.monotonic()-begin,
        ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (PHASE/(name+'_launch_result.json')).write_text(json.dumps(metadata, indent=2)+'\n')
    raise SystemExit(result)


if __name__ == '__main__':
    main()
