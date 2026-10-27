# Stability Adapter TRANSPORT 학습 설계

상태: T0.5 5 mm hysteresis v2 구현·학습 완료, 승격 실패  
범위: `GRIP -> TRANSPORT -> MAINTAIN 진입`  
목표: 스트랩이 연결된 자유 기타를 기능적 그립으로 지지하면서, release 직전의 초기 기타 위치와
회전을 모두 복원한다.

## 0. 2026-09-20 구현 결과

### Hysteresis v2

- SECURE를 연속 30 frame에서 최근 20 frame 중 15 frame 유효 조건으로 변경했다.
- MOVE는 엄지 8 frame, opposing finger 10 frame, motion 10 frame, soft load 6 frame의 독립
  grace를 사용한다. SETTLE은 엄격한 functional-grip truth로 복귀한다.
- MOVE loss 임계 frame은 SETTLE 진입보다 종료 판정을 우선하며, SETTLE에서 회복된
  thumb/finger/motion/load 조건은 각자의 MOVE loss streak만 초기화한다.
- 비활성 pinky는 안전 hover를 유지하고, 활성 손가락은 과압 시 빠르게 풀고 저압 시 천천히 원래
  목표로 복구한다. filtered total 30 N과 per-body/conservative 40 N hard safety는 변경하지 않았다.
- 최종 learned rollout은 SECURE를 통과하고 MOVE에 진입했으며 과부하는 없었다. 최종 hand load는
  `2.66 N`이지만 opposing-finger loss streak가 `10/10`에 도달해 종료됐다.
- 최종 위치 오차 `6.64 mm`, 목표 tolerance `1.0 mm`, `promotion_eligible=false`다.

### 이전 strict v1

- 기능적 GRIP acquisition과 TRANSPORT 유지 판정을 분리했다.
- acquisition은 엄지와 반대편 두 손가락의 넓은 면 접촉을 요구한다.
- TRANSPORT 유지에는 active digit hysteresis를 적용하며 비활성 새끼손가락 접촉만으로 전체
  그립을 무효화하지 않는다.
- `SECURE -> MOVE -> SETTLE`, 191D observation, 9D distal-arm actor, 고정 proximal 6D,
  결정론적 21D 손 제어를 구현했다.
- 안전 검수 후 SECURE를 연속 grip-retained 30 frame으로 강화했다. strict v1 최종본은 교사 50 sample에
  대해 BC 20,000 update를 수행했고 최종 MSE는 `9.290e-7`이다.
- 최종 rollout은 SECURE 중 손 하중 `46.74 N` 과부하로 차단됐다. MOVE에는 진입하지 않았으며,
  `promotion_eligible=false`다.
- 따라서 현재 checkpoint는 진단용 기준선이며 synchronizer/MAINTAIN에 연결하지 않는다.
- 다음 구현은 기타 COM 오차를 손바닥 병진 오차로 그대로 사용하는 1점 IK를 폐기하고,
  strap pivot과 `v_grip = v_root + omega x r`를 포함하는 SE(3) 접촉점 교사로 교체한다.

## 1. 설계 결론

TRANSPORT는 손가락을 새로 쥐는 단계가 아니다. 검증된 기능적 그립을 입력 상태로 받아 왼팔과
손목으로 기타를 이동하고, 손가락은 압력 유지 제어기로 접촉을 보존한다.

첫 학습 버전은 다음처럼 분리한다.

```text
기능적 GRIP snapshot
    -> SECURE: 짧은 그립 확인
    -> MOVE: position/rotation 기준 경로 추종
    -> SETTLE: 목표 pose에서 속도 감쇠
    -> TRANSPORT_READY
    -> MAINTAIN
```

정책이 phase나 substage를 직접 선택하지 않는다. 결정론적 PhaseManager가 측정값과 dwell로
전환한다.

## 2. 구현 전 선행 조건

현재 `GripEnv`의 성공 truth는 모든 손가락이 정해진 패치에 접촉해야 하고
`PAD_CALIBRATION_VALIDATED=False`라서 TRANSPORT reset을 만들 수 없다. 먼저 아래의
`functional_grip`을 별도 truth로 구현하고 성공 snapshot을 수집해야 한다.

