# V7 실제 pick 피드백 사전 검수

요약 판정: 문제없음. 새 실제 Cartesian 피드백은 기존 velocity 이후6개 effort에만 합성하며 원 목표·요청/최종 gate·75 보존 조건을 유지한다.

Critical: 0

## 확인 근거

- [V7:93](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:93)는 실제 RH:pick body origin의 pose와 COM linear/angular velocity로 local0 point 속도를 계산한다. [원 helper:11](/home/ajou/yigyu/3/stability_adapter_2/strap.py:11)의 offset=local−COM과 [V7 Jacobian:95](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:95)의 `Jv−skew(R*offset)*Jω` 부호가 일치한다. COM/origin 두 후보를 실제 J*qdot−pointVelocity로 대조하고 .01m/s 초과/비유한 Jacobian이면 중단한다. preceding controller의 원 refresh 경로 이후 같은 timestamp tensor를 읽는다.
- [목표 속도:100](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:100)는 currentG local 경로 도함수와 기타 actor의 point kinematics를 합쳐 `goalVelocity=vCOM+ω×R*(local−COM)+R*localDot`를 구현한다. world/G 좌표와 속도 기준이 일치한다.
- [힘 합성:104](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:104)는2~2.2초 ramp,4000N/m·40Ns/m, force norm20N을 적용한다. `J[:,EW6]^T*F`만 이전 최종6 effort에 더한 뒤 원 model cap으로 clip한다. 다른75 effort와 native state를 동일성 검사하고, 원 guarded 단일 human81 actuator 반환 경로를 사용한다. 기타 actor 힘/새 충돌체/attachment/state setter가 없다.
- V6→V7 diff는 추가 pick controller·로그/scope뿐이다. 원 close90/시간/기하/75 목표/IK requested 및 rate-final norm160/model/±1rad/3rad/s/finite·PD·gravity·proximal cap을 유지한다. 첫2초 ramp0이면 pick 추가분0이다. 원 velocity 이전/이후와 pick 최종을 순서대로 기록한다.
- [encode:115](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:115)는 velocity field를 pick 전 stage로 표시하고 새 pick_feedback_effort_rows를 실제 최종81로 표시한다. body/tracking도 최종 이전 stage임을 명시한다. V7 AST를 확인했다. 이번에는 물리 실행·소스 변경을 하지 않았다.

## Warning

- [경로 도함수:100](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:100)는 ε=1e−5s 중앙차분이다. piecewise-linear의 정착/횡단 경계에서는 양쪽 기울기의 평균이며 매끈한 연속 도함수가 아니다. 목표 속도 feedforward와 Cartesian velocity 피드백의 효과는 실제240Hz 원자료로 판정한다.
- [계획:8](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_PICK_FEEDBACK_PLAN_V1.md:8)의 원7점 source 감사를 재사용하는 것은 초기 기하/목표가 같다는 범위다. 새 finite task의 실제 궤적·접촉0·기타 drift·원 detector6줄 down/up·첫2초 동일성을 보장하지 않는다. 모델 marker의 kinematic RELEASE와 물리 손/기타 접촉을 구별한다.
- norm20N은 human joint torque를 만들기 위한 virtual force 요청 cap이다. 측정 contact force나 기타에 적용한 외력으로 설명하지 않는다. 합성은 이전 이미 clip된 최종6+task를 다시 clip하는 단계이며 velocity raw 요청을 포함한 모든 항을 한 번만 clip한 식과는 다르다. 이는 현재 계획의 '기존 최종6에 추가'와 일치한다.

## Suggestion

없음. 이번 코드/계획 사전 범위에서 native 시험을 막는 구현 오류를 발견하지 못했다. 실제 완료 원자료 검수는 후속 범위다.
