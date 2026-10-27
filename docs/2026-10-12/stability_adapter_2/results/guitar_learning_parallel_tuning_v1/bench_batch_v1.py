"""Sequential prespecified environment-count trials; no concurrent benchmarks."""
from pathlib import Path
import subprocess,json,sys,time,threading,hashlib
base=Path(__file__).resolve().parent;root=base.parents[4]
results=[]
def run(n):
 name='bench_n%d_v1'%n;out=base/name;command=[sys.executable,'-m','guitar_learning.train_parallel','--settings',str(base/'inputs'/('bench_n%d.json'%n)),'--out',str(out)]
 print('START '+name,flush=True);samples=[];stop=threading.Event()
 def monitor():
  while not stop.is_set():
   proc=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True)
   samples.append(dict(monotonic=time.monotonic(),returncode=proc.returncode,output=proc.stdout.strip()))
   stop.wait(2.)
 thread=threading.Thread(target=monitor);thread.start()
 try:
  with (base/(name+'_console.txt')).open('x') as stream:proc=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 finally:stop.set();thread.join()
 with (base/(name+'_gpu_monitor.json')).open('x') as stream:json.dump(samples,stream)
 row=dict(name=name,command=command,exit_code=proc.returncode);results.append(row)
 print(json.dumps(row),flush=True)
 if proc.returncode:raise SystemExit(proc.returncode)
for n in [2,4,8]:run(n)
a=json.loads((base/'bench_n8_v1/report.json').read_text());b=json.loads((base/'bench_n4_v1/report.json').read_text())
condition=a['collection_transitions_per_s']>=1.3*b['collection_transitions_per_s'] and a['resources']['min_available_memory_bytes']>=8*1024**3
with (base/'n16_decision.json').open('x') as stream:json.dump(dict(run_n16=condition,n8_over_n4=a['collection_transitions_per_s']/b['collection_transitions_per_s'],n8_min_available_bytes=a['resources']['min_available_memory_bytes'],rule='gain>=30% and minimum available RAM>=8GiB during N8'),stream,indent=2)
if condition:run(16)
with (base/'bench_batch_results.json').open('x') as stream:json.dump(results,stream,indent=2)
