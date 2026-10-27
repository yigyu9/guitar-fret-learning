# 왼손 지지점의 world 위치 유지: 다음 제어 소단계 제안

2026-10-06. 상태: 사용자 확인 전. 구현·새 ON trial은 아직 없다.
관절 목표 보정 OFF/ON의6개 native 결과를 joint_hold_v1에 보존했다.
1초 기타 오차는264.207mm/48.065°→196.035mm/33.994°로 개선됐지만,
LH–기타 접촉0과156.395mm의 끝 source 손–넥 거리가 남았다.
관절각 편차 감소만으로 world 위치의 지지점을 유지하지 못했으므로,
팔 자세와 접촉 지점을 연결하는 최소 추가 보정을 검토한다.

## 변경 제안과 유지 조건

현재 `p08_load00` 초기 왼손 palm의 source 형상 중심 world 위치를 임시 지지점
목표로 둔다. source 근접 거리0.800mm를 접촉 성공으로 간주하지 않는다.
실제 palm 위치와 이 목표의 차이를 읽어 왼팔12 목표 보정을 계산한다.
오른팔12는 현재 관절 PI 보정을 유지하며 finger42·torso9·하체 목표/gain은 유지한다.
root, 자유 기타 초기 +5mm/회전/고정 유지 목표, 원본 스트랩 수식과 고정 LA도 유지한다.
기타/손 pose·state를 쓰거나 손을 부착하지 않고 힘을 기타 목표로 직접 적용하지 않는다.

`q_play + delta_final` 목표 하나만 native PD로 전달한다. 이번 무연주 진단에서
`q_play`와 지지점은 초기 자세다. 향후 연주에는 연주 목표에서 지지 목표를 갱신해야 하며,
왼손을 영구 world 고정 목표에 묶는 구조로 승계하지 않는다. 학습 구조는 결정하지 않는다.

## 계획과 검증

- [ ] 1. Native humanoid Jacobian을 read-only로 얻고 palm 형상 중심으로 옮긴다.
  fixed root의 row/column layout, native body origin/COM 기준·좌표계를 설치된
  Isaac Gym 문서와 실제 tensor로 확인한다. 초기각±0.001rad의 fresh native FK
  유한차분과 대조한다. 모델/기존 ±0.3rad 경계에서는 one-sided 차분을 쓴다.
  이 단계는 물리 rollout이 없고 상태를 실행 중 덮어쓰지 않는다.
- [ ] 2. Jacobian이 검증된 경우에만 왼손 위치 오차를 쓰는 제한 least-squares
  목표 보정을 추가한다. 현재 관절 PI 보정은 자연스러운 초기 자세 쪽 regularizer로 둔다.
  목표는 `J * (q_play + delta_final - q_actual)`이 world 위치 오차의2배에
  가까워지는 것이다. damping/regularizer 출발값0.05m/rad는 제안값이다.
  양팔 총 보정±0.15rad, 최종 모델 한계∩C02±0.3rad를 유지하고,
  새 최종 목표 변화율은0.02rad/60Hz update 이하로 제한한다.
  적분 anti-windup은 이 새 최종 적용량으로 검사하며 별도 적분 항을 추가하지 않는다.
- [ ] 3. 같은 초기 상태의 현 관절 PI와 새 위치 보정을0.1초 비교한다.
  actual palm 위치·방향·관절·native 접촉·기타 p/q·strap 장력·목표 포화를 기록한다.
  현재처럼 proxy 방향은 전 physics sample에서 관찰하고 위쪽 반구를 벗어난 결과는
  채택하지 않는다. 새로운 해부학적 wrist/shoulder hard limit은 임의로 만들지 않는다.
- [ ] 4. 개선 후보만0.5초/1초로 연장한다. 원본/비제어 목표 보존·상태 읽기 불변성과
  재현성을 검증하고 그림·설명·별도 검수를 누적한다. 물리 지지가 생긴 뒤 기타 p/q
  오차 보정과 작은 팔·손 동작 안정성으로 진행한다.

FK 유한차분은 계측 검증이고 최종 목표의 task rejection은 별도 항목이다.
Jacobian frame/시점이 확인되지 않으면 position controller를 실행하지 않는다.
이번 제안은 관절 PI와 동일한 보정·최종 목표 범위 안에서 task 목적과 변화율 제한을
추가하는 중요한 제어 변경이므로 사용자 확인 후 진행한다.
