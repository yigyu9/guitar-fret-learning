# 오른손 strike 하위 상세 규칙 S1~S60

> 현재 최상위 실행 정본은 [`RIGHT_HAND_RULES.md`](../RIGHT_HAND_RULES.md)다. 이 문서는 goal·검출·
> 확장 주법의 세부 invariant와 과거 ID 추적을 유지한다. 상위 정본과 충돌하면 상위 정본을 따른다.
> `docs/plans/task_strike_design.md`의 Xu 이식 초안을 검토해
> 이벤트 의미, 타현 주체(agent), 유한 선분 판정, debounce, 명시적 timing window, 동시 손가락 타현,
> 스트럼 순서, 평가 gate를 보강했다.
> 최종 갱신: 2026-07-23. 구현 상태는 [status.md](status.md)에서 관리한다.

입력 해석의 세부 결정은 [StrikeMapper C1~C48](../01_goal_contract/MAPPER_RULES.md), phase·주법·협응의
세부 운동 계약은 [자연스러운 운동 N1~N90](NATURAL_MOTION_RULES.md)을 따른다.

## 용어와 상태

- **target crossing**: eligible event가 요구한 `(string,agent)`에 매칭된 유효 타현.
- **wrong crossing**: 목표가 아닌 줄 또는 잘못된 방향·순서의 교차.
- **wrong agent**: 올바른 줄을 지정되지 않은 피크/손가락으로 타현.
- **extra crossing**: 필요한 crossing을 이미 채운 뒤의 추가 교차.
- **duplicate crossing**: re-arm 없이 같은 `(agent,string)`에서 다시 검출된 교차.
- **miss**: event window가 닫힐 때까지 필요한 줄을 채우지 못함.
- **rest**: 현재 eligible event가 없는 구간. 미래 event 접근은 허용한다.

## 규칙 마스터 표

