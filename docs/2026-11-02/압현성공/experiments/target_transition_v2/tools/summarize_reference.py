"""학습과 같은 초기 자세의 참조 재생 결과를 모아 시간표 선택 근거를 남긴다."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    fig,axes=plt.subplots(3,1,figsize=(11,7),constrained_layout=True)
    results=[]
    for ax,gap in zip(axes,('0.5','0.75','1.0')):
        out=BASE/'validation'/('reference_gap_'+gap+'_v5')
        report=json.loads((out/'report.json').read_text())
        assert report['scene_destroyed']and report['source_unchanged']and report['no_intermediate_reset']
        trace=np.load(out/'trace240.npz');t=trace['time_s'];candidate=trace['candidate']
        if (candidate[:,0]&candidate[:,1]).any():raise ValueError('유효 후보 동시 성공 재발')
        desired=np.full(len(t),np.nan)
        for note in report['notes']:
            desired[(t>note['start_s'])&(t<=note['end_s'])]=note['goal_fret']
            ax.axvspan(note['start_s'],note['end_s'],color='#f3ddae',alpha=.3)
        actual=np.where(candidate[:,0],6.,np.where(candidate[:,1],7.,np.nan))
        ax.plot(t,desired,'k--',lw=2,label='목표 프렛')
        ax.plot(t,actual,color='#397db5',lw=1.6,label='수정 판정의 유효 프렛 후보')
        ax.set_yticks([6,7]);ax.set_ylim(5.6,7.5);ax.set_xlim(0,8);ax.grid(alpha=.2)
        verified=report['AB_on_time_full_hold_verified']
        ax.set_title(f'휴지 {gap}초 · A→B 정시 시작/전체 유지 '+('통과'if verified else '미충족'),fontproperties=font)
        ax.legend(prop=font,loc='lower left',ncol=2)
        results.append(dict(gap_s=float(gap),AB_on_time_full_hold_verified=verified,ABA_on_time_full_hold_verified=report['ABA_on_time_full_hold_verified'],
            notes=report['notes'],maximum_guitar_displacement_m=report['maximum_guitar_displacement_m'],
            maximum_guitar_rotation_rad=report['maximum_guitar_rotation_rad'],report=str(out/'report.json'),
            report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest()))
    axes[-1].set_xlabel('참조 재생 물리 시각 (초)',fontproperties=font)
    fig.suptitle('같은 초기 자세 · 자유 기타 · 상태 덮어쓰기 없는 목표각 참조',fontproperties=font)
    fig.savefig(BASE/'validation/reference_comparison.png',dpi=150);plt.close(fig)
    (BASE/'validation/reference_summary.json').write_text(json.dumps(dict(selected_gap_s=.75,results=results,
        scope='one native replay per gap; proxy contacts, not acoustic measurement; no learned policy performance',
        interpretation='0.75/1.0 passed this path;0.5 failed this path, not an impossibility proof'),ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
