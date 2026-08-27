# 사람에 가까운 오른손 strike를 위한 상세 운동 규칙 N1~N90

> 이 문서는 정확한 crossing을 넘어 READY·APPROACH·RELEASE_RECOVER와 다음 동작 연결까지 규정한다.
> 규칙만으로 인간 모션 분포를 완전히 보증할 수는 없다. 여기의 측정 가능한 제약은 reward/diagnostic/gate로
> 사용하고, 최종 “사람다움” 주장은 technique에 맞는 모션 prior와 rollout 영상 감사까지 통과해야 한다.

## 0. 강제 수준

- **HARD**: 위반하면 goal 오류 또는 안전 실패. 정상 주법을 배제하지 않는 명백한 조건만 둔다.
- **TASK**: 타현 정답/오답을 결정한다.
- **SOFT**: 자연스러운 해법을 선호하는 작은 보상. 핵심 타현을 막지 않는다.
- **DIAG**: 분포를 먼저 기록한다. 정상/실패 분리가 확인된 뒤 승격한다.
- **PLAN**: StrikeMapper가 곡 전체 문맥으로 정하며 runtime RL이 임의로 바꾸지 않는다.
- **SAFETY**: 명백한 관통·비유한·폭주 같은 물리 실패. 음악적 실수와 구분한다.
- **EXPERIMENT**: 구조 후보를 대조실험한 뒤 하나를 checkpoint contract로 봉인한다.

## A. 입력·계획 규칙

| ID | 규칙 | 수준 |
|---|---|---|
| N1 | raw onset/string은 불변 sound-onset 후보이며 오른손 공격 정답과 운동 계획에서 분리한다 | HARD |
| N2 | 정책은 raw가 아니라 agent·direction·zone·phase가 해결된 StrikePlan을 본다 | HARD |
| N3 | 미해결 `unspecified` agent를 물리 학습에 넣지 않는다 | HARD |
| N4 | 같은 source+intent+mapper config는 byte-equivalent plan을 만든다 | HARD |
| N5 | 사람 annotation이 preset과 mapper 추론보다 항상 우선한다 | PLAN |
| N6 | 현재 annotation 없는 곡은 `pick_only_v1` 같은 versioned technique preset을 명시한다 | PLAN |
| N7 | mapper는 동일 motif에 같은 agent/direction 해법을 우선한다 | PLAN |
| N8 | mapper는 event를 repeat/adjacent/leap/multi/strum/rest 관계로 표시한다 | PLAN |
| N9 | agent·direction·zone·intensity의 출처를 annotation/default/inference로 기록한다 | HARD |
| N10 | source/intent/plan/config hash가 checkpoint와 다르면 resume를 거부한다 | HARD |

## B. 공통 운동 phase

음악 event의 `future/eligible/completed/missed`와 별개로 각 활성 agent가 아래 정책 motor phase를
따른다. phase는 exact joint waypoint가 아니라 계획·관측·진단의 계약이다.

```text
READY → APPROACH → RELEASE_RECOVER
          ↑                │
          └─ 다음 타현 준비와 겹침 ─┘
```

| ID | 규칙 | 수준 |
|---|---|---|
| N11 | READY는 단일 고정 pose가 아니라 다음 event에 도달 가능한 relaxed ready manifold 안에서 유지한다 | SOFT |
| N12 | APPROACH 시작은 고정 상수가 아니라 현재 거리·relation·tempo의 예상 reach time으로 정한다 | PLAN |
| N13 | APPROACH는 목표 agent·줄·방향의 entry side, zone lane, body clearance를 만족한다 | TASK/SOFT |
| N14 | marker pick의 contact-band 진입과 signed gap은 선택적 진단이며 별도 정책 phase가 아니다 | DIAG |
| N15 | virtual load는 pick S0 성공 조건이 아니며 fingerstyle/물리 pick 후속 detector에서만 검증한다 | DIAG |
| N16 | RELEASE에서만 올바른 속도 부호와 exit crossing을 가진 one-shot strike를 emit한다 | TASK |
| N17 | RECOVER는 짧은 follow-through를 포함해 release 직후 즉시 역전하지 않는다 | SOFT |
| N18 | RECOVER는 무조건 중립으로 돌아가지 않고 다음 event의 APPROACH와 연결한다 | SOFT |
| N19 | 빠른 연타에서는 이전 RECOVER와 다음 APPROACH가 겹칠 수 있다 | PLAN |
| N20 | RELEASE pulse와 event 보상은 한 번만 소비하며 완료 phase의 dense reward를 반복하지 않는다 | HARD |

