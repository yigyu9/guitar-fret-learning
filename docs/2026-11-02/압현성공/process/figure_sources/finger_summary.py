"""반복 성공 선정 결과를 읽어 손가락·조건별 한글 요약 그래프를 만든다."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
BASE=Path(__file__).resolve().parents[2]
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
selected=json.loads((BASE/'process/verified_successes.json').read_text())['successes']
reports={p.parent.name:json.loads(p.read_text()) for p in (BASE/'process/replay').glob('*/report.json')}
counts=[sum(reports[x['mode']]['goals'][x['row']]['finger']==f for x in selected) for f in range(1,5)]
modes=['free_open','free_feedback','free_live'];verified=[]
for mode in modes:
 a=reports[mode]['goals'];b=reports[mode+'_repeat']['goals']
 verified.append(sum(x['failure'] is None and y['failure'] is None and min(x['best_contact_streak_s'],y['best_contact_streak_s'])>=.1-1e-12 for x,y in zip(a,b)))
fig,axes=plt.subplots(1,2,figsize=(11,4.6),layout='constrained')
for ax,labels,values,total,title in [(axes[0],['검지','중지','약지','소지'],counts,4,'손가락별 반복 성공'),(axes[1],['기본 제어','관절 오차 보정','실시간 손목 보정'],verified,16,'제어 조건별 반복 성공')]:
 y=list(range(len(labels)));ax.barh(y,[total]*len(labels),color='#e8edf3',height=.58);ax.barh(y,values,color='#277da8',height=.58)
 for i,v in enumerate(values):ax.text(v+.08,i,f'{v} / {total}',va='center',fontproperties=font,fontsize=12)
 ax.set_yticks(y,labels,fontproperties=font);ax.set_xlim(0,total*1.23);ax.invert_yaxis();ax.set_title(title,fontproperties=font,fontsize=14,pad=12);ax.set_xticks(range(0,total+1,1 if total==4 else 4));ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
fig.suptitle('v9 초기 자세 — 16개 목표 중 5개 반복 성공',fontproperties=font,fontsize=17)
fig.text(.5,-.02,'두 독립 실행 모두 연속 후보 접촉 100ms 이상 · 물리 실패 없음 | 곡 수행·음향 성공과 구분',ha='center',fontproperties=font,fontsize=10)
fig.savefig(BASE/'analysis/finger_summary.png',dpi=160,bbox_inches='tight');plt.close(fig)
(BASE/'analysis/finger_summary.json').write_text(json.dumps({'per_finger':dict(zip(['index','middle','ring','pinky'],counts)),'per_condition':dict(zip(modes,verified)),'selected_rows':sorted(x['row'] for x in selected)},indent=2)+'\n')
