"""관절 운동·접근 거리·학습 실패와 학습률을 저장된 로그에서 시각화한다."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
BASE=Path(__file__).resolve().parents[1]
rows=json.loads((BASE/'분석/움직임과실패_수치.json').read_text())
labels=['S1','S2','S3','T1','T2','T3'];x=np.arange(6)
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
a=axes[0,0];w=.25
for offset,key,label,color in [(-w,'eval_goal_requested_max_range_deg_mean','Evaluation: requested','#d99a27'),(0,'eval_goal_joint_max_range_deg_mean','Evaluation: actual','#2675b5'),(w,'train_goal_joint_max_range_deg_mean','Training: actual','#7b9e65')]:
 a.bar(x+offset,[r[key] for r in rows],w,label=label,color=color)
a.set(title='Goal-finger joint movement',ylabel='Mean episode max joint range (degrees)',xticks=x,xticklabels=labels);a.legend(fontsize=8)
a=axes[0,1];values=[r['eval_goal_pad_min_distance_mm_mean'] for r in rows]
a.bar(x,values,color='#2675b5');a.axhline(10,color='#c24c4c',ls='--',label='10 mm hover reference')
for i,v in enumerate(values):a.text(i,v+1,f'{v:.1f}',ha='center',fontsize=9)
a.set(title='Even the closest pad position stayed far away',ylabel='Mean closest distance per note (mm)',xticks=x,xticklabels=labels,ylim=(0,88));a.legend(fontsize=8)
a=axes[1,0];values=[100*r['train_terminal_failure_count']/r['train_episodes'] for r in rows]
a.bar(x,values,color='#c66a53')
for i,v in enumerate(values):a.text(i,v+1,f'{v:.1f}%',ha='center',fontsize=9)
a.set(title='Guitar-displacement terminations during training',ylabel='Completed training episodes (%)',xticks=x,xticklabels=labels,ylim=(0,48))
a=axes[1,1]
for label,case,color in [('S1: single middle S3F6',rows[0]['case'],'#2675b5'),('T2: middle S3F6 to S1F8',rows[4]['case'],'#c66a53')]:
 metrics=[json.loads(t) for t in (BASE/'실행_v1/로그'/f'{case}_train/attempt01/J/learning_metrics.jsonl').read_text().splitlines()]
 a.plot(np.arange(1,len(metrics)+1),[m['actor_lr']*1e5 for m in metrics],label=label,color=color)
a.set(title='One failed case kept its initial learning rate',ylabel='Actor learning rate (x 1e-5)',xlabel='PPO update',ylim=(0,3.4));a.legend(fontsize=8)
for a in axes.flat:a.grid(axis='y',alpha=.18);a.set_axisbelow(True)
fig.suptitle('100-update J33 study: motion and contact diagnosis',fontsize=15)
fig.savefig(BASE/'분석/실패원인_로그요약.png',dpi=160)