| ID | 규칙 | 강제 수준 | 담당 예정 |
|---|---|---|---|
| S1 | `notes.t_on`은 불변 sound-onset 후보이고 `presses[].strikes`는 fretted-note 감사 projection이다 | 확정 | source builder |
| S2 | loader가 시간·줄·agent·surface·ID·주법·곡 지문을 fail-fast 검사한다 | 확정 | `goals.py` |
| S3 | 줄 index는 Isaac `0=high-e, 5=low-E`로 한 번만 변환한다 | 확정 | builder/loader |
| S4 | source 방향 없음은 `either`로 보존하고 versioned mapper가 phrase 문맥으로 실제 plan 방향을 해결한다 | 확정 | mapper |
| S5 | 부분 chord의 빈 줄을 자동 span 목표로 채우지 않는다 | 확정 | builder |
| S6 | agent마다 detector를 선택한다: pick point / fingertip pad capsule | 확정 | `rewards/strike.py` |
| S7 | pick은 swept point와 **유한** string의 `t/s/depth` 교차로 판정한다 | 확정, depth 실측 | reward |
| S8 | K6/fingerstyle V2의 손가락은 `*3→*_top` tip pad의 contact→load→release로 판정한다 | 후속 확정, pad 수치 실측 | reward |
| S9 | 교차는 줄뿐 아니라 지정 agent까지 맞아야 target hit다 | 확정 | task/reward |
| S10 | `(agent,string)`별 물리 separation·방향 이력·최소 간격 re-arm으로 떨림 중복을 막는다 | 확정, 수치 실측 | detector |
| S11 | 한 frame의 복수 crossing은 궤적 파라미터 순서로 정렬한다 | 확정 | reward |
| S12 | single은 지정 agent가 지정 줄을 한 번 치면 완료된다 | 확정 | task |
| S13 | multi_pluck은 서로 다른 agent의 target을 같은 window에 채운다 | 확정 | task |
| S14 | strum은 한 agent가 target 줄을 한 방향·제한 시간 안에 채운다 | 확정 | task |
| S15 | event마다 조기/지각 허용창을 명시한다 | 확정, 기본값 후보 | goals/task |
| S16 | window 밖 crossing은 성공이 아니며 false positive다 | 확정 | task/metrics |
| S17 | miss는 window close에서 한 번만 발생한다 | 확정 | task |
| S18 | detector는 goal 없이도 모든 crossing을 내고, 새 event가 있을 때만 matcher가 이를 성공에 배정한다 | 확정 | detector/task |
| S19 | 미래 목표 거리·시간 shaping은 주되 조기 crossing은 보상하지 않는다 | 확정 | reward |
| S20 | actor task는 event별·target수 정규화를 기본으로 하고 6줄 채널 방식은 primitive ablation 후 봉인한다 | 실험 전 결정 | task/PPO |
| S21 | event 완성·보조항은 one-shot이며 event 적분 return이 core를 압도하지 않게 감사한다 | 확정, 가중치 실험 | reward |
| S22 | idle은 gap 길이별 ready manifold를 쓰고 recovery를 다음 event entry gate와 연결한다 | 확정 | mapper/reward |
| S23 | 속도·가속도·jerk 규제는 phase·tempo·technique별 free-band 비용으로 쓴다 | 확정, 분포 실측 | motion reward |
| S24 | 전역 hard joint limit과 bounded action 계약을 지킨다 | base 구현 상속 | `base.py` |
| S25 | 손목 작업영역 이탈은 지속 hysteresis 뒤 실패 종료한다; 3 frame은 K2 전 초기 후보다 | 원칙 확정, 박스·지속시간 실측 | task |
| S26 | 손·팔의 기타 관통과 정상 marker crossing을 분리한다 | 확정, 기하 확장 필요 | safety/task |
| S27 | pick grip은 접촉력이 아닌 상대 자세로 우선 진단한다 | 진단 우선 | metrics |
| S28 | soundboard/bridge 기대기와 비정상 지지는 힘 분포를 먼저 진단한다 | 진단 우선 | metrics |
| S29 | full에서도 독립 RH timing 성공을 유지하고, 왼손 chord-ready 동시성은 별도 combined-audio 채널로 평가한다 | full 전용 보류 | `task_full.py` |
| S30 | 곡별 coverage→integration→full-song 커리큘럼을 사용한다 | 확정 | curriculum |
| S31 | attack intent의 `unknown`과 plan agent의 `unspecified`를 각각 명시 profile/annotation으로 해결한다 | 확정 | intent/mapper |
| S32 | 엄지·i/m/a의 관례적 줄 역할은 prior이지 hard constraint가 아니다 | 확정 | curriculum |
| S33 | 소지는 명시 annotation이 있을 때만 target agent로 사용한다 | 확정 | builder |
| S34 | 물리 `present_agent_mask`와 목표 `target_agent_mask`를 분리하고, 존재하는 비활성 agent crossing을 FP로 기록한다 | 확정 | detector/metrics |
| S35 | hybrid는 pick grip을 유지한 pick+m/a/(명시 c) multi_pluck이며 thumb/index finger target을 동시에 허용하지 않는다 | 확정 | mapper/loader |
| S36 | nail/flesh는 보존하되 nail geometry 전에는 물리적으로 구분하지 않고, palm mute·slap/tap·rasgueado는 일반 타현으로 위장하지 않는다 | 부분 보류 | 후속 |
| S37 | strike 목표 위치는 한 점이 아니라 실제 줄을 허용 y 구간으로 자른 ribbon이다 | 구조 확정·경계 후보 | reward |
| S38 | 넓은 allowed 안의 preferred core는 만점, 양쪽 edge는 smooth quality를 사용한다 | 약한 shaping 후보 | reward |
| S39 | 입력은 `SourceNote→StrikeIntent→StrikePlan→RuntimeGoal` 네 층이고 raw를 정책에 직접 넣지 않는다 | 확정 | goal pipeline |
| S40 | attack=false onset에는 target을 만들지 않고 unknown은 학습 전에 provenance와 함께 해결한다 | 확정 | intent loader |
| S41 | `plectrum/fingerstyle/hybrid` hand setup은 phrase/episode 단위로 고정한다 | 확정 | mapper |
| S42 | regrip 모델 전에는 충분한 rest·transition plan 없는 setup 변경을 거부한다 | 확정 | mapper/loader |
| S43 | 음악 event FSM, 정책 motor phase, `(agent,string)` detector state를 서로 독립적으로 관리한다 | 확정 | task/detector |
| S44 | pick S0의 공개 정책 phase는 `READY→APPROACH→RELEASE_RECOVER` 3단계다. RELEASE pulse 검출과 detector re-arm은 이 phase와 독립이다 | 확정 | task/obs |
| S45 | pick S0는 유효 swept crossing에서만 one-shot RELEASE pulse를 emit하며 CONTACT/LOAD 완료를 요구하지 않는다 | 확정 | detector |
| S46 | ribbon 외에 stroke-local ready/approach/release/recovery 3D 영역을 두고 contact/load tube는 후속 진단으로 둔다 | 구조 확정·수치 실측 | geometry |
| S47 | pick RELEASE crossing은 analytic swept interpolation으로 검출해 60 Hz에 집계하고, contact/load 복원은 fingerstyle V2에서 검증한다 | 확정 | detector |
| S48 | strum은 `audible_mask/traversal_mask/muted_mask`를 분리한다 | 확정 | goal/task |
| S49 | mute/span 정보 없는 비연속 target은 한 agent strum으로 추측하지 않는다 | 확정 | mapper/loader |
| S50 | chord/strum은 target별 onset offset band와 전체 span을 함께 가진다 | 확정·수치 실측 | goal/task |
| S51 | mapper는 넓은 allowed zone 안에 phrase lane을 만들고 시간 horizon+next 3~5 event로 coarticulation한다 | 확정 | mapper/obs |
| S52 | v1 finger pluck은 free stroke이며 rest stroke는 landing string이 명시된 별도 mode로만 허용한다 | 확정 | mapper/detector |
| S53 | detector는 task target을 보지 않고 물리 사건을 생성하며 unmatched crossing은 항상 FP다 | 확정 | detector/matcher |
| S54 | 한 crossing의 오류 class는 배타적으로 하나지만 acoustic correctness와 inferred-plan adherence는 별도 metric이다 | 확정 | task/metrics |
| S55 | dense shaping은 potential difference를 우선하고 frame 가중치가 아닌 event 누적량으로 reward dominance를 감사한다 | 확정 | reward audit |
| S56 | 보조 보상과 style prior는 정확한 event보다 높은 return을 만들 수 없다 | 확정 | reward audit |
| S57 | PPO 전에 do-nothing/hover/jitter/전줄 sweep/zig-zag/조기타현/왕복 등 adversarial policy를 전수 감사한다 | 확정 | tests/audit |
| S58 | Xu RH motion prior는 pick/strum 시작점일 뿐 전신 팔·fingerstyle 인간 분포의 증거가 아니다 | 확정 | style learning |
| S59 | 자연스러움은 phase·tip path·관절군 기여·strum 간격·idle·inactive finger 분포로 평가한다 | 확정·참조 분포 대기 | metrics |
| S60 | reference가 없는 주법은 `kinematically plausible virtual strike`까지만 주장하고 human-like 통과를 보류한다 | 확정 | final gate |

