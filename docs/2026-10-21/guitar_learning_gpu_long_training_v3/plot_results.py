"""Static figures from measured memory events and committed learning metrics."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

p=Path(__file__).resolve().parent
run=p/'train1024_large_2000'
def rows(path):
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):break
            yield json.loads(line)

def cache(path):
    return [r for r in rows(path) if r.get('event')=='cuda_cache_release' and r.get('reason')=='optimizer_boundary']
old=cache(p.parent/'guitar_learning_gpu_long_run_check_v1/train1024_large_64_batched_v4/events.jsonl')
new=cache(run/'events.jsonl')
fig,axes=plt.subplots(1,2,figsize=(12,4.2),constrained_layout=True)
for data,label,color in [(old,'Before: 1024, failed after 39 updates','#c44e52'),(new,'Aggregate: 1024, measured run','#4c72b0')]:
    if not data:continue
    x=[d['update_index']+1 for d in data]
    free=np.array([d['after']['free_bytes'] for d in data])/1024**3
    reserved=np.array([d['after']['reserved_bytes'] for d in data])/1024**3
    axes[0].plot(x,free,label=label,color=color)
    axes[1].plot(x,(free[0]+reserved[0])-free-reserved,label=label,color=color)
axes[0].set(ylabel='GPU free memory after cache release (GiB)',ylim=(0,12),xlim=(0,200),title='First 200 updates')
axes[1].set(ylabel='Estimated non-Torch growth from first update (GiB)',title='Full measured run')
for ax in axes:
    ax.set_xlabel('Committed PPO update')
    ax.grid(alpha=.25)
    ax.legend(fontsize=8)
fig.suptitle('GPU memory: large policy, 1024 environments, horizon 32')
fig.savefig(p/'gpu_memory_comparison.png',dpi=160)
plt.close(fig)

x=[]; reward=[]; cost=[]; original_cost=[]; extra_cost=[]; progress=[]; kl=[]
for r in rows(run/'learning_metrics.jsonl'):
    x.append(r['update_index']+1); reward.append(r['mean_reward']);cost.append(r['mean_cost'])
    extra_cost.append(sum(e.get('cost_components',{}).get('remaining_song_failure',0) for e in r.get('completed_episodes',[]))/r['transitions'])
    original_cost.append(r['mean_cost']-extra_cost[-1])
    progress.append(r['left_curriculum']['progress']);kl.append(r.get('analytic_kl',np.nan))
analysis=json.loads((p/'learning_analysis.json').read_text())
windows=analysis['windows']
# The 100-update episode bins need not contain all-episode or fixed-policy evaluations.
def series(field):
    out=[]
    for w in windows:
        value=w
        for key in field.split('.'):
            value=value.get(key) if isinstance(value,dict) else None
        out.append(np.nan if value is None else value)
    return out
wx=[(w['update_index_first']+w['update_index_last'])/2+1 for w in windows]
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
axes[0,0].plot(x,reward,label='Reward',color='C0',alpha=.8)
axes[0,0].set_ylabel('Reward / transition',color='C0')
cost_axis=axes[0,0].twinx()
cost_axis.plot(x,cost,label='Total cost',color='C1',alpha=.7)
cost_axis.plot(x,original_cost,label='Original cost',color='C2',alpha=.7)
cost_axis.plot(x,extra_cost,label='Remaining-song failure cost',color='C3',alpha=.6,linestyle=':')
cost_axis.set_ylabel('Cost / transition')
axes[0,0].set_title('Collected signals (changing policy / song phase)')
axes[0,1].plot(x,progress,label='Curriculum progress [0,2]')
axes[0,1].plot(wx,series('means.episode_reach_fraction.mean'),label='Wrist reach, ended episodes')
axes[0,1].plot(wx,series('means.episode_contact_fraction.mean'),label='Contact candidate, ended episodes')
axes[0,1].set_title('Curriculum and episode measurements')
axes[1,0].plot(wx,series('timeline_complete_fraction'),label='Timeline complete / ended')
axes[1,0].plot(wx,series('physical_failure_fraction'),label='Physical failure / ended')
axes[1,0].plot(wx,series('left_notes_all_ended.fraction'),label='Achieved notes / all ended-episode targets')
axes[1,0].set(title='100-update bins; unfinished episodes excluded',ylim=(-.03,1.03))
axes[1,1].plot(x,kl,label='Post-update analytic KL')
axes[1,1].axhline(.02,color='gray',linestyle='--',label='KL budget')
axes[1,1].set_title('PPO update size')
for ax in axes.flat:
    ax.set_xlabel('Committed PPO update');ax.grid(alpha=.25);ax.legend(fontsize=8)
handles,labels=axes[0,0].get_legend_handles_labels()
h2,l2=cost_axis.get_legend_handles_labels()
axes[0,0].legend(handles+h2,labels+l2,fontsize=7)
fig.suptitle('Left-hand song learning; contact candidates do not certify acoustic success')
fig.savefig(p/'learning_curves.png',dpi=160)
plt.close(fig)
print(json.dumps(dict(memory_updates=len(new),learning_updates=len(x))))
