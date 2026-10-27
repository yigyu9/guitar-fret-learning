from pathlib import Path
import json,hashlib
base=Path(__file__).resolve().parent
paths=[Path(__file__),base/'analysis_v2.json'];pins={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(base/'plot_inputs_before.json').write_text(json.dumps(pins,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
d=json.loads((base/'analysis_v2.json').read_text());rows=d['per_update'];x=np.arange(1,len(rows)+1)
fig,axs=plt.subplots(2,2,figsize=(11.2,7.2),layout='constrained');fig.suptitle('Training stopped during collection #15: host OOM + worker timeout',fontsize=14)
axs[0,0].plot(x,[r['mean_episode_reward'] for r in rows],marker='o',ms=3,color='#2864ad');axs[0,0].set(title='Mean completed-episode reward',ylabel='Reward',ylim=(-.487,-.483));axs[0,0].text(.03,.91,'320 completed episodes: 0 note matches / 0 audible hold',transform=axs[0,0].transAxes,fontsize=9)
axs[0,1].plot(x,[r['mean_episode_cost'] for r in rows],marker='o',ms=3,color='#27896c');axs[0,1].set(title='Mean episode stability cost',ylabel='Integrated cost',ylim=(0,.004))
axs[1,0].plot(x,[r['metrics']['analytic_kl'] for r in rows],marker='o',ms=3,color='#7957a5');axs[1,0].axhline(.02,color='#ba4d4d',ls='--',label='KL limit 0.02');axs[1,0].set(title='Policy KL: no rollback retries',ylabel='Analytic KL',ylim=(0,.023));axs[1,0].legend(loc='lower right',fontsize=9)
allrows=rows+[dict(logged=d['partial_collect_log'])];xx=np.arange(1,len(allrows)+1);axs[1,1].plot(xx,[r['logged']['worker_rss_peak_sum_kib']/1024**2 for r in allrows],marker='o',ms=3,color='#b36e25');axs[1,1].axvspan(14.5,15.4,color='#e6a3a3',alpha=.3);axs[1,1].set(title='Sum of worker RSS high-water marks',ylabel='GiB (shared pages counted)',xlim=(.5,15.4));axs[1,1].text(.03,.06,'#15 partial: 1,792 samples, no PPO update\nGlobal RAM available minimum: 0.546 GiB\nSeparate rg process killed at ~7.86 GiB RSS',transform=axs[1,1].transAxes,fontsize=9,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
for ax in axs.flat:ax.set_xlabel('Update number');ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.savefig(base/'training_diagnosis.png',dpi=170)
changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
(base/'plot_metadata.json').write_text(json.dumps(dict(input_sha256=pins,changed_inputs=changed,scope='Episode reward/cost and KL from14committed updates; workerRSS fromlastreported60Hz samples; globalRAM hasone recordedminimum, not atimecurve. No causal memoryleak claim.'),indent=2))
assert not changed
