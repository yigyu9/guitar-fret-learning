# LH 증분 IK v3 — desired actual과 제출 명령의 분리

2026-10-17. 새 V3 진단 코드/최소 CPU만 작성한다. V1/V2 및 기존76파일 freeze·실제 V2 결과를 보존하며 A/기존 소비 자료·gain·native·PPO는 변경하지 않는다. 독립 review·Root ACK 전 실제 IK main/source 쌍 생산 평가/전행은0이다. 생산 tracker 구현은 범위 밖이다.

## 관측과 새 가설

닫힌 V2 main은 command16+B가16/23.05초에는 통과했지만27.683/28초에 thumb3–guitar root0/1 source1mm를 만족하지 못했다. actual16+A의 뒤3표본은 source 통과했으나 그 command를 B에 그대로 쓰면 기존 actual−held 오차가 추가 반영되어 실패했다. 원 결과와 source14 FAIL/core30·원29를 수정하지 않는다. 동적 원인을 확정한 관측은 아니다.

가설은 IK 해를 먼저 **desired actual12 x***로 해석하고 제출 명령을 별도로 만드는 것이다. 주 기준은 원 actual16 native wrist-G이며 기존 FK zero/실제 finger 오차를 재보정하지 않는다.

`x*=solve_left(actualq-base, oldHeld12-seed, currentG*actual16_wristG)`

`command64=oldHeld12+(x*−qactual12)`, `commandF32=float32(command64)`

`B64=qactual12+(commandF32−oldHeld12)`, `BF32=float32(B64)`

기존 joint 오차가 유지된다는 조건부 응답에서 B64는 반올림을 제외하면 x*와 같고 `B64−commandF32=qactual−oldHeld`를 보존한다. 이는 유한 PD·support JTF·rate·관성·접촉이 실제로 이 응답을 만든다는 보장이 아니다. 직접 state overwrite나 actual 제어 성공으로 표현하지 않는다.

## 네 시각과16 경계

원 native_repeat_v8의3840/5532/6644/6720만 사용하며 held는3836/5528/6640/6716이다. 원 initial/qref FK와 frozen Motion1.solve_left/solve_wrist 수학·weight·30회 한계를 유지한다. target-base 재최적화는 없다.

16초는 IK0회·command=oldHeld exact·B actual q/native pose 복사본 원본 그대로다. x* 대신 원 actual12를 경계 reference-only 값으로 표시하고 기존 실제 bounds/zero8 eps0는 false일 수 있음을 그대로 남긴다. IK를 호출하지 않았으므로 이 값을 ‘새 strict IK 해’라고 하지 않는다. 원 task-chain 범위의 FK/native 차이와 boundary 목표오차는 별도 기록한다. 이후3표본만 실제 main에서 IK하도록 작성한다.

## 명령·응답 판정

- desired actual IK는 원 strict_commands·bounds/qref±.8/principal<160도·finite·float32 및 FK 위치<10µm/회전<.01도를 검사한다. 16 경계는 IK 미호출을 명시하고 원 actual의 strict/bounds 진단을 성공으로 바꾸지 않는다.
- 최종 command64/F32 모두 원12축 native bounds/qref±.8/principal<160도와 finite를 검사한다. 새 제출105는 oldHeld105의12만 바꾸며 다른93/zero8 exact·원105 bounds를 유지한다. command를 clamp해 합격시키지 않는다.
- B64/B_armF32는 각각 original actual의 다른93/zero8을 exact 유지하고 FK 목표오차<10µm/.01도를 검사한다. B64−x*, BF32−x*, 기존 joint 오차 보존/rounding 잔차와 native-anchored 목표오차를 별도 기록한다.
- actual의 전105/수정12 bounds·zero8 qref exact는 별도 진단이며 false를 보존한다. 이 정적 진단의 source 가능성은 actual 건강 성공이 아니다. 원 eps0/원인 미해결·최종 채택은 false다.

주가설의 정적 조건은 네 시각의 새 명령 strict·해당 시각 desired/B FK goal·B64/BF32 source1mm/소유권 AND다. 실제16 strict IK 미호출이란 범위를 유지한다. 경계 외 하나라도 실패하면 전체 정적 가능성은false다. source/IK 문턱을 사후 완화하지 않는다.

## 형상과 입력 보존

원 native 현재 pose에 trial/current FK rigid delta를 적용한다. Larm4는 own delta, finger/palm은 공통 L_Wrist delta로 실제 wrist-relative pose를 고정한다. finger FK world pose로 실제 형상을 덮지 않으며 전체 원 body FK 오차표를 보존한다. B16 identity는 raw 복사본 그대로다. 기타·다른 body·raw q/속도는 고정된 pose-only 반사실이다.

before와 B64/BF32의 원19 shape/89physicalG 활성1602쌍을 frozen helper/direct plane/complete fallback의 g≥−1mm로 비교할 코드를 작성한다. 부족 pair/time/worst·solver 실패를 보존한다. 큰 self-hull·새 filter·손가락14 목표 변경은 없다.

V2 selected input closure에 새 V3 source/leaf/CPU, 완료 V2 result/input-before·Root before/after/log/ACK·기존 review/freeze를 추가한다. Root after의 before/log/result SHA와 입력불변/return0을 대조하고 실제 소비 selected key만 expected map과 검증한다. primary108모델·원 native/source14/core30 입력을 보존한다. 새 A glob/전조상 재분석을 하지 않는다.

## 제한된 검증 순서

- [ ] leaf/code/선택 expected before를 먼저 기록한다.
- [ ] 최소 CPU는 실제4표본/held/reference/V2 실패 schema, 합성 command 변환·B 재현/오차 보존·F32 차이/경계exact/다른93·zero8/분리된 command bounds 반례만 검사한다. 실제 IK/source 쌍 평가는 sentinel로 금지한다.
- [ ] 새 code/CPU/leaf 동결 후 독립 review·Root ACK를 기다린다.
- [ ] Root만 새 output으로3회 IK/네 표본 형상 main을 수행한다.
- [ ] 후속 전행/finite rate·effort tracker/native는 별도 계획/검수로 진행한다.

`actual_dynamic_tracking_validated=False`, `actual_health_certified=False`, `full_period_certified=False`, `solver_cause_confirmed=False`, `final_adoption_eligible=False`와 새 native/PPO0을 유지한다.
