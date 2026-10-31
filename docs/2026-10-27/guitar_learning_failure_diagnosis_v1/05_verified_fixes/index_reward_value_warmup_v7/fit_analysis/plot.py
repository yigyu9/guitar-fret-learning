"""고정 가치망 보정 전후 오차를 구간별로 그린다."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
source = HERE.parent/'runs/fit/warmup_report.json'
r = json.loads(source.read_text())
labels = ['pre-A','A prep','A audible','A release','post-A','B prep','B7 audible','B gap','B8 audible','tail']
fig,axes = plt.subplots(1,2,figsize=(14,4.5),constrained_layout=True)
for ax,split in zip(axes,['train','holdout']):
    x = np.arange(10)
    for offset,when,color in [(-.2,'before','#b85848'),(.2,'after','#287ca1')]:
        values = [np.sqrt(r[when][split]['phases'][str(i)]['MSE']) for i in range(10)]
        ax.bar(x+offset,values,width=.4,label=when,color=color)
    ax.set_xticks(x);ax.set_xticklabels(labels,rotation=45,ha='right');ax.set_ylabel('Realized discounted return RMSE')
    ax.set_title('%s: envs %s'%(split,'0-95' if split=='train' else '96-127'));ax.legend();ax.grid(axis='y',alpha=.2)
fig.suptitle('V7 reward-value warmup only: fixed guitar / index4 / 3 notes / seed7')
fig.savefig(HERE/'value_rmse.png',dpi=160);plt.close(fig)
paths = [Path(__file__).resolve(),source,HERE/'value_rmse.png']
(HERE/'verification.json').write_text(json.dumps({'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2)+'\n')
