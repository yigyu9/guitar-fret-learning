from pathlib import Path
import argparse,hashlib,json,shutil,re
from PIL import Image
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1';A=P/'artifacts_v1/final_v1';V=ROOT/'docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1';VD=V/'final_v1'
BRIEF=P/'artifact_brief_v1.json';COMP=P/'comparison_v1/report.json';SOURCE=P/'search_v2/report.json';PRESET=P/'comparison_v1/static_candidate_initial_values.json';PRESETCSV=P/'comparison_v1/static_candidate_joint_angles.csv';JOINT=P/'joint_240hz_audit_v1.json';STRIKE=P/'strike_actual_windows_v1.json'
TRIALS=[('margin_only_static','margin_only','static','native_margin_only_static_v1','analysis_margin_only_static_v1.json','visual_margin_only_static_v1'),('roll_m2_static','roll_m2','static','native_roll_m2_static_v1','analysis_roll_m2_static_v1.json','visual_roll_m2_static_v1'),('roll_p2_static','roll_p2','static','native_roll_p2_static_v1','analysis_roll_p2_static_v1.json','visual_roll_p2_static_v1'),('torso_p2_static','torso_p2','static','native_torso_p2_static_v1','analysis_torso_p2_static_v1.json','visual_torso_p2_static_v1'),('margin_only_left','margin_only','left','native_margin_only_left_v1','analysis_margin_only_left_v1.json','visual_margin_only_left_v2'),('torso_p2_left','torso_p2','left','native_torso_p2_left_v1','analysis_torso_p2_left_v1.json','visual_torso_p2_left_v2'),('roll_m2_left','roll_m2','left','native_roll_m2_left_v1','analysis_roll_m2_left_v1.json','visual_roll_m2_left_v2'),('margin_only_strike','margin_only','strike','native_margin_only_strike_v1','analysis_margin_only_strike_v1.json','visual_margin_only_strike_v1'),('margin_only_static_repeat','margin_only','static_repeat','native_margin_only_static_repeat_v1','analysis_margin_only_static_repeat_v1.json','visual_margin_only_static_repeat_v1')]
PREVIEW= P/'artifacts_v1/static_preview'
PREVIEW_FILES=[PREVIEW/'README_v2.md',PREVIEW/'preview_producer_v2.py',PREVIEW/'preview_before_v2.json',PREVIEW/'preview_manifest_v2.json',PREVIEW/'preview_manifest_v1.json',PREVIEW/'static_front_2x2_v2.png']+sorted((PREVIEW/'front_frames').glob('*.png'))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def add(e,p,d=None):
 p=str(Path(p).resolve())
 if d is not None and p in e and e[p] not in (None,d):raise RuntimeError('conflicting SHA '+p)
 if d is not None:e[p]=d
 else:e.setdefault(p,None)
def add_hashes(e,obj):
 hmap=obj.get('input_sha256',{})
 if isinstance(hmap,dict):
  for p,h in hmap.items():add(e,p,h)
def source_targets(report):
 targets={}
 for x in report['annotated_frames']:targets[x['path']]=x['sha256']
 return targets
def expected_inputs():
 e={};add(e,A/'artifact_producer_v6.py')
 for f in [BRIEF,COMP,SOURCE,PRESET,PRESETCSV,JOINT,STRIKE]:add(e,f)
 for f in PREVIEW_FILES:add(e,f)
 for f in [A/'artifact_producer_v1.py',A/'artifact_producer_v2.py',A/'artifact_producer_v3.py',A/'artifact_producer_v4.py',A/'artifact_producer_v5.py']:add(e,f)
 brief=read(BRIEF);comp=read(COMP);source=read(SOURCE)
 for obj in [brief,comp,source,read(JOINT),read(STRIKE)]:add_hashes(e,obj)
 for key,label,mode,native,analysis,visual in TRIALS:
  ap=P/analysis;vr=P/visual/'report.json';np=P/native/'report.json';iv=P/native/'initial_values.json'
  for f in [ap,vr,np,iv]:add(e,f)
  for obj in [read(ap),read(vr),read(np),read(iv)]:add_hashes(e,obj)
  rd=read(vr)
  if rd.get('inputs_unchanged') is not True:raise RuntimeError('visual report input guard false '+visual)
  for view,fn in [('front','front.mp4'),('right_side','right_side.mp4'),('top','top.mp4'),('combined','front_side_top.mp4')]:
   item=rd['videos'][view];add(e,item['path'],item['sha256'])
  for snap in rd['snapshots']:add(e,snap['path'],snap['sha256'])
  for p,h in source_targets(rd).items():
   if any(f'/frames/{v}/' in p for v in ['front','right_side','top']):add(e,p,h)
 return e
