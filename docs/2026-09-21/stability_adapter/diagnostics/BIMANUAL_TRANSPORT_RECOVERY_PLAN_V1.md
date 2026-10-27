# Bimanual transport 학습 실패 분석 및 복구 계획 v1

## 1. 결론

현재 문제는 학습 시간이 짧아서가 아니다. 100 PPO update 동안 SUPPORT 단계의
성공률이 최고 40.6%, 최종 26.6%에서 정체했다. 자동 curriculum 승급 기준은
80%이므로 실제 5 mm TRANSPORT 학습은 시작되지 않았다.

우선 해결해야 할 문제는 다음 순서다.

1. 오른손이 SUPPORT 접촉 상태에 안정적으로 들어가지 못한다.
2. 왼팔 controller가 거의 항상 관절 목표 한계에 걸려 기타의 운동을 상쇄할
   기구학적 여유가 없다.
3. 오른손 접촉 충격과 왼손 상대운동/과압의 원인 귀속이 로그에서 분리되지 않는다.
4. SUPPORT 보상이 멀리 벗어난 상태에서 포화되어 복구 방향을 충분히 제공하지
   못하고, 성공 보상은 누적 음의 보상에 비해 작다.
5. 동기식 episode cycle 때문에 계산량의 절반 이상이 학습 표본으로 사용되지
   않는다.

성공 조건을 먼저 느슨하게 만드는 것은 권장하지 않는다. 현재 병목은 조건이
지나치게 엄격해서라기보다 접촉 획득과 제어 권한이 불안정하기 때문이다.

## 2. 로그 근거

### 2.1 학습량과 결과

- PPO update: 100
- simulator step: 204,800
- 유효 환경 표본: 92,214 (45.0%)
- 완료 episode: 286
- 기록된 성공: 88
- 과압 종료: 101
- 상대운동 손실 종료: 73
- timeout: 22
- finger loss: 1
- environment failure: 0
- 최근 64 episode 최종 성공률: 17/64 (26.6%)

환경 붕괴나 NaN이 아니라 과압과 접촉 상대운동이 실패의 대부분이다.

### 2.2 성공 게이트

100 update의 대략적인 평균 통과율은 다음과 같다.

- 선형 속도: 63%
- 각속도: 64%
- 현재 왼손 grip valid: 85% 내외
- `grip` 복합 게이트: 40% 내외
- 오른손 SUPPORT active: 47% 내외
- safety: 99.8% 내외

로그의 `grip` 게이트는 왼손 grip만 의미하지 않는다. 최근 왼손 접촉 이력,
오른손 ACTIVE, safety를 모두 곱한 복합 값이다. 따라서 이 값만으로는 실제로
어느 조건이 settle을 끊었는지 알 수 없다.

성공률이 높은 update군과 낮은 update군을 비교하면 다음 차이가 난다.

| 항목 | 높은 성공률 update | 낮은 성공률 update |
|---|---:|---:|
| 오른손 SUPPORT active | 51.9% | 20.7% |
| 오른손 tangent error p90 | 151 mm | 202 mm |
| 오른손 normal gap p90 | 91 mm | 138 mm |
| 각속도 평균 | 0.54 rad/s | 0.66 rad/s |
| 복합 grip 게이트 | 42.6% | 16.8% |

집계 로그 수준의 상관관계이므로 인과관계를 확정할 수는 없지만, 오른손 접촉
획득 여부가 성공률과 가장 강하게 함께 움직인다.

### 2.3 왼팔 controller 포화

- physical target clamp: 구간 평균 약 89~96%, 후반 약 96%
- action clamp: 약 46~62%
- tracking-band clamp: 약 35~58%
- Jacobian `dq` clamp: 약 6~10%
- torque utilization p90: 약 0.3%
- 최소 joint-limit margin은 반복적으로 음수에 가까운 값

토크가 부족해서 움직이지 못하는 것이 아니다. controller가 요구하는 관절 목표가
물리 joint limit 또는 tracking band 밖에 있어 명령이 잘린다. 현재 acquisition
grip 자세가 SUPPORT/TRANSPORT 방향의 관절 여유를 남기지 않거나, 적분형 관절
목표가 같은 한계 방향으로 계속 누적되는 것이 원인이다.