현재 `STRICT_PAIR_CONTACT_VERIFIED=False`도 별도의 hard blocker다. pad point가 허용 영역 안에
있다는 기하 판정만으로 실제 collider pair를 증명할 수 없다. 다음 둘 중 하나가 검증되고 manifest
flag가 참이 되기 전에는 functional-grip snapshot 저장, TRANSPORT reset, 승급을 모두 금지한다.

1. CPU/GPU replay에서 digit distal collider와 guitar neck collider의 pair/contact point/normal 검증
2. 동일한 attribution을 제공하도록 검증된 collision proxy + force sensor 계약

`PAD_CALIBRATION_VALIDATED && STRICT_PAIR_CONTACT_VERIFIED`가 기본 gate다. proxy 방식을 사용하면
동등한 새 schema/flag를 발행하며 기존 flag를 임의로 우회하지 않는다.

### 2.1 기능적 그립 truth

정확한 한 점이 아니라 허용 가능한 앞/뒤 면 영역과 실제 힘을 사용한다.

```text
thumb_rear =
    thumb가 넥 뒤쪽 허용 영역에 접촉
    AND raw distal normal force in [1.0, 8.0] N
    AND tangential slip <= 0.12 m/s

opposing_digit_i =
    index/middle/ring/pinky가 넥 앞쪽 허용 영역에 접촉
    AND raw distal normal force in [0.3, 8.0] N
    AND tangential slip <= 0.12 m/s

functional_grip =
    thumb_rear
    AND count(opposing_digit_i) >= 2
    AND opposing force sum in [1.5, 16.0] N
    AND 모든 digit proximal force <= 0.2 N
    AND conservative whole-hand load <= 30 N
    AND guitar-hand relative speed <= 0.15 m/s
```

`opposing force sum`은 앞쪽 네 distal normal force 전체로 계산한다. 개별 distal force는
`<=8.0 N`, whole-hand load는 `<=30 N`이어야 한다. 이 완화 기준은 nominal collision proxy 전용이며,
strict all-five promotion 기준을 대체하지 않는다.

초기 후보 수치이며 nominal scene에서 raw contact trace를 수집해 manifest로 봉인한다. 접촉점의
영역 중심 오차는 보상 품질에는 사용하지만 성공 필수 조건으로 사용하지 않는다.

### 2.2 진입 dwell과 snapshot

- `functional_grip` 8 frame 연속 후 T0.5 TRANSPORT 진입. TRANSPORT 내부 SECURE에서 최근
  20 frame 중 15 frame 이상의 별도 유지 기준을 재확인한다.
- 통과 시 root state, DOF state, PD target, strap state, 접촉 필터 상태, pressure-controller 기준
  action/integrator, 이전 executed 36D action, active digit mask, substage/loss streak를 함께 snapshot
- snapshot에는 엄지와 실제 활성 opposing digit mask를 저장
- 최소 32개의 물리적으로 서로 다른 snapshot을 수집
- 현재 실패한 learned grip checkpoint에서 TRANSPORT를 시작하지 않음
- PhysX contact manifold 자체는 tensor snapshot으로 복원된다고 가정하지 않음
- restore 후 `strap resync -> held-action warm-up -> SECURE 15/20 window`를 다시 통과한
  snapshot만 사용

## 3. 목표 기타 상태

목표는 world 고정 pose가 아니라 사람 body/pelvis frame `B`에서 기록한 release 직전 초기 pose다.
사람 reset 위치가 달라져도 같은 연주 자세를 복원할 수 있다.

v1의 `B`는 humanoid root/pelvis의 현재 frame이며 fixed-base humanoid이므로 reset 이후 움직이지 않는
frame으로 봉인한다. 향후 movable pelvis를 허용하면 guitar twist에서 body-frame의 선·각속도를 빼는
observation schema v2를 별도로 발행한다.

```text
target_position_B = position of guitar at authored release boundary
target_rotation_B = rotation-6D of guitar at authored release boundary
target_linear_velocity_B = 0
target_angular_velocity_B = 0
```

