"""One fixed comparison figure; read-only inputs, no physics."""
from pathlib import Path
import importlib.util
import json
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('corrective_plot_guard',HERE/'analyze.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
audit.complete(audit.read(audit.BASE/'01_launcher.json'),audit.read(audit.BASE/'cpu_inputs/commands.json'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
v=audit.read(HERE/'results_v1/comparison.json');out=HERE/'results_v1/comparison.png';assert not out.exists()
fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
colors={'reference_only':'#377eb8','corrective_mixed':'#e41a1c'}
ax=axes[0,0];x=np.arange(5)
cases=[('warmstart',v['historical_warmstart_acceptance'],'#999999')]+[(c,v['cases'][c]['acceptance'],colors[c]) for c in audit.CONDITIONS]
for i,(name,a,color) in enumerate(cases):
    values=[n['achieved_fraction']*100 for n in a['per_note']]+[a['all3_achieved_fraction']*100,a['A_released_fraction']*100]
    ax.bar(x+(i-1)*.26,values,.25,label=name,color=color)
ax.axhline(90,color='black',ls=':',lw=1);ax.set(xticks=x,xticklabels=['A4','B7','B8','All3','A release'],ylim=(0,105),ylabel='128 first attempts (%)',title='Original criteria; failures retained');ax.legend(fontsize=8)
for c in audit.CONDITIONS:
    folder=audit.BASE/'runs'/(c+'_evaluate');t=dict(np.load(folder/'trace_env0_episode0.npz',allow_pickle=False));meta=audit.read(folder/'trace_metadata.json')
    for name,style in [('2','-'),('3','--')]:
        j=meta['joint_names'].index('LH:index'+name);axes[0,1].plot(t['time_s'],np.rad2deg(t['q'][:,j]),style,color=colors[c],label=c+(' PIP' if name=='2' else ' DIP'))
    body=meta['body_names'].index('human/LH:index3');axes[1,0].plot(t['time_s'],np.linalg.norm(t['net_body_force_n'][:,body],axis=-1),color=colors[c],label=c)
    for origin,style in [('native_reference','-'),('saved_NN_shadow','--')]:
        phases=v['cases'][c]['offline_CPU_recompute'][origin]['heldout_same_scene']
        axes[1,1].plot(np.arange(6),[np.sqrt(np.mean(np.square(p['rms4']))) for p in phases],style+'o',color=colors[c],label=c+' '+origin)
axes[0,1].set(xlabel='Local time (s)',ylabel='Actual angle (deg)',title='env0 actual PIP/DIP');axes[0,1].legend(fontsize=7)
axes[1,0].set(xlabel='Local time (s)',ylabel='Distal body resultant (N)',title='env0 only; not contact-pair pressure');axes[1,0].legend(fontsize=8)
axes[1,1].set(xticks=np.arange(6),xticklabels=['ramp','A hold','release','move','close','B hold'],ylabel='Four-column request RMS',title='Offline heldout env3; not native success');axes[1,1].legend(fontsize=6)
for ax in (axes[0,1],axes[1,0]):
    for boundary in (3.1703,3.2703,3.712,3.832):ax.axvline(boundary,color='gray',lw=.6,alpha=.5)
for ax in axes.flat:ax.grid(alpha=.2,axis='y')
fig.savefig(out,dpi=150);plt.close(fig)
