"""Read-only training monitor plus predeclared low-disk SIGINT guard; no SDK imports."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--pid',type=int,required=True)
    args=parser.parse_args();run=args.run.resolve()
    proc=Path('/proc')/str(args.pid)
    command=(proc/'cmdline').read_bytes().split(b'\0')
    if b'guitar_learning.train' not in command or str(run).encode() not in command:
        raise ValueError('Expected native training PID and exact output path')
    identity=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
    while True:
        try:
            if (proc/'stat').read_text().rsplit(')',1)[1].split()[19]!=identity:break
            os.kill(args.pid,0)
        except (ProcessLookupError,FileNotFoundError):break
        try:
            status=json.loads((run/'status.json').read_text())
        except (FileNotFoundError,json.JSONDecodeError):status={}
        latest=sorted(run.glob('update_*.json'))
        row=json.loads(latest[-1].read_text()) if latest else {}
        disk={str(p):os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in (ROOT,run)}
        gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.free,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True)
        value=dict(run=str(run),utc=datetime.now(timezone.utc).isoformat(),unix_time=time.time(),
            elapsed_s=time.time()-(run/'settings.json').stat().st_mtime,
            phase=status.get('phase'),pid=args.pid,
            disk_free_bytes=disk[str(run)],local_disk_free_bytes=disk[str(ROOT)],
            run_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
            status=status,last_committed_update=row.get('update_index'),
            optimizer_updates=row.get('optimizer_updates'),reward_mean=row.get('mean_reward'),cost_mean=row.get('mean_cost'),
            curriculum=row.get('left_curriculum'),disk_available_bytes=disk,gpu_memory_mib=gpu.stdout.strip(),
            disk_guard='SIGINT native Python once if either output/project available below2GiB; no deletion')
        with (PHASE/'progress.jsonl').open('a') as stream:stream.write(json.dumps(value,allow_nan=False)+'\n')
        if min(disk.values())<2*1024**3:
            with (PHASE/('disk_guard_event_'+run.name+'.json')).open('x') as stream:json.dump(value,stream,indent=2)
            if (proc/'stat').read_text().rsplit(')',1)[1].split()[19]==identity:
                os.kill(args.pid,signal.SIGINT)
            return 2
        print(json.dumps(dict(update=row.get('optimizer_updates'),reward=row.get('mean_reward'),
            cost=row.get('mean_cost'),phase=status.get('phase'),gpu=gpu.stdout.strip())),flush=True)
        time.sleep(50)
    print('native process ended',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