`RELEASE`와 `RECOVER`는 운동을 설명하고 진단하기 위한 하위 동작 이름이다. 런타임 정책에는 둘을
따로 전환시키지 않고 하나의 `RELEASE_RECOVER` phase로 노출한다. 실제 타현 순간은 phase 전환이
아니라 swept crossing detector가 내는 one-shot RELEASE pulse로 판정한다.

중복 방지 detector는 위 정책 phase와 별도로
`ARMED→RELEASE pulse→WAIT_REARM→ARMED`를 `(agent,string)`마다 유지한다.

### phase 시계 후보

- approach lead: 거리 기반 `5..18 control frame`(약 83..300 ms) 후보.
- RELEASE: analytic swept interpolation으로 subframe 시각을 구해 control frame에 집계.
- recovery/follow-through: release 후 `1..3 control frame` 후보.
- rapid event에서는 RECOVER와 다음 APPROACH를 겹치되 release window와 re-arm 조건은 유지한다.

이 수치는 초기 후보이며 agent별 성공 trajectory를 측정한 뒤 봉인한다. phase가 시간을 맞추기 위한
보조 구조이지 정책에 exact joint trajectory를 강제하는 splining 규칙은 아니다.

## C. 피크 규칙

| ID | 규칙 | 수준 |
|---|---|---|
| N21 | pick target은 `RH:pick` tip만 성공 주체이며 손가락 끝 대체를 허용하지 않는다 | TASK |
| N22 | 엄지-검지 상대 자세와 나머지 손가락의 편안한 굽힘을 strike 전후 유지한다 | SOFT/DIAG |
| N23 | 단현 attack은 손목·전완의 작은 회전이 주가 되고 어깨·팔꿈치는 위치 준비에 주로 쓴다 | SOFT |
| N24 | 같은 줄의 빠른 반복은 계획된 alternate 또는 명시 economy 방향을 일관되게 따른다 | PLAN/TASK |
| N25 | 인접 줄 이동은 이전 RECOVER의 follow-through가 다음 approach side로 이어지는 economy 해법을 허용한다 | PLAN |
| N26 | pick이 줄 아래로 필요 이상 깊게 들어가거나 soundboard 쪽으로 dive하지 않는다 | SOFT/SAFETY |
| N27 | string crossing 뒤 re-arm 전 동일 줄 떨림을 새 strike로 세지 않는다 | TASK |

피크 접촉 grip force는 humanoid self-collision OFF에서 관측할 수 없으므로 사용하지 않는다. 상대 pose와
joint configuration을 진단하고, 별도 물리 pick asset 도입 전에는 “실제로 쥐었다”고 주장하지 않는다.

## D. 엄지·손가락식 타현 규칙 — K6/fingerstyle V2

| ID | 규칙 | 수준 |
|---|---|---|
| N28 | thumb/index/middle/ring/pinky는 각 `*3→*_top`의 tip pad만 성공 후보로 쓴다 | TASK |
| N29 | V2 손가락 detector는 armed→contact→load→release를 완료해야 하며 줄 위 정지는 strike가 아니다 | TASK |
| N30 | fingerstyle attack은 활성 손가락 굽힘이 주가 되고 손목 전체의 큰 스윙으로 대체하지 않는다 | SOFT |
| N31 | 엄지 p는 다른 손가락과 독립적으로 움직이고 비활성 i/m/a를 과도하게 펴지 않는다 | SOFT |
| N32 | p=저음, i/m/a=고음 역할은 mapper prior이며 명시 goal을 덮어쓰는 hard rule은 아니다 | PLAN |
| N33 | 빠른 동일 줄 fingerstyle 반복은 가능하면 i/m 교대를 사용하고 같은 손가락 과사용을 비용화한다 | PLAN |
| N34 | 손가락들의 target string 순서와 손 안쪽 순서가 교차하는 assignment를 피한다 | PLAN/HARD |
| N35 | 비활성 손가락 pad가 다른 줄을 engage하면 wrong-agent/string으로 기록한다 | TASK |
| N36 | nail/flesh annotation은 보존하되 nail geometry 전에는 물리 결과를 구분했다고 주장하지 않는다 | DIAG |

