# 기타 기준 geometry PI 사전 검수

요약 판정: 문제없음 — 수정 후 사전 검수 PASS. 미해소 Critical 없음 / Warning 없음 / Suggestion 없음. 현재 단계의 실제 물리 실행·연주 반응은 아직 검증하지 않았다.

- 해소된 Critical — `run_strike_effort_geometry_pi.py:223,231`: 최초 소스는 antiwindup preview만 actual 기준이고 실제 제출은 policy 기준이어서 의도한 팔 제어가 적용되지 않았다. 현재 두 곳 모두 `actual[controlled_arm] + correction` 기준으로 일치한다. 최초 runner/계획은 `source_before_pre_review_fix/`에 보존했고 소비 전 수정이다.
- 원 EFFORT-arm 대비 diff를 검토했다. READY phase0·열린 APPROACH phase1에서만 R9 목표의 base를 actual로 바꾼다. Policy R9는 기록만 남기며 policy finger21 POSITION 목표를 유지한다. P/I/합 bounds와 I 증가·rollback, native/rate clipping은 같은 actual base의 preview·최종 목표에 적용된다. 닫힌 APPROACH의 actual-angle IK/I 유지, RECOVER의 previous target+2δ/I 유지, 60Hz clock/detector/geometry와 PREPARE는 그대로다.
- R9 EFFORT 240Hz capped kp spring·기존 native damping schedule, other72 POSITION/zero explicit torque, 자유 기타·스트랩 OFF·고정 root/하체·checkpoint/학습0 범위는 직전 사전 검수와 diff상 동일하다. Wrapper는 실제 module 선택만 변경했고 사전 input/source SHA·종료 대조·argv 복구와 raw/cleanup 보존을 유지한다.
- `check_strike_geometry_pi_goal_owner.py`와 `numerical_goal_owner_check.json`의 3 SHA 및 AST 추출 회귀를 독립 대조했다. Policy만 +0.8↔−0.8로 바꾸는 세 경우에서 수정 전 desired/I/blocked/preview 묶음은 모두 비불변이고 현재는 모두 불변이다. 느린 native 실험 없이 제출 기준 버그와 수정 효과를 확인했다. 세 신규 Python 파일 AST Python3.8 검사도 통과했다.

확인 SHA256: runner `ba248c3f1a366c97aef4338f2aff549838e0aaf4c6ec1ff31ee293aff0bd740d`, wrapper `0493041c89296333a4ff72eb90de29432833a3578900880df7c2e12fff6ad16c`, 계획 `361c3dc696bdf0191aeecf35ac8a20c7d8aad68f48edfaf41f6f9f0894250dec`, 회귀 producer `196f35d3cf1c2e82148a8c0ea06948263c6f86616115dba570c81fc6f6b4f74b`.

검수는 소스 diff·AST·순수 NumPy 수치·SHA 확인이며 Gym import/native 초기화/physics는 0회다. Actor 전체30 행동의 원래 actuation 동등성·지속 지지·기타 안정성·연주 성공은 인증하지 않는다. PREPARE/첫 actor 관측 및 실제 목표/토크는 새 실행 후 별도 대조해야 한다. 이 사전 검수를 동결한다.
