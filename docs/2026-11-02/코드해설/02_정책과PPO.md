# 관측에서 행동을 만들고 PPO로 학습하는 구조

[전체 안내로 돌아가기](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md)

이 문서는 현재 기본 학습이 실제로 만드는 `FingerSkillPolicy`와 `DecisionPPOTrainer`를 중심으로 설명한다. 파일 안의 `Policy`, `SpecialistPolicy`, 일반 `PPOTrainer._update`는 공용·기존 경로도 지원하는 구현이다. 현재 기본 J/K1을 읽는 순서는 **Encoder → FingerSkillPolicy → compute_decision_gae → DecisionPPOTrainer → 상속받는 저장·복원·실패 롤백**이다. 앞 문서의 [실행과 수집](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md)을 먼저 읽으면 buffer가 어디서 왔는지 연결된다.

## 1. `/home/ajou/yigyu/3/guitar_learning/training/policy.py`

소스: [policy.py:1](/home/ajou/yigyu/3/guitar_learning/training/policy.py:1)

### 파일 전체의 역할과 공통 용어

이 파일은 관측에서 **행동의 확률분포**와 **미래 보상·비용의 예상값**을 계산한다. 기타에 실제 힘을 가하거나 성공 보상을 계산하지 않는다. `forward`는 분포의 평균과 표준편차를 계산하고, `act`는 그 분포에서 행동을 뽑으며, `evaluate`는 전에 뽑은 행동을 새 모델이 얼마나 그럴듯하게 보는지 다시 계산한다.

`latent`는 -1~1 제한을 적용하기 전 실수 행동이고, 실제 행동은 `tanh(latent)`다. `logp`는 실제 행동에 해당하는 로그 확률밀도다. PPO는 수집 때의 logp와 학습 중 새 logp 차이를 사용한다. `reward_value`와 `cost_value`는 각 상태에서 이후 얻을 할인 보상과 비용의 예상값이며 정답 판정 자체가 아니다.

입력 다섯 개는 모든 정책에서 같은 이름을 쓴다.

| 입력 | 현재 기본 모양 | 의미 |
| --- | --- | --- |
| `state` | `[B,557]` | 관절·목표 오차·이전 행동·기타/손목/접촉·음 이력·대기 상태·로컬 잔여 시간·종료 타이머 등 이미 스케일링된 상태 |
| `events` | `[B,64,24]` | 현재와 가까운 미래의 음 토큰. 각 음의 시간·줄·프렛·손가락·접촉/표면 오차 등 |
| `mask` | bool `[B,64]` | 실제 음 토큰이 들어 있는 칸 |
| `priority_events` | `[B,8,24]` | 네 손가락별 tracking/next 토큰 |
| `priority_mask` | bool `[B,8]` | 각 우선 칸의 유효 여부 |

`B`는 수집 시 N개 환경 수이고, PPO 미니배치에서는 선택한 유효 결정 수다. 이 파일은 미터·라디안 등의 원시 단위를 다시 정규화하지 않는다. 환경이 고정 scale로 만든 값을 받으며, 실행 중 running mean/std를 갱신하는 관측 정규화는 없다.

### `Encoder`: 몸 상태와 여러 음을 하나의 문맥으로 합치기

[Encoder:14](/home/ajou/yigyu/3/guitar_learning/training/policy.py:14)는 세 입력 흐름을 합친다.

1. 상태 벡터를 `Linear→Tanh→Linear→Tanh`로 처리해 256차원으로 만든다.
2. 음 하나의 event를 공통 event 네트워크로 128차원 토큰으로 만든다.
3. 상태에서 만든 query와 각 토큰의 내적으로 중요도를 계산하고 softmax 가중합으로 일반 음 문맥 128개를 얻는다.
4. 우선 토큰은 같은 event 인코더를 통과시키지만 가중합으로 섞지 않는다. 손가락·tracking/next 순서가 유지되도록 펼친다.
5. 상태 256+일반 문맥 128+우선 토큰 수×128을 이어 붙여 fusion 네트워크에 넣는다.

