# LH 고정 e16 bias v4 — 엄격 IK와 예측 추종오차의 구분

2026-10-17. V1/V2·실제 V2 실패·V3 코드/leaf/CPU35/freeze는 보존한다. V3 standalone main은 실행하지 않는다. 새 V4 코드/최소 CPU만 작성하고 독립 master review·Root ACK 전 실제 IK/main/source 쌍 평가/전행/native/PPO는0이다. 다른 geometry/source/Root 파일과 A·gain·runtime은 변경하지 않는다.

## 기준과 두 명령 변환

원 native_repeat_v8의 actual16 wrist-G를 고정 reference로 사용한다. 원 initial/qref FK를 재보정하지 않으며 current G×reference를 각3840/5532/6644/6720 시각의 world 목표로 한다. held는3836/5528/6640/6716이다. frozen actual-base+held-seed IK의 desired actual12 해 x*는 reference/frame당 한 번만 구하도록 코드로 작성한다.

`e_current=qactual12−oldHeld12`, `e16=qactual16_12−oldHeld16_12`다.

- 진단 current-error 변환(V3): command64=oldHeld12+(x*−qactual12)=x*−e_current. 반복 적용 시 held에 오차 보정을 누적하는 적분 서보 성격·지연/포화windup이 별도이며 runtime fullstep1로 채택하지 않는다.
- **주후보 fixed-e16 변환**: command64=x*−e16. 현재 held에 오차를 직접 누적하지 않는 고정 bias 식이다. IK seed·비선형성·기존 유한 제어의 실제 응답까지 비적분/안정하다고 인증하는 것은 아니다.

각 command를 float32로 제출한다고 가정하고 `B64=qactual+(commandF32−oldHeld)`와 arm-only F32 반올림을 분리한다. current-error B는 x*+command 반올림, fixed-e16 B는 **x*+(e_current−e16)+command 반올림**이다. 오차 변화량을 지우거나 actual q를 command로 치환하지 않는다. fixed bias가 source를 지킬지 답으로 가정하지 않는다.

## 사전 판정 — 서로 다른 오차를 혼동하지 않는다

1. **desired actual IK numerical fit:** 원 strict_commands/float32/native bounds/qref±.8/principal<160도, FK 위치<10µm/회전<.01도를 그대로 필수로 둔다. 코드가 사용할 원 solver weight/30회 한계는 바꾸지 않는다.
2. **current-error 변환의 B 진단:** V3와 같이 B64/B_armF32 각각 FK 목표오차<10µm/.01도를 요구한다. source1mm도 각각 AND한다.
3. **fixed-e16 변환의 preliminary 추종 설계:** 두 B 각각 model FK와 native-anchored 손목 목표오차가 **위치≤1mm/회전≤.5도**인지 검사한다. 엄격10µm/.01도 diagnostic bool도 별도 남긴다. 이 한도는 desired IK fit·원 source·사용자 actual 건강 기준의 완화가 아닌, 기존 e_current−e16을 포함한 G-relative 손목 예측을 선별하는 새 반사실 설계 한도다. 실제 동적 추종/압현 검증이 아니다.
4. **source:** 원19 hand/forearm×physicalG89 활성1602쌍의 g≥−1mm를 모든 표본·두 B 정밀도에서 그대로 AND한다. 목표 추종1mm와 source 방향 분리1mm는 다른 양이며 서로 대체하지 않는다.
5. **최종 명령:** command64/F32의 원 bounds/qref.8/principal160/finite·제출105 bounds와 다른93/zero8 exact를 각각 검사한다. clamp·lowpass·gain 변경으로 합격시키지 않는다. actual 전105/수정12 bounds·zero8 eps0는 false를 보존한 별도 건강 진단이다.

16초는 두 변환 모두 command=oldHeld raw exact/IK0·B actual q/native pose 복사본 raw exact다. x* 자리의 원 actual12는 reference-only 경계값이며 새 strict IK 해로 부르지 않는다. 원 task-chain FK/native 잔차와 그 goal 오차는 기록한다. 나머지3시각만 main에 IK 호출을 설계한다.

## native-anchored 형상과 범위

V3/원 V2 helper를 재사용한다. current/predicted actual FK rigid delta를 native pose에 적용하며 Larm4는 own delta, 실제 finger/palm은 L_Wrist 공통 delta로 native relative pose를 유지한다. finger FK world pose 대체·원 오차 흡수·기타/다른 body/속도/q 기록 변경은 없다. identity16은 재정규화 없이 raw 복사본 그대로다.

before, current-error B64/BF32, fixed-e16 B64/BF32의 부족 수·모든 pair/time·worst와 old joint error/변화/반올림/desired residual을 별도 남긴다. frozen certificate/complete fallback을 사용하고 큰 hull/solver 실패를 근사 통과시키지 않는다. 네 시각 조건부 geometry이며 전행/시간연속/cooked 침투/실제 force/동적 추종을 인증하지 않는다.

주후보 정적 가능성은 desired IK 원문턱·fixed-e16 명령 strict·B 두 정밀도의 새 추종 설계 한도·원 source1mm·소유권의 네 시각 AND다. 실패하면 그대로 기록하며 V3 이상적 변환의 성공으로 대체하지 않는다. 원 Spine/LH source FAIL·건강 미해결·실제 V2 결과는 보존한다.

## 최소 CPU·동결·실행

V3 selected before에 V4 source/새 leaf/CPU와 frozen V3 code/CPU35/freeze/README를 명시 추가한다. 원 model108/native/source14/core30·원29/V2 actual proof를 그대로 선택 SHA 확인한다. 새 A glob나 전체 조상 재실행은 없다.

- [ ] 실제 schema/e16 reference, 합성 current vs fixed 수식·e_current−e16 잔차·F32·16 rawexact/원 actual-target 분리·다른93/zero8·strict command·두 goal문턱 분리/NaN/오염 반례의 작은 CPU만 수행한다. actual IK/source pair 함수는 sentinel로 금지한다.
- [ ] 새 V4 code/CPU/leaf를 동결한 뒤 transitive V3를 포함한 master review와 Root ACK를 기다린다.
- [ ] Root만 새 output으로 V4 main 한 번(3 IK/4표본)을 실행한다. V3 별도 main/review/생산 실행은 생략한다.
- [ ] 실제 source/goal 실패를 보존하고 이후 전행/runtime/native는 별도 계획·검수로 진행한다.

`actual_dynamic_tracking_validated=False`, `actual_health_certified=False`, `full_period_certified=False`, `solver_cause_confirmed=False`, `final_adoption_eligible=False`를 유지한다. runtime fullstep1 적분 서보·저역통과/저주파 tracker·gain·압현/PPO를 추가하지 않는다.
