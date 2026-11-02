"""검산된 서로 다른 과제의 결과를 분리해서 표시한다."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parents[1]
fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
a=axes[0];values=[12,5,1,28,56];bars=a.bar(range(5),[v/128*100 for v in values],color=['#7d8992']*2+['#d28b26']*3)
a.set_xticks(range(5));a.set_xticklabels(['old 1','old 2','observer 1','observer 2','observer 3'],rotation=18)
a.set_title('PC2: same seed17 / 200 model\nIndex fret4 -> middle fret6, mean, 128 envs')
for bar,v in zip(bars,values):a.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,f'{v}/128',ha='center',fontsize=9)
a.text(.03,.92,'First 32 env IDs: AB = 0 in all five runs',transform=a.transAxes,fontsize=9)
a.set_ylabel('AB achievement (%)');a.set_ylim(0,100)
records=json.loads((OUT/'pc1_comparison_snapshot.json').read_text())['records']
rows=[next(r for r in records if r['condition']==condition and r['seed']==seed and r['total']==100 and r['N']==128 and r['mode']=='mean') for seed in (7,17) for condition in ('control','conservative')]
a=axes[1];x=list(range(4));w=.35
for off,key,name,color in [(-w/2,'AB','AB achievement','#447da3'),(w/2,'full_duration_pair','Both notes held for 1.5 s','#468661')]:
 bars=a.bar([i+off for i in x],[r['recomputed'][key]/128*100 for r in rows],w,label=name,color=color)
 for bar,r in zip(bars,rows):a.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,str(r['recomputed'][key]),ha='center',fontsize=8)
a.set_xticks(x);a.set_xticklabels(['control s7','low LR s7','control s17','low LR s17'],rotation=18)
a.set_title('PC1: +100 model-only fine-tuning\nMiddle fret6 -> fret7, mean, 128 envs')
a.set_ylabel('Rate (%), labels = count / 128');a.set_ylim(0,115);a.legend(fontsize=8,loc='upper left')
for a in axes:a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
(OUT/'figures').mkdir(exist_ok=True);fig.savefig(OUT/'figures/PC1_PC2_review.png',dpi=160);plt.close(fig)
