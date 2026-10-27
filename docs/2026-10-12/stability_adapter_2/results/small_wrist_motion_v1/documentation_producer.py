from pathlib import Path
import json,hashlib,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';P=D/'results/small_wrist_motion_v1';s=P/'native';a=json.loads((P/'analysis.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();original_index=D/'VIDEO_INDEX.md';old_manifest=D/'video_collection_manifest.json';original_sha=sha(original_index);assert all(sha(r['source'])==sha(r['copy'])==r['sha256'] for r in json.loads(old_manifest.read_text())['rows']);update=[]
for view in ('hands','whole_body'):
 source=s/(view+'.mp4');target=D/'videos'/('small_wrist_motion_v1__native__'+source.name);assert not target.exists();shutil.copyfile(source,target);assert sha(source)==sha(target);update.append(dict(source=str(source),copy=str(target),sha256=sha(source),size=source.stat().st_size))
new_index=D/'VIDEO_INDEX_v2.md';assert not new_index.exists();intro='# 영상 모음 갱신 — 122개\n\n새로운 작은 왼손목 움직임의 실제0~5초·스트랩 영상2개를 추가했다. 영상은 모두 ['+str(D/'videos')+']('+str(D/'videos')+')에 있고, 기존120개 원본/모음/목록은 그대로다.\n\n'
for r in update:intro+='- ['+Path(r['copy']).name+']('+r['copy']+')\n'
intro+='\n[이번 초기값·그림·결과 설명]('+str(P/'README.md')+':1)\n\n아래는 기존120개 목록이다.\n\n';new_index.write_text(intro+original_index.read_text());assert sha(original_index)==original_sha
(D/'video_collection_update_v1.json').write_text(json.dumps(dict(previous_index_sha256=original_sha,previous_manifest_sha256=sha(old_manifest),new_index_sha256=sha(new_index),copies=update,total_count=122),indent=2)+'\n')
rows=[('전체 최대 초기 위치오차(mm)','max_initial_position_error_mm'),('전체 최대 초기 회전오차(°)','max_initial_rotation_error_deg'),('5초 종료 초기 위치오차(mm)','end_initial_position_error_mm'),('5초 종료 초기 회전오차(°)','end_initial_rotation_error_deg'),('2초 시작점 대비2~5초 최대 위치차이(mm)','max_position_change_from_2s_mm'),('2초 시작점 대비2~5초 최대 회전차이(°)','max_rotation_change_from_2s_deg')];table='| 항목 | 정지 유지 기준 | 작은 왼손목 동작 |\n|---|---:|---:|\n'
for label,key in rows:table+='| '+label+' | '+format(a['baseline'][key],'.6f')+' | '+format(a['motion_trial'][key],'.6f')+' |\n'
text='''# 작은 왼손목 움직임 중 자유 기타 유지

왼손목 목표±0.005rad/1Hz의 한 actual5초를 완료했다. 실제 움직임이 있었고2~5초 기타 변화는 최대0.481766mm/0.091929°였다. 이 한작은동작에서는 기타가 크게 이탈하지 않았다. 초기 오차를 줄이는 제어나 전반 연주 안정화는 이번에 구현하지 않았다.

## 초기값과 실행 계약

기준은 torso_hold_native_collision_v1의 body9 PD×2다. native t0의 humanoid·기타 상태, 초기81/기존81목표,PD/물리파라미터,절대LA1.1018469719600776m,초기route길이와 cable법칙을 exact 대조했다. 초기 생성 형상 admission을 통과했고, 최초4step까지 기준 state와 exact 같았다. Body9 목표 유지/루트·하체 물리 고정/자유 기타/인체 내부충돌은 그대로다.

L_Wrist_x 한목표에만0.005sin(2πt)rad를 환경 시작부터60Hz로 더했다. 나머지80 목표는 매step 기준과 exact였다. 최종 양쪽Thorax 이하66권한을1축으로 제한한 것이 아니라 첫움직임 영향만 계측한 것이다. 기준offset+움직임offset을 float64에서 합하고 모델·초기offset±0.3 경계를 검사한 뒤float32 target으로 제출했다. 실제 state/pose는 덮어쓰지 않았다.

실험 종료5초 직전 마지막 제출시각은4.983333초다. 그때의δ 약−0.000522642rad를 hold한 채5초를 마쳤다. t=5의 목표를 별도 제출하거나 추가정지 구간을 넣지 않았다. 다음2초 분석 구간은 WAIT 전제나 필수 대기상태가 아니다.

[초기값과 PD·기타p/q]('''+str(s/'initial_values.json')+''':1), [입력과 요청 파형]('''+str(s/'attempt.json')+''':1), [실제 제출 목표]('''+str(s/'controls.jsonl')+''':1), [실제 상태]('''+str(s/'states.jsonl')+''':1), [동작 계획]('''+str(A/'SMALL_WRIST_MOTION_PLAN.md')+''':1)를 따른다.

## 실제 Isaac Gym 영상과 초기·종료 이미지

![작은 왼손목 동작의 실제 손·기타·스트랩0~5초]('''+str(s/'hands.mp4')+''')

![같은 실행의 전신·스트랩0~5초]('''+str(s/'whole_body.mp4')+''')

둘다151frame/30fps·0~5초의 native 카메라 기록이며 파일 인코딩 길이는5.033333초다. 주황실선/가려진옅은점선은 실제13route passive strap의 표시다. 원nativePNG와overlayPNG를 모두 보존했다. CPU PhysX로 실행했고 기존과 같은 CUDA/context/visualgeom 경고는 로그에 보존했다. 표시geometry는 cooked충돌거리 인증이 아니다.

![실제 초기 손·기타·스트랩]('''+str(s/'frames/hands/00000.png')+''')

![실제5초 종료 손·기타·스트랩]('''+str(s/'frames/hands/00150.png')+''')

작은 움직임은 영상에서 잘 안 보일 수 있다. 아래 실제 관절각과 native palm pose를 함께 측정해 목표만 움직였던 경우와 구별했다. 이번도 실제palm–기타 양의rawλ step은0이므로 손바닥옆면 지지가 생겼다고 설명하지 않는다.

## 기준과 실제 동작 비교

'''+table+'''

![실제손목응답과초기기타오차 비교]('''+str(P/'artifacts_v2/wrist_motion_and_guitar_errors.png')+''')

위 주황선은 실제 제출한 목표δ를 deg로 표시했다. 위 파란선은 같은 시각 actual L_Wrist_x 좌표의이번−기준 차이를deg로 변환했다. 2~5초 차이에 상수·linear trend·1Hz sin/cos를 fit한 진폭은0.002564398rad(0.146929°)이고 RMS residual은2.031502e-5rad다. Scalar q의 반응이지 뼈 회전각으로 동일시하지 않는다. 아래두패널은 world초기p/q에 대한 오차의 native trace다. 음영2~5초는 평가구간이다.

같은 시각 기준 대비 실제 palm world원점 차이는최대0.495638mm, 실제palm world회전 차이는0.177237°였다. 같은시각 기타 world위치 차이는2~5초에서최대0.616547mm다. 이것은각실행의2초 시작점 대비변화0.481766mm와 다른측정이다. Actual SDK인체내부contact와palm–기타 양의rawλ step은모두0이고mask정책은유지했다. 다른finger/허벅지접촉을palm접촉으로치환하지 않는다.

최대초기위치오차는기준보다0.080379mm,회전은0.010037°커졌고종료위치는줄지만종료회전은조금커졌다. 개선만있다고설명하지 않는다. 이첫작은동작에서의유지는유망한관측이며,14mm/2.86° 또는0.48mm/.092°를사용자허용한계로확정하지 않는다. 더큰/여러joint연주동작·초기p/q복원보정은후속범위다.

## 검증과 다음 단계

원본runner를예상SHA로대조한뒤복사했고 변경은파형/검증/로그만이다. 사전300목표·나머지80·모델한계검사와 runtime12분석검사가통과했다. 실제t0/5초PNG와그림을열어확인했다. 첫그림v1의범례가마지막peak를가려원본을보존하고범례를밖으로옮긴v2를생성·재검사했다. 추가physics는없었다.

Native는실제1회/1200step,offline후처리는native0이다. 원본과이번입력SHA/PD/고정하체·root/604imageSHA/151frame/300commands를검증했다. Luna·change-reviewer호출은agent thread limit reached로실패했고root자체작성/검증으로명시한다. 독립승인으로표시하지않는다.

[새122개영상목록]('''+str(new_index)+''':1)에두영상을복사했고기존120개/원본목록은보존했다. [다음몸통9PD×2의strap−2mm계획]('''+str(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md')+''':1)은미실행이다. 같은작은동작/관절·기타초기상태에서절대LA만2mm줄여초기이탈을비교한다. 기존gain이다른strap결과를새조합의실측으로보지않는다. 이후연주target+안정화잔차의권한/우선순위와실제p/q복원성능을설계하고학습구조를정한다.
'''
(P/'README.md').write_text(text)
progress='\n\n## 작은 왼손목 움직임 — 실제5초 완료\n\n현재정지유지기준과t0/PD/LA를같게두고L_Wrist_x목표만±0.005rad·1Hz로t0부터움직였다. 한actual1200step/두151frame스트랩영상과12분석검사완료. 실제좌표응답진폭0.146929°·palmworld원점차0.495638mm이고2~5초G변화는0.481766mm/0.091929°였다. 전체최대초기오차14.132608mm/2.894328°로기준14.052228mm/2.884291°보다조금커졌다. [초기값/실제영상/그림설명]('+str(P/'README.md')+':1), [영상모음122개]('+str(new_index)+':1)에기록했다. 이작은1축시험을전반연주·초기p/q복원완료로보지않고최종66권한/자유G/몸통목표/고정하체root/passivestrap을유지한다. [다음strap−2mm비교]('+str(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md')+':1)는미실행이다. Luna/독립검수도구한도로root자체검증과구분한다.\n'
for n in ('README.md','PLAN.md'):
 with (A/n).open('a') as f:f.write(progress)
visual=D/'VISUAL_REPORT.md';assert '## 94.' not in visual.read_text();section='\n\n## 94. 작은 왼손목 움직임 중 자유 기타 유지\n\n같은초기81/G/PD/LA의actual한5초/1200step을새로진행했다. 목표L_Wrist_x만±.005rad/1Hz·60Hz이고나머지80targetexact다.\n\n![실제손목응답과기타초기오차]('+str(P/'artifacts_v2/wrist_motion_and_guitar_errors.png')+')\n\n실제좌표minusstatic의1Hz진폭은.146929°다. 2~5초G변화0.481766mm/.091929°이고전체최대초기오차14.132608mm/2.894328°다. 정지유지에서작은동작검증으로진행했으며큰/여러연주동작·초기오차복원은아직이다. Scalar관절각과actualpalmworld회전은구별한다.\n\n![이번실제Gym손·기타·스트랩0~5초]('+str(s/'hands.mp4')+')\n\n![이번실제5초종료]('+str(s/'frames/hands/00150.png')+')\n\n151frame/30fps로원nativePNG와actual13routeoverlay를보존했다. Root그림/초기·종료PNGQA완료,독립검수는도구threadlimit으로보류다. [상세결과/초기값]('+str(P/'README.md')+':1), [새122개영상모음]('+str(new_index)+':1), [다음미실행strap비교]('+str(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md')+':1)에기록한다.\n'
with visual.open('a') as f:f.write(section)
(P/'review_status.json').write_text(json.dumps(dict(independent_review_completed=False,reviewer_tool_error='agent thread limit reached',luna_tool_error='agent thread limit reached',actual_artifact_producer='root fallback'),indent=2)+'\n')
files=[(A/'run_small_wrist_recorded_diagnostic.py','def main()'),(A/'analyze_small_wrist_motion.py','def main()'),(A/'make_small_wrist_motion_artifacts.py','def main()'),(A/'make_small_wrist_motion_artifacts_v2.py','def main()'),(A/'SMALL_WRIST_MOTION_PLAN.md','# '),(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md','# '),(A/'README.md','## 작은 왼손목'),(A/'PLAN.md','## 작은 왼손목'),(P/'README.md','# '),(visual,'## 94.'),(new_index,'# ')];index='# 변경파일 절대경로와 실제줄\n\n'
for p,key in files:
 line=next(i for i,l in enumerate(p.read_text().splitlines(),1) if l.startswith(key));index+='- ['+p.name+']('+str(p)+':'+str(line)+')\n'
(P/'CHANGED_FILES.md').write_text(index);shutil.copyfile(__file__,P/'documentation_producer.py');print('documented actual5s; video collection122; VIS94')
