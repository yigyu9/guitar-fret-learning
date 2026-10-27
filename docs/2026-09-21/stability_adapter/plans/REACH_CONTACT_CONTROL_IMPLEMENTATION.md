# StabilityAdapter REACH 접촉 제어 구현 방향

## 현재 판단

손이 거의 움직이지 않는 주원인은 reward의 움직임 패널티가 아니다. 현재 학습은 단일
교사 궤적의 behavior cloning이므로 reward를 직접 최적화하지 않는다. 우선 해결할 문제는
다음 세 가지다.

1. 6 cm 거리와 넓은 표면 tolerance가 목표점에서 벗어난 상태를 허용한다.
2. 한 프레임의 palm net force로 `palm_contact_acquired`가 영구 latch된다.
3. latch 직후 교사가 전체 action을 고정해 접촉이 사라져도 다시 접근하지 않는다.

따라서 보상 재조정이나 학습 시간 증가보다 거리·접촉 계약과 teacher를 먼저 수정한다.

## 목표 상태기

```text
WAIT_TERMINAL
  -> DESCEND_BELOW
  -> ALIGN_UNDER_NECK
  -> SOFT_APPROACH
  -> CONTACT_CONFIRM
  -> COMPLIANT_HOLD
          | contact lost
          v
     SOFT_APPROACH
```

- `DESCEND_BELOW`: 현재 손의 XY를 유지하며 기타 아래로 이동한다.
- `ALIGN_UNDER_NECK`: 넥 2/3 목표 아래의 staging point로 이동하고 손바닥 방향을 맞춘다.
- `SOFT_APPROACH`: Torso/L_Thorax 목표를 고정하고 왼팔로만 넥 normal 방향에 접근한다.
- `CONTACT_CONFIRM`: 현재 프레임의 실제 접촉력과 기하 조건을 연속 dwell로 확인한다.
- `COMPLIANT_HOLD`: 접선 방향 위치와 자세를 유지하면서 normal 방향 접촉력을 제어한다.
- 접촉이 일정 시간 사라지면 latch를 유지하지 않고 `SOFT_APPROACH`로 복귀한다.

## 1단계: 거리와 목표점 계약 수정

### 목표점

- 넥 위치는 body 쪽 fret22에서 nut 방향으로 2/3 지점을 유지한다.
- 목표 표면은 guitar local 좌표의 넥 아래면으로 유지한다.
- 단일 `LH:palm` local offset만 사용하지 않고 palm STL inward surface 표본점을
  정의한다.
- 각 frame에서 넥 아래면 목표 영역과 가장 가까운 **하나의 active palm point/closest pair**를
  선택한다. normal, lateral, axial 오차는 모두 이 동일한 pair에서 계산한다.
- 축별 오차를 별도 기록하고 Euclidean 거리 gate와 축별 gate를 AND로 결합한다. 축마다
  서로 다른 표본점의 최소값을 조합하지 않는다.

### 초기 기준

- normal 오차 1.5 cm 이하 AND lateral 오차 2.0 cm 이하 AND axial 오차 2.0 cm 이하
- 접촉 진입 전 Euclidean 거리 gate: 3.0 cm 이하
- hold Euclidean 거리 gate: 2.0 cm 이하

초기값은 실제 collision mesh와 렌더 marker가 일치하는지 확인한 뒤 보정한다. 기존 6 cm
성공 거리와 normal 3.5 cm, lateral/axial 7 cm tolerance는 제거한다.

### 검증

- 넥 목표점, 손바닥 표본점, 각 축 오차를 한 화면에 렌더한다.
- 렌더상 떨어진 상태에서 overlap이 true가 되지 않아야 한다.
- 목표점에서 2 cm 이상 벗어난 축이 있으면 hold gate가 false여야 한다.

## 2단계: 접촉 판정 수정

### 학습용 GPU provisional gate

- 공식 release와 WAIT 동안에는 기존 palm-기타-의자 충돌 dynamics를 그대로 보존한다.
- WAIT terminal snapshot 뒤 REACH 경계에서만 palm이 neck-root의 두 collision shape와
  충돌하도록 filter를 전환한다. digit-neck 충돌은 조기접촉 실패 감지를 위해 유지한다.
- 설정 직후 humanoid/guitar/chair filter를 read-back하고, guitar root가 정확히 두 neck
  shape만 갖는지 확인한다. 예상과 다르면 fail-closed로 환경 생성을 중단한다.
