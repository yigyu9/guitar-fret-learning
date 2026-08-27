# guitar (Pei Xu SA24 dual-hand) 분석 — 규칙·환경·구성 (우리 이식원본)

> 출처=related_work/guitar 코드 + docs/guitar-paper-ko.md. 최종 2026-07-17. **우리 tab2body의 직접 이식원본.**
>
> Xu & Wang(SIGGRAPH Asia 2024)의 물리 기반 양손 기타 연주 RL을 **우리 tab2body 문서와 같은 틀**
> (§규칙=`task_*_design.md`, §환경=`learning_env_design.md`, 형제 분석서=`related_work_analysis/GPS.md`)로
> 재정리한 분석서. GPS가 "규칙·수식 도너"인 것과 달리, **guitar는 우리가 코드를 직접 포팅해 오는 원본**
> (`learning_env_design.md`가 모든 수치의 출처로 지목)이다. 각 값은 `related_work/guitar/{env.py, main.py,
> models.py, utils.py}` + `cfg/{left_demo, right, two_demo}.py` 실측 + 논문 요약(`docs/guitar-paper-ko.md`)에서
> 왔고, 코드로 단정할 수 없는 값은 **확인 필요**로 표기했다. 파일:라인은 §5에 모았다(경로 접두 `related_work/guitar/` 생략).
> 표기: **[코드]**=guitar 코드 실측 · **[논문]**=논문 서술 · **[확인 필요]**=코드/논문 대조 미완 또는 XML 미검증.

---

## §0. 개요

