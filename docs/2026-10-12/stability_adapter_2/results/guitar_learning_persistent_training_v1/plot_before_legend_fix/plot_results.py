"""Final plots only; inputs are pinned before reading and never overwritten."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
RUN=OUT/'run_v1'
paths=[Path(__file__).resolve(),OUT/'learning_analysis.json',OUT/'runtime_analysis.json',RUN/'report.json']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with (OUT/'plot_inputs_before.json').open('x') as f:json.dump(pins,f,indent=2)
d=json.loads((OUT/'learning_analysis.json').read_text());runtime=json.loads((OUT/'runtime_analysis.json').read_text());report=json.loads((RUN/'report.json').read_text())
rows=[r for r in d['per_update'] if r['committed']];x=[r['update_index']+26 for r in rows];old=d['baseline_last_five_updates']
plt.rcParams.update({'font.size':10,'axes.titlesize':12})
fig,axes=plt.subplots(2,3,figsize=(15,8.2),layout='constrained')
ax=axes[0,0];ax.plot(x,[r['episode_reward_mean'] for r in rows],'.-',color='#1f77b4');ax.axhline(old['episode_reward_mean'],ls='--',color='#888888',label='Previous last-5 mean');ax.set(title='Completed episode return',xlabel='Cumulative PPO update',ylabel='Mean return');ax.legend(fontsize=9)
for ax,key,title,color in [(axes[0,1],'left_near_onset_m','Left origin-to-fret near onset','#2e8b57'),(axes[0,2],'right_sweep_m','Right pick-to-guide during sweep','#cf6e17')]:
    ax.plot(x,[1000*r['metrics'][key]['mean'] for r in rows],'.-',color=color)
    ax.axhline(old['metrics'][key]['mean']*1000,ls='--',color='#888888',label='Previous last-5 mean')
    ax.set(title=title,xlabel='Cumulative PPO update',ylabel='Mean geometric proxy distance (mm)');ax.legend(fontsize=9)
ax=axes[1,0]
for label,color,style,name,field in [('Previous: current RSS','#999999','--','old','worker_current_rss_GiB'),('Persistent: current RSS','#bd2437','-','new','worker_current_rss_GiB'),('Persistent: current PSS','#8856a7','-','new','worker_current_pss_GiB')]:
    series=runtime[name]['resources']['complete_series'];ax.plot([v['elapsed_s']/60 for v in series],[v[field] for v in series],ls=style,color=color,label=label)
ax.set(title='Same 8 workers: current memory',xlabel='Elapsed wall time (min)',ylabel='Sum of sampled memory (GiB)');ax.legend(fontsize=9)
ax=axes[1,1];success=[100*r['completed_episodes_with_strict_match']/r['episode_count'] for r in rows];ax.plot(x,success,'.-',color='#2e8b57');ax.set(title='Episodes with a strict musical match',xlabel='Cumulative PPO update',ylabel='Completed episodes (%)',ylim=(-1,max(5,max(success)+1)))
ax=axes[1,2];ax.plot(x,[r['analytic_kl'] for r in report['updates']],'.-',color='#8856a7');ax.axhline(.02,color='#bd2437',ls='--',label='KL budget 0.02');ax.set(title='PPO update size',xlabel='Cumulative PPO update',ylabel='Analytic KL');ax.legend(fontsize=9)
for ax in axes.flat:ax.grid(alpha=.2);ax.set_axisbelow(True)
fig.suptitle('Persistent simulator continuation: +%d updates / %s committed transitions'%(d['completed_updates'],format(report['transitions'],',')),fontsize=15)
fig.savefig(OUT/'training_progress.png',dpi=160);fig.savefig(OUT/'training_progress.pdf');plt.close(fig)
changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
with (OUT/'plot_verification.json').open('x') as f:json.dump(dict(completed=not changed,changed_inputs=changed),f,indent=2)
assert not changed
