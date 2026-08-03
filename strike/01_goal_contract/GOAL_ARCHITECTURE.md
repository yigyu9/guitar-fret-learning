# Strike 입력 아키텍처 — raw goal을 그대로 정책에 넣지 않는 이유

> **현재 실행 v1:** 아래 문서의 풍부한 Intent/Mapper/593D 계약은 후속 fingerstyle·strum
> 확장안과 2026-07-23 pilot 기록을 함께 보존한다. 지금 실행 코드는
> `tab2body.strike_training.v1`의 `[time,frame,string]`, `down_only_v1`, 263D actor observation,
> `READY/APPROACH/RELEASE_RECOVER` 3단계를 사용한다. 정본은
> [README.md](README.md) 첫 절과 [학습 문서](../03_training/README.md)다.

## 결론

현재 `notes.t_on + string`은 **새 음향 onset 후보**의 정본으로 그대로 보존한다. 이것이 항상 오른손
strike라는 뜻은 아니다. 먼저 `StrikeIntent`가 실제 오른손 공격 필요 여부를 해결하고, 결정론적 오른손
mapping 단계가 물리 실행용 `StrikePlan`으로 확장한 뒤 60 Hz `RuntimeGoal`로 래스터화한다.

```text
SourceNote          StrikeIntent             StrikeMapper             StrikePlan            RuntimeGoal
새 음향 onset 후보 → 오른손 공격 여부 해결 → 어떻게 칠지 결정     → 곡 전체 운동 의도  → 정책 관측
t_on,string,effect    true/false/unknown        setup/agent/direction     phase/zone/relation   60 Hz tensor
```

raw와 plan은 서로 대체 관계가 아니다.

- **SourceNote**: 음향 onset 후보 원본이며 수정하지 않는다.
- **StrikeIntent**: 그 onset에 오른손 공격이 필요한지 명시한다.
- **StrikePlan**: 동일한 음악을 수행하는 여러 가능한 오른손 해법 중 하나를 명시한다.
- **RuntimeGoal**: plan의 의미를 잃지 않고 정책이 매 frame 사용할 수 있게 만든다.

## 왜 raw strike만으로 부족한가

현 프로젝트의 fingering JSON note는 대체로 `t_on`, `t_off`, `string`, `fret`, MIDI와 **왼손** finger를
가진다. `presses[].strikes`는 재타현 onset 배열일 뿐이다. 다음 오른손 정보는 없다.

| 필요한 정보 | raw에 존재 | 없을 때 생기는 문제 |
|---|---|---|
| 음향 onset·target string | 있음 | 오른손 공격인지 추가 판정 필요 |
| tied/hammer/pull/slide | 현재 일반 입력에는 부족 | 모든 새 음을 다시 치는 오류 |
| pick/thumb/i/m/a | 없음 | 같은 음마다 타현 주체가 임의로 바뀜 |
| single/multi_pluck/strum | 없음 또는 모호 | 동시 onset을 동시 손가락/빠른 스트럼 중 무엇으로 칠지 모름 |
| up/down 및 손가락 release 방향 | 없음 | 왕복 방향과 준비 자세가 일관되지 않음 |
| strike 위치·음색 위치 | 없음 | 줄 어디서나 치거나 프레임마다 목표점이 흔들림 |
| 세기/accent | 없음 | 공격 속도와 follow-through 크기를 정할 수 없음 |
| 준비·회복 관계 | 없음 | onset에 반응한 뒤 늦게 이동하거나 매번 중립 자세로 복귀 |
| anchor/rest mode | 없음 | 손을 허공에 두거나 기타에 과하게 고정하는 해법이 모두 가능 |

이 모호성을 모두 RL에 맡기면 task reward가 같은 여러 해법 사이를 오가며, 곡 반복 학습에서도 동작이
일관되지 않을 수 있다. 따라서 **음악적 자유도와 운동 제어 자유도를 planner에서 먼저 정리**한다.

## 현재 코드에서 확인한 근거

