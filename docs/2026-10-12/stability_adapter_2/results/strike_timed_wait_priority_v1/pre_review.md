# 시간창 전 R9 대기 제어 사전 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. 실행 전 코드 변경 범위 검수이며 새 native 실행을 하지 않았다.

- `run_strike_timed_wait_priority.py:182–202`: 실제 source phase1이면서 original `approach_open=false`인 경우에만 기존 RECOVER 증분 합성을 공유한다. 최종 R9 목표는 직전 `env.target`에 `2*clip(IK fit−actual, ±0.15rad)`를 더하고 native bounds에 제한한다. 새 policy absolute R9 목표를 해당 분기에 더하지 않는다.
- closed phase1 및 RECOVER에서는 `ready_integral`을 갱신하지 않는다. phase0/열린 phase1의 기존 policy+bounded PI, phase2 RECOVER gain2는 유지된다. actor는 그대로 계산하고 R9 외 policy 손가락21의 목표 소유권은 유지된다.
- 이전 timed-entry runner와 diff를 확인했다. READY3/ENTRY4/EXIT5 선택, source 시간 helper·clock/window/detector·motor phase, 감쇠 schedule, 최종 rate/native bounds·target 제출·history 역변환·물리 적분은 변경되지 않았다. 초기/실제 state overwrite나 기타 외력 추가도 없다.
- 보존 wrapper는 실행 module 이름만 달라지고 native import 전 입력/소스 봉인·종료 재대조 및 argv 복원을 유지한다. 두 Python 파일은 Python3.8 AST 검사를 통과했다.

검수 SHA256:

- runner: `5abc50c214ff8e64be727a1e77c058fdbf3002e8b8cc31b073ee320ea08eaf97`
- wrapper: `058970bc46e638263a106a032c49fe94741ba2bb9bbff34525be58f03572b93d`
- 계획: `b466b8697aa5a7014601175bff40f2a3a786aefbedc085f611c13310797d6e42`

최종 목표각의 FK 예측은 미관측 미래 실제 자세나 인과의 인증이 아니다. READY 대기 응답, 첫 hit·회복까지 이전 실행과 동일성, 이후 timely hit 및 전체 연주 진행은 실행 후 검수 대상이다. 사전 actionable finding 없이 기록을 동결한다.
