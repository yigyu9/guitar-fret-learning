# 원본 시간창 기반 ENTRY 사전 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. 실행 전 변경 범위 검수이며 실제 native 결과·타현 성공은 아직 확인하지 않았다.

- `run_strike_timed_entry.py:163–171`: 기존 `strike_timed_approach_open`에 원본 song time/effective target time/첫 offset/approach lead를 그대로 전달한다. helper나 source clock에 dt를 추가하지 않는다.
- actual source phase1에서 original approach가 닫혀 있으면 geometry3 READY를 선택한다. 열렸을 때 ENTRY4/실제 entry 거리 latch 후 EXIT5, phase0 READY3 및 phase2 EXIT5는 이전 경로를 유지한다. 새 entry check는 닫힌 phase1의 선택이 READY3인지 기록한다. 이는 waypoint 선택 계약이며 실제 조기 crossing 방지나 detector 결과의 증명은 아니다.
- 이전 APPROACH-only runner와 diff를 직접 확인했다. 다른 목표 합성·PI·rate·recovery gain·source phase/detector/window·학습 경로는 변경되지 않았다. R9 phase별 damping 복원과 native properties/state readback도 유지된다.
- 보존 wrapper 변경은 실행 module 이름뿐이다. native import 전 source/data SHA 수집·원문 보존, 종료 재대조·argv finally 복원을 유지한다. 두 새 Python 파일의 Python3.8 AST 검사를 통과했다. 검수 중 native 초기화·물리 실행은 하지 않았다.

검수 SHA256:

- runner: `0e6fc3e2c320738e1b9841c184fdcc4604420866e77e17daca52a22b9334353e`
- wrapper: `be1bf8c3dbee9252e7d590410da1677690c0d065414d300e18761247e216331c`
- 계획: `2a8c5c83b7b603935a0bd0af2592f820691876e2d7db53c89fabae9725b0ac4e`

첫 hit/회복까지 이전 결과의 실제 동일성, 시간창 이후의 인정 타현·기타 범위·전체 진행은 실행 후 확인 대상이다. 사전 actionable finding 없이 기록을 동결한다.
