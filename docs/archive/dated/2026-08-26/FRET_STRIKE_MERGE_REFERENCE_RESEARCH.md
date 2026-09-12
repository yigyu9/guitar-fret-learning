# Fret·Strike 병합을 위한 두 선행 연구의 양손 결합 방식 분석

> **상태: RELATED-WORK REFERENCE.** AdaptNet 설명은 선행연구의 구조이며 현재 프로젝트의
> Synchronizer 구현이 아니다. 현재 선택은 [`master_plan/05_synchronizer.md`](../../master_plan/05_synchronizer.md)를 따른다.

> 작성 목적: 독립적으로 학습한 왼손 fret 정책과 오른손 strike 정책을 하나의 연주 정책으로 합치기 전에, 참고 연구 두 편이 실제로 무엇을 어떻게 결합했는지 논문과 공개 코드를 함께 확인한다.
>
> 조사 대상:
> 1. Chaoyi Luo et al., **Learning to Play Guitar with Robotic Hands** (이하 **GPS**, CGF/SCA 2024)
> 2. Pei Xu and Ruocheng Wang, **Synchronize Dual Hands for Physics-Based Dexterous Guitar Playing** (이하 **SDH**, SIGGRAPH Asia 2024)

---

두 연구는 모두 왼손과 오른손을 먼저 분리하지만, “병합”의 의미가 완전히 다르다.

| 구분 | GPS | SDH |
|---|---|---|
| 왼손 | DroQ로 학습한 프레팅 정책 | PPO로 학습한 범용 프레팅 정책 |
| 오른손 | 학습하지 않은 규칙 기반 궤적 + IK | PPO로 학습한 범용 피킹 정책 |
| 병합 시 추가 학습 | 없음 | 있음. 곡별 synchronizer 학습 |
| 정책 수준 병합 | 없음. 행동 공간은 끝까지 왼손만 | 있음. 두 잠재공간에 학습된 잔차를 넣고 54차원 공동 행동 출력 |
| 시간축 병합 | 같은 탭에서 만든 `goalstate`와 `pluckstate`를 같은 tick으로 재생 | 같은 곡에서 왼손·오른손 goal window를 함께 만들고 중앙 환경에서 학습 |
| 협력 신호 | 기본값에서는 없음. 오른손은 탭 시각을 그대로 따름 | 왼손 압현 준비 상태가 오른손 피킹 보상에 직접 들어감 |
| 물리 결합 | 두 손과 기타가 같은 MuJoCo 장면에 존재 | 두 손과 기타가 같은 Isaac Gym 환경에 존재 |
| 최종 산출물 | 왼손 정책 rollout + 오른손 IK 애니메이션 + 합성음 | 단일 joint stochastic policy `π(aL,aR | oL,oR)` |

따라서 GPS를 “두 학습 정책을 합친 선례”로 해석하면 안 된다. GPS는 **공유 악보 시계 위에서 학습된 왼손과 스크립트 오른손을 조립**한다. 반면 SDH는 **학습된 두 단일손 정책을 보존하면서, 두 손의 잠재표현을 읽는 작은 적응 모듈을 추가 학습**한다.

우리의 fret·strike가 둘 다 학습 정책이라는 점에서는 SDH가 직접적인 병합 레퍼런스다. GPS는 초기 통합 단계에서 필요한 **공통 이벤트 시계, 발음 시점의 왼손 상태 조회, 정책 간 최소 결합**의 참고 사례로 가치가 있다.

---

## 2. 이 문서에서 “병합”을 나누는 다섯 층

양손 병합을 단순히 action 두 개를 이어 붙이는 일로 보면 중요한 차이를 놓친다. 두 연구를 다음 다섯 층으로 나눠 분석한다.

1. **악보/goal 병합**: 같은 노트가 왼손 압현과 오른손 탄현 목표로 어떻게 분해되는가.
2. **시간 병합**: 두 손이 어느 시계를 공유하고, 이벤트가 어느 tick에서 발생하는가.
3. **환경/상태 병합**: 두 손이 같은 물리 장면에 놓이는가, 서로의 상태를 관측하는가.
4. **정책/행동 병합**: 두 정책을 그대로 병렬 실행하는가, 공동 모듈을 추가하는가, 처음부터 하나로 재학습하는가.
5. **협력 보상/출력 병합**: “왼손 준비 후 오른손 탄현”을 무엇으로 강제하고, 최종 음을 어떻게 결정하는가.