- [`assign.py::press_events()`](../../tab2fingermapping/fingermapping/assign.py)는 스스로 “왼손 모터
  goal”이라고 정의한다. 개방현이나
  finger 미배정 note를 건너뛰고, 같은 `(왼손 finger,string,fret)` 재타현은 press 하나의
  `strikes` 배열로 병합한다.
- [`run_fingering.py`](../../tab2fingermapping/fingermapping/run_fingering.py)가 내보내는 `notes`의
  `finger`는 오른손 i/m/a가 아니라 왼손
  운지 번호다.
- [`transcribe.py::segment_notes()`](../../tab2fingermapping/conformer/transcribe.py)는 줄별 class run과
  pitch 변화를 note 구간으로 바꾼다.
  그러므로 pitch가 바뀐 `t_on`은 acoustic segmentation 결과이며 pluck/legato 원인을 알려주지 않는다.
- [`task_strike.py`](../../tab2body/env/tasks/task_strike.py)와
  [strike reward](../../tab2body/env/rewards/strike.py)는 2026-07-23 S0 범위로 구현됐다. 아래 IR 중
  single-pick subset은 실제 계약이고 strum/fingerstyle 필드는 후속 schema 설계다.

## 1단계: SourceNote 계약

source는 upstream 사실만 담는다.

```json
{
  "source_note_id": 24,
  "t_on": 3.2500,
  "t_off": 3.5000,
  "string": 0,
  "string_convention": "csv_0_low_E",
  "effects": {},
  "source": "fingering.notes",
  "source_time_unit": "seconds"
}
```

규칙:

1. 시각 정본은 `notes[].t_on`이다. 이는 right-hand strike가 아니라 sound-onset candidate다.
2. `presses[].strikes`는 fretted note 일치 감사에만 쓴다. 개방현·왼손 미배정 note가 빠지므로 복구
   원본이나 오른손 전수 목록으로 사용하지 않는다.
3. CSV `string 0=low-E`를 plan의 Isaac `0=high-e, 5=low-E`로 builder 경계에서 한 번만 변환한다.
4. 동시 onset을 한 후보군으로 묶되, 이 단계에서는 multi_pluck인지 strum인지 발명하지 않는다.
5. t_off는 울림 길이이지 오른손이 줄에 머무는 시간은 아니다. mute 주법이 없으면 strike 운동에 쓰지 않는다.
6. source SHA-256과 원본 note ID를 이후 intent/plan/checkpoint에 보존한다. upstream에 안정적인 ID가
   없으면 정규화 전 canonical 입력 순서로 ID를 결정론적으로 부여하고 원본 배열 index도 보존한다.

## 2단계: StrikeIntent 계약

```json
{
  "source_note_id": 24,
  "string": 5,
  "string_convention": "isaac_0_high_e",
  "t_on": 3.2500,
  "requires_rh_attack": "true",
  "attack_reason": "explicit_or_default_pluck",
  "group_id": 12,
  "grouping_provenance": "exact_onset"
}
```

`requires_rh_attack`은 `true/false/unknown`이다.

- `true`: pick/pluck/strum처럼 오른손 공격이 명시되거나 신뢰 가능한 규칙으로 확인됨.
- `false`: tied continuation, hammer-on/pull-off 등 오른손 재공격이 없어야 함.
- `unknown`: 현재 Stage1처럼 effect 정보가 부족해 판단할 수 없음.

일반 학습 입력에는 `unknown`을 남기지 않는다. annotation이 없다면 실험 profile이
`assume_attack_for_unknown=true`처럼 명시적으로 해결하고 provenance에 **가정**임을 저장한다. 이를
upstream 정답으로 기록하지 않는다. 모든 onset을 무조건 strike로 처리하면 legato 구간이 구조적으로
부자연스러워진다.

동시 onset grouping도 `exact/within_tolerance/quantized/manual` provenance를 보존한다. 왼손 운지를 위한
50 ms sonority 묶음을 오른손 동시 pluck 정답으로 재사용하지 않는다.

## 3단계: StrikeMapper 계약

