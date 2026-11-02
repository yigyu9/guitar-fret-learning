"""Read-only aggregation of sealed ledgers and new observational evaluations."""
from pathlib import Path
import sys,json,gzip,csv,hashlib,collections,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R))
from guitar_learning.training.training_log_io import iter_episode_rows
PH={'prepare':(0,3),'A':(3,4.5),'gap':(4.5,5.25),'B':(5.25,6.75),'tail':(6.75,7.25)}
def phase(t):return next((k for k,(a,b) in PH.items() if a-1e-7<=t<b-1e-7),'tail')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False))
def csvout(name,rows):
 if rows:
  with (L/'tables'/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def eps(p):return sorted([r['episode'] for r in iter_episode_rows(p)],key=lambda e:e['env_id'])
def outcome(es):
 v=[e['left_note_ledger']['values'] for e in es];n=len(v)
 return dict(n=n,A=sum(bool(x['left'][0]) for x in v),B=sum(bool(x['left'][1]) for x in v),AB=sum(all(x['left']) and not (e['termination']['physical_failure'] or e['termination']['wrist_failure']) for e,x in zip(es,v)),whole_AB=sum(all(t>=1.5-1e-8 for t in x['clean']) and not (e['termination']['physical_failure'] or e['termination']['wrist_failure']) for e,x in zip(es,v)),mean_A_clean_s=float(np.mean([x['clean'][0] for x in v])),mean_B_clean_s=float(np.mean([x['clean'][1] for x in v])),failure=sum(e['termination']['physical_failure'] or e['termination']['wrist_failure'] for e in es))
summary={};conditions=[];reward_rows=[];repeat=[]
folders=[p.parent for p in (D/'진단').glob('*/report.json') if (p.parent/'action_mode.json').exists() and not p.parent.name.startswith('smoke')]+[p.parent for p in (L/'runs').glob('*/report.json')]
for p in sorted(folders):
 es=eps(p);o=outcome(es);summary[p.name]=o;conditions.append(dict(condition=p.name,**o));
 if p.parent==L/'runs':
  rep=json.loads((p/'report.json').read_text());repeat.append(dict(condition=p.name,**o,front32_AB=outcome(es[:32])['AB'],AB_ids=[e['env_id'] for e in es if all(e['left_note_ledger']['values']['left']) and not (e['termination']['physical_failure'] or e['termination']['wrist_failure'])],checkpoint_sha256=rep['checkpoint_sha256'],settings=rep['settings']))
  ids=[e['finger_control_diagnostics']['episode_id'] for e in es];n=len(es);sums=collections.defaultdict(lambda:collections.defaultdict(float));groups=collections.defaultdict(lambda:collections.defaultdict(float));nticks=collections.Counter();maxcon=0;maxround=0;sumterms=np.zeros((n,9));costtotal=0;counterfinal={};termsorder=None
  with gzip.open(p.with_name(p.name+'_reward60.jsonl.gz'),'rt') as f:
   for line in f:
    row=json.loads(line);keys=list(row['reward_terms']);termsorder=keys
    for i in range(n):
     if row['episode_ids'][i]!=ids[i]:continue
     ph=phase(row['end_s'][i]-1/120);nticks[ph]+=1;vals=[row['reward_terms'][k][i] for k in keys];maxcon=max(maxcon,abs(sum(vals)-row['returned_reward'][i]));maxround=max(maxround,max(abs(row['counter_delta'][k][i]-row['reward_terms'][k][i]) for k in keys));sumterms[i]+=vals;costtotal+=row['cost'][i]
     for k,v in zip(keys,vals):sums[ph][k]+=v;groups['success' if all(es[i]['left_note_ledger']['values']['left']) else 'failure'][k]+=v
     sums[ph]['separate_failure_cost']+=row['cost'][i]
  mismatch=max(abs(sumterms[i,j]-es[i]['reward_components'][k]) for i in range(n) for j,k in enumerate(termsorder))
  assert maxcon<1e-5 and mismatch<1e-4,(p.name,maxcon,mismatch)
  for ph in PH:
   reward_rows.append(dict(condition=p.name,phase=ph,env_control_ticks=nticks[ph],**{k:v/n for k,v in sums[ph].items()}))
  dump(p/'reward_analysis.json',dict(max_component_vs_returned_abs=maxcon,max_component_vs_counter_delta_abs=maxround,max_sum_vs_episode_counter_abs=mismatch,first_episode_ids=ids,separate_cost_sum=costtotal,phase_per_env={ph:{k:v/n for k,v in x.items()} for ph,x in sums.items()},scope='exact 60Hz returned reward terms; midpoint bin; no subdivision into240Hz'))
csvout('conditions.csv',conditions);csvout('phase_reward.csv',reward_rows);dump(L/'repeat_results.json',repeat)
# Integrated wrong-source time. Causes/body overlaps intentionally not summed into wrong total.
src=list(csv.DictReader((L/'tables/wrong_sources.csv').open()));agg=collections.defaultdict(list)
for x in src:agg[(x['condition'],x['phase'],x['body'],x['cause'])].append(x)
sourceagg=[]
for (c,ph,b,why),xs in agg.items():sourceagg.append(dict(condition=c,phase=ph,body=b,cause=why,envs=len(xs),mean_seconds_all_envs=sum(float(x['duration_s']) for x in xs)/summary[c]['n'],body_all_causes_fret_min=min(float(x['body_all_causes_fret_min']) for x in xs),body_all_causes_fret_max=max(float(x['body_all_causes_fret_max']) for x in xs)))
csvout('wrong_sources_aggregated.csv',sourceagg)
# Learning summary: last snapshot and full update series, no fabricated rollout gradients.
b=json.loads((L/'learning_ledger.json').read_text());lrrows=[];train={}
for seed,rs in b['series'].items():
 train[seed]=dict(updates=len(rs),transitions=sum(x['transitions'] for x in rs),accepted_actor_steps=sum(x['diagnostics']['minibatches']['actor_accepted']['steps'] for x in rs),rejected_actor_steps=sum(x['diagnostics']['minibatches']['actor_rejected']['steps'] for x in rs),value_steps=sum(x['diagnostics']['minibatches']['value']['steps'] for x in rs),retries=sum(x['kl_retries'] for x in rs),recoveries=sum(x['natural_press_lr']['next_lr']>x['natural_press_lr']['used_lr'] for x in rs),max_attempted_KL=max(x['max_attempted_kl'] for x in rs),min_LR=min(x['actor_lr'] for x in rs),max_accepted_minibatch_grad_norm=max(x['diagnostics']['minibatches']['actor_accepted']['max'].get('grad_norm_pre_clip',0) for x in rs),median_update_last_actor_grad_norm=float(np.median([x['actor_grad_norm'] for x in rs])),median_clip_fraction=float(np.median([x['diagnostics']['post_update']['clip_fraction'] for x in rs])),clip_gt10pct_updates=sum(x['diagnostics']['post_update']['clip_fraction']>.10 for x in rs))
 for i,x in enumerate(rs):
  dg=x['diagnostics'];lrrows.append(dict(seed=seed,update=i+1,LR=x['actor_lr'],KL=x['analytic_kl'],retries=x['kl_retries'],clip_fraction=dg['post_update']['clip_fraction'],reward_value_loss=x['reward_value_loss'],reward_EV=dg['post_update']['critics']['reward']['explained_variance'],cost_EV=dg['post_update']['critics']['cost']['explained_variance'],reward_adv_std=dg['advantages']['reward_raw']['std'],cost_adv_std=dg['advantages']['cost_raw']['std'],actor_grad_norm=x['actor_grad_norm']))
csvout('learning_updates.csv',lrrows);dump(L/'training_summary.json',train)
# Representative env0 timelines preserve scope, all pads/lower status explicit.
for name in ('base_seed7_u300_mean','base_seed17_u300_mean','base_seed17_u300_sampled','base_seed17_u200_mean'):
 rows=list(csv.DictReader((L/'tables'/f'{name}_env0_timeline.csv').open()));t=np.array([float(r['t']) for r in rows]);get=lambda k:np.array([(1. if r[k]=='True' else 0. if r[k]=='False' else float(r[k])) for r in rows]);fig,ax=plt.subplots(6,1,figsize=(12,15),sharex=True)
 for aa in ax:
  aa.axvspan(3,4.5,color='C0',alpha=.08);aa.axvspan(5.25,6.75,color='C1',alpha=.13);aa.grid(alpha=.25)
 ax[0].plot(t,get('wrist_mm'),label='wrist guide excess max |xyz| mm');ax[0].axhline(10,color='r',ls='--',label='phase ready 10mm');ax[0].legend(loc='upper right')
 for k in ('height_mm','lateral_mm','fret_excess_mm'):ax[1].plot(t,get(k),label=k)
 ax[1].axhline(3,color='k',ls='--',label='height upper / lateral threshold');ax[1].legend(loc='upper right');ax[1].set_ylabel('selected approach sample mm')
 ax[2].plot(t,get('normal_cos'),label='normal cos');ax[2].plot(t,get('B_loaded'),label='assigned body loaded bool');ax[2].axhline(.1,color='k',ls='--');ax[2].legend(loc='upper right')
 for k in ('B_raw','B_effective','B_wrong','B_position','B_facing'):ax[3].plot(t,get(k)+.035*('B_raw','B_effective','B_wrong','B_position','B_facing').index(k),label=k)
 ax[3].plot(t,get('B_clean_streak_s'),color='black',label='B integrated clean streak seconds');ax[3].legend(loc='upper right',ncol=3);ax[3].set_ylabel('endpoint flags (offset)')
 for j,n in enumerate(('MCP x','MCP z','PIP','DIP')):
  ax[4].plot(t,get(f'requested_{j}_deg'),label=n+' requested');ax[4].plot(t,get(f'applied_{j}_deg'),ls='--',alpha=.6);ax[4].plot(t,get(f'actual_{j}_deg'),ls=':',alpha=.8)
 ax[4].legend(loc='upper right',ncol=2);ax[4].set_ylabel('native axes deg\nsolid request -- apply : actual')
 ax[5].plot(t,get('standby_weight'),label='B actual standby weight');ax[5].plot(t,get('standby_rate'),label='B standby payout rate /s');ax[5].legend();ax[5].set_xlabel('episode score time seconds');fig.suptitle(name+' / env0 first episode; blue=A orange=B');fig.tight_layout();fig.savefig(L/'figures'/f'{name}_timeline.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(3,1,figsize=(11,9),sharex=True)
for seed in ('7','17'):
 rs=[x for x in lrrows if x['seed']==seed];xx=[x['update'] for x in rs]
 for aa,key in zip(ax,('LR','KL','clip_fraction')):aa.plot(xx,[r[key] for r in rs],label='seed'+seed);aa.set_ylabel(key);aa.grid(alpha=.2);aa.legend()
ax[-1].set_xlabel('cumulative updates');fig.tight_layout();fig.savefig(L/'figures/learning_updates.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5));ks=[k for k in summary if k.startswith('base_seed') and 'std' not in k];xx=np.arange(len(ks));ax.bar(xx-.18,[summary[k]['A']/summary[k]['n'] for k in ks],.18,label='A');ax.bar(xx,[summary[k]['B']/summary[k]['n'] for k in ks],.18,label='B');ax.bar(xx+.18,[summary[k]['AB']/summary[k]['n'] for k in ks],.18,label='AB');ax.set_xticks(xx);ax.set_xticklabels([k.replace('base_seed','s').replace('_u',' / ').replace('_',' ') for k in ks],rotation=65,ha='right');ax.set_ylim(0,1.05);ax.legend();ax.set_ylabel('first episode rate, failures included');fig.tight_layout();fig.savefig(L/'figures/outcomes.png',dpi=150);plt.close(fig)
if reward_rows:
 name='s17_u200_mean_N128_repeat1';rs=[x for x in reward_rows if x['condition']==name];keys=[k for k in rs[0] if k not in ('condition','phase','env_control_ticks')];fig,ax=plt.subplots(figsize=(13,5));width=.8/len(keys);xx=np.arange(len(rs))
 for j,k in enumerate(keys):ax.bar(xx+(j-len(keys)/2)*width,[r[k] for r in rs],width,label=k)
 ax.set_xticks(xx);ax.set_xticklabels([x['phase'] for x in rs]);ax.legend(fontsize=7,ncol=3);ax.set_ylabel('exact term sum per first episode / phase');ax.set_title(name);fig.tight_layout();fig.savefig(L/'figures/phase_rewards.png',dpi=150);plt.close(fig)
dump(L/'summary.json',dict(evaluations=summary,training=train,repeats=repeat,limitations=['env0 only full joint geometry traces','approach witness differs from any-positive contact witness','wrong body source times integrated over audible note, source strings not recorded','extra observer synchronization may change physical trajectories','no saved observations/latent rollout to recover reward-specific gradients']))
print('summaries, term conservation checks, CSV and figures complete',flush=True)
