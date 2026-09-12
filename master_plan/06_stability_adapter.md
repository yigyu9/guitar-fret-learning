# 06. StabilityAdapter

> 상태: **부분 구현 — action/pre-play/strap 기반 계약 구현, PPO task 미구현**

## 한 줄 정의

StabilityAdapter는 자유롭게 움직이는 기타의 pose, velocity, contact, slip 상태를 관측하고, Fret·Strike 기술이 유지되는 범위에서 지지 관련 residual action을 생성한다.

StabilityAdapter는 음악 event의 의미나 score clock을 수정하지 않는다.

## 연주 시작 전 안정화

Episode reset 직후에는 오디오나 Canonical score runtime을 시작하지 않는다. 먼저 별도의
`STABILIZING` 단계에서 StabilityAdapter와 지지 물리만 실행하고, 해당 episode가 reset된
시점의 `pelvis 대비 기타 pose`를 초기 목표로 사용한다. 월드 좌표가 아니라 움직이는 pelvis
좌표계 B를 기준으로 하므로 인체 전체의 작은 이동을 기타 slip으로 잘못 판정하지 않는다.
이 목표를 인체공학적 최적 pose라고 주장하지 않으며, 이후 안정 pose 데이터가 생기면 별도
reference contract로 교체한다.

```text
reset
  → STABILIZING               score/audio 미시작, source action은 hold
  → READY_FOR_PREROLL         안정 조건 연속 충족
  → common pre-roll           Fret·Strike가 첫 event 준비
  → score frame 0             audio playback 시작
```

초기 calibration 기본값은 최소 60 frame 안정화 시간, 30 frame 연속 안정, 최대 300 frame
timeout이다. 위치 5 cm, 회전 10도, 선속도 0.05 m/s, 각속도 0.25 rad/s 이하는 provisional
engineering default이며 논문 평가 threshold가 아니다. G1 micro-environment 분포를 얻은 뒤
봉인한다. Timeout까지 안정화하지 못하면 음악을 억지로 시작하지 않고 episode 실패로 기록한다.

현재 `tab2body/full/stability.py`가 이 초기-pose gate, 15D calibration observation, dense
stability reward와 43D named action manifest를 구현한다. `GuitarEnvBase`는 free guitar와
`strapped-v1`을 선택적으로 활성화할 수 있다. 실제 StabilityAdapter actor/PPO 및 Full G1
source 결합은 아직 구현 전이다. 학습용 actor 구조와 264D named-block observation ABI는
구현했지만, 실제 contact/task-summary tensor를 만드는 Full G1 task가 연결되어야 PPO를 시작한다.

## 입력

### 기타 상태

```text
- guitar pose relative to torso/pelvis
- guitar linear/angular velocity
- gravity expressed in guitar frame
- guitar pose/twist error from playable envelope
```

### 지지·접촉 상태

```text
- strap anchor geometry and tension
- thigh/body/palm/forearm contact
- normal/tangential load
- slip velocity
- friction reserve
- support polygon / center of pressure proxy
- penetration and over-force margin
- artificial assist λ and work
```

접촉은 연속적인 normal/tangential load와 slip velocity를 주 관측으로 사용하고, contact 여부 flag는 보조 관측으로 사용한다. 초기 support group은 세 가지로만 단순화한다.

```text
strap          : tension support
body_contact   : torso/thigh friction contact
arm_contact    : palm/forearm friction contact
```

왼쪽·오른쪽 또는 손가락별 contact 모델은 초기 범위에서 분리하지 않는다. 손가락 끝은 Fret·Strike 연주 접촉으로만 취급하고 support group에는 포함하지 않는다.

초기 support observation은 group별 다음 4개 값으로 제한한다.

```text
normal_load, tangential_load, slip_speed, contact_flag
```

strap은 `normal_load` 대신 tension을 사용한다. 접촉점별 벡터와 세부 force attribution은 후속 확장으로 둔다.

현재 base 환경은 net contact force 중심이므로 contact pair와 support-site attribution을 새로 추가해야 한다.

### 기술 보존 상태

```text
FretTaskSummary
    string별 readiness
    fingertip/press error summary
    next press/strike까지 남은 시간

StrikeTaskSummary
    motor phase와 approach/recovery state
    pick lane error summary
    next strike까지 남은 시간

ActionContext
    authority 대상 joint의 source action proposal
    previous executed action/residual
```

StabilityAdapter는 Fret 420D와 Strike 303D actor observation 전체를 복사해 받지 않는다.
Summary는 policy의 자기 보고가 아니라 `FretReadinessEvaluator`, Strike detector와 phase
machine의 authoritative runtime state에서 만든다. Summary field는 named semantic contract로
version 관리하며 source observation 내부 offset에 직접 의존하지 않는다.

현재 `stability.observation.v2`는 다음 264D block으로 고정한다.

