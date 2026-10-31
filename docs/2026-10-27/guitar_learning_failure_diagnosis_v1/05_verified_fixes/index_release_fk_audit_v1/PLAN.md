# 해제 목표 설계 전 원FK와 실제 검지 자세 검증

기존 실패 진단 계획의 다음 단계다. 새GPU·학습 없이 이미 저장된 두 조건의 env0 실제 관절각과 native body pose를 대조한다. 기존 source FK가 검지 MCP2에서 충분히 맞는다는 가정을 먼저 검증하며, 결과를 본 뒤 유한 해제 목표 설계 방법을 정한다.

1. 원무잡음/잡음 reference의 `trace_env0_episode0.npz` 각354행과 `release_clearance4.npz` env0 해제창58행을 시계·실제 distal pose로 정합한다. 검증: 다른 환경/다른 tick을 섞지 않고 원준비 SHA와 입력 바이트를 확인한다.
2. 현행 `full_fk`를 원prepared actual q(목표각 아님)에 한 번 보정해 그대로 실행한다. 전체354행과 해제창58행에서 wrist/palm과 index1/2/3의 native palm-relative 위치·회전을 비교한다. 검증: 초기 실제q에서 자기일치·실제q와drive target 분리·유한성·quaternion 정규화·단위 확인. 준비자세만의 자기일치를 독립native 동작 검증으로 해석하지 않는다.
3. 원128개 안쪽표본의 world/guitar 좌표를 실제 distal pose와 FK distal pose로 각각 계산하고 차이를 mm로 보고한다. 실제 측정된 여유와의 비교를 통해 해제 목표의 기하 최적화에 기존 FK를 써도 되는지 판단한다. 패드/접촉 gate를 새로 정의하지 않는다.
4. 결과·근거·한계를 그래프와 문서로 저장하고 별도 change-reviewer의 읽기전용 검산을 받는다. 이 검증이 맞지 않으면 MCP2 수학/관계만 다음 최소 단계로 조사하며 팔용 Jacobian을 일반화하지 않는다.

원9보상·목표·모델·분포·음악/해제기준·물리/충돌/가동범위·활성소스·기존 원자료를 수정하지 않는다. 현재 기본 J33/자유기타/67음 성과나 전체 피부·실제 줄압력으로 확대하지 않는다. 원상태와 관절각이 모두 있는 env0만 검증하고 다른3환경의 q/손바닥 pose를 추정하지 않는다.

- [x] 제한된 CPU 분석 구현과 의미 있는 자체검사 — `analyze.py`, returncode0, 전후SHA125개 불변
- [x] 실제 저장 native pose 대조와 이격 여유에 대한 판단 — `RESULTS.md`, `results.json`, `series.json`, `fk_native_comparison.png`; 프로그램 완료와 FK정확성 실패 구분
- [ ] 독립검수·계획/상태/결과 문서 갱신