영역 수치와 근거·시각화는 [strike-zone.md](strike-zone.md)를 따른다.
`allowed y=[-0.385,-0.255]m`, `preferred y=[-0.355,-0.295]m`는 현재 구현값이다.
A2/A3에서는 진단만 하고, A4에서는 global allowed와 sampled lane의 `±12.5 mm`를 목표 성공
gate로 사용한다. 영역 이탈만으로 safety 종료하지는 않는다.

## M1. 주체별 기하 판정 계약

방향 정본은 `down=6번줄→1번줄=Isaac 5→0=+x_g`,
`up=1번줄→6번줄=Isaac 0→5=-x_g`다. 단현은 한 줄만으로 순서를 알 수 없으므로 crossing 순간의
픽 기타 로컬 x 속도 부호로 판정한다. deadband 안의 거의 수직인 움직임은 방향 지정 event에 매칭하지 않는다.

### Pick

프레임 `k-1→k`에서 기타 로컬 pick 위치를 `p0,p1`, 줄 양 끝을 `a_i,b_i`라 한다. xy 투영에서

```text
p(t) = p0 + t(p1-p0),  0 < t ≤ 1
q(s) = a  + s(b-a),    0 ≤ s ≤ 1
```

을 만족하는 `(t,s)`를 구한다. 분모가 epsilon보다 작으면 평행으로 제외한다. 교차점의 z가 해당 줄 z에서
유효 깊이만큼 안쪽이고, pick displacement가 최소값보다 클 때만 후보다. 기존 참조처럼 `t`만 검사하면
string의 무한 연장선 오검출이 생기므로 반드시 `s`도 검사한다.

