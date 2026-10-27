"""Supervise a reviewed native graphics-isolation run and preserve exit status."""
import argparse
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import subprocess,sys
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
p.add_argument('--checkpoint',type=Path,required=True)
p.add_argument('--probe-reference',type=Path)
p.add_argument('--adopt',action='store_true')
p.add_argument('--max-updates',type=int)
a=p.parse_args()
if a.probe_reference:
    command=[sys.executable,'-u',str(Path(__file__).with_name('run_graphics_reset_probe_v2.py')),
        '--out',str(a.out),'--checkpoint',str(a.checkpoint),'--reference-episode',str(a.probe_reference),'--resets','60']
else:
    command=[sys.executable,'-u','-m','stability_adapter_2.run_deadline_training_v9',
        '--out',str(a.out),'--strap','on','--device','cuda','--interval-minutes','30',
        '--stop-at','2026-10-12T11:40:00+09:00',
        '--adopt-graphics-checkpoint' if a.adopt else '--checkpoint',str(a.checkpoint)]
    if a.max_updates:command+=['--max-updates',str(a.max_updates)]
record={'command':command,'started_utc':datetime.now(timezone.utc).isoformat(),
    'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'supervisor_pid':os.getpid(),'output':str(a.out)}
with a.out.with_suffix('.log').open('x') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    record['pid']=process.pid
    with a.out.with_suffix('.launch.json').open('x') as f:json.dump(record,f,indent=2)
    record['returncode']=process.wait()
record['finished_utc']=datetime.now(timezone.utc).isoformat()
with a.out.with_suffix('.exit.json').open('x') as f:json.dump(record,f,indent=2)