```text
O_guitar_state       15
O_support            12
O_fret_summary       11
O_strike_summary      8
O_proprio             86    # 43개 active joint의 q, qdot
O_action_context     129    # source/hold, previous executed, previous residual
O_phase                3
------------------------
total                264D
```

## 출력

```text
StabilityProposal {
    residual[action_name]
    authority_mask
    per_joint_cap
    stability_certificate
    consistency_confidence
}
```

residual은 source action과 이름으로 합쳐지며, 최종 실행은 ActionArbiter가 담당한다.

초기 StabilityAdapter 출력은 실질 가동 관절 97D 전체가 아니라 다음 named action group에만
sparse residual을 낸다. 최종 합성 버퍼는 호환성을 위해 105D named ABI를 사용한다.

```text
active   : Thorax/body, Lower body, L/R Shoulder, L/R Elbow
reserved : L/R Wrist
forbidden: Fret/Strike finger, Neck/Head
```

Actor output tensor도 105D를 만든 뒤 mask하는 방식이 아니라 active joint만 포함한 compact
residual contract를 사용한다. `ActionArbiter`가 manifest의 joint name을 이용해 이를 최종
105D slot에 scatter한다. Active joint 목록이 바뀌면 StabilityAdapter action contract와
checkpoint version을 올린다.

기타가 안정적일 때는 residual authority를 낮게 유지하고, slip·tipping 위험이 커질 때만 authority gate를 높인다.

## 내부 구조

```text
GuitarStateEncoder
SupportStateEncoder
TaskSummaryEncoder
ActionContextEncoder
        ↓
    fusion trunk
        ├─ bounded named residual head
        └─ support-need/confidence head
        ↓
external rule-based consistency/safety gate
```

초기에는 별도의 learned SupportPolicy나 learned ConsistencyBranch를 두지 않는다. 하나의
actor가 분리된 encoder와 shared fusion trunk를 사용해 residual candidate를 제안하고,
외부 규칙 기반 consistency/safety gate가 Fret·Strike 보존과 hard safety를 검사해 최종
권한을 제한한다. Learned consistency predictor는 규칙 기반 구조의 한계가 실험으로
확인될 때만 후속 확장한다.

초기 actor는 block별 encoder와 shared fusion trunk를 쓰는 하나의 43D residual policy다.
Critic은 guitar stability, support quality, Fret retention, Strike retention, regularization의
5개 value target을 분리해 기록한다. 이는 5개 정책이 아니라 하나의 actor를 위한 multi-value
critic이다. Residual head는 0으로 초기화해 첫 policy가 source/hold action을 바꾸지 않게 한다.

전체 authored 관절 슬롯은 105D지만, zero-range 하체 보조축 8개를 제외한 실질 가동
관절 집합은 97D다. StabilityAdapter의 초기 43D는 이 가동 집합 중 body/Thorax 15D,
실제 가동 가능한 하체 16D, 양쪽 shoulder/elbow 12D로 구성한다.
`L/R_Knee_y,z`와 `L/R_Toe_y,z` 8축은 MJCF range가 정확히 0이므로 policy에서 제외하고
초기 자세로 hold한다. 이 8축도 최종 FullBody 105D ABI의 named slot으로는 계속 유지한다.

## 관절 권한

초기 권한은 작게 시작한다.

```text
Tier 0: 신규 body/Thorax hold
Tier 1: R_Thorax 또는 support에 필요한 proximal body
Tier 2: 양쪽 shoulder/elbow residual
Tier 3: 양쪽 wrist residual reserved
Tier 4: 양손 finger residual 금지
```

왼손은 neck의 thumb/palm 지지, 오른손은 guitar body의 palm/forearm 지지를 위해 양쪽 shoulder/elbow residual을 사용할 수 있다. 양쪽 wrist는 Fret/Strike timing과 궤적에 직접 영향을 주므로 초기에는 reserved로 둔다.

StabilityAdapter residual은 새로운 action dimension을 추가하지 않는다. 기존 named action에 다음 순서로 적용한다.

```text
Fret/Strike source action
    → source-specific action transform
    → named joint target/action space
    → StabilityAdapter residual Δa_stability
    → total joint cap + safety filter
    → common EMA/PD
```

`Δa_stability`는 body/lower-body와 양쪽 shoulder/elbow 등 authority mask가 허용한 action에만 적용한다. 양손 finger에는 적용하지 않는다. residual cap은 실제 관절 단위(기본 radian target/action 단위)로 정의한다. source의 mean/log_std, observation normalization, 확률 분포, 기존 checkpoint의 action contract는 변경하지 않는다. source action과 StabilityAdapter residual에 EMA/PD를 각각 적용하지 않고 최종 합성 결과에 한 번만 적용한다.