현재 pick과 줄은 탄성이 없는 marker이므로 S0 detector는 CONTACT/LOAD를 재구성하거나 성공 조건으로
요구하지 않는다. 위 유한 swept crossing이 방향·최소 횡속도·깊이를 만족하고 detector가
`ARMED`이면 RELEASE pulse 하나를 내고 즉시 `WAIT_REARM`으로 전이한다. zone quality는 항상 record에
넣되 K2 보정 전에는 crossing 자체를 제거하지 않는다. signed gap, contact-band 진입,
가상 load는 선택적 진단값이다. 단순 위치 겹침이나 band 내부 정지는 crossing이 아니므로 타현도 아니다.

detector는 goal과 무관하게 최소한 다음 release record를 만든다.

```text
agent, string, control_frame, subframe_t, direction,
crossing_position_g, depth, across_speed, zone_quality
```

같은 `(agent,string)`은 물리 separation·방향 이력·최소 시간이 충족된 뒤에만 다시 `ARMED`가 된다.

초기 최소 depth 후보는 참조와 같은 1 mm지만 확정값이 아니다. 과도한 최대 depth는 K2 전까지
진단으로만 기록한다. asset의 시각 string 반경 0.9 mm,
`RH:pick` marker offset, 60 Hz swept trajectory를 함께 렌더해 true/false 사례를 만든 뒤 정한다.
현재/직전 좌표는 둘 다 **그 프레임의 기타 pose에 대응하는 로컬 frame**으로 변환해 G1/G2의 움직이는
기타에서도 좌표계가 섞이지 않게 한다.

### Finger pad — K6/fingerstyle V2 후속 계약

`thumb/index/middle/ring/pinky`는 각 `RH:*3→*_top` 중심선의 tip 쪽 유효 구간을 capsule pad로
근사한다. 이전·현재 capsule 사이를 시간 보간해 finite string segment와의 최소 표면 간격을 구한다.
단순 근접을 타현으로 세지 않도록 상태를 `armed→contact→load→release`로 둔다.

- `contact`: pad가 주체별 hit corridor에 들어오고 최소 횡방향 속도를 가짐. 아직 onset이 아님.
- `load`: signed gap/penetration proxy가 한 방향으로 증가하며 hover와 구분됨.
- `release`: load peak 뒤 pad가 반대쪽 또는 exit gate로 빠져나감. 이때 하나의 crossing을 emit.
- 같은 corridor 안에 머무르거나 눌러 기대는 상태는 추가 crossing이 아님.
- distal 전체가 아니라 tip pad만 성공 후보이며 다른 마디·손바닥은 비정상 접촉 진단 대상.

손가락별 pad 반경과 hit/release 임계는 mesh 크기 및 합성 궤적으로 따로 보정한다. pick의 1 mm depth를
엄지·검지에 그대로 적용하지 않는다.

## M2. 이벤트 매칭과 타이밍

detector와 matcher를 분리한다. detector는 현재 goal과 무관하게 모든 agent-string release/crossing을
시간순으로 emit한다. matcher만 eligible event의 줄·agent·방향·순서·window를 보고 crossing 하나를
목표 하나에 배정한다. 배정되지 않은 crossing은 rest에서도 false positive다. detector re-arm에
“새 goal 존재”를 넣어 오타를 숨기지 않는다.

줄과 시각은 맞지만 mapper가 추론한 agent/방향만 다르면 raw acoustic hit와 plan violation을 동시에
기록한다. annotation이 없는 inferred plan을 유일한 인간 정답처럼 평가하지 않는다. 한 물리 사건을
wrong-agent, wrong-string, extra로 여러 번 중복 감점하지 않고 우선순위가 있는 배타 class 하나로 분류한다.
event window가 겹치더라도 빠른 restrike를 합치지 않는다. midpoint clipping과 monotone earliest-event
matching 중 하나 및 wrong-agent/wrong-string/extra 오류 precedence는 K-1에서 fixture와 함께
하나로 봉인한다. 그 전에는 matcher 구현을 시작하지 않으며, 선택한 규칙으로 일대일 대응이 유일하지
않은 plan은 loader가 거부한다.

