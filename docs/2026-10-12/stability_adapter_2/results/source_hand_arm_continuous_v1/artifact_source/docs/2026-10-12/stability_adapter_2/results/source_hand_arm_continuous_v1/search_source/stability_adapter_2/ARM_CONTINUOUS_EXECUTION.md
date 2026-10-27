# 연속 팔 탐색의 수치 목적함수와 실행 계약

SOURCE_HAND_ARM_CONTINUOUS_PLAN.md를 실행한다. 이전 goal turn은74개 제안/68개 형상 평가를 완료하고 clear 없음 및 다음 방향을 확인한 진전이다. 이번 단계는 같은 실측 손가락 계층을 유지한 arm12 조합과 실제 자유 기타 검증을 연결한다. Source 호환 자체를 최종 목표로 삼지 않는다.

## 입력과 범위

fixed_strap_source_hand_initial_v1의 실제 native 초기 state/81각/원 left33 offset을 기준으로 한다. 두 시작점은 원 baseline과 source_hand_arm_position_v1 row47의 실제 float32 delta다. 12개 팔각의 원 기준 ±.15rad를 초기·held의 effective bound 및 Wrist_x 명령 ±.005rad와 교차한다. 실수 구간의 양끝을 안쪽 float32 값으로 표현하고, 조립된 초기/held/명령 양끝이 실제 범위 안인지 다시 검사해 검색 구간을 정한다. 이는 가능한 입력 구간의 계산이며 후보 목표를 clipping하는 방식이 아니다. 다른69각·목표/손가락 상대 계층/기타 fullstate/LA/PD/몸통9/root하체/최종66권한은 유지한다.

## 목적함수

각 Powell 호출은 실제 float32 초기각과 float64 offset 합→float32 held 목표로 평가한다. HG 보고 임계값은 기존대로 LP 공통내접반경1e−7m다. 다음 값은 모두 무차원 수치 목적함수의 구성항이며 실제 힘/보상이 아니다.

- 충돌항: `1e6 * Σ (보고된 HG 공통내접반경_mm)^2`.
- 지지 접근항: `palm 옆면 patch 거리상한_mm^2 + thumb3 후면 patch 거리상한_mm^2`. Feasible witness upper bound를 사용하며 optimizer success와 최단거리 인증을 동일시하지 않는다.
- 자세 변화항: `.01 * Σ (원 baseline 대비 실제 초기각 delta_rad/.15)^2`.
- 평면 선호항: `.1 * (1-abs(palm_normal · neck_side_normal))^2`.

초기/held 범위 위반은 geometry 전에 제외하고 위반값/bound와 raw81입력을 남긴다. Palmup≤0 또는 source 계층 identity 실패는 hard invalid로 표시한다. HG 교차가 없는 평가에서는 별도 cross-hands/self1188 전체를 검사하고 교차가 있으면 hard invalid다. Hard invalid 목적값은 위 구성항 합에1e12를 더하며 source_clear=false다. 모든 평가의 부품 값·입력·교차·patch interval·identity 결과를 JSONL에 즉시 flush한다. Geometry 미평가는 null이며 clear나거리0으로 표현하지 않는다.

## 호출 수·선택·실제 검증

각 시작점에 bounded Powell `maxfev=400, xtol=1e-4, ftol=1e-8`을 한 번 호출한다. 첫 목적함수 평가가 해당 seed 재현 검사다. 두 seed를 합해 최대800평가이며 optimizer의 실제 nfev와 저장 행 수를 대조한다. 동일 float32 입력의 반복 호출도 실제 호출 수에 포함해 기록하며 별도 재시작하지 않는다. 최대 평가수 종료는 실패/성공의 물리 판정이 아니다.

전체 sourceclear 중 patch 거리상한 제곱합→초기각 delta L2→평면 정렬→평가 순서로 한 후보만 고른다. 별도 predicted pose와 proposal/trial을 저장하고, 실제 native state로 replay하지 않는다. Native 직접검사를 통과한 같은 초기화만5초 실행한다. 실제 비교에서는 초기/후기 기타 p/q·관절·손 접촉·영상·source prediction 오차를 확인한다. Clear 없으면 native0회로 끝내고 원 quiet 실제5초 기준의 물리 제어·연주 목표 전환 설계로 복귀한다. 고정 LA 본선, 자유 기타·실제 관절 PD, 기타고정/손부착/지속state덮어쓰기 금지는 동일하다.

실행 전 source·leaf·입력 SHA와 사본, 실행 후 같은 SHA·terminal reason을 보존한다. 결과 경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1 이다. 기존 소비 소스/계획/산출물은 수정하지 않는다.