현재 우선 8칸이므로 fusion 입력은 256+128+8×128=1408개다. small은 `(256,256,256)`, medium은 `(512,512,256)`, large는 `(1024,1024,512)`인 3층 fusion을 사용한다. large는 마지막 문맥이 512개이며, 상태 입력층과 event 입력층 자체가 1024로 바뀌는 것은 아니다.

mask가 False인 음은 먼저 0으로 바꾸고 attention 점수를 -∞로 만든다. 모든 음이 비었을 때 softmax가 NaN이 되지 않도록 가짜 null칸 한 개를 추가한다. 우선 토큰도 mask로 최종 0 처리한다. 따라서 빈 음 칸에 과거 숫자가 남더라도 유효한 목표처럼 쓰지 않는다.

### `FingerSkillPolicy.__init__`: 계약을 먼저 확인한다

[FingerSkillPolicy:401](/home/ajou/yigyu/3/guitar_learning/training/policy.py:401)가 현재 runner에서 생성하는 정책이다. 생성자는 `(state_dim, event_dim=24, size='medium', contract=None)`만 받는다. 현재 학습 계약은 `guitar_learning.finger_skill.v3`, 정책 architecture는 `guitar_learning.finger_skill_policy.v2`이며 557상태·J·독립 탐색·K1을 강제한다. 상태 필드 이름이 유일한지, 마지막 5필드가 로컬 잔여 시간 1개+손목 종료 4개인지, 우선 8칸 순서가 맞는지, 행동 이름이 정확한지, GPU 계약인지까지 검사한다. 차원만 맞는 다른 환경을 우연히 연결하는 것을 막는다.

네 손가락은 `index,middle,ring,pinky` 순서다. 손가락마다 출력 4개는 첫 관절의 굽힘·벌림 2축과 다음 두 관절 각 1축이다. 정책은 각 손가락에 다음 20개 local 상태를 별도로 전달한다.

- 해당 4축의 `q_offset`, `q_velocity`, `target_error`: 12개.
- MCP/PIP/DIP 실제 각도의 sin/cos: 6개.
- 실제 각도 유효 여부와 대기 gate: 2개.

이 20개는 전체 state에도 있지만 전용 손가락 head가 자기 관절과 목표를 직접 볼 수 있도록 다시 연결된다. 한 손가락의 입력을 다른 손가락에 잘못 배정하지 않도록 필드명으로 인덱스를 찾는다.

### 지지 쪽 17축과 네 손가락 16축의 분리

[451행](/home/ajou/yigyu/3/guitar_learning/training/policy.py:451)부터 support 입력 허용 목록을 만든다. support는 몸·팔·손목·엄지 등을 포함하는 앞 17개 행동 축이다. 네 연주 손가락 16축은 별도다. support는 앞 17축의 관절/이전 행동, 기타의 위치·방향·변위, 손목과 엄지의 기타 상대 위치, 지지 접촉, 손목 영역 차이, 현재 손목 종료 타이머를 본다. event에서는 앞 9열만 본다. 즉 목표의 거친 시간·줄·프렛·손가락 등의 계획은 보되, 손가락의 실제 패드오차나 압현 성과까지 support 입력으로 그대로 주지 않는다.

이는 손가락이 해야 할 미세 움직임을 팔이 대신 따라 하도록 정보가 강하게 연결되는 것을 줄이는 구조다. 현재 J에서는 support와 finger의 인코더·출력부·표준편차를 모두 학습한다. support를 동결하거나 손가락만 따로 학습하는 분기는 없다.

구조는 다음과 같다.

