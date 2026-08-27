# tab2body/env — 설계 문서 (base.py가 왜 이렇게 구성되었는가)

> 이 문서는 `base.py`(공유 환경 코어)의 **모든 설계 결정과 그 근거**를 정리한다.
> 근거 표기: **[G]**=guitar/(Pei Xu SA'24, 이식 원본) · **[D]**=과거 DIGIT 실패 분석(안티패턴) ·
> **[P]**=PROJECT_CONTEXT(설계 정본·실측 함정) · **[M]**=이 프로젝트에서 직접 실측(도구 명시).
> 최종 갱신: 2026-08-03. 현재 배관 smoke는 `python -m tab2body.train --task ... --smoke`로 실행한다.

---

## 0. base.py는 무엇인가

장기 파이프라인은 **fret[A] ∥ strike[B] → 결합[A+B] → 기타 스테이징 G0→G1→G2**지만,
2026-07-27 현재 fret[A]와 새 pick-only strike[B]가 각각 실행 가능하다.
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
| `rewards/hold.py` | 기타 안정 (G1 스트랩) | ⬜ W2+ |
| `tasks/task_fret.py` | 33DOF 제어·428D 관측·goal/reward/R13 손바닥 종료/F1 집계·4-tuple step | ✅ S0 |
| `strike_goals.py` | 최소 `[time,frame,string]` goal 검증·60 Hz canonical timeline | ✅ v1 |
| `strike_detector.py` | goal 독립 finite swept crossing·RELEASE·물리 re-arm·zone quality | ✅ CPU/CUDA |
| `rewards/strike.py` | A0~A4 stage-mask scalar reward와 guitar reference grip | ✅ v1 |
| `tasks/task_strike.py` | 30DOF·263D 관측·3 motor phase·event matching/진단 | ✅ GPU audit/smoke |
| `tasks/task_full.py` | 후속 병합 태스크 조립 | ⬜ |

---

## 2. 핵심 설계 결정과 근거

### 2.1 신 구성 (씬·액터)

**휴머노이드·기타 별도 2액터 + 의자 박스, env별 순차 생성.**
- *왜 별도 액터:* 기타 스테이징 G0(월드고정)→G1(스트랩)→G2(자유)를 **에셋 재작성 없이 `fix_base_link` 플래그만으로** 전환하기 위함([P] §5.1). 결합 멀티루트 MJCF는 Isaac 미검증이라 IK/렌더용으로 강등.
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

모든 바디 상태를 **기타 로컬 프레임**으로 표현(`to_guitar_frame`). G0에선 기타가 정적이라 월드프레임과 동일하지만, **같은 코드가 G1/G2로 그대로 이어져** weld→free 전이가 정책에 **투명**해진다 — 구 파이프라인의 좌손 0.90→0.18 붕괴가 바로 이 프레임 단절이었다.
- *[M]/[G] 주의:* guitar/env.py L879/L884의 쿼터니언 conjugation 버그는 **기타가 월드고정일 때만 무해**(상수 회전=학습가능 상수). 우리 기타는 움직이므로 base.py는 **정확한 역회전**(`quat_rotate_inverse`)을 쓴다 — 버그를 이식하지 않는다.
- (`isaacgym.torch_utils`는 이 numpy 버전에서 `np.float` 때문에 임포트 실패 → 쿼터니언 유틸을 base.py에 직접 정의.)

### 2.6 control_dofs 분할 — 한 몸, 태스크별 제어 집합

`control_dofs`(관절 이름 접두사) → `controlled`/`ctrl_idx`/`num_actions`. fret[A]는
`L_Thorax~L_Wrist + 왼손 다섯 손가락` 33DOF만 제어하고 몸통은 고정한다.
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
- **접촉 텐서**: `contact_force` (net force) — pluck 검출·G2 마찰용(⚠️[D] item3: XML site 없으면 0 출력 → 보상 전 실측 확인).
- **버퍼**: `progress_buf`/`reset_buf`/`obs_buf`/`prev_action`, `root_init`(G1 자유기타 리셋 훅).

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

## 5. guitar/ (27DOF 부유손) → 우리 (105DOF 좌식) 적응

- **직행**: Env/tensor 골격, RSI(ReferenceMotion), observe_iccgan(parent_link), 멀티크리틱 reward 인터페이스, goal/note/timer 기계.
- **바꿈**: `disable_gravity` 끔(몸통 중력), 게인=SMPL 스케일(mjcf_gains), vel_iter 0→2, 종료=자세기반, 쿼터니언 버그 수정.
- **[P] 신규 난제(참조 없음)**: 좌식 하체 접촉 안정(§2.3), 전신 자기충돌(§2.4), 한 몸 제어분할+결합(§2.6), G1/G2 기타 결합(스트랩 spring-damper+관성+obs).

---

## 6. 완료 상태 (base 코어)

**[DONE]** 2액터 씬·하이브리드 PD·하체 3중 잠금·충돌규약·접촉오프셋·control_dofs 분할·기타상대 관측 변환·기본 관측 빌더·액션 EMA+스케일·RSI reset·종료·step API·접촉 텐서·버퍼·RNG.
**[MISSING → 후속]** full 결합 goal·reward, disc 관측(스타일),
PopArt/AdaptNet, G1 자유기타 root/스트랩 plumbing.

### 6.1 S0 fret 확장 (2026-07-19)

`base.py` 코어는 유지하고 task subclass에서 goal/reward를 배관했다. `obs_buf`의 base-prefix 기록만
확장 관측과 공존하도록 수정. `FretTask`: obs 428
(기본180+goal128+EMA actuator state33+thumb geometry12+미래 goal75), actions 33,
reward/value 6. 현재 checkpoint contract는 이 차원을 포함한다. 이전 353D 정책은 명시적
초기화로만 확장하며, 구 341D·37-action checkpoint는 strict resume하지 않는다.

### 6.2 pick-only strike 확장 (2026-07-27)

`StrikeTask`는 어깨부터 손가락까지 30 action, 고정된 263D actor observation, scalar value/reward를
사용한다. 공개 motor phase는 `READY/APPROACH/RELEASE_RECOVER` 세 개이며, 실제 성공 시점은
별도 detector의 swept crossing RELEASE pulse다. A0 grip, A1 ready, A2 crossing, A3 timing,
A4 zone을 성능 기반으로 승급하고 A3 허용 오차를 100→67→50 ms로 줄인다. GPU runtime audit에서
6줄 finite segment, 충돌 필터, 5단계 tensor 유한성을 확인했다. A1~A4는 완료 episode의 exact
지표만 승급 증거로 쓰며, timing p95에는 허용창 밖의 유효 target crossing도 포함한다. A4 sampled
lane은 `±6 mm` 만점, `±12.5 mm` 성공 경계다.

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

## 7. 검증 도구

- 공용 배관 smoke — `python -m tab2body.train --task fret|strike --smoke --num-envs 8`
- `tools/hold_compare.py` — 하체 홀드 5전략 떨림 비교(설계 근거).
- `tools/foot_settle.py` — 발 접지각 solve. `tools/render_pose.py` — base env 자세 렌더(4뷰). `tools/isaac_contact_audit.py` — 관통 감사.

## 8. 참조 문서
- 설계 정본: `PROJECT_CONTEXT.md` §3·§4와 `docs/plans/`의 태스크별 문서.
- 이식 원본: `guitar/env.py`. 과거 DIGIT 실패 구현의 핵심 안티패턴은 이 문서와
  `docs/base-env-research.md`에 요약되어 있으며, 원본 디렉터리는 정리되었다.
