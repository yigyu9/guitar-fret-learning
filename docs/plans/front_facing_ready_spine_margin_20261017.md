# 반복10 현재 자세에 대한 추가 여유 가설

목표 누락/명령 포화 대신 실제 동작 중 형상 여유 부족이 관측됐다. 원 정지10 성공과 반복10 source 실패를 보존한다. gain·힘 제한·기타 상태를 바꾸지 않는다.

## 첫 단계: 두 실제 시점의 조건부 가능성만 검사

- 기준은 현재 repeat10의 gap 최악5060(21.083333초)와 실제 Spine tilt 최악6330(26.375초,4.959676396도)다. 후자의 target은 직전6328을 명시한다. source60Hz frame의6330을 만들지 않는다.
- 현재 .12mm Body9 증분을 이미 포함한 실제 q와 final goal에 **추가 δ9**를 더하는 가설이다. 기존 증분 중복 가산 금지. 현재 actual G world pose는 고정한 반사실이며 실제 반응을 보장하지 않는다.
- 5060의 submitted-goal FK Chest pose6 보존과 actual Spine 고정법선 gap의 추가0.20mm/0.35mm를 각각 요구한다. 두 gain은 별개의 후보이며 자동 채택하지 않는다.
- 원 initial 상태에서 한 번 보정한 FK를 사용한다. 현재 actual로 재보정하지 않는다. actual native capsule에는 FK 전후 rigid delta를 적용하고, native와 원FK의 gap 차도 기록한다.
- ±.03rad/축 search 및 두 시점의 actual/goal 수정9 bounds 교집합을 사용한다. 원other96/zero8·principal160·F32 검사는 유지한다.
- SLSQP의 F64 제약에 두 시점 actual/goal 모두 Spine≤4.8도, Torso/Chest≤4.9도, 좌우≤2.9도를 넣는다. 원 source1mm·Spine5도 등 채택 gate를 바꾸는 것이 아니라 사전 설계 여유다.
- actual Chest drift≤10µm/.01도, R_Shoulder/L_Wrist/Head≤0.1mm/.01도 보조 상한을 두 시점 모두 부등식으로 제한한다. goal Chest 보존은 위치1e−7m/회전1e−6rad 원 기준을 유지한다. F32는 별도로 평가하며 허용epsilon을 추가하지 않는다.
- 두 후보/두 시점의 point 검사를 먼저 완료한다. 하나의 SLSQP 실패는 기하 불가능성 증명이 아니다. 통과 후보가 없으면 실패·제약 잔차를 보존하고 설계를 재검토한다.

## 후속 조건

point 통과만으로 runtime/native에 진입하지 않는다. 두run 전기간 source/target/ramp·보조 상한을 새 버전으로 검사하고, 실제 정지5초와 반복을 다시 통과해야 한다. 새 제어·native·왼손 해제·PPO를 이 leaf의 첫 단계에서 실행하지 않는다.

- [ ] 실제 schema/expected SHA/model108 입력 닫기
- [ ] 작은 CPU와 독립 FINAL/Root ACK
- [ ] 두 실제 점의 조건부 optimizer 결과와 한계 기록
- [ ] 결과에 근거해 후속 전기간 검사 여부 결정
