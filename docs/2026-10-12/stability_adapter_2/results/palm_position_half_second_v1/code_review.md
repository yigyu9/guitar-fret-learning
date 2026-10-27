# 동일 조건 0.5초 후속 실행 전 독립 코드 검수

- 검수일: 2026-10-07
- 범위: `run_palm_position_followup.py`, `analyze_palm_position_followup.py`, `PALM_POSITION_HALF_SECOND.md`와 이전 0.1초 producer 대비 diff.
- 편집: 이 기록만. 이전 code/runtime review 및 frozen 결과 보존. native 초기화·rollout·source query 실행 없음.

## 요약 판정: 문제없음

- Critical: 없음.
- Warning: 후속 leg_torques의 전체 표본 수 검사 누락은 121개·finite 검사 추가를 확인해 해결했다. 남은 finding 없음.
- Suggestion: 없음.

## 확인한 변경과 경계

- runner diff는 설명·자기 SHA 파일명·121 표본/120 step 루프·종료 조건·완료 검사와 PI prefix 길이 확장이다. shared PI/RatePalmResidual/source Jacobian 계산은 그대로 호출한다.
- step 0..120에서 상태 표본 121개를 저장하고 마지막 표본에서는 실행하지 않는다. 물리 step은 120개이며 240 Hz에서 0.5초다. 0..119 중 4-step 간격의 갱신은 30회이며 dt=1/60을 유지한다.
- PI는 기존 quiescent 3초 자료의 states/trace/leg_torques 121개, controls/contacts 120개와 exact prefix를 검사한다.
- analyzer는 세 조건 각각 이전 0.1초의 states/trace/hands/queries/leg_torques 25개 및 controls/contacts 24개와 exact prefix를 검사하고 소비한 이전·현재 파일 SHA를 기록한다.
- 후속 배열의 121/120개, physics_step/time 정렬과 30개 update 위치를 검사한다. leg_torques에도 전체 121개와 finite 검사를 추가했다.
- ±0.15 rad, native/C02 diagnostic box, 직전 float32 전달 목표 기준 ±0.02 rad rate, 위치 배율 2, regularizer 0.05 m/rad, 단조 anti-windup 최대 25회 및 solver 실패 save-stop 경로는 이전 코드와 동일하다.
- 초기 q·고정 LA·기타 초기 p/q 목표·PD/solver·고정 human root·주요66 연결·몸통9/손가락42/C02 하체 목표 유지 검사와 target-only 제출 경계도 동일하다. 실제 state 고정이나 기타 pose/state 쓰기를 추가하지 않았다.

## 검증 및 최종 경계

두 새 파일을 AST로 파싱했고 121 표본·120 step·30 update·0.5초의 스케줄을 순수 계산으로 확인했다. 제어 알고리즘 diff가 없으므로 이전 순수 수치 검증을 반복하지 않았다. 새 native 실행 결과와 실제 prefix·손/기타 응답·접촉·장력·관절 상태는 이후 원자료 검수 대상이다.

승인된 조건의 시간 연장 구현에 남은 finding이 없다. 이 코드 검수 기록을 동결하며, 0.5초의 안정성 또는 지지를 미리 판정하지 않는다.
