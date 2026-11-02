from pathlib import Path
import json,gzip,csv,collections,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R))
from guitar_learning.training.training_log_io import iter_episode_rows
rep=json.loads((L/'repeat_results.json').read_text());fig,ax=plt.subplots(figsize=(9,4));xx=np.arange(len(rep));ax.bar(xx,[r['AB'] for r in rep],color=['C1' if r['n']==128 else 'C0' for r in rep]);ax.set_xticks(xx);ax.set_xticklabels([r['condition'].replace('s17_u200_mean_','') for r in rep],rotation=25,ha='right');ax.set_ylabel('AB achieved first episodes / N');ax.set_title('Same checkpoint: repeated observed evaluation (no training)');ax.set_ylim(0,128);ax.axhline(12,color='gray',ls='--',label='old128:12');ax.axhline(5,color='k',ls=':',label='old128repeat:5');ax.legend();fig.tight_layout();fig.savefig(L/'figures/repeat_AB.png',dpi=150);plt.close(fig)
p=L/'runs/s17_u200_mean_N128_repeat3';es=sorted([r['episode'] for r in iter_episode_rows(p)],key=lambda e:e['env_id']);ids=[e['finger_control_diagnostics']['episode_id'] for e in es];success=np.array([all(e['left_note_ledger']['values']['left']) and not(e['termination']['physical_failure'] or e['termination']['wrist_failure']) for e in es]);counts={'success':int(success.sum()),'failure':int((~success).sum())};phase=lambda t:next((n for n,(a,b) in {'prepare':(0,3),'A':(3,4.5),'gap':(4.5,5.25),'B':(5.25,6.75),'tail':(6.75,7.25)}.items() if a-1e-7<=t<b-1e-7),'tail');tot=collections.defaultdict(lambda:collections.defaultdict(float));curves=[]
with gzip.open(p.with_name(p.name+'_reward60.jsonl.gz'),'rt') as f:
 for line in f:
  row=json.loads(line);include=np.array([a==b for a,b in zip(ids,row['episode_ids'])])
  if not include.any():continue
  time=np.array(row['end_s']);keys=list(row['reward_terms']);means={k:float(np.array(row['reward_terms'][k])[include].mean()) for k in keys} if include.any() else {};curves.append(dict(t=float(time[0]),**means))
  for i in np.where(include)[0]:
   group='success' if success[i] else 'failure';ph=phase(time[i]-1/120)
   for k in keys:tot[(ph,group)][k]+=row['reward_terms'][k][i]
   tot[(ph,group)]['separate_failure_cost']+=row['cost'][i]
rows=[dict(condition=p.name,phase=ph,group=g,n=counts[g],**{k:v/counts[g] for k,v in vals.items()}) for (ph,g),vals in tot.items()]
with (L/'tables/phase_reward_by_outcome.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,ax=plt.subplots(2,1,figsize=(12,7),sharex=True);keys=list(curves[0])[1:];t=np.array([x['t'] for x in curves]);valid=t<=7.25+1e-7
for k in keys:
 y=np.array([x.get(k,np.nan) for x in curves]);ax[0].plot(t[valid],y[valid],label=k);ax[1].plot(t[valid],np.nancumsum(y)[valid],label=k)
for aa in ax:aa.axvspan(3,4.5,color='C0',alpha=.08);aa.axvspan(5.25,6.75,color='C1',alpha=.1);aa.grid(alpha=.2)
ax[0].set_ylabel('actual60Hz term, first-episode env mean');ax[1].set_ylabel('cumulative term, not discounted return');ax[0].legend(ncol=3,fontsize=7);ax[-1].set_xlabel('score time seconds / s17u200 N128repeat3');fig.tight_layout();fig.savefig(L/'figures/reward_time.png',dpi=150);plt.close(fig)
(L/'reward_time.json').write_text(json.dumps({'condition':p.name,'first_episode_ids':ids,'outcome_counts':counts,'actual60Hz_env_mean':curves,'scope':'exact term mean, subsequent episodes excluded, sums are not discounted returns'},indent=2));print('repeat and reward timelines complete')