- **한 줄 정의**: guitar = **모캡 스타일 분포(ICCGAN/AMP)를 모방하며 타블라처 goal을 따라 물리 손이 기타를 연주하도록 멀티크리틱 PPO로 학습**하는 시스템. 과제를 ① 왼손(프레팅) · ② 오른손(피킹)으로 **분리 학습**한 뒤, 두 정책을 얼리고 잠재공간 오프셋만 배우는 **synchronizer(AdaptNet)**로 특정 곡에 시간동기 결합한다.
- **물리·학습 범위**: 각 손은 **27-DOF 플로팅 손목 모델**(손목 6-DOF + 손가락 21). 기타는 **월드 고정·중력 off**, 손만 떠 있고 **몸통·팔·어깨는 없다**. 보상은 GPS의 단일 스칼라와 달리 **per-string 6채널(왼손) 멀티크리틱 + 판별자 스타일 보상 열**이다. Isaac Gym에서 num_envs=512·60Hz로 돈다.
- **우리(tab2body)와의 관계**: guitar는 **직접 이식 대상**이다 — `learning_env_design.md`는 num_envs·horizon·γ=λ·lr·PopArt·듀얼스케일 커널·goal 기계·60Hz를 전부 guitar `main.py/models.py/env.py`에서 실측했다고 명시한다(**[G]** 마킹). 우리는 이 스택을 대부분 **그대로 이식**하되 ① 손만→**전신**(act_dim 42/33/75), ② 암묵 운지→**명시 운지**(fingermapping finger 라벨, 결정 #12), ③ **disable_gravity 끔**, ④ **GRU 제거**, ⑤ 커리큘럼 신설로 **적응**하고, ⑥ 쿼터니언 conjugation 버그(L880-884)는 전신이라 **기각(수정 필수)**한다(§4).

---

## §1. 구성 (configuration)

### 1-1. 태스크 클래스 분해 (env.py)

상속 사슬: `Env`(L27) → `ICCGANHumanoid`(L446) → `ICCGANHandBase`(L920) → {`ICCGANLeftHand`(L1352), `ICCGANRightHand`(L1733), `ICCGANTwoHands`(L2089)}.

- **`ICCGANHandBase`** = 모든 손이 공유하는 **노트/goal 기계**(노트 로딩·윈도 샘플링·타이머·goal 윈도 시프트). 서브클래스는 `get_goal_dim`·`create_tensors`·`update_goal_tensor`·`observe_goal`·`reward`·`termination_check`만 오버라이드.
- **LEFT(1352, 프레팅)**: `reward()` = **N×6**(줄별 크리틱 6개). 줄별 goal ∈ {**>0**=해당 프렛 눌러라 / **0**=don't-care / **−1**=누르지 마(뮤트)}. 보상 기하 = 손가락 세그먼트↔(줄,프렛) 압점 거리 + press/not-press exp 커널(`_reward` L1526-1687). 클래스 속성 `GOAL_REWARD_WEIGHT=0.8`(L1354)이나 cfg `goal_reward_weight=[0.15]×6`에 **오버라이드됨**.
- **RIGHT(1733, 피킹)**: `random_pitch_rate=0` 강제(L1736). `get_goal_dim`이 **튜플 `(35, 41)`** 반환(actor 35 / critic 35+6, 추가 6 = 줄별 `pluck_correct` 플래그, L1739-1741). `reward()` = **N×1**(단일 크리틱). 보상 = 픽 궤적↔줄 선분 교차 판정(`_reward` L1926-2069).
- **TWO(2089, 동기화)**: `CHARACTER_MODEL=["assets/left_hand_guitar.xml","right_hand.xml"]`(왼손 모델이 기타를 지님, 오른손은 맨손). `get_goal_dim`= 단일 정수 **76** = (n_strings+1)·goal_horizon·2 + 6. `create_tensors`가 좌·우 텐서 **둘 다** 생성(L2097-2098). `update_goal_tensor`는 양손 시프트를 병합하고, 오른손 피킹 goal을 왼손 프렛 goal에서 유도하되 left-only 노트(hammer/pull/tied)를 `tar_effect//100 %2`로 걸러 제거(L2136-2147). `reward()`(L2185-2201)는 `ready` 게이트로 rew_l→rew_r 계산 후 **cat → N×7**. `_reward`/`_termination_check`/`_init_obj_tensors`는 `@staticmethod`라 TwoHands가 자기 `self`에 재사용.

### 1-2. 손 캐릭터 모델 · DOF · act_dim

- 각 손 XML(left_hand_guitar.xml / right_hand.xml / right_hand_guitar.xml)은 **실 DOF 27개 → act_dim=27** **[코드]**(pretrained `actor.mu.bias`=27, `meta1/meta2.mu.bias`=27로 확정). `<joint>` 태그는 28개지만 1개는 `<default>` 블록 내부.
- **손목 = 6-DOF 플로팅**: 슬라이드 3(`wrist_dx/dy/dz`) + 힌지 3(`wrist_x/y/z`). 나머지 **21 DOF = 5손가락**. (손가락별 2-DOF/1-DOF 분해는 XML 미열람 **[확인 필요]**.)
- 제어 = `control_mode="position"` → `DOF_MODE_POS`. 정규화 action ±0.5 → 관절 [lower,upper]로 매핑(`process_actions`, action_offset=center, action_scale=upper−lower).
- **프레임당 policy state_dim = 208** = key_links 16 × 13(pos3+quat4+linvel3+angvel3). 16 key_links = 손목 + 5손가락×3관절. **OB_HORIZON=2**(L939; base Env 기본은 4/L457, 손 클래스가 2로 오버라이드).
- 손별 **독립 ACModel**(§3-2). `value_dim = 판별자수 + rew_dim`: LEFT **2+6=8** · RIGHT **1+1=2** · TWO **2+7=9**(멀티크리틱, main.py:448).

### 1-3. goal 기계 (`ICCGANHandBase`)

- 클래스 상수: `N_STRINGS=6` · `N_FRETS=22` · `GOAL_SAMPLING_RANGE=(10,20)`노트 · `GOAL_HORIZON=5`(룩어헤드) · `GRACE_PERIOD=5`빈프레임 · `OB_HORIZON=2` · `ENABLE_GOAL_TIMER=True`. 시뮬 fps=60·substeps=4·frameskip=1(L965-967).
- **goal_dim**: LEFT=(n_strings+1)·goal_horizon = 7×5 = **35** · RIGHT=**(35,41)** · TWO=**76**. `goal_tensor_dim` = n_strings·goal_horizon = 30(L972-975). (pretrained `embed_goal.0.weight`=(256,35)로 35 확정 **[코드]**.)
- **`load_notes`(L1045-1234)**: 곡 JSON을 트랙별 파싱, 노트당 6프렛 검증, 4프렛 초과/4압현 초과 화음은 축소, 노트 길이 "t"를 1/64 기반 정수 간격으로 변환, 이펙트를 `100·(2^coeff)·flag`로 인코딩(effect_names=`["tied","hammer/pull","chords"]`, `chords`는 −1 슬롯을 프렛으로 채움). **왼손 매핑**: 원시 프렛 −1→0(don't-care), 0→−1(누르지마), >0 유지(L1143-1148). `note_frames_per_tbpm = 60·fps/16 = 225`.
- **`reset_goal`(L1236)**: 노트수 가중 `multinomial`로 트랙 샘플, `random_note_sampling`이면 [10,20) 노트 윈도를 랜덤 위상에서 절취; per-note 프레임 [5,50] 클립; timer=윈도 노트 프레임 합−룩어헤드. 재시작 시 5-노트 룩어헤드를 `update_goal_tensor` 4회 호출로 선충전(L1322-1324).
- **`update_goal_tensor`**: `goal_t[:,0]` 감소 → ≤0이면 `goal_cursor` 전진, 지평 윈도 시프트(가장 오래된 노트 폐기·`goal_track[cursor]` 추가), pitch adjust 적용.
- **`observe_goal`**(LEFT L1420): 프렛 `/(n_frets+2)·2` 스케일 후 값>1은 음수로 랩(−1/0/+fret를 한 채널로 인코딩); 타이머 `(t/20).clip(max=2)−1`; concat → 35차원. RIGHT는 `pluck_correct` 6열 추가. TWO는 [left 35][right 35][pluck 6]=76.

### 1-4. 데이터 (2개의 분리된 스트림)

- **노트 타깃(태스크 goal)**: `assets/notes/*.json`, **20곡**. 형식 = 트랙 리스트; 트랙={`tempo`:BPM, `notes`:리스트}; 노트={`t`:길이, `effects`:dict, `frets`:[6 ints]}. 원시 프렛 −1=현 미포함/0=개방현/>0=프렛. 관측 이펙트 키 = `chords`·`hammer/pull`·`tied`(각 6줄 리스트).
- **손 모캡(ICCGAN 판별자 스타일 타깃)**: `assets/motions/scale.json`(16MB) · `strum.json`(492KB, fps=120). 형식={`fps`, `frames`}; 프레임=관절명→값(병진 `*_dx/dy/dz`→3벡터, 회전→쿼터니언4). yaml 선택: `left_hand_motions.yaml`→scale.json; `right_hand_motions.yaml`→scale.json+strum.json. **노트 JSON과 완전 별개.**
- **pretrained/**: 곡당 체크포인트 20개(각 30MB, TwoHands AdaptNet 전체 meta1+meta2 내장) + 범용 `right_hand` 1개(9MB 단일 ACModel).

### 1-5. AdaptNet 결합 (models.py L288-378)

- main.py L529 배선: `model.actor = AdaptNet(model, left_policy, right_policy)`(meta1=왼손, meta2=오른손). 좌/우 actor는 각 ckpt에서 로드.
- **두 meta 정책 동결(sigma만 예외)**: `"sigma" not in name`인 파라미터만 `requires_grad=False`(L327-332). → 사전학습 정책은 잠기지만 **log_sigma는 학습 유지**(논문 "완전 잠금"과 상이, **[확인 필요]** §5).
- **잔차 주입**: 각 손에 대해 학습 가능 사본(`rnn1/embed_goal1` 등, meta에서 deepcopy)의 latent를 concat → 학습 `embed` MLP(**마지막 층 0-초기화**, L324-325 → AdaptNet은 항등에서 출발); 출력 z를 각 동결 meta의 `rnn+embed_goal`에 **잔차로 가산** 후 동결 mlp/mu/log_sigma 통과. 최종 action = Normal(cat(mu1,mu2), cat(sigma1,sigma2)) → **54차원**(27+27).
- ob_normalizer = 두 손 208 통계 concat → **416**(pretrained `ob_normalizer.mean`=416로 확정 **[코드]**). forward에서 goal 분할 g1=g[:35], g2=g[35:70], 뒤 6(pluck_correct)은 AdaptNet g_dim=0이라 드롭.
- main.py L528: two-hands 실행 시 `env.reward_weights *= 2`(단일손 학습과 스케일 일치, grad clip 덕에 trivial).

### 1-6. 커리큘럼 (없음)

- **다단계 커리큘럼 없음.** `reset_goal`의 랜덤 샘플링/증강만 존재: 랜덤 트랙(노트수 가중) · 랜덤 윈도 10-20 노트 · 랜덤 시작 위상 · `random_pitch_rate`(기본 0.5) · `random_bpm_rate`(기본 0.5, ±20BPM/80-190밴드) · `merge_repeated_notes`(기본 True).
- **주의**: `left_demo.py`·`two_demo.py`는 이들을 **끈다**(pitch/bpm rate=0, merge=False). RIGHT는 `note_file=[]`로 `reset_goal_random`(하드코딩 코드/줄 패턴 21종, per-note dt [5,45)). 테스트 시 `random_note_sampling=False`로 곡 전체를 순차 재생. 에피소드 길이: left 600 · right 600 · two 1200(테스트 500000).

### 1-7. 기타 처리 (월드 고정)

- **월드 고정·무중력**: `create_envs`(L982-989)가 `fix_base_link=True, disable_gravity=True, thickness=0.0003`; `add_actor`는 shape별 `contact_offset=0.0001`; `max_depenetration_velocity=1`(손 오버라이드).
- 기타 바디 "guitar"; 줄 `G:string1..6`(+`_end`), 프렛 `G:nut`+`G:fret1..22`, `G:pluck_range`·`G:pick`. **모든 손/보상 기하는 기타 로컬 프레임**(`quatconj(guitar_orient)`)에서 계산.
- `parent_link="guitar"`로 주 관측/판별자가 기타 상대. **알려진 무해 버그(L880-884)**: parent-relative 관측이 `orient_inv` 대신 `orient`를 씀 — guitar가 월드 고정이라 안전, **기타가 움직이면 깨짐**(→ §4 우리 전신 이식의 필수 수정점).

---

## §2. 규칙 (rules)

**전역 상수(env.py)**: N_STRINGS=6(L933) · N_FRETS=22(L934) · GRACE_PERIOD=5(L943) · GOAL_HORIZON=5(L941). `rew_dim`은 런타임에 `reward().size(-1)`로 추론(L102). **모든 거리 함수는 제곱거리(d²)를 반환**(utils.py `dist2_p2seg_`/`closest_seg2seg_` L115-127) → 아래 모든 exp/임계 상수는 **d²(m²)에 곱해진다**(유효 폭 mm은 sqrt 필요). `terminate_reward=−25`는 main.py:272 적용.

### 2-1. 왼손 per-string 6채널 보상 마스터 표 (`_reward` L1526-1687, 출력 N×6)

| 항목 | 분류 | 수식 / 조건 | 비고 |
|---|---|---|---|
| **압점 기하** | 보상(기하) | `t=linspace(0.3, 0.02·n_frets+0.3, n_frets).clip(max=0.5)`; `fret_pos_target=(1−t)·fret[i]+t·fret[i−1]` | L1485-1488. 압점 = 와이어에서 너트쪽 t 비율(fret1→0.30, +0.02/fret, fret≳10에서 0.50 포화). **30~50% 가변**(35% 고정 아님). |
| **압현 커널(듀얼스케일)** | 보상 | `rew_press = clip(0.8·exp(−1000·d²)+0.2·exp(−30·d²), 0, 1)`, d²=`dist2fret_min`(허용 프렛/손가락 마스크된 세그↔압점 min 제곱거리) | L1657-1658. Sharp(1000)·0.8 + Broad(30)·0.2. 논문 식4와 **정확 일치**. |
| **not-press 커널(7mm)** | 보상 | `rew_not_press = clip((dist2string_min/0.000049)², 0, 1)` = `clip((d/7mm)⁴, 0, 1)` | L1666. `dist2string_min`이 이미 제곱거리라 결과는 (d/0.007)**⁴**. 논문 식5는 (d/0.007)² — **paper↔code 불일치**(§5). |
| **goal 의미** | 전제 | `m_tar`=goal>0(눌러라) · `m_notar`=(goal==−1)&has_goal(뮤트) · `m_nogoal`=goal==0(don't-care) | L1578,1661,1662. |
| **합성** | 보상 | `rew_tar = rew_press·m_tar + rew_not_press·m_notar + m_nogoal·(0.9 + 0.1·rew_not_press)` | L1670. don't-care는 0.9 기본 + 이격 최대 0.1. |
| **all-correct 보너스** | 보상 | `rew_correct = all(press==goal.clip(min=0) OR m_nogoal)`; `rew_tar = 0.8·rew_tar + 0.2·rew_correct` | L1668,1671. 볼록결합(가산 아님), 전 줄 공통 스칼라 브로드캐스트. 논문 식7. |
| **has_goal 게이트** | 보상 | `rew = where(has_goal, rew_tar, rew_not_press)` | L1673. 손 전체에 타깃 없으면 not-press로. |
| **부드러움 보너스** | 보상 | `rew += 0.05·exp(−50·fps·(dw + 0.1·df)²)` (dw=손목 변위, df=손끝 변위 손목로컬) | L1675-1686. 전 줄 채널에 가산. 논문 식8. |
| **세로손가락 실격** | 보상 마스크 | `invalid = (fj1.z − fj0.z)/finger_len > 0.0872`(≈sin5°); 실격 세그 dist²=+inf | L1542-1545. 끝마디(idx2) 면제, 세그 0·1만. 코드값 **0.0872**이나 주석은 "10 degrees"(0.1736), **불일치**(§5). |
| **press 검출(6.3mm)** | 판정 전제 | `pressed_string = dist2string < 0.00004`(제곱, sqrt=6.32mm) AND `finger_over_fret`(y가 두 프렛 와이어 사이) → 최고 프렛 승 | L1562-1566. `info["press"]`(N×6). |
| **홀드 정확도(½)** | 통계 | press를 `goal_orig_t2 = 0.5·note_duration_frames` 이상 유지해야 accuracy/precision/recall 집계 | L1584,1608. 코드=½, 논문 §6.1="2/3" **불일치**(§5). |

### 2-2. 오른손 피킹 보상 (`_reward` L1926-2069, 출력 N×1)

| 항목 | 분류 | 수식 / 조건 | 비고 |
|---|---|---|---|
| **피킹 판정(선분교차)** | 판정 | 픽 궤적(현재 vs 직전 픽) ↔ 줄의 line-line 교차; `plucking=(0<t<1)&(z<zs)`; `plucking_valid`=교차&(z<zs−depth), depth=0.001(training) | L1949-1972. |
| **근접 커널(듀얼스케일)** | 보상 | `rew2str = 0.35·exp(−10000·d²)+0.05·exp(−2000·d²)` | L1990-1991. |
| **줄위 커널** | 보상 | `dist2str_z=(clip(zs+0.003−z, min=0)+|dist2str_h|)²`; `rew2str_z = 0.175·exp(−10000·dz²)+0.025·exp(−2000·dz²)` | L1997-1998. 논문 식12. |
| **no-target 이격(3mm)** | 보상 | `rew_no_tar = clip(sqrt(min d²)/0.003, 0, 1)`; 정제 `0.4·rew_no_tar + (0.6/n)·Σpluck_correct + 0.5·all(pluck_correct)` | L1994-1995,2013. 논문 식13. |
| **가속 벌점** | 보상(≤0) | `rew −= (lifetime>2)·clip(rew_a,max=1)·0.7`, rew_a=픽 가속도 제곱항 | L2018-2020. |
| **픽 속도 부드러움** | 보상 | `+0.05·exp(−20·fps²·|Δpick|²)` | L2022. 논문 식16. |
| **손목/관절 속도** | 보상 | `+0.05·exp(−120·wrist_v2)` + `0.05·exp(−50·joint_v2)`(v2는 fps² 스케일) | L2024-2027. |
| **픽 쥐기 보너스** | 보상 | `+0.05 if thumb3 접촉 ∧ (index2∨index3 접촉)` | L2028-2032. 논문 식15. |
| **pluck_range 가드** | 보상(≤0) | `rew −= 1 if 픽 바디가 G:pluck_range 접촉 & lifetime>4` | L2034-2035. |

### 2-3. 양손 결합 보상 cat(6,1)=7 (`reward` L2185-2201)

- `rew_l` = LeftHand._reward → N×6. 오른손 **ready 게이트**(L2195-2199): `pressed`=(press==goal_left·(goal_left>0)) ∨ (goal_left==0) ∨ ~goal_right; `timer`=(goal_t[:,0]≤3) ∨ (goal_t_≥5); `ready = pressed ∨ timer`(왼손이 눌렀거나 노트 임박해야 오른손이 튕김 — 협력 조건). `rew_r` = RightHand._reward(…, ready) → N×1. 반환 `cat((rew_l, rew_r), −1)` → **N×7**(채널 0-5=줄별 프렛, 채널 6=피킹). **타이머 예외는 논문에 없는 구현 디테일** **[확인 필요]**.

### 2-4. 종료 조건

| 대상 | 조건 | 근거 |
|---|---|---|
| **LEFT** | too_far1(손목 x<−0.1\|>0.3, y<−0.3\|>0.3, z<−0.2\|>0.05) ∨ too_far2(손가락 관절 z<−0.07) ∨ under_fretboard(12점 중 \|x\|<0.028 & z<0) ∨ too_far3(thumb_top x>0.07), 모두 lifetime>4 게이트 | L1443-1469 |
| **RIGHT** | 손가락 관절(손목 포함) x<−0.3\|>0.3, y<−0.6\|>0, z<−0.1\|>0.3, lifetime>4 | L1886-1895 |
| **TWO** | OR(left, right) | L2182-2183 |
| **공통** | 종료 시 보상 = `terminate_reward = −25`(전 열 broadcast) | main.py:272 |

### 2-5. 판별자 (AMP/ICCGAN, WGAN-GP hinge)

- **관측** `observe_iccgan`(L838-913, disc는 include_velocity=False): key_link별 상대 위치(3)+상대 방향 쿼터니언(4)=**7차원**/링크. 프레임수=ob_horizon+1.
- **학습 손실**(main.py L220-238): `loss_r=relu(1−score_r).mean` · `loss_f=relu(1+score_f).mean` · `gp=(‖∇_interp score‖₂−1)².mean` · `l = loss_f + loss_r + 10·gp`(GP 계수 10).
- **보상**(main.py L257-259): `r = disc(ob).clamp(−1,1).mean(−1, keepdim=True)`.
- **구성**: LEFT = 판별자 **2개**(`LH/wrist`=손목+엄지1-3/parent=guitar, `LH/fingers`=검지·중지·약지·소지1-3/parent=LH:wrist). RIGHT = **1개**(`RH/hand`=손목+전손가락/parent=guitar). TWO = LH/wrist+LH/fingers(각 weight=0.05, RH/hand 주석처리).

### 2-6. reward_weights 조립 (env.py L493-568)

task 열은 cfg `goal_reward_weight`로, 판별자 열은 미지정 시 잔여 질량 균등분배. `rew_dim>1`이면 disc 가중 ×(1−task합), task 가중은 마지막 rew_dim 슬롯 → **disc+task 합=1**. 각 열은 독립 크리틱(`multi_critics = reward_weights.size>1`, main.py:111).

| 태스크 | reward_weights 벡터 | disc 합 / task 합 | value_dim |
|---|---|---|---|
| **LEFT** (`[0.15]×6`, disc 2 미지정) | `[0.05, 0.05 \| 0.15×6]` | 0.1 / 0.9 | 8 |
| **RIGHT** (`0.5` 스칼라, disc 1) | `[0.5 \| 0.5]` | 0.5 / 0.5 | 2 |
| **TWO** (`[0.075]×6+[0.5]`, disc 각 0.05) | `[0.025, 0.025 \| 0.075×6, 0.5]` | 0.05 / 0.95(프렛 6×0.075=0.45 + 피킹 0.5) | 9 |

---

## §3. 환경 (environment)

### 3-0. 한 장 요약

Isaac Gym + PhysX 위에서 **멀티크리틱 PPO(on-policy) + AMP/ICCGAN 판별자**로 학습. Actor·Critic 각각 `GRU256 → goal_embed 가산 → MLP(1024/1024/512, ReLU6)`이고 Critic은 `value_dim` 멀티헤드에 DiagonalPopArt를 붙인다. 관측은 RunningMeanStd(clamp±5)로 정규화. 손 시뮬은 **60Hz(dt 1/60, substeps4, frameskip1)·중력 off·base 고정·position 제어**. 각 보상 열마다 독립 GAE·독립 정규화 후 `reward_weights` 가중, PPO surrogate는 열을 `.sum(-1)` 후 배치평균.

### 3-1. 알고리즘 — 멀티크리틱 PPO + AMP

- 보상이 **스칼라가 아니라 열 벡터**(판별자 스타일보상 열 + task 열). 열마다 독립 value 헤드·GAE·정규화(PopArt) → 마지막에 `reward_weights`로 섞어 단일 정책 그래디언트. `value_dim = 판별자수 + rew_dim`.
- 판별자는 옵션(WGAN-GP hinge, §2-5). AMP 스타일 분포 모방으로 손 동작 스타일 학습.

### 3-2. 네트워크 (models.py)

- **Actor**(L170-227): `GRU(state_dim,256, batch_first)` → 마지막 유효프레임 → `s += embed_goal(g)`(embed_goal=Linear(goal_dim,256)+ReLU6+Linear(256,256)) → MLP=Linear(256,1024)+ReLU6+Linear(1024,1024)+ReLU6+Linear(1024,512) → 헤드 `mu=Linear(512,act_dim)`·`log_sigma=Linear(512,act_dim)`. 분포=Normal(mu, exp(log_sigma)+1e-8). **log_std init**: bias=−3(std≈0.05), weight=uniform(±1e-4) → 초기 탐색을 담당(엔트로피 보너스 없음).
- **Critic**(L128-167): GRU256 → embed_goal 가산 → MLP=…(1024/1024/512/**value_dim**), MLP weight=uniform(±1e-4)/bias=0. 멀티헤드 = 마지막 Linear out=value_dim.
- **활성**: Actor/Critic ReLU6, 판별자만 ReLU.
- **관측 정규화** `RunningMeanStd(state_dim, clamp=5.0)`(float64 버퍼, 유효 프레임 마스크로만 update). **value 정규화** `DiagonalPopArt(value_dim, momentum=0.1)` — update 시 최종 Linear weight/bias 재스케일로 출력 보존.

### 3-3. 하이퍼파라미터 (main.py:37-52)

| 항목 | 값 | 근거 / 비고 |
|---|---|---|
| 알고리즘 | 멀티크리틱 PPO (on-policy) | Isaac 대규모 병렬 |
| `num_envs` / `horizon` | **512 / 8** | 업데이트당 8×512=**4096 샘플** (L38-39) |
| `batch_size` | 256 | 4096/256=**16 미니배치** (L40) |
| `opt_epochs` | 5 | 롤아웃마다 5×16=80 grad step (L41) |
| `gamma` / `lambda_` | **0.95 / 0.95** | GAMMA_LAMBDA=**0.9025** (L44-45) |
| `actor_lr` / `critic_lr` | **5e-6 / 1e-4** | 분리 param group, Adam, 고정 (L42-43,95-98). actor가 20× 느림 |
| `disc_lr` | 1e-5 | disc 전용 Adam (L102-104) |
| PPO clip `ε` | **0.2** (ratio [0.8,1.2]) | `pg = -min(adv·ratio, adv·clip).sum(-1).mean()` (L323-324) |
| `value_coef` | 0.5 | `loss = pg + 0.5·vf` (L326-328) |
| grad_clip | 1.0 | actor+critic 합산 grad-norm (L330) |
| entropy | **0 (항 없음)** | log_std 헤드가 탐색 담당 (L324-328) |
| terminate_reward | **−25** (전 열 대입) | (L50,272) |
| control_mode | "position" | (L51) |
| disc | WGAN-GP hinge, gp 10 | (L220-237) |
| max_epochs / save | 50000 / 10000 (cfg override) | left/right 100000·two 60000 (L47-49) |

### 3-4. 멀티크리틱 GAE / 정규화 / 가중 (main.py L253-303)

- `rewards` shape=(HORIZON·N, value_dim). disc 열=스타일보상, task 열=`rewards[:, -rew_dim:]`, terminate 행=−25. values는 PopArt로 unnorm.
- δ: `advantages = rewards − values + GAMMA·values_`; GAE 역방향 `advantages[t] += GAMMA_LAMBDA·advantages[t+1]·not_done[t]` — **열(크리틱)별 독립**. `returns = adv + values`.
- **열별 정규화**: `adv = (adv − mu_col)/(sigma_col+1e-8)`. `PopArt.update(returns)`로 returns 정규화. `multi_critics`면 `adv *= reward_weights`(열별 가중).

### 3-5. 시뮬레이션 (env.py L129-156, 손 오버라이드 L946-997)

- 기본 Env fps=30·frameskip=2·substeps=2. **손(L965-967)은 fps=60·substeps=4·frameskip=1로 강제** → dt=1/60, 물리 substep 4회(=240Hz 유효). `do_simulation`은 frameskip회 `gym.simulate` 반복.
- **PhysX**: solver_type=1(TGS), num_position_iterations=4, num_velocity_iterations=0, contact_offset=0.01, rest_offset=0, bounce_threshold_velocity=0.2, max_depenetration_velocity=10(손은 1), contact_collection=CC_LAST_SUBSTEP, use_gpu_pipeline=True, gravity=(0,0,−9.81).
- **손 asset**: fix_base_link=True, disable_gravity=True, thickness=0.0003; shape contact_offset=0.0001로 축소.
- **제어**: position→DOF_MODE_POS, `a = action·scale + offset`(정규화 ±0.5 → [lower,upper]).
- **종료/오버타임**: 손별 기하 경계 이탈(§2-4) + `overtime = lifetime≥episode_length`; goal_timer 만료 시 reset_goal.

### 3-6. I/O 및 사이징 (env.py L100-102, 572-585 · main.py L448)

- `act_dim = action_scale.size(-1)` = 작동 DOF 수 · `ob_dim = observe().size(-1)` · `rew_dim = reward().size(-1)`.
- `state_dim = (ob_dim − g)//ob_horizon`(g=max goal_dim) = 프레임당 proprio. ACModel이 obs를 s(:-goal)와 g(-goal:)로 분할 후 s를 (ob_horizon, state_dim)로 reshape해 GRU 입력.
- `disc_dim` = key_link수·7. `value_dim = 판별자수 + rew_dim`.
- proprio는 per-frame = key_link수·13(include_velocity=True), disc는 ·7(False).

| 태스크 | act_dim | state_dim | ob_dim | goal_dim | rew_dim | value_dim |
|---|---|---|---|---|---|---|
| **LEFT** | 27 **[코드]** | 208 | 451 **[확인 필요]** | 35 **[코드]** | 6 | 8 |
| **RIGHT** | 27 | 208 | 457 **[확인 필요]** | (35,41) | 1 | 2 |
| **TWO** | 54(27+27) | 416 **[코드]** | 908 **[확인 필요]** | 76 | 7 | 9 |

- **[확인 필요]**: state_dim/ob_dim/disc_dim(LH/wrist=4·7=28, LH/fingers=12·7=84, RH/hand=16·7=112)는 cfg key_links 링크 수(좌16/우16/양32)와 관측 규칙으로 **산출**한 값 — XML 링크명 존재는 미검증. act_dim=27·state_dim=416·ob_normalizer=416·goal 35만 pretrained ckpt로 직접 확정.
- **type**: obs/action/reward 모두 float32(done만 bool), device cuda, 배치축 N=num_envs.

---

## §4. 우리(tab2body)와의 이식 매핑

> guitar는 **직접 이식원본**이므로, GPS의 "빌려온 수식/기각" 2분류와 달리 **그대로 이식 / 적응(바꿈) / 기각** 3분류로 정리한다. `PROJECT_CONTEXT.md §3(결정)·§4(함정)`와 `task_fret_design.md`·`learning_env_design.md`에 연결.

### 4-1. 그대로 이식 (port as-is)

| 항목 | 값·근거 | 우리 문서 연결 |
|---|---|---|
| **멀티크리틱 PPO** | 열별 독립 GAE·정규화 후 `.sum(-1)` | learning_env §1-2, 결정 #9 |
| **DiagonalPopArt** | 헤드별 value 정규화(끄지 말 것) | learning_env §3-2 "이질적 열 균형의 핵심" |
| **듀얼스케일 press 커널** | `clip(0.8·e^(−1000d²)+0.2·e^(−30d²),0,1)` | task_fret R1, 논문 식4 정확 일치 |
| **goal 기계** | 노트 로딩·윈도 10-20·룩어헤드 5·타이머 시프트 | task_fret R15, learning_env §6-3 |
| **하이퍼파라미터** | num_envs 512·horizon 8·γ=λ=0.95·actor 5e-6/critic 1e-4·entropy 0·grad_clip 1·value_coef 0.5·terminate −25 | learning_env §2 표(전 항목 [G]) |
| **reward_weights 조립** | disc·task 정규화(합=1), 열별 크리틱 | learning_env §4 |
| **60Hz 제어** | dt 1/60, substeps 4, frameskip 1 | learning_env §2 "goals.py 타이머가 이 시계로 tick" |
| **all-correct 볼록결합** | `0.8·base + 0.2·all_correct` | task_fret M1 |

### 4-2. 적응 (바꿈)

| 항목 | guitar(원본) | 우리(tab2body) | 근거 |
|---|---|---|---|
| **운지 감독** | 암묵(availability 마스킹 L1614-1651, in-window min) | **명시**(fingermapping finger 라벨 = explicit goal, min을 지정 손가락 세그로 제한) | 결정 #12, 논문 부록 D-2(5노트 미리보기 한계)가 직접 근거 |
| **제어 부위** | 손만(27-DOF 플로팅) | **전신**(act_dim 42/33/75, SMPL, reach·팔모션) | learning_env §7 ① |
| **중력** | disable_gravity=True | **끔**(전신은 중력 필요) | task_fret R11/R14 |
| **GRU** | GRU256(ob_horizon=2, 플로팅 손 관성용) | **제거 권장**(ob_horizon=1 단일프레임 MLP, 룩어헤드가 goal에 있음) | learning_env §3-4 [미정] |
| **리셋 순서** | `reset_done()`(이터레이션 시작) | **step-tail 자동 리셋**(IsaacGymEnvs식) | learning_env §4 [우리] |
| **PD 게인** | 손 XML 게인 | **SMPL 전신 게인 재튜닝** | task_fret R11 |
| **goal 인코딩** | (n_strings+1)·5=35 | **finger 채널 추가**(잠정 65, 상한 125) | learning_env §5-2, §6-3 |
| **판별자** | LEFT 2 / RIGHT 1 / TWO 2 상시 | **S0 off**(value_dim=rew_dim), 태스크 후 추가 | learning_env §1-3 |
| **커리큘럼** | 없음(랜덤 샘플링뿐) | **폴리포니 커리큘럼 신설**(단음→dyad→3~4음→바레, F1≥0.9 게이트) | learning_env §2 [우리] |
| **strike rew_dim** | RIGHT=1(통합) | **1 vs 6(줄별) 미정** | learning_env §7 [미정] 5 |

### 4-3. 기각 (reject)

| 항목 | guitar 상태 | 기각/수정 사유 |
|---|---|---|
| **쿼터니언 conjugation 버그** | `observe_iccgan` L880-884: parent-relative가 `orient_inv` 대신 `orient` 사용, "guitar 월드 고정이라 무해"(저자 FIXME) | 우리는 **몸통이 움직이므로 반드시 수정**. 사전학습 ckpt 호환은 깨짐. task_fret 문서·base.py 담당자와 교차확인 필요 |
| **wrist 인덱스 오프셋 버그** | PROJECT_CONTEXT 함정 목록이 지목하는 항목 | **[확인 필요]** — 본 분석의 코드 근거(env.py 정독)에서는 정확한 라인을 직접 특정하지 못함. 이식 전 원본 재확인 필요(GPS의 string 인덱스 반전 규약과도 교차확인) |
| **DroQ / off-policy** | (guitar 아님, GPS 스택) | 이미 결정 #9로 기각 — guitar의 on-policy PPO를 취함 |

### 4-4. 이식 전 확정 필요 (paper↔code 불일치 · XML 미검증)

- **세로손가락 임계**: 코드 `0.0872`(≈sin5°) vs 주석 "10 degrees"(0.1736). 이식 시 **코드값 신뢰 여부** 확인(task_fret R9에 이미 반영: "0.0872, 코드 주석 10°와 불일치—재확인").
- **not-press 지수**: 코드 (d/0.007)**⁴** vs 논문 식5 (d/0.007)². goals.py 이식 전 저자 의도 확정(task_fret R3에 (d²/0.000049)² 채택).
- **N_FRETS**: 코드 22 vs 논문 §5 본문 "24프렛". XML(`assets/left_hand_guitar.xml`) 확인.
- **홀드 정확도 임계**: 코드 ½(L1608) vs 논문 §6.1 "2/3".
- **AdaptNet log_sigma**: 코드 미동결(L328,331 `"sigma": continue`) vs 논문 "완전 잠금".
- **학습 트랙 수**: 논문 §6 "500 트랙" vs pretrained/ 20곡+오른손1.
- **XML DOF/링크**: act_dim=27만 ckpt 확정, 손가락별 DOF 분해·16 key_link 존재는 미검증.

---

## §5. 참고

**경로 접두** `related_work/guitar/` 생략. 라인은 조사 시점 기준(이식 전 재확인 권장).

| 약칭 | 파일 | 주요 라인 |
|---|---|---|
| env | `env.py` | 상수 L933-943 · 시뮬 L129-156,946-997 · observe_iccgan L838-913(버그 L880-884) · reward_weights L493-568 · 사이징 L100-102,572-585 · **좌손 _reward L1526-1687**(압점 L1485-1488·실격 L1542-1545·press커널 L1657-1658·notpress L1666·합성 L1670·allcorrect L1668,1671·부드러움 L1675-1686·검출 L1562-1566) · 종료 L1443-1469 · **우손 _reward L1926-2069**(교차 L1949-1972·커널 L1990-1998·이격 L1994-2013·벌점 L2018-2035) · 우손 종료 L1886-1895 · **양손 reward L2185-2201**(ready L2195-2199) · load_notes L1045-1234 · reset_goal L1236 · observe_goal L1420 |
| main | `main.py` | 하이퍼 L37-52 · 학습루프 L88-399 · PPO L323-330 · 멀티크리틱 GAE L253-303 · terminate −25 L272 · disc 학습 L220-238 · disc 보상 L257-259 · value_dim L448 · AdaptNet 배선 L528-529 |
| models | `models.py` | Actor L170-227(log_std init L198-199) · Critic L128-167 · RunningMeanStd L6-39,241 · DiagonalPopArt L44-85,244 · **AdaptNet L288-378**(0-init L324-325·동결 L327-332·잔차 L356-378) |
| utils | `utils.py` | dist2_p2seg_/closest_seg2seg_ L115-127(제곱거리 반환) |
| cfg | `cfg/{left_demo,right,two_demo}.py` | goal_reward_weight·판별자 key_links·parent_link·episode_length·max_epochs override |

**논문**: `docs/guitar-paper-ko.md`(Xu & Wang, SIGGRAPH Asia 2024). ICCGAN 모방·멀티크리틱(식9) / availability 마스킹(그림4) / 보상 커널(식4-8 좌·식12-16 우) / synchronizer AdaptNet(식1-2) / 정량(왼손 F1≈0.8·오른손>0.9·동기화 후 대부분≈100%, 평균+193%) / **한계 부록 D-2(5노트 미리보기 → 우리 명시운지 노벨티 근거)**.

**미해결(코드/논문 대조 필요, §4-4 요약)**: ① not-press 지수 ⁴ vs ² · ② 세로손가락 0.0872 vs 주석 10° · ③ N_FRETS 22 vs 24 · ④ 홀드 정확도 ½ vs 2/3 · ⑤ AdaptNet log_sigma 미동결 · ⑥ 500 vs 20 트랙 · ⑦ ready 타이머 예외(논문 무기재) · ⑧ 쿼터니언 버그 전신 파급 · ⑨ XML DOF/링크(act_dim 27만 확정) · ⑩ wrist 인덱스 오프셋 버그 라인 미특정.
