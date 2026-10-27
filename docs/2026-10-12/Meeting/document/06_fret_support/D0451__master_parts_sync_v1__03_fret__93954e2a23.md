# 03. Fret

> 상태: **FRET-V2 420D 구현 / GPU 커리큘럼 학습 중 / full-song source 승급 미완료**

## 한 줄 정의

Fret은 `FretEvent`를 보고 왼손 손가락과 손목을 움직여 지정된 줄을 올바르게 압현하고
유지하는 곡별 skill prior다. 학습된 weight는 해당 곡의 G0→G2에서 재사용한다.

Fret은 최종 양손 연주 정책이 아니다. 오른손 타현 시점, 기타 지지, 기타 root 제어를 책임지지 않는다.

## 입력

### 음악 입력

```text
FretEvent 또는 Canonical PlayEvent의 fret projection
```

필수 정보는 다음과 같다.

- 현재·다음 event의 string/fret/finger target
- press 시작 시각
- release 시각 또는 sustain 종료 시각
- chord group
- hand position target
- transition context

### 물리 입력

- 왼팔·왼손 관절 위치와 속도
- 손목·손바닥·손가락 끝의 기타 좌표계 위치
- 현재 압현 품질과 contact proxy
- 이전에 실제 실행된 action
- 현재 event phase와 남은 시간

기타가 움직이는 환경에서도 왼손 target geometry는 기타 좌표계로 다시 계산해야 한다. 기타 안정성용 접촉력·지지력은 Fret source observation에 직접 추가하지 않고 StabilityAdapter 쪽에서 관리한다.

## 출력

### 직접 출력

```text
FretProposal {
    action[30]
    action_distribution
    source_contract_hash
}
```

현재 action 소유권은 다음과 같다.

```text
L_Shoulder : 3
L_Elbow    : 3
L_Wrist    : 3
LH hand    : 21
----------------
합계       : 30
```

`L_Thorax`는 초기 Fret source action에서 제외하고 hold한다.
이 30D 구성은 Fret source action ABI로 확정하며, 몸통 관절은 FullBodyPlayer의
StabilityAdapter와 ActionArbiter가 별도로 관리한다.

### 진단 출력

```text
FretReadiness {
    required_strings_ready
    finger_assignment_correct
    press_quality_per_string
    chord_ready
    sustain_valid
    thumb_support_valid
    readiness_confidence
}
```

이 값은 policy가 선언하는 성공값이 아니라 별도의 readiness evaluator가 physics snapshot에서 계산하는 값이다.

## 모델 구성

```text
FretGoalEncoder
    current + lookahead FretEvent
        ↓
FretGeometryEncoder
    finger target, fretboard-relative geometry
        ↓
FretProprioEncoder
    left chain q/qdot, hand geometry
        ↓
Shared Motor Trunk
        ├─ 30D joint action head
        └─ optional readiness auxiliary head
```

초기 actor는 feed-forward MLP로 시작한다. event phase와 이전 실행 action을 명시하면 GRU가 반드시 필요한 것은 아니다. history ablation에서 실패가 남을 때만 temporal encoder를 추가한다.

single-note, chord, sustain, release와 position transition은 별도 actor로 나누지 않고
하나의 `FretMotorPolicy`가 event/phase 조건에 따라 수행한다.

Fret의 핵심 모델은 다음 두 개를 구분한다.

1. `FretMotorPolicy`: 실제 관절 action 생성
2. `FretReadinessEvaluator`: 압현 준비·유지·안전 판정

둘을 하나의 actor 출력으로 합치지 않는다. 초기 `FretReadinessEvaluator`는 규칙 기반으로
구성하고 physics snapshot을 authoritative input으로 사용한다. learned readiness head는
추가하더라도 auxiliary prediction으로만 사용하며 Synchronizer의 타현 허가를 직접 결정하지 않는다.

