# 1. strike goal — 음향 onset 후보를 실행 가능한 오른손 계획으로 만들기

> **현재 source v3 / compiled plan v4:** 손가락·hybrid는 확장 설계지만 pick-only single/strum과 phrase down/up 계획은
> 구현되어 있다. 원본은 다음 최소 사건 계약을 사용하고 실행 전 `strike_plan.v4`로 컴파일한다.
> 원속도 traversal-edge 전이가 물리 계약을 만족하지 않으면 학습 전에 차단한다.

```json
{
  "schema": "tab2body.strike_training.v3",
  "metadata": {
    "fps": 60,
    "profile": "pick_gesture_compiler_v3",
    "string_convention": "Isaac 0=high-e, 5=low-E"
  },
  "events": [
    {"time": 1.25, "frame": 75, "string": 2}
  ]
}
```

- event의 필수 키는 `time`, `frame`, `string`이다. v3 선택 키는 `event_id`, `source_time`,
  `time_uncertainty_s`, `source_ref`이며 v1/v2도 계속 읽는다.
- `time`이 정본이다. `frame`은 nearest 60 Hz 값이며 오차가 0.5 frame을 넘으면 거부한다.
- 시간과 frame은 감소하지 않는다. 같은 onset의 이종 줄 사건은 strum 후보로 보존한다.
- 외부 원본에는 방향이 없지만 `phrase_dp_microtiming_v3` 계획기가 곡 전체를 본 뒤 각 사건의
  `down/up`을 확정한다. RL은 `strike_plan.json`의 방향을 그대로 실행한다.
- A0~A3는 single motor skill, A4는 실제 strum 문맥의 clean recovery, S0~S2는 2~6줄 strum
  기술을 배우며 S3에서 원래 timeline을 사용한다.
- builder는 fingering `0=low-E`를 경계에서 정확히 한 번 `5-string`으로 변환한다.
- plan은 사건 중심 간격 대신 이전 traversal의 마지막 offset과 다음 traversal의 첫 offset 사이를
  검사한다. 방향 반전 경로가 방금 친 줄을 다시 지나면 clearance가 필요한 전이로 기록한다.
- 자동 묶음이 source evidence와 충돌할 때는 원본 시각을 덮어쓰지 않는다. 연속 source ID,
  `merge|separate`, 이유와 JSON evidence가 모두 있는 reviewed override만 허용한다.
- `audit_strike_goal_quality.py --all`로 bundle 전체를 먼저 검사하고, `INFEASIBLE`은 full-song
  학습 전에 해결한다. `AMBIGUOUS`는 진단을 보존하되 자동 정답으로 취급하지 않는다.

구현 정본은 `tab2body/env/strike_goal_compiler.py`, `tab2body/env/strike_goals.py`와
`tab2body/tools/build_strike_plan.py`다.

정책의 현재 기본 관측은 `strike.observation.v2` 303D다. 이 문서 뒤쪽의 263D와
`strike-plan.v1` 예시는 삭제된 pilot 계약을 설명하는 역사 절이며 현재 실행에 사용하지 않는다.

## 책임 경계

현재 upstream이 신뢰성 있게 제공하는 것은 주로 `notes[].t_on`, `t_off`, 줄, fret/pitch다. 여기서
`t_on`은 **새 소리가 시작된 후보 시각**이지 언제나 오른손이 줄을 친 시각은 아니다. hammer-on,
pull-off, slide 또는 전사 분할도 새 onset을 만들 수 있다. `presses[].strikes`는 왼손 press에 붙인
재타현 시각 projection이며 개방현과 왼손 미배정 note를 누락하므로 오른손 원본으로 쓰지 않는다.

따라서 strike 입력은 다음 네 층으로 분리한다.

| 층 | 질문 | 변경 가능 여부 |
|---|---|---|
| `SourceNote` | 언제 어느 줄에서 새 소리가 시작됐는가 | upstream 사실로 보존 |
| `StrikeIntent` | 이 onset에 오른손 공격이 필요한가 | annotation/profile로 해결 |
| `StrikePlan` | 어떤 setup·agent·방향·주법으로 실행할 것인가 | versioned mapper가 결정 |
| `RuntimeGoal` | 현재/다음 event, 3-phase 운동 상태와 re-arm 상태는 무엇인가 | plan을 60 Hz로 래스터화 |

