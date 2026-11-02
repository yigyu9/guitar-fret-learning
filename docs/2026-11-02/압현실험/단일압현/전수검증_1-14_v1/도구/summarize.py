"""전수 검사 원문을 대조해 손가락별 줄×프렛 표를 갱신한다.

준비/손가락 후보/압현 실패와 검사 오류를 구분한다. pilot와 과거 연구는
새336조합의 성공 분모에 상속하지 않으며 봉인·정리 검증 실패도 성공에서 제외한다.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
FINGERS=('index','middle','ring','pinky')
KOREAN=('검지','중지','약지','소지')
LABELS={'pending':'미검사','press_success':'현행 압현 달성','native_press_failed':'실제 압현 실패',
        'preparation_failed':'준비 실패','finger_ik_unresolved':'손가락 후보 미확보','inspection_error':'검사 오류'}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)


def collect(run):
    cases=json.loads((STUDY/'설계/cases.json').read_text())['cases']
    if len(cases)!=336 or len({r['case_id'] for r in cases})!=336:raise ValueError('고정336조합 필요')
    records=[]
    state_path=run/'state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {}
    for case in cases:
        row=dict(case,status='pending',checked=False,task_success=False,report=None,clean_fraction=None,wrong_s=None)
        paths=sorted((run/case['case_id']).glob('attempt*/report.json'))
        accepted=[];errors=[]
        for p in paths:
            d=json.loads(p.read_text())
            if d.get('case')!=case['case_id'] or d.get('schema')!='guitar_learning.range336.native_single_press.v1':raise ValueError('보고서 identity 불일치: '+str(p))
            valid=(d.get('completed') is True and d.get('execution_completed') is True and d.get('failure') is None
                and d.get('source_sha256_match_after') is True and d.get('scene_closed') is True and d.get('pool_closed') is True)
            (accepted if valid else errors).append((p,d))
        # 검사 오류 재시도만 허용한다. 정상 과제 실패 뒤의 재시도를 성공으로 골라내지 않는다.
        chosen=accepted[0] if accepted else errors[-1] if errors else None
        if chosen:
            p,d=chosen;valid=bool(accepted);status=d.get('outcome') if valid else 'inspection_error'
            if status not in LABELS:raise ValueError('알 수 없는 결과: '+str(status))
            if status=='press_success' and not(d.get('task_success') and d.get('preparation_ready')):raise ValueError('성공 전제 불일치')
            episode_path=p.with_name('episode.json');episode=json.loads(episode_path.read_text()) if episode_path.exists() else {}
            song=episode.get('song',{});trace=d.get('trace_summary',{})
            row.update(status=status,checked=valid,task_success=status=='press_success',report=str(p.resolve()),attempts=len(paths),
                clean_fraction=song.get('mean_clean_audible_fraction'),wrong_s=trace.get('audible_wrong_control_s'),
                preparation_ready=d.get('preparation_ready'),episode_reason=episode.get('reason'),failure=d.get('failure'),
                finger_tracking_max_error_rad=trace.get('assigned_tracking_max_error_rad'),elapsed_s=d.get('elapsed_s'))
            if row['task_success'] and song.get('stage_success') is not True:raise ValueError('에피소드 성공 불일치')
        if chosen is None and state.get('results',{}).get(case['case_id'],{}).get('status')=='inspection_error':
            row.update(status='inspection_error',failure='실행 보고서 생성 전 검사 오류. 실행 원장은 state.json 및 attempt*.execution.json 참조.')
        records.append(row)
    return records


def plot(rows,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap,BoundaryNorm
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Patch
    plt.rcParams['font.family']=FontProperties(fname='/usr/share/fonts/truetype/nanum/NanumGothic.ttf').get_name()
    statuses=list(LABELS);colors=['#ededed','#50bb94','#ea837c','#e7b96f','#b3a1cd','#6f747e']
    fig,axes=plt.subplots(4,1,figsize=(15,12),layout='constrained')
    for ax,finger,title in zip(axes,FINGERS,KOREAN):
        subset={r['case_id']:r for r in rows if r['finger']==finger};values=np.zeros((6,14),dtype=int)
        for s in range(1,7):
            for f in range(1,15):
                row=subset[f'{finger}_s{s}_f{f}'];values[s-1,f-1]=statuses.index(row['status'])
                if row['status']=='press_success':ax.text(f-1,s-1,f"{100*(row['clean_fraction'] or 0):.0f}%",ha='center',va='center',fontsize=9)
        ax.imshow(values,cmap=ListedColormap(colors),norm=BoundaryNorm(np.arange(-.5,len(statuses)+.5),len(statuses)),aspect='auto')
        ax.set_title(title,loc='left',fontweight='bold');ax.set_xticks(range(14),range(1,15));ax.set_yticks(range(6),[f'{s}번 줄' for s in range(1,7)])
        ax.set_xticks(np.arange(-.5,14,1),minor=True);ax.set_yticks(np.arange(-.5,6,1),minor=True);ax.grid(which='minor',color='white',linewidth=2);ax.tick_params(which='minor',bottom=False,left=False)
    count=sum(r['checked'] for r in rows);success=sum(r['task_success'] for r in rows)
    fig.suptitle(f'1~14프렛 단일 압현 검사 · 정상 검사 {count}/336 · 현행 압현 달성 {success}\n숫자: 원시 240Hz 원장 기반 음 구간 clean 유지율 · 1회 진단이며 학습 결과 아님',fontsize=16)
    fig.legend(handles=[Patch(color=c,label=LABELS[s]) for s,c in zip(statuses,colors)],loc='outside lower center',ncol=3,frameon=False)
    fig.savefig(path,dpi=150,facecolor='white');plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,default=STUDY/'로그/sweep_v1');parser.add_argument('--no-plot',action='store_true');args=parser.parse_args()
    rows=collect(args.run);counts=dict(Counter(r['status'] for r in rows));out=STUDY/'분석'
    write(out/'전수검증_결과.json',dict(schema='range336.summary.v1',total=336,counts=counts,source_run=str(args.run.resolve()),rows=rows,
        denominator='336 fixed combinations; pilot and past results not inherited; inspection errors and pending remain explicit',
        limitation='Finite local search misses are unresolved, not proof of physical impossibility. Success is current loaded-pad task, not acoustic performance.'))
    with (out/'전수검증_결과.csv').open('w',newline='') as stream:
        fields=list(dict.fromkeys(key for row in rows for key in row))
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    lines=['# 1~14프렛 단일 압현 전수 검사','',f"전체336조합: 정상 검사{sum(r['checked'] for r in rows)}, 현행 압현 달성{sum(r['task_success'] for r in rows)}.",'',
        '기호: 성공=현행 압현 달성(괄호 안은 음 구간 clean 유지율), 준비=준비 실패, 후보=손가락 후보 미확보, 압현=실제 압현 실패, 오류=검사 오류, —=미검사.','',
        '탐색 미해결은 물리적 불가능 판정이 아니다. 개별 조합1회 진단이며 여러 초기 조건의 안정적 성공률이나 정책 학습 성공을 뜻하지 않는다. 성공은 봉인·종료·원시 에피소드 검증을 통과한 경우만 인정한다.','']
    symbols={'pending':'—','preparation_failed':'준비','finger_ik_unresolved':'후보','native_press_failed':'압현','inspection_error':'오류'}
    for finger,title in zip(FINGERS,KOREAN):
        lines += ['## '+title,'','| 줄 / 프렛 | '+' | '.join(map(str,range(1,15)))+' |','|---|'+'---:|'*14]
        for s in range(1,7):
            cells=[]
            for f in range(1,15):
                r=next(r for r in rows if r['case_id']==f'{finger}_s{s}_f{f}')
                cells.append(f"성공({100*(r['clean_fraction'] or 0):.0f}%)" if r['task_success'] else symbols[r['status']])
            lines.append(f'| {s} | '+' | '.join(cells)+' |')
        lines.append('')
    lines += ['[원시 집계](전수검증_결과.json) · [CSV](전수검증_결과.csv)','']
    (out/'전수검증_결과.md').write_text('\n'.join(lines))
    if not args.no_plot:plot(rows,out/'전수검증_현황.png')
    print(json.dumps(counts,ensure_ascii=False))


if __name__=='__main__':main()
