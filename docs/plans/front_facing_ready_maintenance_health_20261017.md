# 유지 보정 이후 관절 건강 검사 범위

2026-10-17 KST. 요구조건은 `paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/REQUIREMENTS_v2.md`이다. 원 `assess_joint_health_v3.py`와 기존13개 수치 예산 통과·엄격한 EPS0 실패·원인 미확정은 그대로 보존한다. 새 후보가 아직 선정되지 않았으므로 이 문서의 실제 새 검사는0이다.

새 몸통/왼손 유지 보정이16초 뒤 적용되므로 원 정지창11–13/13–15초의 고주파 분석만으로 보정 후 제어를 인증하지 않는다. 향후 새 건강 분석 버전에서 baseline17–19/19–21초의 실제240Hz 관절 상태를 같은 detrend/Hann/10Hz 초과 RMS 수학으로 추가 검사한다. 각2초 half-open480표본이며 전105채널의 RMS≤0.001rad를 요구한다. 타현이나 해제/접근/닫힘 구간을 정지로 잘못 분류하지 않는다. 유한 유지 목표의 미세 보정과 실제 관절 고주파 운동은 구분한다.

- [ ] 원97축 bounds 초과0.001rad·zero8 초기 기준 차0.0001rad·native 속도10rad/s 수치 예산을 전 실제 실행에서 동일하게 확인한다. 원 EPS0 상태·제한 의미/원인 확정 여부는 별도로 기록하며 예산 통과로 덮지 않는다.
- [ ] 원 정지창과 새 보정 후 정지창을 각각 기록한다. 새 구간이 없거나 누락되면 baseline 후속 검증을 통과로 설명하지 않는다.
- [ ] 목표/실제q/native dq/외부 effort 명령/native 센서/PD stiffness·damping·cap을 구분한다. 원 첫0step의 센서·접촉이 미갱신임을 보존한다. 새 baseline 정지17–22초의 command/sensor 기록을 함께 연결한다.
- [ ] 실제 schema CPU/원 건강 수학 재사용 범위와 입력SHA를 확인하고 독립 검수·Root ACK 후에만 새 output으로 실행한다. 새 관절 gain/cap/solver 변경이나 기타 직접 보조 힘을 도입하지 않는다.

추가 정지5초·core·발·모든 source·수동 조건·압현 준비와 AND한다. 이 검사만으로 전신 안정화, 원 limit 잔차의 정확한 SDK 원인, 자유Root 균형 또는 최종 채택을 주장하지 않는다.
