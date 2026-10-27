"""Supervise independent-scene validation/training and record exact exit status."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--probe',action='store_true')
p.add_argument('--checkpoint',type=Path);p.add_argument('--adopt',action='store_true');p.add_argument('--steps',type=int,default=256);p.add_argument('--max-updates',type=int)
a=p.parse_args()
if a.probe:command=[sys.executable,'-u','-m','stability_adapter_2.run_parallel_probe_v1','--out',str(a.out)]
else:
    if not a.checkpoint:p.error('checkpoint required')
    command=[sys.executable,'-u','-m','stability_adapter_2.run_parallel_training_v1','--out',str(a.out),
        '--num-envs','4','--rollout-steps',str(a.steps),'--strap','on','--device','cuda',
        '--interval-minutes','30','--stop-at','2026-10-12T11:40:00+09:00',
        '--adopt-parallel-checkpoint' if a.adopt else '--checkpoint',str(a.checkpoint)]
    if a.max_updates:command+=['--max-updates',str(a.max_updates)]
record={'started_utc':datetime.now(timezone.utc).isoformat(),'command':command,'supervisor_pid':os.getpid(),
    'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with a.out.with_suffix('.log').open('x') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=process.pid
    with a.out.with_suffix('.launch.json').open('x') as f:json.dump(record,f,indent=2)
    record['returncode']=process.wait()
record['finished_utc']=datetime.now(timezone.utc).isoformat()
with a.out.with_suffix('.exit.json').open('x') as f:json.dump(record,f,indent=2)
