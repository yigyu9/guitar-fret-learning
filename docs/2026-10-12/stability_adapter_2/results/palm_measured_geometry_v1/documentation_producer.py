import json
from pathlib import Path
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'palm_measured_geometry_v1'
def read(p):return json.loads(Path(p).read_text())
g=read(P/'analysis.json');h=read(B/'palm_single_hinge_pose_v1/analysis.json')
def link(p,line=1):return '['+p.name+']('+str(p)+':'+str(line)+')'
trial=B/'torso_hold_native_collision_v1/native'
rows5=sorted((r for r in g['rows'] if r['physics_step']==1200),key=lambda r:r['fraction'])
table=['| 팔12 기하 보정 비율 | Palm 유한 patch 거리 상한 (mm) | 대표점 오차 (mm) | 검지3–기타 증가 (mm) | 중지3–기타 증가 (mm) | Source 선별 |','|---:|---:|---:|---:|---:|---|']
for r in rows5:
 def inc(body):return max([x['increase_m']*1000 for x in r['new_or_increased_source_intersections'] if x['kind']=='human_guitar' and x['a']==body and x['b']=='guitar']+[0.])
 table.append('| '+str(r['fraction'])+' | '+format(r['palm_finite_patch_interval']['distance_m']*1000,'.9g')+' | '+format(r['palm_anchor_error_mm'],'.6f')+' | '+format(inc('LH:index3'),'.6f')+' | '+format(inc('LH:middle3'),'.6f')+' | '+('기준' if r['fraction']==0 else '거절')+' |')
