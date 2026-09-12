# 4. Strike-v2: 오른손 타현 기술

## 4.1 Strike이 해결하는 문제

Strike는 오른손 pick 또는 strum으로 기타 줄을 실제로 가로질러 소리를 내는 기술을 학습하는 **오른손 skill prior**입니다.

Strike가 책임지는 것:

- 오른쪽 어깨·팔꿈치·손목의 접근과 회복
- pick/grip의 안정성
- single pick과 multi-string strum의 방향·순서
- 타현 전 준비와 타현 후 recovery

Strike가 책임지지 않는 것:

- 왼손이 올바른 프렛을 눌렀는지
- 전체 몸과 기타가 안정적인지
- event를 실행할지 기다릴지에 대한 최종 permission

## 4.2 StrikeEvent와 입력

오프라인 compiler는 음표 목록을 오른손이 실행할 타현 사건으로 묶습니다. 사건에는 보통 다음이 들어갑니다.

- `event_id`, score time
- gesture: `single_pick` 또는 `strum`
- traversal mask: 실제로 지나가야 하는 줄
- audible mask: 그 순간 소리가 나야 하는 줄
- string offsets와 sweep duration
- 물리적 진행 방향
- approach lead, timing window, recovery deadline
- 다음 event ID와 rearm 문맥

traversal과 audible은 다를 수 있습니다. 예를 들어 strum이 여러 줄을 지나가지만 일부 줄은 mute/protected 상태일 수 있습니다. 따라서 “소리가 나야 하는 줄”과 “pick이 통과해야 하는 줄”을 하나의 mask로 합치면 안 됩니다.

## 4.3 Action 30차원

```text
R_Shoulder  3
R_Elbow     3
R_Wrist     3
RH hand    21
----------------
합계         30
```

single picking과 strumming은 별도 정책으로 분리하지 않고 하나의 Strike policy가 gesture와 target geometry를 입력으로 받는 방향입니다. grip의 기준값은 deterministic controller가 제공하고, policy는 필요한 동작을 제안합니다.

## 4.4 Observation 303차원 계약

| 블록 | 크기 | 의미 |
|---|---:|---|
| `O_proprio` | 60 | 오른팔·오른손 관절 상태와 속도 |
| `O_arm_anchor` | 18 | 몸·기타 기준의 팔 anchor |
| `O_hand_geometry` | 30 | 손·pick 위치와 방향 |
| `O_grip_safety` | 7 | grip과 접촉/안전 상태 |
| `O_current_event` | 32 | 현재 pick/strum 목표 |
| `O_target_geometry` | 25 | string zone과 접근 geometry |
| `O_lookahead` | 52 | 다음 타현과 recovery 문맥 |
| `O_phase_detector` | 29 | phase와 detector 상태 |
| `O_recovery` | 18 | 이전 crossing 후 회복 정보 |
| `O_synchronizer` | 2 | source policy용 동기화 context |
| `O_history` | 30 | 이전 action/상태 history |
| **합계** | **303** | `strike.observation.v2` |

## 4.5 모델 구조

```text
11개 observation block
  → block encoder들
  → concat 552D
  → MLP 512 → 256
      ├─ Actor: 30D mean + learned log_std
      └─ Critic: scalar value 1D
```

현재 architecture 이름은 `strike.block_encoder_mlp.v1`입니다. Strike은 한 scalar reward/value를 사용합니다. Fret과 Strike의 observation block 수가 같아 보여도 각 block의 의미와 크기가 다르므로 checkpoint를 서로 바꿔 쓸 수 없습니다.

## 4.6 실제 타현 detector

Strike 성공은 actor의 action이나 손 위치만으로 판정하지 않습니다. 한 physics step 안에서 pick point가 움직인 선분을 swept point로 계산하고, 기타의 각 줄도 유한한 segment로 계산합니다.

```text
이전 pick 위치 ───────── 현재 pick 위치
                   ╲
                    ╲ 올바른 줄 segment와 교차?
```

판정에 포함되는 요소:

- pick point가 실제 줄 segment를 통과했는가
- 기타 기준 depth가 충분한가
- 진행 방향이 event 방향과 맞는가
- 속도가 최소 기준을 넘는가
- 현재 timing window 안인가
- 같은 crossing을 중복 기록하지 않았는가
- rearm 조건을 만족한 뒤 다음 타현을 허용했는가

