"""One small fixed-denominator comparison, after actual analysis only."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('angle_figure_complete',HERE/'analyze.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
a.complete(a.read(a.BASE/'01_launcher.json'),a.read(a.BASE/'cpu_inputs/commands.json'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
v=a.read(HERE/'results_v1/comparison.json');out=HERE/'results_v1/comparison.png';assert not out.exists()
rows=list(v['historical_acceptance'].items())+[('goal_angle1000',v['acceptance'])];x=np.arange(len(rows));fig,ax=plt.subplots(figsize=(10.5,4.8));fig.subplots_adjust(left=.08,right=.99,bottom=.23,top=.88)
for offset,key,label,color in [(-.18,'all3_achieved_fraction','All3 achieved','#377eb8'),(.18,'A_released_fraction','A native released','#ff7f00')]:
    values=[r[key]*100 for _,r in rows];bars=ax.bar(x+offset,values,.35,label=label,color=color)
    for b,(_,r) in zip(bars,rows):ax.text(b.get_x()+b.get_width()/2,b.get_height()+1.5,'%d/128'%round(r[key]*128),ha='center',fontsize=8)
ax.axhline(90,color='black',ls=':',lw=1,label='Original 90% rate threshold')
ax.set(xticks=x,xticklabels=['Incremental\n1000 steps','Reference-only\n2000 steps','Mixed\n2000 steps','Goal raw loss\n1000 steps','Goal angle loss\n1000 steps'],ylim=(0,116),ylabel='All 128 first attempts (%)',title='All3 and A release stay separate; original failures retained')
ax.legend(loc='upper left',fontsize=8,ncol=2);ax.grid(axis='y',alpha=.2)
fig.text(.01,.02,'Full music also requires per-note clean/wrong and zero failures. Deterministic fixed-guitar F4; no PPO/naturalness claim.',fontsize=8)
fig.savefig(out,dpi=150);plt.close(fig)
