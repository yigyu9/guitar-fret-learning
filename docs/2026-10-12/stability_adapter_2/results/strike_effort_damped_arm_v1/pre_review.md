# Strike EFFORT R9 spring 사전 검수

요약 판정: 문제없음 — 사전 검수 PASS. Critical 없음 / Warning 없음 / Suggestion 없음. 실제 신규 native 실행·연주 반응과 과거 prefix 동일성은 아직 이 판정에 포함하지 않는다.

- `run_strike_effort_damped_arm.py:71–79,146–172`: 직전 rebase 대비 변경을 대조했다. PREPARE에서는 기존 POSITION을 유지하고 첫 source PLAY advance에서 controlled R_Shoulder/Elbow/Wrist 9개만 EFFORT/stiffness 0으로 바꾼다. Sim DOF 81·R9 membership 및 native full-properties readback/state 보존을 검사한다. 기존 damping은 source phase1에서 1/4, phase0/2에서 baseline이다. 다른 72개 POSITION properties는 그대로다.
- `:103–122`: 매 physics step 직전 실제 q를 읽어 `clip(saved_kp*(logical_final_target-actual_q), ±saved_effort_limit)`를 계산한다. CPU float32 tensor를 GraphicsGym→NoStrapGym→native API로 전달하며 lifetime을 유지한다. R9 외 72요소는 0이고 torque bounds/finite·setter 상태 보존을 검사한다. 별도 velocity 토크·몸체 force·실제 state write는 추가하지 않았다. Raw에는 요청 토크와 같은 시점 actual/target이 기록된다.
- 기존 60Hz 목표 합성·rate/native bounds·source policy finger21·왼팔12 hold·Thorax/other36·actual-angle waiting IK·RECOVER gain2·clock/detector/history 분기는 diff상 유지됐다. HOLD에서도 마지막 logical 목표로 spring을 계산하고 마지막 damping schedule을 유지하며 source clock/history는 진행하지 않는다. 기타는 자유·스트랩 OFF·root/하체 고정 조건이다.
- `:320–336`: torque/controls/trace를 close/encode 전에 저장하고 종료·인코딩 예외는 cleanup_failures로 남긴다. 파일 저장 자체의 완전 실패까지 보장하는 계약은 아니다. Wrapper 변경은 실제 runner 선택이며 기존 사전 입력 SHA/source_before와 종료 SHA·argv 복원 경계를 유지했다.

두 신규 Python 파일의 AST Python3.8 검사를 완료했다. native 초기화/physics 실행은 0회이며 기존 소비된 코드·원자료는 수정하지 않았다. 요청 spring 토크는 측정 drive/total torque가 아니고, 짧은 EFFORT damping probe 결과를 전 관절의 damping 모델·연주 안정성·원본 POSITION+외부 torque와의 동등성으로 확대하지 않는다. PREPARE prefix 및 첫 actor 관측은 실제 실행 후 별도 대조해야 한다.

확인 SHA256: runner `75e52c82776b7c05842d0471aa4d90199cbe5684880dd0e8c4b198bca00266af`, wrapper `e582461c11ea9f46922666f593b9cc6951e2e9bc890e75d4a6e430f506a23155`, 계획 `305f0f9fbc8683cde5d4d2da9be778efec027d84e2014189e063e8faa6427adb`. 이 사전 검수는 동결한다.
