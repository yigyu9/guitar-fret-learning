# 04. Strike

> 상태: **STRIKE-V2 303D 구현 / full-song 평가 기록 존재 / source 승급 미완료**

## 한 줄 정의

Strike는 `StrikeEvent`를 받아 오른팔·오른손으로 올바른 pick crossing 또는 strum traversal을
만들고, 그 뒤의 recovery까지 수행하는 곡별 오른손 skill prior다. 학습된 weight는 해당
곡의 G0→G2에서 재사용한다.

Strike는 Fret-ready를 만들거나 기타를 지지하지 않는다. Strike의 성공 여부는 actor의 의도가 아니라 crossing/event detector가 판정한다.

Single picking과 strumming은 별도 정책으로 나누지 않는다. 하나의
`StrikeMotorPolicy`가 event의 target string mask, 방향, 줄별 timing offset과 sweep
duration을 조건으로 두 동작을 모두 수행한다.

## 입력

### StrikeEvent

```text
StrikeEvent {
    event_id
    score_time_s
    gesture                  # single_pick / strum
    traversal_mask[6]
    audible_mask[6]
    string_offset_s[6]
    musical_direction
    physical_direction
    sweep_duration_s
    approach_lead_s
    timing_window
    recovery_deadline_s
    next_event_id
}
```

이 event는 오디오에서 매 frame 직접 추출되는 것이 아니라, Tablature와 연주 형태를 offline compiler가 만든 결과다. Strike는 필요하면 이 event를 현재 기타 geometry에 투영한다.

### 물리 상태

```text
- right shoulder/elbow/wrist/hand q, qdot
- R_Thorax pose/twist relative to guitar
- palm/pick pose/twist relative to guitar
- projected gravity in R_Thorax frame
- grip quality and forbidden-region clearance margin
- motor phase and detector state
- released traversal mask
- ready dwell, detector rearm and recovery state
- Synchronizer release/timing command
- previous executed action
```

Strike source가 기타 world pose/twist, 안정성용 raw contact force, strap 장력이나
slip을 직접 보지는 않는다. 움직이는 기타에서도 `R_Thorax`, palm과 pick의 기타 상대
pose/twist는 live로 유지한다.

## 출력

### 직접 action

```text
a_raw ∈ [-1, 1]^30
```

```text
R_Shoulder : 3
R_Elbow    : 3
R_Wrist    : 3
RH hand    : 21
----------------
합계       : 30
```

이 30D 출력은 기존 Strike checkpoint의 joint name/order, action scaling, joint-limit
mapping, EMA와 PD target semantics를 그대로 사용한다. StrikeMotorPolicy 자체를
residual policy로 바꾸지 않는다. FullBodyPlayer에서 필요한 안정화 보정은 중앙
`ActionArbiter`가 허용된 named joint에만 별도로 합성한다.

### 구조화된 side output

```text
StrikeIntent {
    event_id
    motor_phase
    desired_crossing_time
    desired_direction
    target_traversal_mask
    approach_ready
    predicted_release_confidence
}
```

이 side output은 Synchronizer와 진단기가 사용할 수 있지만, 실제 strike 성공 판정의 truth가 아니다.

## 상태공간

```text
s_t = (x_t, z_t, m_t, h_t)
```

### 물리 상태 `x_t`

```text
right-chain q, qdot
R_Thorax-to-guitar relative pose/twist
palm/pick-to-guitar relative pose/twist
projected gravity
grip quality and forbidden-region clearance
```

### 음악 목표 상태 `z_t`

```text
current event id/time
target string masks
direction
per-string timing offset
sweep duration
next-event summary
```

### 실행 상태 `m_t`

```text
motor_phase ∈ {READY, APPROACH, RELEASE_RECOVER}
detector_armed
ready_streak
event_resolved
released_mask[6]
last_release_time[6]
recovery clearance/progress
wrong-crossing state
```

### history `h_t`

```text
previous executed action
```

위 상태가 actor observation에 표현되지 않으면 policy 관점에서는 부분 관측이 된다. 따라서 phase, ready dwell, recovery, detector armed, 이전 실행 action을 명시적인 observation block으로 둔다.

## 모델 구성

### 1. StrikeEventCompiler

학습 모델이 아니다.

```text
입력  : Canonical PlayEvent + picking profile + tempo
출력  : StrikeEventSequence
```

single pick, strum, 줄별 offset, direction, sweep duration, recovery deadline을 생성한다.