초기 timing 후보는 single/multi_pluck `[-2,+3] frame`, strum 첫 release도 같은 창, 전체 span
`≤6 frame`이다. 이와 별도로 각 target은 `onset_offset_s` 또는 offset band를 가진다. 모든 target을 한
control frame에 폭주해도 max span만 맞으면 성공하는 규칙은 금지한다.
이는 구현을 시작하기 위한 값이며 성공한 rollout의 onset error 분포와 오디오 허용오차를 보고 봉인한다.
miss를 goal on 상태로 무기한 끌지 않는다. 지각 허용창이 닫히면 반드시 missed로 소모한다.

## M3. 보상 계약

core는 target 수와 무관하게 최대값이 같은 event 단위로 계산한다.

```text
r_event = normalized one-shot target hits + small one-shot completion
          - exclusive FP/FN/plan violations
          + potential-based approach shaping
          + bounded phase/technique naturalness cost
```

- hit가 가장 크고 단 한 번 발생한다.
- pending 접근은 `gamma*Phi(next)-Phi(now)` 형태의 potential difference를 우선한다. 정지 hover와
  왕복 이동이 양의 누적 보상이 되지 않는지 reset/event 전환까지 단위검사한다.
- longitudinal position quality는 preferred=1, allowed edge→preferred raised-cosine, outside=0 후보다.
- miss/wrong-string/wrong-agent/extra는 서로 다른 metric과 감점을 가진다.
- 6줄 모두 무관한 rest frame에 큰 상수 보상을 주지 않는다. 긴 무음이 학습을 지배하기 때문이다.
- event completion, 준비, jerk/energy 등 모든 auxiliary는 **event 동안 적분한 절대 return**으로 core보다
  작은지 scripted rollout에서 감사한다. 프레임별 5% 같은 규칙은 긴 event에서 core를 초과할 수 있다.
- chord target 수, rest 길이, timestep subdivision이 달라도 event당 최대 task return은 거의 불변이어야 한다.

줄별 6채널은 진단과 critic 후보로 유지하되 actor 정본으로 미리 확정하지 않는다. event-normalized scalar와
target 수 정규화 6채널을 A1 primitive에서 ablation한다. 어느 방식에서도 non-target FP가 비활성 채널에서
사라지거나 strum이 single보다 최대 6배 큰 signal을 얻으면 실패다.

Xu의 영구 `pluck_correct` 상태와 무목표 보너스는 episode 길이와 무음 비율에 민감하므로 현재 정본으로
채택하지 않는다. 정확도는 보상 누적 상태가 아니라 event confusion matrix로 계산한다.

## M4. 관측 계약

actor가 최소한 알아야 할 것은 다음과 같다.

- 우측 controlled DOF position/velocity와 `prev_action`.
- 기타 로컬 `R_Wrist`, `RH:pick`, 다섯 `RH:*_top` 위치·속도.
- 현재 event의 줄별 target agent, remaining mask, kind, direction, time-to-open/close.
- phrase hand setup, `present_agent_mask`, target별 onset offset, audible/traversal/muted mask, phrase lane.
- 0.10 s와 0.25 s 미래 snapshot 및 ordered next 3~5 event의 target-agent·방향·시간.
- event FSM과 독립인 `READY/APPROACH/RELEASE_RECOVER` 3단계 정책 phase.
- 각 활성 `(agent,string)`의 `ARMED/WAIT_REARM` detector state와 현재 frame RELEASE pulse.
- signed gap/contact/load proxy는 pick S0의 선택적 진단값이며 actor 필수 입력이 아니다.
- 정규화 곡 진행률.

critic에만 event 결과 누계나 exact window phase를 추가할 수 있지만 actor가 행동에 필요한 timing을
볼 수 없게 만들면 안 된다. actor/critic 필드 순서와 dimension은 테스트와 checkpoint contract에
봉인한다.

## M5. 안전과 자연스러움

