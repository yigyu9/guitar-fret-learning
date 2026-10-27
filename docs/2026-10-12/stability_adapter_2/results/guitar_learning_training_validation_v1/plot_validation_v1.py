"""Scientific figure from the recorded native 240Hz evidence only."""
from pathlib import Path
import json,gzip
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(12,4.4))
colors=['#6b7280','#2563eb','#dc2626','#059669','#a855f7']
for mode,color in zip(['zero','right','left_arm','fingers','all'],colors):
 folder=BASE/('probe_D_'+mode+'_v1');times=[0.];distance=[0.]
 for path in sorted((folder/'episode_0000').glob('transition_*.json.gz')):
  with gzip.open(path,'rt') as stream:row=json.load(stream)
  for m in row['info']['physics_measurements']:
   times.append(m['music']['task_time_s']);distance.append(np.linalg.norm(m['stability']['guitar_delta_m'])*1000)
 label={'zero':'Zero action','right':'Right elbow/wrist','left_arm':'Left arm','fingers':'Left fingers','all':'Combined 39'}[mode]
 axes[0].plot(times,distance,label=label,color=color,lw=1.6)
 summary=json.loads((folder/'episode_0000/summary.json').read_text())
 if summary['reason']=='terminal_failure':axes[0].plot(times[-1],distance[-1],'x',color=color,ms=8,mew=2)
axes[0].axhline(80,color='black',ls='--',lw=1,label='Termination: 80 mm')
axes[0].set(xlabel='Task time after preparation (s)',ylabel='Guitar displacement from prepared pose (mm)',title='Default-range trajectory probes (one trial each)')
axes[0].legend(fontsize=8,ncol=2,loc='upper right');axes[0].set_xlim(0,4.8);axes[0].set_ylim(bottom=0)
for mode,color in [('before','#64748b'),('after','#0f766e')]:
 times=[];distance=[];folder=BASE/('eval_'+mode+'_v1')/'episode_0000'
 prepared=json.loads((folder/'prepared.json').read_text());target=next(iter(prepared['music']['geometry']))
 times.append(0);distance.append(np.linalg.norm(prepared['music']['geometry'][target]['delta'])*1000)
 for path in sorted(folder.glob('transition_*.json.gz')):
  with gzip.open(path,'rt') as stream:row=json.load(stream)
  for m in row['info']['physics_measurements']:
   times.append(m['music']['task_time_s']);distance.append(np.linalg.norm(m['music']['geometry'][target]['delta'])*1000)
 axes[1].plot(times,distance,label=mode.capitalize()+' 4 PPO updates',color=color,lw=1.7)
axes[1].axvspan(1.07,1.17,color='#f59e0b',alpha=.15,label='Strict strike window')
axes[1].axvline(1.12,color='#b45309',ls='--',lw=1)
axes[1].set(xlabel='Task time after preparation (s)',ylabel='Ring-finger origin to fret target distance (mm)',title='Same B target: string 2 / fret 7 / ring')
axes[1].legend(fontsize=8,loc='best');axes[1].set_xlim(0,1.47)
for ax in axes:ax.grid(alpha=.2)
fig.text(.5,.015,'Native PhysX CPU records. Marker proximity is not fretting or acoustic success. Both policies: 0 strict matches.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.055,1,1));fig.savefig(BASE/'validation_summary.png',dpi=160);plt.close(fig)