### 2. StrikeGoalProjector

학습 모델이 아니다.

```text
입력  : current StrikeEvent + live guitar geometry
출력  : ready, entry, exit, final-string target, lane, depth
```

기타가 움직여도 기타 좌표계에서 target geometry를 다시 계산한다.

### 3. StrikePhaseMachine

학습 모델이 아니다.

```text
READY
  → approach lead 도달
  → APPROACH

APPROACH
  → 올바른 crossing
  → RELEASE_RECOVER

APPROACH
  → deadline 초과
  → MISS / FAILED

RELEASE_RECOVER
  → rearm + clearance + next handoff
  → 다음 event
```

Strum은 마지막 required string까지 crossing되고 order/direction 조건이 맞아야 완료된다.

### 4. GripController

초기에는 reference 기반 deterministic controller다.

```text
입력  : canonical grip reference + RH joint state
출력  : grip reference target + residual span + grip quality
```

현재 [PickGripReference와 grip reward](/home/ajou/yigyu/3/tab2body/env/rewards/strike.py)를 기반으로 한다. 곡이나 event에 따라 그립을 바꾸지 않으며 single picking과 strumming에 같은 canonical grip을 사용한다. 여러 pick style과 grip switching은 후속 확장으로 분리한다.

### 5. StrikeMotorPolicy

Strike의 핵심 학습 actor다.

동일한 actor와 30D action 계약을 single picking과 strumming에 공통으로 사용한다.
학습 curriculum만 single-string crossing에서 인접 줄, 다중 줄 strumming 순으로
확장한다.

```text
11 named observation block
        ↓ 각각 Linear + ELU encoder
encoded feature concat
        ↓ 512 → 256 fusion MLP
single 30D action-mean head
```

actor와 critic은 같은 303D block 계약을 사용하지만 encoder와 fusion parameter는 공유하지
않는다. 현재 구현은 arm/hand별 head나 auxiliary head를 두지 않고, 하나의 30D
distribution으로 관절 간 협응을 학습한다.

```text
μ ∈ R^30
logσ ∈ R^30
a ~ TanhNormal(μ, σ)
```

crossing 성공은 policy 출력이 아니라 detector가 판정한다.

### 6. PickStrikeDetector

```text
입력  : previous/current pick position in G, string segments, dt
출력  : release mask, crossing position/time, direction, false positive
```

현재 [strike detector](/home/ajou/yigyu/3/tab2body/env/strike_detector.py)의 swept crossing, depth, speed, displacement, rearm, debounce를 기본으로 재사용한다.

메인 연구에서는 다음 첫 번째 계약을 사용한다.

```text
KinematicStrikeDetector
    pick marker가 줄을 통과했는가

PhysicalStrikeDetector
    실제 pick/string 접촉과 충격이 발생했는가
```

기타 줄은 기타 좌표계에 고정된 가상 geometry이며 실제 collision object로 만들지 않는다.
실제 string 변형, contact solver와 음향 합성은 메인 범위에서 제외한다. 가상 crossing은
음악 event만 생성하며 기타에 force, torque 또는 impulse를 적용하지 않는다.

### 7. RecoveryPlanner

```text
입력  : completed event, next event, direction, clearance, time budget
출력  : clearance target, next approach target, handoff feasibility
```

초기에는 deterministic planner로 두고, actor는 planner가 제공하는 target을 따라간다.

### 8. SafetyFilter

```text
policy action
→ grip constraint
→ phase/action mask
→ joint limit
→ rate limit
→ EMA
→ PD target
```

penetration, velocity blowup, invalid crossing은 reward가 아니라 hard safety 조건으로도 관리한다.

## Observation block

```text
O_proprio                  60
O_arm_anchor               18
O_hand_geometry            30
O_grip_safety               7
O_current_event            32
O_target_geometry          25
O_lookahead                52
O_phase_detector           29
O_recovery                 18
O_synchronizer              2
O_history                  30
-----------------------------
total                     303
```

`strike.observation.v2`의 세부 구성은 다음과 같다.

- `O_proprio`: 오른팔·오른손 30관절의 `q, qdot`
- `O_arm_anchor`: `R_Thorax`의 guitar-relative position 3, rotation-6D 6,
  relative linear/angular velocity 6, projected gravity 3
- `O_hand_geometry`: palm과 pick 각각의 guitar-relative position 3,
  rotation-6D 6, relative linear/angular velocity 6