`ReachEnv.authored_root_snapshot`을 만들 때 guitar root pose를 body frame으로 변환해 별도
`TargetGuitarState`에 저장한다. 목표는 episode 도중 다시 계산하지 않는다.

성공 판정은 위치와 회전을 가중합하지 않고 각각 통과해야 한다.

```text
position_ok = ||p_B - p_target_B|| <= 0.02 m
rotation_ok = geodesic(R_B, R_target_B) <= 6 deg
velocity_ok = ||v_B|| <= 0.03 m/s AND ||omega_B|| <= 0.10 rad/s
target_pose_ok = position_ok AND rotation_ok
```

`2 cm / 6 deg`는 1차 nominal 후보다. 렌더에서 연주 자세가 어긋나면 더 엄격하게 조정하되,
position과 rotation을 서로 보상시키지 않는다.

## 4. TRANSPORT 내부 상태기계

### 4.1 SECURE

- 시작 시 현재 팔·손 목표를 그대로 유지
- 최근 20 frame 중 transport grip-retained 15 frame 이상 확인
- 실패하면 GRIP으로 자동 회귀하지 않고 `grip_lost_at_entry`로 episode 종료
- 목적: 잘못된 snapshot과 순간 접촉을 학습 데이터에서 제거

### 4.2 MOVE

- 현재 기타 pose에서 target pose로 시간 매개 기준 경로를 생성
- 위치는 body frame cubic smoothstep, 회전은 shortest-path quaternion slerp 사용
- 기준 경로의 최대 선속도 `0.08 m/s`, 최대 각속도 `0.25 rad/s`
- strap tension이 soft limit을 넘거나 slip이 증가하면 경로 진행률을 낮추고 정지 가능
- 정책은 기타 root force를 직접 출력하지 않고 관절 target만 출력

### 4.3 SETTLE

- position/rotation tolerance에 처음 들어오면 경로 진행을 1로 고정
- 기타 pose를 더 끌어당기지 않고 속도와 진동을 감쇠
- `target_pose_ok + velocity_ok + functional_grip + strap_safe`를 30 frame 연속 유지하면 성공
- 성공 tolerance를 한 frame 이탈하면 성공 streak는 0으로 초기화하되, MOVE 복귀는 position
  `>3 cm` 또는 rotation `>9 deg`의 넓은 exit tolerance가 5 frame 지속될 때만 수행

이 MOVE↔SETTLE 전환은 outcome reward를 반복 지급하지 않는다. TRANSPORT 성공 reward는
episode당 한 번만 지급한다.

## 5. 정책 입력

첫 구현은 named observation manifest를 사용한다.

| block | field | frame/단위 |
|---|---|---|
| phase | TRANSPORT one-hot, substage one-hot, phase age, dwell fraction | scalar |
| proprio | Stability 소유 관절 q/dq, soft-limit margin | joint local |
| guitar | 기타 position, rotation-6D, linear/angular velocity | body frame B |
| target | position error 3D, rotation error 3D, velocity error 6D, path progress | B |
| grip (actor) | 활성 digit mask, EMA normal force, EMA force vector, slip, opposition, proximal-clear flag | guitar/grip frame |
| hand | palm/wrist와 guitar grip frame의 상대 pose/twist | grip frame H |
| strap | tension, tension rate, extension ratio, upper/lower anchor direction | B/G |
| safety | whole-hand load, penetration margin, joint/effort margin | normalized |
| history | 직전 executed action, 직전 pose error, 직전 grip quality | normalized |

회전 입력에는 quaternion 자체 대신 rotation-6D 또는 SO(3) log error를 사용한다. actor에는 EMA
force만 제공한다. raw/EMA force, 원시 proximal force와 정확한 pair contact는 gate와 privileged
critic에 모두 제공한다. 이 분리를 observation manifest와 checkpoint ABI에 명시한다.

## 6. 정책 출력과 제어 계층

현재 런타임 계약은 `15D arm + 21D left hand = 36D`다. 기존 상위 설계 문서의 30D 표기는 구현 전에
현재 named joint manifest에 맞게 정정한다.

### 6.1 1차 학습