### 2.4 오른손 SUPPORT 접근

오른손 palm force 평균은 전체 프레임 기준 약 4.6 N으로 목표 6 N과 크게
동떨어지지 않는다. 문제는 접촉한 뒤의 힘보다 접촉에 들어가는 비율이다.
오른손 tangent error와 normal gap의 p90이 각각 약 150 mm, 100 mm 수준이므로
상당한 프레임에서 오른손이 아직 접근 경로에 있다.

현재 오른손은 goal episode가 시작된 뒤 먼 위치에서 접근한다. 접근 중에는 왼손이
기타를 혼자 유지해야 하고, 접촉 전환 순간에는 기타에 충격을 줄 수 있다. 이
과정이 SUPPORT 정지 학습과 한 episode 안에서 섞여 있다.

### 2.5 보상과 표본 효율

SUPPORT 보상의 위치 오차 항은 12 mm를 넘으면 clamp되어 더 멀어진 상태에서
추가 방향 정보를 주지 않는다. 프레임당 평균 보상은 약 -2~-3이고 성공 보상은
종료 시 +5 한 번이므로 성공 궤적도 긴 음의 누적 보상에 묻힐 수 있다.

또한 동기식 cycle은 먼저 끝난 환경을 비활성화한 뒤 마지막 환경이 끝날 때까지
기다린다. 그 결과 이론상 204,800개 중 92,214개, 45.0%만 PPO 표본으로
사용됐다. 학습 시간을 두 배로 늘려도 실제 정보량 증가가 작다.

## 3. 복구 계획

### P0. 원인 분리 진단부터 추가

다음 항목을 episode별·환경별로 기록한다.

1. 왼손 최근 접촉 이력, 오른손 ACTIVE, safety를 각각 독립 게이트로 기록한다.
2. 9개 왼팔 관절별 physical-target/tracking/action clamp 횟수와 방향을 기록한다.
3. 과압을 왼손 digit, 왼손 palm, 오른손 palm, 기타-몸 충돌로 귀속한다.
4. 오른손 최초 접촉 전 30 frame부터 접촉 후 60 frame까지 기타 선속도·각속도,
   palm normal/tangent velocity, 접촉력, impulse를 event trace로 저장한다.
5. 다음 네 가지 deterministic ablation을 같은 snapshot에서 비교한다.
   - 오른손 OFF / policy residual OFF
   - 오른손 ON / policy residual OFF
   - 오른손 OFF / 현재 policy
   - 오른손 ON / 현재 policy

이 비교로 오른손 sidecar, PPO residual, 원래 왼손 grip 중 무엇이 기타를 먼저
흔드는지 결정한다.

### P1. 오른손 접근과 SUPPORT 유지를 학습 episode에서 분리

1. 오른손을 GRIP 마지막 구간에 안전한 pre-contact 위치까지 미리 이동시킨다.
2. goal episode 시작 후 별도의 `SUPPORT_ACQUIRE` 상태를 둔다.
3. 오른손이 ACTIVE이고 접촉력이 안정 범위에서 12 frame 유지되기 전에는 PPO
   rollout과 settle timer를 시작하지 않는다.
4. 접근 속도를 거리 구간별로 나눈다.
   - 먼 구간: 빠른 이동
   - 표면 30 mm 이내: 최대 step을 크게 감소
   - 표면 5 mm 이내: normal velocity 제한
   - 접촉 후: force feedback만 사용
5. anchor는 최초 한 frame 접촉이 아니라 안정된 patch/contact dwell 이후 고정한다.
6. force target 6 N은 우선 유지한다. 과압 귀속을 확인하기 전에 힘을 더 높이지
   않는다.

P1 완료 기준:

- 오른손 ACTIVE rate 95% 이상
- 접촉 획득 성공률 95% 이상
- 접촉 전환 impact 종료 2% 미만
- ACTIVE 상태 palm force p90 20 N 미만
- tangent/normal 오차는 전체 episode가 아니라 ACTIVE 구간에서 별도 평가

### P2. 왼팔의 기구학적 여유 확보

