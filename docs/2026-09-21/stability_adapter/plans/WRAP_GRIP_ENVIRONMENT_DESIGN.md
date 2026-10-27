# StabilityAdapter WRAP·GRIP 환경 상세 설계

## 1. 목적과 범위

이번 구현 단위의 목적은 REACH가 만든 손바닥-넥 안정 접촉을 실제 획득 그립으로 전환하는 것이다.

```text
REACH_HOLD
  → WRAP_THUMB
  → WRAP_FINGERS
  → WRAP_SETTLE
  → GRIP_CLOSE
  → GRIP_BALANCE
  → GRIP_HOLD
  → ACQUISITION_GRIP_READY
```

WRAP과 GRIP의 책임은 분리한다.

- `WRAP`: 엄지와 손가락을 목표 면에 저속·저접촉으로 배치한다.
- `GRIP`: 배치된 손가락의 힘을 증가시켜 반대쪽 접촉, force balance, 낮은 slip을 만든다.
- `TRANSPORT`: 검증된 그립을 유지하면서 기타 pose를 이동한다. 이번 범위에 포함하지 않는다.

현재 순수 REACH residual checkpoint는 standalone 실행에 실패했으므로 WRAP reset source로 쓰지 않는다.
초기 구현은 검증된 REACH 교사의 `contact-acquired hold` snapshot을 사용한다. 전체 연결 학습은 WRAP과
GRIP이 각각 독립 승급한 뒤 수행한다.

## 2. 손과 넥의 기준 좌표

### 2.1 grip frame `H`

기타 local frame `G`에서 다음 축을 정의한다.

- `+y_H`: body에서 nut으로 향하는 넥 축
- `+z_H`: 넥 아래면에서 fretboard 쪽으로 향하는 두께 축
- `+x_H`: 오른손 좌표계를 완성하는 넥 폭 방향

grip station은 기존과 동일하다.

```text
y_grip = y_fret22 + (2/3) * (y_nut - y_fret22) = 0.0675 m
```

현재 runtime collision convex hull의 해당 단면은 다음과 같다.

- 아래면 `z_bottom = -0.013461 m`
- 위면 `z_top ≈ +0.009300 m`
- 반폭 `x_half = 0.036047 m`
- contact frame 중심 `p_H/G = [0, 0.0675, (z_bottom + z_top)/2]`
- contact frame 반두께 `z_half = (z_top - z_bottom)/2 ≈ 0.011381 m`

위 값은 상수로 복사하지 않고 neck collision mesh와 asset hash에서 다시 계산하여
`GRIP_GEOMETRY.json`에 봉인한다.

### 2.2 접촉 목표 영역

초기 목표점 후보는 다음과 같다. 손가락 mesh의 실제 도달 가능 영역을 렌더한 뒤 확정한다.

| 그룹 | 목표 면 | 후보 위치 in `H` | 역할 |
|---|---|---:|---|
| thumb | 아래면 `-z_H` | `(0, +0.012, -z_half)` | 주 opposition 접촉 |
| index | 위면 `+z_H` | `(0, +0.027, +z_half)` | 보조·방향 안정화 |
| middle | 위면 `+z_H` | `(0, +0.009, +z_half)` | 주 gripping contact |
| ring | 위면 `+z_H` | `(0, -0.009, +z_half)` | 주 gripping contact |
| pinky | 위면 `+z_H` | `(0, -0.027, +z_half)` | 보조·토크 안정화 |

점 하나를 맞히게 하지 않고 각 목표를 타원형 surface region으로 정의한다.

- axial tolerance: `±12 mm`
- lateral tolerance: `±15 mm`
- surface-normal distance: WRAP hover `5~12 mm`, contact `≤5 mm`
- 손가락별 목표 region은 겹쳐도 되지만 axial 순서
  `index > middle > ring > pinky`는 바뀌면 안 된다.

각 손가락은 body origin이 아니라 해당 STL의 neck-facing surface sample 중 목표 영역에 가장 가까운
active point를 사용한다. active point는 reward 계산에는 바뀔 수 있지만, 제어 Jacobian과 속도 감쇠는
손가락마다 고정된 control point를 사용한다.