`fret_ready`의 hard condition은 타현 대상 줄의 effective sounding fret이 목표와 같고,
음악적으로 방해되는 추가 압현이 없으며, 필요한 압현이 타현 직전 최소 1 control frame
동안 연속 확인되는 것이다. 같은 frame에서 순간적으로 접촉한 상태는 ready로 인정하지
않는다. 엄지 지지는 이 boolean에 직접 포함하지 않고
`thumb_support_ready`와 `support_confidence`로 분리한다. G1/G2에서의 타현 허가는
`fret_ready AND support_safe`로 결합하며, `support_safe`는 StabilityAdapter 쪽의
물리적 지지 판정이 제공한다.

각 손가락의 correct press는 목표 string/fret cell 안의 위치 조건과 실제 누름 상태를
동시에 만족해야 한다. 위치만 맞고 줄 위에 떠 있는 상태는 `approach_ready`일 수 있지만
`press_ready`는 아니다. 가상 줄 모델에서의 실제 누름은 손끝이 원래 virtual string
위치보다 fretboard 방향으로 들어간 깊이로 판정한다. fretboard 접촉이나 접촉력은
`fret_ready`의 필수 조건으로 사용하지 않으며, 세부 depth threshold는 소규모 기하
검증으로 정한다. 초기 버전은 모든 줄에 동일한 하나의 press-depth threshold를
사용하며 줄별 보정은 검증에서 체계적인 차이가 확인될 때만 추가한다.
Press depth 계산은 fingertip rigid body의 중심이 아니라 virtual string 쪽을 향한
실제 fingertip 표면점을 기준으로 한다. 초기 구현은 각 distal finger body의 실제
pad 표면에 고정된 `finger_pad_marker` 하나를 사용하고 이를 매 frame 기타 좌표계로
변환한다.

Fret 길이 방향 위치는 대상 fret 구간의 nut 쪽 wire를 0, bridge 쪽 wire를 1로
정규화한다. `0.1 <= u_fret <= 0.9`이면 구간 안에서 위치와 관계없이 동일한 correct
position 점수를 주며 중앙이나 특정 wire 근처에 추가 보너스를 주지 않는다. 양 끝
0.1 구간은 wire 경계 혼동을 막기 위한 margin으로 둔다.

넥 폭 방향의 string 영역은 인접한 두 virtual string 중심선 사이의 중점을 경계로
5:5 분할한다. neck width 전체를 빈틈이나 중첩 없이 여섯 영역으로 나누며
`finger_pad_marker`가 속한 영역의 string 하나를 선택한다. 각 영역 안에서는 중심선과의
거리에 따른 추가 점수 차이를 두지 않는다.

추가 압현은 존재 자체로 실패시키지 않고 현재 타현될 string의 실제 sounding fret을
바꾸는 경우에만 hard interference로 처리한다. 한 string에 여러 press가 있으면 bridge에
더 가까운 가장 높은 fret이 effective sounding fret이 된다. 따라서 목표보다 낮은 fret의
추가 press나 현재 타현되지 않는 string의 추가 press는 현재 event의 hard failure가
아니다. 개방현 목표에서는 해당 string의 어떤 fretted press도 음높이를 바꾸므로
interference다.

`fret_ready`는 어떤 손가락이 눌렀는지가 아니라 각 타현 대상 string의
`effective_sounding_fret`으로 판정한다. Finger Mapping과 다른 손가락이 같은 목표 fret을
대신 눌러도 해당 string의 음악적 성공으로 인정한다. 다만 그 손가락이 동시에 담당해야
할 다른 target string이 비면 그 string의 readiness 실패로 처리된다. 계획 운지 일치율은
hard gate와 분리된 진단 지표로 보고한다.

Finger Mapping의 `t_press=t_strike-0.12s`는 이동 시작이 아니라 목표 압현 시작
시각이다. 정책은 lookahead를 이용해 그보다 먼저 이동·정렬하고, `t_press`에 실제
correct press를 완성한 뒤 연결된 strike와 `t_release`까지 필요한 압현을 유지한다.
0.12초는 음악적·물리적 제약이 허용할 때 Finger Mapping이 확보하려는 nominal lead이지,
모든 event에 다시 적용하는 downstream hard deadline이 아니다. 실제 lead가 6 frame보다
짧은 event는 `short_lead`라는 진단·난이도 tag로 표시하되 Fret은 동일하게 해당 event의
`t_press`를 따른다.

