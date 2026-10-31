"""완료된 seed7 100회 비교의 원본 수치로 그래프를 생성한다."""
from pathlib import Path
import json,gzip,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
r=Path(__file__).resolve().parents[1];out=Path(__file__).resolve().parent
font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if font.exists():plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams['axes.unicode_minus']=False
s=json.loads((r/'summary.json').read_text());conditions=['E0','E1','E2','E3','E4'];rows=[s[f'seed7_{x}_u100']['free_v9'] for x in conditions]
colors=['#6b7280','#93a1b0','#a8b7c5','#1c9e7a','#e5902b'];x=np.arange(5)
fig,axes=plt.subplots(2,2,figsize=(12.8,8.2),layout='constrained')
ax=axes[0,0];mcp=[a['env0_trace']['max_actual_initial_extension_deg'][0] for a in rows];pip=[a['env0_trace']['max_actual_initial_extension_deg'][1] for a in rows]
for vals,off,col,label in [(mcp,-.18,'#3879b6','시작 관절 MCP_x'),(pip,.18,'#e0a14a','중간 관절 PIP')]:
 bars=ax.bar(x+off,vals,.36,color=col,label=label);ax.bar_label(bars,fmt='%.2f',fontsize=9,padding=2)
ax.set(xticks=x,xticklabels=conditions,ylabel='최대 초기 펴짐 (도)',ylim=(0,19),title='초기 펴짐 감소 — 대표 환경 1회, 0~3초');ax.legend(fontsize=9)
ax=axes[0,1];bad=[a['mean_unready_slow_wrist_s'] for a in rows];bars=ax.bar(x,bad,color=colors);ax.bar_label(bars,fmt='%.2f',padding=3);ax.set(xticks=x,xticklabels=conditions,ylabel='평균 시간 (초)',ylim=(0,1.3),title='준비 미완료 상태의 저속 손목 시간 — 32회')
ax=axes[1,0];early=[a['mean_early_candidate_s'] for a in rows];bars=ax.bar(x,early,color=colors);ax.bar_label(bars,fmt='%.2f',padding=3);ax.set(xticks=x,xticklabels=conditions,ylabel='음 시작 전 후보 접촉 시간 (초)',ylim=(0,1.15),title='남은 문제: 조기 접촉 후보 증가 — 32회 평균')
ax=axes[1,1];ax.axhspan(4,8,color='#1c9e7a',alpha=.12,label='줄 위 준비 영역 4~8mm');ax.axvline(2.8,color='#777',ls='--',lw=1,label='내려가기 시작 2.8초');ax.axvline(3,color='#b83232',ls=':',lw=1.2,label='실제 음 시작 3초')
inputs=[r/'summary.json']
for c,color in [('E0',colors[0]),('E3',colors[3]),('E4',colors[4])]:
 p=r/f'blocks/seed7_{c}_u100/free_v9_eval/evaluation/finger_control_trace.jsonl.gz';inputs.append(p)
 with gzip.open(p,'rt') as f:allrows=[json.loads(line) for line in f]
 first=min(a['episode_id'] for a in allrows if a['env_id']==0);a=[a for a in allrows if a['env_id']==0 and a['episode_id']==first and a['episode_time_s']<=3.1]
 ax.plot([t['episode_time_s'] for t in a],[t['natural_preparation']['fingers'][1]['height_m']*1000 for t in a],color=color,label=c,lw=1.7)
ax.set(xlabel='실제 에피소드 시각 (초)',ylabel='선택 패드의 압현면 위 높이 (mm)',ylim=(-1,48),xlim=(0,3.1),title='준비 영역을 지나 일찍 표면에 도달함 — 대표 환경');ax.legend(fontsize=8,loc='upper right')
for ax in axes.flat:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('중지 3번 줄 · 6프렛 / large · 64환경 · 100회 · seed7\n모든 조건의 v9 평가: 달성 32/32 · 압현 유지 2.50초 · 물리/손목 실패 0',fontsize=14,fontweight='bold')
fig.savefig(out/'comparison.png',dpi=160,facecolor='white');plt.close(fig)
(out/'figure_provenance.json').write_text(json.dumps(dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},opening_scope='env0 first actual observation baseline; native MCP_x/PIP, not32 mean',time_metrics_scope='all32 first episodes, failures included'),ensure_ascii=False,indent=2)+'\n')