## 3. 접촉 topology와 attribution

### 3.1 GPU 학습용 collision isolation

GPU net-contact tensor에는 collider pair가 없으므로 각 palm/digit body가 neck-root 이외의 물체와
충돌하지 않도록 한 뒤 body별 net force를 사용한다.

초기 filter 후보는 현재 REACH 계약을 확장한다.

```text
neck root shapes       = 4 | 16 = 20
other guitar shapes    = 2 | 16 = 18
palm / active digits   = 1 | 2 | 8 = 11
chair                  = 8
disabled proxy         = 31
left wrist/forearm     = 1 | 2 | 4 | 8 = 15
```

따라서 palm/digit과 neck root만 `filter_a & filter_b == 0`이고 다음 접촉은 차단된다.

- palm/digit ↔ guitar body·fret·nut·proxy
- palm/digit ↔ chair
- palm/digit ↔ 다른 humanoid body 및 서로 간 self-contact
- wrist/forearm ↔ 모든 guitar collision shape

phase 진입 시 다음을 runtime read-back으로 감사한다.

1. guitar root에 접촉 가능한 shape가 정확히 두 neck mesh인지
2. 각 digit chain의 모든 collision shape filter가 예상값인지
3. neck 이외 guitar, chair, humanoid와 공통 blocking bit가 있는지
4. palm과 digit 전체 STL vertex가 ground plane에서 contact offset 이상 떨어져 있는지

filter는 force attribution 수단일 뿐 관통 방지 증거가 아니다. 차단된 pair는 PhysX contact가 생기지
않으므로 다음 보수적 collision geometry를 별도로 만든다.

- palm/digit: runtime cooked shape와 contact offset을 포함하는 convex hull
- non-neck guitar mesh: asset-local convex decomposition과 BVH
- chair: runtime center/orientation/half-extent를 사용하는 exact OBB
- humanoid self-collision: body별 convex hull; asset에서 의도적으로 제외된 인접 관절 pair만 예외
- ground: 모든 hull support vertex의 world minimum height

오프라인에서 원본 collider의 모든 vertex/analytic extent가 proxy 내부에 포함되는지 확인하고 asset·proxy
hash를 manifest에 기록한다. 매 frame GJK/convex-distance 또는 보수적 SDF lower bound로 palm/digit과
모든 비넥 proxy 및 비인접 손가락 사이 signed distance를 계산한다. contact offset을 뺀 거리가
`≤2 mm`이면 `non_neck_clear=false`, 음수면 즉시 관통 failure다. filter read-back과 이 매-frame 거리
gate를 모두 통과해야 접촉 성공을 허용한다.

### 3.2 contact group

contact force는 다음 body group별로 240 Hz 네 substep의 최대값과 impulse를 수집한다.

- thumb: `thumb1`, `thumb2`, `thumb3`
- index: `index1`, `index2`, `index3`
- middle: `middle1`, `middle2`, `middle3`
- ring: `ring1`, `ring2`, `ring3`
- pinky: `pinky1`, `pinky2`, `pinky3`
- palm: `LH:palm`

각 substep에서 먼저 group body들의 force vector를 합한 뒤 normal/tangent를 계산하고, 네 substep의
최대값을 control-frame 값으로 사용한다. 서로 다른 substep에서 나온 body별 최대값을 사후 합산하지
않는다. 개별 body 최대값은 과도 충격 안전 판정용으로 별도 유지한다.

반대쪽 힘이 상쇄되지 않도록 전체 손 안전 load는 vector sum이 아니라 같은 substep의 body별 norm
합으로 정의한다.

```text
F_hand_load[k] = sum_b norm(F_contact_body[b, k])
F_hand_peak = max_k F_hand_load[k]
I_excess += relu(F_hand_load[k] - 20 N) * (1/240 s)
```

`b`에는 palm과 모든 thumb/finger collision body가 포함된다. per-body raw peak도 별도로 유지하며,
reset부터 episode 종료까지 `I_excess`를 누적한다.

성공 접촉은 distal body(`*2`, `*3`)의 힘을 우선 사용한다. proximal `*1` 접촉은 약한 보조 접촉만
허용하며, proximal force가 `2 N`을 넘으면 잘못된 wrap으로 간주한다.