```text
허용된 지지 상태 + event9열 → support Encoder → 17축 평균
전체 state557 + event24열 → finger Encoder → 공통 손가락 문맥
  각 손가락: 공통 문맥 + 자기 우선토큰2×128 + 자기 상태20
             → Linear128 → Tanh → Linear4
전체 state557 + event24열 → 별도 value Encoder → 보상가치1 / 비용가치1
```

Actor support·finger와 critic은 같은 Encoder 클래스를 쓰지만 **가중치를 공유하지 않는 별도 인스턴스**다. `value_parameters`가 공용 메서드를 재사용한다고 해서 actor와 critic 가중치를 같이 쓰는 것은 아니다. 마지막 출력 head는 가중치와 bias를 0으로 초기화한다. 초기 평균 행동이 0이며 랜덤 탐색이 먼저 움직임을 만든다. 따라서 첫 시점의 무작위 큰 출력에서 학습을 시작하지 않는다.

### `forward`: 무엇을 반환하는가

[forward:500](/home/ajou/yigyu/3/guitar_learning/training/policy.py:500)는 support 평균 17개, 각 손가락 평균 4×4개, 오른손 0 여섯 개를 이어 `[B,39]` 평균을 만든다. 네 손가락 head는 자기 tracking/next 우선토큰을 별도 인코딩하여 공통 문맥과 합친다. value Encoder의 출력에서 보상·비용 critic이 각각 `[B]`를 만든다.

`priority_tokens`는 우선8칸을 인코딩하고 유효 마스크를 곱한 토큰이다. 명시적인 for loop가 `index → middle → ring → pinky` 순서로 `finger_tokens` 두 칸을 펼치고 자기 `local_state` 20열을 꺼낸다. 공통 `context`와 함께 `finger_input`을 만들어 각 head에 넣은 뒤 `finger_means`를 이어 16축을 만든다. 기존 복합 표현을 풀어 쓴 것으로 손가락 순서·계산·표본 추출 순서는 유지한다.

표준편차는 support 17개와 finger 16개의 학습 가능한 `log_std`에서 나온다. -5~2로 제한하므로 latent 표준편차 범위는 약 0.00674~7.389다. 초기값 -3이면 약 0.0498이다. 오른손 비활성 칸은 평균 0·고정 log_std -3으로 채워 형상은 유지한다. 지역변수 `active_log_std`와 최종 반환 `log_std`는 표준편차 자체가 아닌 로그 표준편차다. 정규분포의 표준편차 인자는 `log_std.exp()`로 만든다.

`_active_mask`는 항상 앞 33축만 True다. 샘플링·우도·KL·entropy는 활성 축을 기준으로 계산한다. 현재 기본 J의 확률적 행동은 33축이며 외형 39축 중 오른손 6축이 랜덤하게 움직이는 구조가 아니다.

### `act`, `log_probability`, `evaluate`: 같은 행동의 의미를 유지하기

[act:549](/home/ajou/yigyu/3/guitar_learning/training/policy.py:549)는 평균과 표준편차를 계산한 뒤 활성 축에만 정규분포 잡음을 더한다. `deterministic=True`이면 잡음 없이 평균을 사용한다. `tanh`는 모든 실수를 -1~1로 제한한다. 예를 들어 latent 0.05는 행동 약 0.04996이며, latent 2는 약 0.964다. 이 숫자가 관절각 2rad라는 뜻은 아니다.

[log_probability:533](/home/ajou/yigyu/3/guitar_learning/training/policy.py:533)는 정규분포 확률에 tanh 변수변환의 Jacobian 보정을 적용한다. 계산에는 포화 부근에서도 안정적인 `softplus` 식을 쓴다. PPO 학습에 실제 bounded 행동과 맞는 likelihood를 제공하려는 처리다.

[evaluate:562](/home/ajou/yigyu/3/guitar_learning/training/policy.py:562)는 `[B,39]`의 **이전에 수집한 latent**를 받아 새 모델의 logp와 entropy를 계산한다. 여기서 행동을 새로 뽑으면 PPO의 old/new 비교가 다른 행동끼리 이뤄져 잘못된다. entropy는 tanh 전 latent 정규분포의 entropy이며, 실제 관절 움직임의 다양성이나 tanh 후 정확한 entropy와 같지 않다.