def main():
 pa=argparse.ArgumentParser();pa.add_argument('--pin',action='store_true');args=pa.parse_args();A.mkdir(parents=True,exist_ok=True);VD.mkdir(parents=True,exist_ok=True)
 exp=expected_inputs()
 if args.pin:
  before={'schema':'initial_pose_search_final_artifact_before_v1','producer':{'path':str(A/'artifact_producer_v6.py'),'sha256':sha(A/'artifact_producer_v6.py')},'inputs':[{'path':p,'sha256':sha(p)} for p in sorted(exp)],'scope':'approved brief, comparison/analysis/native/visual evidence, copied visual reports media, and pre-existing static preview SHA; no later review/root docs'}
  (A/'artifact_before_v6.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n');print('pinned',len(exp));return
 before=read(A/'artifact_before_v6.json');pins={x['path']:x['sha256'] for x in before['inputs']}
 if before['producer']['path']!=str(A/'artifact_producer_v6.py') or before['producer']['sha256']!=sha(A/'artifact_producer_v6.py'):raise RuntimeError('producer SHA mismatch')
 if set(pins)!=set(exp):raise RuntimeError('input set changed')
 for p,h in pins.items():
  if sha(p)!=h:raise RuntimeError('input changed after pin '+p)
 brief=read(BRIEF);comp=read(COMP);visual_rows={Path(x['report']).parent.name:x for x in brief['visuals']}
 comp_trials={(x['label'],x['mode']):x for x in comp['trials']}
 copyrows=[];imagerows=[];case_data=[]
 for case,label,mode,native,analysis,visual in TRIALS:
  t=comp_trials[(label,mode)];rp=read(P/visual/'report.json');vrow=next(x for x in brief['visuals'] if x['report']==str(P/visual/'report.json'))
  nreport=read(P/native/'report.json');ad=read(P/analysis)['measured'];
  if bool(nreport['completed'])!=bool(t['completed']) or not rp['inputs_unchanged']:raise RuntimeError('trial/report mismatch '+case)
  if int(rp['frame_count_per_view'])!=int(vrow['frame_count']):raise RuntimeError('frame count mismatch '+case)
  vdir=VD/case;vdir.mkdir(parents=True,exist_ok=True)
  for view,filename in [('front','front.mp4'),('right_side','right_side.mp4'),('top','top.mp4'),('combined','front_side_top.mp4')]:
   item=rp['videos'][view];src=Path(item['path']);dst=vdir/filename;want=item['sha256']
   if sha(src)!=want:raise RuntimeError('video source SHA mismatch '+case+'/'+filename)
   shutil.copy2(src,dst)
   if sha(dst)!=want:raise RuntimeError('video copy SHA mismatch '+case+'/'+filename)
   stream=item['stream'];copyrows.append({'case':case,'view':view,'source':str(src),'copy':str(dst),'sha256':want,'frames':int(stream['nb_read_frames']),'duration_s':float(stream['duration']),'width':int(stream['width']),'height':int(stream['height'])})
  case_data.append({'case':case,'label':label,'mode':mode,'native':native,'analysis':analysis,'visual':visual,'summary':t,'analysis_data':ad,'report':rp})
 # Select only requested snapshots: initial three views, four completed static comparison frames, one LH failure, one strike end.
 def copy_frame(case,visual,src,rel,expected_sha):
  src=Path(src);dst=A/'images'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  if sha(src)!=expected_sha:raise RuntimeError('image source SHA mismatch '+str(src))
  shutil.copy2(src,dst)
  if sha(dst)!=expected_sha:raise RuntimeError('image copy mismatch '+str(dst))
  with Image.open(dst) as im:w,h=im.size
  imagerows.append({'kind':case,'visual':visual,'source':str(src),'copy':str(dst),'sha256':expected_sha,'width':w,'height':h})
  return dst
 # t0 front/right/top from the candidate's native margin_only static recording.
 base_report=read(P/'visual_margin_only_static_v1/report.json');base_frames=source_targets(base_report)
 for view in ['front','right_side','top']:
  p=P/'visual_margin_only_static_v1/frames'/view/'00000.png';copy_frame('initial_'+view,'visual_margin_only_static_v1',p,Path('initial_views')/(view+'.png'),base_frames[str(p)])
 for label,visual in [('margin_only','visual_margin_only_static_v1'),('roll_m2','visual_roll_m2_static_v1'),('roll_p2','visual_roll_p2_static_v1'),('torso_p2','visual_torso_p2_static_v1')]:
  r=read(P/visual/'report.json');s=next(x for x in r['snapshots'] if float(x['time_s'])==5.0)
  copy_frame('static_final_'+label,visual,s['path'],Path('static_comparison')/(label+'_t5_three_views.png'),s['sha256'])
 lr=read(P/'visual_margin_only_left_v2/report.json');ls=lr['snapshots'][-1]
 copy_frame('LH_failure_last_camera','visual_margin_only_left_v2',ls['path'],Path('left_failure')/'margin_only_left_last_camera.png',ls['sha256'])
 sr=read(P/'visual_margin_only_strike_v1/report.json');ss=next(x for x in sr['snapshots'] if float(x['time_s'])==5.0)
 copy_frame('strike_final','visual_margin_only_strike_v1',ss['path'],Path('strike')/'margin_only_strike_t5.png',ss['sha256'])
 # Initial pose/body values from pinned static candidate preset; show the principal torso scalar targets.
 preset=read(PRESET);names=preset['joint_names'];target=dict(zip(names,preset['target81_rad']));actual=dict(zip(names,preset['native_initial_actual81_rad']))
 body_names=[f'{part}_{axis}' for part in ['Torso','Spine','Chest','Neck','Head'] for axis in 'xyz']
 body_table='\n'.join(f'| {n} | {target[n]:.6f} | {actual[n]:.6f} |' for n in body_names)
 # Tables from comparison report and actual visual reports.
 trial_table=[]
 for d in case_data:
  t=d['summary'];c=t['contacts'];v=d['report'];m=d['analysis_data'];ph=v['physics_end_s'];cam=v['last_camera_time_s'];fr=v['frame_count_per_view'];dur=v['videos']['combined']['stream']['duration']
  table_label=f"{d['label']} · {d['mode']}"
  status='완료' if t['completed'] else '보호 중단'
  trial_table.append(f"| {table_label} | {status} · {ph:.3f}s | {t['max_BB_mm']:.3f}mm / {t['max_SO3_deg']:.3f}° | LH 무접촉 {c['all_left_arm_hand_contact_free_samples']}/{c['samples']} | RH 손목·손 {c['right_wrist_hand_contact_samples']} | 카메라 {cam:.3f}s · {fr}f · {dur}s |")
 # Build document with direct evidence links and factual caveats.
 root=Path('/home/ajou/yigyu/3');
 q=lambda p:f'[{Path(p).name}]({Path(p)})'
 static_images='\n\n'.join(f'![{label} 정적 5초 끝 시점]({A/"images"/"static_comparison"/(label+"_t5_three_views.png")})' for label in ['margin_only','roll_m2','roll_p2','torso_p2'])
 readme=f'''# 초기 자세 후보 탐색 — 9회 native 결과

 ## 요약

 `margin_only`는 현재 정적/타현 후속 시험용 **임시 후보**다. 전체 왼손 task의 적격 후보는 0개이며, 전역 기본값은 바꾸지 않았다. 네 정적 조건은 5초 관측을 완료했지만 전 구간에서 왼팔·손이 분리된 조건은 아니다. 왼손 task 세 번은 모두 기타/actor-root 안전 한계로 보호 중단됐다. 따라서 현재 자료로 완전한 왼손 운지·양손 연주·수동 평형을 선언할 수 없다.

 총 9회는 네 정적 후보(`margin_only`, `roll_m2`, `roll_p2`, `torso_p2`), 세 왼손 16초 task, 한 EW6 스크립트 타현, 그리고 `margin_only` 정적 exact repeat다. source 검사에서 7개 제안 중 5개가 다음 단계 후보로 적격이었지만, 이는 source analytic 검사이며 cooked 연속 충돌 인증이 아니다. 4개 정적 조건만 실제 native 비교에 포함됐고 `roll_m2_torso_p2`는 이번 9회 native 시험에 없었다.

 ## 9회 결과

 | 조건·모드 | 실제 진행 | 기타 BB 최대 이동 / 회전 | 왼팔·손 무접촉 | 오른손목·손 접촉 | 카메라 끝·영상 |
 |---|---|---|---|---|---|
 {chr(10).join(trial_table)}

 완료된 5초 영상은 모두 151프레임·30fps·5.0333초 MP4다. 물리 구간은 5.000초이고 추가 시점 표본은 영상 격자에 맞춘 끝 프레임이다. 세 왼손 실패 영상은 각각 299프레임/9.966667초, 193프레임/6.433333초, 301프레임/10.033333초다. 실제 물리 종료와 카메라 마지막 시각, MP4 재생 길이는 서로 다른 값이므로 각 조건별 표를 함께 본다.

 ### 정적 비교 이미지

 아래 네 이미지는 각각 실제 native annotated 전면·옆면·위 3-up의 5초 snapshot이다. 각 source PNG를 바이트 그대로 복사했다.

 {static_images}

 초기 상태 3시점은 `margin_only` 정적 실행의 t=0 front/right/top native annotated frames다: [전면]({A/'images/initial_views/front.png'}) · [오른쪽 옆면]({A/'images/initial_views/right_side.png'}) · [위]({A/'images/initial_views/top.png'}).

 ## 왼손 보호 중단과 접촉 해석

 세 왼손 실행 모두 actor-root 변위가 200 mm 안전 한계를 넘어 보호 중단됐다. 기타 BB 중심 이동은 actor-root 변위와 다른 기준점이다. 회전은 각각 29.122°, 28.493°, 30.141°로 35° 회전 한계보다 낮았다. 오류 로그 문구는 `guitar safety displacement`지만 결과집계의 보호 조건은 actor-root 병진이다.

 - `margin_only` 왼손: 물리 종료 9.966667 s, 마지막 카메라 9.933333 s(차이 0.033333 s), 299프레임·9.966667 s. actor-root 최대 205.923 mm, BB 중심 112.825 mm / 29.122°. A hold 3–4.5 s에서 엄지+다른 손가락 양의 raw lambda가 360/360표본이었다. 6–7 s A open에서는 LH 접촉 없음 240/240이었지만 RH 접촉이 97/240 있었다. 7–8.5 s B로 이동할 때 LH는 360/360 무접촉이었으나 RH:middle3 접촉도 360/360이었다. B hold/release 완료가 아니며 두 손이 동시에 독립 접촉으로 분리된 증거가 아니다.
 - `torso_p2` 왼손: 6.433333 s 보호 중단, 카메라 6.400000 s(0.033333 s 차이), 193프레임·6.433333 s. actor-root 최대 203.210 mm, BB 중심 62.826 mm / 28.493°. A open 단계 6.000–6.433 s에서 104 physics ticks만 실행했고 B에 도달하지 않았다.
 - `roll_m2` 왼손: 10.016667 s 보호 중단, 카메라 10.000000 s(0.016667 s 차이), 301프레임·10.033333 s. actor-root 최대 210.964 mm, BB 중심 116.170 mm / 30.141°. B close에 들어갔지만 holdB와 releaseB는 완료하지 않았다.

 대표 실패의 마지막 카메라 화면은 종료 전 0.033333초의 관측 프레임이며 평형 시점이 아니다.

 ![margin_only 왼손 task 보호 중단 직전 native 3-up]({A/'images/left_failure/margin_only_left_last_camera.png'})

 ## 스크립트 타현

 `margin_only` 타현 trial은 5초 완료했으며 기타 BB 최대 5.116316 mm / 2.203204°, RH 손목·손 접촉 0, LH raw contact query는 863/1200표본이었다. 이 시험은 EW6 팔꿈치·손목 6-DOF IK 스크립트이며 checkpoint 연결은 OFF다. 명령된 가상피크 검출 실제 창은 down 3.20–3.55 s와 up 3.75–4.45 s이며 원본 detector 순서는 하향 6→5→4→3→2→1, 상향 1→2→3→4→5→6이다. legacy 상향 집계의 3.95 s cutoff는 원자료에서 보존했고 상향 뒤쪽 일부가 누락된다. 이것은 곡 학습/체크포인트 음악 수행 성공이 아니다.

 ![EW6 스크립트 타현 5초 끝 native 3-up]({A/'images/strike/margin_only_strike_t5.png'})

 ## 후보 초기값과 범위

 임시 후보의 기타 BB 중심 world 위치는 `[{preset['guitar_body_BB_center_W_m'][0]:.6f}, {preset['guitar_body_BB_center_W_m'][1]:.6f}, {preset['guitar_body_BB_center_W_m'][2]:.6f}] m`, 기타 actor-root world 위치는 `[{preset['guitar_actor_root_W_m'][0]:.6f}, {preset['guitar_actor_root_W_m'][1]:.6f}, {preset['guitar_actor_root_W_m'][2]:.6f}] m`, 기타 쿼터니언 xyzw는 `{', '.join(f'{x:.6f}' for x in preset['guitar_quaternion_xyzw'])}`다. root·하체 fixed, strap enabled=`{preset['strap_enabled']}`. 주요 몸통 DOF scalar 값은 초기 목표 및 native actual이다. suffix는 native DOF 축 이름이며 world rotation axis가 아니다.

 | DOF | 목표 (rad) | 초기 실제 (rad) |
 |---|---:|---:|
 {body_table}

 전체 [81개 관절각 초기값 JSON]({PRESET}) · [관절각 CSV]({PRESETCSV}) · [native initial values]({P/'native_margin_only_static_v1/initial_values.json'}).

 source proxy 검사와 native 관측은 구분한다. source report의 analytic capsule/형상 검사는 이산 초기 자세 source 모델 검사이며 PhysX cooked 형상의 연속 clearance나 움직이는 동안의 비관통 인증이 아니다. 아래 PNG/영상과 접촉 수는 native visual report의 실제 annotated frames/MP4 및 native query 집계다.

 ## 공통 조건과 한계

 아홉 실행 모두 자유 기타, strap OFF, root·하체 고정, self-collision ON, 유한한 active human control이다. 기타 고정/부착, 기타 힘, 매 프레임 상태 덮어쓰기는 사용하지 않았다. contact overlay는 고정 반경·X-ray 표시다. 채운 원은 양의 raw lambda, 빈 원은 lambda=0이며 힘(N)·압력·접촉 면적이나 marker 크기 단위가 아니다. 초록/분홍 손 재질은 접촉 색 범례가 아니다. 상체 제어가 남아 있어 관측된 지지는 수동 평형을 뜻하지 않는다.

 완료 정적 조건들의 LH free 표본은 각각 418/1200, 46/1200, 93/1200, 113/1200이고 RH 손목·손 접촉은 0이다. 이 표본 비율은 full-trial independent-support pass가 아니다. 세 LH trial 전체 기준 LH free 1315/2392, 468/1544, 1132/2404이며 RH hand contacts는 각각 798, 18, 916이다. Exact repeat는 initial values, state trace, actual contacts, final efforts, final state 5개 파일 SHA가 정적 실행과 같았다.

 ## 원자료·영상

 [결과 안내]({P/'README.md'}) · [변경 파일 색인]({P/'changed_files_v1.md'}).\n\n[36개 MP4 전체 index]({V/'README_final_v1.md'}) · [승인된 9시험 brief]({BRIEF}) · [comparison report]({COMP}) · [native/source proposal report]({SOURCE}) · [240 Hz joint audit]({JOINT}) · [실제 EW6 windows]({STRIKE}) · [copy manifest]({A/'artifact_manifest_v1.json'}).

 이 문서와 영상 색인은 서로 연결된 동일 버전이다. 복사된 PNG/MP4는 source visual report SHA와 일치하며 재인코딩하지 않았다.
 '''
 (A/'README_final_v1.md').write_text(readme,encoding='utf-8')
 # Build video index: all four views for all nine cases.
 view_names=[('front','전면'),('right_side','오른쪽 옆면'),('top','위'),('combined','전면·옆면·위 합본')]
 idx=['# 초기 자세 탐색 — 전체 native 영상 색인','',f'조건별 분석은 [{A/"README_final_v1.md"}]({A/"README_final_v1.md"})에서 본다. 각 영상은 visual report의 source MP4를 바이트 그대로 복사한 파일이다. 5초 completed runs는 151 frame·5.0333 s, 세 보호 중단은 각각 299/193/301 frame이다. MP4 재생 길이와 마지막 camera sample은 각 캡션에 분리해 표시한다.','']
 for d in case_data:
  case=d['case'];label=d['label'];mode=d['mode'];rp=d['report'];idx += [f'## {label} · {mode} · physics {rp["physics_end_s"]:.6f}s / camera {rp["last_camera_time_s"]:.6f}s · {rp["frame_count_per_view"]} frames','']
  for v,nm in view_names:
   fn={'front':'front.mp4','right_side':'right_side.mp4','top':'top.mp4','combined':'front_side_top.mp4'}[v]
   item=next(x for x in copyrows if x['case']==case and x['view']==v)
   idx += [f'### {nm} · playback {item["duration_s"]:.6f}s','',f'![{label} {mode} — {nm}]({item["copy"]})','']
 idx += [f'요약은 [{A/"README_final_v1.md"}]({A/"README_final_v1.md"})와 연결된다.','']
 (V/'README_final_v1.md').write_text('\n'.join(idx),encoding='utf-8')
 # Validate all source pins, all media/images, and absolute markdown targets.
 for p,h in pins.items():
  if sha(p)!=h:raise RuntimeError('input changed during production '+p)
 for row in copyrows:
  if sha(row['copy'])!=row['sha256']:raise RuntimeError('final video mismatch '+row['copy'])
 for row in imagerows:
  if sha(row['copy'])!=row['sha256']:raise RuntimeError('final image mismatch '+row['copy'])
 for doc in [A/'README_final_v1.md',V/'README_final_v1.md']:
  for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
   if target.endswith('artifact_manifest_v1.json'):continue
   if not Path(target).exists():raise RuntimeError('broken link '+target)
 if str(V/'README_final_v1.md') not in (A/'README_final_v1.md').read_text() or str(A/'README_final_v1.md') not in (V/'README_final_v1.md').read_text():raise RuntimeError('pair mismatch')
 outputs=[A/'README_final_v1.md',V/'README_final_v1.md']+ [Path(x['copy']) for x in copyrows]+[Path(x['copy']) for x in imagerows]
 manifest={'schema':'initial_pose_search_artifact_manifest_v1','producer':{'path':str(A/'artifact_producer_v6.py'),'sha256':sha(A/'artifact_producer_v6.py')},'before':str(A/'artifact_before_v6.json'),'before_sha256':sha(A/'artifact_before_v6.json'),'input_count':len(pins),'inputs_unchanged':True,'videos_total':len(copyrows),'all_36_video_hashes_match_visual_reports':True,'snapshots_total':len(imagerows),'all_snapshot_hashes_match_visual_reports':True,'all_markdown_links_exist':True,'summary_index_pair_valid':True,'videos':copyrows,'images':imagerows,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
 (A/'artifact_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 # Manifest link is now created; check all targets one final time.
 for doc in [A/'README_final_v1.md',V/'README_final_v1.md']:
  for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
   if not Path(target).exists():raise RuntimeError('final link missing '+target)
 print(json.dumps({'inputs':len(pins),'videos':len(copyrows),'images':len(imagerows),'links_ok':True,'pair_ok':True}))

if __name__=='__main__':main()
