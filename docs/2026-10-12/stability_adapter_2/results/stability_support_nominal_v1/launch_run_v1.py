"""Supervise the support-nominal native learner and retain exact exit status."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
source = p.add_mutually_exclusive_group(required=True)
source.add_argument('--initialize-rms', type=Path)
source.add_argument('--checkpoint', type=Path)
p.add_argument('--max-updates', type=int)
args = p.parse_args()
command = [sys.executable, '-u', '-m', 'stability_adapter_2.run_deadline_training_v7',
    '--out', str(args.out), '--strap', 'on', '--device', 'cuda',
    '--interval-minutes', '30', '--stop-at', '2026-10-12T11:40:00+09:00']
if args.initialize_rms: command += ['--initialize-rms', str(args.initialize_rms)]
if args.checkpoint: command += ['--checkpoint', str(args.checkpoint)]
if args.max_updates: command += ['--max-updates', str(args.max_updates)]
record = {'command': command, 'started_utc': datetime.now(timezone.utc).isoformat(),
    'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'supervisor_pid': os.getpid(), 'output': str(args.out)}
with args.out.with_suffix('.log').open('x') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    record['pid'] = process.pid
    with args.out.with_suffix('.pid').open('x') as stream: stream.write(str(process.pid)+'\n')
    with args.out.with_suffix('.launch.json').open('x') as stream: json.dump(record, stream, indent=2)
    record['returncode'] = process.wait()
record['finished_utc'] = datetime.now(timezone.utc).isoformat()
with args.out.with_suffix('.exit.json').open('x') as stream: json.dump(record, stream, indent=2)