[analytic_kl:539](/home/ajou/yigyu/3/guitar_learning/training/policy.py:539)는 이전/현재 정규분포 차이를 활성 축별로 합친 `[B]` 값을 돌려준다. PPO는 이를 전체 유효 결정에 대해 평균해 업데이트가 너무 큰지 판단한다. 이 함수의 `previous_log_std`·`current_log_std`도 각각 이전/현재 로그 표준편차이며 KL 수식의 연산 순서는 유지한다.

### 항상 학습하는 대상과 삭제된 이전 계약

[actor_parameters:487](/home/ajou/yigyu/3/guitar_learning/training/policy.py:487)는 support Encoder·17축 head, finger Encoder·네 손가락 head와 두 `log_std`의 모든 매개변수를 actor optimizer에 넘긴다. `requires_grad`를 끄는 단계 분기는 없다. [value_parameters:493](/home/ajou/yigyu/3/guitar_learning/training/policy.py:493)는 기존 `Policy.value_parameters`를 재사용해 value Encoder와 두 critic을 별도 optimizer에 넘긴다. `_validate`도 공용 입력 검사를 재사용한다.

`phase='J'`, `exploration='independent'`는 고정된 클래스 메타데이터다. 생성자에서 선택하지 않는다. R/F 단계, 단계 간 actor 이전 `transfer_from`, 상관 탐색의 `bend_basis`·`_to_basis`·`_from_basis`, 행동을 3/6tick 유지하는 선택은 현재 손가락 경로에서 삭제했다. 각 활성 축의 독립 Gaussian 잡음으로 매 정책 tick에 새 행동을 만든다.

관측 끝은 다음 5열이다. 앞의 552열은 공유 왼손 관측이다.

| 끝의 순서 | 필드 | 고정 scale |
| --- | --- | --- |
| 1 | `finger_skill.remaining_s` | 원곡 전체 task 길이 |
| 2 | `wrist_termination.active` | 1 |
| 3 | `wrist_termination.elapsed_s` | 1.5초 |
| 4 | `wrist_termination.preparation_remaining_s` | 3초 |
| 5 | `wrist_termination.severe_elapsed_s` | 0.1초 |

R/F/J one-hot 3열과 `finger_skill.planned_ticks` 1열은 제거했다. 따라서 이전 561상태 checkpoint는 새 모델에 호환되지 않는다. 더 오래된 557상태라도 필드와 schema가 다르므로 호환되지 않는다. 숫자 차원이 같은 것만으로 `load`가 허용되지 않으며, 현재 계약으로 새 학습을 시작하고 같은 계약 안에서만 엄격하게 재개한다.

### 같은 파일의 다른 두 정책을 읽는 법

[Policy:42](/home/ajou/yigyu/3/guitar_learning/training/policy.py:42)는 기본적인 39축 공동 attention 정책이다. 일반 Encoder 두 개, 33/6 두 actor head, 39개 std, 두 critic을 가진다. `_validate`는 batch/상태차원/event24열/mask/우선칸/유한값을 검사한다. `forward→act→evaluate`의 의미는 위와 같지만 기본 priority가 2칸이고 별도 손가락 head가 없다. 현재 runner가 이 클래스를 직접 생성하지는 않는다.

[SpecialistPolicy:125](/home/ajou/yigyu/3/guitar_learning/training/policy.py:125)는 과거 left/right/joint 손별 학습용이다. 각 손의 actor Encoder와 head를 따로 만들고, 비활성 손은 0 또는 이전한 고정 partner로 계산한다. 구형 GPU 왼손 reward 계약이면 손가락 전용 head도 붙인다. `partner_initialized`는 고정 상대가 실제로 이전됐는지 checkpoint에 남기는 buffer다. 활성 손만 likelihood와 sampling에 포함한다.