각 target face의 world outward normal에 body net force를 투영한다.

```text
s = dot(F_body, n_target_face_world)
F_normal = relu(s)
F_tangent = norm(F_body - s * n_target_face_world)
```

`s≤0`이면 해당 접촉은 invalid다. 반대 방향 성분을 `abs()`로 뒤집어 정상 접촉으로 처리하지 않는다.

correct-face geometry는 active point 하나로 판정하지 않는다. 각 digit chain의 전체 cooked collision
hull과 neck convex hull 사이 closest/intersection feature를 매 frame 계산한다.

- 지정 distal hull의 closest feature가 해당 target face region과 contact-offset 범위 안에 있어야 한다.
- 같은 digit의 다른 hull feature가 non-target top/bottom/side face에 `contact_offset + 2 mm` 이내로
  접근하면 `wrong_face_geometry=true`다.
- proximal `*1` 보조 접촉을 허용할 때도 closest feature가 target face의 확장 region 안에 있어야 하며
  force는 `2 N` 미만이어야 한다.
- 전체 surface gate와 force 방향 gate를 모두 만족할 때만 `correct_face_contact=true`다.

GPU provisional opposition은 실제 contact normal 대신 force vector를 사용한다.

```text
F_thumb_vec = sum(thumb distal body contact-force vectors)
F_opp_vec = sum(active opposing-finger distal force vectors)
opposition_angle_gpu = acos(dot(unit(F_thumb_vec), unit(F_opp_vec)))
```

두 group 모두 minimum normal force를 만족할 때만 angle이 valid하다. correct-face geometry와
`opposition_angle_gpu ≥150°`를 함께 요구한다.

GPU provisional slip은 손가락마다 고정된 surface control point와 해당 target face의 closest point를
사용한다. 두 점의 rigid-point velocity를 같은 world frame에서 계산하고 target normal 성분을 제거한다.

```text
v_digit = v_digit_body + omega_digit_body × (p_digit - p_digit_com)
v_neck = v_guitar_com + omega_guitar × (p_neck - p_guitar_com)
v_tangent = (I - n_target n_target^T) * (v_digit - v_neck)
```

관측용 slip p95는 최근 30개 contact-active frame의 ring buffer에서 계산하고 최소 20개 유효 sample을
요구한다. GRIP 성공 판정은 120-frame dwell 전체의 contact-active sample p95를 사용하며 5 frame보다
긴 contact gap이 있으면 window를 reset한다.

### 3.3 strict contact proof

GPU isolation 결과는 학습용 provisional truth다. checkpoint 공식 승격에는 CPU-pipeline replay가
필요하다.

- `{digit body, guitar root}` RigidContact pair 확인
- guitar-local contact point가 해당 target face region 안인지 확인
- canonical contact normal이 목표 surface normal과 `25°` 이내인지 확인
- pair별 contact force/impulse가 force band 안인지 확인
- thumb와 opposing-finger contact normal 사이 각도가 `150°` 이상인지 확인
- 기존 REACH strict 계약을 재사용해 `{LH:palm, guitar root}` pair도 확인
- palm contact의 guitar-local point가 grip station 아래면 region 안에 있고 canonical normal이 아래면
  outward normal과 `25°` 이내인지 확인
- palm pair-specific force가 `0.5~8 N` band 안인지 확인

`RigidContact.lambda`의 단위는 가정하지 않는다. 정적 known-load fixture에서 CPU contact lambda 합과
net-contact force tensor를 비교해 `force_N`인지 `impulse_Ns`인지 판별한다. impulse이면
`F=lambda/(1/240 s)`로 변환하며, 변환 mode·scale·검증 오차(목표 `≤5%`)를 runtime manifest에 봉인한다.
strict slip은 실제 contact local point를 world로 변환한 두 rigid-point velocity에서 계산한다. 공식
20/20 replay는 palm strict contact, thumb strict contact, opposing-finger strict contact를 모두 같은
frame에서 AND하며 하나라도 provisional-only이면 승격하지 않는다.

CPU proof가 구현되기 전 checkpoint 상태는 `grip_candidate_pair_unverified`까지만 허용한다.