`StrikeMapper`는 왼손의 finger mapping과 대응되는 오른손 규칙 엔진이다. 입력은 attack=true intent와
곡/실험 technique preset이며, 출력은 재현 가능한 plan이다.

### 우선순위

1. 사람이 제공한 event annotation.
2. 곡·트랙 technique preset.
3. 결정론적 mapping 규칙과 전후 문맥 비용.
4. 어느 경로로도 결정할 수 없으면 오류. 무작위 agent 선택 금지.

### 초기 preset

| preset | 처리 |
|---|---|
| `pick_only_v1` | 모든 단현 agent=pick. chord는 명시 설정에 따라 pick strum 또는 오류 |
| `fingerstyle` | p/i/m/a mapping solver가 target별 agent를 배정 |
| `hybrid` | pick이 지정 bass, m/a가 upper target을 담당 |
| `annotated` | 입력 annotation만 사용하고 빈 항목은 오류 |

현재 프로젝트 데이터에는 오른손 annotation이 없으므로 첫 구현은 **곡/실험에 `pick_only_v1`을 명시**하는
것이 가장 정직하다. universal agent schema는 처음부터 유지하되 여러 주법을 한꺼번에 추측·학습하지 않는다.

### phrase 단위 hand setup

agent를 event마다 독립 선택하지 않는다. 먼저 phrase/episode의 hand setup을 정한다.

| hand_setup | 사용 가능 agent | 금지/주의 |
|---|---|---|
| `plectrum` | pick | 피크를 쥔 thumb/index를 finger-pluck으로 동시에 사용 금지 |
| `fingerstyle` | thumb/index/middle/ring, 명시 pinky | pick target 금지 |
| `hybrid` | pick + middle/ring, 명시 pinky | pick grip의 thumb/index finger-pluck 금지 |

setup 전환은 pick을 잡거나 놓는 실제 동작이므로 event 한 프레임에서 즉시 바뀌지 않는다. 명시된 휴지
구간과 transition plan이 없으면 phrase 내부 setup 변경을 거부한다.

### mapper가 최적화할 것

- 동일 motif의 agent/direction 일관성.
- 불필요한 손목·팔 이동과 strike-zone 위치 점프 최소화.
- 다음 event까지 도달 가능성.
- 빠른 동일 줄 반복에서 alternate/economy 또는 i/m 교대 규칙.
- multi_pluck의 한 agent 한 target 점유와 손가락 교차 방지.
- strum의 단조로운 줄 순서와 최대 span 시간.
- 현재 event의 recovery가 다음 event approach로 자연스럽게 연결되는지.

mapper는 최종 joint trajectory를 만들지 않는다. `agent`, `direction`, `zone`, `phase timing`,
`relation` 같은 **운동 의도**만 정하고 실제 관절 운동은 정책이 물리적으로 해결한다.

## 4단계: StrikePlan 계약

2026-07-23 구현 정본은 `tab2body.strike-plan.v1`이다. 아래 긴 예시는 strum/fingerstyle까지 확장할
개념 모델이고, 현재 실행 가능한 v1은 `single`만 허용한다. exact key 검사는
`tab2body/strike_contract.py`, 실제 42-event 예시는
`strike/contracts/02_Jazz1-200-B_solo.strike-plan.json`을 따른다. `multi_pluck/strum` enum은
예약되어 있지만 validator가 명시적으로 거부하며, traversal/muted/ordered-target 계약을 구현한 다음
schema를 올려야 한다.

