# 엄지 유지 자세 변경 후 해제·재접촉의 기준 좌표

2026-10-17 KST. `front_facing_ready_finite_hand_maintenance_20261017.md`의 미래 Motion 설계에 대한 사전 보완이다. 원 spec/소비 Motion1/기존 실행과 판정은 수정하지 않는다. ThumbV2는 선정0이며 확장V3는 아직 실제 계산 전이다. 새 runtime 성공 선언이 아니다.

## 바꾸지 않는 물리 기준

Root 고정·유한 하체·기타 자유/중력ON/strapOFF, 원 gain/cap, 오른손21축 파지와 말단6축 타현을 유지한다. 완전 해제는 왼팔·왼손 전체의 기타 raw 접촉0인 연속15초이며3601 native/901 source 표본과 실제 손/전완 source2mm·손목G상대60mm를 모두 요구한다. 이후 접촉95%·연속5초 유지와 지정 압현 준비는 별도다. 서로 다른 실행이나 이탈 중 시간을 합치지 않는다.

## 원 참조와 새 목표를 분리한다

엄지 각도δ가 선정된 경우에만 적용한다. 원 closed/open14·actual10 손목 참조는 원 spec 그대로 저장한다. a(t)=smoothstep(t,16,16.5), gripped 엄지 closed 목표는F32(original_closed+δ·a(t))이고 원 open 목표는 그대로다. 원 계획대로 open/close 중 엄지 보정은 각각 a·(1−opening), a·close로 변화하며 모든 phase 경계는 직전 실제 제출LH26 exact다. `held+δ`를 매번 더하지 않는다.

- release의 선언된 command 개방량은 **그 release 시작 시각의 새 closed 목표와 원 open 목표의 차이**다. 실제 개방량은 그 release 시작 native q에서 측정한다. 과거 actual10 기준 차이도 별도 진단으로 보존하지만 이를 현재 동작의 개방량으로 부르지 않는다.
- 단독 release/free_strike/regrasp의 release16초는 a=0이므로 시작 엄지는 원closed이고 선언 개방량은 원약0.18rad다. 향후 연속 실행의 release28초/59초는 a=1이면 변경된 closed에서 시작한다. δ=−.1일 때의 예시 개방량은 약0.08rad이며 아직 선정 각도나 성공값이 아니다.
- regrasp의 선언closed는 닫힘 종료 시각의 새closed14이고, thumb 이외13축은 원값이다. 실제 닫힘은 close 시작 native q에서 측정하고 원closed 오차와 새closed 오차를 각각 기록한다.
- 원11개 opening/closing 후보 이름·index·direction은 보존한다. thumb만 변경된 command 개방량에 대해 원 공식 min(0.1rad, 0.5×개방량)으로 필수 실제 개방/닫힘량을 정한다. 나머지 후보의 기존 수치는 그대로다. 원 spec 수치를 새 수치로 덮어쓰거나 원판정 통과로 설명하지 않는다. 이 새 자세에 맞춘 기준 변경과 실제 접촉0/15초·source·접지·지지의 고정 물리 기준을 구분한다.
- 기존 재파지는 선언된 후보 중 **동일 축 하나 이상**이 모든5초 표본에서 닫힘량과 목표 오차≤0.1rad를 만족하는 판정이다.11개 축 모두가 성공했다는 의미로 부르지 않는다. 각축 개별 결과를 기록한다.

## 구현 전 확인

- [ ] 실제 원 spec slot/index/closed/open/expected SHA를 읽어 공식과 값을 고정한다.
- [ ] Motion parent의 중간 요청/metadata와 새 최종 요청·목표 소유권을 나눠 기록한다. 실제16 참조·고정e16와 원actual10 참조를 분리한다.
- [ ] baseline/repeat와 release16·연속release28/59의 경계, 절대 목표와 누적 덧셈 방지, 원/새 개방량, 실제 reference 시점을 CPU로 확인한다. 새13 command·bounds·rate/F32와 실제 운동을 구분한다.
- [ ] 새 analyzer는 새 목표를 직접 재구성하고 원 legacy 참조 진단을 보존한다. phase별 가짜 시간/cfg/state 치환이나 원 raw의 재작성은 하지 않는다.
- [ ] 정적 선정·독립 코드 검수·RootACK·실제 baseline 정지/source/발/건강·압현 준비 통과 뒤에만 다음 물리를 실행한다.

새 thumb 자세에 대한 압현 준비·연속15초 해제·재접촉 후 유지·77초 연속/재시작은 모두 미검증이다. strict EPS0/원인 미확정·fullfinger FK 및 현 힘/진동/음향의 범위 제한을 계속 보존한다.