## 4. phase state machine

### 4.1 WRAP

```text
WRAP_ENTRY
  → THUMB_HOVER
  → THUMB_TOUCH
  → FINGER_HOVER
  → FINGER_TOUCH
  → WRAP_SETTLE
```

#### WRAP_ENTRY

- REACH palm contact를 유지한다.
- 기타 선속도 `≤0.05 m/s`, 각속도 `≤0.15 rad/s`를 다시 확인한다.
- torso와 L_Thorax 목표를 REACH terminal 값에 고정한다.
- palm force가 `1~8 N` 범위가 아니면 WRAP을 시작하지 않는다.

#### THUMB_HOVER / THUMB_TOUCH

- thumb control point를 아래면 목표의 normal 바깥 `8 mm`까지 이동한다.
- hover pose가 15 frame 유지된 뒤 `≤0.03 m/s`로 접근한다.
- `0.5~5 N` thumb normal force를 10 frame 확인한다.
- palm force는 `1~8 N`에서 유지한다.

#### FINGER_HOVER / FINGER_TOUCH

- 네 손가락을 위면 hover region으로 먼저 이동한다.
- middle·ring을 먼저 닫고 index·pinky를 뒤따르게 한다.
- WRAP에서는 각 finger normal force를 `0.3~3 N`으로 제한한다.
- thumb 또는 palm contact가 풀리면 즉시 정지하고 contact-loss recovery로 전환한다.

#### WRAP_SETTLE

다음 조건을 30 control frame 연속 만족하면 GRIP으로 전이한다.

- thumb가 올바른 아래면 region에 접촉
- middle 또는 ring을 포함한 opposing finger 2개 이상이 위면 region에 접촉
- 모든 접촉이 WRAP low-force band 안에 있음
- fingertip axial 순서가 유지됨
- palm-up `≤25°`, grip heading `≤25°`
- 기타/손 상대속도 `≤0.05 m/s`
- digit 조기·잘못된 면 접촉, 과도 힘, strap 위반 없음

### 4.2 GRIP

```text
GRIP_ENTRY
  → CLOSE_SYNERGY
  → FORCE_BALANCE
  → GRIP_HOLD
  → ACQUISITION_GRIP_READY
```

#### CLOSE_SYNERGY

- WRAP terminal action에서 시작한다.
- finger flexion을 한 번에 닫지 않고 `middle/ring → index → pinky` 순서로 증가시킨다.
- thumb는 position controller보다 compliant force target을 우선한다.
- arm/wrist는 grip frame을 따라가되 torso/L_Thorax는 고정한다.

#### FORCE_BALANCE

초기 force 후보는 다음과 같다.

| 항목 | 진입/유지 band |
|---|---:|
| thumb normal force | `2~8 N` |
| opposing fingers aggregate | `2~10 N` |
| 각 active finger | `0.5~5 N` |
| palm support | `0.5~8 N` |
| proximal phalanx | `<2 N` |
| 개별 body raw peak | `<12 N` |
| 전체 왼손 raw peak | `<30 N` |

thumb와 opposing force의 balance ratio는 다음처럼 계산한다.

```text
balance_error = abs(F_thumb - F_opposing) / max(F_thumb + F_opposing, eps)
```

초기 통과값은 `balance_error ≤0.35`다.

#### GRIP_HOLD

다음 조건을 120 frame(2초) 연속 만족하면 `ACQUISITION_GRIP_READY`다.

- thumb 아래면 contact active
- opposing finger 2개 이상 contact active, 그중 middle 또는 ring 포함
- thumb/opposing normal angle `≥150°`
- palm support contact가 `0.5~8 N`에서 active
- force band와 balance 조건 통과
- digit-neck tangential slip p95 `≤0.02 m/s`
- hand-guitar 상대 선속도 `≤0.02 m/s`
- 상대 각속도 `≤0.15 rad/s`
- 기타 선속도 `≤0.05 m/s`, 각속도 `≤0.15 rad/s`
- palm-up `≤30°`, torso `≤2.5°`, L_Thorax `≤15°` excursion
- strap extension/tension, contact impulse, ground clearance 안전 조건 통과

