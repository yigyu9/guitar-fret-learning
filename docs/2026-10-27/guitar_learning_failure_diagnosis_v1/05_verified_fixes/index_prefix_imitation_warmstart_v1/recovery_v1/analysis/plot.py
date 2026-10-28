"""One compact figure from frozen actual outputs; no physics or policy changes."""
from pathlib import Path
import importlib.util
import json

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('warmstart_figure_guard',HERE/'analyze.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit);audit.preflight()
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

v=json.loads((HERE/'results_v1/comparison.json').read_text());r=json.loads((HERE/'results_v1/label_replay.json').read_text())
out=HERE/'results_v1/comparison.png';assert not out.exists()
original=HERE.parent.parent/'runs/collect';nn=HERE.parent/'runs/evaluate'
ref=dict(np.load(original/'trace_env0_episode0.npz'));t=dict(np.load(nn/'trace_env0_episode0.npz'))
metadata=json.loads((original/'trace_metadata.json').read_text());joint=[metadata['joint_names'].index('LH:index'+n) for n in ('2','3')]
body=metadata['body_names'].index('human/LH:index3')
fig,axes=plt.subplots(2,2,figsize=(11,7.4),constrained_layout=True)
ax=axes[0,0];x=np.arange(5)
for offset,key,label,color in [(-.25,None,'Fresh NN 0','#999999'),(0,'collect','Reference','#377eb8'),(.25,'evaluate','Warmstart NN','#e41a1c')]:
    a=v['fresh0000_acceptance'] if key is None else v['cases'][key]['acceptance']
    values=[n['achieved_fraction']*100 for n in a['per_note']]+[a['all3_achieved_fraction']*100,a['A_released_fraction']*100]
    ax.bar(x+offset,values,.24,label=label,color=color)
ax.axhline(90,color='black',ls=':',lw=1);ax.set(xticks=x,xticklabels=['A4','B7','B8','All3','A release'],ylim=(0,110),ylabel='128 first attempts (%)',title='Original criteria; failures retained');ax.legend(fontsize=8)
ax=axes[0,1]
for data,style,label in [(ref,'--','ref'),(t,'-','NN')]:
    for j,color,name in [(0,'#4daf4a','PIP'),(1,'#984ea3','DIP')]:ax.plot(data['time_s'],np.rad2deg(data['q'][:,joint[j]]),style,color=color,label=label+' '+name)
ax.set(xlabel='Local time (s)',ylabel='Actual angle (deg)',title='env0: actual PIP/DIP');ax.legend(ncol=2,fontsize=8)
ax=axes[1,0]
for data,style,label in [(ref,'--','ref'),(t,'-','NN')]:ax.plot(data['time_s'],np.linalg.norm(data['net_body_force_n'][:,body],axis=-1),style,label=label)
ax.set(xlabel='Local time (s)',ylabel='Distal body resultant (N)',title='env0 only; not contact-pair pressure');ax.legend(fontsize=8)
ax=axes[1,1];x=np.arange(6)
for i,name,color in [(2,'PIP','#4daf4a'),(3,'DIP','#984ea3')]:
    ax.plot(x,[p['rms4'][i] for p in v['offline']['errors']['heldout_same_scene']],':o',color=color,label=name+' heldout ref obs')
    ax.plot(x,[p['rms_request_minus_reference4'][i] for p in r['evaluate']['phases']],'-o',color=color,label=name+' NN obs/oldtarget')
ax.set(xticks=x,xticklabels=['ramp','A hold','release','move','close','B hold'],ylabel='Request RMS (action units)',title='Offline correction gap, not executed action');ax.legend(fontsize=8)
for ax in (axes[0,1],axes[1,0]):
    for boundary in (3.1703,3.2703,3.712,3.832):ax.axvline(boundary,color='gray',lw=.6,alpha=.6)
for ax in axes.flat:ax.grid(alpha=.2,axis='y')
fig.savefig(out,dpi=160);plt.close(fig)
