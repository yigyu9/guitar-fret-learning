> **HISTORICAL — 통합 이전 기록.** 본문의 수치·명령·검증 결과는 작성 당시 기준이다. [현재 StabilityAdapter 안내](../../../../stability_adapter/README.md)를 먼저 읽는다. 보관은 미완료 검증의 완료를 뜻하지 않는다.

# 지지 유지·복원 환경 구현

사용자가 설계 구현과 테스트를 요청했다. 기준 설계는
`docs/2026-09-14/archive/STABILITY_SUPPORT_CURRICULUM_DESIGN.md`이며, 현재 support-v1 원본과 체크포인트를 보존한다.

- [x] 새 순수 보상·접촉 증거·유지 tracker와 CPU 회귀 검사.
- [x] 별도 S1~S4 runtime·초기화·470D 관측·8 history·학습/평가 진입점.
- [x] S0 reference 진단·초기 자세/접촉 확보 가능성 검사. 19후보 중 지지 검증 통과0개.
- [x] CPU/GPU 경계 검사, 짧은 학습·재개·영상 평가.
- [x] 독립 변경 검토와 수정, 사용법·실험 결과·장기 학습 가능 여부 문서화.

역할: 순수 보상/계약 helper, S0 진단 도구를 독립 구현하고 주 작업에서 simulator/runner를 통합한다.
S0가 통과하지 않은 reference로 장기 학습을 허용하지 않는다. 진단용 미검증 초기화는 별도 명시 모드로만 제공한다.
실제 유지 reference를 찾지 못한 경우도 검사 결과를 숨기거나 지원 성공으로 표시하지 않는다.

결과: [구현·시험 보고서](../../../2026-09-14/archive/STABILITY_SUPPORT_HOLD_IMPLEMENTATION.md).
코드 구현·시험은 완료했으나 물리 지지 reference 확보와 단계별 학습 성능 검증은 남아 있다.
