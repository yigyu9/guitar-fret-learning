from pathlib import Path
import json,hashlib,shutil
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';P=D/'results/body9_strap_minus2mm_v1';s=P/'native';d=json.loads((P/'analysis.json').read_text());old,new=d['summary'];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();original_index=D/'VIDEO_INDEX_v2.md';previous=sha(original_index);update=[]
for view in ('hands','whole_body'):
 source=s/(view+'.mp4');target=D/'videos'/('body9_strap_minus2mm_v1__native__'+source.name);assert not target.exists();shutil.copyfile(source,target);assert sha(source)==sha(target);update.append(dict(source=str(source),copy=str(target),sha256=sha(source),size=source.stat().st_size))
index=D/'VIDEO_INDEX_v3.md';assert not index.exists();intro='# 영상 모음 갱신 — 124개\n\n같은손목동작에서스트랩만2mm줄인실제0~5초영상2개를추가했다. 모두 ['+str(D/'videos')+']('+str(D/'videos')+')에있다. 기존122개/목록은보존한다.\n\n'
for r in update:intro+='- ['+Path(r['copy']).name+']('+r['copy']+')\n'
intro+='\n[새실험의초기값·그림·결과]('+str(P/'README.md')+':1)\n\n아래는기존122개목록이다.\n\n';index.write_text(intro+original_index.read_text());assert sha(original_index)==previous
(D/'video_collection_update_v2.json').write_text(json.dumps(dict(previous_index_sha256=previous,new_index_sha256=sha(index),copies=update,total_count=124),indent=2)+'\n')
metrics=[('최대초기위치오차(mm)','guitar','max_initial_position_error_mm'),('최대초기회전오차(°)','guitar','max_initial_rotation_error_deg'),('종료초기위치오차(mm)','guitar','end_initial_position_error_mm'),('종료초기회전오차(°)','guitar','end_initial_rotation_error_deg'),('2초기준2~5초최대위치차이(mm)','guitar','max_position_change_from_2s_mm'),('2초기준2~5초최대회전차이(°)','guitar','max_rotation_change_from_2s_deg'),('실제손목좌표1Hz진폭(°)','wrist','amplitude_deg'),('초기slack(mm)','strap','initial_slack_mm'),('첫양의법칙T step','strap','first_positive_step'),('최대법칙T(N)','strap','max_law_tension_n'),('종료법칙T(N)','strap','end_law_tension_n')];table='| 항목 | 원본LA/같은동작 | LA−2mm/같은동작 |\n|---|---:|---:|\n'
for label,group,key in metrics:table+='| '+label+' | '+format(old[group][key],'.6f')+' | '+format(new[group][key],'.6f')+' |\n'
text='''# 같은 초기 자세·손목 움직임에서 스트랩 -2mm

절대LA만2mm줄인한actual5초에서최대초기이동·회전오차와2~5초변화가모두줄었다. 원본LA의같은움직임보다나은후속비교기준으로유지한다. 전체연주·초기p/q복원보정·손바닥옆면grip완료는아직아니다.

## 초기값과 변경 범위

실제native humanoid/기타t0상태·초기81/기존81target·PD·physics·초기route길이·기타목표p/q·cablelaw·최종66명단·파형을11field로exact비교했다.1200개의제출target/갱신step/파형도기준small_wrist_motion_v1과exact였다. Body9PD×2/목표유지,root하체물리고정,자유G·selfcollision정책도같다.

Trial물리입력변경은 initial_settings.strap_rest_length_m 한필드다.1.1018469719600776→1.0998469719600776m이고길이는5초내내상수다. 각도/기타초기translation/mainoffset/PDscale은같다. 새trialpath/SHA·선언LA/closure를새proposal에명시했고원본소스/입력/계획은수정하지않았다. Freshnative초기형상admission을다시통과했다.

[새trial]('''+str(A/'trials/body9_strap_fine_v1/la_minus2mm.json')+''':1), [초기값·실제81/G p/q·PD]('''+str(s/'initial_values.json')+''':1), [선언]('''+str(P/'proposal.json')+''':1), [실행계획]('''+str(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md')+''':1), [전체실측]('''+str(P/'analysis.json')+''':1)을따른다.

