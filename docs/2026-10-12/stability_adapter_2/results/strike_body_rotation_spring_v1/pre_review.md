# Child-frame 회전 spring 사전 독립 검수

요약 판정: **문제없음 / 사전 PASS**. 남은 Critical·Warning·Suggestion 없음. 검수 중 native 초기화·물리 실행은0회다.

- `run_strike_body_rotation_spring.py:76`의 XML Shoulder/Elbow/Wrist3그룹이 native R9 index51–59와 같은 순서이며 basis는 각각 X/Z/Y 열로 구성된 orthonormal B다. 저장 기준 초기 native parent-relative 회전과 q로 구성한 `rest=Exp(Bq0)⁻¹ Rrelative0`가 초기 목표 q0에서 실제 회전을 재현함을 독립 확인했다.
- `:125`의 실제 회전은 같은 직전 physics 상태에서 읽은 parent⁻¹child이고 목표는 `Exp(B final_target_q) rest`다. `log(actual_relative⁻¹ goal_relative)`는 actual child-frame 오차이며 B.T 변환·original kp 곱·float32 요청·기존 effort clipping 및 다른72요소0의 연결이 맞는다. 순수100개 회전 사례에서 동일 목표 오차0, world 회전 불변성 최대오차1.3322856994638522e−15rad 및 양의 kp 가정의 오차 정렬을 확인했다. 저장 `spring_math_check.json`의 현재 runner SHA도 일치한다.
- 기존 EFFORT damped-arm 대비 요청 torque의 오차 정의·기록 metadata만 변경했다. Source policy+PI 목표, closed wait actual IK, RECOVER 이전 목표+2δ, finger21·왼팔·PD damping schedule·source clock/detector·성공 조건은 그대로다. Soft orientation5 cost는 추가하지 않았고 body/G pose·velocity 쓰기나 기타 힘·부착은 없다.
- Wrapper의 실제 모듈 연결·사전/종료 입력 SHA·argv 복구, 실패 시 raw 우선 저장과 cleanup 기록 구조를 확인했다. 두 Python 파일 Python3.8 AST가 통과한다. `human_rotation_spring.json`과 physics별 기록은 basis/rest 및 actual/goal relative quaternion·오차를 남겨 후속 독립 재계산이 가능하다.
- 관련 velocity 감사 README/summary는 동일 snapshot의 `Rchild Bv` 근사와 qdot·Jacobian·force duality 미인증을 명시한다. 이 spring의 native effort 입력이 해당 child tangent와 공액이라는 사실은 검증되지 않았고 계획에도 후보로 한정되어 있다. 따라서 이 PASS는 제한된 실험 구현의 수학·경계 검수이며 물리 torque 방향·폐루프 안정성의 PASS가 아니다.

확인 SHA256: runner `42690ff938ab8defd2c64e9f1d78c9fbc5338ca1d4c10796bd33a503d0eff6c5`, wrapper `70d58625e22ccd158a96a0a0d7912a713fd3147585ede75d1a79525968669f48`, 계획 `6b59c1dc3cef005a76cd0f722aa808bf38b3392faa9c6a7a431eb76d79ebf1a7`.

실제5초 native 결과·초기/PREPARE prefix·요청 torque와 기록 상태의 수치·영상·입력 보존 및 연주/지속 지지는 실행 후 별도 검수한다. Source/native CPU/GPU 동등성은 인증하지 않는다.