hinges=['| 단일 축 body | 최대 원점 오차 (µm) | 최대 회전 오차 (µrad) | 24시점 |','|---|---:|---:|---|']
for r in h['summary']:hinges.append('| '+r['body']+' | '+format(r['max_position_error_mm']*1000,'.6f')+' | '+format(r['max_rotation_error_rad']*1e6,'.6f')+' | 통과 |')
text='''# 손바닥 단독 접근의 형상 진단과 손가락 연동 준비

손바닥 대표점을 넥 옆면에 가깝게 만드는 팔12 보정은 검지·중지의 source 형상 교차를 증가시켰다. 이 방향을 실제 PD 제어로 실행하지 않았다. 대신 엄지·검지·중지의 단일 축 6관절을 조건부로 검증하고, 팔과 손가락을 함께 조정하는 다음 계획을 남겼다.

## 실행 범위와 기준 물리 영상

이번 추가 native 초기화·physics step·물리 trial은 모두 0이다. 직전 body9 PD×2의 실제 5초 저장 자료를 읽었다. 같은 결과를 새 시뮬레이션으로 집계하지 않는다. 초기값은 '''+link(trial/'initial_values.json')+''', 입력 설정은 '''+link(trial.parent/'proposal.json')+'''에 있다. 기타 최대 이동14.052228mm/회전2.884291°이지만 실제 palm 접촉은 0인 기준 실행이다.

![분석 기준인 기존 실제 Isaac Gym 손·스트랩 0~5초]('''+str(trial/'hands.mp4')+''')

![같은 기존 실행의 전신·스트랩 0~5초]('''+str(trial/'whole_body.mp4')+''')

각 영상은 t0~5초, 151프레임/30fps로 인코딩 길이 약5.033초다. 주황 실선은 보이는 실제 passive strap 경로, 옅은 점선은 인체/기타에 가려진 경로다. 실제13개 경로점과 camera/depth로 그린 표시이며 천의 너비·처짐·충돌 mesh를 추가한 모델은 아니다. 앞으로 실제 trial에도 같은 스트랩 표시와 원본 native PNG를 저장한다.

## 1. 실제 손가락 자세를 읽은 팔12 기하 보정

저장 step0/24/120/1200(0/0.1/0.5/5초)의 actual body pose를 source mesh에 사용했다. 검증된 팔 FK의 현재각→후보각 차이만 적용하고, 손가락의 현재 palm 상대 자세는 유지했다. 기타를 해당 시점에 고정한 offline 질의다. 실제 관절/기타 state에는 쓰지 않았다.

네 시점 × 보정 비율0/1/0.5/0.25의 16배치를 조회했다. 4개의 비율0은 기준이며 신규 후보가 아니다. 12개 비영 후보 중 초기 t0의 0.25만 source 선별을 통과했고, 나머지11개는 새/증가 교차가 있었다. 모든 상향 proxy와 PD 목표 경계는 통과했지만 전체 형상 교차가 남았다. 초기 quarter 통과를 runtime 안전성으로 일반화하지 않는다.

![손바닥 거리 감소와 손가락 형상 교차 증가]('''+str(P/'artifacts_v2/palm_gap_and_finger_overlap.png')+''')

위 패널은 유한 옆면 patch와 palm source hull의 거리 witness 상한(mm), 아래는 검지3·중지3의 기타 쌍에서 새/증가로 기록된 common insphere radius 증가 중 최대값(mm)이다. 비율0을 0으로 표시한 아래 값은 baseline에 대한 증가가 없다는 뜻이며 baseline의 모든 형상이 겹침 없다는 뜻은 아니다. 선으로 연결한 것은 네 배율의 source 질의이지 실제 시간 경과가 아니다.

5초 저장 상태에서의 비교:

'''+ '\n'.join(table)+'''

비율1의 palm 상한9.89187017e-8mm는 작은 비영 값이다. 정확한 0으로 보고하지 않는다. 동시에 palm–기타 source 교차 증가0.110574mm와 검지3–fret3/중지3–fret4 교차 증가0.7mm도 기록됐다. Source 선별은 LP 부호epsilon0.1µm와 baseline 대비 radius 증가10µm를 사용했다. 이는 공식 native 관통/성공 기준이 아니다.

조회한 native filter 허용 self source 쌍에는 Chest–Thorax와 Shoulder–Elbow 같은 연결 capsule 겹침도 포함된다. 그 큰 common radius를 실제 SDK 접촉 또는 PhysX 관통 깊이로 설명하지 않는다. 다음 후보 선별에서는 기존 source audit와 같은 연결 graph 거리≤2 제외를 쓰되 원래 연결쌍 진단을 별도 보존한다. Native 내부 충돌 정책은 변경하지 않는다. 손가락–기타 교차는 이 제외로 숨기지 않는다.

원자료: '''+link(P/'analysis.json')+'''. Source LP common insphere radius는 native penetration depth·힘·해부학적 손바닥 지지 인증과 다르다.

## 2. 단일 축 손가락 6관절의 조건부 검증

엄지2/3, 검지2/3, 중지2/3의 MJCF 단일 축 관계를 4진단+20heldout 시점에 대조했다. 총24×6=144행이다. t0의 parent–child 상대 위치·회전을 한 번만 보정하고, 매 시점 actual 부모 자세와 scalar q를 입력해 child pose를 예측했다. t0 상대값을 매 시점 다시 fitting하지 않았다.

![단일 축 관절의 조건부 예측 오차]('''+str(P/'artifacts_v2/conditional_single_hinge_errors.png')+''')

왼쪽은 원점 오차 µm(mm×1000), 오른쪽은 회전 오차 µrad(rad×1e6), 로그 축이다. 기존 비교 경계100µm/1000µrad를 유지했다.

'''+ '\n'.join(hinges)+'''

전부 조건부 비교를 통과했다. 실제 부모 자세를 제공했으므로 전체 손 FK, 넓은 각도 범위, PD 반응, 접촉 또는 기타 잡기 성공을 인증한 것은 아니다. 이전 finger1 두좌표 모델의 전체손 실패는 유지한다. 원자료: '''+link(B/'palm_single_hinge_pose_v1/analysis.json')+'''.

## 3. 다음 단위와 제어권

'''+link(A/'PALM_FINGER_COUPLED_SOURCE_PLAN.md')+'''은 아직 미실행이다. 임시 진단 범위는 왼팔12+검증한 손가락6이다. 팔±0.05rad/손가락±0.10rad의 첫 source 범위와 모델/Aug19/최종 PD target 초기offset±0.3의 교집합에서 palm 옆면·thumb 후면·index/middle 전면을 함께 고려한다. 원래81관절 PD 목표+bounded residual을 유지한다. actual 각을 그대로 PD base로 치환하지 않는다.

안전한 source 방향을 확인한 뒤 적용 계약과 실제 ON 5초 시험을 진행한다. 몸통9 목표 유지/임시 gain×2, root·하체 물리 고정, 자유 기타, passive strap 및 초기 G p/q는 같다. 최종 양쪽 Thorax 이하66 제어권을 제한하지 않는다. 기타 초기 오차 복원·유지와 연주 목표+안정화 보정 관계는 계속 설계 중이며 학습은 아직 시작하지 않는다. WAIT→REACH→GRIP→TRANSPORT를 필수 전제로 두지 않는다.

## 검증·보존·담당

- [x] 16배치 source 질의, 기준0의 mesh 변화<1e-12m, 입력 SHA 불변 확인.
- [x] 144행 단일 축 조건부 비교, 입력 SHA 불변 확인.
- [x] 두 실제 PNG를 원자료와 대조했다. 첫 그림의 긴 축 제목 겹침을 실제로 발견해 원본v1을 보존하고 제목만 줄인 v2를 생성·재검사했다. 새 물리 실행은 없다.
- [x] 계획·진행 기록과 실제 줄 색인 추가.
- [ ] 독립 change-reviewer 검수: 호출이 `agent thread limit reached`로 실패했다. 독립 승인으로 표시하지 않는다.
- [ ] 다음 팔·손가락 연동 source 후보 및 실제 PD/G 복원 검증.

이번 산출물은 도구 한도로 Sol/root가 작성했다. Luna가 생성했다고 표시하지 않는다. 최종 원본 SHA/크기 보존 검사와 Python3.8 문법 검사 결과는 root 감사 파일에 남긴다. 전체 기타 안정화 성공을 선언하지 않는다.
'''
(P/'README.md').write_text(text)
phases=['palm_measured_geometry_execution_v1','palm_single_hinge_pose_v1','palm_single_hinge_pose_execution_v1','palm_measured_geometry_v1']
for name in phases:
 f=B/name
 if f!=P:(f/'README.md').write_text('# '+name+'\n\n저장된 실제 Isaac Gym 자료를 이용한 offline source/조건부 pose 분석이다. 추가 native·physics는0이며 실행 소스·입력 SHA·로그를 보존한다.\n\n상세 결과와 기존 스트랩 영상: '+link(P/'README.md')+'\n')
 (f/'review_status.json').write_text(json.dumps(dict(independent_review_completed=False,attempted_tool='collaboration.followup_task /root/contact_footprint_review',tool_error='agent thread limit reached',actual_artifact_producer='Sol/root fallback',scope='root source/numeric/PNG QA; not independent approval'),ensure_ascii=False,indent=2)+'\n')
