# 사용자 기준 no-left 실제 물리 독립 검수

요약 판정: 문제없음. V13 정지와 V14 팔꿈치 파동은 각각 실제5초/1200physics/300control 완료, LEFT 접촉·추종 force/task0을 유지했다. 이는 현재 active human PD/gravity/finite point 제어와 초기값에 한정된 결과이며 무제어 평형 또는 연주 성공의 판정은 아니다.

Critical: 0

## Critical

- 추가 필수 수정 없음. [timelines producer:56](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:56)의 240Hz 명령 검산을 두 완료 case에서 읽기 전용으로 다시 실행해 canonical cases/comparisons exact 일치 및 passed를 확인했다. 별도로 좌우 scalar PD·gravity 기록+task의 requested 합성·clip을 각1200행 검산해 오차0을 확인했다. body9 합성, 사용 point Jacobian·child 분리·finite/cap·인간33 ownership 및 POSITION48 target/readback 보존도 통과했다. save는 메모리로만 대체했고 물리/디스크 재생산0이다.

## Warning

- 조건 범위: [OFF helper:51](/home/ajou/yigyu/3/stability_adapter_2/left_wrist_tracking_off_v2.py:51)의 task81은0이지만 :52–54의 LEFT gravity/scalar PD는 유지된다. actual LEFT0은 t0부터 분리한 초기 자세의5초 시험이며 동작 중 잡은 손을 놓는 release 시험은 아니다. `current_G_point_tracking=true`는 오른팔/body 목표 추종이며 LEFT 추종을 뜻하지 않는다. point request N과 raw contact lambda도 실제 접촉력 N으로 혼동하지 않는다.
- 샘플링 범위: [timelines:145](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:145)의 기타 최대변화·같은 시각 비교와 :175의 elbow range는60Hz trace다. canonical [analysis_final_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/analysis_final_v2.json)은240Hz endpoint 최대변화를 별도 계산한다. 파동 elbow range는60Hz `9.982977°`,240Hz 독립 계산 `9.983940°`로 샘플링을 구분한다. net drift와 후기 변화는 서로 다른 수치다.
- 보존된 이력 범위: V9 syntax/0step 호환 실패,2step 미완료 control 실패 및 안전중단을 완료5초와 합치지 않는다. V12 standalone before-map 누락 두 입력은 [source 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/review_source_v13.md:13)에 기록한 V11 map과 합성 확인 범위로 유지한다. 분석 output V1은 잘못된 glob에 log 파일이 섞여 실패한 기록이며 현재 canonical output은 같은 미수정 producer를 정상 directory 인자로 실행한 V2다.

## Suggestion

- 추가 없음. 성공2개와 실패7개, source/metadata/문법 실패 및 active 제어 범위를 최종 문서에서도 구분한다.

## 확인 근거

- 두 완료 case의 initial_values 전체 exact, V14 config 차이는 elbow amplitude0→5° 한 필드뿐이다. 최초2.5초 trace exact이며 목표 파동은 R_Elbow_y scalar,2.5~4.5초/.5Hz다. 실제240Hz range static `.042334°`,wave `9.983940°`; 같은 시각60Hz 기타 추가 최대차 `.014141704mm/.008541677°`다.
- 초기 native invariant guitar/neck/rootlower/finger42/PD/mass/q_ref/limits 및 FK/source audit가 모두 통과했다. 실제 PD driveMode는 EFFORT33/POSITION48이다. 양쪽Hip native state는 모든1200 endpoint에서 초기와 exact, 렌더151회씩 state-preserved이며 실제 영상151frames/30fps/5.033333초는 물리5초와 구분된다.
- actual LEFT 전구간0, tracking enabled false/force3/task12는 각1200 applied 행에서 exact0. 두 case의 상완 full-body1193step(positive raw lambda1191),Rhip1198(positive1192); 후기120step은 둘 다 presence/positive120이다. Chest/Torso/Spine/Thorax/head 접촉0이다. distal 접촉은 static45/wave162step 모두 **R_Elbow만**이며 손목·RH palm/finger 접촉0, 후기전완도0이다. 따라서 정착 후기의 주된 기록은 상완+Hip이며 지속 전완/손가락 받침으로 표현하지 않는다.
- 240Hz 기타 최대 body BBcentre 변화는 두 case `15.856413mm`,최대SO3 `5.557130°`; final은 static `10.213922mm/3.493939°`,wave `10.221150mm/3.489720°`다.4→5초 변화는 static `.000381270mm/.000803242°`,wave `.001582865mm/.000381277°`; final angular speed는 `.005024373/.005458830rad/s`로0이라고 표현하지 않는다. body9 최대 scalar 초기차 `1.768234°`,Chest 최대world rotation 변화 `3.663738°`다.
- [analysis producer:20](/home/ajou/yigyu/3/stability_adapter_2/analyze_user_guided_no_left_v1.py:20)은 `4×completed_control≤physics≤4×completed_control+3`를 허용하고 :28은 실제 적용 step까지만 명령을 검사한다.9attempt 총2780physics/694 completed control이며 성공2/실패7이다. 전수 summary를 독립 replay해 passed를 확인했고 canonical과 다른 leaf는 angular speed의 float 오차 `8.67e−19` 하나뿐이었다. incomplete case의 후기 지표는null,0step/2step을 완전control로 올려 세지 않았다.
- 현재 native attempt의 원 입력과 다른 경로는 승인된 main PLAN append뿐이다. `navigation_before_v1/PLAN.md` SHA `ac5695ec21909b84f59bfe1535f2a402c6bffe28a9e29ead44ffec43031ce562`가 모든 attempt의 원SHA와 같고 현재 PLAN은 snapshot bytes의 exact prefix다. 독립 replay는 이 경로만 읽기 전용 역사 SHA context로 해결했고 다른 입력 SHA는 그대로 확인했다. 원 attempt/analysis/source/raw 파일은 수정하지 않았다.

검수자는 이 파일만 생성했다. 실제 물리를 추가 실행하거나 native/source/assets/분석 산출물을 수정하지 않았다.