## 실제 Isaac Gym 영상·초기/종료

![스트랩−2mm의실제손·기타·스트랩0~5초]('''+str(s/'hands.mp4')+''')

![동일실행의전신·스트랩0~5초]('''+str(s/'whole_body.mp4')+''')

한actual1200step/5초,카메라두개각151frame/30fps·인코딩5.033333초다. 원nativePNG와actual13routeoverlay를모두보존했다. 주황실선/가려진옅은점선은passive cable경로이며clothmesh가아니다. 기존과동일한CPU PhysX/CUDA/context/visualgeom경고를원로그에남겼다.

![실제initial 손·기타·스트랩]('''+str(s/'frames/hands/00000.png')+''')

![실제5초종료 손·기타·스트랩]('''+str(s/'frames/hands/00150.png')+''')

초기geometry는같고표시restlength만1.099847m다. Native actual p/q를고정/덮어쓰지않았다. Palm–G 양의rawλ step은이번도0이므로손바닥옆면지지를만들었다고설명하지않는다.

## 비교 수치와 그림

'''+table+'''

![동일손목움직임의기타오차와법칙장력]('''+str(P/'artifacts/guitar_errors_and_strap_tension.png')+''')

위/중간패널은원 world초기p/q에대한실측trace오차다. 아래는저장state직전제출된cable법칙T이며실제contactλ를N으로변환한값이아니다. 두길이의route position/velocity로이전state→다음step법칙T를재구성한최대오차는모두0N이다. K6000N/m·damping120Ns/m·cap300N을그대로썼고두초기법칙T는0이다.

최대위치오차는0.122052mm(약0.86%),회전은0.286663°(약9.90%)줄었다.2~5초pose범위도위치0.118278mm·회전0.021840°줄었다. 초기·종료·후반지표를혼동하지않는다. 초기에장력이생기는step은39→37로앞당겨지고peakT는24.129230→28.152161N으로늘었다. 이러한관측을단일원인/인과인증이나최종성공상한으로확대하지않는다.

실제L_Wrist_x의2~5초 qminus원본정지기준을constant/trend/sin/cos1Hz로fit한진폭은0.147836°다. 이전같은파형0.146929°와비슷하여손목동작이없어진결과가아니다. Scalar q진폭은뼈회전으로동일시하지않는다. 실제palm–기타양의rawλ/selfSDKcontact step은둘다0이고native충돌mask정책은그대로다. 다른finger/허벅지지지를palm지지로치환하지않는다.

## 검증과 다음 단위

입력생성4검사·native보고서검사·offline분석10검사,604native/overlayPNG SHA와원자료closure가통과했다. 실제그래프와native초기/종료PNG를열어대조했다. Native는1회/1200step이고입력생성/그래프는native0이다. Luna/change-reviewer는agent thread limit reached로실패해root가작성/검증했고독립승인으로표시하지않는다.

