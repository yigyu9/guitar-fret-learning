# 05. Synchronizer

> 상태: **CPU 계약·합성 runtime 구현 — one-simulator Isaac `FullG0Task` 연결 전**

## 한 줄 정의

Synchronizer는 공통 음악 시간축을 기준으로 Fret과 Strike의 readiness와 local execution phase를 조정하는 timing supervisor다.

이 공통 시간축은 raw audio가 아니라, 오프라인에서 생성한 Tablature·Finger Mapping·Picking Plan을 합친 `Canonical PlayEvent`다.

Synchronizer는 일반적인 관절 제어기가 아니다. 기타를 잡기 위한 torque, 손가락 압현 action, pick 궤적 action을 직접 소유하지 않는다.

초기 Synchronizer는 학습 모델이 아니라 규칙 기반 timing supervisor로 구현한다. learned timing correction은 규칙 기반 기준선이 부족하다고 검증된 경우에만 후속 확장한다.

## 입력

```text
- Canonical PlayEvent current/next events
- global score frame/time
- event별 earliest traversal crossing frame와 safe delay budget
- string별 physical FretReadiness
- Strike readiness
- Strike detector state
- detector crossing별 subframe 시각·방향
- guitar stable certificate
```

핵심은 Fret의 “준비가 되었는가”와 Strike의 “칠 수 있는가”를 같은 event id와 score time으로 비교하는 것이다.

## 출력

```text
SyncCommand {
    event_id
    deadline_action       # prepare / wait / execute / skip / resolved
    strike_permission
    traversal_permission_mask  # 물리적으로 계획된 전체 traversal
    scorable_target_mask       # 준비가 확인된 audible target
    hold_fret_action
    hold_strike_action
    timing_shift_frames
    delay_cause           # fret / strike / both
}
```

`strike_permission`의 조건은 deterministic hard gate로 둔다.

```text
strike_permission =
    event requires strike
    AND Fret ready dwell 완료
    AND Strike approach valid
    AND guitar stable
    AND event별 허용 window 안
```

여기서 Fret ready dwell은 타현 직전 최소 1 control frame이다. 각 audible target string의
`effective sounding fret`이 목표와 일치한 상태가 한 frame 동안 연속 확인된 뒤 다음
frame부터 strike를 허가한다. 더 긴 고정 dwell은 요구하지 않으며 같은 frame에 처음
발생한 순간 접촉은 허가 근거로 쓰지 않는다. Traversal 중 지나가지만 소리 내지 않는
protected string은 readiness 대상에서 제외한다.

압현 timing의 단일 기준은 Finger Mapping의 event별 `t_press`이다. Synchronizer는
고정된 `strike_frame-6` deadline을 별도로 만들지 않고, 연결된 strike 시점에 실제
correct press와 유지 상태가 성립하는지를 확인한다. Finger Mapping의 기본
`t_press=strike_time-0.12s`는 가능한 경우의 nominal lead이다. 실제 lead가 6 frame보다
짧은 `short_lead` event는 제어 규칙을 바꾸는 예외가 아니라 별도로 보고할 난이도
subgroup으로 취급한다.

실행 시 Fret가 반복적으로 늦게 준비되는 오차를 흡수하기 위해 actor용 goal view에는
최대 3 control frame의 `press advance`를 허용한다. 현재 string이 비압현일 때만 미래의
PRESS 목표를 먼저 보여 주며, 이미 다른 fret을 누르는 string은 덮어쓰지 않는다.
따라서 press onset만 앞당기고 현재 음의 release 시점은 변경하지 않는다. Strike의
late rescue도 최종 50 ms tolerance에 맞춰 최대 3 frame으로 두되, 실제 event별 한도는
다음 transition의 rearm slack으로 0~3 frame 범위에서 자동 축소한다.

타현 release의 시작 경계는 event 중심 시각이 아니라, string traversal offset 중 가장
이른 crossing 시각이다.

```text
release_boundary = event_time + min(traversal_offsets)
```

`release_decision_deadline`과 `traversal_completion_deadline`은 구분한다. 전자는 이
event를 언제 실행·부분 실행·누락할지 결정하는 시점이고, 후자는 허가된 strum이 마지막
계획 string까지 지나갈 시간을 포함한 종료 시점이다. 여러 string을 한 frame 이상에 걸쳐
통과하는 strum을 첫 crossing 직후 조기에 resolve하지 않는다.

예정된 release boundary에 Fret이 준비되지 않았을 때 Synchronizer는 60 Hz 기준 최대
3 frame(50 ms) 안에서만 strike를 지연할 수 있다. 단, 다음 event의 안전 간격을
침범하지 않도록 각 event의 실제 budget을 더 작게 제한한다.