환경은 `StrikePlan`을 실행할 뿐 음높이, 코드명, 왼손 손가락 배정이나 주법을 프레임마다 다시 추론하지
않는다. 자세한 데이터 흐름은 [GOAL_ARCHITECTURE.md](GOAL_ARCHITECTURE.md), 실제 agent·방향·주법
선택 순서는 [MAPPER_RULES.md](MAPPER_RULES.md)를 따른다.

## SourceNote와 StrikeIntent

```json
{
  "source_note_id": 24,
  "t_on": 3.250,
  "t_off": 3.500,
  "string": 0,
  "string_convention": "csv_0_low_E",
  "effects": {},
  "source": "fingering.notes"
}
```

```json
{
  "source_note_id": 24,
  "string": 5,
  "string_convention": "isaac_0_high_e",
  "requires_rh_attack": "true",
  "attack_reason": "experiment_default",
  "group_id": 12,
  "grouping_provenance": "exact_onset"
}
```

`requires_rh_attack`의 정본 어휘는 `true/false/unknown`이다. `unknown`을 학습 직전에 조용히 `true`로
바꾸지 않는다. effect annotation이나 명시적인 실험 profile로 해결하고, 그 결정의 provenance를 남긴다.
upstream에 안정적인 note ID가 없으면 builder가 정규화 전 원본 note의 canonical 입력 순서로
`source_note_id`를 결정론적으로 부여하고, 원래 배열 index와 source provenance를 함께 보존한다.

## StrikePlan 실행 이벤트 스키마

아래 객체는 upstream raw가 아니라 mapper가 만든 **물리 실행 IR**이다. 실제 JSON 키는 구현 시 이
이름을 기준으로 schema version과 함께 봉인한다.

```json
{
  "event_id": 17,
  "source_note_ids": [24],
  "t_onset": 1.250,
  "hand_setup": "fingerstyle",
  "targets": [{
    "string": 5,
    "agent": "thumb",
    "surface": "flesh",
    "release_intent": "thumb_outward",
    "onset_offset_s": 0.0
  }],
  "kind": "single",
  "stroke_mode": "free",
  "stroke_direction": "none",
  "audible_mask": [0, 0, 0, 0, 0, 1],
  "traversal_mask": [0, 0, 0, 0, 0, 1],
  "muted_mask": [0, 0, 0, 0, 0, 0],
  "ordered_targets": null,
  "window_early_frames": 2,
  "window_late_frames": 3,
  "max_span_frames": 1,
  "phrase_lane_y_m": -0.325,
  "intensity": 0.5,
  "schedule": {
    "approach_start": 1.0833,
    "release_target": 1.2500,
    "recover_by": 1.3500
  },
  "relation_prev": "rest",
  "relation_next": "adjacent",
  "anchor_mode": "none",
  "provenance": {"agent": "preset", "direction": "mapper", "intensity": "neutral_default"}
}
```

같은 onset의 손가락식 화음과 hybrid picking은 다음처럼 target별 주체를 분리한다.

```json
{
  "event_id": 18,
  "source_note_ids": [31, 32, 33],
  "t_onset": 1.500,
  "hand_setup": "hybrid",
  "targets": [
    {"string": 4, "agent": "pick", "surface": "pick", "release_intent": "up", "onset_offset_s": 0.000},
    {"string": 2, "agent": "middle", "surface": "nail", "release_intent": "toward_palm", "onset_offset_s": 0.012},
    {"string": 1, "agent": "ring", "surface": "nail", "release_intent": "toward_palm", "onset_offset_s": 0.008}
  ],
  "kind": "multi_pluck",
  "stroke_mode": "free",
  "stroke_direction": "none",
  "audible_mask": [0, 1, 1, 0, 1, 0],
  "traversal_mask": [0, 1, 1, 0, 1, 0],
  "muted_mask": [0, 0, 0, 0, 0, 0],
  "ordered_targets": null,
  "window_early_frames": 2,
  "window_late_frames": 3,
  "max_span_frames": 1,
  "phrase_lane_y_m": -0.325,
  "intensity": 0.5,
  "schedule": {
    "approach_start": 1.3333,
    "release_target": 1.5000,
    "recover_by": 1.6000
  },
  "relation_prev": "adjacent",
  "relation_next": "rest",
  "anchor_mode": "none",
  "provenance": {"agent": "preset", "direction": "mapper", "intensity": "neutral_default"}
}
```