- PhysX ground plane은 filter 0이라 bitmask로 차단되지 않으므로 palm mesh 표본의 ground
  clearance를 `non_neck_clear`에 포함한다.
- palm net contact force vector를 넥 아래면 world normal에 투영한 압축 성분
  `max(0, dot(F_palm, n_neck_underside))`을 provisional normal force로 사용한다.
- tangential force는 별도 기록하며 normal force로 합산하지 않는다. 짧은 spike를 그대로
  제어 입력으로 쓰지 않도록 저역 필터와 raw maximum을 함께 유지한다.
- palm STL inward surface 표본점은 목표점 선택과 ground clearance에 사용한다.
- 위 normal force, 동일 active point의 엄격한 neck-local geometry gate,
  `non_neck_clear`를 동시에 만족해야 provisional contact로 계산한다.
- GPU net-contact tensor는 collider pair를 증명하지 못하므로 이 gate만으로 checkpoint를
  공식 승격하지 않는다.
- 손가락 접촉은 REACH 동안 계속 실패 조건으로 유지한다.

### 240 Hz substep 수집

- 한 control step의 네 번 `simulate()` 각각 직후 contact tensor를 refresh한다.
- 네 substep의 palm normal force 최대값과 arm force 최대값을 기록한다.
- 안전 상한 초과 impulse는 각 substep에서
  `max(raw_arm_force - 30 N, 0) * (1/240 s)`로 누적한다.
- contact 진입/유지 dwell은 60 Hz control frame 기준으로 판정하되, 그 frame의 force 값은
  네 substep 전체를 반영한다.
- 중간 substep의 30/80 N 충격을 마지막 substep 값으로 덮어쓰지 않는다.

### 접촉 상태

- 접촉 진입: filtered palm normal force 2~15 N을 10 frame 연속 만족
- 접촉 유지: filtered palm normal force 1~20 N
- 접촉 해제: filtered palm normal force 0.5 N 미만이 5 frame 연속되면 contact state를 해제
- 20 N 초과 30 N 이하에서는 confirm/hold dwell을 즉시 reset하고 넥 normal 반대 방향으로
  retreat한다.
- 30 N 초과분은 REACH reset부터 episode 종료까지
  `max(raw_arm_force - 30 N, 0) * (1/240 s)`로 누적한다. reset 시 0으로 초기화하고
  3 N·s 이상이면 실패한다. threshold와 누적 구간은 manifest에 고정한다.
- raw arm force 80 N 이상은 즉시 실패로 유지한다.
- `palm_contact_acquired` 영구 OR-latch를 제거하고 현재 접촉 상태와 과거 접촉 이벤트를
  분리한다.

### 최종 승격 gate

- Isaac Gym `RigidContact`는 shape index를 제공하지 않으므로 이를 판정 계약으로 요구하지
  않는다.
- 구현 시작 시 asset 로드 전후의 rigid body, contact-capable shape, collision filter 집합을
  런타임에서 덤프한다. fixed-joint collapse 뒤 어떤 geom이 guitar root에 귀속되는지 증거
  JSON으로 남기고 그 집합과 asset hash를 manifest에 고정한다.
- guitar root에 neck 외 contact-capable shape가 하나라도 귀속되면 body pair만으로 neck을
  증명하지 않는다. 목표 영역 local position/normal과 비넥 surface exclusion을 필수로 한다.
- CPU pipeline deterministic replay에서 실제 `{LH:palm, guitar root}` body pair를 찾고,
  guitar 쪽 local contact position이 목표 axial/lateral/underside 범위 안인지 확인한다.
- `RigidContact.normal`은 body0에서 body1 방향이다. guitar가 body0이면 그대로, guitar가
  body1이면 부호를 반전해 항상 `guitar -> palm` 방향으로 canonicalize한다.
- canonical normal과 guitar underside outward normal의 각도가 25도 이내인지 확인한다.
- neck-valid contact들의 pair-specific `RigidContact.lambda`를 합산하고 1~20 N 범위인지
  확인한다. 동등한 substep impulse 기준을 사용할 경우 변환식과 threshold를 artifact에
  기록한다.
- body pair, topology audit, local position, canonical normal, 비넥 exclusion, pair-specific
  force를 모두 만족해야 한 frame의 strict neck contact로 판정한다.
