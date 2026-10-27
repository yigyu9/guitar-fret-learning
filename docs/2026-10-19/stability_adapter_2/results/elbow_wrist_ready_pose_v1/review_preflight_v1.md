# 준비 자세·6관절 실행 사전 검수

요약 판정: 수정 권장. source V3 close90의 조건부 수락은 일치하지만 실행 wrapper V1의 ball norm hard gate가 계획과 다르다. 아래 Critical 해결 전에는 타현 native 실행을 권고하지 않는다.

Critical: 1

## Critical

- [run_elbow_wrist_ready_v1.py:39](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:39): `solve_pick` 결과를 검사 없이 request6에 넣는다. 이 helper의 [norm 잔차:27](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v1.py:27)는 158° 초과 soft penalty뿐이며 모델/±1rad bounds가 ball norm<160°를 보장하지 않는다. [제어 계획:5](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V1.md:5)의 hard 조건과 다르다. 현재 G/실제 upstream는 source와 달라질 수 있으므로 source waypoint 통과로 대체할 수 없다. 새 wrapper 버전에서 finite 결과·요청6 및 실제 rate 적용 최종6의 norm<160°를 검사하고 실패 시 명시적으로 중단하거나, hard 조건을 보장하는 IK를 사용한다. 기존 source/helper/V1은 보존한다.

## 확인 근거

- [V3 범위:43](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py:43): 초기 변경은 오른12이며 Thorax±.25/Shoulder±.35/distal±1rad와 모델 교집합이다. 그 외69 초기 scalar는 두 후보 모두 정확히 동일하다. actual source initial norm은 close80 22.88/51.27/101.99/23.15°, close90 22.42/54.01/98.95/22.35°로 모두160° 미만이다. 초기값 범위에도 여유가 있다.
- [V3 결과:65](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py:65): close80의 최대 경로오차2.022248mm는2mm 초과로 거절, close90은 .000212463mm/initial 준비오차 .332629mm 및 전체 source clear로 수락한다. V1 두 후보 wholeclear false, V2 두 후보 wholeclear true이지만 최대 경로오차15.927/11.228mm로 거절한 기록을 보존했다.
- source V1/V2/V3의 현재 입력1016/1018/1020개 SHA가 모두 일치한다. anchor·guitar discovery·human/guitar XML mesh 선언·manifest·contract inputs·새 wrapper를 포함한 A helper를 pin한다. 해당 소스 네 개 AST를 확인했다. optimizer/native는 재실행하지 않았다.
- [wrapper:35](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:35): 현재 기타 pose와 실제 q를 사용하고 나머지75 요청은 준비 q_ref로 되돌린다. [최종 목표 검사:44](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:44)는 target75 동일성을 확인하며 실제75 상태를 덮어쓰지 않는다. 기존 contract의 rate·모델 clipping·60/240Hz와 body9+arms24 EFFORT/48POSITION 합성 제출 경로를 재사용한다.
- [wrapper patch:63](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:63)는 원 runner의 네 핵심 patch, 기존 support recorder/controller 및 OFF tracking initializer를 적용한다. 추가 코드에는 새로운 힘·state setter가 없다. readonly callback은 기존 endpoint 이후 pick/Chest/trunk 관측을 추가하고 상태 보존을 검사한다. source close90 config diff는 candidate 경로/SHA와 strike waypoint/enabled만이며 기존 gain/cap/LEFT OFF/root·하체/strap/Gfree 조건을 바꾸지 않는다.

## Warning

- [source 경로 검사:61](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py:61): 준비 initial whole audit 1회, waypoint5개+중점1개의 위치/norm/전완 capsule 검사다. 손·손가락 전체 연속 경로 clearance 또는 cooked/native 타현 인증은 아니다. 실행 중 실제 접촉·추종·guard·원 detector를 별도로 확인한다.
- [source trajectory:24](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py:24)와 [실제 wrapper trajectory:9](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:9)는 시간 배치가 다르다. CONTROL_PLAN이 wrapper의 접근/정착/down/up 일정을 정의하므로 source 경로 위치 검사를 실제 시간별 추종/속도 검증으로 설명하지 않는다. 원 detector60Hz RELEASE 판정은 후속 단계이며 아직 검수하지 않았다.
- [wrapper 요청 기록:45](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:45)의 IK 오차는 rate 적용 전 요청에 대한 값이다. 실제 marker 추종오차 및 rate 적용 최종 목표는 따로 분석해야 한다. 준비 첫2초/disabled의 error=0은 IK 검산 결과가 아닌 기본값이다.

## Suggestion

없음. Critical을 새 버전에서 닫은 뒤 수락 후보의 정지/타현 최대2시험으로 진행한다.