반대로 엄지나 검지가 여러 줄을 연속으로 훑으면 target별 agent를 복수로 만드는 것이 아니라,
같은 agent를 가진 `kind=strum`과 `ordered_targets`로 표현한다.

| 필드 | 계약 |
|---|---|
| `event_id` | plan 안에서 0부터 연속인 고유 정수 |
| `source_note_ids` | 원본 note와의 역추적 링크. 임의로 끊거나 바꾸지 않음 |
| `t_onset` | 기준 acoustic onset 초. 접근이나 근접이 아니라 RELEASE 목표 시각 |
| `hand_setup` | phrase 단위 `plectrum/fingerstyle/hybrid` |
| `targets` | 비어 있지 않은 `{string, agent, surface}` 배열. string=0..5, agent/surface는 아래 어휘 |
| `kind` | `single`, `multi_pluck`, `strum` |
| `stroke_mode` | v1 손가락은 `free`; `rest`는 landing string을 명시한 별도 지원 주법 |
| `stroke_direction` | pick/strum의 `down/up`, 손가락 multi-pluck은 `none`; source `either`는 plan에서 해결 |
| `release_intent` | target별 pick 방향 또는 finger의 `toward_palm/thumb_outward` 같은 실행 의도 |
| `audible/traversal/muted_mask` | 들려야 하는 줄, 물리적으로 지나가는 줄, mute되어야 하는 줄을 분리 |
| `ordered_targets` | key는 항상 존재. non-strum은 `null`, strum은 `targets`의 정확한 순열 |
| timing window | 초기값은 early 2 frame(33 ms), late 3 frame(50 ms). 실측 전 **후보값** |
| `max_span_frames` | single/multi_pluck=1, strum 초기값=6(100 ms). 첫 줄부터 마지막 줄까지 최대 간격 |
| target onset offset | 정확한 값이면 `onset_offset_s`, 허용 범위면 `onset_offset_band_s=[lo,hi]`; target마다 정확히 하나 |
| `phrase_lane_y_m` | 넓은 allowed zone 안에서 구절 동안 일관되게 유지할 strike lane |
| target zone override | 명시된 음색 위치가 있을 때만 target별 preferred band를 덮어씀. 없으면 phrase lane 사용 |
| `intensity` | source가 없으면 neutral `0.5`와 default provenance를 저장 |
| `schedule` | `approach_start≤release_target≤window_close<recover_by`; `recover_by`는 late release도 회복할 수 있게 둔 최종 완료 시각 |
| `relation_prev/relation_next` | repeat/adjacent/leap/multi/strum/rest 등 coarticulation 문맥 |
| `anchor_mode` | 기본 `none`; 허용 profile 없이 손바닥·소지를 고정하지 않음 |
| `provenance` | annotation/profile/mapper 중 각 실행 결정을 만든 근거 |

### 타현 주체(agent) 정본

| 값 | 해부·에셋 대응 | 의미 |
|---|---|---|
| `pick` | `RH:pick` | 엄지·검지 사이 피크의 tip marker |
| `thumb` | `RH:thumb3→thumb_top` | 오른손 엄지(p) pad |
| `index` | `RH:index3→index_top` | 검지(i) pad |
| `middle` | `RH:middle3→middle_top` | 중지(m) pad |
| `ring` | `RH:ring3→ring_top` | 약지(a) pad |
| `pinky` | `RH:pinky3→pinky_top` | 소지(c). 데이터가 명시할 때만 사용 |
| `unspecified` | 없음 | source에 정보가 없음을 뜻하는 중간값. 학습 전 반드시 resolve |

`agent`는 plan adherence 조건이다. 지정하지 않은 손가락이 같은 줄을 쳤다면 음향적으로는 맞을 수 있지만
선택한 plan에는 위반이다. 따라서 평가는 `acoustic hit`와 `plan violation`을 별도로 기록한다. mapper가
추론한 agent를 upstream의 유일한 인간 정답처럼 취급하지 않는다.

