# 접촉 구간의 손·기타 유한시간 응답 측정

## 목적과 이번 결정

alpha .40은 양의 손바닥 raw lambda가 없고 .45에서는 step2에만 생겼다.
.40→.45에서 기타 최대 이동/회전은5.048mm/.967°→5.341mm/1.006°로 커졌다.
손 접근만 최적화하면 기타를 밀어낼 수 있으므로 두 응답을 함께 식별한다.
.45는 접촉 구간 측정 기준일 뿐 새 초기 자세나 최종 제어로 채택하지 않는다.
평행은 부드러운 선호이며 실제 넥 지지와 기타 초기 p/q 유지가 우선이다.

## 불변 조건과 실험

초기 humanoid q, 기타 p/q, 절대LA1.1018469719600776m, 기존PD, 몸통9와
오른팔/손가락 목표, root/하체 물리고정과 self-collision ON을 유지한다.
왼팔12 PD 목표의 constant bias만 바꾸고 66관절 합성 경로/initial±.3rad∩native
범위를 지킨다. 기타 자유·중력·수동 strap이며 고정/부착/상태 덮어쓰기는 없다.

- [ ] 1. 이전 경계 분석과 실제 소비 입력을 읽기 전 SHA로 봉인한다.
  .45 bias baseline, 12개 단일축 .005rad probe, 독립 heldout .001rad 조합을 생성한다.
  +.005가 목표 범위를 벗어나면 해당 축은 −.005로 한다. 실제 float32 목표차로 계산한다.
- [ ] 2. 기존 동결 runner를 수정 없이 재사용한다. 각24step(.1초), 계획14init/336steps다.
  실행별 종료/입력/로그를 기록하며 실패하면 남은 실험을 멈춘다. 기존 .45 저장자료와
  새 baseline의6개 raw도 비교해 반복 재현성을 확인한다.
- [ ] 3. baseline−probe가 아닌 명시적 (probe−baseline)/실제 전달 목표차로
  손 task6과 기타 world 오차6의 유한시간 응답 행렬을 각각 구한다.
  손 task=[목표−손 위치m3, .08×법선 회전벡터rad3], 기타=[실제−초기 목표 위치m3,
  (R_actual R_goal^-1)의 world rotation vector rad3]다. Euler/DOF 성분 차가 아니다.
  heldout의 실제값과 baseline+행렬×전달 목표차 예측을 비교한다.
  접촉 시점/양의 raw lambda/몸통 실제 움직임과 기타 궤적도 함께 기록한다.
- [ ] 4. 독립 검수와 그래프/설명 문서로 결과를 남긴 뒤 후보를 결정한다.

## 측정 뒤 결정

행렬은 고정 초기 상태의 .1초 응답이며 FK나 실시간 feedback Jacobian이 아니다.
heldout에서 접촉 모드와 예측 오차를 읽고 국소 모델의 사용 범위를 결정한다.
기타 위치·회전 악화를 함께 다루는 제한된 목표 보정 후보를 이후 별도로 구현·검증한다.
처음 보정 폭은 최대 .025rad∩기존 목표 범위로 계획하며 구체적인 목적함수와 후보는
측정 후 문서에 추가한다. 임의의 안정 성공 기준이나 허용 오차를 정하지 않는다.
새 feedback/PD gain/strap/finger/후기 시간 변경을 이번 식별과 섞지 않는다.

코드·설정·메인 계획은 stability_adapter_2, 결과·로그·그림은
docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1에 저장한다.
원본 및 동결된 이전 phase를 보존한다. raw lambda는 N 단위 지지력이 아니며
source 면 간격/법선은 PhysX cooked clearance 인증이 아니다.