압현을 `t_release`보다 먼저 해제해 필요한 sustain을 끊으면 early-release failure다.
반대로 `t_release` 이후 계속 누르고 있어도 그 상태가 다음 타현의 sounding fret이나
다음 손가락 assignment를 방해하지 않으면 hard failure로 처리하지 않는다. 늦은 해제로
다음 개방현·더 낮은 fret을 방해하거나 필요한 손가락 이동을 실패하면 해당 후속 event의
interference 또는 readiness failure로 페널티를 준다.

## Observation block

```text
O_proprio
    left shoulder/elbow/wrist/hand q, qdot

O_geometry
    fingertip, palm, wrist의 guitar-relative position/velocity

O_goal
    current FretEvent + next events + sustain/chord state

O_phase
    press/hold/release phase, dwell progress, deadline

O_history
    previous executed action, previous fingertip state
```

기존 Fret의 425D는 `fret.observation.v1` 관측 계약으로 보존한다. 새 기본 계약은
`fret.observation.v2/420D`이며 다음 named block 순서를 고정한다.

| block | dim | 역할 |
|---|---:|---|
| `O_proprio` | 60 | 30개 제어 관절의 q, qdot |
| `O_arm_anchor` | 18 | L_Thorax의 기타 상대 pose/twist와 중력 방향 |
| `O_hand_geometry` | 60 | wrist·palm pose/twist, 네 손끝·엄지 위치/속도 |
| `O_current_event` | 45 | 현재 줄·프렛·손가락·barre·NO_PRESS·chord |
| `O_target_geometry` | 24 | 손끝/손목 목표 오차와 압현 깊이·측면 오차 |
| `O_finger_transition` | 52 | 손가락별 13D KEEP/MOVE/REST 전환 정보 |
| `O_lookahead` | 72 | 다음 두 개의 서로 다른 canonical FretEvent |
| `O_readiness_contact` | 45 | 줄별 압현/오압현/유지/미끄럼과 chord readiness |
| `O_phase` | 12 | prepare/press/hold/release/transition 및 시간 진행 |
| `O_synchronizer` | 2 | release enable, timing offset |
| `O_history` | 30 | 직전 실제 실행 action |

v2 actor/critic은 block별 encoder 뒤 shared fusion MLP를 사용하는 feed-forward
`FretMotorPolicy`다. readiness block은 policy가 선언한 값이 아니라 현재 physics
snapshot을 규칙 기반으로 판정한 값이다. 기존
[Fret task](/home/ajou/yigyu/3/tab2body/env/tasks/task_fret.py)는 v1 baseline과 물리
판정 구성요소의 기준으로 계속 사용한다.

첫 배관 검증 곡은 `02_Jazz1-200-B_solo`로 한다. 길이 14.35초, 서로 다른 Fret 상태
51개, 사용 string/fret cell 7개, 최대 7프렛으로 현재 bundle 중 짧고 단순하다.
다만 middle·pinky 표본이 적으므로 이 곡의 smoke 성공을 네 손가락 일반화 증거로
해석하지 않는다.

## 실제 압현 시각화

`FretPressVisualizer`를 별도 디버그 도구로 둔다. Finger Mapping의 목표뿐 아니라
시뮬레이션 physics snapshot에서 판정된 실제 압현을 guitar 위에 string/fret cell 단위로
표시한다.

```text
FretPressSnapshot
    event_id
    finger_id
    finger_pad_marker pose
    detected_string / detected_fret
    press_depth
    effective_sounding_fret per string
    correct / harmless_extra / interfering / not_pressed
        ↓
viewer overlay + frame trace + 녹화 영상 overlay
```

기본 색은 목표 cell 윤곽=파랑, 올바른 실제 압현=초록, 음악적으로 무해한 추가
압현=노랑, 방해되는 압현=빨강으로 한다. 화면 표시와 trace는
`FretReadinessEvaluator`가 사용하는 동일한 판정 결과를 소비해야 하며 별도 heuristic을
다시 구현하지 않는다. 도구는 reward나 action에 영향을 주지 않으며 켜고 끌 수 있어야
한다.

