# A 달성 지급 유보: CPU 산술

상위 PLAN은 root 소유다. 새 보상/학습/native 구현 없이 기존 지정 시간표의 production ledger만 재사용한다. 원 달성 지급은 별도 base_paid로 보존하고 새 pending/paid/expired/failed를 계산한다. 유효 native release latch를 본 control이 실패하지 않았을 때 .25b를 즉시 한 번 지급한다. pending 중 failure/reset/end/마감 초과는 소멸하고, 지급 후 미래 실패는 소급 취소하지 않는다. 안전종료까지 지연하는 새 조건은 없다.

- [x] 원 audit.main을 변경 없이 실행하고 결과 저장만 메모리로 받아 기존 결과와 exact 비교한다. 같은 clean/wrong 두 시간표의 원5항 tick-exact 검사를 유지한다.
- [x] 별도 A escrow 산술과 미달성/조기·적시·늦은 해제/실패/반복/부분 reset/H32/동일 control/예산/B7·B8 불변을 검사한다.
- [ ] 작은 표와 해석을 저장하고 source+CPU 실제 수치를 같은 change-reviewer에게 통합 검수한다.

source/원 raw/원 ledger/상위 PLAN 변경0, GPU/native/fit/PPO0. 지정된 합성 candidate/wrong일 뿐 실제 물리/안정된 무접촉/피부분리 자료가 아니다. 원 음악·해제90% 기준을 유지한다.