StabilityAdapter는 residual candidate와 support-need/confidence만 제안한다. 초기에는 외부 Safety/Consistency layer가 규칙 기반으로 최종 `authority_gate`, hard cap, safety veto를 결정한다. learned ConsistencyBranch는 후속 확장으로 둔다.

초기 규칙은 세 범주로 나눈다.

```text
hard failure:
    pose 이탈, tipping/drop, 필수 접촉 상실, 위험 slip,
    penetration/over-force, strap 과장력, pelvis safety 이탈

residual 감소·차단:
    Fret readiness·Strike timing 저하,
    residual cap/rate 반복 도달, 불안정한 contact force

residual 증가:
    pose drift, 회전·속도 증가, slip 증가,
    friction 여유 감소, strap tension 증가
```

우선순위는 `hard safety → Fret/Strike 보존 → 기타 pose 안정화 → residual 최소화`로 한다. threshold와 지속 시간은 G1 calibration에서 정하고, hysteresis를 사용한다.

기술 보존은 source action과의 수치적 동일성이 아니라 실제 Fret/Strike event 결과를
primary 기준으로 삼는다. Fret sounding-fret·sustain과 Strike crossing·timing이 유지되면
안정화를 위한 shoulder/elbow/body action 변화는 허용한다. Source action deviation과
residual magnitude/rate는 과도한 개입을 막는 bounded soft regularization으로만 사용하며,
이 항들이 실제 음악 실패를 상쇄하거나 반대로 유효한 안정화를 hard reject하지 않는다.

authority gate는 하나의 global scalar로만 두지 않는다. 공통 hard safety gate와 세 개의 group gate를 사용한다.

```text
global_safety_gate
    ├─ body_gate
    ├─ lower_body_gate
    └─ arm_support_gate
```

좌우 arm은 초기에는 하나의 `arm_support_gate`로 묶고, 필요할 때만 후속 단계에서 분리한다.

Fret과 Strike finger action은 StabilityAdapter가 소유하지 않는다.

Neck/Head도 StabilityAdapter가 소유하지 않는다. Neck/Head는 기타 지지 residual이 아니라 시선·주의 방향을 위한 `GazeTarget/AttentionBranch`가 담당하며, 최종 ActionArbiter에서 별도 action group으로 합성한다.

## 확정된 하체 방향

하체는 연주에서 큰 동작을 담당하지 않지만, 최종 full-body action space에는 포함한다.

```text
action space:
    하체 전체 포함

평상시 behavior:
    초기 seated 자세 근처에서 hold

예외:
    기타가 기울거나 미끄러질 때 작은 하체 보정 허용
```

하체 action은 초기 자세에 대한 bounded residual로 해석한다.

```text
a_lower = hold_action(q_initial) + bounded_residual
```

여기서 `hold_action`은 normalized action의 숫자 0이 아니라, 초기 자세를 유지하는 PD target에서 계산한다.

하체 자세 reward는 joint-angle 기반으로 결정한다. 초기 자세에서의 모든 차이를 벌하지 않고 관절별 dead-zone 밖의 이탈만 벌한다.

```text
r_posture = -Σ_j w_j · max(0, |q_j - q_initial_j| - δ_j)^2
```

기타의 기울기·각속도·미끄러짐·drop recovery는 별도의 `r_guitar_stability`로 계산한다. 하체 posture reward가 기타 안정화 reward를 대체하지 않는다.

### 단계별 authority

```text
G0:
    하체 action slot은 ABI에 예약
    실제 authority는 hold/mask

G1:
    하체 residual trainable
    작은 cap과 posture dead-zone 적용

G2:
    하체 residual authority 확대
    artificial assist=0
```

논문상의 기본 표현은 `posture-constrained whole-body guitar controller`로 한다. 하체 action을 제거한 hard-lock baseline과 비교해 외란 상황에서 하체가 기타 recovery에 기여하는지 검증한다.

## 지원 물리

실제 장비와 curriculum assist를 분리한다.

### 물리 효과를 갖는 가상 strap constraint

- 두 strap button을 잇고 가슴 위쪽과 왼쪽 어깨를 감싸는 신체 표면 guide를 지나는 준-비신축성 maximum-length cable을 적용한다.
- 케이블은 설정 길이 이내에서 느슨하게 휘고, 초과 신장은 1% 이내로 제한하며 물리는 240 Hz에서 갱신한다.
- 굽힘점의 반력은 각 guide가 속한 신체 rigid body에 나누어 적용한다.
- guide뿐 아니라 guide 사이의 모든 선분을 전체 humanoid collision capsule과 비교해 비관통을 검증한다.
- 화면에는 물리 계산과 동일하며 humanoid를 관통하지 않는 경로를 표시한다.
- rope/cloth contact는 초기 범위에서 제외한다.
- G1에서는 guide를 매 step 신체 표면에 재투영하고 접선 방향의 제한적 미끄러짐을 허용하는 확장을 검증한다.
- 가상 strap constraint와 curriculum artificial assist를 구분한다.

