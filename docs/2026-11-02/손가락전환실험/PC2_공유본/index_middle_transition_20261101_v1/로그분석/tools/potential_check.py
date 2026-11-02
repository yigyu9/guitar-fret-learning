from pathlib import Path
import json,gzip,sys
import numpy as np
L=Path(__file__).resolve().parents[1];R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R))
from guitar_learning.training.training_log_io import iter_episode_rows
out={}
for p in sorted((L/'runs').glob('*repeat[123]')):
 es=sorted([x['episode'] for x in iter_episode_rows(p)],key=lambda e:e['env_id']);ids=[e['finger_control_diagnostics']['episode_id'] for e in es];n=len(es);counts=np.zeros(n,int);sums=np.zeros(n);seq=[]
 with gzip.open(p.with_name(p.name+'_reward60.jsonl.gz'),'rt') as f:
  for line in f:
   x=json.loads(line)
   for i in range(n):
    if x['episode_ids'][i]!=ids[i]:continue
    r=x['reward_terms']['song_left_approach'][i];sums[i]+=.99**int(counts[i])*r;counts[i]+=1
    if i==0:seq.append(r)
 phi=[]
 with gzip.open(p/'finger_control_trace.jsonl.gz','rt') as f:
  for line in f:
   x=json.loads(line)
   if x['env_id']==0 and x['episode_id']==ids[0] and abs(x['episode_time_s']*60-round(x['episode_time_s']*60))<1e-6:phi.append(x['natural_preparation']['approach_potential_endpoint'])
 assert len(seq)==len(phi)==435
 # t0 not logged: infer from the first transition, then verify all later transitions independently.
 phi0=.99*phi[0]-seq[0];phi[-1]=0.;err=max(abs(seq[j]-(.99*phi[j]-phi[j-1])) for j in range(1,435));tel=abs(sums[0]+phi0)
 assert err<1e-5 and tel<1e-5,(p.name,err,tel)
 out[p.name]={'gamma':.99,'ticks_by_env':counts.tolist(),'discounted_approach_by_env':sums.tolist(),'discounted_range':[float(sums.min()),float(sums.max())],'env0_phi0_inferred_from_first_transition':phi0,'env0_max_later_transition_potential_error':err,'env0_discounted_terminal_balance_abs':tel,'scope':'t0 Phi inferred, not independently recorded; later 434 actual transitions checked against endpoint Phi; final Phi forced0 by original contract; no policy-performance inference'}
(L/'potential_check.json').write_text(json.dumps(out,indent=2));print([(k,v['discounted_range'],v['env0_max_later_transition_potential_error']) for k,v in out.items()])