`surface`는 `pick`, `nail`, `flesh`, `unspecified` 중 하나다. `agent=pick`은 `surface=pick`이어야 하고,
손가락 agent는 `nail/flesh/unspecified`를 쓸 수 있다. 현재 에셋에는 nail geometry가 없으므로 이 값은
보존·보고하되 nail과 flesh를 물리 성공 조건으로 구분하지 않는다. 향후 nail asset이 생기면 contract
version을 올려 surface까지 감독한다.

## 생성·mapping 규칙

1. `notes[].t_on`을 sound-onset candidate로 보존하고 먼저 `requires_rh_attack`을 해결한다.
   `presses[].strikes[]`는 fretted-note 대조용일 뿐 source 복구나 합집합에 쓰지 않는다.
2. 같은 onset tolerance 안의 여러 줄은 후보 group으로만 묶는다. 그 사실만으로 multi-pluck/strum을
   확정하지 않고 grouping provenance를 보존한다.
3. 명시적 스트럼 정보가 있으면 `kind=strum`, 단일 agent, 실제 traversal 순서를 보존한다. 서로 다른
   손가락이 각 줄을 튕기면 `multi_pluck`, pick과 m/a가 섞이면 hybrid multi-pluck이다.
4. audible target 사이의 빈 줄을 자동으로 들리는 target으로 만들지 않는다. strum span이 명시되면
   `traversal_mask`에는 포함하되 mute 정보에 따라 `audible_mask` 또는 `muted_mask`에 둔다.
5. mute/span 정보 없이 비연속 target을 한 agent strum으로 추측하지 않는다. annotation/profile이
   해결하지 못하면 unresolved 오류로 둔다.
6. source direction의 `either`는 source에 보존하되 mapper가 phrase 문맥과
   `alternate/economy/all_down/free` profile로 plan의 실제 방향을 결정한다.
7. agent annotation이 없으면 intent 단계의 `unspecified`를 보존한다. mapper가 phrase-level
   hand setup과 versioned preset으로 resolve하지 못하면 loader가 중단한다.
8. `plectrum`은 pick만, `fingerstyle`은 p/i/m/a/(명시 c), `hybrid`는 pick+m/a/(명시 c)를 기본으로
   허용한다. 피크를 쥔 thumb/index를 finger target으로 동시에 배정하지 않는다.
9. setup 전환에는 명시된 긴 rest와 regrip transition plan이 필요하다. regrip 모델이 없는 v1에서는
   phrase 내부 전환을 거부한다.
10. mapper는 target joint waypoint를 만들지 않는다. setup, agent, 방향, 순서, 3-phase 시간 관계,
    strike lane/corridor와 recovery relation까지만 정하고 실제 궤적은 물리 정책이 찾는다.

이는 기존 Xu 초안의 “최저~최고 목표줄 자동 채움”을 수정한 결정이다. span 보간은 데이터가 실제로
연속 스트럼을 뜻한다고 보장할 때만 합법이다.

## 서로 독립인 event·운동·detector 상태

음악 event는 `future → eligible → completed | missed`로 한 번만 전이한다.

- `future`: 조기 허용창 전. 접근 보상만 가능하고 교차 성공은 불인정한다.
- `eligible`: `[t-early, t+late]`. 목표 교차를 성공으로 매칭할 수 있다.
- `completed`: 필요한 줄을 한 번씩 맞혔다. 다시 보상하지 않는다.
- `missed`: 지각 허용창 또는 strum span을 넘겼다. 뒤늦은 교차는 false positive다.

pick S0에서 공개 운동 상태는 다음 세 개다.

```text
READY → APPROACH → RELEASE_RECOVER
```

- `READY`: 고정 home이 아니라 다음 event에 도달 가능한 relaxed manifold다.
- `APPROACH`: 이동, entry-side 정렬과 줄 횡단 직전 준비를 한 phase로 묶는다.
- `RELEASE_RECOVER`: crossing 뒤 짧은 follow-through와 separation을 다음 `APPROACH`에 잇는다.
  유한 줄을 가로지른 실제 one-shot RELEASE 시점은 이 phase가 아니라 detector pulse가 정한다. 실제
  `WAIT_REARM→ARMED` 전이는 detector만 결정한다.