### 허벅지·몸통 지지

신체 지지는 실제 충돌 기반의 단순 box/capsule proxy를 사용한다. 기존 humanoid collision
shape로 안정적인 접촉과 force attribution이 가능하면 그대로 사용하고, 부족한 부위에만
named proxy를 추가한다. 초기에는 `body_contact`와 `arm_contact` 두 그룹으로 집계하며,
손가락 끝은 support에서 제외한다. G1·G2는 같은 proxy를 사용하고 artificial assist와
물리 접촉을 별도 신호로 기록한다.

- 실제 collision proxy와 friction contact
- 하중 band와 slip margin 측정
- 고정 weld 금지

### 인공 hand assist

- palm/forearm/neck/body support site에만 연결
- dead zone, force cap, slew-rate cap
- 가능하면 기타와 손에 equal-and-opposite force
- G2에서 정확히 0

pick과 fret fingertip을 support tether에 직접 연결하면 과제 shortcut이 생기므로 금지한다.

Artificial assist 감소는 고정 iteration schedule이 아니라 performance-gated staircase로
진행한다. 현재 assist level에서 기타 안정성, Fret·Strike 보존과 안전 gate를 연속 평가
구간 동안 통과한 경우에만 assist를 한 단계 줄인다. 감소 후 성능 저하가 rollback
threshold를 연속 초과하면 한 단계 강한 assist로 돌아간다. 승급·복귀 threshold와 연속
구간 수는 calibration으로 정하며 hysteresis를 두어 단계 진동을 막는다.

## 기타 좌표계와 몸통 좌표계

```text
guitar frame G
    pick/fret target geometry

body frame B
    기타가 몸통·허벅지에 대해 이동하는 정도

world/gravity frame
    중력에 대한 기타 자세
```

안정성의 주된 reference는 pelvis에 고정된 body frame `B`로 한다. 기타가 pelvis·허벅지·스트랩에 대해 초기 상대 pose를 유지하는지가 StabilityAdapter의 primary objective다. 최종 G2에서도 pelvis를 hard-lock하지 않고 강한 joint-angle hold와 제한적 trainable residual을 사용한다. `W`는 전체 위치를 강하게 고정하는 용도가 아니라 gravity 기준 기울기, 낙하 방향 속도, tipping/drop을 판정하는 secondary safety reference로 사용한다.

Fret·Strike의 target geometry와 음악 event는 계속 guitar frame `G`에서 계산한다. 따라서 좌표계의 역할은 다음처럼 분리된다.

```text
G: 연주 기술과 target geometry
B: pelvis 기준 기타 지지와 상대 pose 보존 (primary)
W/gravity: tipping·drop·외란 안전 판정 (secondary)
```

G0의 pelvis hard-lock은 source equivalence와 초기 안정성 검증 및 `PelvisLocked` ablation baseline에만 사용한다. G1·G2의 본 실험에서는 pelvis hold 오차와 residual을 별도 기록한다.

guitar-local 관측만으로는 안정성을 판정할 수 없다. 기타 내부에서는 정지해 보여도 몸통에서 미끄러지고 있을 수 있기 때문이다. 반대로 world pose 전체를 primary로 고정하면 몸통의 허용 가능한 움직임까지 과도하게 벌할 수 있다.

## 보상·지표

- pose/twist dead-zone 유지
- linear/angular velocity와 settling time
- support load band
- slip velocity와 friction reserve
- strap/tether tension·work
- penetration·over-force
- residual magnitude·rate·jerk
- Fret/Strike counterfactual degradation

안정성 reward 하나로 최종 승급하지 않는다. Fret/Strike 보존, event timing, safety를 함께 통과해야 한다.

## 안정성 제약과 종료 계약

기타 pose 보존은 두 층으로 나눈다.

```text
hard-failure envelope:
    초기 기타 pose에서 회복 불가능한 위치·회전 이탈
    과도한 미끄러짐 또는 필수 접촉 상실
    drop, penetration, over-force
    → failure 처리 및 episode terminate

soft constraint region:
    hard-failure envelope 안의 모든 상태
    → pose 오차, 속도, slip, support load, residual 크기를 reward로 평가
```

위치·회전 reward는 초기 pose 주변의 dead-zone 밖에서만 점진적으로 감소시킨다. hard-failure 조건은 단일 simulation step의 노이즈로 판정하지 않고, 연속된 control step 동안 유지되거나 drop처럼 회복 불가능한 사건이 발생할 때만 terminate한다. hard envelope의 수치는 사용자가 임의로 입력하는 대신 G1 calibration, 고정 기타에서의 Fret·Strike 허용 오차, 접촉·기하 여유로 산출한다.