`ACQUISITION_GRIP_READY`는 운반 준비 상태일 뿐 `MAINTAIN_READY`나 연주 가능 상태가 아니다.

## 5. 관측 입력

flat index를 코드에 직접 쓰지 않고 `GRIP_OBSERVATION_V1.json`에서 named block과 slice를 생성한다.

| Block | 내용 | Frame |
|---|---|---|
| `O_phase` | WRAP/GRIP substage one-hot, phase time, dwell fraction | scalar |
| `O_proprio` | 소유 36 DoF q/dq = 72D | joint local |
| `O_guitar` | guitar pose, linear/angular velocity, projected gravity | `H`/world |
| `O_palm` | palm pose/velocity, palm-up, heading, contact force | `H` |
| `O_digits` | thumb+4 fingertip control point 위치/속도, target error | `H` |
| `O_contact` | 5 digit group별 raw/filtered normal, tangent, active/loss streak | target face |
| `O_grip` | opposition angle, force balance, active finger count, slip p95 | scalar |
| `O_strap` | length ratio, tension, tension rate, anchor motion | guitar/world |
| `O_safety` | 36D joint-limit margin, 비넥 signed distance, ground clearance, penetration, force/impulse margin | scalar |
| `O_history` | 이전 executed action, 이전 grip quality, 이전 force error | mixed |

첫 구현의 예상 크기는 약 190~220D지만, 실제 크기는 runtime body/DoF manifest에서 생성한다.
정책 입력에는 GPU에서 실제 얻을 수 있는 provisional contact만 사용한다. 정확한 randomization과
unclipped provisional force는 critic용 privileged block에 둘 수 있지만, GPU rollout 중 존재하지 않는
CPU contact pair는 actor나 critic에 넣지 않는다. CPU pair 정보는 promotion 평가에서만 사용한다.

## 6. 정책 출력과 제어 권한

현재 REACH가 torso/L_Thorax를 포함한 15D를 사용하므로 기존 문서의 30D ABI가 아니라 다음 36D를
정본으로 사용한다.

```text
Torso 3 + L_Thorax 3
+ L_Shoulder 3 + L_Elbow 3 + L_Wrist 3
+ left hand 21
= 36D
```

phase mask는 다음과 같다.

- WRAP: arm/wrist 9D + hand 21D 활성, torso/L_Thorax 6D 고정
- GRIP: wrist·arm 소형 residual + hand 21D 활성, torso/L_Thorax 6D 고정
- force safety shield: action 이후 항상 적용하며 policy가 우회할 수 없음

joint target 실행 순서는 하나로 고정한다.

```text
phase reference + bounded residual
  → joint soft-limit
  → per-joint rate cap
  → EMA
  → PD
  → effort clamp
```

초기 rate cap 후보:

- finger flexion: `2°/control frame`
- finger ab/adduction: `1°/frame`
- wrist: `1°/frame`
- shoulder/elbow: REACH terminal action 기준 normalized `0.01/frame`
- 접촉 후 normal 방향 fingertip speed: `≤0.03 m/s`

## 7. 신경망 구조

긴 REACH 상태기를 그대로 압축한 무상태 residual MLP가 실패했으므로 WRAP/GRIP은 phase와 contact
state를 명시적으로 입력하고 head를 분리한다.

```text
proprio encoder      72D → 128 → 96
hand/target encoder       → 128 → 96
contact/grip encoder      → 96  → 64
guitar/strap encoder      → 64  → 48
phase embedding                  16
              concat → 384 → 256
                    ├─ WRAP actor head → 36D mean
                    ├─ GRIP actor head → 36D mean
                    └─ phase value heads
```

- activation: ELU
- actor output: tanh-squashed Gaussian
- action mask 밖의 joint는 log-prob/entropy에서 제외
- critic은 정확한 randomization과 unclipped provisional force를 추가로 받는 asymmetric critic
- v1에는 RNN을 넣지 않는다. force/slip history로 chatter 구분이 안 된다는 ablation 후에만 GRU 추가

처음부터 순수 PPO로 접촉을 탐색하지 않는다.

