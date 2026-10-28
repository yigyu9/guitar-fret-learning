"""One fixed-denominator on/off comparison after actual completion."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('off_figure_guard',HERE/'analyze.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
a.complete(a.on.read(a.BASE/'01_launcher.json'),a.on.read(a.BASE/'cpu_inputs/commands.json'))
v=a.on.read(HERE/'results_v1/comparison.json');out=HERE/'results_v1/comparison.png';assert not out.exists()
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=[v[k][m]['acceptance'] for m in a.on.MODES for k in ('paired_on','cases')];x=np.arange(4)
fig,ax=plt.subplots(figsize=(10.5,4.8));fig.subplots_adjust(left=.08,right=.99,bottom=.21,top=.88)
for offset,key,label,color in [(-.18,'all3_achieved_fraction','All3 achieved','#377eb8'),(.18,'A_released_fraction','A native released','#ff7f00')]:
    bars=ax.bar(x+offset,[r[key]*100 for r in rows],.35,label=label,color=color)
    for b,r in zip(bars,rows):ax.text(b.get_x()+b.get_width()/2,b.get_height()+1.5,'%d/128'%round(r[key]*128),ha='center',fontsize=9)
ax.axhline(90,color='black',ls=':',lw=1,label='Original 90% rate threshold')
ax.set(xticks=x,xticklabels=['On\ndeterministic','Off\ndeterministic','On\nstochastic','Off\nstochastic'],ylim=(0,116),ylabel='All 128 first attempts (%)',title='Guard bypass changes target directions; all3 stochastic stays 10/128')
ax.legend(loc='upper left',fontsize=8,ncol=3);ax.grid(axis='y',alpha=.2)
fig.text(.01,.025,'Stochastic release includes A-unachieved: on 77/118, off 83/124. Full music also requires clean/wrong and zero failures.',fontsize=8)
fig.savefig(out,dpi=150);plt.close(fig)