[영상모음124개]('''+str(index)+''':1)에두복사본을추가했다. 이전영상/모음/목록은같은바이트로보존했다. [다음original대비−4mm계획]('''+str(A/'BODY9_STRAP_MINUS4MM_PLAN.md')+''':1)은미실행이다. 현재−2mm를유망한동작비교기준으로두되해당길이의별도무동작정지µm범위는측정하지않았다. 초기이탈추가감소와이후실제관절로p/q오차복원·연주target+안정화보정권한설계는계속진행한다.
'''
(P/'README.md').write_text(text)
progress='\n\n## 몸통9 PD×2·같은손목동작의strap−2mm — 한5초완료\n\nLA1.1018469719600776→1.0998469719600776m만줄였고native t0/PD/1200target는exact같았다. 최대초기오차14.132608mm/2.894328°→14.010556mm/2.607665°,2~5초변화0.481766mm/.091929°→.363488mm/.070089°로줄었다. 실제손목좌표진폭.146929→.147836°,cablepeak24.129230→28.152161N과첫양의T step39→37을기록했다. Actual한1200step/두151frame스트랩영상·분석10검사완료. [초기값/영상/그림]('+str(P/'README.md')+':1), [영상모음124개]('+str(index)+':1)에남겼다. −2mm는유망한동작비교기준이며별도무동작정지는미측정이다. [다음total−4mm계획]('+str(A/'BODY9_STRAP_MINUS4MM_PLAN.md')+':1)은미실행이다. 전체66권한/몸통목표/고정root하체/자유G/passivestrap과초기p/q복원·유지/연주목표+안정화보정목적은유지한다. Luna/독립검수도구한도는root자체검증과구분한다.\n'
for name in ('README.md','PLAN.md'):
 with (A/name).open('a') as f:f.write(progress)
visual=D/'VISUAL_REPORT.md';assert '## 95.' not in visual.read_text();section='\n\n## 95. 같은초기자세·손목동작의strap−2mm\n\n새actual한5초/1200step이다. LA만2mm줄였고native t0/PD/목표파형1200개는기준과exact다.\n\n![초기오차와제출cable법칙T]('+str(P/'artifacts/guitar_errors_and_strap_tension.png')+')\n\n최대초기오차14.132608mm/2.894328°→14.010556mm/2.607665°,2~5초범위.481766mm/.091929°→.363488mm/.070089°다. 실제손목좌표진폭은.147836°로유지됐다. Peak법칙T는24.129230→28.152161N이며rawcontact force인증과구별한다.\n\n![새실제Gym손·기타·strap0~5초]('+str(s/'hands.mp4')+')\n\n![새실제5초종료]('+str(s/'frames/hands/00150.png')+')\n\n두151frame영상·원nativePNG와actual13route를보존했다. RootactualPNGQA/자료검사완료,독립검수는도구threadlimit으로보류다. [초기값/전체결과]('+str(P/'README.md')+':1), [124개영상목록]('+str(index)+':1), [다음미실행−4mm계획]('+str(A/'BODY9_STRAP_MINUS4MM_PLAN.md')+':1)에남긴다. Grip/연주/초기p/q복원완료로확대하지않고전체목표를계속진행한다.\n'
with visual.open('a') as f:f.write(section)
(P/'review_status.json').write_text(json.dumps(dict(independent_review_completed=False,reviewer_tool_error='agent thread limit reached',luna_tool_error='agent thread limit reached',actual_artifact_producer='root fallback'),indent=2)+'\n');files=[(A/'prepare_body9_strap_fine_trial.py','def main()'),(A/'analyze_body9_strap_fine.py','def main()'),(A/'make_body9_strap_fine_artifacts.py','def main()'),(A/'trials/body9_strap_fine_v1/la_minus2mm.json','{'),(A/'BODY9_STRAP_FINE_COMPARISON_PLAN.md','# '),(A/'BODY9_STRAP_MINUS4MM_PLAN.md','# '),(A/'README.md','## 몸통9 PD×2·같은손목'),(A/'PLAN.md','## 몸통9 PD×2·같은손목'),(P/'README.md','# '),(visual,'## 95.'),(index,'# ')];changed='# 변경파일의절대경로와실제줄\n\n'
for p,key in files:
 line=next(i for i,l in enumerate(p.read_text().splitlines(),1) if l.startswith(key));changed+='- ['+p.name+']('+str(p)+':'+str(line)+')\n'
changed+='\nNative runner는수정하지않고기존 run_small_wrist_recorded_diagnostic.py를그대로사용했다.\n';(P/'CHANGED_FILES.md').write_text(changed);shutil.copyfile(__file__,P/'documentation_producer.py');print('documented minus2mmactual5s; collection124; VIS95')