progress='''\n\n## Palm 단독 접근 형상 진단과 단일 축 손가락 검증 완료\n\n직전 body9×2의 저장0/0.1/0.5/5초를 이용해16 source 배치를 조회했다. 신규12제안 중 t0 quarter만 선별을 통과하고 이후에는 검지·중지–기타 교차 증가가 있어 이 팔12 방향의 native ON을 실행하지 않았다. 손바닥 대표점 접근만으로 전체손 지지가 안전해지지 않았다. 추가 native/physics는0이다.\n\n엄지2/3·검지2/3·중지2/3의 actual parent 조건부 예측은24시점/144행에서 기존0.1mm/1mrad 경계를 통과했다. 전체손 finger1 모델 실패는 유지한다. [그림·설명·기준 실제 스트랩 영상]('''+str(P/'README.md')+''':1), [실제 변경 줄]('''+str(P/'CHANGED_FILES.md')+''':1)에 남긴다.\n\n[다음 팔12+손가락6 연동 source 계획]('''+str(A/'PALM_FINGER_COUPLED_SOURCE_PLAN.md')+''':1)은 미실행이다. Source 각도 범위/PD 경계와 전체손 형상을 함께 확인한 뒤 실제5초를 진행한다. 최종66 연주권한·자유G·하체root 고정·몸통목표와 기타 초기p/q 복원·유지 목표는 유지한다. 새 영상은 실제 passive strap 경로를 필수 표시한다. Luna/독립검수는 도구한도로 root 수행과 구분한다.\n'''
for name in ('README.md','PLAN.md'):
 p=A/name;assert '## Palm 단독 접근 형상 진단과 단일 축 손가락 검증 완료' not in p.read_text()
 with p.open('a') as f:f.write(progress)