- S25 손목 박스는 fret의 왼손 박스를 복사하지 않고 우손 초기 자세·6줄 reach·정상 strum 궤적으로
  다시 산출한다. 경계 밖 3 frame 연속은 초기 후보이며 K2 전에는 진단만 하고, 정상/오류 분포가
  분리된 뒤 checkpoint에 봉인한 지속시간으로 종료한다.
- S26은 fret R14의 neck/body/top analytical proxy를 오른팔·우손 표본으로 확장한다. string marker의
  의도된 교차는 검사 대상이 아니다.
- `G:pluck_range`는 줄 자체가 아니라 넓은 box rigid body다. 그 net force는 접촉 부위와 상대를
  특정하지 못하므로 즉시 `-1` 보상으로 쓰지 않는다.
- self-collision OFF에서는 thumb/index contact force 기반 pick-grip 규칙이 성립하지 않는다.
  pick은 index2에 고정된 kinematic marker이고 별도 질량·방향이 없다. 엄지-검지 상대 거리,
  손가락 관절 범위, marker trajectory를 진단하며 물리 pick 도입은 보류한다.
- legacy 오른손은 free wrist 6+손 21의 27-action 모델이라 현재 어깨 이하 우팔/손 30-action checkpoint에 직접
  로드할 수 없다. 궤적 teacher·손 자세 seed로 쓸 때도 retarget/FK 검증을 먼저 한다. 상세 근거는
  [기존 guitar pick 구현 분석](../90_references/LEGACY_GUITAR_PICK_ANALYSIS.md)을 따른다.
- fingerstyle에서는 활성 fingertip pad만 성공 후보로 삼고, 비활성 손가락 crossing과 손바닥/다른 마디의
  string corridor 진입을 따로 기록한다. 엄지=p, 검지=i, 중지=m, 약지=a 관례는 초기 curriculum에
  활용할 수 있지만 goal의 명시 agent를 덮어쓰지 않는다.

## M6. 성공 판정

학습 보상과 최종 통과는 분리한다. 전체곡 deterministic 평가에서 다음을 모두 요구한다.

1. target crossing precision≥0.99, recall≥0.99, F1≥0.99.
2. wrong-string rate≤0.01, wrong-agent rate≤0.01, extra/duplicate rate≤0.01.
3. event completion≥0.99; single·multi_pluck·strum·재타현 및 agent별로 따로 보고한다.
4. onset absolute error p95≤50 ms, mean signed error도 함께 기록한다.
5. 방향이 명시된 event direction accuracy≥0.99, strum order accuracy≥0.99.
6. 전체곡 완주 100%, 실패 종료·비유한 상태·속도 폭주·심각한 관통 0.
7. reset 직후 overlap과 swept tunneling 0.
8. rollout 영상에서 목표 marker, 실제 crossing, miss/wrong reason을 프레임 단위로 대조한다.

사람에 가까운 운동의 통과조건은 위 정확도 gate와 별도다. technique·agent·tempo별로 최소 다음 분포를
held-out reference와 비교한다.

- 네 motor phase duration과 skipped/illegal transition, release timing, WAIT_REARM duration.
- contact dwell과 virtual-load peak는 fingerstyle 또는 해당 실험 진단을 활성화했을 때만 기록.
- tip attack/release 속도·각도, 경로 효율·곡률·역전 횟수, follow-through·re-arm 거리/시간.
- shoulder/elbow/wrist/finger의 tip-velocity 기여율과 proximal high-frequency power.
- palm drift, inactive finger curl/spread/crossing, pick grip relative pose.
- multi-pluck release spread, strum inter-string interval CV·span·속도 profile·field 밖 반전 비율.
- gap 길이별 idle energy, phrase lane jump, action clamp·torque saturation, 기타 support/관통.

Xu의 RH clip은 pick/strum prior 초기화에는 쓸 수 있지만 floating hand 자료라 전신 팔과 p/i/m/a
fingerstyle 자연스러움을 보증하지 않는다. 해당 reference와 blind 영상 평가가 없으면 최종 표현은
“안전하고 운동학적으로 타당한 virtual strike”로 제한한다.

수치 1~5는 첫 정본 후보다. 데이터 timestamp 자체의 오차가 더 크다는 증거가 나오면 기준을 바꾸되,
평가 후 결과에 맞춰 몰래 낮추지 않고 문서·checkpoint contract 버전을 올린다.
