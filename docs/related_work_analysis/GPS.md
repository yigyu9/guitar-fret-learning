# GPS (CGF24 로봇 손 기타) 분석 — 규칙·환경·구성

> 출처=related_work/GPS 코드 + docs/GPS-paper-ko.md. 최종 2026-07-17.
>
> GPS(Luo et al., CGF'24/SCA'24, DOI 10.1111/cgf.15166)를 **우리 tab2body 문서와 같은 틀**
> (§규칙 = `task_*_design.md`, §환경 = `learning_env_design.md`)로 재정리한 분석서. 각 값은
> `related_work/GPS/guitarplay/…` 코드 실측 + 논문 요약(`docs/GPS-paper-ko.md`)에서 왔고, 코드로 단정할 수
> 없는 값은 **확인 필요**로 표기했다. 파일:라인은 §5에 모았다(경로 접두 `guitarplay/` 생략).
> 표기: **[코드]**=GPS 코드 실측 · **[논문]**=논문 서술 · **[확인 필요]**=코드/논문 대조 미완.

---

## §0. 개요

- **한 줄 정의**: GPS = **모캡 없이 타블라처만 입력하면 Shadow Hand(로봇 손)가 기타를 학습해 연주**하는
  최초의 RL+IK 시스템. 과제를 ① 오프라인 운지 배정 → ② **왼손 프레팅 RL(DroQ)** → ③ 오른손 탄현 IK 로 3분할한다.
- **물리·학습 범위**: **왼손 손+전완(20-DOF)만** MuJoCo 완전 동역학으로 RL 학습한다. **오른손은 학습이 아니라
  test 모드 IK 궤적**이고, **몸통·상완·어깨는 아예 없다**(기타는 공간에 고정, 손만 떠 있음). 보상은 **단일
  스칼라**(fingering + energy + key-press 3항 합)이다.