[transfer_actor:327](/home/ajou/yigyu/3/guitar_learning/training/policy.py:327)는 자체 손별 checkpoint에서 요청한 손의 actor와 std를 옮기며 critic·optimizer·난수는 옮기지 않는다. 전체 신경망 shape/dtype/finite와 계약을 먼저 확인한 뒤 복사한다. 구형 specialist를 현재 FingerSkillPolicy에 자동 합치는 통로로 이해하면 안 된다.

## 2. `/home/ajou/yigyu/3/guitar_learning/training/ppo.py`

소스: [ppo.py:1](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:1)

### 책임과 현재 실제 설정

PPO는 수집한 관측과 latent를 다시 평가해 좋은 선택의 확률을 높이고 나쁜 선택의 확률을 낮춘다. 물리를 실행하거나 reward를 새로 만들지는 않는다. 현재 runner는 `DecisionPPOTrainer`를 쓰며 이 클래스가 `PPOTrainer`의 생성자, 실패 롤백, 저장·불러오기를 상속한다.

[PPOConfig:116](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:116)의 기본값에 `launch.py`가 일부를 덮어쓴 **최종 현재 설정**은 다음과 같다.

| 항목 | 현재 값 | 뜻 |
| --- | ---: | --- |
| actor_lr | 0.00003 | 행동망 Adam 학습률 |
| value_lr | 0.0003 | 가치망 Adam 학습률 |
| gamma / cost_gamma | 0.99 / 1.0 | 보상은 할인, 비용은 비할인 |
| gae_lambda | 0.98 | 기본 dataclass 기본값 0.95를 GPU 왼손 설정이 덮어씀 |
| clip_ratio | 0.2 | 확률비 PPO clip 범위 0.8~1.2 |
| epochs | 2 | actor와 critic 각각 자료를 2회 순회 |
| minibatch_size | 4096 | dataclass 기본값 256을 GPU 설정이 덮어씀 |
| max_grad_norm | 0.5 | actor/critic 각각 gradient 크기 제한 |
| target_kl | 0.02 | 전체 수집 자료 평균 KL 허용치 |
| kl_retries / retry_lr_factor | 3 / 0.25 | 미니배치당 재시도 최대 3회, 학습률 축소계수 |
| advantage_normalization | joint | 보상/비용 우위를 먼저 차감한 뒤 함께 정규화 |
| cost_weight | 1 | 비용 우위 계수 고정 |
| episode_cost_budget / lambda_lr | None / 0 | 에피소드 비용에 따른 승수 자동조정 없음 |

이 구현의 actor 목적에는 별도 entropy bonus가 없다. entropy는 진단 로그에 기록한다. 초기 std가 학습 가능한 값이라는 사실과 entropy를 높이도록 별도 보상을 준다는 설명은 구분해야 한다.

### `compute_decision_gae`: duration을 고려한 미래 평가

[compute_decision_gae:386](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:386)는 `[D,N]` reward/value/next_value/종료/duration/valid를 받는다. valid가 False인 padding은 계산하지 않는다. 환경별 유효 결정은 앞에서부터 빈틈없는 prefix여야 한다.

결정 길이를 `d`라 할 때:

```text
delta = 결정 내부 할인누적 보상 + gamma^d × 다음 가치 × (true terminal 아님) - 현재 가치
advantage = delta + (gamma×lambda)^d × 다음 advantage × (episode 끝 아님)
가치망 정답 = advantage + 수집 당시 현재 가치
```

결정 내부 보상은 Collector가 이미 할인해서 합쳤다. 다음 가치에만 gamma^d를 적용하며 내부 보상을 다시 통째로 할인하지 않는다. 현재 K1이면 d=1이다.

