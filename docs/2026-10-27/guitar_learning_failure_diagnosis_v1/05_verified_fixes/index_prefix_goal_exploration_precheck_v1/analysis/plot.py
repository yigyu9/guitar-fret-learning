"""One static comparison, only after both actual jobs and the analysis complete."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('exploration_plot_guard',HERE/'analyze.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
a.complete(a.read(a.BASE/'01_launcher.json'),a.read(a.BASE/'cpu_inputs/commands.json'))
v=a.read(HERE/'results_v1/comparison.json');out=HERE/'results_v1/comparison.png';assert not out.exists()
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=[v['original_goal_acceptance'],*[v['cases'][m]['acceptance'] for m in a.MODES]];x=np.arange(3)
fig,ax=plt.subplots(figsize=(10.5,4.8));fig.subplots_adjust(left=.08,right=.99,bottom=.21,top=.88)
for offset,key,label,color in [(-.18,'all3_achieved_fraction','All3 achieved','#377eb8'),(.18,'A_released_fraction','A native released','#ff7f00')]:
    bars=ax.bar(x+offset,[r[key]*100 for r in rows],.35,label=label,color=color)
    for b,r in zip(bars,rows):ax.text(b.get_x()+b.get_width()/2,b.get_height()+1.5,'%d/128'%round(r[key]*128),ha='center',fontsize=9)
ax.axhline(90,color='black',ls=':',lw=1,label='Original 90% rate threshold')
ax.set(xticks=x,xticklabels=['Original goal70e\ndeterministic','Candidate std4\ndeterministic','Candidate std4\nstochastic'],ylim=(0,116),ylabel='All 128 first attempts (%)',title='Sampling changes music and release differently; PPO updates = 0')
ax.legend(loc='upper left',fontsize=8,ncol=3);ax.grid(axis='y',alpha=.2)
fig.text(.01,.025,'Stochastic release 118 includes 77 without A achievement. Full music also requires per-note clean/wrong and zero failures.',fontsize=8)
fig.savefig(out,dpi=150);plt.close(fig)
