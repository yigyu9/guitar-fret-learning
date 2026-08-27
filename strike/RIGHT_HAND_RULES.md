# 오른손 구현 규칙 — 현재 실행 정본

> 최종 갱신: 2026-08-10  
> 범위: geometry-less pick, 고정 string marker, single/strum downstroke, Isaac Gym  
> 이 문서는 **현재 실행 코드가 따라야 하는 최상위 규칙**이다. upstroke·양손 결합은
> [확장 규칙](RIGHT_HAND_EXTENSIONS.md), 기존 S/N 번호의 세부 근거는
> [물리 규칙 S1~S60](02_physical_control/rules.md)과
> [자연스러운 운동 N1~N90](02_physical_control/NATURAL_MOTION_RULES.md)을 따른다.

> 이 문서는 목표 계약도 함께 포함한다. 2026-08-03 현재 코드와 정확히 일치하는 범위 및 아직 진단·보류인
> 항목은 [코드 정리·검증 보고서](CODE_AUDIT_2026-08-03.md)를 함께 읽는다.

## 1. 먼저 고정하는 현재 범위

현재 환경에서 오른손은 박자에 맞춰 **단일 RELEASE 또는 여러 줄의 연속 RELEASE 제스처**를 만드는 실행 주체다.

| 항목 | 현재 계약 |
|---|---|
| 입력 | v1/v2 `[time, frame, string]`; v2는 동시 onset 허용, 원본 `time`이 정본 |
| 타현 주체 | 검지에 고정된 질량·충돌 없는 `RH:pick` 기준점 |
| 줄 | 탄성·접촉력이 없는 고정 유한 선분 6개 |
| 주법 | pick-only, single pick/strum, downstroke |
| 제어 | 오른쪽 어깨 3 + 팔꿈치 3 + 손목 3 + 손 21 = 30 DOF |
| 타현 판정 | 두 control frame 사이의 유한 swept crossing 직후 one-shot `RELEASE` |
| 공개 운동 phase | `READY → APPROACH → RELEASE_RECOVER` |
| 현재 제외 | up/alternate, fingerstyle, 물리 pick, 접촉력·음향, 왼손 결합 |

따라서 이 환경에서 “피크가 줄에 접촉하여 소리를 낸다”는 표현은 물리적 사실이 아니다. 현재 측정
가능한 것은 `RH:pick` 경로가 줄 선분을 언제·어디서·어느 방향으로 통과했는가이다.

## 2. 규칙 수준

- **MUST**: 입력·이벤트·안전 불변식. 위반하면 거부하거나 실패한다.
- **TASK**: 올바른 타현과 오타현을 나누는 판정 규칙.
- **SOFT**: 정확한 타현을 보존하면서 자연스러운 해법을 선호하는 작은 비용/보상.
- **DIAG**: 먼저 분포만 저장한다. 사람/실패 궤적이 분리된 뒤에만 gate로 승격한다.
- **PLAN**: 학습 전에 mapper/coordinator가 문맥으로 결정하고 runtime이 임의로 바꾸지 않는다.
- **SAFETY**: 음악적 실수와 별개인 관통·비유한·폭주 등의 물리 실패.
- **DEFER**: 현재 물리나 입력으로 측정할 수 없어 구현하지 않는다.

## 3. 용어

- **target time**: 입력 `events[].time`이 지정한 목표 음향 발생 시각. 별도 beat grid가 없으므로
  현재 v1에서는 이를 임의의 “정확한 박 위치”로 재해석하지 않는다.
- **release time**: swept interpolation으로 얻은 실제 유효 crossing의 subframe 시각.
- **strike**: 한 agent가 한 string에서 만든 one-shot RELEASE 하나.
- **stroke/strum**: 한 agent가 `traversal_mask`의 여러 줄을 down 방향으로 연속 통과한 RELEASE 묶음.
- **wrong release**: wrong string/direction/zone 또는 window 밖에서 발생한 유효 물리 crossing.
- **duplicate**: 같은 `(agent,string)`이 re-arm 전 다시 만든 crossing.
- **miss**: 허용창이 닫힐 때까지 target과 매칭된 RELEASE가 없음.
- **rest**: 현재 eligible target이 없는 구간. detector는 rest에도 계속 동작한다.