예를 들어 보상 1, 현재 가치 2, 다음 가치 3이면 비종료 delta는 `1+0.99×3-2=1.97`이다. 실제 terminal이면 다음 가치를 제거해 `1-2=-1`이다. truncation이면 delta에서 다음 가치는 보존하지만 이후 에피소드로 이어지는 advantage carry는 끊는다. H32 경계에서는 수집된 마지막 다음 가치로 미래를 추정하므로 보상을 단순히 0에서 끝내지 않는다.

현재 GPU 환경은 실패뿐 아니라 정상 timeline 끝도 `terminated=True`로 반환한다. `truncated`는 현재 기본에서 항상 False다. 위 truncation 설명은 계산기가 지원하는 일반 규칙이며 현재 곡 끝을 truncation으로 처리한다는 뜻은 아니다.

### `policy_advantages`: 보상과 비용이 만나는 한 곳

[policy_advantages:158](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:158)는 현재 모드에서 `combined=reward_advantage−1×cost_advantage`를 만든 뒤 수집 자료 전체 평균·표준편차로 정규화한다. 미니배치마다 별도 정규화하지 않는다. 분산이 0이면 1e-8 분모 보호를 적용해 일정한 성분이 학습을 밀지 않도록 한다.

예를 들어 reward 우위 3, cost 우위 5인 선택은 결합 우위 -2다. 보상만 크다고 강화되는 것이 아니다. `joint`는 두 원래 우위의 상대 규모를 보존한 채 차감한다. 비기본 `separate`는 reward와 cost를 각각 표준화하고 차감한 뒤 다시 정규화한다. 이 둘은 동일하지 않으며 현재 v3 실행은 joint를 강제한다. 가치망 정답에는 actor 우위 정규화를 적용하지 않는다.

### `DecisionPPOTrainer._update`의 실제 순서

[DecisionPPOTrainer:420](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:420)에서 읽기 시작한다.

1. `config=self.config`, `batch=detach한 buffer`로 읽기 쉬운 지역명을 붙이고 reward와 cost의 GAE/return을 각각 계산한다.
2. `valid.sum()`으로 실제 결정을 세고 2개 미만이면 거부한다. 관측·latent·old 분포에서 유효 슬롯만 꺼내 `[M,...]`로 만든다. padding 관측은 정책에 평가시키지 않는다.
3. reward/cost 우위를 결합·정규화한다. 종료 에피소드의 비용은 선택적 비용 승수 갱신에 사용할 수 있도록 유효한 완료 행만 모은다. 현재 비용 승수 갱신은 꺼져 있다.
4. 각 epoch에서 유효 결정을 무작위 순열로 나누어 actor를 학습한다.
5. actor가 전부 성공하면 같은 return 정답으로 reward/cost critic을 학습한다.
6. 모든 모델값이 유한한지 확인하고 update 카운터를 1 올린다.
7. 수집한 전체 유효 결정을 새 모델로 평가해 확률비·clip 비율·가치망 오차 등을 기록한다.

`reward_advantage`·`cost_advantage`는 각각 보상/비용 GAE 우위이고, `reward_return`·`cost_return`은 각 critic의 고정 학습 목표다. `old_log_std`는 수집 당시 로그 표준편차다. 일반 song용 `PPOTrainer._update`에 남은 `ar/ac/rr/rc` 같은 축약명과 구분해 현재 J 실행은 이 전체 이름을 따라 읽는다.

actor의 미니배치 식은 다음과 같다.

```text
ratio = exp(현재 logp - 수집 당시 logp)
actor_loss = -mean(min(ratio×advantage, clamp(ratio,0.8,1.2)×advantage))
```

같은 수집 행동을 현재 정책이 더 높은 확률로 보면 ratio>1이다. 양의 우위 행동을 너무 급히 강화하지 않도록 clip을 사용한다. clip만으로 전체 정책 변화가 보장되지는 않아 별도의 KL 검사를 추가한다.