1. deterministic IK + synergy + compliant force teacher 생성
2. teacher trajectory behavior cloning
3. learner 방문 상태에서 DAgger relabeling
4. teacher intervention safety shield를 유지한 PPO fine-tuning

접촉 중 teacher와 learner action을 단순 선형 혼합하면 force spike가 생길 수 있으므로, mixture 대신
frame 단위 intervention/veto를 사용한다.

## 8. 보상 구조

`gamma=0.99`, `Phi=1-C`의 discount-correct potential shaping을 유지한다.

### 8.1 WRAP cost

```text
C_wrap = 0.30 * digit_target_distance
       + 0.15 * correct_side_clearance
       + 0.15 * palm_pose_hold
       + 0.15 * opposition_preparation
       + 0.10 * digit_relative_speed
       + 0.10 * guitar_motion
       + 0.05 * joint_margin
```

추가 penalty:

- 목표 반대 면 접촉
- 손가락 순서 교차
- proximal phalanx 과접촉
- palm/thumb 지지 접촉 상실
- action rate, force overshoot, guitar acceleration

### 8.2 GRIP quality와 cost

각 품질을 `[0,1]`로 정규화한다.

```text
Q_grip = min(
    Q_thumb_contact,
    Q_opposing_contact,
    Q_opposition_angle,
    Q_force_band,
    Q_force_balance,
    Q_slip,
    Q_hand_guitar_sync
)
C_grip = 1 - Q_grip
```

최솟값을 사용하므로 큰 힘 하나로 다른 실패 조건을 평균내어 숨길 수 없다. 실제 phase success는
reward threshold가 아니라 4.2의 모든 boolean gate를 AND하여 판정한다.

```text
r_shape = gamma * Phi(next) - Phi(current)
r = r_shape
  - time_cost
  - action_rate_cost
  - excessive_force_cost
  - guitar_acceleration_cost
  + one_time_success_reward
  - one_time_failure_penalty
```

success/failure terminal reward는 정확히 한 번만 지급한다.

## 9. 안전·종료 조건

다음은 즉시 hard failure다.

- thumb가 위면, opposing finger가 아래면에 `>1 N`으로 먼저 접촉
- 개별 digit raw force `≥20 N` 또는 전체 손 force `≥40 N`
- `20 N` 초과 force impulse 누적 `≥2 N·s`
- digit/palm이 neck 이외 기타 shape, chair, humanoid, ground와 접촉할 가능성
- 기타 drop, strap 최대 extension/tension 위반
- NaN/Inf, joint hard limit, 비정상 관통 또는 velocity blow-up
- WRAP `1,200 frame`, GRIP `1,200 frame` timeout

다음은 즉시 실패 대신 제한된 recovery를 허용한다.

- thumb/palm 접촉이 5 frame 미만 끊김: 저속 재접근
- opposing finger 하나가 5 frame 미만 slip: 해당 finger만 감압 후 재접촉
- force band 상단 초과가 30 N 미만: normal 방향 retreat

recovery는 phase당 최대 2회로 제한한다. 반복적인 접촉 해제로 보상을 수집하지 못하도록 세 번째
손실은 episode failure로 종료한다.

## 10. reset과 curriculum

### 10.1 snapshot

- `WRAP_RESET`: 검증된 REACH teacher hold terminal snapshot
- `GRIP_RESET`: 검증된 WRAP low-force terminal snapshot

snapshot에는 root/DoF state뿐 아니라 다음도 포함한다.

- strap elapsed/max length와 route state
- PD target과 previous action
- phase 시작 joint reference와 action manifest hash
- collision filter contract hash

teleport reset에서는 filtered force, contact active/loss streak, dwell, slip window와 recovery count를 모두
0으로 초기화한다. root/DoF/strap 복원 후 collision filter를 다시 설치·감사하고, held action으로 최소
1 physics control step을 진행한다. warm-up frame은 reward와 success dwell에 포함하지 않는다.

- `WRAP_RESET`: palm correct-face contact `1~8 N`을 10 frame 재확인하고 모든 digit force가 `0.2 N`
  미만인지 확인한다. thumb 접촉을 요구하면 안 된다.
