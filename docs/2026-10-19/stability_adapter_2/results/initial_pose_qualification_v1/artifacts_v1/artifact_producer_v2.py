from __future__ import annotations
import csv, hashlib, json, shutil, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1'
ART=P/'artifacts_v1';V=ROOT/'docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1'
BRIEF=P/'approved_artifact_brief_v1.md';SUMMARY=P/'qualification_summary_v1.json'
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CASES=[
 {'key':'baseline','label':'기준 자세','native':'native_baseline_v2','visual':'visual_baseline_v1','analysis':'analysis_baseline_v1.json'},
 {'key':'static','label':'정적 분리','native':'native_static_v3','visual':'visual_static_v1','analysis':'analysis_static_v1.json'},
 {'key':'strike','label':'EW6 타현','native':'native_strike_v2','visual':'visual_strike_v1','analysis':'analysis_strike_v1.json'},
 {'key':'left_cycle','label':'왼손 사이클 (보호 중단)','native':'native_left_cycle_v2','visual':'visual_left_cycle_v1','analysis':'analysis_left_cycle_v1.json'},
 {'key':'z_plus3mm','label':'초기 G world Z +3 mm','native':'native_z_plus3mm_v2','visual':'visual_z_plus3mm_v1','analysis':'analysis_z_plus3mm_v1.json'},
]
VIEWS=[('front','전면'),('right_side','오른쪽 옆면'),('top','위'),('combined','전면·옆면·위 합본')]

def sha(path:Path)->str:
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def read(path:Path):return json.loads(Path(path).read_text())
def sources():
 expected={}
 def add(path,hashval=None):
  path=str(Path(path).resolve())
  if hashval is not None:
   if path in expected and expected[path] is not None and expected[path]!=hashval:raise SystemExit(f'conflicting source hashes for {path}')
   expected[path]=hashval
  else:expected.setdefault(path,None)
 direct=[BRIEF,SUMMARY,P/'static_reproduction_v1.json',P/'strike_actual_windows_v1.json',P/'initial_arm_limit_margins_v1.json',
         P/'visual_baseline_v1/report.json',P/'visual_static_v1/report.json',P/'visual_strike_v1/report.json',P/'visual_left_cycle_v1/report.json',P/'visual_z_plus3mm_v1/report.json',
         P/'visual_baseline_v1/inputs_before.json',P/'visual_static_v1/inputs_before.json',P/'visual_strike_v1/inputs_before.json',P/'visual_left_cycle_v1/inputs_before.json',P/'visual_z_plus3mm_v1/inputs_before.json',FONT]
 direct += [P/c['analysis'] for c in CASES]
 for path in direct:add(path)
 summary=read(SUMMARY)
 for path,digest in summary.get('input_sha256',{}).items():add(Path(path),digest)
 for c in CASES:
  analysis=read(P/c['analysis'])
  for path,digest in analysis.get('input_sha256',{}).items():add(Path(path),digest)
  report=read(P/c['visual']/ 'report.json')
  for path,digest in report.get('input_sha256',{}).items():add(Path(path),digest)
  for view,src_name in [('front','front.mp4'),('right_side','right_side.mp4'),('top','top.mp4'),('combined','front_side_top.mp4')]:
   item=report['videos'][view];add(P/c['visual']/src_name,item['sha256'])
  for snap in report['snapshots']:add(Path(snap['path']),snap['sha256'])
 return expected

def metric(c,summary):
 row=next(x for x in summary['cases'] if x['case']==c['key'])
 return row

