# Gripped 왼손목의 현재 기타 상대 유한 추종 — 최소 정적 진단

2026-10-16 요청, 2026-10-17 작성. 새 `diagnose_gripped_wrist_tracking_v1/`의 코드/최소 CPU만 먼저 작성한다. 독립 검수·Root ACK 전 실제 IK 생산 main·전행 sweep·새 native·PPO는0이다. 원 소비 자료/A/목표/gain/물리/filter/문턱을 변경하지 않는다.

## 관측과 가설

현재 `.15mm` Body9 후보 native_repeat_v8의 core는 원29게이트 결과와 별도로 올바른 `--baseline` 재분석 `analysis_repeat_v8_retry_v1`의30게이트가 통과했다. 반면 source14게이트는 Spine/Torso와 LH grip에서 실패했다. LH는1381×1602쌍 중544부족, worst LH:index1–guitar root0 g=−1.176551591mm@step6644이며 root1도 부족했다. 원 성공/실패 자료를 보존한다.

Root의 좁은5표본 관측상 actual16→worst의 G-relative L_Wrist 변화는 약.571059mm/.203656도다. gripped 상태의 원 Motion1이 LH를 hold하는 것과 양립하지만 인과 확정은 아니다. 가설은 **actual16의 실제 G-relative 손목 pose를 현재 기타 pose에 유한 LH12 IK로 추종하면 source1mm를 만족하는 조건부 기하가 가능한가**다. 성공을 가정하지 않는다. 별도 Spine/Chest 보존 가설을 합성하거나 그 성공을 전제하지 않는다.

## 입력과 네 시각

고정 run은 닫힌 native_repeat_v8, 시각은 step3840/5532/6644/6720(16/23.05/27.6833333333/28초)만이다. actual16 native wrist/G로 `T_G^-1 T_LWrist`를 만든 뒤 각 current native G로 world 목표를 재구성한다. G world pose/source vertices는 각 원 시각 그대로다. 실제 시각/원 target60 행을 대조한다. state step k는 k번째 새 명령 직전이므로 **직전 제출 target k−4**(3836/5528/6640/6716)를 사용한다. 같은 k의 target을 held seed로 선취하지 않는다. 마지막6720은 final state이며 새 target 행이 없다. 각 state와 held target의 시각 차이를 명시한다.

사전 입력은 native attempt/config·initial/native properties·states240/targets60·finalstate/report/support wrapper·native external before/log, source14 FAIL summary와 각 before map, 올바른 core30 summary/before 및 원29 summary, 직접 소비 frozen source와 primary108모델(선언106+manifest2), 본 코드/leaf/CPU다. historical expected map의 실제 소비 key를 확인하고 flat/envelope/충돌을 검사한다. 새 A glob와 전조상 전체 재검증을 하지 않는다. 원문을 before SHA/archive하고 종료 후 동일성을 확인한다.

## 원 solver와 두 q 경로

원 native initial/q_ref로 full_fk를 구성하며 actual16/현재 body로 FK zero를 재보정하지 않는다. frozen Motion1.solve_left와 그 원 solve_wrist/least_squares 수학·가중치·30회 한계를 그대로 사용한다. 각 표본의 FK base는 qactual105이고 seed는 마지막 제출 target의 LH12다. target-base 재최적화는 추가하지 않는다.

원 solve_left가 float32 round-trip한 새12값을 actualq와 마지막 제출 target에 각각 삽입한다. 각 다른93 및 zero8은 자기 원본과 exact 불변이어야 한다. actual의 기존 다른축 eps0/zero8 잔차는 false일 수 있으며 실제105 bounds 성공으로 바꾸지 않는다. 원 수정12 bounds/q_ref±.8/principal<160도·finite와 제출105 bounds를 분리한다. actual-base FK의 목표오차 **위치<10µm/회전<.01도**, strict_commands를 후보의 필수 조건으로 사전 고정한다. 원 solver로 못 만족하면 실패를 그대로 기록하며 가중치·정규화·bounds·FK 보정으로 억지 통과시키지 않는다.