빠른 반복에서는 이전 `RELEASE_RECOVER`와 다음 `APPROACH`가 겹칠 수 있다. `CONTACT/LOAD`는 탄성 없는
marker pick S0의 필수 상태가 아니다. 향후 fingertip pad나 물리 pick에서 실제 engagement를 판별할 때
진단 또는 하위 상태로 추가하되 공개 세 phase를 다시 잘게 나누지 않는다.

중복 검출을 막는 detector 내부 상태는 운동 phase와 별개다.

```text
ARMED → RELEASE pulse → WAIT_REARM → ARMED
```

detector는 현재 goal 유무와 관계없이 모든 물리 release/crossing을 기록한다. matcher만 eligible event에
일대일 배정하며, 배정되지 않은 crossing은 항상 false positive다. re-arm도 물리 separation과 시간으로만
결정한다. goal이 없다는 이유로 검출을 끄면 rest 중 반복 오타가 숨는다.

정책 관측은 현재 event와 0.10 s, 0.25 s lookahead뿐 아니라 다음 3~5개 ordered event를 제공한다. 각 항목은
`target_mask(6), target_agent(줄별 7-way: none+6 agents), kind, direction(3 one-hot), time_to_event,
time_to_close, hand_setup, phrase_lane, target별 onset offset, valid`를 포함하고, 현재
strum/multi-pluck에는 `remaining_mask(6)`도 제공한다. 별도 상태 필드로
`motor_phase(READY/APPROACH/RELEASE_RECOVER)`와 `(agent,string)`별 re-arm 상태를 제공한다.
역사적 pick-only pilot v1은 이 풍부한 확장 필드의 일부만 사용해 actor observation을 263D로 봉인했다.
정확한 field 순서와 dimension은 환경 observation manifest와 checkpoint contract에 저장한다.

## 2026-07-23 pilot 계약 기록

2026-07-23 아래 네 항목을 단일 schema로 봉인했다.

1. `StrikePlan`: `tab2body.strike-plan.v1`, 현재 실행 kind는 single만.
2. 당시 `RuntimeGoal`: manifest hash가 있는 exact 593D.
3. matcher: exact target 일대일 소비와 배타적 오류 class.
4. detector: finite swept `t/s`, direction/speed/depth와 ARMED/WAIT_REARM.

이 pilot 계약과 checkpoint는 제거됐고 이후 계약과 호환되지 않는다. 새 loader도 이름이 다른
예시를 암묵적으로 받아들이거나 tensor 차원을 임의로 바꾸지 않는다.

## loader 필수 검사

- 모든 숫자 finite, FPS 양수, frame/time 일치.
- event ID 연속·고유, 정규화 뒤 event 시간 엄격 증가; 동시는 한 event로 묶음.
- target 줄은 0..5이며 한 event에서 줄 하나당 target 하나만 허용. `single`은 정확히 한 target.
- agent는 정본 어휘이고 학습 입력에는 `unspecified`가 남지 않음.
- surface는 정본 어휘이며 pick/손가락 agent와 모순되지 않음.
- `multi_pluck`은 agent가 target별로 서로 다르고, `strum`은 한 agent만 사용.
- hand setup과 target agent가 일치하며 plectrum/hybrid의 thumb/index 중복 사용이 없음.
- `audible_mask`, `traversal_mask`, `muted_mask`가 서로 모순되지 않고 target과 일치함.
- `ordered_targets`는 non-strum에서 `null`, strum에서 target의 정확한 순열이며 direction과 모순되지 않음.
- target별 onset offset band와 전체 span이 일관되고, 한 frame 폭주를 성공으로 강제하지 않음.
- 각 target은 `onset_offset_s` 또는 `onset_offset_band_s=[lo,hi]` 중 정확히 하나만 가지며 band는 정렬·finite.
- `schedule`은 `approach_start≤release_target≤window_close<recover_by`이고 onset과 일관됨.
- window와 span은 음수가 아니며 K-1 matcher 계약으로 일대일 배정이 유일하지 않으면 오류.
  별도 source event를 window 중첩만으로 병합하지 않음.
- free/rest stroke가 지원 범위와 일치하고 rest stroke면 landing string을 명시함.
- 곡 ID, source/intent/plan/config SHA-256과 mapper version을 checkpoint에 저장하고 불일치 resume를 거부.
