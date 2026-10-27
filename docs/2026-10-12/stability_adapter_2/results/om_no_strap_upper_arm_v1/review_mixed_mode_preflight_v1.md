# POSITION·EFFORT 혼합 모드 사전 검수

판정: **문제없음**. Critical 0 / Warning 1 / Suggestion 0. 실행용 v12/V13과 직전 v11의 변경 부분, 새 사전 SHA 및 최초 실패 기록을 읽기 전용으로 검토했다. 추가 native 실행·학습·원본 수정은 하지 않았다.

- [step:48](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v12.py:48): 기존 계약의 rate/model codec과 단일 target owner를 사용한다. POSITION69 readback exact, 전체 native state 불변, 전체 readback finite를 모두 요구한다. 오른 EFFORT12의 POSITION readback만 구동 검증에서 제외하고 논리 목표·readback·두 판정 bool을 별도 기록한다.
- [owner 및 physics:57](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v12.py:57): target 제출 window와 physics owner를 각각 finally에서 닫으며 기존 4physics와 tick당 effort1회 경로를 유지한다. CPU 모의 검사에서 control당 setter1회·effort4회·physics4회, closed window/owner 및 horizon 이후 제출 금지를 확인했다.
- [기록:106](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v12.py:106): position_command_rows를 별도 저장한다. 기존 source/guard/construction·Jacobian/torque 제어·step_physics 함수는 v11과 AST가 동일하다. 물리 목표나 torque cap을 변경하는 코드가 아니다.

실제 factory/step 함수를 native import 없이 CPU에서 실행했다. 정상 readback과 오른12만 다른 readback은 통과했다. POSITION 관절1개 불일치, native state 변이, 오른 readback NaN은 각각 physics0·effort0에서 거절됐고 두 bool이 원인에 맞게 기록됐다. 계약 생성과 기존 effort 진단의 제한 범위는 이전 사전 검수를 유지한다.

Warning 1 — [계획 첫 문단](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V13.md:3)의 readback 원인 설명은 가설로 제한해야 한다. [실패 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/failure.json)은 `target readback mismatch or command changed state`라는 **결합 검사** 실패만 보여준다. 저장 trace는 step0뿐이고 effort 행/호출은0이다. 최초 실패가 readback 불일치인지 state 변이인지 아직 확정할 수 없다. 다음 실행의 분리 bool로 판단해야 한다.

[새 사전 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/mixed_mode_preflight_inputs_v1.json)의 두 SHA가 현재 파일과 일치한다.

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v12.py | 17d3ccc23df050b214a1025b975e2645d741e7a4f86f8e96b28d45da1e50ebd1 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V13.md | cf6f9f0f8905e88d7210e9831008d18c7525b6355f0a4a64a766809e56cf1470 |

실행 차단 사항은 발견하지 않았다. 오른 POSITION readback을 제외해도 실제 상태 불변 검사는 완화하지 않는다. 오른 logical POSITION target은 actuator effort나 실제 관절 추종값이 아니며, native effort 적용·Jacobian 속도 관계·접촉·기타 유지 성공은 아직 별도 검증 대상이다. 지정한 새 리뷰 파일만 작성했다.