```json
{
  "schema": "tab2body.strike-plan.v1",
  "song_id": "example_song",
  "source_sha256": "...",
  "intent_sha256": "...",
  "mapper": {"version": "v1", "preset": "pick_only_v1", "config_sha256": "..."},
  "events": [{
    "event_id": 24,
    "source_note_ids": [24],
    "t_onset": 3.2500,
    "hand_setup": "plectrum",
    "kind": "single",
    "targets": [{
      "string": 5,
      "agent": "pick",
      "surface": "pick",
      "release_intent": "up",
      "onset_offset_s": 0.0,
      "zone_y_preferred_m": [-0.355, -0.295]
    }],
    "audible_mask": [0, 0, 0, 0, 0, 1],
    "traversal_mask": [0, 0, 0, 0, 0, 1],
    "muted_mask": [0, 0, 0, 0, 0, 0],
    "ordered_targets": null,
    "stroke_direction": "up",
    "stroke_mode": "free",
    "intensity": 0.5,
    "window_early_frames": 2,
    "window_late_frames": 3,
    "max_span_frames": 1,
    "phrase_lane_y_m": -0.325,
    "schedule": {
      "approach_start": 3.0833,
      "release_target": 3.2500,
      "recover_by": 3.3500
    },
    "relation_prev": "adjacent",
    "relation_next": "repeat",
    "anchor_mode": "none",
    "provenance": {
      "agent": "preset",
      "direction": "mapper",
      "intensity": "neutral_default",
      "lane": "mapper"
    }
  }]
}
```

### 필수 필드

- event identity와 raw source 연결.
- `single / multi_pluck / strum`.
- target별 `string / agent / surface / zone`.
- 들리는 줄 `audible_mask`, 실제 지나가는 줄 `traversal_mask`, 음소거 줄 `muted_mask`.
- target마다 정확한 값은 `onset_offset_s`, 허용 범위는 `onset_offset_band_s=[lo,hi]` 중 정확히
  하나를 사용한다. chord/strum의 미세 시간차를 보존한다.
- `ordered_targets` key는 항상 존재하며 non-strum은 `null`, strum은 target의 정확한 순열이다.
- acoustic onset/release 기준 시각과 허용 window.
- direction 또는 finger release intent.
- approach/release/recover 시간 관계.
- 이전·다음 event 관계.
- intensity. source에 없으면 명시적 neutral default와 provenance.
- anchor mode. 기본은 `none`; 근거 없는 고정점을 만들지 않는다.
- stroke mode. v1 손가락은 free stroke만 지원하고 rest stroke는 landing string까지 명시해야 한다.

모든 추론 필드는 provenance를 저장한다. 실제 annotation과 mapper default를 평가에서 구분할 수 있어야 한다.

`schedule.recover_by`는 RECOVER 시작 시각이나 nominal release 직후의 고정 phase 경계가 아니라
**가장 늦은 계획 회복 완료 시각**이다. late window 끝보다 뒤에 recovery margin을 두며, runtime
RECOVER는 실제 RELEASE pulse에서 시작한다. event가 miss이면 가짜 RELEASE를 만들지 않고 miss용
reposition plan으로 넘어간다.

S0의 `entry_side`, `exit_side`, `next_recovery_target`은 별도 JSON key가 아니다.
`stroke_direction/release_intent/relation_next`, target string과 다음 event에서 mapper가 결정론적으로
유도해 RuntimeGoal에 넣는다. K-1 fixture가 이 유도 결과를 검사한다. 물리 pick/fingerstyle에서 이
정보를 독립 annotation으로 보존해야 할 때만 schema version을 올려 직렬화한다.

## 5단계: 60 Hz RuntimeGoal

정책에는 JSON 객체 대신 현재 event와 미래 event를 정규화한 고정 길이 텐서를 준다.

### Actor 필수 관측

- 음악 event state와 별도인 현재 motor phase one-hot:
  `READY/APPROACH/RELEASE_RECOVER`.
- phrase hand_setup one-hot과 setup transition 상태.
- 실제 존재해 검출할 `present_agent_mask`, 현재 target의 `target_agent_mask`, remaining mask.
- time-to-onset, time-to-window-open/close, phase progress.
- direction, kind, stroke mode, intensity, phrase lane와 allowed zone 폭.
- audible/traversal/muted mask와 target별 onset offset.
- 현재와 0.10/0.25 s 및 다음 3~5개 event의 동일 핵심 필드.
- 이전/다음 관계: repeat/adjacent/leap/multi/strum/rest.
- `(agent,string)` detector re-arm state와 현재 frame release pulse.
- signed gap/contact/load proxy는 pick S0의 선택적 진단값이며 actor 필수 입력이 아니다.
- 기타 로컬 wrist, pick, fingertip 위치·속도와 prev action.
- 정규화 곡 진행률.

