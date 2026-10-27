"""Scientific summary from pinned analysis outputs and sampled resources."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
RUN=OUT.parent/'guitar_learning_long_B_8env_dense_v2_20261018_130137'
paths=[Path(__file__).resolve(),OUT/'analysis.json',OUT/'runtime_analysis.json',RUN/'report.json',RUN/'resources.jsonl']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with (OUT/'plot_inputs_before.json').open('x') as f:json.dump(pins,f,indent=2)
data=json.loads((OUT/'analysis.json').read_text());runtime=json.loads((OUT/'runtime_analysis.json').read_text())
report=json.loads((RUN/'report.json').read_text())
rows=[r for r in data['per_update'] if r['committed']];x=[r['update_index']+1 for r in rows]
plt.rcParams.update({'font.size':11,'axes.titlesize':12,'figure.dpi':150})
fig,axes=plt.subplots(2,3,figsize=(15,8.3),layout='constrained')
ax=axes[0,0];ax.plot(x,[r['episode_reward_mean'] for r in rows],marker='.',color='#1f77b4');ax.set(title='Episode return: no musical success',xlabel='Completed PPO update',ylabel='Mean completed episode return')
for ax,key,title,color in [(axes[0,1],'left_near_onset_m','Left origin-to-fret near onset','#2e8b57'),(axes[0,2],'right_sweep_m','Right pick-to-guide in sweep window','#cf6e17')]:
    ax.plot(x,[1000*r['metrics'][key]['mean'] for r in rows],marker='.',color=color)
    ax.set(title=title,xlabel='Completed PPO update',ylabel='Mean geometric proxy distance (mm)')
ax=axes[1,0];ax.plot(x,[r['analytic_kl'] for r in report['updates']],marker='.',color='#8856a7');ax.axhline(.02,color='#bd2437',ls='--',label='KL budget 0.02');ax.set(title='PPO updates stayed within KL budget',xlabel='Completed PPO update',ylabel='Analytic KL');ax.legend(fontsize=10)
times=[];rss=[];pss=[]
for line in (RUN/'resources.jsonl').read_text().splitlines():
    r=json.loads(line);workers=r.get('workers',[])
    if len(workers)==8 and all(w['memory']['rss_current_bytes'] is not None and w['memory']['pss_current_bytes'] is not None for w in workers):
        times.append(r['elapsed_s']/60);rss.append(sum(w['memory']['rss_current_bytes'] for w in workers)/2**30);pss.append(sum(w['memory']['pss_current_bytes'] for w in workers)/2**30)
ax=axes[1,1];ax.plot(times,rss,label='8 workers current RSS',color='#bd2437');ax.plot(times,pss,label='8 workers current PSS',color='#8856a7');ax.set(title='Worker memory kept increasing',xlabel='Elapsed wall time (min)',ylabel='Sum of sampled current memory (GiB)');ax.legend(fontsize=9)
ax=axes[1,2];values=[runtime['timing']['percent_of_wall'][k] for k in ('reset_s','step_s','update_s')];names=['Reset + preparation','Policy stepping','PPO optimizer'];ax.barh(names,values,color=['#bd2437','#1f77b4','#2e8b57']);ax.invert_yaxis();ax.set(xlim=(0,61),xlabel='Share of total wall time (%)',title='Time spent in simulator work')
for i,v in enumerate(values):ax.text(v+.5,i,'%.3f%%'%v,va='center',fontsize=10)
for ax in axes.flat:ax.grid(alpha=.2);ax.set_axisbelow(True)
fig.suptitle('8-worker dense_v2 run: 25 updates / 51,200 committed transitions / 0 matches',fontsize=15)
fig.savefig(OUT/'training_analysis.png',dpi=160)
fig.savefig(OUT/'training_analysis.pdf')
plt.close(fig)
changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
with (OUT/'plot_verification.json').open('x') as f:json.dump(dict(completed=not changed,changed_inputs=changed),f,indent=2)
assert not changed