## E. 동시 타현·스트럼·하이브리드

| ID | 규칙 | 수준 |
|---|---|---|
| N37 | multi_pluck은 서로 다른 agent가 서로 다른 target을 같은 onset window에 완료한다 | TASK |
| N38 | multi_pluck release spread는 plan offset band를 따르며, annotation 없는 동시 후보의 초기 band만 1 control frame 이내다 | TASK/DIAG |
| N39 | 한 agent를 동시에 두 단현 target에 배정하지 않는다; 연속 통과는 strum이다 | HARD |
| N40 | strum은 한 agent가 ordered target을 한 방향으로 단조롭게 통과한다 | TASK |
| N41 | strum 중 되돌아가 누락 줄을 채우는 zig-zag를 한 event로 인정하지 않는다 | TASK |
| N42 | strum 첫 target release가 음악 onset 기준이며 줄별 실제 offset과 전체 span을 기록한다 | TASK |
| N43 | strum은 손목·전완 중심, 넓거나 강한 stroke에서만 팔꿈치 기여를 점진적으로 허용한다 | SOFT |
| N44 | hybrid는 pick grip을 유지하면서 지정 m/a가 독립적으로 upper string을 pluck한다 | SOFT/TASK |
| N45 | pick과 finger target의 궤적·준비 side가 서로 충돌하는 plan을 loader가 거부한다 | HARD |

rasgueado, slap, tap, palm mute는 별도 detector가 필요하다. 이들을 일반 strum/pluck 규칙에 맞춰
성공으로 꾸미지 않는다.

## F. 팔·손목·손가락 협응

| ID | 규칙 | 수준 |
|---|---|---|
| N46 | 큰 string leap와 zone 이동은 APPROACH에서 어깨→팔꿈치→손목으로 분배한다 | SOFT |
| N47 | RELEASE 가까이에서는 proximal 이동을 줄이고 technique에 맞는 distal/wrist 운동을 우선한다 | SOFT |
| N48 | palm normal과 wrist angle은 넓은 soft range 안에서 연속적이어야 한다 | SOFT/DIAG |
| N49 | event 사이에 어깨·팔꿈치가 불필요하게 왕복하거나 매번 초기 pose로 복귀하지 않는다 | SOFT |
| N50 | hard joint limit, bounded action, torque cap은 모든 phase와 technique에 적용한다 | HARD |
| N51 | 속도·가속도·jerk 비용은 phase·tempo·intensity로 gate하며 정상 attack을 정지시키지 않는다 | SOFT |
| N52 | 관절군별 실제 속도·가속도·토크·limit ratio 분포를 기록한다 | DIAG |

권장 움직임 우선순위는 상황 의존이다.

| 상황 | 주 운동 | 보조 운동 | 억제 대상 |
|---|---|---|---|
| finger single | 해당 손가락 | 작은 손목 안정화 | 어깨/팔꿈치 attack 스윙 |
| pick single/repeat | 손목·전완 | 손가락 grip 유지 | 매 note 어깨 왕복 |
| string leap | APPROACH의 손목·팔꿈치 | 필요한 어깨 이동 | release 순간 큰 proximal jerk |
| strum | 손목·전완 | span/intensity에 따른 팔꿈치 | 손가락 grip 붕괴 |
| multi_pluck | 활성 손가락들 | 안정된 손목 | 손 전체의 한 덩어리 스윙 |

## G. 위치·접촉·anchor

| ID | 규칙 | 수준 |
|---|---|---|
| N53 | 목표는 점이 아니라 실제 줄을 allowed y로 clip한 strike ribbon이다 | TASK/SOFT |
| N54 | preferred core 내부는 동등하게 허용하고 event마다 임의의 한 점으로 끌지 않는다 | SOFT |
| N55 | 연속 event의 zone 중심은 음색 지시가 없으면 부드럽게 유지한다 | PLAN/SOFT |
| N56 | 비목표 줄·다른 agent·soundboard/bridge의 우발 engagement를 분리 기록한다 | TASK/DIAG |
| N57 | anchor_mode 기본은 none이며 손바닥/소지를 항상 기타에 고정하지 않는다 | PLAN |
| N58 | forearm/palm-edge/pinky anchor는 technique annotation과 정상 접촉 분포가 있을 때만 허용한다 | PLAN/DIAG |
| N59 | 손·팔의 기타 관통, 초기 overlap, swept tunneling은 허용하지 않는다 | SAFETY |
| N60 | 손목 작업영역 이탈과 비유한 상태·속도 폭주는 지속 hysteresis 뒤 실패 종료한다 | SAFETY |