---

## 3. GPS: 학습 정책 병합이 아니라 공유 타임라인 조립

### 3.1 논문의 3단 분해

GPS 논문은 기타 연주를 다음처럼 명시적으로 분리한다.

1. 탭에서 왼손 운지를 휴리스틱으로 정한다.
2. 정해진 운지를 따라 왼손 프레팅 정책만 DroQ로 학습한다.
3. 탭의 탄현 시각에 맞춰 오른손 손끝 경로를 만들고 IK로 관절 자세를 계산한다.

즉 오른손에는 체크포인트도, actor도, 오른손 reward도 없다. 논문이 말하는 coordination은 두 정책의 협력 학습이 아니라 **동일한 tablature schedule을 따르는 왼손 제어와 오른손 모션 계획의 시간 정렬**이다.

### 3.2 하나의 탭에서 두 goal 배열을 동시에 만든다

`Tablature.notesToState()`는 각 노트를 두 목록에 동시에 기록한다.

- 프렛이 있는 노트는 `keys[fret*6 + string]`에 `(time, duration, finger)`로 들어간다.
- 쉼표가 아닌 모든 줄 이벤트는 `plucks[string]`에 `(time, duration, fret, finger)`로 들어간다.

그 후 [`music/goal.py`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/music/goal.py#L12-L57)가 같은 `control_timestep` 격자에서 세 배열을 만든다.

```text
goalstate[t][120]  = 각 프렛 센서의 active 여부와 담당 손가락
pluckstate[t][6]   = 해당 tick에 각 줄을 탄현해야 하는지
stringstate[t][6]  = 각 줄의 목표 프렛과 담당 손가락
```

`goalstate`는 노트 지속 구간 전체에서 켜지지만, `pluckstate`는 각 노트의 `starttick` 한 프레임에서만 1이다. 이것이 GPS의 가장 중요한 공통 계약이다. 왼손과 오른손은 별도 파일이나 별도 clock을 쓰지 않고 **한 탭을 한 번 이산화한 결과**를 소비한다.

### 3.3 두 손은 처음부터 같은 MuJoCo 장면에 붙어 있다

`GuitarTask` 생성자는 기타 arena에 오른손과 왼손을 모두 attach한다. 따라서 렌더링과 qpos는 같은 physics instance에 있다. 그러나 같은 장면에 있다는 사실이 공동 제어를 뜻하지는 않는다.

공개 코드의 실제 action 경로는 다음과 같다.

- [`before_step()`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L611-L625)는 action 전체를 왼손에만 적용한다.
- [`action_spec()`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L708-L714)도 왼손 spec만 반환한다.
- 오른손/왼손 action을 둘로 나누는 코드는 주석 처리되어 있다.
- 에너지 보상도 왼손 actuator power만 합산한다.

따라서 학습 중 MDP는 사실상 왼손 단일 에이전트다. 오른손 모델이 scene graph에 존재해도 정책 학습에는 참여하지 않는다.

### 3.4 테스트 시 오른손을 붙이는 실행 순서

오른손은 `test`가 참일 때만 [`after_step()`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L633-L672)에서 갱신된다.

한 control step의 주요 순서는 다음과 같다.

```text
왼손 actor action 적용
  → MuJoCo step
  → tick 증가
  → 현재 진행 중인 오른손 손끝 궤적의 다음 점으로 IK
  → 미래 pluckstate를 보고 새 탄현 궤적 예약
  → 현재 왼손 접촉으로 줄별 최고 프렛 갱신
  → 화면/음원 상태 갱신
```

탄현 궤적은 줄에 따라 고정 배정된다.

- 엄지: 4·5·6번줄, 직선형 경로
- 검지·중지·약지: 3·2·1번줄, 타원형 경로
- 소지: 탄현에 사용하지 않음

[`_create_trajactory()`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L231-L304)가 손끝의 월드 좌표 경로를 만들고, [`_update_right_hand_pos()`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L343-L400)가 `qpos_from_site_pose()`를 호출해 해당 손가락 joint의 IK를 푼다. 손목 두 joint는 매 step 고정값으로 되돌린다.

### 3.5 양손 결과가 실제로 만나는 곳은 발음 계산이다

GPS에서 두 손의 결과가 의미적으로 합쳐지는 지점은 actor 내부가 아니라 음원 후처리다.

1. `_update_music_play()`가 현재 활성화된 120개 프렛 센서를 훑는다.
2. 각 줄에서 눌린 프렛 중 가장 높은 번호를 `_string_max_pos[6]`에 저장한다.
3. 오른손 탄현 경로가 발음 지점에 도달하면 `_string_play(string)`이 실행된다.
4. 해당 줄의 `string_max_pos`를 표준 튜닝에 더해 음높이를 결정한다.
5. Karplus–Strong 기반 합성음을 재생하거나 영상용 note event를 기록한다.

이를 식으로 쓰면 GPS의 최종 음 event는 다음과 같다.

```text
note(t, string) = pitch(open_string[string],
                        max_active_fret_from_left_hand(t, string))
```

즉 오른손은 **언제·어느 줄을 발음할지**, 왼손은 **그 순간 어느 음높이가 날지**를 결정한다. 이것이 GPS에서 가장 실질적인 양손 결과 병합이다.

### 3.6 “왼손이 준비될 때까지 대기”는 기본 병합 규칙이 아니다

코드에는 `wait` 분기가 있어 목표 프렛과 현재 최고 활성 프렛이 일치할 때 소리를 내도록 기다리는 경로가 있다. 하지만 모듈 전역 기본값은 `wait=0`이다. 기본 실행에서는 오른손이 왼손 성공 여부와 무관하게 예약된 궤적을 따라가며, 왼손이 늦으면 잘못된 프렛 또는 개방현 음이 날 수 있다.

따라서 GPS의 기본 동기화는 다음과 같이 이해해야 한다.

- 강한 동기화: **탭 tick 공유**
- 약한 물리 결합: **발음 순간 왼손 센서 상태 조회**
- 없는 것: 오른손이 왼손 state를 관측하는 정책, 공동 reward, 두 손 공동 update

### 3.7 코드에서 확인되는 타이밍 주의점

공개 커밋은 `_ANIMATION_NUM=10`, control rate 30 Hz다. 그런데 `after_step()`은 `pluckstate[tick+3]`를 발견하면 길이 10의 궤적을 만들고, 기본 `wait=0`에서 궤적 index가 10에 도달할 때 `_string_play()`를 호출한다.

코드만 문자 그대로 추적하면 다음 현상이 가능하다.

- 목표 탄현 tick보다 3프레임 전에 경로를 예약한다.
- 실제 발음 호출은 경로 시작 후 10 control step째다.
- 결과적으로 목표보다 약 7프레임, 30 Hz 기준 약 0.23초 늦을 가능성이 있다.

이는 논문에 설명되지 않은 구현상 의문점이다. composer callback 순서나 영상 후처리에서 추가 보정되는지 공개 코드만으로 확인되지 않으므로, “확정 버그”가 아니라 **이식하면 안 되는 매직 넘버/검증 필요 지점**으로 보는 것이 안전하다.

### 3.8 GPS 병합 방식의 장단점

장점:

- 이미 학습된 왼손 정책을 수정하지 않고 즉시 전체 연주를 렌더링할 수 있다.
- 공통 탭 clock과 발음 계약이 단순해 디버깅이 쉽다.
- 오른손 학습 실패가 왼손 정책을 망가뜨리지 않는다.
- 양손 공동 시뮬레이션 학습 비용이 없다.

한계:

- 오른손이 학습 정책이 아니므로 우리의 strike 체크포인트 병합 문제를 직접 해결하지 않는다.
- 왼손 준비 상태가 오른손 행동을 수정하지 않는다.
- 양손 collision, 전신 균형, 상체 관절 경쟁을 공동 최적화하지 않는다.
- 최종 품질이 hand-authored trajectory와 시간 상수에 강하게 의존한다.
- 공동 성공 지표가 아니라 주로 왼손 프렛 precision/recall/F1을 평가한다.

---

## 4. SDH: 잠재공간 잔차를 학습하는 진짜 두 정책 병합

### 4.1 1단계: 두 단일손 정책을 독립 학습

SDH는 먼저 두 정책을 별도 환경에서 학습한다.

```text
πL(aL_t | oL_t): 왼손 프렛 압현
πR(aR_t | oR_t): 오른손 스트링 피킹
```

두 정책 모두 27차원 action을 내며 PPO와 모방학습/태스크 보상을 사용한다. 다만 목적 구조는 다르다.

- 왼손: 6개 줄별 프레팅 목적 + 손목/엄지 모방 + 나머지 손가락 모방 = 8개 value 목적
- 오른손: 피킹 목적 + 오른손 전체 모방 = 2개 value 목적

왼손은 500개 곡에서 뽑은 note와 pitch/tempo 증강으로 범용 정책을 만들고, 오른손은 절차적으로 생성한 피킹 패턴으로 범용 정책을 만든다. 이 단계에서는 각 손이 상대 손의 상태를 보지 않는다.

### 4.2 2단계: 두 정책을 중앙 환경으로 옮긴다

특정 곡을 동기화할 때 [`ICCGANTwoHands`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/env.py#L2089-L2201)가 양손과 기타를 한 Isaac Gym 환경에 둔다.

중앙 환경은 다음을 결합한다.

- pose state: `s = {sL, sR}`
- goal: `g = {gL, gR+}`
- action: `a = [aL, aR]`, 총 54차원
- task reward: `[왼손 줄 6채널, 오른손 피킹 1채널]`, 총 7채널
- value output: 왼손 모방 2채널까지 더해 총 9개 critic head
- termination: 왼손 종료 조건 OR 오른손 종료 조건

중요한 점은 중앙 환경으로 옮긴 뒤에도 사전학습 actor를 통째로 fine-tune하지 않는다는 것이다. 두 actor의 기술을 보존하고 그 사이에 `AdaptNet` synchronizer를 넣는다.

### 4.3 goal 병합: 한 곡을 왼손용·오른손용으로 다시 분해

[`update_goal_tensor()`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/env.py#L2102-L2147)는 하나의 곡 cursor와 timer를 공유하면서 두 goal window를 함께 shift한다.

왼손 goal:

- 각 줄의 프렛 번호를 유지한다.
- pitch augmentation이 있으면 프렛 번호에 반영한다.
- 5개 future note와 각 note timer를 사용한다.

오른손 goal:

- 프렛 번호는 버리고 각 줄의 pick 여부만 bool로 만든다.
- hammer-on, pull-off, tied note처럼 왼손만으로 소리를 바꾸는 effect note는 제거한다.
- 스트럼 대상의 최상단 줄과 최하단 줄 사이의 빈 줄을 채워 연속 스트럼 구간으로 만든다.
- 이미 올바르게 피킹한 줄의 상태 `pluck_correct[6]`를 critic/goal 관측에 덧붙인다.

최종 goal 관측 크기는 코드 기본값에서 다음과 같다.

```text
left window:  (6 strings + timer) × 5 = 35
right window: (6 strings + timer) × 5 = 35
pluck_correct:                          6
total:                                 76
```

두 손이 같은 timer를 공유한다는 점이 중요하다. SDH도 GPS처럼 공통 score clock을 먼저 확립하지만, 그 위에 상태 기반 협력 학습을 추가한다.

### 4.4 정책 병합의 핵심: AdaptNet synchronizer

논문의 식 (1)–(2)는 다음과 같다.

```text
zL_t = EφL(oL_t) + ΔzL_t
zR_t = EφR(oR_t) + ΔzR_t

[ΔzL_t, ΔzR_t]
  = Sθ(Concat(EθL(oL_t), EθR(oR_t)))
```

여기서:

- `EφL`, `EφR`: 사전학습 단일손 정책의 원래 state/goal encoder
- `EθL`, `EθR`: 각 원래 encoder를 복제해 만든 학습 가능한 encoder
- `Sθ`: 양손의 복제 encoder 출력을 함께 읽어 두 latent offset을 출력하는 MLP
- `ΔzL`, `ΔzR`: 원래 단일손 latent에 더하는 잔차

공개 코드 [`models.py:AdaptNet`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/models.py#L288-L378)의 forward 흐름은 더 구체적이다.

```text
1. 결합 state를 왼손 state와 오른손 state로 split
2. trainable-copy left encoder  → s1
3. trainable-copy right encoder → s2
4. concat(s1, s2) → synchronizer MLP
5. MLP 출력을 ΔzL, ΔzR로 split
6. frozen original left latent  + ΔzL → 기존 left MLP/action head
7. frozen original right latent + ΔzR → 기존 right MLP/action head
8. 두 Normal 분포의 μ와 σ를 concat → 54차원 joint Normal
```

따라서 한 손의 offset도 자기 관측만으로 결정되지 않는다. `Sθ` 입력에 양손 encoded state가 모두 들어가므로, 오른손 상태가 왼손 latent를 바꿀 수 있고 왼손 상태가 오른손 latent를 바꿀 수 있다. 이것이 단순 action concatenation과 다른 핵심이다.

### 4.5 0 초기화가 기존 기술을 보존한다

Synchronizer MLP의 마지막 linear layer는 weight와 bias를 모두 0으로 초기화한다. 학습 시작 시에는:

```text
ΔzL = 0
ΔzR = 0
```

이므로 joint actor의 첫 행동 분포는 두 사전학습 actor를 단순 병렬 실행한 것과 같다. 이후 PPO가 협력이 필요한 만큼만 latent를 움직인다.

이 설계의 효과는 다음과 같다.

- 랜덤한 54차원 행동에서 시작하지 않는다.
- 단일손에서 이미 배운 프레팅·피킹 기술을 초기 rollout부터 사용한다.
- 협력 학습은 “기술 재학습”보다 “타이밍·자세의 조건부 수정”에 집중한다.
- 문제가 생겼을 때 offset norm을 관찰해 단일손 기반 동작과 동기화 수정량을 분리해서 볼 수 있다.

### 4.6 보상 병합은 스칼라 합이 아니라 7개 task 채널 유지

두 손 환경의 task reward는 [`reward()`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/env.py#L2185-L2201)에서 다음처럼 만들어진다.

```text
rew_l = left_reward(...)          # N × 6, 줄별 프렛 보상
rew_r = right_reward(..., ready)  # N × 1, 피킹 보상
rew   = concat(rew_l, rew_r)      # N × 7
```

동기화 cfg의 task weight는 처음에 다음과 같다.

```text
[0.075 × 6, 0.5]
```

`main.py`가 단일손 학습 때의 총 가중 규모를 유지하기 위해 전체 `env.reward_weights`를 2배 한다. 왼손 모방 판별자 두 개는 유지되고 오른손 모방 판별자는 cfg에서 주석 처리된다. 결과적으로 joint value network는 다음 9개 head를 가진다.

```text
[LH wrist/thumb imitation,
 LH fingers imitation,
 fret string 1, ..., fret string 6,
 right-hand picking]
```

각 head는 별도 GAE와 advantage 정규화를 거친 뒤 weight가 곱해진다. 즉 피킹 보상의 스케일이 프렛 보상을 압도하거나 그 반대가 되는 것을 단일 스칼라 합보다 완화한다.

### 4.7 협력 조건: 왼손 상태로 오른손 reward를 gate한다

논문은 모든 줄이 기대 압현 상태가 아니면 오른손에게 “아직 피킹 target이 없다”고 간주한다고 설명한다. 그 결과 오른손은 왼손이 준비되기 전에 피킹해서 보상을 얻을 수 없다.

공개 코드는 줄별 `ready`를 계산한다.

```text
pressed = (
    current_press == expected_positive_fret
    OR left_goal_is_dont_care
    OR this_string_is_not_a_right_hand_target
)

timer = (current_note_remaining <= 3) OR (elapsed_in_note >= 5)
ready = pressed OR timer
```

그리고 `ready`를 오른손 `_reward()`에 넘긴다. 이 구조가 양손 사이의 직접 협력 신호다.

다만 코드의 `timer` 예외는 논문보다 느슨하다. 논문만 따르면 모든 목표 줄의 압현 준비가 우선이지만, 코드는 노트가 임박했거나 이미 일정 시간이 지났으면 압현 불일치에도 오른손 target을 다시 허용한다. 이는 deadlock과 영원한 대기를 피하고 피킹 학습 신호를 살리기 위한 실용적 완화로 추정되지만, 저자가 그 의도를 명시하지는 않았다.

### 4.8 최종 action과 checkpoint의 형태

[`main.py`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/main.py#L456-L529)는 `--left`와 `--right` 체크포인트에서 각각 actor 구조와 normalization 통계를 복원한 뒤:

```python
model.actor = AdaptNet(model, left_policy, right_policy)
```

로 joint actor를 교체한다. 최종 actor는 다음을 함께 checkpoint에 가진다.

- 왼손 base actor (`meta1`)
- 오른손 base actor (`meta2`)
- 왼손/오른손 trainable encoder copy
- synchronizer MLP
- 양손 결합 관측 normalizer
- 공동 critic과 PopArt 통계

추론 시에는 별도 actor 두 개를 외부 scheduler가 호출하는 것이 아니다. 한 `AdaptNet` forward가 결합 관측을 받고 왼손·오른손 action 분포를 동시에 반환한다.

### 4.9 논문과 공개 코드의 동결 범위 차이

논문은 사전학습 정책의 “모든 파라미터를 lock”하고 synchronizer 관련 `θ`만 최적화한다고 서술한다. 그러나 공개 코드의 freeze loop는 이름에 `sigma`가 들어간 파라미터를 건너뛴다.

```python
for n, p in meta1.named_parameters():
    if "sigma" in n: continue
    p.requires_grad = False
```

오른손도 동일하다. 따라서 base actor의 `log_sigma` head는 optimizer에 포함되고 학습 가능하다. 평균 행동을 만드는 encoder/MLP/`mu`는 동결되지만 탐색 분산은 변할 수 있다.

정확한 표현은 다음과 같다.

- 논문 의도: base policy 완전 동결 + synchronizer만 학습
- 공개 코드: base policy의 deterministic mean 경로 동결 + synchronizer와 두 `log_sigma` head 학습

우리 구현에서 완전 동결을 계약으로 삼을 경우 `log_sigma`까지 명시적으로 freeze하거나, 반대로 분산 적응을 허용한다면 checkpoint contract와 문서에 예외를 명시해야 한다.

### 4.10 왜 단순 병렬 실행만으로 부족했는가

SDH의 단일손 정책은 개별 평가에서 왼손 F1 약 0.8, 오른손 평균 F1 0.9 이상을 보였다. 그러나 그대로 같은 환경에 놓으면 피킹 순간과 압현 준비 순간이 어긋나 joint F1이 크게 떨어졌다.

동기화 후 25개 곡에서 평균 개선율은 약 193%, 최대 657%였고 대부분의 곡이 거의 100%에 가까운 joint accuracy를 보였다. 부록에서는 단일손 정확도가 거의 완벽한 정책도 함께 놓으면 약 20% 성능 하락이 생긴다고 보고한다. 즉 SDH의 이득은 단순 곡별 fine-tuning만이 아니라 실제 양손 temporal coordination에서 온다.

직접 54차원 joint policy를 처음부터 학습한 ablation은 훨씬 느렸다. 두 손 환경 시뮬레이션 자체도 단일손보다 약 40% 느리고, 초기 샘플이 협력이 아니라 기본기 탐색에 소비되기 때문이다. 단일손 학습은 약 `8×10^8` samples와 3–4일, synchronizer는 곡 난이도에 따라 약 `1×10^7–8×10^7` samples와 1.5–12시간을 사용했다고 부록이 보고한다.

---

## 5. 두 연구의 병합 구조를 같은 그림으로 비교

### 5.1 GPS

```text
                        ┌─ goalstate ──> left DroQ actor ──> left qpos/contact ─┐
tablature ─> tick grid ─┤                                                       ├─> pitch/audio/video
                        └─ pluckstate ─> scripted path + IK ──> right qpos/event ┘
```

양손 사이에 학습 가능한 화살표가 없다. 둘은 공통 입력과 최종 발음 계산에서만 만난다.

### 5.2 SDH

```text
left obs/goal  ─> frozen left latent  ─┐       ┌─ +ΔzL ─> frozen left head  ─> aL
                                      ├─ Sθ ──┤
right obs/goal ─> frozen right latent ─┘       └─ +ΔzR ─> frozen right head ─> aR
                       ▲                                  │
                       └──── joint state/reward PPO ──────┘
```

실제 코드에서는 `Sθ` 앞에 원래 encoder를 복제한 trainable encoder 쌍이 하나 더 있다. 양손 task reward와 왼손 imitation reward가 `Sθ`의 업데이트를 결정한다.

---

## 6. 우리 fret·strike 병합에 직접 연결되는 설계 원칙

이 절은 새 아키텍처를 확정하는 결정문이 아니라, 두 연구에서 근거가 확인된 병합 원칙을 추린 것이다.

### 6.1 가장 먼저 고정해야 할 것은 actor가 아니라 공통 이벤트 계약이다

두 연구 모두 정책 결합보다 먼저 하나의 악보 시계를 만든다. 우리도 다음 항목을 joint training 전에 단일 계약으로 고정해야 한다.

- note/event ID
- onset과 duration의 기준 시계
- 왼손이 유지해야 할 프렛/손가락 목표
- 오른손이 통과해야 할 줄과 방향
- hammer-on/pull-off/tie처럼 strike가 없어야 하는 이벤트
- chord/strum cluster의 원자성
- 발음 판정 시점과 허용 window

현재 song bundle의 `fret_training.json`, `strike_training.json`, `strike_plan.json`이 서로 독립적인 tick 반올림을 하면 synchronizer가 정책 오차가 아니라 데이터 clock 오차를 학습하게 된다.

### 6.2 첫 통합 baseline은 GPS형 병렬 실행이어야 한다

추가 학습 전에 다음 baseline을 먼저 측정하는 것이 좋다.

```text
frozen fret policy + frozen strike policy
+ 같은 simulator
+ 같은 score/event cursor
+ action concat 또는 전신 joint별 action ownership merge
+ 추가 residual 없음
```

이 baseline은 SDH의 0-initialized synchronizer가 학습 첫 step에서 구현하는 상태와 같다. 측정해야 할 핵심은 단일손 F1이 아니라:

- strike 순간 target fret correctness
- fret-ready time과 strike crossing time의 signed offset
- onset joint precision/recall/F1
- 양팔/몸통 공유 joint에서 action conflict
- 한 손 성공이 다른 손 실패를 유발하는 비율

### 6.3 협력 신호는 오른손 reward gate 하나로 시작할 수 있다

SDH에서 가장 직접적인 양손 결합은 왼손 준비 여부를 오른손 reward에 넣은 것이다. 우리도 초기에는 actor 전체를 서로 관측시키기 전에 다음과 같은 event-level gate를 둘 수 있다.

```text
fret_ready(e, t) = target strings가 올바른 프렛/손가락 상태이며
                   최소 hold 조건을 만족

strike_credit(e, t) = strike_reward(e, t) × readiness_gate(fret_ready, timing)
```

단, hard gate만 쓰면 fret 실패 시 strike가 영원히 학습 신호를 못 받는다. SDH 코드의 timer 예외처럼 다음 중 하나가 필요하다.

- 시간에 따라 완화되는 soft gate
- readiness와 timing을 분리한 두 critic
- teacher-forced ready 단계에서 시작하는 curriculum
- 최대 대기 시간을 넘으면 strike 단독 신호 허용

### 6.4 base 기술 보존을 명시적인 불변조건으로 둔다

SDH의 핵심은 “두 체크포인트를 불러왔다”가 아니라 **초기 joint policy가 단일손 policy와 동치**라는 점이다.

우리 synchronizer/adaptor가 만족해야 할 초기화 테스트 예시는 다음과 같다.

```text
at initialization:
joint_action.left  == fret_checkpoint_action
joint_action.right == strike_checkpoint_action
residual_norm      == 0
```

공유 몸통 joint가 있으면 단순 equality가 불가능할 수 있다. 그 경우 action ownership 또는 merge rule을 먼저 고정해야 한다. 예를 들어 왼손 actor는 왼팔·왼손, 오른손 actor는 오른팔·오른손만 소유하고 몸통은 별도 coordinator가 소유하는 방식이다. 이 부분은 두 참고 연구가 모두 floating hands라 직접 해결해 주지 않는 우리 고유 문제다.

### 6.5 가장 안전한 단계적 경로

두 연구를 함께 해석하면 다음 순서가 자연스럽다.

1. **공통 event compiler 검증**: 두 goal stream이 같은 onset ID와 clock을 공유하는지 테스트한다.
2. **GPS형 frozen 병렬 baseline**: 양손 체크포인트를 수정 없이 같은 환경에서 실행한다.
3. **공동 판정만 추가**: 발음 순간 `fret_ready ∧ strike_valid` joint metric을 만든다.
4. **SDH형 reward coupling**: fret readiness를 strike credit에 연결하되 soft/timer escape를 둔다.
5. **0-init residual coordinator**: base actor를 동결하고 작은 양손 adaptor만 학습한다.
6. **필요할 때만 범위 확대**: log-std, 상위 actor layer, 공유 몸통 controller 순으로 제한적으로 unfreeze한다.

처음부터 전체 75-DOF joint actor를 다시 학습하는 것은 SDH ablation이 보여 준 비효율을 그대로 떠안을 가능성이 크다.

### 6.6 두 연구에서 그대로 가져오면 안 되는 부분

- GPS의 `tick+3`/10-frame trajectory 같은 매직 타이밍 상수
- GPS의 기본 `wait=0` 동작을 “동기화 완료”로 간주하는 것
- GPS의 오른손 IK를 학습된 strike 정책 병합 근거로 사용하는 것
- SDH의 floating-hand 전제에서 나온 action 단순 concat을 전신 공유 joint에 그대로 적용하는 것
- SDH 논문의 “완전 동결”만 믿고 공개 코드의 `log_sigma` 예외를 놓치는 것
- hard readiness gate로 strike gradient를 완전히 차단하는 것
- 단일손 F1만 유지되면 joint 연주도 성공한다고 가정하는 것

---

## 7. 구현 전 확인 체크리스트

### 공통 데이터

- [ ] fret과 strike가 동일한 event ID를 사용한다.
- [ ] 두 goal compiler의 초/프레임 변환과 반올림 규칙이 같다.
- [ ] open, mute, tied, hammer, pull, slide 이벤트의 양손 의미가 정의되어 있다.
- [ ] strum group에서 왼손 chord-ready 판정이 원자적으로 계산된다.

### 체크포인트 결합

- [ ] 두 정책의 observation normalization 통계를 각각 보존한다.
- [ ] action joint name과 ordering을 이름 기반으로 검증한다.
- [ ] 공유 joint ownership/merge rule이 명시되어 있다.
- [ ] 0 residual에서 단일손 rollout 재현 테스트를 통과한다.
- [ ] freeze 대상에 actor mean, encoder, value, normalizer, log-std가 각각 포함되는지 명시한다.

### 공동 학습

- [ ] fret 6채널과 strike 채널을 한 스칼라로 조기에 합치지 않는다.
- [ ] readiness gate가 strike 학습 신호를 영구 차단하지 않는다.
- [ ] 양손 termination이 다른 손의 정상 rollout을 어떻게 종료시키는지 정의한다.
- [ ] joint metric은 반드시 “올바른 strike 시점의 올바른 fret”을 측정한다.
- [ ] synchronizer offset과 base action을 별도로 기록한다.

### 타이밍 진단

- [ ] `fret_ready_time - score_onset`
- [ ] `strike_crossing_time - score_onset`
- [ ] `strike_crossing_time - fret_ready_time`
- [ ] 조기 strike, 지연 strike, fret release-too-early를 별도 집계한다.
- [ ] control step, physics substep, 영상/audio sample clock 사이의 변환을 테스트한다.

---

## 8. 출처와 근거 위치

### GPS

- 논문: [Learning to Play Guitar with Robotic Hands](https://doi.org/10.1111/cgf.15166)
- 공식 코드: [MRXuanL/GPS-GuitarPlaySimulation](https://github.com/MRXuanL/GPS-GuitarPlaySimulation)
- 탭에서 왼손/오른손 배열 생성: [`music/goal.py`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/music/goal.py#L12-L57)
- 오른손 궤적과 IK: [`guitar_task_withhands.py` L231–400](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L231-L400)
- 왼손-only action: [`before_step`, `action_spec`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L611-L714)
- 테스트 병합 loop: [`after_step`](https://github.com/MRXuanL/GPS-GuitarPlaySimulation/blob/8620d439d498a9273d2a8851460828ea3a26918e/guitarplay/suite/tasks/guitar_task_withhands.py#L633-L672)

### SDH

- 논문: [arXiv:2409.16629](https://arxiv.org/abs/2409.16629), DOI [10.1145/3680528.3687692](https://doi.org/10.1145/3680528.3687692)
- 공식 코드: [xupei0610/guitar](https://github.com/xupei0610/guitar)
- 공식 실행법: [`README.md`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/README.md)
- 두 체크포인트 로딩과 AdaptNet 배선: [`main.py` L456–529](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/main.py#L456-L529)
- AdaptNet 구조와 freeze 예외: [`models.py` L288–378](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/models.py#L288-L378)
- 양손 goal, reward, ready gate: [`env.py` L2089–2201](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/env.py#L2089-L2201)
- 동기화 목적/판별자 설정: [`cfg/two_demo.py`](https://github.com/xupei0610/guitar/blob/e97867fcec0d4d12f1a44e845632f5dc89a96e38/cfg/two_demo.py)

---

## 9. 한 문장 요약

GPS는 **“한 악보 시계에서 왼손 RL과 오른손 IK를 재생하고 발음 순간 접촉 상태를 합치는 방식”**, SDH는 **“두 단일손 actor의 기술을 보존한 채 양손 상태를 함께 읽는 0-초기화 latent residual synchronizer를 곡별로 학습하는 방식”**이다.
