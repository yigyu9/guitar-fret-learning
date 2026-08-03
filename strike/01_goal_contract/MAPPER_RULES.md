# StrikeMapper 결정 규칙 C1~C48

> 목적: sound-onset 후보를 보고 event마다 즉흥적으로 agent를 고르는 대신, 곡/phrase 전체에서 일관된
> 오른손 실행안 하나를 결정론적으로 만든다. mapper는 joint trajectory를 만들지 않는다.

## 0. 구현 결론

현재 데이터에는 신뢰 가능한 오른손 agent·방향·주법 annotation이 없다. 따라서 첫 구현은
`pick_only_v1` profile을 곡/실험 설정에 명시하고, 이것이 **사람 annotation이 아니라 canonical
realization**임을 provenance에 남긴다. raw acoustic correctness와 plan adherence를 별도 평가한다.

```text
SourceNote → StrikeIntent → phrase segmentation → hand setup
           → event-kind candidates → sequence-level agent/direction search
           → microtiming/lane/phase schedule → validated StrikePlan
```

## A. source와 attack intent

| ID | 결정 규칙 |
|---|---|
| C1 | source는 `notes[]` 전수이며 `presses[].strikes`를 합집합하거나 복구 원본으로 쓰지 않는다 |
| C2 | 원본 note ID가 있으면 보존하고, 없으면 canonical 입력 순서로 결정론적 ID를 부여해 원본 index·`t_on/t_off`·string·effect·source SHA와 함께 보존한다 |
| C3 | 명시 effect/annotation이 있으면 `requires_rh_attack=true/false`를 먼저 결정한다 |
| C4 | effect가 부족하면 `unknown`으로 두며 mapper 내부에서 조용히 true로 바꾸지 않는다 |
| C5 | experiment profile의 `assume_attack_for_unknown`이 unknown을 해결하면 provenance=`experiment_default`다 |
| C6 | 같은/가까운 onset은 candidate group일 뿐 strum 또는 multi-pluck 정답이 아니다 |
| C7 | 빠른 같은 줄 재타현은 별도 source/event ID로 유지하고 window overlap 때문에 병합하지 않는다 |
| C8 | source timestamp uncertainty와 grouping tolerance는 config에 저장하고 결과에 provenance를 남긴다 |

attack intent 우선순위는 `manual annotation > 신뢰 가능한 score effect > versioned experiment profile >
unresolved error`다. `tied/hammer/pull` 어휘가 입력 포맷마다 다르면 loader 경계에서 canonical effect로
변환하며 모르는 문자열은 false로 추측하지 않는다.

## B. phrase와 hand setup

| ID | 결정 규칙 |
|---|---|
| C9 | 명시 phrase 경계가 최우선이며 없으면 configurable rest와 technique 변화 후보로 분할한다 |
| C10 | rest threshold는 고정 상식값이 아니라 profile version에 포함하고 plan에 기록한다 |
| C11 | setup 선택 우선순위는 event annotation > track/phrase annotation > experiment preset이다 |
| C12 | `plectrum`의 target 가능 agent는 pick뿐이다 |
| C13 | `fingerstyle`의 target 가능 agent는 p/i/m/a와 명시된 c이며 pick target은 금지한다 |
| C14 | `hybrid`의 target 가능 agent는 pick+m/a와 명시된 c이며 pick grip의 thumb/index pluck은 금지한다 |
| C15 | phrase 내부 setup 변경은 regrip transition과 충분한 rest가 명시되지 않으면 infeasible이다 |

에셋에 `RH:pick` marker가 항상 존재해도 fingerstyle phrase에서 그것은 실제 피크로 간주하지 않는다.
`present_agent_mask`는 물리적으로 검사할 body, `target_agent_mask`는 이번 event의 목표를 뜻한다. 실제
비활성 손가락 crossing은 FP지만 fictitious/inactive pick marker는 detector 입력에서 제외할 수 있어야 한다.

## C. event kind와 string mask

| ID | 결정 규칙 |
|---|---|
| C16 | attack=true target 하나는 `single` 후보다 |
| C17 | 서로 다른 agent가 각기 한 줄을 release하면 `multi_pluck`이다 |
| C18 | 한 agent가 여러 줄을 단조 순서로 통과하면 `strum`이다 |
| C19 | 같은 onset 표기만으로 C17과 C18 중 하나를 확정하지 않는다 |
| C20 | 명시 strum/span/mute annotation이 있으면 audible/traversal/muted mask를 그대로 보존한다 |
| C21 | audible target 사이 빈 줄을 자동 audible로 만들지 않는다 |
| C22 | 물리 sweep이 지나가는 mute 줄은 traversal+muted에 두되 audible에는 넣지 않는다 |
| C23 | mute/span 정보가 없는 비연속 target은 한 agent strum 후보에서 제외한다 |
| C24 | 한 agent를 같은 instant의 여러 single target에 복제하지 않는다; 이는 strum 후보여야 한다 |

mask invariant:

```text
audible_mask ∩ muted_mask = ∅
audible_mask ∪ muted_mask ⊆ traversal_mask      # strum
target strings = audible_mask                   # 현재 음향 목표
ordered_targets는 traversal 순서와 direction에 일치
```

multi-pluck은 sweep이 아니므로 target 사이 줄을 traversal에 자동 포함하지 않는다.

## D. agent assignment