## H. source·setup·검출 보강

| ID | 규칙 | 수준 |
|---|---|---|
| N61 | 새 `notes.t_on`은 sound-onset 후보이며 자동으로 오른손 strike라고 간주하지 않는다 | HARD |
| N62 | tied/hammer/pull 등 attack=false onset에는 오른손 release/strike target을 만들지 않는다 | TASK |
| N63 | `requires_rh_attack=unknown`은 명시 profile/annotation 없이 학습에 넣지 않는다 | HARD |
| N64 | plectrum/fingerstyle/hybrid hand setup은 phrase 또는 episode 단위로 유지한다 | PLAN |
| N65 | plectrum/hybrid에서 pick을 쥔 thumb/index를 동시 finger target으로 쓰지 않는다 | HARD |
| N66 | pick을 잡고 놓는 setup 전환은 충분한 rest와 명시 transition plan 없이는 허용하지 않는다 | HARD/PLAN |
| N67 | 음악 event FSM, 정책 motor phase, `(agent,string)` detector state를 독립 상태로 보존한다 | HARD |
| N68 | 물리적으로 존재해 검사할 `present_agent_mask`와 이번 목표의 `target_agent_mask`를 분리한다 | HARD |
| N69 | detector는 goal 유무와 무관하게 모든 release/crossing을 emit하고 matcher만 event에 배정한다 | TASK |
| N70 | re-arm은 물리 separation·방향 이력·최소 시간으로만 정하며 새 goal 존재를 조건으로 삼지 않는다 | TASK |
| N71 | pick detector는 analytic swept interpolation으로 RELEASE를 만들고 정책 phase·re-arm state와 분리해 60 Hz에 집계한다 | HARD |
| N72 | source의 `either` 방향은 보존하되 plan은 profile과 sequence 문맥으로 실제 실행 방향을 해결한다 | PLAN |
| N73 | strum의 `audible_mask`, `traversal_mask`, `muted_mask`를 서로 다른 의미로 저장한다 | HARD |
| N74 | mute/span 정보 없는 비연속 target을 single-agent strum으로 추측하지 않는다 | HARD/PLAN |
| N75 | chord/strum은 target별 onset offset band를 가지며 전체 최대 span 하나로 미세시각을 대체하지 않는다 | PLAN/TASK |
| N76 | 각 줄의 tangent/across-string/soundboard-normal로 stroke frame을 만들고 approach/release/recovery 3D 영역을 둔다; load tube는 후속 진단이다 | TASK/DIAG |
| N77 | 넓은 allowed zone 안에서 `phrase_lane_y_m`를 유지하고 명시된 음색·주법 변화 때만 부드럽게 옮긴다 | PLAN/SOFT |
| N78 | 현재 event 외에 시간 horizon과 ordered next 3~5 events를 함께 보고 recovery를 다음 entry gate로 잇는다 | HARD |
| N79 | idle은 short/medium/long gap으로 나눠 oscillator 유지/hover-ready/relaxed park를 선택한다 | PLAN/SOFT |
| N80 | anchor는 `float/forearm_body/palm_bridge/pinky_body` 중 profile로 명시하고 접촉 whitelist를 mode별로 둔다 | PLAN/DIAG |

### phase별 3D 영역

기존 strike ribbon은 **release가 허용되는 줄 위 y 영역**이다. 자연스러운 운동 전체를 한 ribbon 거리로
유도하지 않고, 같은 줄의 local stroke frame에서 다음의 부피를 구분한다.

| 영역 | 목적 | 성공으로 세는가 |
|---|---|---|
| ready shell | 긴 쉼의 여러 편안한 자세 허용 | 아니오 |
| approach corridor / entry gate | 다음 lane으로 운반하고 올바른 pre-strike side·접근각 확보 | 아니오 |
| release ribbon | target string·agent·time·zone에서 one-shot emit | 예 |
| exit/recovery corridor | 즉시 역전·다른 줄 오타 없이 빠져나감 | 아니오 |
| contact/load diagnostic overlay | fingerstyle/물리 pick 후속 engagement 이력 | S0에서는 아니오 |