```text
learned: shoulder + elbow + wrist 9D residual
fixed: Torso 3D + L_Thorax 3D reference
fixed controller: 21D hand pressure maintenance
executed: masked 15D arm + controlled 21D hand = 36D
```

- 손가락은 GRIP 종료 자세를 기준으로 digit별 pressure controller가 작은 굽힘 보정을 수행
- 엄지/활성 opposing digit만 압력 제어, 비활성 손가락은 안전 hover 또는 저압 보조 접촉
- learned 9D residual은 phase reference에 더한 뒤 joint limit/rate/EMA/PD를 한 번만 적용
- Torso 3D와 L_Thorax 3D는 v1에서 reference에 고정하고 actor forward/log-prob/entropy에서 제외
- 15D arm 명령과 21D pressure-controller 명령을 명시적으로 합성해 반드시 GripEnv의 36D
  `_apply_grip_action()` 경로로 실행; `ReachEnv.step(15D)` 우회 금지
- 따라서 상체를 움직여 strap anchor/guides로 기타를 당기는 보상 우회를 허용하지 않음

### 6.2 2차 fine-tuning

1차 정책이 목표 pose와 그립을 안정적으로 유지한 뒤에만 21D 손 residual을 연다.

- hand residual cap은 normalized action 기준 처음 `±0.01`
- grip pressure controller 주위의 residual만 허용
- 접촉력 상한, proximal contact 또는 slip 악화 시 residual veto

## 7. 교사 제어기와 초기화

TRANSPORT를 처음부터 PPO로 탐색시키지 않는다. 안전한 결정론적 교사로 경로를 생성한 뒤 residual
behavior cloning과 PPO 순서로 학습한다.

### 7.1 기타 목표 twist

```text
v_ref = clip(kp_pos * position_error - kd_pos * guitar_velocity, 0.08 m/s)
omega_ref = clip(kp_rot * rotation_log_error - kd_rot * guitar_omega, 0.25 rad/s)
```

이 twist는 직접 기타에 가하지 않는다. root twist를 grip point의 강체 twist로 변환한 뒤 왼팔
resolved-rate IK의 wrist/palm 목표로 사용한다.

```text
r = p_grip - p_root
v_grip_ref = v_ref + omega_ref x r
omega_grip_ref = omega_ref
```

회전 중 `omega x r`을 생략해 손과 기타 사이에 인위적인 slip을 만들지 않는다.

### 7.2 장력·그립 기반 속도 조절

```text
path_rate = base_rate
path_rate *= grip_quality_scale
path_rate *= strap_margin_scale
```

- functional grip margin이 작아지면 정지
- strap tension soft limit 접근 시 정지 또는 작은 반대 방향 완화
- hard limit 초과, contact loss, proximal collision은 즉시 실패
- 교사가 접촉력을 회복하려고 기타를 왕복시키지 않음

strap soft limit은 구현 전에 nominal functional-grip/transport trace에서 tension, extension ratio,
tension-rate의 p95/p99를 측정해 별도 `TRANSPORT_STRAP_LIMITS.json`에 봉인한다. manifest에는
`soft_stop`, `resume`(soft_stop보다 낮은 hysteresis), `hard_fail`, 최소 3개 값을 각 channel별로
둔다. 현재 hard limit 300 N/extension ratio 0.01을 soft limit처럼 재사용하지 않는다.

## 8. 보상

성공 truth와 보상을 분리한다. 성공은 3절과 functional grip의 논리곱이고, 보상은 그 방향으로
학습을 유도할 뿐이다.

### 8.1 pose potential

```text
C_pos = clamp(||position_error|| / d_scale, 0, 1)
C_rot = clamp(rotation_error_rad / r_scale, 0, 1)
C_vel = clamp(linear_speed / v_scale, 0, 1)
C_omega = clamp(angular_speed / w_scale, 0, 1)

C_path = weighted cost from current path-reference pose/twist error
C_final = weighted cost from final target pose error

C_transport = 0.70*C_path + 0.30*C_final
Phi_transport = 1 - C_transport
r_progress = gamma*Phi_next - Phi_current
```