## 4. 입력과 좌표 규칙

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C01 | MUST | 사건은 유한하고 비음수인 `time`, 이에 가장 가까운 60 Hz `frame`, Isaac `string`을 가진다. |
| RH-C02 | MUST | `abs(frame - time×60) ≤ 0.5`이고 사건 시각과 frame은 엄격히 증가해야 한다. |
| RH-C03 | MUST | Isaac 줄 번호는 `0=high-e … 5=low-E`이며 source 경계에서 정확히 한 번만 뒤집는다. |
| RH-C04 | MUST | v1은 한 frame 한 target을 유지한다. v2의 동시·근접 이종 줄 onset은 임의 단현으로 줄이지 않고 strum으로 컴파일한다. |
| RH-C05 | TASK | `down`은 연주자 기준 6→1번 줄, Isaac `5→0`, 기타 로컬 `+x_g`다. |
| RH-C06 | MUST | 방향 필드가 없는 v1은 `down_only_v1`로 명시하고 up/alternate를 추측하지 않는다. |

## 5. 운동 phase와 detector state

정책에 보이는 운동 phase는 세 개만 사용한다.

```text
READY → APPROACH → RELEASE_RECOVER
  ↑                            │
  └─── 다음 사건 준비와 겹칠 수 있음 ─┘
```

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C07 | SOFT | `READY`는 한 pose가 아니라 다음 target의 진입측에 도달 가능한 편안한 준비 범위다. |
| RH-C08 | TASK | `APPROACH`는 목표 줄, down 진입측, 목표 lane과 body clearance를 향한다. |
| RH-C09 | TASK/SOFT | `RELEASE_RECOVER`는 one-shot crossing, 짧은 follow-through, separation과 다음 접근 연결을 포함한다. event index가 먼저 진행돼도 최소 follow-through 동안 직전 줄·lane·방향 문맥을 보존한다. |
| RH-C10 | MUST | `CONTACT`와 `LOAD`를 현재 공개 phase 또는 성공 조건으로 만들지 않는다. |
| RH-C11 | SOFT | 빠른 반복에서는 이전 recovery와 다음 approach가 겹칠 수 있으며 매 음 home pose로 복귀하지 않는다. |

중복 방지 detector는 정책 phase와 독립이다.

```text
ARMED → RELEASE pulse → WAIT_REARM → ARMED
```

정책 phase, 음악 event 상태, 줄별 detector state를 하나의 상태기로 합치지 않는다.

## 6. RELEASE와 매칭 규칙

프레임 `k-1→k`의 pick 경로와 목표 줄의 실제 선분을 기타 로컬 좌표에서 검사한다.

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C12 | TASK | 타현은 위치 겹침이나 접촉 상태가 아니라 유효한 swept crossing의 RELEASE pulse다. |
| RH-C13 | TASK | 교차 파라미터는 pick frame 경로 `0<t≤1`과 string 선분 `0≤s≤1` 안에 있어야 한다. |
| RH-C14 | TASK | 평행/정지 경로, 최소 displacement 미만, 최소 depth 미만, 최소 횡속도 미만은 RELEASE가 아니다. |
| RH-C15 | TASK | crossing 순간의 기타 로컬 x 속도 부호가 down 방향이어야 한다. |
| RH-C16 | MUST | detector는 현재 goal을 읽지 않고 모든 유효 RELEASE를 기록한다. |
| RH-C17 | MUST | matcher만 시간·줄·방향·zone을 이용해 RELEASE 하나를 target 하나에 배정한다. |
| RH-C18 | TASK | window 밖, wrong string/direction, rest 중 RELEASE는 성공이 아니라 false positive다. |
| RH-C19 | TASK | 한 물리 RELEASE는 target/wrong/extra 중 배타적으로 한 class만 갖는다. |
| RH-C20 | TASK | down-only v1의 같은 줄은 물리 separation과 최소 frame을 모두 만족해야 다시 ARMED가 된다. up/alternate에서는 직전 방향 이력도 추가한다. |
| RH-C21 | MUST | 새 target이 나타났다는 이유만으로 re-arm하지 않는다. |

