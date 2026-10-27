# Gripped 손목 추종 v2 — 두 기준·기존 관절 오차 보존 응답

2026-10-17. V1 코드/CPU30/leaf/freeze는 보존한다. 새 V2 파일만 작성하며 A·기존 소비 자료·gain·native·PPO는 변경하지 않는다. 코드 동결·독립 검수·Root ACK 전 실제 IK main/source 쌍 생산 평가/전행은0이다. 생산 LH tracker 구현은 이번 범위가 아니다.

## 가설을 나누는 이유

actual16 wrist-G만 목표로 삼고 실제 q12를 새 command12로 완전히 바꾸는 반사실은 원 actual−held 관절 오차와 유한 PD의 기존 평형을 지운다. 따라서 원 V1과 실제 source14 FAIL을 수정하지 않고 두 reference와 두 응답을 별도로 계산한다. 원 actual16→worst 손목-G 변화의 상관을 원인으로 확정하지 않는다. source1mm/원5도·IK/수치 기준을 완화하지 않는다.

기록은 동일 닫힌 native_repeat_v8의 step3840/5532/6644/6720이다. held는 각각 직전 제출3836/5528/6640/6716이며 같은 step의 새 target을 선취하지 않는다. reference는 actual16 native 기타 pose로 표현한다.

- **actual16 reference**: 실제 native L_Wrist의 G-relative pose.
- **command16 reference(주가설)**: qactual16의 다른93을 유지하고 LH12만 held3836으로 넣은 원 FK pose의 G-relative 값. full held105 FK reference는 별도 진단이며 기준으로 대체하지 않는다.

원 initial/q_ref full_fk를 재사용하며 실제16 body/FK로 zero를 재보정하거나 finger FK 오차를 흡수하지 않는다. 두 reference 차이를 원값으로 기록한다. command16 reference는16에서 기존 command_pose와 일치하므로 목표 jump가0인 유지제어 기준으로 더 자연스럽다. 이것이 실제 평형 유지·기타 상대하중·추종 성공의 증명은 아니다.

## 명령 IK와16 경계

각 reference/frame의 world 목표는 current native G×reference다. step3840은 원 future wrapper 조건과 같이 **newCommand12=oldHeld12 exact, IK0회**로 둔다. 같은 held 명령의 실제 FK 목표오차를 평가한다. command16 기준은 수치 오차 범위의0이며 actual16 기준 경계오차는 진단값으로 남긴다. phase hold를 우회하는 새 생산코드는 만들지 않는다.

나머지3시각×2reference에서 원 Motion1.solve_left를 actual FK base+held12 seed로 한 번씩 사용하도록 코드만 작성한다. target-base 재최적화는 없다. 원 solve_wrist 가중치/30회/초기 FK·qref±.8/bounds/principal<160도·float32를 유지한다. new command의 실제 FK 목표오차 위치<10µm/회전<.01도·원 strict_commands 및 제출105 bounds가 필수다. 불가능하면 실패 그대로이며 가중치·문턱·FK를 보정하지 않는다.

## 두 actual 응답과 float32

oldActual12=q, oldHeld12=h, 새 float32 command12=c라 두면 다음을 분리한다.

- A, 완전 추종: q_pred12=c. 원 actual−held 오차를 없애는 낙관적 진단이다.
- **B, 증분 응답(주가설)**: q_pred12=q+(c−h). float64에서 q_pred−c=q−h를 보존한다. arm-only float32 round-trip 후의 오차 보존 잔차를 별도로 기록한다. 기존 오차가 미래에도 고정된다는 조건부 가정이며 dynamics 해가 아니다.

각 예측의 다른93과 zero8은 자기 원 actual을 exact 보존한다. 새 제출 target은 oldHeld105의12만 c로 교체하고 다른93/zero8은 oldHeld 원본을 보존한다. 실제 q 전체를 target으로 치환하지 않는다. actual/target base의 같은 command delta가 같은 SE3를 보장하지 않으므로 actual-base A/B와 target-base 명령 변화를 따로 기록한다. target-base 재최적화나 target-base 기하를 actual로 쓰지 않는다.

step3840의 B는 command delta0이므로 qactual과 native pose-only 반사실 모두 **원본 그대로**다. identity 처리에서 원 quaternion을 재정규화해 raw를 바꾸지 않는다. A는 held와actual 차이를 지우므로 같은 경계에도 B와 다를 수 있다.

actual105 eps0/zero8 actual≠qref, q_pred의 actual bounds와 command bounds를 분리한다. 명령의 원 bounds는 필수이며 기존 actual 잔차를 무근거 epsilon으로 통과시키지 않는다. 반사실의 actual bounds는 진단표에 false 그대로 남기고 건강/원인/최종 채택은false다. 이를 새 생산 actual 건강 성공으로 표현하지 않는다.

## native-anchored 형상

V1과 같이 trial/current actual FK의 body rigid delta를 현재 native pose에 적용한다. Larm4는 own delta, 모든 실제 LH finger/palm은 공통 L_Wrist delta를 사용한다. finger의 실제 wrist-relative pose는 고정된다는 가정이며 전체 finger FK world pose를 native로 대체하지 않는다. 기타·다른 신체·raw q/속도는 원본 그대로인 pose-only 복사본이다.

각 reference에 A, B_float64, B_armF32를 분리해 원19 hand/forearm×physicalG89의 활성1602쌍을 원 g≥−1mm·frozen helper/direct certificate/complete fallback으로 평가할 코드만 만든다. before를 별도로 보존하고 부족 pair/time/worst를 모두 기록한다. 큰 hull/solver 실패를 근사 통과시키지 않는다.

주가설의 조건부 source 가능성은 **command16 reference + B의 두 정밀도**가 네 시각 모두 source1mm·원 명령 IK/소유권을 만족할 때만 true다. actual16+A는 기존 오차를 지우는 낙관적 진단으로 별도다. 어느 결과도 전행 source·실제 force·압현·동적 추종·생산 제어·건강 채택을 보증하지 않는다. 원 Spine/LH source FAIL과 원 fullfinger FK 오차표를 유지한다.

## 검증과 봉인

V1 selected closure를 재사용하되 V2 source/새 leaf/CPU를 before에 명시 추가한다. 닫힌 native/source14 FAIL/core30+원29/원 expected maps/primary108·직접 소비 helper·원 initialFK를 전후 SHA 확인한다. 새 A glob와 전체 조상 재분석은 하지 않는다.

- [ ] 최소 CPU: 실제4표본/held/reference schema와16 command target 재구성, 합성 q-offset 보존 및A 소거/B 보존·armF32 차이,16 exact held/actual 불변, actual-base vs target-base의 같은 delta 차이, rigid delta/finger 상대pose/다른93·zero8·NaN/누락 반례를 검사한다. solve_left와 실제source 쌍 평가는 sentinel로 금지한다.
- [ ] V2 code/CPU/leaf 동결 후 독립 review/Root ACK를 기다린다.
- [ ] Root만 새 output으로6회 IK+두 기준/두 actual 응답의 네 시각 기하 main을 실행한다.
- [ ] 결과에 따라 별도 전행/finite blend/runtime 계획을 검토한다. 현재 단계에서는 생산 구현/native0이다.

`actual_dynamic_tracking_validated=False`, `full_period_certified=False`, `solver_cause_confirmed=False`, `final_adoption_eligible=False`를 유지한다. source/수치 budget 통과를 SDK 원인 확정이나 현재 actual 건강 성공으로 승격하지 않는다.