위 가중합은 shaping에만 사용한다. 성공 판정은 반드시 position과 rotation을 개별 통과한다.
MOVE에서는 현재 path-reference pose/twist 오차를 주 shaping으로 사용하고, final target potential은
경로 진행을 보조하는 작은 항으로만 사용한다. 실제 기타 선속도 `>0.10 m/s`, 각속도
`>0.35 rad/s`, path corridor overshoot는 soft cost 및 연속 6 frame policy failure로 처리해 기타를
빠르게 던진 뒤 SETTLE하는 우회를 막는다.

### 8.2 grip 유지 보상

- thumb rear contact 유지
- 최소 2 opposing digit 유지
- force opposition과 balance margin 증가
- slip 감소
- 권장 contact 영역 중심에 가까울수록 작은 품질 보상

grip quality의 절대 보상은 작게 두고, 접촉을 강하게 누른 채 이동하지 않는 정책이 pose 진행보다
유리해지지 않게 한다.

### 8.3 비용

- raw force가 soft operating band를 넘는 초과분
- proximal contact, penetration, self-contact
- strap soft tension 초과와 tension rate
- action rate, joint acceleration, wrist jerk
- torso deviation과 joint-limit margin 감소
- 목표 근처의 기타 속도와 진동

### 8.4 outcome

- TRANSPORT 성공: `+5`, 한 번만 지급
- 정책 실패: `-5`, 한 번만 지급
- 매 nonterminal step: `-(1-gamma)*5`

실제 수치는 reward-channel magnitude trace를 보고 정규화한다. 왕복하거나 성공을 늦춰 terminal
discount를 악용할 수 없는지 단위 테스트한다.

성공과 실패 terminal 모두 `Phi_next=0`으로 마스킹한다. terminal 직전의 남은 potential이 실패
정책에 지급되지 않는지, 같은 시작/끝/horizon의 정지·왕복 trajectory가 다른 shaping return을
얻지 않는지 단위 테스트한다.

## 9. 실패와 복구

### 즉시 실패

- NaN/Inf 또는 관측/action contract 불일치
- strap hard tension/extension 초과
- strap hard tension-rate 초과
- per-body contact `>40 N` 또는 whole-hand operating limit 초과
- 기타가 허용 envelope/바닥 아래로 이탈
- 심한 관통, proximal collision, joint/velocity blow-up

### 짧은 loss dwell 후 실패

- 엄지 뒤쪽 접촉 상실 6 frame
- opposing digit 수가 2 미만인 상태 6 frame
- slip `>0.08 m/s`가 10 frame
- functional grip 전체 조건 상실 12 frame
- 실제 기타 선속도/각속도 cap 초과 6 frame

phase hard timeout은 기준 경로 길이와 속도 cap으로 계산한다.

```text
path_duration = 1.5 * max(path_length/0.08, rotation_length/0.25)
nominal_move_frames = ceil(path_duration * 60)
transport_timeout = max(300, 3*nominal_move_frames + 180 settle frames)
```

`1.5`는 cubic smoothstep의 최대 미분값이다. 구현에서는 가능하면 위 근사 대신 실제 생성된
reference-path duration을 timeout 계산에 직접 사용한다.

path rate가 grip/strap margin 때문에 0인 상태가 120 frame 지속되면 timeout을 기다리지 않고
`transport_stalled`로 실패 처리한다.

첫 버전은 TRANSPORT 중 GRIP으로 되돌아가 재획득하지 않는다. 실패 snapshot은 별도의 grip-recovery
데이터로 저장하고 episode를 종료한다. 이렇게 해야 TRANSPORT reward를 반복 수집하지 않는다.

## 10. 커리큘럼

각 단계는 고정 evaluation seed를 통과한 뒤에만 다음으로 승급한다.

1. `T0 HOLD`: target=current pose, 120 frame 그립 유지
2. `T1 TRANSLATE`: 회전 고정, 2→5→10 cm 위치 이동
3. `T2 ROTATE`: 위치 고정, 3→6→12 deg 회전
4. `T3 COUPLED_NEAR`: 위치 5 cm + 회전 6 deg 동시 이동
5. `T4 DISTANCE_LADDER`: 실제 functional-grip snapshot→target 거리/회전 분포의
   25→50→75→100 percentile 순서로 확대