### Critic 전용 후보

- event completion 누계와 wrong-string/agent 누계.
- exact time-window phase와 mapper cost.
- 안전 진단값.

행동에 필요한 agent·방향·시간을 critic에만 숨기면 안 된다.

## 룩어헤드 방식

고정 시간 샘플만으로는 빠른 구간에서 여러 event를 놓칠 수 있고 느린 구간에서는 같은 event만 반복한다.
따라서 다음 두 가지를 함께 쓴다.

- 시간 기반: 현재, +0.10 s, +0.25 s.
- event 기반: 최소 next1..next3, 빠른 곡은 최대 next5.

중복 event는 valid mask로 구분한다. 빠른 연타에서도 뒤 event를 보고 coarticulation하고, 긴 쉼에도
time-to와 예상 reach time으로 출발 시점을 정한다. mapper는 넓은 allowed zone 안에서 phrase-level
`phrase_lane_y_m`를 정하며, 음색/주법 변경이 없으면 event마다 목표 y를 무작위로 바꾸지 않는다.

## plan 검증

loader는 물리 환경 생성 전에 다음을 전수 검사한다.

1. attack=true intent만 plan에 정확히 한 번 존재하고 false intent는 target이 아님.
2. source note 전체가 true/false로 해결되며 unknown이 남지 않음.
3. 모든 `unspecified` agent가 해결됨.
4. event kind와 agent 점유 및 hand_setup availability가 일치함.
5. `approach_start≤release_target≤window_close<recover_by`이며 release target과 event/target onset이 일관됨.
6. 같은 agent의 겹치는 event가 실제로 가능한 strum/restrike가 아니면 오류.
7. direction과 ordered target 순서 일치.
8. preferred zone이 allowed strike zone 안에 포함.
9. audible/traversal/muted mask와 target·order가 일치하고, 비연속 target strum의 mute 정보가 해결됨.
10. target별 offset band, 전체 span과 방향/order가 일관됨.
11. free/rest stroke 지원 범위와 landing string이 명확함.
12. window 중첩이 일대일 crossing 매칭을 모호하게 만들지 않음.
13. 모든 추론값에 mapper version과 provenance 존재.
14. song ID, source SHA, intent SHA, plan SHA를 checkpoint contract에 저장.

## 2026-07-23 pilot에서 봉인했던 역사적 계약

2026-07-23 다음처럼 동결했다.

- schema는 `tab2body.strike-plan.v1`; S0 offset은 줄별 `[low,high]` 6개이며 모두 `[0,0]`.
- 당시 RuntimeGoal은 `runtime-goal-manifest.json`의 593D field 순서와 정규화를 따랐다.
- matcher는 exact pending target을 한 번만 소비하고 error는 배타적으로 분류한다.
- pick crossing은 `0<t≤1`, `0≤s≤1`, 최소 속도/깊이와 물리 separation/time re-arm을 쓴다.

이 593D 계약과 checkpoint는 제거됐으며 새 263D v1에 로드하지 않는다. 과거 예시의
`direction/pick_free/timing.prepare_start` 같은 별칭도 새 최소 loader가 조용히 허용하지 않는다.

## 선택 결론

- **`notes.t_on` 그대로**: 음향 onset 후보 원본으로 사용한다.
- **`presses[].strikes` 그대로**: 오른손 원본으로 사용하지 않는다.
- **raw onset을 그대로 정책 입력**: 사용하지 않는다.
- **정책 입력**: attack intent를 해결하고 versioned `StrikePlan`으로 확장한 60 Hz 표현을 사용한다.
- **현재 데이터의 첫 preset**: `pick_only_v1`을 명시한다.
- **fingerstyle/hybrid**: 같은 schema를 쓰되 annotation 또는 별도 오른손 mapping solver를 거친다.
