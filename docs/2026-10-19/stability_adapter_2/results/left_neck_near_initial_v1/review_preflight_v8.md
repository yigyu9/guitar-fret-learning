# 사전 검수 — 현재 기타 기준 왼손목 위치 추종

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 기존 초기 필수 검사와 안전 guard를 유지하는 bounded 5초 정지 진단을 막는 변경 코드 오류는 발견하지 않았다. 실제 추종·접촉·pair 전환 결과는 미검증이다.

- [helper3:22](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:22)는 t0 실제 L_Wrist origin 위치의 G-local offset을 저장한다. [위치/속도:38](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:38)는 현재 자유기타 pose로 목표를 변환하고 `v_COM + ω×R(local−COM)`으로 두 점의 속도를 계산한다. body-origin pose와 COM linear velocity 규약에 맞다.
- [Jacobian:42](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:42)는 COM frame에서 `J_origin=J_linear−skew(R(−COM))*J_angular`, origin frame에서는 원 J_linear를 사용한다. native origin 속도와 J*qdot 오차가 .01m/s를 넘으면 중단한다. 기존 controller가 먼저 Jacobian을 refresh하며 변경 코드에 추가 물리 적분은 없다.
- [합산:48](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:48)는 `1000*(목표−현재)+30*(목표속도−현재속도)` 가상 요청의 norm을30N으로 제한한다. Jᵀ 요청의 왼12 성분을 기존 unclipped left gravity+scalar 요청에 더하고 최종 모델 effort cap으로 clip한다. 오른 contribution은 그대로 두며 양팔24 owner/57 POSITION 및 tick당 한 번의 human81 effort 제출을 상속한다. 기타 직접 힘·부착·상태 setter는 추가하지 않았다.
- [활성 조건:47](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:47)은 정지 모드에서는 전체5초, pair에서는 steps<480만 true다. runner의 첫 PLAY tick120과 task 종료 step480이 맞는다. 기존 원 actor firstdone/horizon 규칙은 그대로다.
- [기록:55](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:55)는 부모의 합산값을 추종 전 값으로 명명하고 최종 actual81을 tracking rows에 별도 저장한다. encode는 부모의 이전 scope를 피하여 EndpointRecording 경로로 저장한다. scene3는 helper import만, runner5는 mode flag 설정·import·report 설명만 변경했다. 초기 geometry/PD·mass/contract 및 single target submission 규칙은 이전 검수 범위대로 유지된다. 3Python AST 검사는 통과했다.

Warning 1 — wrist origin의 위치 한 점을 추종한다. wrist 방향·손가락 배치·6facet 간격이나 cooked 비접촉을 보장하는 제어가 아니다.30N은 가상 요청 norm이고 실제 손/기타 접촉힘이 아니다. 정지 진단에서도 실제 면·접촉·기타 변화와 함께 평가해야 한다.

Warning 2 — pair step480에서 task 요청을 즉시0으로 만들므로 토크 불연속이 생길 수 있다. 정지5초에서 추종 항을 계속 켠 결과는 task OFF 이후 양손 전환 성공의 증거가 아니다. 원본 firstdone과 안전 종료를 유지하여 준비·PLAY·검열 범위를 구분해야 한다. 앞선 Jacobian·중력 모델 및 60Hz sample 안전 검사 한계도 유지된다.

검수는 계획V9·helper/scene/runner diff·좌표/속도 수식·상속 제출/기록 경로·AST에 한정했다. 추가 native/추론/학습과 다른 담당 파일 수정은 하지 않았다.

검수 SHA256:

- 계획V9: `9531c8b0b6af74e6f407adef14fc50bf0eedb44de0c54428b78b5f88c55432fe`
- helper3: `bcbe43d81be7ab107cb899a73763dfdcfb50be97b5c4217b6467e28b7e58f72e`
- scene3: `cd5e2e4aaa3423e78f4e61deda6fd13de3f657a694c8fe1b34092b90af984123`
- runner5: `b8662e0c4f56bd0d7f588f726ff0d53055d9938ca6e3ca005b18a0d21b223ddd`
