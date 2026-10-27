"""Compare completed free/fixed CPU analyses without changing native raw data."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
rows=[];pins=[];cases=[];assets=[];traces={}
for condition,base in [('free',root),('fixed',root/'fixed')]:
    path=base/'analysis.json';analysis=json.loads(path.read_text());inputs[str(path)]=sha(path)
    for mode in ['incremental','position']:
        run=base/mode;report=json.loads((run/'report.json').read_text());settings=json.loads((run/'settings.json').read_text())
        allpins=json.loads((run/'inputs_before.json').read_text())
        pins.append({p:h for p,h in allpins.items() if '/3/guitar_learning/' in p})
        cases.append(settings['cases']);assets.append(report['scene']['guitar_representation'])
        for name in ['report.json','settings.json','inputs_before.json','trace60.npz']:
            inputs[str(run/name)]=sha(run/name)
        with np.load(run/'trace60.npz',allow_pickle=False) as f:
            trace={k:f[k].copy() for k in ['q','target','alive','tick']}
        traces[condition,mode]=trace
        window=(trace['tick']/60>=11.5)&(trace['tick']/60<=12)
        complete=trace['alive'][window].all(0)
        cols=[i for i,n in enumerate(report['joint_names']) if not n.startswith('LH:thumb')]
        err=(trace['q'][window][:,complete][:,:,cols]-np.array(report['B_target_rad'])[cols])*180/np.pi
        rms=np.sqrt((err*err).mean((0,2)))
        failures=[r for r in report['failure_reasons'] if r]
        counts=np.array([r['flags'] for r in failures],dtype=int).sum(0).tolist() if failures else [0]*4
        rows.append(dict(condition=condition,mode=mode,summary=analysis['results'][mode]['summary'],
            B_original_row_denominator=84,B_completed_rows=int(complete.sum()),
            B_finger4_actual_rms_deg_max=max(v['actual_rms_deg'] for r in analysis['results'][mode]['rows']
                if r['B_final60']['fully_observed'] for v in r['B_final60']['fingers'].values()),
            B_total16_actual_rms_deg_median=float(np.median(rms)),B_total16_actual_rms_deg_max=float(rms.max()),
            B_total16_actual_absolute_error_deg_max=float(abs(err).max()),B_row_rms_deg=rms.tolist(),
            B_row_ids=np.flatnonzero(complete).tolist(),failure_reason_counts=dict(zip(
                ['guitar_translation','guitar_rotation','velocity','support_normal'],counts)),
            failure_flags_may_overlap=True,scene_closed=report['scene']['closed'],
            gpu_physx=report['scene']['physx_use_gpu'],gpu_pipeline=report['scene']['use_gpu_pipeline'],
            diagnostic_guitar_mode=report['scene']['diagnostic_guitar_mode']))
assert all(p==pins[0] for p in pins) and len(pins[0])==510
assert all(c==cases[0] for c in cases)
assert all(a==assets[0] for a in assets)
paired={}
for mode in ['incremental','position']:
    a,b=traces['free',mode],traces['fixed',mode]
    good=(a['alive'][:,:42]&b['alive'][:,:42])&(a['tick'][:,None]/60<=6)
    delta=(a['target'][:,:42]-b['target'][:,:42])[good]
    paired[mode]=dict(target_path_both_alive_0_to6s_max_target_difference_rad=float(abs(delta).max()),joint_scalar_samples=int(delta.size))
payload=dict(schema='guitar_learning.control_matrix_free_fixed.v1',input_sha256=inputs,results=rows,
    all_four_runs_same_active510_source_pins=True,predeclared_cases_identical=True,guitar_asset_metadata_identical=True,
    runner_sources='free run_control_matrix.py and fixed run_control_matrix_fixed.py separately pinned; not identical scripts',
    paired_target_paths=paired,scope='No training. Failure-time samples censored; all84row/336finger denominators retained. Free B angle statistics condition on completed rows and cannot establish unbiased free/fixed quality rankings.')
(root/'analysis.free_fixed.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
lines=['# 자유 기타·고정 기타 제어 비교','','**기타를 고정하면 두 제어 모드 모두84행 전체가 완료되고 B 도달 각도 기준을 통과했다.** 자유 기타에서는 각각54/84·40/84행이 물리 실패해, 마지막 B 자세를 관측하지 못한 경우가 많았다. 이번 결과는 전반적인 관절 구동 고장을 지지하지 않으며, 손가락의 실제 추종과 손가락 움직임에 동반된 기타 이탈을 분리해서 조사해야 한다. 기타가 밀린 것인지 지지가 줄어 낙하한 것인지는 현재 순힘·변위만으로 확정할 수 없다.','','## 동일 조건과 분모','','네 실행은 같은 활성 Python510개 SHA, 사전 지정84행, 기타 단일 강체89shape 자산 메타데이터를 사용했다. 자유/고정 진단 실행 스크립트는 각각 별도로 봉인되어 있고 동일 원문이 아니다. GPU PhysX·GPU tensor pipeline과 장면 종료를 모두 확인했다. 고정은 진단 전용이며 최종 학습은 자유 기타 조건을 유지한다.','','| 조건 | 제어 | 물리 실패/84 | 추종 창 완전관측/84 | 완전관측 창 p95 최대 | B 완료 행/84 | B 통과/336손가락 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
    s=r['summary'];lines.append(f"| {r['condition']} | {r['mode']} | {s['failed_cases']} | {s['tracking_windows_complete']} | {s['complete_tracking_p95_deg']['maximum']:.3f}° | {s['B_rows_complete']} | {s['B_checks_pass']} |")
lines+=['','추종은 ±0.15rad 명목 목표각의3~4초/5.5~6초 선택축 오차 p95≤10°이며 완전관측 창은 모두 통과했다. 양방향은 native 관절 축 부호이고 해부학적 굽힘/펴짐을 일괄 가정하지 않는다. B는 각 손가락4축 RMS≤10°·최대≤20°다. 실패·불완전행을 통과로 세지 않고 원분모에 남겼다.','','## B 각도와 기타 이탈은 다른 문제','','| 조건 | 제어 | B 관측 행/84 | 손가락4축 RMS 최대(판정 단위) | 관절 절대오차 최대(판정 단위) | 16축 통합 RMS 행 중앙값 | 16축 통합 RMS 행 최대 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for r in rows:
    lines.append(f"| {r['condition']} | {r['mode']} | {r['B_completed_rows']} | {r['B_finger4_actual_rms_deg_max']:.3f}° | {r['B_total16_actual_absolute_error_deg_max']:.3f}° | {r['B_total16_actual_rms_deg_median']:.3f}° | {r['B_total16_actual_rms_deg_max']:.3f}° |")
lines+=['','고정에서는84행 전체, 자유에서는 생존한30/44행만 관측했다. 자유의 RMS가 조금 작아도 자유 기타의 B 자세가 더 낫다는 증거가 아니다. 고정 검사는 B 목표각이 현행 PD·native 범위에서 대체로 실행 가능함을 보여주며, 자유 기타의 B 이동 경로가 안전하다는 뜻은 아니다. 손가락 이동과 기타 접촉/지지 변화를 이어서 살펴야 한다.','','자유 실패 flags는 누적에서 변위51·회전3·속도1, 위치에서 변위37·회전1·속도2이며 겹칠 수 있다. 고정 조건에서는 변위 자체가 제한되므로 실패0만으로 안전 제어가 좋아졌다고 말하지 않는다.','','## 누적 출력과 위치 제어의 의미','','같은 출력0.05를5초 유지하면 누적은 한계 도달 전 총1rad(57.296°) 이동을 요청하고 위치는 참조각에서 부호별 native 가동범위의5%만큼 떨어진 고정 목표를 요청한다. 고정에서 편향42행 전체의 목표각 변화 절댓값 중앙값은 누적41.378°·위치2.069°였다. 작은 지속 출력의 누적 효과를 확인하지만 동일 물리 입력이 아니므로 위치 제어의 학습 우월성은 미확정이다.','','raw0도 누적에서는 목표 유지, 위치에서는 초기 참조 목표 복귀다. B 이전 raw0 뒤 시작 자세와 동적 반응까지 같다고 취급하지 않는다. 동일 명목 목표각 비교는 첫6초 target_path 구간이며, 자유/고정에서 함께 살아 있던 표본의 제출 목표각 최대 차이는 다음과 같다.']
for mode,v in paired.items():lines.append(f"- {mode}: {v['target_path_both_alive_0_to6s_max_target_difference_rad']:.9g}rad ({v['joint_scalar_samples']}개 관절 표본).")
lines+=['','## 다음 판단','','- 작은 명령 전달·native 각도 반응이 확인돼 전면 제어 재작성의 근거는 없다. 일부 축의4~5° 추종오차는 패드 위치에 영향을 줄 수 있으므로 실제 압현 기하에서 계속 확인한다.','- 고정 B 도달을 자유 기타의 안전 복귀로 확대하지 않는다. 자유 기타의 손가락 이동 경로·엄지/손바닥 접촉·지지 분담을 분리한다.','- 누적 편향은 개선 후보지만 position을 곧바로 기본 채택하지 않는다. 동일 물리적 탐색 크기와 같은 짧은 과제의 압현·해제 학습 비교가 필요하다.','- 순힘은 접촉 상대를 인증하지 않고 외부 제출 effort0은 POSITION drive 토크0이 아니다. body_state는env0만 있어 다른행의 충돌 원인을 몸체 영상 없이 확정하지 않는다.','','[자유 상세](RESULTS.md) · [고정 상세](fixed/RESULTS.md) · [비교 수치](analysis.free_fixed.json)','','![자유·고정 비교](analysis.free_fixed.png)']
(root/'FREE_FIXED_COMPARISON.md').write_text('\n'.join(lines)+'\n')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','axes.unicode_minus':False})
fig,axes=plt.subplots(1,3,figsize=(16,5.5));labels=['자유\n누적','자유\n위치','고정\n누적','고정\n위치'];colors=['#c05621','#dd6b20','#2b6cb0','#4299e1']
for ax,values,title,ylabel,limit in [(axes[0],[r['summary']['failed_cases'] for r in rows],'물리 실패 (원84행)','실패 행',84),(axes[1],[r['summary']['B_rows_complete'] for r in rows],'마지막 B 완전 관측 (원84행)','관측 행',84),(axes[2],[r['B_finger4_actual_rms_deg_max'] for r in rows],'관측된 손가락별4축 RMS 최대','오차(°)',6.)]:
    bars=ax.bar(labels,values,color=colors);ax.set_title(title);ax.set_ylabel(ylabel);ax.set_ylim(0,limit*1.14);ax.grid(axis='y',alpha=.2)
    for bar,value in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,value+limit*.025,f'{value:.3f}' if isinstance(value,float) else str(value),ha='center')
fig.suptitle('관절 추종과 자유 기타 이탈을 분리한 진단',fontsize=16)
fig.text(.5,.015,'B 각도 오차: 자유는 완료30/44행, 고정은 전체84행. 생존행 선택 편향으로 자세 우열을 비교하지 않음.',ha='center',fontsize=11)
fig.tight_layout(rect=[0,.06,1,.92]);fig.savefig(root/'analysis.free_fixed.png',dpi=160);plt.close(fig)
print(json.dumps(dict(sources_match=True,cases_match=True,assets_match=True,paired=paired),indent=2))