6. `T5 INITIAL_POSE`: 모든 snapshot에서 authored initial pose 복원
7. `T6 RANDOMIZED`: grip snapshot, 기타 mass/friction, 작은 sensor noise/latency
8. `T7 END_TO_END`: release→WAIT→REACH→WRAP→GRIP→TRANSPORT

각 batch의 reset 혼합:

- 70% 현재 curriculum 단계의 functional-grip snapshot
- 20% 한 단계 이전 snapshot
- 10% grip boundary snapshot

strap stiffness/damping/route randomization은 nominal 성공 이후 별도 profile로 연다.

## 11. 네트워크와 학습

- block별 `Linear + ELU` encoder, 각 64~128D
- phase/substage embedding 결합
- shared trunk `512 -> 256`
- TRANSPORT 전용 actor head: shoulder/elbow/wrist 9D residual
- checkpoint action manifest: stochastic output 9D, fixed proximal mask 6D,
  pressure-controller hand output 21D, executed action 36D
- asymmetric critic: 정확한 mass/inertia, friction, strap parameter, 외력을 privileged input으로 사용
- GRU는 사용하지 않음; history 입력으로 부족하다는 ablation이 있을 때만 추가

학습 순서:

1. 교사 rollout 수집 및 실패 trace 제거
2. arm residual behavior cloning
3. teacher trust region 안에서 PPO
4. trust region 단계적 완화
5. 필요할 때만 작은 hand residual fine-tuning

현재 실패한 GRIP learned checkpoint의 weight를 부모로 사용하지 않는다. GRIP teacher/reference와
functional-grip snapshot을 초기화 근거로 사용하고 TRANSPORT checkpoint에 provenance를 기록한다.

## 12. 검증 및 승급 기준

nominal 100 episode와 held-out 100 episode를 별도로 평가한다.

### 필수 metric

- TRANSPORT 성공률
- position error p50/p95
- rotation error p50/p95
- target dwell 중 linear/angular speed p95
- functional grip retention rate
- active digit 수와 digit별 force p95
- slip p95
- strap tension/rate p95
- whole-hand load p95/max
- torso deviation, action jerk
- 실패 reason histogram

### 1차 승급 기준

- nominal 성공률 `>=90%`
- held-out 성공률 `>=80%`
- position p95 `<=2 cm`, rotation p95 `<=6 deg`
- grip retention `>=95%`
- overload/proximal collision `0건`
- target dwell 30 frame 완료
- 고정 GRIP regression seed에서 성공률 저하 `<=5%p`

평균 reward만으로 승급하지 않는다.

## 13. 구현 순서

- [x] functional-grip 영역/힘 manifest 작성
- [x] nominal collision-proxy attribution 검증 및 functional-grip 전용 flag 개방
- [x] 기존 all-five exact-patch 성공 gate와 별도로 functional-grip truth 구현
- [ ] functional-grip snapshot capture/restore 구현 및 검증 영상 생성
- [x] authored release guitar pose를 target state로 저장
- [x] TRANSPORT 191D observation / 9D action 계약 구현
- [x] 9D actor + fixed 6D proximal + 21D pressure controller의 단일 36D 실행 경로 구현
- [x] SECURE/MOVE/SETTLE PhaseManager 구현
- [x] hand pressure-maintenance controller 분리
- [ ] strap pivot을 포함한 SE(3) transport teacher와 reference path 구현
- [ ] reward/termination 상태기계 전체 단위 테스트(성공/안전 마스킹 및 회전 helper는 완료)
- [ ] strap soft/resume/hard limit trace 보정과 manifest 작성
- [x] T0.5 5 mm 교사 rollout 및 영상 검증
- [ ] 승격 가능한 교사 궤적을 사용한 BC warm start 후 PPO 학습
- [x] 단일 seed 진단 TRANSPORT 영상 생성
- [ ] nominal/held-out 평가와 승격용 TRANSPORT 영상 생성

첫 구현 milestone은 `functional-grip snapshot -> T0 HOLD -> T1 2 cm translation`이다. 이 세 단계가
검증되기 전에는 전체 초기 pose 운반이나 MAINTAIN 학습으로 확대하지 않는다.
