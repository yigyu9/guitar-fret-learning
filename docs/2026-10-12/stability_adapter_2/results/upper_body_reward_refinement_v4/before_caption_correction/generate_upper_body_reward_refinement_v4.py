import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4')
data=json.loads((base/'plot_data.json').read_text())
font_path='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family']=font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['axes.unicode_minus']=False
fig,axs=plt.subplots(1,3,figsize=(21,8.4),dpi=120)
fig.patch.set_facecolor('#f5f7fb')
for ax in axs:
 ax.set_facecolor('white')
 ax.grid(True,axis='y',color='#dbe3eb',linewidth=.8)
 ax.spines[['top','right']].set_visible(False)
# 1: Hold reward comparison, input values copied from plot_data.json.
hold=data['hold_comparison'];x=[r['duration_s'] for r in hold]
y3=[r['v3_hold_max'] for r in hold];y4=[r['v4_hold_max_one_event_beta1'] for r in hold]
ax=axs[0]
ax.plot(x,y3,'o-',color='#c06a35',lw=2.7,ms=7,label='v3.1: 2 × 지속시간 (초당 누적)')
ax.plot(x,y4,'s-',color='#347a9f',lw=2.7,ms=7,label='v4: 고정 event hold, β=1')
ax.set_title('유지 보상 상한 비교',fontsize=16,fontweight='bold',color='#18324b',pad=14)
ax.set_xlabel('eligible 유지 시간 (초)',fontsize=11)
ax.set_ylabel('홀드 항 최대 기여 (후보 점수; 정산 단위 상이)',fontsize=10)
ax.set_xticks(x);ax.set_ylim(-.25,21.7);ax.legend(loc='upper left',fontsize=9,frameon=True)
ax.text(.04,.57,'v3: 초당 +2 누적\nv4: 한 Fret event에서 최대 +0.10β\n단위·분모가 달라 직접 성능 비교 아님',transform=ax.transAxes,va='top',fontsize=9,color='#526879',bbox=dict(boxstyle='round,pad=.4',fc='white',ec='#c5d0db',alpha=.92))
# 2: Onset example, beta=1 conditional comparisons.
ax=axs[1]
labels=['초안: 6/6 정음\nU=0','초안: 5/6 오음\nU=1','v4 하한: 정음\n최악 하위항','v4 하한: 실패\n최선 하위항']
vals=[data['onset_example']['draft_correct_hold0'],data['onset_example']['draft_wrong_hold1'],data['onset_example']['six_string_correct_lower_worst'],data['onset_example']['five_of_six_wrong_lower_best']]
colors=['#76a98c','#d77763','#347a9f','#8496b0']
bars=ax.bar(range(4),vals,color=colors,width=.68)
ax.axvline(1.5,color='#91a0ad',ls='--',lw=1.3)
for bar,val in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,val+.035,f'{val:.3f}'.rstrip('0').rstrip('.'),ha='center',va='bottom',fontsize=10,fontweight='bold',color='#18324b')
ax.set_xticks(range(4),labels,fontsize=9);ax.set_ylim(0,2.75)
ax.set_title('β=1 조건부 onset 비교',fontsize=16,fontweight='bold',color='#18324b',pad=14)
ax.set_ylabel('조건부 event 점수 (후보)',fontsize=11)
ax.text(.04,.97,'초안 예: 오음+U가 정음보다 큼\nv4 하한: 정음 1.826 > 실패 1.609\n각 쌍에서 다른 1차·기타 항 동일 가정',transform=ax.transAxes,va='top',fontsize=9,color='#526879',bbox=dict(boxstyle='round,pad=.4',fc='white',ec='#c5d0db',alpha=.92))
# 3: Approach quality, plotted from JSON arrays, distance converted m -> mm only.
ax=axs[2];dist_mm=[v*1000 for v in data['approach_distance_m']]
ax.plot(dist_mm,data['approach_quality'],color='#6a65a8',lw=3)
ax.fill_between(dist_mm,data['approach_quality'],0,color='#8d87c1',alpha=.12)
ax.set_xlim(0,250);ax.set_ylim(-.04,1.08)
ax.set_title('접근 보조 함수 후보',fontsize=16,fontweight='bold',color='#18324b',pad=14)
ax.set_xlabel('유효 영역 바깥 거리 (mm)',fontsize=11);ax.set_ylabel('접근 품질 A (0–1)',fontsize=11)
ax.text(.04,.97,'clamp(1 - d / 250 mm, 0, 1)\n유효 영역 안은 plateau 1\nsource geometry 미검증 toy 곡선',transform=ax.transAxes,va='top',fontsize=9,color='#526879',bbox=dict(boxstyle='round,pad=.4',fc='white',ec='#c5d0db',alpha=.92))
fig.suptitle('v4 보상 수식 비교 · 설계/합성 산술 · 새 물리 0 / 학습 0',fontsize=22,fontweight='bold',color='#18324b',y=.99)
fig.text(.5,.935,'plot_data.json 표본을 사용한 수학적 비교 · 세 패널은 각자 독립 y축이며 학습 성능 그래프가 아님',ha='center',fontsize=11,color='#526879')
fig.tight_layout(rect=[0,.02,1,.91],w_pad=2.3)
fig.savefig(base/'reward_refinement.png',bbox_inches='tight',facecolor=fig.get_facecolor())