critic은 `0.5×(보상가치 MSE+비용가치 MSE)`를 최소화한다. actor와 critic은 별도 Adam이므로 가치 예측 오류의 gradient가 actor Encoder를 직접 움직이지 않는다.

### KL 검사와 롤백: 실패한 시도를 그대로 반영하지 않는다

actor 미니배치 갱신 직전 모델 파라미터와 actor Adam 상태를 snapshot한다. 갱신 후 **해당 미니배치만이 아니라 모든 유효 결정**에서 정책을 다시 계산하고 analytic KL 평균을 검사한다. 0.02 이하·유한이면 승인한다. 초과하면 모델과 Adam을 직전 상태로 복구하고 학습률을 줄여 같은 미니배치를 재시도한다. 최초 시도와 최대 3회 재시도가 가능하다.

최대 횟수까지 실패하면 [KLGuardError:173](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:173)가 발생한다. 상위 [PPOTrainer.update:218](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:218)는 **update 전체 이전**의 모델·두 Adam·비용 승수·update 카운터·Torch/CUDA난수 상태를 복원하고 예외를 다시 전달한다. critic 계산 중 오류도 같은 전체 롤백을 거친다. 실패한 절반짜리 update를 성공한 checkpoint로 만들지 않기 위한 장치다.

KL 재시도 중 허용된 축소 학습률은 이후 미니배치에도 남을 수 있다. gradient 0.5 제한은 적용 전 norm을 측정한 뒤 gradient를 clip하므로 로그의 `actor_grad_norm`이 0.5보다 클 수 있다. 그 숫자만으로 제한이 작동하지 않았다고 결론내리면 안 된다.

### 지표를 해석할 때 보는 함수

| 심볼 | 하는 일과 해석 |
| --- | --- |
| [rollout_evaluation:16](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:16) | 전체 관측을 최대 4096개씩 나누어 정책 출력을 합친다. 토큰 중간값 때문에 GPU 메모리가 급증하는 것을 줄이며 gradient 없이 계산한다. |
| [tensor_summary:27](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:27) | 배열을 펼쳐 double로 집계하고 count/nonfinite/mean/std/min/max를 반환한다. 유한한 표본이 없으면 통계는 None이다. |
| [MinibatchSummary:37](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:37) | optimizer 단계별 평균을 표본 수로 가중한다. steps와 sample_visits를 구분한다. 2epoch이면 자료 방문 수가 고유 결정 수보다 많다. |
| [advantage_diagnostics:68](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:68) | 일반 PPO 경로의 원시·결합·정규화 우위와 TD오차를 기록한다. 현재 DecisionPPO는 하단에서 유효 결정 기준 진단을 별도로 만든다. |
| [post_update_diagnostics:86](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:86) | 일반 PPO의 갱신 후 확률비·행동 포화·std·가치망 설명분산을 계산한다. 현재 DecisionPPO의 진단 필드와 완전히 같지는 않다. |
| [gaussian_kl:153](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:153) | 일반 PPO 용 39차원 정규분포 KL 평균. 현재 DecisionPPO는 정책의 활성 축·탐색기저를 아는 `analytic_kl`을 쓴다. |

DecisionPPO의 최상위 `actor_loss`, `reward_value_loss`, `cost_value_loss`는 **마지막 미니배치 값**이다. epoch 전체 평균을 보려면 `diagnostics.minibatches.*.sample_weighted_mean`을 본다. `analytic_kl`은 마지막 승인 시점의 전체 자료 KL이며, `max_attempted_kl`에는 거부한 시도도 포함될 수 있다.

`diagnostics.advantages`는 원래 reward 우위와 cost 우위 및 결합우위의 규모를 비교하는 데 쓴다. `post_update.ratio`와 `clip_fraction`은 갱신 크기를, critics의 MSE와 explained_variance는 예측 품질을 설명한다. explained_variance는 정답 분산이 0이면 None이며 성공률이 아니다. latent Gaussian entropy도 실제 압현 성공이나 관절 움직임 크기의 직접 지표가 아니다.