### RH-C21A~F — goal compiler와 빠른 사건

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C21A | MUST | source `time`은 불변 정본으로 보존하고 easy/runtime time은 파생값으로만 만든다. |
| RH-C21B | TASK | 물리 최소 간격보다 가까운 서로 다른 줄 사건은 down 방향의 단일 strum으로 묶는다. |
| RH-C21C | TASK | strum 성공은 `traversal_mask` 전체의 올바른 방향 RELEASE가 모인 직후이며, 일부 통과는 아직 hit도 FP도 아니다. |
| RH-C21D | MUST | 가까운 같은 줄 재타현은 alternate/upstroke가 구현되기 전까지 지원되는 척하지 않고 fail-fast한다. |
| RH-C21E | TASK | 각 사건의 early/late 허용치는 전역 허용치와 인접 간격 45% 중 작은 값으로 정해 창 중첩을 막는다. |
| RH-C21F | MUST | A4 완료와 전체곡 평가는 `tempo_lambda=1`의 원래 시각에서만 인정한다. |

현재 초기값은 최소 depth `1 mm`, 최소 횡속도 `0.05 m/s`, re-arm 거리 `3 mm`, 대기 `2 frame`이다.
이 수치는 checkpoint 계약에 포함하지만 사람 궤적에 근거한 최종값은 아니므로 재보정 대상이다.

READY/APPROACH/RECOVER는 운동 계획 상태이지 RELEASE의 물리 정답 조건이 아니다. 계획 단계와 다른
순간에 발생한 RELEASE는 `release_phase_violation`으로 별도 진단하되, 그 이유만으로 올바른 타현을
false positive로 바꾸거나 timing 표본에서 지우지 않는다.

## 7. Strike 영역 규칙

타현 위치는 한 점이 아니라 실제 줄을 기타 로컬 y 구간으로 자른 ribbon이다.

- global allowed: `[-0.385, -0.255] m`
- global preferred: `[-0.355, -0.295] m`
- event lane 만점: 중심 `±6 mm`
- event lane 성공 경계: 중심 `±12.5 mm`

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C22 | MUST | 유한 줄 선분과 global allowed의 교집합만 release ribbon으로 사용한다. |
| RH-C23 | SOFT | preferred 내부 위치들은 동등하게 유효하며 고정 중앙 한 점을 정답으로 만들지 않는다. |
| RH-C24 | TASK | A4는 sampled lane outer band와 global allowed를 모두 만족해야 target hit다. |
| RH-C25 | MUST | 영역 밖 crossing도 detector record에서 삭제하지 않고 wrong release로 남긴다. |

A2/A3에서는 zone을 진단하고 A4부터 성공 판정에 사용한다. 영역 실패는 음악적 오류이지 그 자체로
안전 종료는 아니다.

## 8. 피크 자세와 자연스러운 운동

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C26 | SOFT | 초기 엄지·검지와 자유 손가락 자세는 `pick-grip-reference.json`의 21-DOF 목표를 따른다. |
| RH-C27 | DIAG | 실제 rigid pick이 없으므로 피크 면 각도·파지력·미끄러짐을 측정했다고 주장하지 않는다. |
| RH-C28 | SOFT | 단현 미세 attack은 손목·전완을 우선하고 어깨·팔꿈치는 줄 이동과 사전 배치에 주로 쓴다. |
| RH-C29 | SOFT | release 가까이에서는 큰 proximal jerk를 줄이되 손목만 고정적으로 쓰도록 강제하지 않는다. |
| RH-C30 | SOFT | release 직후 즉시 역전하지 않고 짧은 follow-through 뒤 separation을 만든다. |
| RH-C31 | DIAG | 연속 down의 string-field 밖 recovery corridor와 역방향 재타현율을 먼저 측정하고, GPU 궤적 근거 뒤 TASK/SOFT로 승격한다. |
| RH-C32 | DIAG | phase별 어깨/팔꿈치/손목 기여율, 속도, 가속도, jerk, path curvature와 action saturation을 기록한다. |
| RH-C33 | DIAG | 최대 depth와 최대 속도는 정상/실패 rollout 분포가 생기기 전까지 hard gate로 고정하지 않는다. |
| RH-C34 | SOFT | 속도·jerk 비용은 READY/APPROACH/RECOVER에 강하고 release 근처 정상 가속에는 완화한다. |