수치가 없는 gate는 hard rule이 아니다. 정상 합성 궤적과 GPU replay에서 agent/mode별 분포를 먼저
기록한 뒤 median/MAD와 분위수로 봉인한다.

## I. stroke mode별 release 규칙

| ID | 규칙 | 수준 |
|---|---|---|
| N81 | v1 finger single은 free stroke(tirando)를 기본으로 하며 release 뒤 손바닥 쪽 flexion으로 빠진다 | PLAN/SOFT |
| N82 | rest stroke(apoyando)는 `stroke_mode=rest`와 `allowed_landing_string`이 있을 때만 지원한다 | HARD |
| N83 | 허용된 rest-stroke landing은 FP가 아니며, 일반 free stroke에서 인접 줄에 기대는 것은 FP/진단이다 | TASK |
| N84 | same-direction pick 반복의 공중 return은 string field 밖 recovery corridor를 지나며 복귀 중 crossing을 금지한다 | TASK/SOFT |
| N85 | finger strum은 손가락 형상을 대체로 유지한 wrist/forearm sweep이며 줄마다 개별 finger flexion으로 꾸미지 않는다 | SOFT |

## J. timing·세기 규칙

- release 성공은 event별 early/late window 안에서만 한 번 인정한다.
- intensity source가 없으면 `0.5 neutral`을 provenance와 함께 사용한다. 오디오 amplitude를 검증 없이
  pick force로 직접 매핑하지 않는다.
- intensity는 attack 속도와 follow-through 범위를 조절하되, 더 깊은 기타 관통으로 보상하지 않는다.
- t_off는 울림 길이이며 mute annotation이 없는 한 오른손 contact 유지 목표가 아니다.
- strum의 전체 span과 줄별 offset은 BPM에 상관없이 실제 seconds/frame으로 함께 기록한다.

## K. 보상·검출 분리 규칙

| ID | 규칙 | 수준 |
|---|---|---|
| N86 | actor task objective는 target 수로 정규화한 event-level 신호를 기본으로 하고 6줄 채널은 진단/critic 후보로 둔다 | HARD/EXPERIMENT |
| N87 | 한 물리 crossing은 target-hit/wrong/extra 중 배타적으로 한 class에만 분류하되 raw acoustic와 plan adherence metric은 병기한다 | TASK |
| N88 | 접근 shaping은 potential difference를 우선하며 모든 auxiliary 누적량을 event 적분 return으로 core보다 작게 감사한다 | HARD |
| N89 | PPO 전 do-nothing/hover/jitter/전줄 sweep/zig-zag/조기타현/왕복 potential 등 adversarial policy의 return 우위를 검사한다 | HARD |
| N90 | 사람다움은 정확도·안전과 별도로 reference feature 분포와 blind rollout 감사가 통과될 때만 주장한다 | HARD |

## L. 자연스러움 보상 구조

보상은 다음 우선순위를 바꾸지 않는다.

1. **안전**: hard limit·관통·비유한 상태.
2. **event correctness**: string·agent·time·zone·direction·중복.
3. **phase completion**: approach/release/recover 연결.
4. **자연스러움**: 계층적 관절 사용·smoothness·grip·inactive finger·zone continuity.
5. **style prior**: technique에 맞는 사람 모션 분포.

긴 idle/READY frame의 상수 보상, 줄 위 hovering의 매-frame 보상, 완료 goal의 반복 보상은 금지한다.
자연스러움 비용은 핵심 event를 못 맞히면서도 얻을 수 있는 우회로가 되지 않도록 event/phase gate를 건다.

줄별 6채널은 wrong-string 원인을 찾는 진단과 multi-critic 후보로 유용하지만 actor 합산 정본으로 미리
확정하지 않는다. strum/chord 크기에 따라 최대 보상이 달라지거나 zig-zag partial이 합산 이득을 얻을 수
있기 때문이다. v1 primitive에서 다음을 ablation한다.

- event-normalized scalar actor objective + 6줄 diagnostic/critic.
- target 수로 정규화한 6채널 actor objective.

