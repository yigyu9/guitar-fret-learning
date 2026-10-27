# Bimanual transport v1

목표: 왼손은 넥 force closure와 병진 이동을 담당하고, 오른손은 기타 바디 전면을
가볍게 지지해 회전과 흔들림을 줄인다. 기존 Goal Transport의 9차원 PPO action과
checkpoint 계약은 유지한다.

## 고정 계약

- 왼손 손가락 21 DoF: 정책이 아닌 force-hold sidecar가 소유한다.
- 왼팔 이동 9 DoF: `L_Shoulder/L_Elbow/L_Wrist` PPO residual + 6D servo가 소유한다.
- 오른팔 지지 9 DoF: `R_Shoulder/R_Elbow/R_Wrist` deterministic sidecar가 소유한다.
- `Torso`, `L_Thorax`, `R_Thorax`, 오른손 손가락은 snapshot pose를 유지한다.
- 오른손 지지 목표: transport snapshot에서 실제 도달·접촉이 안정적이었던 guitar
  local `(0.115, -0.295, -0.0017)` 전면 body face.
- 오른손 접근: 전면 150 mm 여유 확보 → `(0.115, -0.295, 0.13)` 횡이동 → 접촉.
  접촉 획득 순간의 접선 좌표를 anchor로 고정해, 지지 후 패치 중앙으로 끌면서
  기타를 옆으로 미는 현상을 막는다.
- 오른손 목표 작동력: 6 N. 접촉 리플을 고려해 유지 허용 3–20 N,
  relief 35 N, hard failure 40 N으로 분리한다. 패치 안에서 발생하는
  zero-force 리플은 접촉 획득 누적치를 지우지 않는다.
- curriculum: SUPPORT, 5 mm, 10 mm, 30 mm, 50 mm, 100 mm.
- SUPPORT 입문 단계는 정밀 복원이 아니라 양손 접촉 획득용이므로 6 cm/15°,
  0.15 m/s, 0.75 rad/s 안전 범위에서 30-frame 정착을 요구한다. 정밀
  위치·회전은 이후 이동 단계가 담당한다.
- SUPPORT timeout은 접근·접촉 약 350 frame과 연속 정착 여유를 합쳐 900 frame이다.
- translation 성공: 요청 방향 projected displacement 80% 이상 필수.

## 구현 체크리스트

- [x] 기타 근접 접촉과 의자 접촉을 분리하는 오른손 force attribution
- [x] 기존 오른손 avoidance를 attributed guitar contact 기준으로 수정
- [x] 왼손 force-hold 필터/deadband/누적 제한/과압 release
- [x] force-valid 3-frame hysteresis 전에는 trajectory 정지
- [x] 0.5/1/3/5/10 cm curriculum 및 projected progress 성공 gate
- [x] `WAIT -> LEFT_GRIP -> RIGHT_APPROACH -> RIGHT_SUPPORT -> TRANSPORT`
- [x] 오른손 9-DoF 6D Jacobian support controller
- [x] 오른손 의도 접촉은 허용하고 비목표/과압 접촉은 avoidance로 전환
- [x] 이동 보상에 누적 projected displacement와 forward velocity 반영
- [x] force/support/curriculum 진단 필드 및 독립 진단 도구 추가
- [x] 순수 함수와 환경 계약 회귀 테스트
- [x] GPU snapshot restore 및 controller smoke
- [x] 변경 검수

## 성공 기준

1. 정상 WAIT의 의자 접촉은 기타 충돌로 오인하지 않는다.
2. 왼손 힘이 부족하면 arm trajectory만 멈추고 손가락 복구는 계속한다.
3. 오른손이 목표 body patch에 접근해 목표 6 N, 허용 3–20 N으로 지지하되
   transport 목표를 직접 끌지 않는다.
4. authored WAIT transient는 초기환경 재현을 위해 관찰만 하고, REACH 이후 40 N 이상 attributed guitar contact는 안전 실패로 유지한다.
5. 기존 Goal Transport 9D policy checkpoint는 구조 변경 없이 로드 가능하다.

## 구현 검증 결과

- 관련 순수/계약 회귀: 53개 통과.
- SUPPORT GPU smoke 550 frame: SUPPORT 200 frame, frame 413에서 성공,
  failure 없음, finite 유지.
- 10 mm zero-residual smoke 500 frame: SUPPORT 240 frame, 최대 palm force
  27.36 N(< relief 35 N), failure 없음.
- 동일 10 mm 조건에서 projected progress는 오른손 지지 사용 시 -9.72 mm,
  미사용 시 -17.67 mm였다. 오른손 지지는 역방향 드리프트를 줄였지만 zero-residual
  servo만으로 목표 이동을 달성하지는 못했다. 다음 학습은 새 0.5 cm curriculum과
  projected-progress 보상을 사용해야 하며, 이 수치는 학습 완료 성능으로 해석하지 않는다.