따라서 “손이 줄 근처에 있다”는 것은 ready에 가까운 상태일 뿐, 타현 성공 자체가 아닙니다. detector는 index finger에 붙은 `RH:pick` marker를 기준으로 하며, pick은 일반적인 질량 중심점과 다릅니다.

## 4.7 Phase machine

Strike의 실행 흐름은 대략 다음과 같습니다.

```text
READY → APPROACH → RELEASE/STRIKE → RECOVER
```

- `READY`: 다음 event를 받을 수 있는 상태
- `APPROACH`: 목표 string zone으로 접근
- `RELEASE/STRIKE`: 방향·속도·깊이를 갖고 줄을 통과
- `RECOVER`: 이전 event의 손상을 줄이고 다음 event에 재진입

premature release, wrong crossing, miss, recovery 지연은 별도 penalty 또는 metric으로 기록합니다.

## 4.8 String zone과 방향

Strike은 줄 번호만 보는 것이 아니라 기타 기준 zone과 접근 방향을 봅니다. 허용 zone, 선호 zone, lane center, core/allowed width, 최소 crossing depth/speed, rearm frame이 detector 설정으로 정의됩니다.

이 값들은 “아무 데서나 줄을 치면 성공”하지 않도록 하는 물리적 기준입니다. 설정을 바꿔 성공률이 올라도, 기존 checkpoint와 detector contract가 달라진 것이므로 같은 실험으로 비교하면 안 됩니다.

## 4.9 Curriculum

현재 curriculum은 acquisition 단계와 strum/song 통합 단계로 나뉩니다.

```text
A0_PICK_GRIP
 → A1_TIP_READY
 → A2_SINGLE_CROSSING
 → A3_TIMED_SINGLE
 → A4_STRUM_CONTEXT_RECOVERY
 → S0_TWO_STRING_STRUM
 → S1_STRUM_SPAN
 → S2_TIMED_STRUM
 → S3_SONG_INTEGRATION
```

처음에는 grip과 pick tip을 안정화하고, 이후 단일 crossing, timing, recovery, 여러 줄 strum, 곡 통합으로 올라갑니다. 단계가 어려워져도 observation/action shape는 유지하고, event sampling·reward mask·timing gate를 바꿉니다.

## 4.10 보상과 평가

Strike reward는 다음을 함께 반영합니다.

- grip 유지
- target zone 접근
- ready 품질
- 실제 crossing
- timing 품질
- premature/early crossing penalty
- strum traversal 진행률
- terminal physical completion
- recovery 품질
- wrong direction, miss, zone 이탈

평가 때는 다음을 분리해 기록해야 합니다.

1. 목표 위치에 도착했는가?
2. 올바른 방향으로 crossing했는가?
3. 필요한 모든 줄을 순서대로 지났는가?
4. timing window 안에서 발생했는가?
5. 다음 event 전에 recovery했는가?

## 4.11 코드 읽기 지도

- contract와 block 순서: `../../tab2body/strike_v2_contract.py`
- 모델: `../../tab2body/learning/strike_v2_model.py`
- task: `../../tab2body/env/tasks/task_strike.py`
- crossing detector: `../../tab2body/env/strike_detector.py`
- event reward/logic: `../../tab2body/env/strike_events.py`
- 설정: `../../tab2body/strike_cfg.py`
- 학습 진입점: `../../tab2body/train_strike.py`
- 상위 개념: `../../master_plan/04_strike.md`

## 4.12 현재 상태와 주의점

Strike-v2의 303D contract, detector, curriculum, full-song 평가 기록이 있습니다. 그러나 모든 song bundle이 정식 source로 승급된 것은 아닙니다. 일부 곡은 strike audit가 PASS이고, 일부는 방향·입력·alternate restrike 등의 이유로 AMBIGUOUS 또는 unsupported로 남아 있을 수 있습니다.

새 곡에서 성공률이 낮을 때 먼저 policy를 의심하기 전에 `strike_plan.json`, traversal/audible mask, source/Isaac 줄 변환, detector 설정, rearm 조건을 확인합니다.