`w_shoulder > w_elbow > w_wrist` 같은 순서는 release 근처의 불필요한 운동 비용으로만 사용한다. 큰 줄
이동의 준비 과정까지 같은 가중치로 억제해 목표에 도달하지 못하게 만들면 안 된다.

현재 `audit_strike_motion.py`는 RELEASE depth/속도, tip speed, phase별 관절군 속도·가속도·jerk,
action saturation, recovery corridor·역방향 RELEASE와 오른팔/손 관통을 한 JSON에 저장한다. 이 값은
DIAG이며 성공/실패 정책 분포가 분리되기 전에는 C33·C34·C37의 hard threshold가 아니다.

## 9. 안전, 보상과 성공 조건

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C35 | MUST | 모든 제어 관절은 bounded action, hard joint limit과 finite-state 계약을 지킨다. |
| RH-C36 | SAFETY | 손·팔이 기타를 관통해 crossing을 만드는 shortcut, 비유한 상태와 속도 폭주는 실패다. |
| RH-C37 | DIAG | strike 전용 관통·작업영역 proxy는 정상 접촉과 분리 보정되기 전까지 진단으로 둔다. |
| RH-C38 | DEFER | pick-string 접촉력의 최소/최대값은 현재 marker 환경에서 보상이나 성공 조건으로 사용하지 않는다. |
| RH-C39 | MUST | event completion과 core RELEASE 보상은 one-shot이며 완료 뒤 매 frame 반복하지 않는다. |
| RH-C40 | MUST | wrong/extra/duplicate/miss 비용은 grip·smoothness 보조 보상으로 상쇄할 수 없어야 한다. |
| RH-C41 | SOFT | approach shaping은 PPO gamma와 같은 discount의 potential difference로 구성해 hover·왕복의 누적 이득을 막는다. |
| RH-C42 | MUST | do-nothing, hover, jitter, 전줄 sweep, 왕복 crossing이 목표 수행보다 높은 return을 얻지 못해야 한다. |

현재 단현 사건의 핵심 성공은 다음과 같다.

```text
StrikeSuccess =
    matched_RELEASE
  ∧ correct_string
  ∧ down_direction
  ∧ inside_time_window
  ∧ required_zone_gate
  ∧ no_safety_failure
```

회복은 RELEASE 순간의 음 정답과 분리해 episode 품질로 평가한다.

```text
StrikeEpisodeSuccess = StrikeSuccess ∧ valid_follow_through ∧ rearm_or_safe_exit
```

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C43 | MUST | `ChordReady`는 독립 오른손 `StrikeSuccess`에 넣지 않는다. |
| RH-C44 | MUST | timing p95에는 허용창 밖의 올바른 target attempt도 포함한다. |
| RH-C45 | MUST | precision, recall, F1, wrong rate, timing, zone과 safety를 서로 숨기지 않고 병기한다. |
| RH-C46 | DIAG | 자연스러움은 정확도·안전과 별도 feature/영상 gate로 평가한다. |
| RH-C47 | MUST | reference가 없으면 “human-like”가 아니라 “운동학적으로 타당한 virtual strike”까지만 주장한다. |

## 10. 현재 학습 커리큘럼

```text
A0_PICK_GRIP
→ A1_TIP_READY
→ A2_FREE_CROSSING
→ A3_TIMED_CROSSING (100 → 67 → 50 ms)
→ A4_ZONE_CONTROL
```

