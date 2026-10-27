# 대기 목표 actual-angle rebase 사전 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / Suggestion 없음. 실행 전 코드·계획 범위 검수이며 native 초기화·물리 실행을 하지 않았다.

- `run_strike_timed_wait_rebase.py:182–203`: 실제 source phase1/닫힌 original approach window에서만 R9 목표 기준을 직전 actuator 목표에서 실제 관절각으로 바꾼다. actual R9에 local IK correction을 1배 더한다. fit의 bounds가 actual±0.15rad∩native이고 correction도±0.15rad이므로 요청 목표는 bounded fit에 해당한다. 최종 전달 목표는 기존 rate/native clipping 뒤의 값이다.
- actual DOF 값은 계산에 읽을 뿐 state setter로 쓰지 않는다. 닫힌 phase1의 I는 이전값을 유지하고, phase2는 이전 actuator 목표+2δ, phase0/열린 phase1은 기존 policy+PI를 유지한다. actor 손가락21축과 최종 target/history 소유권도 유지된다.
- 이전 timed-wait-priority runner와 diff를 확인했다. geometry/time helper/clock/window/detector·source motor phase·PD schedule·rate·기타 목표·물리 적분 변경은 없다. wrapper 변경은 실행 module 이름뿐이며 import 전 입력/소스 보존과 종료 SHA·argv 복원이 유지된다. 두 Python 파일의 Python3.8 AST를 통과했다.

검수 SHA256:

- runner: `c0c58a112c7b3bd09920a8bd035d14d80708ca6e5bdf578cca92eb194491840e`
- wrapper: `dd82b0ca438ee58a3b7a37992667002478cf93408484124eccd4865d226355f4`
- 계획: `ccf131c432bee8694df3bb4f6e356e5bd231767442fc3206b9ef6602f1c48cf0`

실제 READY 유지·목표 추종·첫 hit/회복 prefix 동일성·이후 timely hit는 아직 실행 후 검수 대상이다. 코드의 목표 정의를 실제 자세 성공이나 실패 원인의 확정 근거로 보지 않는다. 사전 actionable finding 없이 기록을 동결한다.