- `GRIP_RESET`: palm support, thumb 아래면, opposing finger 2개 이상과 correct-face/WRAP low-force
  band를 10 frame 재확인한다. 하나라도 재형성되지 않으면 snapshot을 사용하지 않는다.

실제 episode 안에서 WRAP→GRIP이 무중단 전이할 때만 같은 frame에서 재측정한 contact state를 넘긴다.
이 경우에도 GRIP success dwell과 slip p95 window는 0에서 시작한다. excess impulse는 WRAP reset부터
누적한 값을 그대로 이어받아 앞 단계의 충격을 숨기지 않는다.

현재 실패한 REACH policy checkpoint에서 snapshot을 수집하지 않는다.

### 10.2 curriculum

1. nominal 1-env WRAP teacher
2. nominal 1-env GRIP teacher
3. hand joint `±2°`, guitar pose `±5 mm/±2°`
4. 초기 기타 속도 `≤0.02 m/s`, `≤0.05 rad/s`
5. neck friction과 guitar mass를 한 항목씩 randomize
6. 이전 REACH snapshot을 20% 섞어 end-to-end regression

한 번에 여러 물리 parameter를 열지 않는다. 각 단계 승급 시 nominal seed를 다시 평가한다.

## 11. 검증과 승급 기준

### WRAP

- nominal 20/20 성공
- randomized 50 seeds 성공률 `≥95%`
- 잘못된 면 접촉 0건
- raw force `20 N` 이상 0건
- terminal digit target error p95 `≤12 mm`

### GRIP

- nominal 20/20 provisional hold 성공
- randomized 50 seeds 성공률 `≥90%`
- 2초 hold 중 contact 유지율 `≥99%`
- slip p95 `≤0.02 m/s`
- force band 위반 frame 비율 `<1%`
- strap/environment failure 0건
- CPU strict replay 20/20 통과 후에만 공식 checkpoint 승격

필수 영상:

1. WRAP close-up: thumb와 네 finger target/active point 표시
2. GRIP close-up: digit별 normal force, balance, slip overlay
3. 전체 자세: torso/L_Thorax excursion과 기타/strap 움직임
4. 실패 영상: wrong-face, force overshoot, contact-loss recovery 각각 1개

## 12. Synchronizer와 handoff

WRAP·GRIP 동안 Fret/Strike checkpoint는 frozen inference와 log만 허용하고 physical action에는 섞지
않는다. score clock도 시작하지 않는다.

`ACQUISITION_GRIP_READY`는 Transport 입력이다. 이 그립은 4~5프렛 사이를 점유하므로 그대로는 Fret
연주 손으로 사용할 수 없다. 향후 `MAINTAIN_READY`에서 strap/body/thigh support가 손가락을 풀어도
기타를 유지한다는 별도 gate를 통과한 후에만 finger ownership을 Fret으로 넘긴다.

따라서 이번 GRIP 성공 조건에 Synchronizer fret/strike 성능을 포함하지 않는다.

## 13. 구현 순서

- [ ] P0: digit별 runtime body/shape/filter/contact topology JSON 생성
- [ ] P0: thumb/fingertip STL surface와 target region 렌더
- [ ] P0: GPU isolation 및 CPU RigidContact pair probe
- [ ] P1: `GRIP_GEOMETRY.json`, observation/action/reward manifest 생성
- [ ] P1: 36D phase mask, per-joint cap, single EMA/PD 실행 경로
- [ ] P2: WRAP 환경·teacher·snapshot·진단 영상
- [ ] P2: WRAP nominal 20/20 통과
- [ ] P3: GRIP compliant teacher와 force/slip state machine
- [ ] P3: GRIP nominal 20/20 provisional hold 통과
- [ ] P4: WRAP/GRIP BC + DAgger + safety-intervention PPO
- [ ] P4: 독립 learner-only 평가와 실패 checkpoint 분리
- [ ] P5: CPU strict replay와 공식 checkpoint promotion
- [ ] P5: REACH→WRAP→GRIP 통합 regression 영상

첫 구현은 학습부터 시작하지 않는다. P0 topology/target 렌더와 P1 계약을 먼저 고정하고, WRAP
teacher가 저접촉 배치를 재현한 뒤 GRIP force 제어를 추가한다.
