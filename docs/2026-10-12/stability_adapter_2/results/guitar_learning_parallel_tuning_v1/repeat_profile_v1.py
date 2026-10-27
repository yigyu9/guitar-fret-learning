"""Repeat top two environment counts sequentially, then profile a fixed native buffer."""
from pathlib import Path
import subprocess,json,sys,time,threading
base=Path(__file__).resolve().parent;root=base.parents[4]
reports=[json.loads(p.read_text()) for p in base.glob('bench_n*/report.json')]
assert len(reports)>=4 and all(d['completed'] for d in reports)
ordered=sorted(reports,key=lambda d:d['collection_transitions_per_s'],reverse=True)
counts=[d['settings']['num_envs'] for d in ordered[:2]]
(base/'repeat_decision.json').write_text(json.dumps(dict(counts=counts,rule='repeat two fastest valid count trials; same saved settings'),indent=2))
for n in counts:
 name='repeat_n%d_v1'%n
 command=[sys.executable,'-m','guitar_learning.train_parallel','--settings',str(base/'inputs'/('bench_n%d.json'%n)),'--out',str(base/name)]
 print('START '+name,flush=True)
 with (base/(name+'_console.txt')).open('x') as stream:
  proc=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 if proc.returncode:raise SystemExit(proc.returncode)
 print('DONE '+name,flush=True)
# A separate read-only optimizer trial; no physical benchmark is concurrent.
with (base/'update_device_profile_console.txt').open('x') as stream:
 proc=subprocess.run([sys.executable,str(base/'profile_updates_v1.py'),'--run',str(base/('bench_n%d_v1'%counts[0]))],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
raise SystemExit(proc.returncode)
