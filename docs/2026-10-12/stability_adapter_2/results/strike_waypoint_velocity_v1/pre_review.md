# Waypoint 속도 감쇠 — 독립 사전검수

요약 판정: **문제없음(PASS)**. Critical / Warning / Suggestion 없음. READY-incremental runner 대비 새 runner/wrapper/계획의 변경만 읽었으며 native 초기화·physics 실행은 하지 않았다.

- [run_strike_waypoint_velocity.py:173](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:173): 실제 pick 원점을 각 시점의 기타 좌표로 변환한 연속 PLAY control 차분이다. 첫 측정은 v=0이고 이후 `env.steps/240` 시간 차를 분모로 사용한다. 이전 위치/시간은 열린 APPROACH에서도 갱신되므로 활성 분기 사이만 건너뛴 차분이 아니다. 각 advance는 기존 integrate의 4 physics steps 후 돌아오며 PREPARE/HOLD에서는 이 측정 함수를 호출하지 않는다.
- [run_strike_waypoint_velocity.py:177](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:177): phase0/닫힌 phase1/phase2만 −0.1s·v_G 보정을 적용하고 벡터 norm을 0.005m로 제한한다. 열린 phase1 보정은 0이다. 분기 AST만 추출한 순수 fixture에서 첫 0속도, 활성/비활성 gate, 4-step 시간 차, 5mm norm 제한과 servo 목표 합성을 확인했다. m/s·s·m 단위가 일치한다.
- [run_strike_waypoint_velocity.py:172](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:172): source waypoint는 사본이며 nominal/servo/측정 위치·시간·속도·보정을 각각 기록한다. 변경된 servo 목표는 adapter IK residual에만 사용된다. 원본 geometry 반환값, entry-distance 판정, source readiness/타현/회복 감지기 및 source clock에 쓰거나 전달하지 않는다.
- READY/닫힌 APPROACH/RECOVER의 이전 제출 목표+2δ 및 I 유지, 열린 APPROACH의 policy+PI, native bounds·60Hz 최종 rate clip·float32 제출, 네 finger residual·PD schedule·PREPARE·기존 물리/cleanup은 diff상 그대로다. 속도 유한성·norm 제한 검사를 추가했고 두 report의 계수·측정 범위 metadata가 실제 코드와 일치한다.
- [strike_waypoint_velocity_preserved_run.py:56](/home/ajou/yigyu/3/stability_adapter_2/strike_waypoint_velocity_preserved_run.py:56): 새 trial module 연결만 바뀌었다. task import 전 입력 SHA·소스 사본, 종료 대조 및 argv 복원은 기존 방식이다. 두 Python 파일의 Python 3.8 AST 문법과 문자열 dict key 중복 검사를 통과했다.

검수 SHA256: runner `7988c9d9af63897fc6f566f32ffc230a61f71598167b588a52115f1d18e67443`; wrapper `37a8b82fafc39ef37ffeddc8290081d2ca3f9555520bb7142b5cac2090151099`; 계획 `92218258f604a91de063610a714a3f009011e0285c50747a3cf5257b1134138a`.

20mm 초안의 소스·계획과 기존 사전검수는 `source_before_velocity_cap_review/`에 보존했다. 최신 변경은 norm cap·검사·metadata를 5mm로 통일한 것뿐이며 wrapper는 동일하다. 순수 포화 fixture에서도 5mm를 확인했다. 5mm<READY–ENTRY 깊이 차 9.5mm는 실제 충돌·조기 타현 방지 보장이 아니다.

이 v_G는 움직이는 기타 좌표의 저장 control 표본 간 위치 차분이며 순간 body 속도·DOF qdot 인증이 아니다. 사전 PASS는 실제 감쇠 효과·타현·안정성·성공이나 물리 실행 완료를 증명하지 않는다.