1. 현재 functional-grip snapshot에서 9개 관절의 상·하한 여유를 측정한다.
2. SUPPORT에 필요한 보정 방향으로 여유가 0.10 rad 미만인 관절을 식별한다.
3. 손 접촉점은 유지하면서 어깨·팔꿈치·손목 자세를 재배치해 새 acquisition-grip
   snapshot을 만든다. 사용자가 요청한 대로 L_Thorax보다 아래 관절을 우선한다.
4. Jacobian DLS에 joint-center null-space 항과 joint-limit 가중치를 추가한다.
5. physical clamp가 발생한 축은 내부 적분 target도 즉시 실제 clamp 값으로
   되돌려 같은 한계 방향 누적을 막는다.
6. 정규화 action, joint radian, PD target 사이 변환을 관절별로 검증한다.

P2 완료 기준:

- physical target clamp rate 20% 미만
- tracking clamp rate 20% 미만
- action clamp rate 15% 미만
- 모든 제어 관절의 최소 limit margin 0.05 rad 이상
- torque p90은 안전 한계 이하를 유지

### P3. SUPPORT 보상 재구성

1. 절대 위치 오차의 포화 penalty 대신 이전 frame 대비 오차 감소량을 사용한다.
2. 위치·회전 오차의 절대 penalty는 작은 bounded 항으로만 유지한다.
3. 오른손 ACTIVE 전에는 접근 안정화, ACTIVE 후에는 속도 감소와 왼손 grip
   유지에 서로 다른 보상을 적용한다.
4. 기타 linear/angular acceleration과 접촉 impulse에 직접 penalty를 준다.
5. 정상 프레임 보상 규모를 약 `[-0.2, 0.2]`로 맞추고 terminal success가
   한 episode의 차이를 분명히 만들도록 재조정한다.
6. 성공 조건과 안전 종료 조건은 보상과 별도로 유지한다.

### P4. 학습 표본 효율 개선

최선은 종료된 environment만 snapshot으로 비동기 복원하는 것이다. 구현 비용이
크다면 우선 active environment가 절반 이하가 되는 순간 synchronized cycle을
조기 재시작한다. 조기 재시작 표본은 실패로 세지 않고 truncation으로 처리하여
critic bootstrap을 유지한다.

목표는 valid sample fraction을 현재 45%에서 80% 이상으로 높이는 것이다.

### P5. 다시 학습하는 순서

1. noise 0에서 deterministic SUPPORT 평가 32 episode
2. 오른손 접촉 획득만 검증
3. SUPPORT PPO를 residual scale 0.10 이하에서 학습
4. SUPPORT 성공률 90% 달성 후 시작 noise를 0.5/1.0/2.0 mm 순으로 증가
5. noise 2 mm에서 최근 64 episode 성공률 80% 이상일 때만 5 mm로 승급
6. 5 mm에서는 목표 통과·제동 보상을 사용하고, SUPPORT controller는 먼저
   고정한 상태로 학습
7. 각 단계에서 deterministic evaluation과 WAIT부터 시작하는 전체 영상을 저장

## 4. 구현 우선순위와 예상 효과

| 순서 | 변경 | 예상 효과 |
|---|---|---|
| 1 | 게이트·관절·과압 귀속 진단 | 잘못된 완화/증력 방지 |
| 2 | 오른손 pre-position + SUPPORT_ACQUIRE | 접촉 대기와 충격 제거 |
| 3 | grip snapshot 관절 여유 + anti-windup | 96% target clamp 해소 |
| 4 | SUPPORT 보상 재스케일 | 성공 행동의 학습 신호 강화 |
| 5 | 비동기 또는 조기 cycle reset | 같은 시간에 약 1.8배 표본 확보 |
| 6 | 무노이즈부터 noise curriculum | 안정 동작을 먼저 학습한 뒤 강건화 |

가장 먼저 구현할 묶음은 P0과 P1이다. 현재 상태에서 timeout이나 성공 dwell만
완화하거나 과압 한계를 더 올리면 숫자상 성공은 증가할 수 있지만, 오른손이
불안정하고 왼팔이 joint limit에 걸린 상태를 그대로 숨기게 된다.
