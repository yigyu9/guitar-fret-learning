# tab2body/env — 설계 문서 (base.py가 왜 이렇게 구성되었는가)

> 이 문서는 `base.py`(공유 환경 코어)의 **모든 설계 결정과 그 근거**를 정리한다.
> 근거 표기: **[G]**=guitar/(Pei Xu SA'24, 이식 원본) · **[D]**=과거 DIGIT 실패 분석(안티패턴) ·
> **[P]**=PROJECT_CONTEXT(설계 정본·실측 함정) · **[M]**=이 프로젝트에서 직접 실측(도구 명시).
> 최종 갱신: 2026-09-17. 현재 배관 smoke는 `python -m tab2body.train --task fret|strike --smoke`로 실행한다.
> 이 문서는 현재 G0 Fret/Strike 공유 환경만 설명한다. 과거 G1/G2 자유기타 실험은 폐기했으며,
> asset XML에 남은 관련 주석은 checkpoint hash 보존용 역사 metadata일 뿐 지원 기능이 아니다.

---

## 0. base.py는 무엇인가

현재 파이프라인은 **fret[A] ∥ strike[B] → G0 결합[A+B]**이며,
fret[A]와 pick-only strike[B]가 각각 실행 가능하다. 자유기타 환경은 StabilityAdapter에서 새로 설계한다.
모든 태스크는 **같은 `GuitarEnvBase`를 인스턴스화**하고 `control_dofs`(제어할 관절)·goal·reward 모듈만 바꿔 끼운다.
따라서 base.py = **태스크 없는 공유 sim + 관측 + step 코어**. 여기에 태스크 특화(goal 인코딩, reward)는 없다.

## 1. 모듈 구조

| 모듈 | 역할 | 상태 |
|---|---|---|
| `base.py` | 공유 코어: 2액터 로드·하이브리드 PD·하체 furniture 잠금·기타상대 관측·RL 루프(reset/step/종료) | ✅ 완성·검증 |
| `collision.py` | actor 기본 필터와 엄지 pad/neck-back proxy 전용 충돌 채널 상수 | ✅ GPU 감사 |
| `goals.py` | 60Hz JSON + 0/6/15-frame lookahead + 손가락별 R15 13D string-mask next-goal×4 | ✅ 전수 검사+GPU PASS |
| `rewards/fret.py` | 지정 손가락 pad signed-depth, PRESS/NO_PRESS/DONT_CARE, 오압현 무효화, hand soft range, 6채널 | ✅ S0 |
| `rewards/thumb.py` | tapered neck-back 접근 + `LH:thumb_pad` 접촉·압축 깊이 기반 R6 지지 보상 | ✅ GPU sweep·학습 검증 |
| `rewards/motion.py` | wrist goal 도달 후 finger→wrist→elbow→shoulder R12 속도 우선순위 | ✅ CPU+GPU smoke |
| `safety.py` | R13 손바닥 법선 + R14 기타 관통 + R22 손가락 쌍별 capsule 관통 진단 | ✅ CPU+GPU smoke |
| `tasks/task_fret.py` | 30DOF 제어·Fret-v1 425D/Fret-v2 420D 관측·goal/reward/R13 손바닥 종료/F1 집계·4-tuple step | ✅ S0 |
| `strike_goals.py` | 최소 `[time,frame,string]` + 선택적 provenance/reviewed override 검증·60 Hz canonical timeline | ✅ raw v3 |
| `strike_goal_compiler.py` | phrase 방향 계획·microtiming·traversal-edge/path feasibility | ✅ direction v3 / transition v2 |
| `strike_detector.py` | goal 독립 finite swept crossing·RELEASE·물리 re-arm·zone quality | ✅ CPU/CUDA |
| `rewards/strike.py` | A0~A4 single→clean-recovery/S0~S3 strum stage-mask scalar reward와 guitar reference grip | ✅ 현재 계약 |
| `tasks/task_strike.py` | 30DOF·v2 303D/v1 327D 관측·3 motor phase·끝줄/exit 완주·path-aware dual recovery·failure mining | ✅ state v14 |
| `strap_chain.py` | opt-in XPBD 입자 체인 스트랩(1D 옷감): 몸 capsule 감김·마찰, 기타 버튼 장력, 몸 반작용 (§6.7) | ◐ CPU 검증, GPU 미검증 |
| `tasks/task_full.py` | G0 one-step transaction bridge; shared Isaac simulator backend는 미구현 | ◐ |
| `../full/` | canonical event, rule Synchronizer, strict source loader, 105D named ABI(실질 가동 97D) runtime 계약 | ✅ CPU |

---

## 2. 핵심 설계 결정과 근거

### 2.1 신 구성 (씬·액터)

**휴머노이드·기타 별도 2액터 + 의자 박스, env별 순차 생성.**
- *현재 범위:* G0 월드고정 기타를 별도 액터로 로드한다. 과거 `fix_base_link` 기반 G1/G2 전환은 제거했으며 새 환경 계약에서 다시 정의한다.
- *왜 순차 생성:* env1의 모든 액터 → env2 순. Isaac 함정 #7([P]).

**`fix_base_link=True`(휴머노이드 골반 용접), 중력 ON.**
- [G]는 손을 `fix_base_link + disable_gravity`로 **중력을 지워** 안정화한다. **우리는 그걸 복사하지 않는다** — 골반만 용접하고 관절 몸통은 중력을 받게 둔다([D]도 골반 용접). `disable_gravity`는 기타 액터에만(정적 goal 기하).
- *왜 골반 용접:* 자유 root 좌식은 **등받이가 없어 3초 내 뒤로 전도**([P] P2, [M] settle_test). balance/tipping 문제를 설계로 제거.

### 2.2 하이브리드 PD (제어 방식) — [M] 실측 2건이 강제

```
비잠금 관절: DOF_MODE_POS, stiffness=0, damping=kd  (감쇠는 솔버 내부=암시적=무조건 안정)
            + 매 스텝 명시 토크 τ = kp·(q*−q), 관절군별 20~300 N·m 클램프
```
- *왜 안 되는 것들:* ① **Isaac 네이티브 POS drive가 멀티힌지(D6) 관절을 왜곡** — 어깨가 kp 무관 ~20° 오답 수렴([M] isaac_pose_check; [P] 함정 #3). ② **순수 명시 PD(감쇠 0)는 bang-bang 발산** — 팔꿈치 235°, qd≈−90rad/s([M]).
- *역사적 결과:* 상체 유지 이탈 **1.93°**(구 환경 진단; 네이티브 drive는 20.3°). 이 수치는 현재
  학습 품질이나 checkpoint 호환성을 보장하지 않으며, 현재 배관은 공용 `--smoke` 명령으로 재검증한다.

### 2.3 하체 = "furniture" 3중 잠금 — [M] 안정성 엔지니어링의 핵심

하체(Hip/Knee/Ankle/Toe)는 정책이 제어하지 않는 **가구**다. 완벽 정지를 위해 3층으로 잠근다. 각 층은 실측된 실패 모드를 하나씩 막는다(`tools/hold_compare.py`, `verify_stability.py`):

| 층 | 기법 | 막는 실패 모드 |
|---|---|---|
| 1 | **리밋 핀칭** `lower=upper=pose±1e-4` (하드 제약) | 소프트 하이브리드 PD는 다리 중력토크가 ±300 클램프를 포화 → **60°+ 드리프트**([M]) |
| 2 | **높은 armature=10** (관성 증가) | 핀칭 리밋의 **~30Hz 서브스텝 떨림** (0.10°→0.0015° p2p, [M] hold_compare) |
| 3 | **매 스텝 init 재주입** (step_physics) | 소프트 리밋의 지속 중력 하 **느린 정착**(~0.7°/50s→0°) ([D]도 동일하게 이중 강제) |

- *역사 결과:* 하체 드리프트 **0.0000°/50초**([M] verify_stability). 능동 상체 제어 중에도 0°를
  당시 task smoke에서 확인했다. 현재 재검증은 공용 `python -m tab2body.train --task fret --smoke`를 사용한다.
- *[M] 근본 트레이드오프(중요):* 잠긴 발이 **바닥에 닿으면** [핀칭=떨림] 또는 [소프트=26° 드리프트]를 피할 수 없다(hold_compare로 5전략 비교). 그래서 발은 **바닥에서 ~1cm 띄운 채 평평**하게 둔다(foot_settle.py). SMPL 좌우 다리 bind 비대칭으로 두 발의 자연 접지 높이가 4cm 다른 것도 확인됨. → armature가 **떨림을 죽여서** 접지 없이도 자연스러운 자세가 가능해진 것이 돌파구.
- *[D]와의 관계:* DIGIT은 발을 아예 띄워(접촉 0) 떨림을 원천 회피 + 잠금을 stiff PD(kp2000)로 했다. 우리는 stiff PD를 **핀칭 위에 얹지 않는다**(핀칭이 이미 위치를 잡으므로 stiff PD는 리밋 구속에 에너지만 주입). armature가 더 깔끔한 레버.

### 2.4 충돌 규약 — [P] 함정 #2/#4, [M]/[P] 자기충돌

- **필터 humanoid=1 / guitar=2 / chair=0.** Isaac은 두 shape의 필터비트 AND가 0이면 충돌. 1&2=0 → 휴머노이드↔기타 충돌(운지/pluck 접촉 감사가 유효). 이걸 틀리면 관통 감사가 조용히 무효화([P] 함정 #2; [M] 실제로 한 번 무효였음).
- **휴머노이드 자기충돌 OFF**(필터 1이라 1&1=1≠0 → 꺼짐). [D]는 켰지만 **[P] P2가 반대를 실측**: 좌식은 사지가 몸통에 밀착 → 가짜 자기접촉이 다리를 밀어냄. 측정된 [P]를 따라 OFF.
- **per-shape contact_offset=1e-4**(휴머노이드·기타), 전역 0.002. PhysX 기본 2cm는 **가짜 접촉으로 관절을 밀어냄**([P] 함정 #4; [G]도 손에 1e-4 독립 도달).
- **엄지 전용 채널**: 일반 shape는 human=1/guitar=2를 유지한다. fret 태스크에서만
  `LH:thumb_pad=2`, `G:thumb_support_proxy=1`로 바꿔 이 둘만 추가 충돌시킨다.
  proxy는 실제 넥 후면 z 평면의 중앙 유효 폭을 나타내는 invisible box다.
- **시작 시 자동 감사**: 현재 human 55 shape, guitar 28 shape이며 일반 shape와 엄지 예외
  필터, pad/proxy shape 수, 모든 `contact_offset=1e-4`를 검사한다. R14는 물리 접촉과
  별도로 기타 로컬 해석 깊이와 swept 통과를 기록한다.

### 2.5 기타-상대 관측 — [G] observe_iccgan, [P] §5.1

모든 바디 상태를 **기타 로컬 프레임**으로 표현(`to_guitar_frame`). 현재 G0에서는 기타가 정적이다.
새 자유기타 환경이 이 변환을 재사용할지는 새 관측 계약과 함께 검증한다.
- *[M]/[G] 주의:* guitar/env.py L879/L884의 쿼터니언 conjugation 버그는 **기타가 월드고정일 때만 무해**(상수 회전=학습가능 상수). base.py는 정확한 역회전(`quat_rotate_inverse`)을 사용한다.
- (`isaacgym.torch_utils`는 이 numpy 버전에서 `np.float` 때문에 임포트 실패 → 쿼터니언 유틸을 base.py에 직접 정의.)

### 2.6 control_dofs 분할 — 한 몸, 태스크별 제어 집합

`control_dofs`(관절 이름 접두사) → `controlled`/`ctrl_idx`/`num_actions`. fret[A]는
`L_Shoulder~L_Wrist + 왼손 다섯 손가락` 30DOF만 제어한다. `L_Thorax`와 몸통은 초기 PD 자세로 고정한다.
strike[B]는 `R_Shoulder + R_Elbow + R_Wrist + RH:*`의 30DOF를 제어하고 `R_Thorax`는 고정한다.
제어하지 않는 관절은 하이브리드 PD로 init에 유지한다.
- *[P] 고유 난제:* [G]는 fret/strike를 별도 액터로 학습한다. 우리는 한 몸의 제어 관절을 나눈다.
  결합 단계에서는 두 정책을 같은 몸에 주입해야 한다. 다른 손의 외란에도 비제어 관절이 안정적이어야 한다.

### 2.7 60Hz 제어 · joints_isaac

- **60Hz**(dt=1/60, substeps=4, frameskip=1: 제어 1스텝=sim 1스텝) — [G] 손 설정과 동일. GPS 30Hz는 상속 안 함. **핵심: goals.py의 노트 타이머가 물리와 정확히 같은 시계로 tick**해야 함.
- **init 자세 = `joints_isaac`**(MuJoCo용 `joints` 아님). MuJoCo↔Isaac 멀티힌지 FK가 손목에서 8.4cm 차이([P] 함정 #1) → Isaac 도구는 joints_isaac.

---

## 3. RL 루프 API (base가 제공하는 것)

```python
env = GuitarEnvBase(num_envs, control_dofs=[...접두사...], max_episode_length, action_alpha=0.5,
                    action_scale=1.0, reset_noise, obs_body_names, seed)
obs = env.reset()                       # RSI: 좌식 init(+옵션 노이즈), obs 반환
obs, done = env.step(actions)           # 액션적용→sim→refresh→종료+자동리셋. (obs, done)
```
- **액션**: tanh 정책의 `[-1,1]` → EMA(α=0.5) → `tgt = mid + ema(a)·half_range`로 hard range에 1:1 대응한다. 제어관절 reset은 경계 포화를 피하려고 hard range 안쪽 2%를 사용한다.
- **관측(기본)**: 비잠금 dof pos+vel(고유수용) + obs_body들의 **기타상대 위치**. 태스크는 이를 `super().compute_observations()`로 받아 goal obs를 concat.
- **종료**: timeout | NaN | 속도 blow-up(>50rad/s). root 용접이라 전도는 설계상 불가; 태스크가 자기 조건을 OR.
- **접촉 텐서**: `contact_force` (net force) — 현재 Fret/Strike 접촉 검사와 pluck 검출에 사용한다.
- **버퍼**: `progress_buf`/`reset_buf`/`obs_buf`/`prev_action`, `root_init`.

---

## 4. 파라미터 값 (참조 근거)

| 그룹 | 값 | 근거 |
|---|---|---|
| sim | dt 1/60, substeps 4, TGS(solver 1), pos_iter 4, **vel_iter 2**, contact_offset 0.002/per-shape 1e-4, rest_offset 0 | [C][G]; vel_iter는 [G]의 0→2로 올림([M] 접촉 감쇠) |
| 잠금 하체 | pinch + damping=kd + **armature=10** (stiff PD는 얹지 않음) | [M] hold_compare; [D]는 20000/2000을 핀칭 없이 |
| 상체 kp | 캡 ≤600, 손가락 20, 손목/팔꿈치비틀림 60, 목 하한100/캡150, 하한 30 | [M] `_compute_gains`; [G] SMPL MJCF hips 300/knees 300/torso 600 |
| kd | max(0.25·kp, mjcf_kd) | [M] |
| 명시 토크 클램프 | finger 20 / wrist 60 / elbow 100 / shoulder·thorax 150 / 기타 300 N·m | [M] R14 보강 |
| 액션 | tanh bounded, EMA α 0.5, scale 1.0, reset soft inset 2% | 현재 fret 제어 계약 |
| (goal, 후속) | lookahead 5, grace 5, resample (10,20) | [G] — goals.py에서 |

---

## 5. guitar/ (27DOF 부유손) → 우리 (105개 authored slot / 97DOF 실질 가동 좌식) 적응

- **직행**: Env/tensor 골격, RSI(ReferenceMotion), observe_iccgan(parent_link), 멀티크리틱 reward 인터페이스, goal/note/timer 기계.
- **바꿈**: `disable_gravity` 끔(몸통 중력), 게인=SMPL 스케일(mjcf_gains), vel_iter 0→2, 종료=자세기반, 쿼터니언 버그 수정.
- **[P] 신규 난제(참조 없음)**: 좌식 하체 접촉 안정(§2.3), 전신 자기충돌(§2.4), 한 몸 제어분할+결합(§2.6). 자유기타 결합은 새 StabilityAdapter 환경 범위다.

---

## 6. 완료 상태 (base 코어)

**[DONE]** 2액터 씬·하이브리드 PD·하체 3중 잠금·충돌규약·접촉오프셋·control_dofs 분할·기타상대 관측 변환·기본 관측 빌더·액션 EMA+스케일·RSI reset·종료·step API·접촉 텐서·버퍼·RNG.
**[MISSING → 후속]** full 결합 goal·reward, disc 관측(스타일), one-simulator FullG0 task,
그리고 별도로 재설계할 StabilityAdapter 환경. AdaptNet은 현재 선택이 아닌 역사적 비교안이다.

### 6.1 S0 fret 확장 (2026-07-19)

`base.py` 코어는 유지하고 task subclass에서 goal/reward를 배관했다. `obs_buf`의 base-prefix 기록만
확장 관측과 공존하도록 수정. `FretTask`: obs 425
(기본180+goal128+EMA actuator state30+thumb geometry12+미래 goal75), actions 30,
reward/value 6. 현재 checkpoint contract는 이 차원과 `L_Shoulder`부터 시작하는 제어 순서를 포함한다.
기존 33-action checkpoint는 재개하거나 초기화에 사용하지 않는다.

### 6.2 pick-only strike 확장 (2026-07-27)

`StrikeTask`는 어깨부터 손가락까지 30 action, 기본 Strike-v2 303D actor observation,
scalar value/reward를 사용한다. 327D v1은 명시적 호환 모드로 보존한다. 공개 motor phase는
`READY/APPROACH/RELEASE_RECOVER` 세 개이며, 실제 성공 시점은
별도 detector의 swept crossing RELEASE pulse다. A0 grip, A1 ready, A2 crossing, A3 timing,
A3 single timing 뒤 A4에서 실제 strum 문맥의 clean recovery를 익힌 후 S0~S2에서
strum 폭 2→6, E0 양방향 마지막 줄·exit 완주와 timing
`400→250→225→200→175→150→100→zone 100→67→50 ms`를 익히고
S3에서 곡으로 통합한다. 현재 compiler는 direction `phrase_dp_microtiming_v3`, transition
`entry_side_edge_gap_v2`를 사용한다. S3의 짧은 사건 간격은 다음 접근 전까지 확보된 frame을
사용하는 handoff recovery, 충분한 간격·마지막 사건은 12-frame full recovery를 적용한다. 직접
exit-side→next-entry-side 경로가 최근 줄이나 비목표 줄을 가로지르면
`release lift → elevated transfer → approach` clearance와 detector re-arm을 모두 요구한다.
관측에는 이전 recovery 방향, 현재 음악 방향, clearance required/reached가 포함된다.
A1~S3는 완료 episode의 exact 지표만 승급 증거로 쓰며, timing p95에는 허용창 밖의
유효 target crossing도 포함한다. S3 sampled lane은 `±6 mm` 만점, `±12.5 mm` 성공
경계다.

### 6.3 Goal Pair 병목 개선 (2026-08-12)

- pair와 연속 구간을 전환 종류·incoming 손가락별로 균형 표집한다.
- 연속 구간 길이는 mixed 단계에서 2→4→8 이벤트, full에서 최대 12 이벤트로 늘린다.
- 특정 손가락 집중을 끄고 네 손가락을 공동 학습한다.
- 회복 중 모든 손가락과 왼쪽 어깨·팔꿈치·손목을 허용한다.
- retention은 손가락 균형 표집한 실제 곡의 두 연속 구간을 재생한다.
- 회복은 phase 기준선 대비 하락이 사라지면 끝낸다. 최종 숙달 기준과 혼용하지 않는다.
- 안정 압현 자세는 goal 상태별 cache에 저장하고 reset의 35%에 재사용한다.
- 사람 왼손 모션은 비활성 손가락·엄지에만 최대 0.03의 약한 자세 감점으로 적용한다.
- `local_reach_margin`으로 현재 MCP 위치에서 손가락만으로 목표에 닿는지 기록한다.
- 얕은 일반 관통은 연속 감점하며, 엄지 지지는 엄지 전용 안전 규칙으로 분리한다.

### 6.4 S3 failure-mining 상태와 평가 격리 (2026-08-28)

S3 `stalled`에서는 event별 실패 mass와 노출 mass를 decay `0.995`로 갱신하고,
전역 실패율의 prior exposure `16`으로 축소한 실패율을 hard-window score로 사용한다.
episode 시작의 15%만 hard window에서 뽑고 하나의 window 확률을 10%로 제한해,
노출이 많은 하나의 사건이 표집 분포를 자기강화하는 것을 막는다. hard episode도
PPO update에는 포함하지만 stalled S3 승급 evidence에서는 제외한다.

영상·deterministic 전체곡 평가는 `failure_mining_updates_enabled=False`인 격리 구간에서
실행하고 종료 뒤 기존 failure mass·exposure·score를 복원한다. 평가 중 생긴 동일
실패가 병렬 환경 수만큼 누적되어 학습 표집을 오염하지 않도록 한 계약이다.
이 절의 저장 계약은 curriculum schema `v12`, environment state `v13`, semantic contract
`exposure_normalized_failure_mining.v12`였으며 현재 exact resume 대상이 아니다. 당시 path-aware
전환에서는 관측이 321D에서 327D로 바뀌어 구 actor도 전이하지 않고 fresh A0부터 학습했다. 현재
endpoint 계약의 제한된 S2 actor 전이는 아래 §6.6이 별도로 정의한다.

평가·주기 영상은 failure-mining mass/exposure/score뿐 아니라 `StrikeTask` generator RNG와
reset generation을 함께 snapshot한다. 산출물 생성 뒤 이 상태를 복원한 다음 학습 observation을
새로 reset하므로, 진단 rollout이 이후 hard-window 표집과 reset 난수열을 바꾸지 않는다.

### 6.5 Strike 입력 품질과 path-aware 실행 계약 (2026-08-30)

새 plan의 정본 profile은 direction `phrase_dp_microtiming_v3`, transition
`entry_side_edge_gap_v2`다. compiler는 사건 중심 간격이 아니라 이전 traversal 마지막 줄과 다음
traversal 첫 줄의 실제 edge gap, exit/entry side와 직접 경로 재통과 줄을 봉인한다. full-song
preflight는 `INFEASIBLE` transition을 GPU 생성 전에 거부한다.

2026-08-30에 사용자가 판정을 위임해 `00_SS1-68-E_comp`의 source event 147~149를 하나의 down
strum으로 병합한 후보를 `approved_user_delegated` 상태로 canonical에 승격했다. 수동 오디오 청취는
수행하지 않았고 source JAMS·symbolic chord·기존 `46.5 ms < 50 ms` 불가능 경계를 근거로 승인했다.
현재 canonical은 raw v3/plan v4, direction v3/transition v2, 104 events(61 single/43 strum),
최소 edge gap `51.0 ms`, `INFEASIBLE=0`이다. 전체 strict audit는 exit 0,
`PASS 2 / AMBIGUOUS 6 / INFEASIBLE 0`이다. 이 곡은 남은 source/grouping 경고 때문에
`AMBIGUOUS`지만 original-tempo preflight를 통과하므로 303D v2 정책을 fresh A0부터 학습할 수 있다.
승격 전 정본과 후보는 `training/history/20260830_user_delegated_strum_merge/`에 보존한다.
이미 실행 중인 구 run은 메모리에 로드된 이전 goal/contract를 계속 사용하며 새 canonical은 다음
fresh run부터 적용된다.

### 6.6 S2 양방향 끝줄·exit 완주 계약 (2026-08-31)

`20260830_1928_00_SS1-68-E_comp`의 S2 시작 구간은 up 완주율이 약 `99.3%`인 반면 down은
`0.1%` 미만이었다. down은 대부분 `5→4→3→2→1`까지 통과한 뒤 마지막 `0`번 줄을 남겼다.
S1에서 두 방향이 모두 약 `99.4%`였으므로 입력 방향 분포보다 S2 전이 시 끝점 유도의 구조적
비대칭으로 판정했다.

마지막 줄 하나만 남으면 `APPROACH` 목표를 줄의 진입점이 아니라 방향별 final-string→exit 선분의
exit로 바꾼다. 그 선분 투영의 지금까지 최대값만 `0..1`로 보상하므로 down/up에 같은 수식을 쓰며,
뒤로 왕복해도 양의 보상을 다시 얻지 못한다. 마지막 줄 RELEASE가 검출된 순간에는 timing gate와
독립된 one-shot physical-completion pulse를 준다. 따라서 물리 sweep 획득과 목표 시각 정렬은
분리하며, 과거의 지연 clawback을 다시 도입하지 않는다.

S2는 `E0_BALANCED_ENDPOINT`에서 먼저 양방향 물리 완주를 복구한 뒤 `T0_400MS`로 이동한다.
완료 episode의 down/up completed/event raw count를 각각 합쳐 최저 방향 완주율을 계산하고,
scheduled recovery completed를 물리 완료 수로 나눈 conditional rate와 전체 예정 사건 수로 나눈
end-to-end rate를 따로 gate한다. 한쪽 최저 방향 완주율이 `0.60` 미만인 evidence가 3회 연속이면
그 방향을 전체 학습 표본의 `70%`로 집중한다. 강제 focus가 아닌 `60%` 표본은 여전히 down/up
`30/30`의 balanced holdout이며 승급 evidence는 이 holdout만 사용한다. E0와 T0에서는
어깨·팔꿈치·손목 첫 9개 action의 정책 표준편차 하한을 `0.03`으로 유지한다.

이 절의 저장 계약은 checkpoint `v13`, curriculum `v13`, environment state `v14`였으며
Strike-v1의 역사적 재현 규칙이다. 현재 기본 Strike-v2로 exact resume하거나 전이하지 않는다.
동일한 327D 관측·30 action·goal/grip/asset/profile/recovery 계약을
가진 S1 최종 또는 S2 진입 직후(`stage_iteration=0`, S2 evidence 0) checkpoint는 사용자가
`--allow-policy-objective-transfer`를 명시한 경우에만 actor, observation normalizer와 학습된
`log_std`를 새 S2 run으로 가져올 수 있다. critic·optimizer·iteration·curriculum·환경 RNG는 모두
초기화한다. 기준 전이 소스는 `20260830_1928_00_SS1-68-E_comp/checkpoints/strike_003147.pt`다.

### 6.7 XPBD 입자 체인 스트랩 (opt-in, 2026-10-01)

기본값은 꺼져 있다(`guitar_fixed=True`, `strap_chain_config=None`). 이 경우 G0 동작은 바뀌지 않는다.
켜려면 `GuitarEnvBase(..., guitar_fixed=False, strap_chain_config="tab2body/assets/strap_chain.json")`로 생성한다.

- **모델**: 스트랩을 입자 24개 체인으로 본다(옷감 시뮬레이션의 1D 버전).
  - 양 끝은 기타 엔드핀과 힐 버튼에 고정한다.
  - 내부 입자는 중력, 장력 전용 거리 제약, 몸 capsule 충돌, Coulomb 마찰로 움직인다.
  - 경로: 엔드핀 → 오른쪽 겨드랑이 아래 → 등 대각선 → 왼쪽 어깨 위 → 가슴 앞 → 힐.
- **솔버** (각 선택은 CPU 실측에서 실패한 대안을 대체한 것):
  - 거리 제약은 체인 전체를 삼중대각 선형계로 한 번에 푼다. Gauss-Seidel은 24입자에서 수렴하지 못했고,
    남은 중력 늘어짐이 최대 42N의 가짜 장력으로 읽혔다.
  - active set은 풀기 전에 정한다(늘어났거나 장력이 있는 구간만). 풀어본 뒤 빼는 2-pass 방식은
    느슨한 스트랩에 에너지를 주입했다.
  - 충돌은 입자-capsule이 아닌 선분-capsule로 한다. 입자 간격(5.6cm)이 어깨 반지름보다 커서,
    입자 충돌만으로는 선분이 어깨를 관통해 고리가 빠졌다.
  - 장력은 수렴한 XPBD 승수(-λ/h²)에서 읽는다. 최종 위치의 늘어남은 감긴 구간에서
    20/90N이 번갈아 나오는 인공물을 남긴다.
  - 감쇠는 버튼 장력의 변화율로 건다(Kelvin-Voigt, τ = c·L/EA). 길이 변화율을 쓰면
    느슨하게 출렁이는 스트랩에서도 힘이 생겼다.
- **결합**: 60Hz 명시적 결합이다. `post_simulate`가 버튼과 capsule을 보간하며 스트랩을 전진시키고,
  다음 `simulate` 동안 `apply`가 힘과 COM 기준 토크를 건다.
  - 기타는 두 버튼 힘의 합력과 토크를 받는다.
  - 몸은 준정적 균형(스트랩 무게 − 기타가 받은 힘)을 접촉 비율대로 나눠 받으므로 스트랩이 운동량을 만들지 않는다.
- **reset**: 첫 reset에서만 스트랩을 몸에 밀착(cinch)시키고, 그 모양을 Chest 기준 템플릿으로 저장한다.
  이후 reset은 템플릿을 옮겨 놓고 4스텝만 적응시킨다. reset 직후 한 스텝은 body transform이
  stale이라 힘을 걸지 않는다.
- **몸 proxy 보강**: SMPL capsule은 팔이 앞으로 뻗으면 오른쪽 겨드랑이 뒤(견갑골)가 비어 있다.
  그래서 스트랩이 등을 타고 올라가 목걸이처럼 걸렸다. 이를 막으려고 config에 `R_Thorax` capsule
  하나와 골반 capsule(MJCF에서는 box)을 추가했다.
- **CPU 실측** (`tools/strap_chain_preview.py`, 기타를 4.5kg 병진 질점으로 수직 이동만 허용):
  - 처짐 9.6mm, 들어 올리는 힘 44.14N(무게 44.15N), 몸 하중 45.3N(= 무게 + 스트랩)
  - 관통 0mm, 약 1초 안에 정착(이후 ±0.5N, 0.2mm 잔떨림)
  - `--free`(지지 없음)는 왼쪽 어깨 아래로 진자처럼 흔들리며, 이는 물리적으로 정상이다.
- **미검증 (GPU 필요)**: Isaac 실제 결합 안정성, free guitar의 허벅지·손 접촉, `ENV_SPACE` 좌표 일치,
  4096 env 비용(`torch.linalg.solve` 23×23 배치 × 6 substep × 5회/step).
  검사: `python tests/test_strap_chain.py` (CPU, fake env로 coupler 기하·힘 검사 포함).
  GPU 확인: `python -m tab2body.tools.strap_chain_isaac_check` (영상·정지 이미지·`report.json`을
  `_gen/diagnostics/strap_chain_check/`에 쓰고, 검사 실패 시 exit 1).

## 7. 검증 도구

- 공용 배관 smoke — `python -m tab2body.train --task fret|strike --smoke --num-envs 8`.
  canonical 검수 전 Strike는 `--curriculum-stage A0_PICK_GRIP`을 함께 사용하고 full curriculum을
  시작하지 않는다.
- Strike bundle 읽기 전용 감사 —
  `python -m tab2body.tools.audit_strike_goal_quality --all --format human --strict`.
  `PASS`는 통과, `AMBIGUOUS`는 사람 검수 대기, `INFEASIBLE`은 full-song 학습 금지다.
  수정은 canonical에 직접 쓰지 않고 evidence가 있는 `*.proposed.json` 후보로 만든 뒤 오디오 승인,
  canonical 원자 교체, strict 재감사 순서로 수행한다.
- `tools/hold_compare.py` — 하체 홀드 5전략 떨림 비교(설계 근거).
- `tools/foot_settle.py` — 발 접지각 solve. `tools/render_pose.py` — base env 자세 렌더(4뷰). `tools/isaac_contact_audit.py` — 관통 감사.

## 8. 참조 문서
- 설계 정본: `PROJECT_CONTEXT.md` §3·§4와 `docs/archive/plans/`의 태스크별 문서.
- 이식 원본: `guitar/env.py`. 과거 DIGIT 실패 구현의 핵심 안티패턴은 이 문서에 요약되어 있다.
