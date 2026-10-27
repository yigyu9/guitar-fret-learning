"""Keep exact native Python exit status for a detached authorized training run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--mode', choices=('on', 'off'), required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--transfer', type=Path, required=True)
args = p.parse_args()
command = [sys.executable, '-u', '-m', 'stability_adapter_2.run_deadline_training_v5',
    '--out', str(args.out), '--strap', args.mode, '--device', 'cuda',
    '--transfer-policy', str(args.transfer), '--interval-minutes', '30',
    '--stop-at', '2026-10-12T11:40:00+09:00']
record = {'command': command, 'started_utc': datetime.now(timezone.utc).isoformat(),
    'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'supervisor_pid': os.getpid(), 'output': str(args.out)}
with args.out.with_suffix('.log').open('x') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    record['pid'] = process.pid
    args.out.with_suffix('.pid').write_text(str(process.pid)+'\n')
    args.out.with_suffix('.launch.json').write_text(json.dumps(record, indent=2)+'\n')
    record['returncode'] = process.wait()
record['finished_utc'] = datetime.now(timezone.utc).isoformat()
args.out.with_suffix('.exit.json').write_text(json.dumps(record, indent=2)+'\n')