- `O_grip_safety`: total/pinch/free grip quality 3과 금지 영역별 normalized
  penetration safety margin 4. 물체 밖에서는 1, 허용 penetration 한계에서는 0,
  한계를 넘으면 음수가 된다.
- `O_current_event`: valid, gesture, traversal/audible mask, 줄별 offset,
  musical/motor direction, sweep, timing window, approach lead와 tempo
- `O_target_geometry`: ready/entry/exit/active target vector 12, lane offset 1,
  current/next required string one-hot 12
- `O_lookahead`: 이후 두 event를 각각 26D로 encoding
- `O_phase_detector`: motor phase, ready dwell, resolved/completed state,
  string별 armed/rearm progress와 last-release pulse
- `O_recovery`: context/mode, progress, required/available budget,
  clearance state, recovery/next-entry target과 direction
- `O_synchronizer`: `release_enable`, supervisor timing offset
- `O_history`: 최종 실행된 Strike 30D action slice

기존 327D는 `strike-v1` baseline이다. `strike-v2`는 observation이 다르므로 기존
checkpoint를 직접 resume하지 않는다. 기본 학습 설정은 v2를 선택하고, v1은 명시적인
호환 모드로만 선택한다. 관측 ABI는
[strike_v2_contract.py](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py), actor/critic은
[strike_v2_model.py](/home/ajou/yigyu/3/tab2body/learning/strike_v2_model.py), 환경 조립은
[task_strike.py](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py)에 있다.

`O_synchronizer`의 timing offset은 목표 시각, timing reward와 recovery handoff 시각에
동일하게 적용된다. `release_enable=0` 동안 발생한 물리 crossing은 detector 기록에는
남지만 올바른 event로 채점되지 않으며 wrong crossing으로 계산된다. 독립 Strike
학습에서는 기본값 `(release_enable=1, timing_offset=0)`을 사용한다.

## Reward

- grip quality와 ready dwell
- ready/entry/exit 접근 progress
- 정확한 string crossing
- 올바른 방향과 순서
- crossing depth와 속도
- per-string timing error
- strum traversal completion
- sweep duration
- recovery clearance와 next-event handoff
- wrong crossing, duplicate crossing, premature release
- joint limit, penetration, action jerk

timing은 다음처럼 줄별로 계산한다.

```text
timing_error_i = actual_release_i
               - (event_time + string_offset_i)
```

늦은 crossing이 deadline을 넘으면 성공으로 바꾸지 않고 miss/skip으로 기록한다.

## 학습 순서

```text
A0 pick grip
A1 tip ready
A2 single crossing
A3 timed single
├─ single-only 곡 ─────────────────────────────→ S3 song integration
└─ strum 포함 곡 → A4 recovery → S0 two-string strum
                  → S1 strum span/order → S2 timed strum
                  → S3 song integration
```

각 단계에서 observation/action shape은 유지하고 event sampling, reward mask, timing tolerance, failure mining만 변경한다.
분기는 raw audio가 아니라 검증된 `strike_plan.json`의 gesture 구성으로 자동 결정한다.
single-only 경로의 S3에서는 strum 및 strum microtiming gate를 적용하지 않지만 grip,
ready, single crossing, timing, strike zone, recovery, song F1과 safety gate는 유지한다.
선택된 route와 active stage 목록은 run manifest와 checkpoint curriculum context에 기록한다.

## 현재 코드에서의 처리

재사용할 것:

- `PickStrikeDetector`
- 기타 좌표계 target geometry
- grip reference와 grip constraint
- recovery context와 strum metric
- A0~S3 curriculum의 실험 기록

분리·수정할 것:

- phase machine
- event cursor
- observation manifest
- reward component
- physical detector 계약

Strike-v1은 비교용 baseline과 명시적 호환 모드로 보존한다. Strike-v2는 기본 설정에
연결했으며 CPU 계약 검증과 Isaac Gym GPU smoke를 통과했다. 2026-09-07의 A1 검증 기록에는
600 iteration 학습 후 deterministic 64 episode에서 grip, ready, full-episode와 safety
gate가 통과한 것으로 남아 있다. 다만 해당 실행 폴더는 현재 작업 트리에 없으므로 이 기록을
재현 가능한 공식 성능 근거로 사용하지 않는다. G0 source 승급은 실제 checkpoint와 sealed
qualification 결과가 함께 남은 실행만 대상으로 한다.