visual=D/'VISUAL_REPORT.md';section='''\n\n## 93. 손바닥 단독 접근의 손가락 형상 교차와 연동 준비\n\n직전 body9×2 실제5초의 저장 상태를 사용했다. 이번 새 native/physics 실행은0이다.\n\n![손바닥 접근과 손가락 source 교차 증가]('''+str(P/'artifacts_v2/palm_gap_and_finger_overlap.png')+''')\n\n16배치 중4개는 기준0, 신규12개 중 초기 quarter만 source 선별을 통과했다. 5초 상태에서 quarter도 검지3/중지3–기타 common radius 증가0.920751/0.767056mm가 있어 실제 ON은 실행하지 않았다. 위 거리는 source witness 상한, 아래는 baseline 대비 source radius 증가이며 native 관통 깊이가 아니다.\n\n![조건부 단일 축 손가락 pose 비교]('''+str(P/'artifacts_v2/conditional_single_hinge_errors.png')+''')\n\n실제 부모 pose를 제공한6관절×24시점의 최대 원점 오차0.130835µm/회전오차0.187805µrad다. 전체손 FK/PD/접촉 인증이 아니며 이전 finger1 모델 실패를 유지한다.\n\n![분석 기준인 기존 실제 Isaac Gym 손·스트랩 영상]('''+str(trial/'hands.mp4')+''')\n\n이 영상은 기존 actual1200step/151frame이며 이번 추가 실행이 아니다. 실제 passive strap의 보이는 경로는 주황 실선, 가려진 경로는 옅은 점선이다. [전체 설명/원자료/초기값]('''+str(P/'README.md')+''':1), [다음 미실행 연동 계획]('''+str(A/'PALM_FINGER_COUPLED_SOURCE_PLAN.md')+''':1)에 기록한다. Root 실제PNG QA 완료, 독립검수는 도구 thread 한도로 보류다. 최종66권한과 기타 초기복원·유지/연주 안정화 목표는 계속 진행한다.\n'''
assert '## 93.' not in visual.read_text()
with visual.open('a') as f:f.write(section)
changed=[(A/'check_measured_palm_geometry.py','def main()'),(A/'check_palm_single_hinges.py','def main()'),(A/'make_measured_palm_geometry_artifacts.py','def main()'),(A/'make_measured_palm_geometry_artifacts_v2.py','def main()'),(A/'PALM_MEASURED_GEOMETRY_EXECUTION.md','# '),(A/'PALM_SINGLE_HINGE_CHECK_PLAN.md','# '),(A/'PALM_FINGER_COUPLED_SOURCE_PLAN.md','# '),(A/'README.md','## Palm 단독'),(A/'PLAN.md','## Palm 단독'),(visual,'## 93.'),(P/'README.md','# ')]
index='# 이번 변경의 절대 경로와 실제 줄\n\n'
for p,needle in changed:
 n=next(i for i,l in enumerate(p.read_text().splitlines(),1) if l.startswith(needle));index+='- '+link(p,n)+' — '+str(p)+'\n'
index+='\nSource 실행 소스는 소비 후 수정하지 않았다. 그림v1의 제목 겹침을 보존하고 새v2만 생성했다. 원본 스트랩 구현은 이번에 변경하지 않았으며 '+link(A/'strap_trial_recording.py',47)+'을 계속 사용한다.\n'
(P/'CHANGED_FILES.md').write_text(index)
print('documented',len(phases),'phases; appended VIS section93')
