# 학습 환경 정의 — 알고리즘·네트워크·하이퍼파라미터·I/O (fret · strike · full 공통)

> **상태: SUPERSEDED.** 초기 학습 구조를 보존한 역사 문서다. 현재 정본은 [`master_plan`](../../master_plan/README.md)이며, 아래의 차원·하이퍼파라미터·Full 구조를 현행 계약으로 사용하지 않는다.

> 최종 갱신: 2026-09-01. 현재 Fret 계약은 `30 action / 425 observation / 6 reward-value`다. 아래의
> `341 observation` 표기는 당시 설계 상태이며, 이 문서의
> strike·full 값과 ‘후보’ 표기는 후속 설계다. fret 실행은 `tab2body/TRAINING.md`를 따른다.

> tab2body **학습측**(`learning/models.py`·`learning/ppo.py`·`cfg.py`)의 사양. 규칙 문서
> (`task_*_design.md`)가 "무엇을 보상/조건으로 하나"라면, 이 문서는 **"어떤 알고리즘·네트워크로
> 학습하고, 입출력 텐서의 type·shape이 무엇인가"** 를 정한다. 모든 수치는 이식원본
> `related_work/guitar/{main.py, models.py, env.py}`(Pei Xu SA'24) 정독 실측값이며, 다른 값을 쓸 땐 이유를
> 붙였다(주파수·ob_horizon·goal 인코딩·fret/timer 정규화는 env.py에서만 확인).
> 파일 지도 = `tab2body/STRUCTURE.md`, 결정 = `PROJECT_CONTEXT.md §3`. 원문 설계 갱신일은 2026-07-21이며,
> 현재 실행 계약·명령은 위의 2026-09-01 안내와 `tab2body/TRAINING.md`를 따른다.
> 표기: **[G]**=guitar 실측 · **[우리]**=우리 결정/적응 · **[미정]**=착수 전 확정 필요.

## 0. 한 장 요약

- **알고리즘**: 멀티크리틱 **PPO**(on-policy) + 옵션 AMP 판별자. Isaac 대규모 병렬용. [G]/결정 #9
- **네트워크**: Actor·Critic **분리**(공유 없음), 각 `goal_embed + MLP`, Critic은 `value_dim` **멀티헤드**.
- **핵심 수치**: `num_envs=512` · `horizon=8`(→4096 샘플/업데이트) · `γ=λ=0.95` · `clip 0.2` ·
  `5 epoch × minibatch 256` · `actor_lr 5e-6 / critic_lr 1e-4`(분리·고정) · **엔트로피 0** ·
  `grad_clip 1.0` · `value_coef 0.5` · 종료보상 `−25` · PopArt value 정규화 · **60Hz 제어**.
- **환경별 action**: fret `42` / strike `33` / full `75`. **환경별 reward 열**: fret `6` / strike `1` / full `7`.

---

## 1. 알고리즘 — 왜 멀티크리틱 PPO인가

### 1-1. PPO (on-policy) [G]/결정 #9
- Isaac Gym은 **수백~수천 env를 GPU에서 동시 롤아웃**한다. 이런 대규모 병렬 on-policy 샘플에는
  PPO가 표준이고 안정적이다.
- GPS의 **DroQ(off-policy, SAC 계열)** 는 CPU·소수 env·리플레이 버퍼 세팅의 산물이라 우리 구조와
  반대 → **미채택**(결정 #9, 이름으로 명시 기각).

### 1-2. 멀티크리틱 (핵심) [G]
- 보상이 **스칼라 하나가 아니라 열(column) 벡터**다. fret은 **줄마다 1채널(6채널)**, 여기에
  옵션 판별자가 열로 더해진다.
- **왜 나누나**: 줄별 보상은 **스케일·희소도가 제각각**(어떤 줄은 매 스텝 눌리고 어떤 줄은 거의
  don't-care). 이를 한 스칼라로 합치면 큰 채널이 작은 채널을 가린다. 그래서 **채널마다 독립
  value 헤드·GAE·정규화(PopArt)** 를 두고, 마지막에 가중 합친다(§4).
- `value_dim = (판별자 수) + rew_dim`.

### 1-3. AMP 판별자 (옵션, 스타일) [G]
- 자연스러운 손·팔 **동작 스타일**을 참조 모션 분포 모방으로 학습(ICCGAN/AMP, WGAN-GP hinge).
- **S0(첫 학습)에서는 끈다** → `value_dim = rew_dim`. 태스크가 먼저 되면 자연스러움용으로 추가.

---

## 2. 하이퍼파라미터 (값 + 이유)

| 항목 | 값 | 근거·이유 |
|---|---|---|
| `num_envs` | **512** [G] | GPU 병렬 폭. RTX 4070 Ti 12GB에서 105-DOF는 무거우니 512로 시작(스모크로 상한 확인). |
| rollout `horizon` | **8** [G] | 8스텝×512env = **4096 샘플/업데이트**. 매우 짧은 지평 — 60Hz라 8스텝=0.13s. 밀집 보상 전제. |
| minibatch | **256** [G] | 4096/256 = **16 미니배치**. |
| opt epochs | **5** [G] | 롤아웃마다 5×16 = 80 그래디언트 스텝. |
| `γ` / `λ` | **0.95 / 0.95** [G] | 유효 지평 ≈ 1/(1−0.95)=20스텝 ≈ 0.33s. 짧은 지평이 압현/타현의 즉각 크레딧에 맞음. GPS는 recall용 0.84 권고 — 정체 시 노브. |
| PPO clip `ε` | **0.2** (ratio [0.8,1.2]) [G] | 표준. |
| `actor_lr` / `critic_lr` | **5e-6 / 1e-4** (분리, 고정) [G] | **actor를 critic보다 20× 느리게** — 정책을 천천히, 가치추정을 빠르게. adaptive-KL·target-KL **없음**(재현 부담↓). |
| entropy coef | **0 (없음)** [G] | 탐색은 정책의 상태의존 log_std가 담당(§3). 엔트로피 보너스 항 자체가 없음. |
| value coef | **0.5** [G] | `loss = pg + 0.5·vf`. |
| grad clip | **1.0** [G] | actor+critic 합산 grad-norm 클립. |
| 종료 보상 | **−25** (전 열 broadcast) [G] | 어떤 종료든 그 스텝 모든 보상 열에 −25. 실패 부트스트랩. |
| value 정규화 | **DiagonalPopArt** (헤드별) [G] | 이질적 열 보상 균형의 핵심. 끄지 말 것. |
| 제어 주파수 | **60Hz** (dt 1/60, substeps 4, frameskip 1) [G] | goals.py 타이머가 이 시계로 tick. |
| disc | WGAN-GP hinge, gp 10, lr 1e-5 [G] | 옵션(§1-3). |
| max_epochs / save | (cfg override) [cfg] | main.py 기본은 50000/10000이나 태스크 cfg가 override: fret(left_demo)=100000/20000·strike(right)=100000/50000·full(two_demo)=60000/20000. +500 epoch마다 ckpt. 참고값. |

**[우리] 곡별 커리큘럼**: 정책 하나는 곡 하나에 귀속된다. 동일한 곡 goal·운지·규칙을 유지한 채
`coverage`(곡 내부 random start) → `integration`(random-start 확률 감소) → `full_song`(항상 0프레임)
순으로 시작점만 바꾼다. 여러 곡을 섞어 새 곡에 zero-shot 일반화하는 목적이 아니다.

---

## 3. 네트워크 구조 (`learning/models.py`)

Xu `ACModel`: **Actor와 Critic은 트렁크를 전혀 공유하지 않는** 별개 망. 각자 `goal_embed`로 goal을
받아 본체에 더한다. 활성은 전 구간 **ReLU6**.

- **관측 정규화** [G]: actor·critic 입력 obs는 `RunningMeanStd(state_dim, clamp=±5.0)`로 정규화하며, 매
  업데이트마다 유효 프레임(seq_len 마스크)만으로 running mean/var를 갱신한다(guitar `models.py` ob_normalizer).
  판별자 정규화(§3-3)·value PopArt(§3-2)와 **별개의 3번째 정규화** — 원시 obs가 그대로 망에 들어가지 않는다.

### 3-1. Actor (정책) [G]
```
입력 obs → GRU(state_dim,256)[별도, §3-4]  ⊕  goal_embed(goal)   # 아래 Linear(256,..)의 입력 256 = GRU 은닉
  goal_embed: Linear(goal_dim,256) → ReLU6 → Linear(256,256)
  본체 MLP:   Linear(256,1024) → ReLU6 → Linear(1024,1024) → ReLU6 → Linear(1024,512)
  두 헤드:    mu = Linear(512, act_dim)         log_sigma = Linear(512, act_dim)
분포: Normal(mu, exp(log_sigma)+1e-8)  = 대각 가우시안, 차원 = act_dim
```
- **log_std는 상태의존 헤드지만 초기엔 거의 상수**: `bias=−3`(std≈0.05), `weight≈0`. → 초기 탐색은
  전 상태 동일, 학습하며 상태·DOF별로 분화. **엔트로피 보너스가 없어도 이게 탐색을 담당**(§2).
- 출력 `act_dim`은 base가 `[-1,1]`→EMA(0.5)+scale(2)로 PD 타깃에 매핑.

### 3-2. Critic (멀티크리틱) [G]
```
입력 obs → [별도 GRU/본체]  ⊕  goal_embed
  본체 MLP: Linear(256,1024)→ReLU6→Linear(1024,1024)→ReLU6→Linear(1024,512)→ReLU6→Linear(512, value_dim)
DiagonalPopArt(value_dim): 마지막 Linear의 weight·bias를 헤드별로 정규화
```
- **멀티헤드 = 멀티크리틱**: 마지막 `Linear(512, value_dim)` 하나가 `value_dim`개 값을 낸다(별도 망 아님).
- `value_dim = 판별자수 + rew_dim`. fret S0 = `0 + 6 = 6`.

### 3-3. 판별자 (옵션) [G]
`GRU(disc_dim,256) + MLP(256→256→128→32)`, 출력 32-D, 보상=`score.clamp(-1,1).mean(-1)`. 헤드마다 자체
`RunningMeanStd`. S0엔 없음.

### 3-4. [우리/미정] GRU 제거
Xu는 본체 앞에 `GRU(256)`로 `ob_horizon=2` 프레임을 시계열 처리한다(플로팅 손 관성용). **우리는
룩어헤드가 goal 관측에 이미 들어가고 목표가 매 스텝 완결적이라, `ob_horizon=1` 단일프레임 MLP로 충분**할
것으로 본다 → GRU 제거 권장. **[미정]**: 제거(권장) vs 유지. 유지해도 `ob_horizon=1`이면 GRU는 시계열 이득 없는 1스텝 비선형 사상으로 축소(항등은 아님).

---

## 4. 멀티크리틱 학습 루프 (`learning/ppo.py`) [G]

```
롤아웃(no_grad, 8스텝):
  a, v, logp = actor.act(obs)            # v = value_dim 벡터
  obs2, rews, done, info = env.step(a)   # rews = (N, rew_dim)  ← 열 벡터
  버퍼에 (s,a,v,logp,r,done…) 축적
업데이트(버퍼가 8스텝 차면):
  [옵션] 판별자 업데이트 → disc 보상 열 채움
  reward 벡터 조립: [disc열…, task열…]; rewards[terminate] = -25 (전 열)
  value PopArt 역정규화 → 열별 GAE → returns
  ★열별 어드밴티지 표준화: adv = (adv - mean_col)/(std_col+1e-8)     # 채널 균형의 핵심
  adv *= reward_weights (열별 가중)
  value_normalizer.update(returns); returns_norm = value_normalizer(returns)  # returns를 PopArt 공간으로
  5 epoch × minibatch 256:
     ratio = exp(logp_new - logp); clip [0.8,1.2]
     pg = -min(adv*ratio, adv*clip).sum(-1).mean()     # 열을 SUM, 배치를 mean
     vf = (v_new - returns_norm).square().mean()       # 전 헤드 MSE, 둘 다 PopArt 정규화 공간(v_new=미정규화 크리틱 출력)
     loss = pg + 0.5*vf ; grad_clip 1.0 ; step
```
- **핵심**: GAE·정규화는 **열별로 벡터 연산**, 가중 합은 **surrogate 안에서 `.sum(-1)`**. 즉 6개 줄
  크리틱이 각자 어드밴티지를 만들고, 가중치로 섞여 하나의 정책 그래디언트가 된다.
- `reward_weights`: 판별자 열 = `1 − Σ(task가중)`을 나눔, task 열 = `goal_reward_weight`. fret =
  `[0.15]×6`(합 0.9), disc 2개면 각 0.05.

**[우리] 리셋 순서**: Xu는 `reset_done()`으로 이터레이션 시작에 리셋. **우리 base는 step 끝에서
자동 리셋**(IsaacGymEnvs식). → 루프를 우리 base의 `step→(obs,reward,done)`에 맞춘다(Xu `reset_done` 이식 X).
**[우리/미정] 보상 반환**: base `step`을 4-튜플로 확장 vs `task.compute_reward()` 분리.

---

## 5. 환경별 I/O type·shape

모든 텐서: `dtype=float32`(done만 `bool`), device `cuda`, 배치축 `N=num_envs`.

### 5-1. 공통 계약 (base가 제공)
- `reset() -> obs`  ·  `step(actions) -> (obs, [reward,] done)`  *(reward 반환은 [미정] §4)*
- **action**: `(N, act_dim)` in `[-1,1]` → PD 타깃.
- **obs**: `(N, ob_dim)`, `ob_dim = 고유수용 + 기타상대 바디 + goal`.
  - 고유수용: 비잠금 DOF의 `pos+vel`. base 현재 = **비잠금 전체 81 → 162**. **[우리/미정]** 태스크
    제어 DOF만(예: fret 42→84)으로 축소할지.
  - 기타상대: `obs_body_names` 월드위치를 기타프레임으로 → `3 × K`.
  - goal: 태스크가 `super().compute_observations()`에 concat.

### 5-2. 환경별 값

| 환경 | act_dim (제어 DOF) | rew_dim (보상 열) | value_dim (=disc+rew, S0) | 제어 부위 |
|---|---|---|---|---|
| **fret** (왼손) | **42** | **6** (줄별) | 6 | 몸통+좌팔+좌손 |
| **strike** (오른손) | **33** | **1** (pluck) *[미정: 6줄별로 갈지]* | 1 | 우팔+우손 |
| **full** (병합) | **75** | **7** (좌6+우1) | 7 | 전신(AdaptNet) |

- 잠금 하체 24 DOF는 전 태스크 제외. full에서도 Neck/Head 6은 비제어(유지).
- **goal_dim**(관측): Xu 좌손 = `(n_strings+1)×goal_horizon = 7×5 = 35`. **[우리]** 명시 운지로 **손가락
  채널 추가** → 아래 §6 인코딩 참조. **후보 goal_dim: 최소 35(Xu) ~ 상한 125(§6-3), 잠정 65**
  (줄당 fret+finger 2채널+타이머 → 13/슬롯×5), 확정 전.
- 사이징 속성(모델/루프가 소비): `state_dim`·`act_dim`·`goal_dim`(=[actor,critic] 2리스트)·`rew_dim`·
  `disc_dim`(dict)·`reward_weights`(len=value_dim). base가 노출해야 함 **[미정 인터페이스]**.

---

## 6. I/O 예시 (구체 텐서)

**설정**: fret 태스크, `N=512`, 관측 바디 K=6(`LH:index_top·middle_top·ring_top·pinky_top·thumb_top·L_Wrist`),
고유수용=제어 42(권장), goal_horizon=5.

### 6-1. action (정책 출력)
```
action.shape = (512, 42)   float32, 값 ∈ [-1,1]
예 한 행(42): [ 0.03, -0.12, 0.44, ... , -0.02 ]   # 몸통9·좌팔12·좌손21 순서 = base.dof_names의 제어 부분집합
→ base: tgt = mid + 2.0·EMA(a)·half_range, 리밋 클램프 후 PD 타깃
```

### 6-2. observation (정책 입력)
```
obs.shape = (512, ob_dim)   ob_dim = 84(고유수용) + 18(기타상대) + goal_dim
 블록 레이아웃(한 env):
  [0:42]    제어 DOF pos           (rad)
  [42:84]   제어 DOF vel           (rad/s)
  [84:102]  기타상대 바디 6×3 위치  (m, 기타 로컬프레임)
  [102: ]   goal (아래 6-3)
```
> 주: 위 84 = **[미정] 제어-DOF 축소(§5-1) + ob_horizon=1(§3-4) 채택 시**의 값이다. base 기본은
> 162(비잠금 81×2)이며, ob_horizon=2 유지 시 비-goal 블록(고유수용+기타상대)이 2배가 된다.

### 6-3. goal 인코딩 예시 (**[우리] 후보 인코딩(상한 125), 확정 전**)
악보 상황: *지금 3번 줄 2프렛을 중지(finger 2)로 눌러야 하고(0.5s 뒤 릴리즈), 다음은 2번 줄 3프렛.*
줄 인덱스는 `G:string6=low-E` 규약. 한 lookahead 슬롯 = 줄별 `[fret/12, finger/4, is_press, is_mute]`(4)
× 6줄 + 타이머(1) = **25/슬롯**. `goal_horizon=5` → `goal_dim = 25×5 = 125`(상한). *Xu식 최소(35)와
이 상한(125) 사이에서 인코딩 확정 예정 — finger를 스칼라/one-hot·status 포함 여부로 조절.*
```
현재 슬롯(줄 순서 s1..s6, 여기선 s3만 활성):
  s3: [fret=2/12=0.167, finger=2/4=0.5, is_press=1, is_mute=0]
  그 외 줄: [0, 0, 0, 0]  또는 개방 발음 줄이면 is_mute=1
  timer: t = 노트 전환까지 남은 프레임 수; 정규화 = clamp(t/20, ≤2) − 1 ∈ [−1,1] (0.5s≈30프레임 → 30/20=1.5 → 0.5). Xu env.py observe_goal 근거, 이식 시 재확인.
다음 슬롯: s2 = [3/12=0.25, ...]   # 룩어헤드 = 규칙 R15(현재+다음 프렛 인지)
```

### 6-4. reward (환경 출력)
```
reward.shape = (512, 6)   float32   # 줄별 채널 (멀티크리틱)
예 한 행: [0.98, 0.90, 0.11, 0.90, 0.90, 0.95]   # s3(눌러야 하는데 아직 멂)=0.11, 나머지 자유/이격 만점권
종료 스텝이면 [-25,-25,-25,-25,-25,-25]
value(정책이 추정): (512, 6)   # 열마다 1개 = 멀티헤드
```

### 6-5. done
```
done.shape = (512,)   bool    # timeout | NaN | vel-blow | 태스크 종료(R7·R8·R13·R14)
```

---

## 7. 우리 적응 요약 + 미확정 결정

**Xu 대비 적응 [우리]**: ①단일 손→전신(act_dim 42/33/75) ②명시 운지(goal에 finger 채널, 보상은 지정
손가락) ③S0 판별자 off(value_dim=rew_dim) ④커리큘럼 신설 ⑤리셋은 우리 base의 step-tail 사용.

**착수 전 확정 [미정]**:
1. **base 인터페이스**: 사이징 속성(`rew_dim`/`goal_dim`/`value_dim`) 노출 + 보상 반환 경로(step 4-튜플 vs
   `compute_reward` 분리).
2. **GRU 제거**(§3-4): 단일프레임 MLP로 갈지.
3. **goal 인코딩 확정**(§6-3): finger 표현·status·lookahead 깊이 → `goal_dim` 최종값.
4. **고유수용 범위**(§5-1): 비잠금 전체(162) vs 제어 DOF만(태스크별).
5. **strike rew_dim**: 1(Xu) vs 6(줄별, fret과 대칭).

## 8. 참고
- 이식원본 수치: `related_work/guitar/main.py`(하이퍼·루프)·`models.py`(망)·`env.py`(주파수·ob_horizon·goal/fret/timer 정규화)·`cfg/{left_demo,right,two_demo}.py`.
- 규칙(무엇을 보상): `docs/plans/task_{fret,strike,full,hold}_design.md`.
- 파일 지도: `tab2body/STRUCTURE.md`. 결정·함정: `PROJECT_CONTEXT.md §3·§4`.
