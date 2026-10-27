# 3조건 위치 목표 보정: native 실행 전 독립 검수

- 검수일: 2026-10-07
- 대상: `palm_position_residual.py`, `run_palm_position_compare.py`, 순수 테스트 및 승인된 `PALM_POSITION_COMPARISON.md`.
- 편집: 이 기록만. native 초기화·rollout·source query 실행 및 기존 frozen 산출물 변경 없음.

## 요약 판정: 문제없음

- Critical: 없음.
- Warning: 실제 refresh 결과의 Jacobian readiness 누락은 수정 확인 후 해결했다. 남은 finding 없음.
- Suggestion: 없음.

## 수식·제어 경계

- 왼팔 각 3열의 SO(3) left tangent 오른쪽 곱과 `J_linear - skew(source-COM) J_angular`가 승인한 source 위치 미분에 일치한다.
- augmented least squares는 위치 오차 배율 2와 regularizer 0.05 m/rad를 구현한다. 고정 축을 RHS로 이동하고 나머지 축의 bounded solve를 수행한다.
- delta bounds는 총 보정 ±0.15 rad, 기록된 native/C02 교집합, 직전 전달 목표 대비 ±0.02 rad를 delta 좌표로 합친다. runner는 실제 전달된 float32 목표를 다음 update의 previous로 사용한다.
- 최종 delta에 대한 `error*(raw-delta)>1e-12` 판정으로 이번 적분을 복구한다. blocked mask는 단조 증가하고 최대 25회 계산 후 종료한다. 오른팔은 RATE_PI와 같은 독립 계산을 사용한다.
- native 제출은 주요66관절의 목표각뿐이다. 몸통9·손가락42·하체의 목표를 유지하며 실제 상태를 고정하지 않는다. 기타 pose/state 재주입, 인위적인 기타 복원력 또는 gain 변경을 추가하지 않았다.
- 기존 PI 구현을 그대로 호출하고 states/trace/controls/contacts/leg_torques의 0.1초 prefix exact를 실행 후 확인하도록 구성했다. 실제 prefix 일치는 이번 코드 검수에서 아직 측정하지 않았다.

## 독립 검증

- 새 순수 테스트 4개를 실행해 통과했다: SciPy rotation 기반 source 미분, dense/fixed-axis solve, rate/cap/적분 복구, 위치 목적함수와 오른팔 matched 계산.
- 100개 결합 LS update의 자유/활성 축 KKT 조건, bounds/rate, 최종 blocked mask에 따른 적분 복구 및 25회 종료 한계를 추가 확인했다.
- 주입한 solver 실패가 예외를 발생시키고 integral/previous를 변경하지 않는지 확인했다. runner의 예외 경로는 failure 및 부분 배열을 저장하고 재전파하며 다른 controller로 대체하지 않는다.
- runner에 native state/pose setter 호출이 없음을 확인했다. CPU descriptor의 device/dtype/shape/null guard 이후, 환경 수명 안에서 실제 row를 복사한다.

## 수정 확인 및 최종 경계

`run_palm_position_compare.py` 93–94행은 refresh한 LH row의 finite/nonzero readiness를 검사하고 실패를 저장·중단한다. 155–156행의 완료 계약에도 이를 포함한다. runtime normal proxy의 유효성·위쪽 여부는 별도 관측값이며 잘못된 결과를 숨기는 plot/실행 계약으로 사용하지 않는다.

solve/anti-windup은 float64, native 전달은 float32이며 bounds/rate 허용 오차 2e-7 rad를 기록한다. 이 검수는 승인된 3조건의 구현·수학 검수다. 실제 초기 상태 일치, prefix·접촉·장력·손 위치·기타 안정성은 이후 native 원자료로 별도 검수해야 한다. 기록을 동결한다.