| ID | 수준 | 규칙 |
|---|---|---|
| RH-C48 | MUST | 각 단계는 이전 단계의 자세·ready·crossing 정확도를 계속 유지한다. |
| RH-C49 | MUST | 최소 iteration 이후 완료 episode의 성능 gate를 연속 통과해야 승급한다. |
| RH-C50 | MUST | 최대 iteration에 도달해도 자동 승급하지 않고 `stalled`로 남긴다. |

A4는 실제 곡의 `[time,frame,string]` source 사건을 사용한다. v2의 동시 onset과 물리 최소 간격보다
가까운 이종 줄 사건은 goal compiler가 down-strum으로 묶고, 가까운 동줄 재타현은 명시적으로 거부한다.

## 11. 양손 통합과의 경계

현재 strike 환경은 왼손 상태를 보지 않는다. 오른손 detector를 `FretReady`로 끄면 왼손 미준비 중의
오타현과 반복 crossing이 숨으므로 금지한다. 향후 full task는 아래 세 결과를 따로 보존한다.

```text
RightHandResult          # 오른손 줄·방향·시간·영역
LeftHandReadyResult      # 목표 음의 압현·해제·안정화
CombinedPerformance     # 두 결과와 공통 event 정렬의 결합
```

양손 규칙과 strum 입력은 [RIGHT_HAND_EXTENSIONS.md](RIGHT_HAND_EXTENSIONS.md)에 정의한다.

## 12. 구현 연결과 필수 검증

| 규칙 묶음 | 담당 코드 | 필수 증거 |
|---|---|---|
| RH-C01~06 입력·좌표 | `env/strike_goals.py`, `tools/build_strike_training_data.py` | closed schema, time/frame, string 변환, 동시 onset 거부 |
| RH-C07~11 phase | `env/tasks/task_strike.py` | phase 전이, 직전 event follow-through 문맥 보존 |
| RH-C12~21 검출·re-arm | `env/strike_detector.py`, `env/strike_events.py` | finite segment, subframe, 방향/depth/speed, goal-independent detector |
| RH-C22~25 zone | `task_strike.py`, `rewards/strike.py` | allowed/preferred/lane 경계와 wrong release 보존 |
| RH-C26~42 운동·보상·안전 | `rewards/strike.py`, `env/base.py`, strike audit 도구 | 보조 return 상한, 관절군/jerk/depth 분포, adversarial policy |
| RH-C43~50 평가·curriculum | `learning/strike_curriculum.py`, `learning/strike_evaluation.py` | 완료 episode gate, timing tail, stalled, checkpoint 복원 |

PPO 장시간 실행 전에 최소 다음 반례를 통과해야 한다.

1. 무한 string 연장선만 가로지르는 경로는 RELEASE가 아니다.
2. rest 중 crossing과 re-arm 후 반복 crossing은 모두 FP로 남는다.
3. 줄 위 hover와 왕복 jitter가 target RELEASE보다 높은 return을 얻지 못한다.
4. release 직후 다음 target이 바뀌어도 직전 줄의 follow-through가 유지된다.
5. recovery 중 반대 방향 crossing은 다음 upstroke로 오인되지 않는다.
6. allowed 밖 crossing도 detector에서는 사라지지 않는다.

## 13. 다음 작업 순서

현재 schema를 바꾸기 전에 다음 진단을 우선한다.

1. 직전 event의 줄·lane·방향을 회복 종료까지 보존하는지 확인.
2. 최대 crossing depth, 최대 tip speed와 body-dive 분포 저장.
3. 연속 down을 위한 string-field 밖 recovery corridor 진단.
4. phase별 어깨·팔꿈치·손목 기여율과 jerk/reversal 저장.
5. strike 전용 기타 관통 monitor 보정.

그 뒤 `audible/traversal/muted/protected` mask와 ordered matcher를 추가하고, 마지막에 공통 event ID와
`FretReady`를 가진 full-task coordinator를 구현한다. 물리 pick과 접촉력은 이 순서 뒤에도 별도 V2다.
