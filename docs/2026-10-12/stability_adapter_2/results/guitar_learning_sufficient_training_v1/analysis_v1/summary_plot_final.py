from pathlib import Path
import json
out=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1')
s=json.loads((out/'training_final_summary.json').read_text())
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_path='/usr/share/fonts/truetype/nanum/NanumSquareR.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family']=font_manager.FontProperties(fname=font_path).get_name()
updates=s['updates'];x=list(range(1,129));success=[u['successes']/u['episodes']*100 for u in updates];hold=[u['episode_summary']['hold_fraction']['mean']*100 for u in updates];ready=[u['episode_summary']['ready_s']['mean']/.2*100 for u in updates]
def rolling(values):return [sum(values[i-15:i+1])/16 if i>=15 else float('nan') for i in range(len(values))]
fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharex=True,sharey=True)
axes[0].plot(x,success,color='#2d6a9f',alpha=.18,lw=1,label='업데이트별 성공률 (8회)');axes[0].plot(x,rolling(success),color='#2166ac',lw=2.4,label='최근 16업데이트 평균');axes[0].axhline(s['all_episodes']['success_fraction']*100,color='#777777',ls='--',lw=1,label='전체 평균 51.66%');axes[0].set_title('왼손 단음 성공률');axes[0].set_ylabel('비율 (%)')
axes[1].plot(x,rolling(hold),color='#2a9d8f',lw=2.4,label='음 구간 목표 접촉 유지율');axes[1].plot(x,rolling(ready),color='#d47716',lw=2.4,label='마지막 200ms 준비 구간 접촉률');axes[1].set_title('접촉 유지와 준비 — 최근 16업데이트 평균')
for ax in axes:
 ax.axvspan(.5,14.5,color='#b6b6b6',alpha=.23,zorder=0);ax.axvline(14.5,color='#999999',lw=.8,ls=':');ax.set_xlim(.5,128.5);ax.set_ylim(0,100);ax.set_yticks([0,20,40,60,80,100]);ax.set_xlabel('이번 실행의 추가 업데이트');ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=9,framealpha=.9)
fig.suptitle('추가 128회 학습 · 1,024회 수행 · 물리 실패 0회',fontsize=14,y=.99);fig.text(.5,.015,'회색: 과거 C의 처음 14회와 정확히 재현되는 구간 · 단일 학습 계보/동일 준비 자세 · 최종 정책 평가는 별도',ha='center',fontsize=9,color='#444444');fig.tight_layout(rect=[0,.055,1,.94]);fig.savefig(str(out/'summary_learning_curve.png'),dpi=170);plt.close(fig)