## 초기 바레 범위

초기 Fret-v2는 한 손가락이 한 string을 누르는 압현과 여러 손가락 chord를 지원하지만
한 검지가 여러 string을 동시에 누르는 barre는 지원하지 않는다. Finger Mapping과
Canonical PlayEvent의 `barre` field는 삭제하지 않고 미래 확장을 위해 보존한다.
`barre=true` 입력을 만나면 일반 chord로 조용히 변환하지 않고 capability validation에서
명확히 unsupported로 판정한다. 기본 압현 검증을 통과한 뒤 여러 index-pad marker와
별도 readiness semantics를 갖는 barre 확장 단계로 추가한다.

초기 Fret-v2는 일반 fretted/open note와 이를 사용하는 picking·strum만 대상으로 한다.
Hammer-on, pull-off, slide, bend 등 별도의 왼손 onset 또는 연속 pitch 제어가 필요한
특수 주법은 현재 연구 범위에서 고려하지 않는다. 입력에 technique label이 존재하면
일반 press/strike event로 임의 해석하지 않고 unsupported capability로 보고한다.

## Action 실행 계약

```text
a_policy[-1, 1]^30
→ stage mask / finger authority mask
→ source action transform
→ common EMA
→ joint limit clamp
→ PD target
→ physics
```

Fret source의 고유 transform, thumb support, hold, fine reach scale은 checkpoint와 함께 버전 관리한다. Full에서 source를 재사용할 때 이 변환을 생략하면 같은 actor라도 다른 정책이 된다.

`isolated_press` 기본 action 계약은 30D 왼손 authority를 유지하며,
고정 60-frame 경계에서 shoulder·elbow를 잠그지 않는다. 준비 구간과 잠금
경계가 겹치면 pinky curl 궤적의 프렛 방향 보정을 막는 것이 확인되었다.
향후 proximal lock을 쓰려면 시간이 아니라 valid-region·depth·lateral readiness를
연속 유지한 후에만 latch하고, 별도 action-contract version으로 검증한다.

## Reward

- 1순위 음악 결과: strike 시 string별 effective sounding fret, full/partial chord, miss
- 2순위 유지 결과: sustain, early release, 다음 event interference
- 3순위 shaping: fingertip target 접근, press depth, 계획 운지, thumb support, smoothness
- 별도 안전: joint limit, penetration, unsafe velocity

15 mm 이내 near-miss mask는 실패 funnel 진단에만 사용한다. 경계 안쪽에만
고정 음수 보상을 주면 가까워지는 행동이 더 나쁘어지는 비단조 보상 절벽이
생기므로 현재 가중치는 0으로 고정한다.

Reward는 위 계층의 우선순위를 보존하도록 각 하위 tier의 합산 가능 범위를 제한한다.
접근·자세·smoothness shaping의 최대 합이 wrong sounding fret 또는 missed target의 손실을
상쇄할 수 없어야 한다. 평균 scalar reward와 별개로 각 음악 event outcome을 항상
명시적으로 기록한다. 압현 reward가 높더라도 타현 timing은 Fret 단독 성공으로 인정하지
않는다.

## 학습 범위

```text
F0 single-finger reach
F1 single-string press
F2 chord readiness
F3 sustain/release
F4 position transition
F5 phrase-level multi-event
F6 full-song / randomized reset / physics profile
```

Fret source release 조건은 해당 곡의 평균 reward가 아니라 full-song event subgroup,
chord, transition과 평가 seed의 최악 성능으로 판정한다.

승급은 single-note 정확성, chord 완성도, sustain/release, 빠른 transition과 short-lead
subgroup, 같은 곡의 평가 rollout, 관절·충돌 안전성을 모두 통과하는 AND gate로 결정한다. 평균
reward나 전체 평균 정확도가 한 실패 영역을 가릴 수 없다. 구체 threshold는 소규모
검증과 baseline 분포를 본 뒤 봉인한다.
