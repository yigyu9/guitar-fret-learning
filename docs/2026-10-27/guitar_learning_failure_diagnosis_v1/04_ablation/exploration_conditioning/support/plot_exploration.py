"""Plot stored target-FK samples; no new stochastic or physics experiment."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE=Path(__file__).resolve().parents[1]
data=json.loads((BASE/'results.json').read_text())
fig,axes=plt.subplots(2,3,figsize=(15,8),sharey='row')
colors=('#3475a5','#d88a32')
x=np.arange(4);width=.34
for column,endpoint in enumerate(('one_tick','60','180')):
    for group,(key,color) in enumerate(zip(('arm12_only','nonthumb16_only'),colors)):
        record=data['groups'][key]['one_tick'] if endpoint=='one_tick' else data['groups'][key]['paths'][endpoint]
        fields=list(record['per_finger'].values());median=np.array([f['centroid_endpoint_mm']['median'] for f in fields])
        lo=np.array([f['centroid_endpoint_mm']['p05'] for f in fields]);hi=np.array([f['centroid_endpoint_mm']['p95'] for f in fields])
        position=x+(group-.5)*width
        axes[0,column].bar(position,median,width,color=color,label=key)
        axes[0,column].errorbar(position,median,yerr=np.array([median-lo,hi-median]),fmt='none',color='#333333',capsize=3,lw=1)
        axes[1,column].bar(position,[f['centroid_centered_rms_spread_mm'] for f in fields],width,color=color)
    label='1 tick (256 paired draws)' if endpoint=='one_tick' else endpoint+' ticks (16 independent paths)'
    axes[0,column].set_title(label)
    for row in range(2):
        axes[row,column].set_xticks(x);axes[row,column].set_xticklabels(('index','middle','ring','pinky'))
        axes[row,column].grid(axis='y',alpha=.2);axes[row,column].set_axisbelow(True)
axes[0,0].set_ylabel('Median centroid displacement from start (mm)')
axes[1,0].set_ylabel('RMS spread around sample mean (mm)')
axes[0,0].legend(loc='upper left',fontsize=9)
fig.suptitle('Prepared035 controller-target FK only; no physical motion or learning'+chr(10)+'Gaussian latent std=exp(-3); paired draws; native codec/bounds; whiskers=p05..p95',fontsize=13)
fig.tight_layout(rect=(0,0,1,.92));fig.savefig(BASE/'exploration_displacement.png',dpi=140);plt.close(fig)
