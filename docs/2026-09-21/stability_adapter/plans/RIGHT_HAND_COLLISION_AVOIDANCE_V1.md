# Right-hand collision avoidance v1

- [x] 몸체별 오른손 substep 접촉력 수집
- [x] `HOLD -> RETREAT -> PARK` 상태기 구현
- [x] 오른쪽 shoulder/elbow/wrist 9-DoF Jacobian 후퇴 구현
- [x] 왼손 action과 독립적인 PD target 합성
- [x] REACH/GRIP 진단 필드 추가
- [x] 순수 함수·계약 테스트
- [x] GPU 접촉/비접촉 smoke와 로그 확인

성공 기준:

1. 접촉이 없으면 오른손 target을 변경하지 않는다.
2. 0.2 N 이상 접촉 시 순접촉력 방향으로 오른팔이 후퇴한다.
3. 0.05 N 이하가 30 frame 유지되면 PARK로 전환한다.
4. `R_Thorax`, 왼팔, 몸통 action 소유권은 변경하지 않는다.
5. 40 N 이상 접촉은 회피로 숨기지 않고 기존 안전 실패 조건에 남긴다.

검증 결과:

- CPU 상태기/소유권 계약 테스트 5개 통과.
- 초기 환경·REACH·GRIP 영향 범위 회귀 테스트 70개 통과.
- GPU Isaac Gym smoke에서 1 N 접촉 주입 시 `RETREAT` 진입.
- 오른팔 target 최대 변화량 `0.007807 rad`, 9개 대상 관절과 전체 상태 유한성 확인.
- 비접촉 physics step의 측정 오른손 접촉력 `0.0 N` 확인.
- 40 N 이상 오른손 접촉은 REACH 성공과 GRIP snapshot 승격을 모두 차단.