### 생성·저장·복원을 제공하는 `PPOTrainer`

[PPOTrainer.__init__:183](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:183)는 학습률·확률 범위·정수 예산·유한값을 검사하고 actor/value Adam을 따로 만든다. [_actor_snapshot / _actor_restore:209](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:209)는 미니배치 KL 재시도의 복구 단위다. `update`는 위에서 설명한 전체 트랜잭션의 외곽이며 자식 클래스의 `_update`를 호출한다.

[_identity:342](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:342)는 trainer schema·정책 architecture·전체 입력/제어 계약·PPO설정을 식별자로 묶는다. 기본 joint 정규화 필드는 직렬화에서 생략하지만 로드 비교의 의미가 느슨해지는 것은 아니다. `DecisionPPOTrainer`는 자기 schema를 오버라이드하므로 일반 PPO checkpoint와 구분된다.

[save:349](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:349)는 모델, 두 optimizer, 비용 가중치, update 수, 메타데이터, Python/NumPy/Torch/CUDA 난수 상태를 저장한다. 임시 파일에 먼저 쓴 뒤 하드링크로 목표 이름을 만들므로 기존 동일 파일명을 덮어쓰지 않는다. 디스크 동기화와 SHA 명세는 호출측 `CheckpointRecorder`가 덧붙인다.

[load:364](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:364)는 identity 전체 일치, 모델 유한값, CUDA 난수 장치 수 일치를 확인하고 모델/optimizer/난수/카운터를 복원한다. 물리 시뮬레이터의 현재 몸 위치나 진행 중 에피소드 원장은 payload에 없다. 일정·sampler·소스 SHA검사는 runner 메타데이터 복원 단계가 담당한다. 따라서 이 함수 하나만 호출했다고 현재 학습의 모든 재개 검증이 끝난 것은 아니다.

### 일반 `compute_gae`와 `_update`가 남아 있는 이유

[compute_gae:135](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:135)는 고정 1tick 전이 `[T,N]`용이며 duration/valid가 없다. [PPOTrainer._update:237](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:237)는 이 형식의 기존 수집기와 정책을 학습한다. 현재 기본은 DecisionCollector와 DecisionPPO를 쓰므로 이 구현을 현재 자료형에 그대로 끼우면 안 된다. 현재 J 수집기는 매 60Hz tick마다 한 결정을 만들어 duration=1·valid=True인 자료를 넣는다. DecisionPPO의 일반 duration/padding 지원이 남아 있어도 현재 환경에 행동 유지 옵션이 있다는 뜻은 아니다. 이 구분과 정책 자체의 활성 33축 KL 계산 때문에 buffer 형식을 확인한 뒤 연결해야 한다.

## 3. 실제 소스를 볼 때 따라갈 질문

“손가락이 무엇을 보는가”는 `local_fields`와 `forward`의 head 연결을 본다. “어느 축을 학습하는가”는 `actor_parameters`와 항상 33축인 `_active_mask`를 본다. “보상과 비용 중 무엇이 학습을 지배하는가”는 원래 reward가 아니라 GAE 뒤 `diagnostics.advantages`를 본다. “모델이 너무 급히 바뀌는가”는 clip 비율·전체 KL·재시도와 축소 학습률을 본다.

현재 기본에서는 J33 모두 학습하지만 손가락의 실제 움직임은 이 파일만으로 결정되지 않는다. 제어 codec, PD, 충돌, 목표 기하, 보상과 종료도 함께 작용한다. 반대로 이 파일의 입력 목록, 활성 마스크, logp식, GAE 할인, 비용 결합을 바꾸면 같은 보상값에서도 학습 의미가 바뀌므로 checkpoint 계약과 검사를 함께 갱신해야 한다.
