# 열린 APPROACH 증분 팔 목표 — 독립 사전검수

요약 판정: **문제없음(PASS)**. 현재 남은 Critical / Warning / Suggestion 없음. 기존 waypoint-velocity runner 대비 새 runner/wrapper/계획의 변경만 검수했다. Native 초기화·physics 실행은 하지 않았다.

- [run_strike_incremental_approach.py:197](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:197): 열린 phase1도 기존 policy+PI 대신 이전 제출 목표+2δ를 쓴다. READY/닫힌 phase1/RECOVER의 목표 식은 그대로다. δ±0.15rad·증분2δ±0.3rad·native bounds·기존 최종 float32 rate clip을 유지한다. 각 증분 한계는 누적 목표의 초기각 대비 한계를 뜻하지 않는다.
- Phase0/닫힌1/열린1/phase2의 목표 합성 AST만 추출해 순수 검산했다. Source arm policy +0.8↔−0.8을 바꾸어도 목표·I가 같았고 이전 목표+2δ의 float32/native clipping이 정확히 맞았다. I는 zero로 초기화된 뒤 모든 source phase에서 갱신되지 않는다.
- 기존 5mm 속도 보정은 READY/닫힌 phase1/RECOVER에만 적용하며 열린 phase1은 원래 ENTRY/latched EXIT 목표다. Source geometry·phase·clock·감지기/성공기준, PREPARE, native POSITION/PD schedule, 왼팔 hold·finger21 source policy 및 free4 +0.2rad, physics/cleanup은 diff상 변경되지 않았다.
- [run_strike_incremental_approach.py:292](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:292): 연결/최종 report는 `integral_update_source_phases=[]`, 모든 phase I hold, source arm9 목표는 기록용이라고 명시한다. Actor30 계산·history 경로를 유지해도 실제 source30 action 전체 동등성을 주장하지 않는 계획 범위가 적절하다.
- [strike_incremental_approach_preserved_run.py:56](/home/ajou/yigyu/3/stability_adapter_2/strike_incremental_approach_preserved_run.py:56): wrapper는 새 trial module 연결만 바꿨다. 입력 SHA/소스 사본을 task import 전에 기록하고 종료 대조·argv 복원을 유지한다. 두 Python 파일 AST3.8·문자열 dict key 중복 검사를 통과했다.
- 해소된 선택 Suggestion: PI else 삭제로 읽히지 않게 된 `old_integral` 복사 한 줄을 실행 전 제거했다. `source_before_orphan_review/`에 이전 runner 원문 SHA `4996e4807788d4bfe96bccf70e98d254ca1625055363c23a3c532a74553eccef`를 보존했고 diff가 그 한 줄뿐임을 확인했다.

최종 검수 SHA256: runner `bdf142469647b884a3844d99730f57334c7158390f5fec5ab6b9224a534f00e9`; wrapper `10c4aa9d5a8ec2e85bc0fb2be5189636b5bcadb1e9be2b2ff6e10199313d1e31`; 계획 `23df959f7511c027ef04ff4ee27d69e4fcbf4e39b9f56c13ede367516397706b`. 사전 PASS는 실제 타현·회복·안정성·성공이나 물리 실행 완료를 인증하지 않는다.