def write_docs(summary):
 labels={c['key']:c['label'] for c in CASES}
 rows=[];special=[]
 for c in CASES:
  report=read(P/c['visual']/'report.json');sums=read(P/c['analysis'])['measured'];info=metric(c,summary)
  snaps=report['snapshots'];first=snaps[0];last=snaps[-1]
  initial_dst=ART/c['key']/Path(first['path']).name
  final_dst=ART/c['key']/Path(last['path']).name
  initial_link=f'[{first["time_s"]:g}초 PNG]({initial_dst})';final_link=f'[{last["time_s"]:g}초 PNG]({final_dst})'
  duration=f'{info["duration_s"]:.3f} s'
  status='완료' if info['native_completed'] else '보호 중단'
  left=f'{info["left_free_samples"]}/{info["contact_samples"]} 표본 무접촉'
  if c['key']=='strike':left+='; 접촉 41/1,200, paired thumb+other 0'
  if c['key']=='left_cycle':left+='; B 도달 전 actor-root 한계 초과'
  rows.append(f'| {c["label"]} | {c["native"]} | {duration} · {status} | {info["maximum_BB_mm"]:.3f} mm | {info["maximum_SO3_deg"]:.3f}° | {left} | {initial_link} → {final_link} |')
  for snap in snaps:
   t=snap['time_s'];name=Path(snap['path']).name;dst=ART/c['key']/name
   if c['key']=='left_cycle' and t in (3.5,5.333333333333333,6.5,7.266666666666667):
    role={3.5:'A 잡기 유지',5.333333333333333:'A 해제 진행 중',6.5:'A 분리 유지',7.266666666666667:'중단 직전 마지막 카메라 프레임'}[t]
    special.append((c['key'],f'{t:.4g}초 · {role}',dst))
 table='\n'.join(rows)
 plot=ART/'maxima_comparison_v1.png'
 fig,axs=plt.subplots(1,2,figsize=(12,4.8))
 colors=['#0072B2','#009E73','#D55E00','#CC79A7','#56B4E9']
 x=list(range(len(CASES)));labelsx=[c['label'] for c in CASES]
 bb=[metric(c,summary)['maximum_BB_mm'] for c in CASES]
 so3=[metric(c,summary)['maximum_SO3_deg'] for c in CASES]
 for ax,values,title,ylabel in [(axs[0],bb,'최대 기타 BB 중심 변위','최대 변위 (mm)'),(axs[1],so3,'최대 기타 SO(3) 회전','최대 회전 (deg)')]:
  bars=ax.bar(x,values,color=colors,edgecolor='black',linewidth=.4)
  bars[3].set_hatch('///');bars[3].set_edgecolor('#7A1F5C')
  ax.set_xticks(x,labelsx,rotation=25,ha='right');ax.set_title(title);ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.25);ax.set_axisbelow(True)
  for i,(bar,val) in enumerate(zip(bars,values)):
   suffix='*' if i==3 else ''
   ax.text(bar.get_x()+bar.get_width()/2,bar.get_height(),f'{val:.3f}{suffix}',ha='center',va='bottom',fontsize=8)
 fig.suptitle('관측 기간 내 최대 변화 — 왼쪽/오른쪽 축은 서로 다른 물리량',fontsize=11)
 fig.tight_layout();fig.savefig(plot,dpi=180);plt.close(fig)
 links=[]
 for key,title,dst in special:
  links.append(f'![{title}]({dst})')
 left_images='\n\n'.join(links)
 summarydoc=f'''# 초기 자세 적격성 비교

정지 지지 초기 후보는 유망하지만, 완전한 양손 연주 reset으로 채택하지 않는다. 먼저 왼손 해제 동작과 관절 움직임 여유를 해결·검증해야 한다. 기존 기본값은 변경하지 않았다.

| 조건 | 실행 | 실제 완료 구간 | 최대 BB 중심 변화 | 최대 SO(3) 회전 | 왼팔·손 접촉 | 초기·마지막 3-up |
|---|---|---:|---:|---:|---|---|
{table}

왼손 사이클은 16초 의도에서 7.283333초에 보호 중단됐다. actor-root 이동은 0.203189 m로 0.20 m 한계를 넘었고, 기타 BB 중심 변화는 115.508 mm, 회전은 30.527°였다. **회전 35° 중단은 아니다.** B 지점에 도달하지 않았으며, 마지막 카메라 프레임은 7.266667초로 물리 종료보다 1/60초 앞선다. MP4는 219프레임/30 fps, 표시 7.3초이며 마지막 문구는 중단 직전 장면이다. 이를 정지 평형이나 16초 성공으로 읽지 않는다.

Strike는 5초 실행에서 EW6 타현 목표만 변경하고 다른 75개 목표는 유지했다(실제 상태는 움직일 수 있음). LH brief contact는 41/1,200 표본, 오른손목·손 접촉은 0이었다. V7 실제 타현 창의 raw detector에서는 6→1 하향과 1→6 상향 통과를 확인했다. legacy 상향 cutoff 집계는 보존하고 정정된 창은 [strike actual windows]({P/'strike_actual_windows_v1.json'})에서 확인한다. 학습된 곡 연주 성공을 뜻하지 않는다.

![조건별 최대 기타 BB 중심 변화와 SO(3) 회전; 별도 단위 축이며 *는 불완전 실행의 관측 구간 최대값]({plot})

아래 두 native annotated 영상은 대표적인 정적 분리 결과와 보호 중단 결과를 본문에서 바로 보여준다.

## 정적 분리 실행

![native_static_v3 세 시야 annotated 영상]({V/'static/front_side_top.mp4'})

## 왼손 사이클 보호 중단

![native_left_cycle_v2 세 시야 annotated 영상, 7.3초 부분 영상]({V/'left_cycle/front_side_top.mp4'})

## 왼손 사이클 주요 시점

마지막은 peak나 평형 시점이 아니라 중단보다 1/60초 앞선 마지막 카메라 관찰이다.

{left_images}

## 조건·해석 범위

기준 near 10초는 최대 2.811 mm/0.693°였으나 LH arm/hand 접촉이 2,255/2,400 표본이라 독립 지지 비교가 아니다. Static v3는 2.719 mm/0.826°, 왼팔·손 무접촉 2,400/2,400, 오른손목·손 접촉 0이며 마지막 2초 변화는 0.01591 mm/0.006185°다. `native_static_v2`의 전역 guard는 실패했다. v3만 guard 통과 및 [5개 raw 결과 exact 재현]({P/'static_reproduction_v1.json'})이 확인됐다.

Z+3 mm 조건은 reset 시 support motor local reference를 다시 계산했다. 고정 anchor에 대한 외란 복원력이나 강건성 실험으로 보지 않는다. 초기 scalar 한계 여유는 L_Wrist_y 0°, R_Thorax_y 약 0.000046°, L_Thorax_z 0.0012°다. 이는 모델 scalar bound이며 해부학적 world angle/인증이 아니다. 보호 중단 실행의 실제 joint bound overshoot 최대는 0.19815°이며 목표는 모델 한계와 변화율 안이었다. 상속된 near/axilla 호환 metadata는 새 접촉 인증이 아니다. LH는 시작 시 분리·후퇴하며 고정 palm 접촉을 요구하지 않는다.

다섯 실행 모두 자유 기타, strap OFF, 인위적 기타 힘 없음, root·하체 고정, self-collision ON과 유한한 active human support다. 이 결과는 passive equilibrium, force closure, 강건성, checkpoint 또는 music-ready success를 증명하지 않는다.

## 시각 자료와 원자료

기본 전면·옆면·위 순서의 세 view이며 조건별 개별 영상 3개와 합본 1개는 [전체 video index]({V/'README.md'})에 있다. 3-up PNG와 MP4는 각 visual report의 해시와 대조해 바이트 보존 복사했다. 최대 변위와 최대 회전은 서로 다른 시점일 수 있다. [qualification summary]({P/'qualification_summary_v1.json'}) · [limit margins]({P/'initial_arm_limit_margins_v1.json'}) · [copy manifest]({ART/'copy_manifest_v1.json'}).
'''
 (ART/'README.md').write_text(summarydoc,encoding='utf-8')
 # Video index links/embeds all 20 preserved video files.
 sections=['# 초기 자세 적격성 — annotated video index','',f'조건 비교와 해석 한계는 [{ART}/README.md]({ART}/README.md)에 있다. 각 source MP4는 재인코딩 없이 바이트 보존 복사했다. front/right_side/top과 세 시야 합본을 조건별로 제공한다. 실패한 왼손 사이클은 7.3초 부분 영상이며 B에 도달하지 않았다.','']
 for c in CASES:
  sections += [f'## {c["label"]} · {c["native"]}','']
  for view,label in VIEWS:
   dst=V/c['key']/({'front':'front.mp4','right_side':'right_side.mp4','top':'top.mp4','combined':'front_side_top.mp4'}[view])
   sections += [f'### {label}','',f'![{c["label"]} — {label}]({dst})','']
 (V/'README.md').write_text('\n'.join(sections),encoding='utf-8')

