"""Three prespecified bounded fresh-seed configurations, same selected count/device."""
from pathlib import Path
import subprocess,json,sys,statistics,math,time,threading
base=Path(__file__).resolve().parent;root=base.parents[4]
means={}
for n in (8,16):
 values=[json.loads((base/(kind+'_n%d_v1'%n)/'report.json').read_text()) for kind in ('bench','repeat')]
 assert all(d['completed'] for d in values)
 means[n]=statistics.mean(d['collection_transitions_per_s'] for d in values)
best=max(means.values());n=min(n for n,value in means.items() if value>=.9*best)
profile=json.loads((base/'update_device_profile.json').read_text())['warm_median_s']
device='cuda:0' if profile.get('cuda:0',float('inf'))<.8*profile['cpu'] else 'cpu'
decision=dict(num_envs=n,count_mean_tps=means,count_rule='smallest count within90% of best mean of original+repeat for two fastest counts',device=device,device_rule='CUDA if identical-real-buffer optimizer warm median is at least20% faster; full native pilot verifies execution but not GPU PhysX',warm_optimizer_median_s=profile,scope='three fresh runs; seed7; no model/reward/control/gain changes; 4updates each; tiny pilot not convergence')
(base/'pilot_decision.json').write_text(json.dumps(decision,indent=2))
results=[]
for label,std,lr in [('baseline',math.exp(-3),3e-5),('explore',.12,3e-5),('faster',.12,1e-4)]:
 settings=json.loads((base/('bench_n%d_v1'%n)/'settings.json').read_text());settings.update(updates=4,device=device,initial_std=std);settings['ppo']['actor_lr']=lr
 source=base/'inputs'/('pilot_'+label+'.json');source.write_text(json.dumps(settings,indent=2))
 name='pilot_'+label+'_v1';command=[sys.executable,'-m','guitar_learning.train_parallel','--settings',str(source),'--out',str(base/name)]
 print('START '+name,flush=True);samples=[];stop=threading.Event()
 def monitor():
  while not stop.is_set():
   a=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True)
   samples.append(dict(monotonic=time.monotonic(),returncode=a.returncode,output=a.stdout.strip()));stop.wait(2.)
 thread=threading.Thread(target=monitor);thread.start()
 try:
  with (base/(name+'_console.txt')).open('x') as stream:proc=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 finally:stop.set();thread.join()
 (base/(name+'_gpu_monitor.json')).write_text(json.dumps(samples))
 row=dict(name=name,command=command,exit_code=proc.returncode);results.append(row)
 (base/'pilot_batch_progress.json').write_text(json.dumps(results,indent=2));print(json.dumps(row),flush=True)
 if proc.returncode:
  report=base/name/'report.json'
  if not report.exists():raise SystemExit(proc.returncode)
  d=json.loads(report.read_text())
  if d.get('guard_violations') or d.get('changed_inputs') or d.get('worker_failures') or d.get('physical_flags_errors'):raise SystemExit(proc.returncode)
(base/'pilot_batch_results.json').write_text(json.dumps(results,indent=2))
