# 자연 오른팔 V8 위쪽 기준점 비교 사전 검수

요약 판정: **문제없음.** Critical 0 / Warning 0 / Suggestion 0. V7→V8 변경만 읽기 전용으로 대조했다. 새 물리 실행·학습은 하지 않았다.

[runner V8:80](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v8.py:80)은 초기 human 전완 motor 목표에 world Z `0.012m`를 더한다. 나머지 변경은 계획 경로와 [offset 기록](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v8.py:90)뿐이다. 초기 q·기타 p/q·전완 local reference·point K1500/D25/cap30·관절별 posture K/D·native effort cap·owner window·POSITION69/상태 불변/Jacobian 속도 gate가 유지된다. 기타 pose setter·직접 기타 힘·부착을 추가하지 않는다. 인간 actuator 목표 한 점의 변경이며 기타 고정 목표가 아니다.

`source_target_local_G_m`은 기존 source 8mm 안쪽 참고점이다. 실제 `desired_motor_point_W_m`은 그 초기 world 변환에 +12mm를 추가한 값이므로 두 필드를 동일한 목표로 해석하지 않는다. 목표 속도는0이고 초기 world 목표는 유지한다. 이탈 래치는 관측만 하며 토크 차단이 아니다.

[계획 V8](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_RIGHT_ARM_REFERENCE_PLAN_V8.md:4)은 이전 완료 시험의 큰 위치·회전 이탈을 실패로 명시한다. 이번 작은 비교의 효과·자연스러움·안정화 성공은 코드 검수만으로 인증하지 않는다. 기존 후보 SHA는 이전 검수와 동일하다.

검수 SHA256:

- 계획 V8: `f80edb802998204e013119c55f7057b138ea3082b2a64d27d4c05e49b1851ce6`
- runner V8: `0da679294a31d97bf5a6176a52a0616b7265a3658b1533d94a28879e05418ef8`
- 초기 후보: `077ddd78562807651804cc989746ef55ae747d06100f18fcc80e846574a5cc4d`

이 새 리뷰 외 기존 파일은 수정하지 않았다.