def main():
 ART.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
 before=read(ART/'artifact_before_v2.json'); expected={x['path']:x['sha256'] for x in before['inputs']}
 if before['producer']['path']!=str(ART/'artifact_producer_v2.py') or before['producer']['sha256']!=sha(ART/'artifact_producer_v2.py'):raise SystemExit('producer changed after pre-pin')
 if set(expected)!=set(sources()):raise SystemExit('input set changed since pin')
 mismatches=[p for p,h in expected.items() if sha(Path(p))!=h]
 if mismatches:raise SystemExit(f'pre-pinned input mismatch: {mismatches[:10]}')
 summary=read(SUMMARY);copyrows=[]
 if len(summary['cases'])!=5:raise SystemExit('expected five final cases')
 for c in CASES:
  visual=read(P/c['visual']/'report.json'); info=metric(c,summary)
  if not visual.get('inputs_unchanged'):raise SystemExit(f'visual inputs not unchanged: {c["key"]}')
  vdir=V/c['key'];adir=ART/c['key'];vdir.mkdir(parents=True,exist_ok=True);adir.mkdir(parents=True,exist_ok=True)
  for view,filename,key in [('front','front.mp4','front'),('right_side','right_side.mp4','right_side'),('top','top.mp4','top'),('combined','front_side_top.mp4','combined')]:
   src=P/c['visual']/filename;dst=vdir/filename;want=visual['videos'][key]['sha256']
   if sha(src)!=want:raise SystemExit(f'visual report video hash mismatch: {c["key"]}/{filename}')
   shutil.copy2(src,dst)
   if sha(dst)!=want:raise SystemExit(f'video copy hash mismatch: {c["key"]}/{filename}')
   copyrows.append({'kind':'annotated_video','case':c['key'],'view':key,'source':str(src),'copy':str(dst),'sha256':want})
  for snap in visual['snapshots']:
   src=Path(snap['path']);dst=adir/src.name;want=snap['sha256']
   if sha(src)!=want:raise SystemExit(f'snapshot hash mismatch: {c["key"]}/{src.name}')
   shutil.copy2(src,dst)
   if sha(dst)!=want:raise SystemExit(f'snapshot copy mismatch: {c["key"]}/{src.name}')
   copyrows.append({'kind':'annotated_3up_snapshot','case':c['key'],'time_s':snap['time_s'],'source':str(src),'copy':str(dst),'sha256':want})
  report=read(P/c['native']/'report.json')
  if bool(report['completed'])!=bool(info['native_completed']):raise SystemExit(f'native completion mismatch: {c["key"]}')
 write_docs(summary)
 # Final source hashes must still match; check copy bytes against already pinned report source hashes.
 after={p:sha(Path(p)) for p in expected}
 bad=[p for p,h in expected.items() if after[p]!=h]
 if bad:raise SystemExit(f'pinned input changed during production: {bad[:10]}')
 for r in copyrows:
  if sha(Path(r['copy']))!=r['sha256']:raise SystemExit('copy hash changed after docs generation')
 outputs=[ART/'README.md',ART/'maxima_comparison_v1.png',V/'README.md']
 for c in CASES:
  outputs+=sorted((ART/c['key']).glob('*.png'))+sorted((V/c['key']).glob('*.mp4'))
 manifest={'schema':'initial_pose_qualification_artifact_copy_manifest_v1','producer':{'path':str(ART/'artifact_producer_v2.py'),'sha256':sha(ART/'artifact_producer_v2.py')},'input_pin_before':before['inputs'],'input_pin_after':[{'path':p,'sha256':h} for p,h in after.items()],'all_input_pins_unchanged':True,'copies':copyrows,'all_copy_hashes_verified':True,'chart_units_separated':True,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
 (ART/'copy_manifest_v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'inputs':len(expected),'copies':len(copyrows),'videos':sum(x['kind']=='annotated_video' for x in copyrows),'snapshots':sum(x['kind']=='annotated_3up_snapshot' for x in copyrows),'inputs_unchanged':True,'copies_verified':True}))
if __name__=='__main__':main()