```text
event_delay_budget = min(configured_max_3_frames, next-event safe cap)
```

따라서 `+3 frame`은 모든 event에 강제로 주는 지연이 아니라 event별 상한이다. 실제 한도는
전환 여유에 따라 0~3 frame이다. 그 안에 준비되면
`delayed_rescue`, 초과하면 `timing_failure`로 기록한다. 예정 frame의 `on_time` 성공과
지연 보정 성공은 같은 지표로 합치지 않으며 실제 strike timing error도 함께 보고한다.
단일 string event가 해당 event의 delay budget 안에도 준비되지 않으면 해당 strike는 실행하지 않고
`missed_note`로 처리한 뒤 공통 음악 시간축은 계속 진행한다. 하나의 실패 때문에 뒤
event 전체를 밀지 않는다. Chord/strum처럼 여러 string을 동시에 타현하는 event는
delay budget 안에 완전히 준비되지 않아도 deadline에 타현을 실행하고 string별 성공·실패를
평가한다. 단, deadline에 준비된 target string이 하나도 없으면 타현하지 않고
`missed_chord` 또는 `missed_strum`으로 처리한다.
3 frame은 Strike의 최종 50 ms timing tolerance와 맞춘 configured 상한이다. 이 값은
detector의 허용 구간을 추가로 넓히지 않는다. 누락률이 높으면 Fret 자체의 lookahead·학습
성능을 먼저 점검하며, 평가 중 임의로 상한을 확장하지 않는다.

같은 `[release_boundary, release_boundary+event_delay_budget]` 허용 구간을 Fret readiness와
Strike 실행 모두에 적용한다. 실제 지연은 `delayed_by_fret`, `delayed_by_strike`,
`delayed_by_both`로 원인을 분리한다. 허용 구간 안에도 실제 타현 crossing이 발생하지
않으면 `missed_note_due_strike_timing`으로 기록한다.

오른손 action hold는 모든 `wait`에 무조건 적용하지 않는다. 아직 entry에 도달하지 않은
오른손은 shift된 native timing 관측을 보며 entry까지 계속 접근하고, 물리적 entry
readiness가 확인된 뒤에만 현재 action을 hold한다. 그렇지 않으면 늦은 오른손이 entry에
도달하지 못하는 deadlock이 생긴다. 닫힌 permission 중 실제 crossing은 성공으로 소비하지
않고 premature/blocked로 기록한다. 향후 one-simulator backend는 detector 결과를 가리는
것에 그치지 않고 이 entry-side phase boundary를 물리 제어 루프에서 집행해야 한다.

이때 hold는 직전 Strike 명령을 단순 반복하지 않는다. 그 명령의 PD target이 이미 줄
반대편이면 닫힌 gate에서도 타현을 계속 밀 수 있기 때문이다. One-simulator backend는
현재 오른손 관절 자세를 normalized current-pose target으로 역변환하고, 첫 hold frame에는
common EMA까지 역산한 `strike_entry_hold_action`을 제공해야 한다. 관성으로 gate를 넘은
closed crossing은 물리 위반으로 기록하며 G0 승급을 실패시킨다. Hold 중 속도가 거의 0이
되어도 readiness가 해제되지 않도록 approach 방향 판정은 정지를 허용하거나 entry-ready
latch를 유지한다.

Strum 성공은 unordered string mask로 판정하지 않는다. Detector의 frame 내부 crossing
시각과 방향을 이용해 canonical traversal order를 정확히 따라야 한다. 역순, 잘못된 방향,
계획 밖 string crossing이 하나라도 있으면 `full` 성공으로 인정하지 않는다.

## 세 가지 시간

```text
score_time
    음악적으로 정해진 시간

local_motor_phase
    손이 현재 event를 준비하는 진행 상태

physical_execution_time
    실제 압현·crossing이 발생한 시간
```

Synchronizer는 score clock을 임의로 멈추지 않는다. 준비가 늦으면 제한된 local hold를 사용하고, deadline을 넘으면 miss/skip으로 기록한다.

## 모델 구성

### Rule Supervisor

가장 먼저 구현할 기준선이다.

```text
EventStream + readiness + timing window
→ deterministic permission/deadline
```

이 기준선만으로 충분하면 learned Synchronizer가 불필요할 수 있다.

### Learned Timing Supervisor

Rule Supervisor가 처리하지 못하는 오차만 학습한다.