- palm-first 이력이 확인되고 digit 조기접촉이 없으며, raw arm force 80 N 실패 및 excess
  impulse 실패가 없는 strict contact를 30 control frame 연속 만족해야 공식 REACH 성공으로
  승격한다.

## 3단계: compliant teacher 구현

- 최초 접촉 시 전체 action을 고정하는 `contact_hold_action` 조기 반환을 제거한다.
- 접선 방향에는 위치 제어를 계속 적용한다.
- normal 방향에는 filtered palm-neck normal force 기준 목표 6 N의 저이득 force controller를
  적용한다. net-force norm이나 tangential friction을 normal force로 사용하지 않는다.
- force가 1 N 아래로 떨어지면 넥 방향으로 천천히 전진한다.
- force가 15 N을 넘으면 넥에서 천천히 물러난다.
- phase 3에서는 Torso 2도, L_Thorax 15도 예산을 유지하고 왼팔 9축을 주로 사용한다.
- phase 3 action 제한은 동작이 관찰될 정도로 재보정하되 접촉 직전 normal 속도는 별도로
  제한한다.

### teacher 통과 기준

- 접촉 전 최소 거리 2 cm 이하
- palm-first contact
- 접촉력 1~20 N, 30 frame 연속
- 접촉 손실 뒤 자동 재접근 확인
- 손가락 조기 접촉, 아래쪽 접근 위반, 80 N 충격 없음
- 5개 이상의 작은 기타 pose/velocity perturbation에서 재현

## 4단계: 보상 구조 재조정

Teacher 검증 전에는 reward weight를 조정하지 않는다. PPO/residual 학습 단계에서는 다음처럼
구성한다.

- 거리 보상: axial/lateral/normal 개선량을 분리한 potential shaping
- 방향 보상: palm-up과 neck heading 정렬
- 접근 보상: 목표 근처에서만 상대속도 감쇠
- 접촉 보상: 현재의 유효 palm-neck 접촉에만 지급
- 유지 보상: 연속 접촉 dwell 증가량에 지급
- 접촉 손실 패널티: hold 상태에서 force가 해제 기준 아래로 내려갈 때 부과
- 안전 패널티: 손가락 조기 접촉, 과도한 force, 잘못된 접근 방향
- 자세 패널티: Torso를 강하게, L_Thorax를 중간, 왼팔을 약하게 제한
- action delta 패널티는 안전용 작은 값으로 유지하고 거리 개선보다 커지지 않게 계측한다.

매 rollout에서 각 reward 항목을 따로 기록해 거리 개선 보상과 움직임 비용의 실제 크기를
비교한다.

## 5단계: 학습 방식 변경

단일 궤적 standalone absolute-action BC는 사용하지 않는다.

1. 검증된 compliant teacher로 여러 초기 perturbation 궤적을 수집한다.
2. teacher action 자체보다 이전 action에 대한 bounded residual을 학습한다.
3. learner rollout에서 방문한 실패 직전 상태를 teacher로 다시 labeling하는 DAgger를
   반복한다.
4. 접촉 직전과 접촉 손실 상태를 일반 이동 상태보다 더 자주 sampling한다.
5. teacher 없이 성공한 독립 rollout만 checkpoint 후보로 저장한다.

## 구현 순서와 완료 조건

- [x] 손바닥 표본점과 축별 거리 구현
- [ ] 런타임 contact-capable shape/filter topology dump와 manifest 고정
- [x] 목표점 렌더 및 런타임 축별 오차 검증
- [x] REACH palm-neck collision isolation과 런타임 필터 감사
- [x] palm 비넥 충돌 차단 filter read-back 및 ground clearance 검증
- [x] GPU provisional normal-force gate와 현재 접촉 state 구현
- [x] 4개 physics substep force maximum·impulse 누적 구현
- [ ] CPU body-pair/topology/local-position contact replay 구현
- [x] compliant teacher와 contact-loss recovery 구현
- [ ] 5개 perturbation teacher 평가 통과
- [ ] reward 항목별 로깅 및 크기 검증
- [x] residual policy와 DAgger 구현
- [ ] 다중 seed standalone 평가 통과
- [x] 교사 성공 후보·학습 실패 결과 영상 생성
- [ ] 성공 checkpoint 생성

첫 구현 단위는 **1단계 거리 계약 + 2단계 접촉 상태**까지로 제한한다. 이 두 단계의 렌더와
수치 검증을 통과한 뒤 teacher와 학습을 변경한다.