어느 경우에도 non-target FP가 비활성 채널에서 사라지지 않아야 하고 event당 최대 task return은 target
수와 무관해야 한다. 별도 `RH/hand` style/discriminator 채널을 쓰며 shared naturalness를 여섯 줄에
복제하지 않는다.

## M. 규칙만으로 충분한가

규칙은 잘못된 동작을 정의하고 학습을 올바른 해법 쪽으로 유도할 수 있지만, 사람이 실제로 쓰는 미세한
관절 상관관계 전체를 수기 임계값으로 보증할 수는 없다. 이 프로젝트에는 Xu의
`right_hand_motions.yaml`이 있고, 약 39.6 s scale clip과 2.32 s strum clip에 RH wrist/finger 모션이
포함된다. 원본 `cfg/right.py`도 goal reward weight 0.5와 별도 `RH/hand` discriminator를 함께 사용한다.
즉 기존 자연스러움은 task rule만의 결과가 아니다. 이 자료는 현재 style objective의 시작점으로 사용할
수 있다.

하나의 unconditional discriminator에 모든 주법을 섞지 않는다. 가능한 style objective는 최소
`hand_setup × agent × kind × direction × tempo/string-lane × 3-state motor phase`로 reference를 선택하거나
condition해야 한다. pick strum clip이 finger single의 자연스러움 정답이 되거나, 정확한 event보다
style score가 높은 정책이 선택되면 안 된다. task primitive가 안정된 뒤 style weight를 점진적으로 올리고
정확도 회귀가 생기면 이전 gate로 돌아간다.

제한도 명확하다.

- floating hand 자료라 전신 어깨·팔꿈치 자연스러움을 직접 감독하지 못한다.
- 짧은 strum과 scale 자료가 p/i/m/a fingerstyle 전체를 대표하지 않는다.
- scale/strum JSON에는 전용 pick-tip, 줄 crossing, acoustic onset, RELEASE 정답 라벨이 없다.
- legacy 27-action 정책은 현재 30-action 우팔 정책에 직접 로드할 수 없다.
- 기존 sit_guitar 영상의 팔·손 사용은 프로젝트 결정상 금지다.

따라서 pick/strum v1은 기존 RH prior를 retarget된 자세·속도·follow-through 분포의 참고로 사용할 수
있지만 detector threshold나 사건 정답으로 사용할 수는 없다. 상세 근거는
[기존 guitar pick 구현 분석](../90_references/LEGACY_GUITAR_PICK_ANALYSIS.md)에 있다. fingerstyle을 사람답다고 주장하려면 깨끗한
technique-specific 오른손 또는 전신 참조 분포가 추가로 필요하다. reference가 없는 technique은 규칙 기반
metric과 영상 감사까지는 가능해도 인간 분포 일치라고 부르지 않는다.

## N. 최종 평가 gate

정확도 외에 다음을 event·agent·technique별로 저장한다.

- 세 공개 phase별 체류시간, skipped/illegal 전이, release timing과 WAIT_REARM 체류시간.
- contact dwell과 virtual-load peak는 fingerstyle/물리 pick 진단이 활성일 때만 기록.
- approach 완료 시점, attack/release 속도·각도, along-string slip, 경로 효율·곡률·역전 횟수,
  follow-through 길이와 re-arm 시간/clearance.
- wrist/elbow/shoulder/finger의 tip-velocity 기여율, frequency-band power와 event별
  peak velocity/acceleration/jerk.
- palm orientation, inactive finger spread/curl, pick-grip relative pose.
- zone y 분포와 event 간 zone jump.
- multi-pluck release spread와 palm drift; strum inter-string interval CV·span·속도 profile·field 밖 반전 비율.
- gap 길이별 idle energy, ready-manifold distance, preposition lateness.
- wrong string/agent/zone, extra/duplicate, soundboard/bridge engagement.
- contact/torque/limit 비율과 관통·tunneling.
- style discriminator 점수는 technique별로 분리.
- target/actual/agent/phase overlay가 있는 deterministic rollout 영상.

정확도 gate를 통과하지 못한 정책의 낮은 jerk를 자연스러움 성공으로 인정하지 않는다. 반대로 정확도가
높아도 proximal jerk, 비활성 손가락 경직, 기타 기대기, 부자연스러운 매-note reset이 보이면 최종 통과가 아니다.