제출 전체 target FK의 목표오차는 실제 q와 Body9 등 차이가 있으므로 별도 진단이다. 이를 actual-base 성공과 혼동하지 않고 actual q 전체를 target으로 치환하지 않는다. 원 rate/cap/controller를 replay하지 않았으므로 새12목표의 실제 동적 추종이나 주입 없는 구현 가능성을 인증하지 않는다.

actual16 wrist-G reference와 (1) actualq16에서 LH12만 held target으로 바꾼 원 command_pose 방식, (2) full submitted target FK 방식의 wrist-G 차이를 함께 기록한다. 첫16시각의 새12−held12 및 world 목표 차이는 후속 finite blend/경계 연속성 필요성 판단 자료일 뿐이며 현재 생산 Motion/일정을 바꾸지 않는다.

## 실제 손가락 형상의 native-anchored 반사실

원 fullfinger FK 오차가 있으므로 trial FK의 finger world pose로 native 형상을 덮지 않는다. body의 rigid delta를 `D_body=T_FK_trial(body)·T_FK_current(body)^−1`로 정의한다.

- L_Thorax/L_Shoulder/L_Elbow/L_Wrist는 각각 자신의 D_body를 해당 현재 native pose에 왼쪽 합성한다.
- LH 손가락/손바닥의 실제 pose는 **모두 D_LWrist 하나**로 움직인다. 실제 각 손가락–손목 상대 pose가 그대로 유지된다는 조건부 가정이며 손가락 q/FK 오차를 보정한 것이 아니다.
- 기타·다른 신체·q 기록/속도는 원 자료를 그대로 둔다. 이 pose-only 복사본은 새 native state가 아니라 형상 평가용 반사실이다. actualq-base delta와 submitted-target-base delta를 각각 계산·구분한다.

현재/반사실 wrist 목표 오차, body별 delta, 손가락 relative pose 불변, 원 fullfinger/native FK 오차 표와 actual105 eps0를 함께 기록한다. 원 raw와 source vertex를 변경하지 않는다. actual16 기준을 새 FK reference로 삼지 않는다.

## 형상 판정과 범위

원19 hand+forearm shape와 physicalG89의 native 활성18×89=1602쌍을 각 시각/경로에서 검사한다. inactive thumb_pad는 보존하고 active 예산을 적용하지 않는다. frozen helpers2의 AABB/direct plane/cache/complete fallback과 원 **g≥−1mm** 예산을 사용한다. 원 helper가 거부하는 큰 Minkowski나 solver 실패를 근사 통과시키지 않는다. 부족만 정밀 fallback하며 humanoid self-hull을 새로 만들지 않는다.

원 before와 actual-base 반사실 after의 부족 수·모든 부족 pair/time·worst를 비교한다. 제출목표 반사실도 독립 표로 남긴다. 주가설의 정적 가능성은 네 표본 모두 원 strict IK/소유권/actual-base native-anchored source1mm가 통과할 때만 true다. submitted 경로는 별도 진단이며 그 형상 실패를 숨기지 않는다. 양쪽 모두 실제 force/contact·압현/동적 안정·전행/시간연속·최종 채택 증거가 아니다. 원 Spine FAIL과 건강 미해결도 남는다.

## 제한된 검증 순서

- [ ] 새 leaf/code와 expected before를 먼저 작성한다.
- [ ] 최소 CPU: 실제 state/target/final schema·source 배치/필터19/1602·원 초기FK·G-relative 재구성·rigid delta 방향·finger 상대pose·다른93/zero8·누락/NaN/SHA/잘못된마지막target 반례를 검사한다. 실제 solve_left는 CPU에서 sentinel로 금지한다.
- [ ] code/CPU를 동결하고 다른 reviewer와 Root ACK를 기다린다.
- [ ] Root만 새 output으로 네 표본 실제 IK/형상 main을 수행한다. 실패는 원문 보존한다.
- [ ] 후속 전행/finite tracking 생산코드/native는 별도 새 계획·검수 없이는 실행하지 않는다.

이 진단으로 손가락 goal·LH12 생산 제어·gain/cap·하체·RHS·G 직접힘을 바꾸지 않는다. `actual_dynamic_tracking_validated=False`, `full_period_certified=False`, `final_adoption_eligible=False`를 유지한다.