- **우리(tab2body)와의 관계**: 우리는 **전신 물리 + 멀티크리틱 PPO + 명시 운지**로 간다(전혀 다른 스택).
  GPS는 우리의 **직접 이식 대상이 아니라 "규칙·수식 도너"** 다 — 우리 `task_fret_plan.md`·`PROJECT_CONTEXT`가
  이미 GPS의 **프렛 수식·reciprocal 커널·축분해 finger reward·freedom 완화·γ=0.84·idle 에너지 2배·finger
  goal 관측**을 이름으로 인용한다(§4). 알고리즘(DroQ)은 하드웨어 구조가 반대라 **명시 기각**(우리 결정 #9).

---

## §1. 구성 (configuration)

### 1-1. 제어 대상 (DOF · 좌/우 · 손가락)
- **모델**: Shadow Hand E3M5, **왼손 1 + 오른손 1**. 기본 손 = **24 관절(NQ) / 20 액추에이터(NU)**. 5손가락
  (엄지 THJ, 검지 FFJ, 중지 MFJ, 약지 RFJ, 소지 LFJ). FFJ0/MFJ0/RFJ0/LFJ0는 **커플드 텐던**(J2+J1 두 관절을
  1 액추에이터가 구동) → 관측 관절 24 > 액추에이터 20의 원인.
- **RL 제어는 왼손만**. 왼손 action ≈ **20차원 = 손 17(감축) + 전완 슬라이드 3**.
  - 감축(`reduced_action_space=True`, gym 기본): 액추에이터 A_THJ5·A_THJ1·A_LFJ5 제거 + THJ2 범위를
    (0,0.698)로 클램프. **엄지는 어떤 프렛에도 배정되지 않음**(넥 뒤 지지 미모델링, 기타가 공간 고정이라 역할 無).
  - 전완 3-DOF = 병진 슬라이드 forearm_tx/ty/tz. tx는 **[−0.23, 0.09]** 로 오버라이드(넥 따라 이동), ty=(−0.01,0.10), tz=(−0.1,0.02).
- **오른손은 RL 아님**: `action_spec` None, `apply_action` 주석 처리. **test 모드에서만** 스크립트 궤적+IK로
  탄현 애니메이션. 학습 보상/관측/종료에 **무관**.
- 최종 왼손 action 차원 20은 감축 로직에서 **유도**된 값(코드에 명시 출력 없음) — 실행 시 `action_spec(physics).shape` 확인 권장. **[확인 필요]**

### 1-2. 운지 배정 (arrangeFinger, offline greedy)
- 시뮬레이션 **전** 타블라처 구성 단계에서 1회 실행, 결과를 `note.finger`에 저장. **글로벌 최적화 없는 그리디**.
- 상태: `fingers[5]` = 각 손가락이 자유로워지는 시각(릴리즈 타임, 초기 0), 파지위치 `handpos=P`(검지 지판 위치).
  노트를 **시작 시각 순** 정렬해 순차 배정.
- 손가락 인덱스 0..4 = [엄지, 검지, 중지, 약지, 소지]. **압현은 1~4만**(엄지 0은 프렛 미배정). 개방현(pos==0)은 finger=−1.
- 후보 비용 = `|i + handpos − 1 − pos|` (손가락 i의 자연 프렛 vs 목표 프렛 거리). **릴리즈 타임 ≤ 현재 노트 시각**인
  손가락만 후보. 자유 손가락 없으면 "not enough finger" 로깅 후 skip.
- 파지위치 갱신: `pos−handpos>4 → handpos=pos`(상향), `handpos−pos>0 → handpos=max(pos−3,1)`(하향).
- **바레/동시 노트**: 같은 시각·같은 프렛 노트 묶어, 자유 손가락 부족하면 skip; 충분하면 가까운 N개를 골라
  손가락 오름차순↔줄 내림차순(낮은 손가락 인덱스 → 높은 줄 번호)으로 배정.

### 1-3. 기타 모델 / 프렛 수식
- 상수(미터): NUM_KEYS=120, 스케일 길이 LENGTH=**0.645m**, BASE=**17.84**, MAX_FORCE=1, ACTIVATION_THRESHOLD=0.2, STRING_NUM=6.
- **120 사이트 = 20 프렛 × 6 줄**. key→string=`key%6`, fret_row=`int(key/6)`.
- **프렛 배치(평균율 "rule of 18")**: `curLi = restLength / 17.84`; `newZ = lastZ + (curLi+lastLi)/2`; 이후 `restLength −= curLi`.
  → 하드코딩 프렛 반길이 표 `LENGTH[]`(0.018077…→0.006041…, task L27-33)를 **수치적으로 재현 검증됨**.
- **줄 x좌표**: `x = 0.02 − j·0.008`(줄 8mm 간격, j=0..5 → +0.02..−0.02), 높이 y=0.013 고정. 사이트는 box, z-크기=프렛 반길이.
- 사이트마다 MuJoCo **touch 힘센서** + framepos. 키 상태 = force/MAX_FORCE, activation = state ≥ key_bound. **현 동역학은 없음**(강체 메시 조립).
- **튜닝**: STANDNAME=[E4,B3,G3,D3,A2,E2] → **줄 인덱스 0 = high E(1번줄), 5 = low E(6번줄)**. (우리 `G:string6=low-E`와 동일 규약: 인덱스 5 = low E = 6번줄.)
- 기타 OBJ 메시의 실제 미터 스케일은 명시 태그 없이 **가정**(사이트 좌표는 명백히 미터). **[확인 필요]**

### 1-4. 데이터 (타블라처 입력)
- Note = (name, time, duration, finger=−1). name = "STRING FRET"(예 "5 3" = 5번줄 3프렛, "0 0" = 쉼표).
- 내부: `keys[fret*6+string] += (time,duration,finger)`, `plucks[string] += (…)`. 코드/화음 빌더(addChord/ChordDic) 존재.
- **8곡 내장**(test_task.py idx 0-7): chord transition, little star, scales practice, Happy Birthday, long long ago, farewell(DreamingofHomeandMother), for Elise, Red River Valley. 외부 `out.txt`("string fret time duration") 로더도 있음.
- **goal 이산화**(goal.py): `totaltick=(endtime+init_buffer_time)/dt`, dt=1/30s. `goalstate[tick][key]=[active(0/1), finger]`, `pluckstate[tick][6]`, `stringstate[tick][string]=[fret+1, finger]`(기본 [20,−1]). 관측은 미래 `n_step_lookahead` 틱 노출(실행 10).

### 1-5. 스테이징 / 커리큘럼
- **코드에 없음**. 한 번에 **1곡만** 학습(table 인덱스; main은 table=8 하드코딩). 점진 난이도·다단계 스케줄 부재.
  init_buffer_time·n_step_lookahead는 존재하나 **정적**(커리큘럼 아님).
- 논문이 커리큘럼/오른손 RL을 서술하는지는 코드만으론 확정 불가 — 코드엔 커리큘럼 無, 오른손 IK뿐. **[확인 필요]**

### 1-6. 손↔기타 결합
- 기타(composer.Entity)가 **root/arena**, 두 손을 `arena.attach(hand)`로 붙임. **몸통·팔·휴머노이드 없음** —
  전완+손 어셈블리 2개가 공중에 떠 있음.
- 왼손(RL): pos≈(−0.3,−0.32,0.60), 안쪽 yaw 1.57. 오른손: pos≈(0.331,0.08,1.017), 관절 거의 동결(range≈±1e-8),
  **test 모드에서만** 스크립트 궤적(엄지=4·5·6번줄 직선, 검지중지약지=1·2·3번줄 타원호)+IK로 구동.
- **사운드는 페이크**: 줄별 눌린 최고 프렛으로 음높이 결정, 현 동역학 없음. 정상 학습 중 오른손은 사실상 정지.

---

## §2. 규칙 (rules)

**보상 조립**: 매 30Hz 제어 스텝마다 `_get_reward`(task L802-808)가 3항을 합쳐 **단일 스칼라**를 만든다.
per-step 관측용으로 `[f, e, k]` 3열을 노출하지만 이는 **로깅용**이고, `get_reward()`는 스칼라 합만 돌려준다
(우리처럼 per-string 멀티크리틱 벡터가 아님).

### 2-1. 규칙 마스터 표 (항목 | 분류 | 수식/조건 | 비고)

| 항목 | 분류 | 수식 / 조건 | 비고 |
|---|---|---|---|
| **총 보상 합성** | 보상 | `r = (1−w_k)·r_finger + r_energy + w_k·r_key`, 기본 w_k=0.5 (→ finger·key 각 0.5, energy는 위에 무가중 가산) | task L802-808. `operator='*'`(곱셈 합성) 인자는 저장되나 **미참조=dead code**. |
| **압현 보상 r_finger** | 보상 | per (key,finger): `(r_x+r_y+r_z)/3`, 필요 손가락 평균. `r_a = tolerance(\|diff_a\|, bounds, margin, sigmoid, value_at_margin=0.1)`. **z·y**: bounds=(0, finger_bound). **x**: bounds=(0, **LENGTH[fret]**)=프렛폭 의존(0.0181→0.0060). 누를 키 없으면 **1.0** | task L403-514. **축분해**(x=프렛 길이방향 관대 / y·z 수직 엄격). 커널=`self._sigmoid`(run=reciprocal). 적응형 밴드 `_reward_distance_y`(hstart=0.007, zbound=0.005)는 정의만 되고 **미호출=dead**. |
| **키압 보상 r_key** | 보상 | on키: `0.5·tolerance(force/MAX_FORCE, bounds=(key_bound,1), margin=key_margin, sigmoid="gaussian", vam=0.1).mean()` + off키: `0.5·(1 − activation[off].any())` | task L161-216. 커널 **가우시안 하드코딩**(finger의 self._sigmoid와 분리). 오누름 1개라도 있으면 뒤 항 0.5 **전부 상실**(all-or-nothing). |
| **에너지 벌점 r_energy** | 보상(≤0) | `r_energy = −flag·energy_coef·Σ actuators_power`(**왼손만**). 눌러야 할 키 없으면 flag=**2**(2배), 있으면 1 | task L218-229. 선형 벌점. energy_coef=0.005(기본)/0.0025(run). 모듈상수 `_energy_penalty_coef=0.005`는 **미참조=dead**. |
| **freedom 완화** | 보상 토글 | off(오누름 금지) 집합을 줄별 "현재 프렛보다 오른쪽(높은 프렛)"만으로 축소: `string_current[key%6][0] < key/6+1` | task L191-215. 기본 False. 근거=발음은 최고 프렛만 결정 → 낮은 프렛 허용해도 청감 무해(recall↑, precision↓). |
| **종료: 시간 초과** | 종료 | `tick_id ≥ totaltick` → 종료, **discount 유지 1.0** | task L634-635,693. `totaltick=(endtime+init_buffer_time)/dt` (goal L8). 정상 종료. |
| **종료: 오누름 조기종료** | 종료 토글 | `wrong_press_termination AND activation[should_not_press].any()` → **discount=0**, 종료 | task L647-651,695-697. 기본 False → 기본은 시간초과만 종료. **넘어짐·이탈·성공 조기종료 없음**. |
| **성공/평가 F1** | 성공판정 (로깅) | `tp=\|ons∩keys\|, fp=\|ons\keys\|, fn=\|keys\ons\|`; `P=tp/(tp+fp)`, `R=tp/(tp+fn)`, `F1=2PR/(P+R)`; init_buffer 틱 제외 | gym L182-221, task L674-685. **보상 아님**, TensorBoard 로깅 전용. 튕기지 않는 줄 오누름은 무해 → **recall이 실질 품질 지표**. |
| **key activation 판정(전제)** | 전제 | `activation[k] = (state[k] ≥ key_bound)`, `state = clip(force,0,MAX_FORCE)/MAX_FORCE` | guitar L107-118. ACTIVATION_THRESHOLD=0.2(기본), MAX_FORCE=1. |

### 2-2. 어블레이션 토글 (항목 | argparse 기본 | task 기본 | 실효)

| 토글 | argparse 기본 | task 기본 | 실효 여부 |
|---|---|---|---|
| `--disable_finger_reward` | False | False | **DEAD** — 저장만, 미참조 → finger 보상 항상 활성 |
| `--disable_energy_reward` | False | False | **DEAD** — 저장만, 미참조 → energy 벌점 항상 활성 |
| `--disable_key_reward` | False | False | **PARTIAL** — **관측만** 게이팅, 보상 합의 k항은 제거 안 됨 |
| `--wrong_press_termination` | False | False | **LIVE**(§2-1 오누름 종료) |
| `--freedom` | False | False | **LIVE**(§2-1 freedom) |
| `--sigmoid` | "gaussian" | "gaussian" | **LIVE**(finger 전용; key는 가우시안 하드코딩). 선택: reciprocal/long_tail/hyperbolic/linear/cosine/quadratic |
| `--rightKey_weight` | 0.5 | 0.5 | **LIVE** — finger vs key 분배 |
| `--finger_bound / --finger_margin` | 0.01 / 0.1 | 0.01 / 0.1 | **LIVE** — finger z·y 허용/마진 |
| `--key_bound / --key_margin` | 0.01 / 0.01 | 0.2 / 0.2 | **LIVE** — activation 임계 + key tolerance 하한/마진 겸함 |
| `--energy_coef` | 0.005 | 0.005 | **LIVE** |
| `--init_buffer_time` | 1s | 0 | **LIVE** — 워밍업 무음, F1 집계 제외 |
| `--n_step_lookahead` | 10 | 1 | **LIVE** — 관측 룩어헤드(보상 무관) |
| `--operator` | '+' | '+' | **DEAD** — 미참조 |

> **주의(3항 어블레이션 함정)**: 논문이 보고하는 "finger/energy 보상 제거" 어블레이션과 달리, 코드의 disable
> 토글 3개 중 2개는 **런타임 효과가 전혀 없다**. 논문 수치는 다른/이전 코드 경로였을 가능성 — 코드만으론 1:1 매핑 불가. **[확인 필요]**

### 2-3. 실행 config(main→train(args[25]))의 보상 값
`rightKey_weight=0.5, key_bound=1, key_margin=1, finger_bound=0.001, finger_margin=0.1, energy_coef=0.0025, sigmoid='reciprocal'`.
- **degenerate 경고**: `key_bound=1` → activation이 force≥MAX_FORCE(=1)를 요구하고 key tolerance는 bounds=(1,1).
  코드 그대로 충실히 보고하되, **의도인지 잔재인지 코드만으론 판정 불가**. **[확인 필요]**

---

## §3. 환경 (environment)

### 3-0. 한 장 요약
MuJoCo 3.1.4 + dm_control composer 위에서 gymnasium으로 래핑, **off-policy DroQ**(sbx/JAX, SAC+Dropout-Q, MlpPolicy)로
학습. 정책은 **왼손 20-DOF만** 제어, 관측 **246차원**·행동 **20차원**(둘 다 float64 Box). 물리 300Hz/제어
30Hz(decimation 10). 실행 config는 **n_env=4 SubprocVecEnv, γ=0.84, batch 512, total 1e7 step**.

### 3-1. 알고리즘 — DroQ (off-policy)
- `from sbx import DroQ`. 의존: `sbx-rl 0.12.0, stable-baselines3 2.3.0, jax 0.4.26, flax 0.8.2`(JAX 백엔드, CUDA 12.4).
- 생성: `DroQ("MlpPolicy", env, gradient_steps=-1, batch_size=512, learning_rate=3e-4, learning_starts=50000, dropout_rate=0.01, buffer_size=1e6, gamma=0.84)`.
- `gradient_steps=-1` → 롤아웃 env-step 수만큼 gradient step(SB3 규약). 탐험: `NormalActionNoise(0, 0.1)`(use_noise=True).
- **DroQ 고유 계수(net_arch, n_critics, policy_delay/UTD, tau, ent_coef auto, layer_norm, train_freq)** 는 코드에
  명시 없음 → sbx 0.12.0 내부 기본값. 이 환경에 sbx 미설치라 소스 확인 불가. **[확인 필요]**

### 3-2. 네트워크 / 정책
- `"MlpPolicy"`. policy_kwargs·net_arch·activation 미지정 → sbx DroQ 기본값(코드로 확인 불가). **[확인 필요]**
- 액션 rescale: 정책 출력 [−1,1]²⁰ → `action·ac_power + ac_center`로 액추에이터 ctrlrange 매핑(gym L170).

### 3-3. 하이퍼파라미터 (항목 | 값 | 근거/비고)

| 항목 | 값 | 근거 / 비고 |
|---|---|---|
| 알고리즘 | DroQ (sbx/JAX) | off-policy, SAC+Dropout-Q |
| `gamma` | **0.84** | arg 기본 0.99 무시, train/test 모두 오버라이드(train L391). 논문: "현재 노트가 보상 지배 → 높은 discount 불필요" |
| `batch_size` | 512 | args[25] |
| `learning_rate` | 3e-4 (상수) | linear schedule 미사용 |
| `dropout_rate` | 0.01 | |
| `buffer_size` | 1e6 | |
| `learning_starts` | 50000 | |
| `gradient_steps` | −1 | 하드코딩(롤아웃 step 수만큼) |
| `seed` | 42 | |
| action noise σ | 0.1 | use_noise=True |
| `total_timesteps` | **1e7** | args[25]. 논문은 "곡당 5e6, 6h"(불일치, **[확인 필요]**) |
| n_env | **4** (SubprocVecEnv) | CPU 소수 병렬 |
| n_step_lookahead | 10 | 관측 룩어헤드 |
| init_buffer_time | 1s | 워밍업 30틱(F1 제외) |

### 3-4. 시뮬레이션
- 엔진: MuJoCo 3.1.4 via `composer.Environment(task, RandomState(42))`. dm-control 1.0.18.
- 주파수(base L11-16): `_FRAME_RATE=30` → physics 1/300s(300Hz), control 1/30s(30Hz), **decimation=substeps=10**.
- 접촉: `default.geom.solref=(physics_timestep·2, 1)`.
- 병렬: n_env=4 SubprocVecEnv. 에피소드 길이 = totaltick(곡 endtime 의존).
- **제어 대상 = 왼손만**: action_spec은 left_hand만, before_step은 left_hand.apply_action만. 오른손은 test 모드 IK(학습 무관).

### 3-5. 관측 / 행동 / 보상 (type · shape)

**Observation** — `Box(−inf, inf, shape=(246,), dtype=float64)` (gym L119). 시퀀스
`['goal','last_state','state','lh_shadow_hand/joints_pos']`, 실행 기본(n_step_lookahead=10, normalization=True) 기준 **246 = 81 + 21 + 120 + 24**:

| 블록 | 차원 | 내용 |
|---|---|---|
| goal | 81 | string goal 66 = `(n_look+1)×6 = 11×6`(정규화) + fingstate 15 = 5손가락 × (x,y,z) 목표 키 위치 |
| last_state | 21 | 직전 action 20 + 직전 reward 1 |
| state | 120 | 기타 키 힘 상태 `clip(force,0,MAX_FORCE)/MAX_FORCE`, NUM_KEYS=120 |
| lh joints_pos | 24 | 왼손 관절 qpos (커플드 J0로 관절 24 > 액추에이터 20) |

> 246은 실행 config 전용 값. n_step_lookahead·STRINGSTATE·normalization을 바꾸면 goal 차원이 변한다(STRINGSTATE=0이면 goal이 NUM_KEYS 기반 (n+1)×120으로 급증). **[확인 필요]**

**Action** — `Box(−1, 1, shape=(20,), dtype=float64)` (gym L121). 20 = 왼손 액추에이터 17(감축) + 전완 슬라이드 3.

**Reward** — **스칼라**(task L700-702). `r = f_reward + e_reward + k_reward`(=(1−w)·finger + energy + w·key). per-step 관측엔
`np.array([f,e,k])` 3열이 실리지만 로깅/관측용이고, 학습 보상은 스칼라. info의 F1/precision/recall은 평가 전용.

**step 반환** — `(obs, reward, terminated, False, info)` gymnasium 5-튜플, **truncated 항상 False**. terminated = tick ≥ totaltick.

---

## §4. 우리(tab2body)와의 대조

### 4-1. 근본 차이 (축 | GPS | 우리 | 함의)

| 축 | GPS | 우리 (tab2body) | 함의 |
|---|---|---|---|
| RL 알고리즘 | **DroQ**(off-policy, SAC+Dropout-Q, sbx/JAX) | **멀티크리틱 PPO**(on-policy, Isaac Gym) | 리플레이버퍼 vs 대규모 병렬 롤아웃 |
| 병렬 폭 | n_env=**4**(SubprocVecEnv, CPU) | num_envs=**512**(GPU) | 소수 env off-policy ↔ 수백 env on-policy |
| 제어 부위 | **왼손 20-DOF만**(오른손 IK 스크립트) | **전신** act 42/33/75 (몸통+팔+손) | 손만 ↔ 전신 물리 |
| 몸·팔 | **없음**(공간 고정 기타 + 플로팅 손) | SMPL 전신 좌식 연주 | reach·팔 모션·자세 사실성은 우리만의 과제 |
| 보상 구조 | **단일 스칼라**(f+e+k), [f,e,k]는 로깅용 | **per-string 6채널 멀티크리틱** + DiagonalPopArt | 스칼라 합 ↔ 열벡터 + 헤드별 정규화 |
| 운지 | 오프라인 **그리디** arrangeFinger, 보상은 손가락 특정 | fingermapping **명시 운지**, 보상은 지정 손가락 | 둘 다 "명시"지만 배정 알고리즘·합법성 보장이 다름 |
| discount γ | **0.84**(고정) | 0.95(기본), 0.84는 recall 정체 시 노브 | GPS 근거를 우리가 튜닝 후보로 인용 |
| 오른손/타현 | IK 궤적(학습 X, test 전용, 현 동역학 없음) | strike 태스크로 **RL 학습**(rew_dim 1 또는 6) | 우리는 타현도 물리+학습 |
| 종료 | 시간초과(+옵션 오누름) | R6·R7·R8·R13·R14 다중 종료 + −25 broadcast | 우리 안전/사실성 종료가 훨씬 두꺼움 |
| 커널 분리 | finger=self._sigmoid(reciprocal), key=gaussian 하드코딩 | fret은 듀얼스케일 가우시안 `clip(0.8·e^(−1000d²)+0.2·e^(−30d²),0,1)` | 우리는 Xu 듀얼스케일 유지 + GPS 축분해 교훈 반영 |

### 4-2. 우리가 빌려온 것 (이미 PROJECT_CONTEXT / task_fret_plan 인용)
- **프렛 수식(rule of 18)** — `curLi = restLength/17.84`, 스케일 0.645m. 우리 압점 기하의 근거(§1-3).
- **reciprocal 커널** — 미세 이동 민감 → 가우시안 대비 수렴↑(task_fret_plan.md:106). GPS main config가 reciprocal.
- **축분해 finger reward** — 유클리드 단일거리는 F1≈0.6 정체, x(프렛 길이방향) 관대 / y·z 엄격으로 대폭 개선.
  우리는 Xu 듀얼스케일 유지하되 **"유클리드 단일거리 금지"** 교훈 채택(task_fret_plan.md:28,285).
- **freedom 완화** — 목표보다 높은 프렛만 금지(낮은 프렛 허용). 우리는 Xu의 max-fret 내장 방식과 대비해 인용(:106).
- **γ=0.84** — 짧은 지평 recall↑ 노브로 인용(:106). 우리 기본은 0.95, 정체 시 GPS 값 참조.
- **idle 에너지 2배** — 눌러야 할 키 없을 때 flag=2. 우리 R17(idle 에너지)의 직접 근거(:62).
- **어블레이션 토글** — sigmoid/rightKey_weight/finger_bound/energy_coef 스윕 구조를 우리 스윕 설계 참고.
- **finger goal 15-dim 관측** — 5손가락 목표 키 위치. 우리 goal 인코딩에 finger 채널 추가의 선례(:62,106).

### 4-3. 우리가 명시적으로 **안** 가져오는 것
- **DroQ**(결정 #9, 이름으로 기각) — off-policy·CPU·소수 env·리플레이 버퍼는 우리 GPU 대규모 병렬 on-policy와 반대.
  **논문 결함이 아니라 하드웨어 구조 차이가 근거**(learning_env_design.md:27).
- **단일 스칼라 보상** — 우리는 줄별 스케일/희소도 차이 때문에 멀티크리틱(6채널) 채택.
- **오른손 IK 스크립트** — 우리는 타현도 물리 RL(strike 태스크).

---

## §5. 참고

**경로 접두** `related_work/GPS/guitarplay/` 생략. 라인은 조사 시점 기준(이식 전 재확인 권장).

| 약칭 | 파일 | 주요 라인 |
|---|---|---|
| task | `suite/tasks/guitar_task_withhands.py` | 보상 합성 L802-808 · key L161-216 · finger L403-514 · energy L218-229 · 종료 L634-651,691-698 · F1 L674-685 · fret LENGTH[] L27-33 · 튜닝 L23-25 · 오른손 IK L231-401 |
| gym | `example/envs/guitar_gym_env.py` | Box obs L119 · action L121 · sequence L16-23 · step/F1 L182-221 · rescale L170 |
| guitar | `modelpy/guitar/guitar.py` | createSites/fret math L20-43 · 센서 L49-57 · state/activation L107-118 |
| gconst | `modelpy/guitar/guitar_constants.py` | NUM_KEYS·LENGTH·BASE·MAX_FORCE·ACTIVATION_THRESHOLD |
| base | `suite/tasks/base.py` | 주파수 L11-16 · set_timesteps L48 · attach hands L137-235 · forearm_tx 오버라이드 L148 |
| hand | `modelpy/hands/shadow_hand.py` | 감축 L86-90,184-207 · forearm dofs L56-99,299-338 · power L437-446 |
| handconst | `modelpy/hands/shadow_hand_constants.py` | NQ=24·NU=20·JOINT_GROUP·FINGERTIP_BODIES |
| handR | `modelpy/hands/shadow_hand_R.py` | 오른손 action None L319-332 |
| tab | `music/tablature.py` | arrangeFinger L122-228 · notesToState L34-46 |
| goal | `music/goal.py` | totaltick L8 · goalstate/pluck/string L13-43 |
| train | `train_guitar.py` | DroQ 생성 L194-202 · args 스윕 L343-372 · args[25] L369 · train(a) 오버라이드 L379-402 · γ=0.84 L391 |
| testtask | `suite/tasks/test_task.py` | 8곡 내장 L918-926 · 외부 로더 L963-988 |

**논문**: `docs/GPS-paper-ko.md` (Luo et al., CGF'24/SCA'24, DOI 10.1111/cgf.15166). 운지 §4 / 프레팅 RL §5 / 탄현 IK §6 /
정량 결과·어블레이션 §7-8 / 한계 §한계. 주요 정량치(Für Elise recall≈0.58, Red River Valley F1≈0.75 등)는 논문 그림
육안 근사값이라 소수점 신뢰 불가. **[확인 필요]**

**미해결(코드/논문 대조 필요)**: ① step 수 논문 5e6 vs 코드 1e7 불일치 · ② `tolerance()` 커널 폐형식은 dm_control
라이브러리 표준으로 가정(레포 내 rewards.py 미독) · ③ key_bound=1 축퇴가 의도인지 잔재인지 · ④ disable 토글 3개 중
2개 무효 → 논문 어블레이션과 코드 경로 매핑 불가 · ⑤ DroQ 내부 기본값(net_arch·n_critics·UTD·tau·train_freq).