```text
EventEncoder
ReadinessEncoder
StrikeIntentEncoder
TimingHistoryEncoder
        ↓
Timing trunk
        ├─ lead correction head
        ├─ phase hold head
        └─ timing confidence head
```

출력은 저차원 timing command이며, 처음부터 30D 또는 60D 관절 action을 출력하지 않는다.

## 상태공간

```text
sync_state_t = {
    current_event_id
    score_time
    event_phase
    fret_ready_dwell
    strike_ready
    guitar_stable_dwell
    strike_window
    deadline
    local_hold_state
    last_timing_error
}
```

event cursor는 Synchronizer가 하나만 소유한다. Fret과 Strike는 이 cursor를 각각 복제하지 않는다.

현재 Fret-v2와 Strike-v2 checkpoint가 학습 중 관측한 actor-side Synchronizer 입력은
항상 `(strike_permission, timing_correction)=(1, 0)`이었다. 이를 runtime에서 실제 gate
값으로 바꾸면 frozen source policy에 학습 분포 밖 입력을 넣게 된다. 따라서 G0에서는 두
actor가 보는 이 2D block을 `(1, 0)`으로 유지하고, permission·hold·timing shift는 source
actor 밖의 `RuleBasedSynchronizer`가 결정한다. Permission과 hold는 action bridge가
집행하며, delay는 Strike의 기존 native timing field에만 명시적으로 반영한다.

두 actor의 출력은 그대로 PD에 보내지 않는다. Fret의 adjacent-finger synergy와 Strike의
pick-grip constraint처럼 checkpoint가 학습할 때 actor 밖에 있던 source-specific action
transform을 먼저 한 번 적용한다. 그 뒤 관절 이름으로 105D에 합치고 common EMA/PD를 한
번만 적용하며, 실제 post-EMA local action을 다음 frame의 각 source `O_history`에 넣는다.
Earlier-stage action mask가 필요한 checkpoint는 final-stage transform만으로 재생하지 않으며,
physical G0에서는 독립 승급 조건을 통과한 final-stage source만 허용한다.

## 현재 구현 경계

다음 CPU 독립 계약은 구현되어 있다.

- song bundle을 하나의 offline canonical event timeline으로 컴파일
- 하나의 cursor와 단조 증가 score clock, exactly-once event resolution
- 한 control frame readiness dwell, bounded delay, skip/partial 규칙
- frozen Fret/Strike checkpoint 검증·추론과 named 105D action 합성
- source별 normalized action→joint target 범위와 후처리 handshake
- checkpoint file hash에 묶인 runtime resume와 source postprocessor
- traversal order·direction·subframe detector 계약

아직 구현되지 않은 것은 Fret·Strike 관측과 detector를 하나의 humanoid/기타 물리 상태에서
계산하고, common EMA/PD와 simulator step을 정확히 한 번 수행하는 Isaac Gym
`FullG0Task`다. 현재 CPU runtime 검증을 실제 fixed-guitar physical rollout 성공으로
해석하지 않는다.

## Synchronizer가 하지 않는 일

- Fret 손가락 action 생성
- Strike 어깨·팔꿈치·손목 action 생성
- 기타 root pose 안정화
- 기타 지지 접촉 제어
- score time을 무제한으로 정지
- readiness 조건을 무시한 조기 strike 성공 인정

## 보상·지표

- Fret-ready dwell 이전 strike 감소
- strike window timing error
- premature/late/miss/skip 비율
- `strike_time - fret_ready_time`
- event synchronization success
- chord/strum target-string accuracy
- full/partial/missed multi-string event 비율
- local hold 사용량
- deadline escape 비율

Chord/strum은 모든 target string이 정답일 때만 full event success로 센다. 일부만
정답이면 전체 성공률에는 포함하지 않고 정확한 target string 비율만큼 partial reward를
준다. 정답 string이 하나도 없으면 missed event이며 partial reward는 0이다.

Timing 개선이 기타 안정화 실패나 Fret/Strike 성능 저하를 가리면 안 된다. 승급은 별도의 source retention과 safety gate를 통과해야 한다.

## 필수 baseline

고정 기타 G0에서 같은 Fret·Strike checkpoint와 event timeline을 사용해 다음을 paired
비교한다.

```text
S0: scheduled strike를 그대로 실행, Fret readiness gate 없음
S1: rule-based Synchronizer의 readiness·bounded-delay·miss 규칙 사용
```

이 비교는 기타 안정화 변수를 제거한 상태에서 premature strike, full/partial event,
timing error와 miss 변화를 측정해 timing supervisor 자체의 효과를 검증한다.