| ID | 결정 규칙 |
|---|---|
| C25 | 사람 agent annotation은 모든 관례 prior보다 우선한다 |
| C26 | `pick_only_v1`의 single은 pick, 연속 mask chord는 profile이 허용할 때만 pick strum이다 |
| C27 | fingerstyle은 target마다 서로 다른 available agent를 하나씩 배정한다 |
| C28 | p=저음, i/m/a=고음은 soft cost이고 hard string 고정표가 아니다 |
| C29 | 손 안쪽 agent 순서와 string 순서가 교차하는 assignment는 infeasible 또는 최상위 비용이다 |
| C30 | 빠른 같은 줄 fingerstyle run은 i/m 교대와 충분한 agent recovery를 우선한다 |
| C31 | hybrid는 지정 bass/내성 pick과 upper m/a/(c)를 우선하고 grip 충돌 후보를 제거한다 |
| C32 | 모든 hard constraint 뒤 동률은 고정 agent 어휘 순서와 event ID로 결정해 재현성을 보장한다 |

fingerstyle 후보 비용에는 최소한 다음을 둔다.

- agent가 이전 release에서 회복할 수 있는가.
- 현재 string에서 다음 string까지 손가락 이동량.
- 같은 agent 과사용과 i/m alternation 위반.
- 손가락 assignment crossing과 비활성 손가락 간섭 위험.
- 다음 2개 이상 event까지 보았을 때 palm/wrist lane이 유지되는가.

수치 weight는 synthetic feasibility와 reference 분포 전에는 후보값이다. hard constraint를 큰 벌점 하나로
흉내 내지 않고 후보 생성 단계에서 제거한다.

## E. pick/strum 방향

| ID | 결정 규칙 |
|---|---|
| C33 | source에 방향 annotation이 있으면 plan은 그대로 따른다 |
| C34 | source의 `either`는 원본에 보존하되 runtime plan에는 실제 `down/up`을 넣는다 |
| C35 | profile은 `alternate/economy/all_down/free` 중 하나를 명시한다 |
| C36 | alternate는 같은 run 안에서 down/up을 교대하고 event마다 home pose로 돌아가지 않는다 |
| C37 | economy는 이전 RECOVER의 follow-through가 다음 string entry side와 같은 방향일 때 동일 방향을 허용한다 |
| C38 | strum 방향은 ordered traversal과 일치하고 string field 안에서 반전하는 후보를 제거한다 |

각 event의 greedy 최소 이동만 고르지 않고 phrase candidate graph에서 다음 목적함수를 최소화한다.

```text
total_cost = Σ event_cost(realization_e)
           + Σ transition_cost(realization_e, realization_e+1)
```

transition cost는 direction 연속성, string 이동, agent recovery, phrase lane jump, setup 전환, entry/exit
side 충돌을 포함한다. 동률 tie-break와 mapper version을 plan hash에 포함한다.

## F. microtiming과 intensity

| ID | 결정 규칙 |
|---|---|
| C39 | source에 줄별 실제 onset이 있으면 기준 onset과 target별 정확한 `onset_offset_s`를 손실 없이 보존한다 |
| C40 | multi-pluck의 annotation 없는 offset은 profile의 `onset_offset_band_s=[lo,hi]`로 두고 exact same substep을 강제하지 않는다 |
| C41 | strum은 target별 monotone `onset_offset_band_s`와 전체 sweep duration을 함께 생성한다 |
| C42 | intensity가 없으면 neutral default와 provenance를 기록하고 오디오 amplitude를 force로 바로 바꾸지 않는다 |

첫/중앙/마지막 줄 중 무엇이 score onset인지 profile에 명시한다. 단일 `max_span_frames`만 두어 한 frame
폭주 sweep을 허용하지 않는다. 값은 seconds와 control frame 양쪽으로 저장하되 seconds가 의미 정본이다.

## G. strike lane·phase·coarticulation

| ID | 결정 규칙 |
|---|---|
| C43 | phrase 시작에 allowed zone 안의 `phrase_lane_y_m`와 band를 정하고 이유 없는 event별 y jump를 금지한다 |
| C44 | 음색/technique annotation이 바뀌면 여러 event에 걸친 lane transition을 만들고 순간이동시키지 않는다 |
| C45 | `schedule.approach_start = onset - estimated_reach_time - margin`이며 거리·agent·tempo별 reach model을 쓴다 |
| C46 | S0는 `stroke_direction/release_intent/relation_next`에서 entry side·exit side·next recovery target을 결정론적으로 유도해 RuntimeGoal에 넣고 중복 plan key를 만들지 않는다 |
| C47 | 짧은 run의 RECOVER는 다음 APPROACH와 겹칠 수 있고 매 note neutral 복귀를 만들지 않는다 |
| C48 | mapper는 wrist/finger joint waypoint를 출력하지 않고 corridor와 시간 관계까지만 출력한다 |

idle plan은 gap 길이로 나눈다.

- short: 현재 oscillatory cycle을 유지하며 다음 entry side로 이어간다.
- medium: 다음 phrase lane 근처의 ready manifold에 머문다.
- long: profile이 허용한 relaxed/anchor mode로 park하고 reach deadline에 출발한다.

## 결정론적 compile 절차

```text
1. SourceNote 전수 로드·검증·hash
2. 각 note의 attack intent 해결; unknown이 남으면 중단
3. attack=true note를 candidate onset group과 phrase로 분할
4. phrase hand setup을 고르고 불가능한 agent 후보 제거
5. event별 kind/agent/direction/mask 후보 열거
6. phrase graph에서 총 event+transition cost 최소 경로 선택
7. microtiming, lane, approach/release/recover schedule 생성
8. hard invariant·도달시간·window 일대일성 검사
9. provenance와 source/intent/config/plan hash 저장
10. 같은 입력·version·seed에서 byte-equivalent plan인지 재생성 검사
```

초기에는 ambiguity를 정책 관측으로 모두 넘기지 않는다. 하나의 versioned canonical plan으로 정확도와
물리 실행을 먼저 학습하고, 여러 valid realization을 다루는 것은 plan-conditioned 정책이 안정된 뒤의
별도 확장이다.
