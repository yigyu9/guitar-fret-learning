# Action Residual 구현 계획과 완료 조건

> **상태: CLOSED HISTORICAL PLAN.** 이 계획의 I0 prototype은 보존하지만 이후 단계는 현재 Master Plan으로 대체되었다.

> 기준 architecture: `full.action_residual.pre_tanh.v1` — 75D/no-gaze  
> 원칙: 한 단계의 계약과 등가성 검증을 통과하기 전에 다음 단계의 PPO 학습을 시작하지 않는다.

## 1. 구현 범위

전체 작업은 다음 다섯 층으로 나눈다.

```text
I0  순수 tensor 계약·encoding
 ↓
I1  고정 기타 G0 Full runtime
 ↓
I2  G0 양손 동기화 PPO
 ↓
I3  free guitar + soft hand tether G1
 ↓
I4  tether 제거 + 완전 자유 기타 G2
```

I0는 구현과 CPU 계약 테스트를 완료했다. I1부터는 `tab2body`의 실제 asset, observation, action, PPO 경로에 연결한다.

## 2. I0 — Encoding과 action 안전 계약

### 구현 항목

- field/block manifest
  - name, offset, size, 내부 component 순서, unit, frame, scale, clip, valid 규칙
  - block별 정확한 dimension 검산
  - canonical JSON과 SHA-256
- Goal encoding
  - global clock 8D
  - 현재+다음 3 event
  - finger categorical embedding
  - 공유 EventTokenEncoder와 invalid slot zeroing
- Readiness 64D, Joint/history 600D, Guitar/support 128D, Privileged 128D packer
- 고정 물리 scale 정규화와 finite/range validation
- residual authority, stochastic execution, PPO credit의 세 mask 분리
- source 60D는 항상 실행하고 authority가 없는 신규 body 15D는 seated neutral로 고정하는 profile mask
- radian cap을 현재 base action 주변의 방향별 pre-tanh cap으로 변환
- source raw/projected 입력을 tagged type으로 구분하고 frozen RMS를 정확히 한 번만 적용
- 관절 순서·value-head 순서·static context schema가 같은 shape 뒤에 숨지 않도록 semantic checkpoint 검증
- 실제 joint limit·velocity scale을 포함한 pipeline hash 생성(Full envelope binding은 I1)
- 확률 계산은 FP32 pre-tanh latent를 저장하고 재평가하는 경로로 고정
- 기존 flat-context API와의 호환 경로

### 완료 조건

- 모든 block의 offset이 겹치지 않고 마지막 offset이 정확한 width와 일치
- manifest hash가 같은 입력에서 결정적이며 field 하나가 바뀌면 달라짐
- invalid optional sensor의 payload가 정확히 0이고 valid bit가 0
- invalid category, nonfinite, 잘못된 shape는 fail closed
- invalid Goal event token 출력이 bias 학습 뒤에도 정확히 0
- physical cap 적용 뒤 deterministic PD target 변화가 `cap_rad`를 넘지 않음
- source finger는 실행될 수 있지만 coordinator PPO credit에서는 제외 가능

### 현재 상태 — DONE

| 항목 | 상태 | 코드 |
|---|---|---|
| Goal categorical/event encoding | DONE | `goal_encoder.py` |
| Readiness·Joint·Guitar·Privileged manifest/packer | DONE | `context_encoding.py`, `context_pipeline.py` |
| source projected legacy 순수 연산 | DONE | `source_projection.py` |
| source-intent robust calibration 알고리즘 | DONE / CALIBRATION_REQUIRED | `source_intent.py` |
| 세 action mask와 joint distribution | DONE | `action_safety.py`, `distribution.py` |
| 방향별 physical residual cap | DONE / CALIBRATION_REQUIRED | `action_safety.py`, `model.py` |
| actor·critic structured 경로와 static semantic checkpoint | DONE | `model.py`, `critic.py` |
| concrete context-pipeline hash 생성 | DONE / I1 BINDING REQUIRED | `context_pipeline.py` |

`python full/action_residual/tests/run_all.py`에서 6개 test module, 총 35개 계약 test가 통과한다. `CALIBRATION_REQUIRED`는 알고리즘이 없다는 뜻이 아니라 실제 source rollout 통계와 관절별 안전 cap 수치가 아직 봉인되지 않았다는 뜻이다.

## 3. I1 — 고정 기타 G0 Full runtime

### 3.1 공통 event compiler

Fret frame cursor와 Strike `song_time/event_index`를 각각 진행하지 않는다. 하나의 `score_frame@60Hz`와 immutable event timeline을 만들고 다음을 제공한다.

- current + next 3 event
- fret window, strike window, onset, deadline, release
- 줄별 fret/finger/state
- audible/traversal mask, direction, per-string offset
- song ID와 timeline SHA-256

한 physics step에서 event cursor는 한 번만 읽고, gate가 닫혀도 clock은 계속 진행한다.

### 3.2 Frozen source pair loader

- 동일 곡·동일 timeline인 Fret/Strike checkpoint만 허용
- checkpoint SHA, action-name order, observation dimension, RMS hash 검증
- Fret 425D field manifest 생성
- Strike 327D 기존 manifest 검증
- source actor/RMS/log_std 동결과 rollout 전후 tensor-content hash 비교
- source adapter에는 bare tensor가 아니라 `RawSourceObservation` 또는 projector가 만든 tagged observation만 전달
- source projection manifest의 RMS hash와 실제 source policy `obs_rms`를 exact 비교

### 3.3 Projected source observation

- 자기 관절과 자기 손의 live guitar-relative geometry 유지
- 반대 손·신규 body·Neck/Head raw q/qdot은 source RMS mean으로 치환
- source 이전 action은 공통 EMA 이후 75D에서 이름으로 gather
- `projected_legacy`와 `live_all` A/B metric 기록

### 3.4 75D action runtime

- 실제 ordered DOF name에서 75D profile 생성
- source action transform과 Full `ctrl_mid/half/action_scale` 등가성 audit
- seated-hold neutral 계산과 checkpoint 봉인
- 한 joint TanhNormal sample
- deployment transform 후 공통 EMA 정확히 1회
- FP32 pre-tanh `latent`, `policy_action`, `executed_action`을 서로 분리 저장
- `policy_action → inactive neutral → source별 deployment transform → 공통 EMA 1회 → PD target` 실행 trace 기록
- 실제 `env.ctrl_idx`의 ordered name과 75D manifest exact equality 검증
- 실제 lower/upper limit·velocity scale로 만든 `ActionResidualContextPacker.schema_sha256`를 actor·critic과 같은 Full checkpoint envelope에 봉인하고 load 전에 선검증

### 3.5 Readiness API

기존 reward 내부 local metric을 직접 읽지 않고, 같은 common event와 snapshot을 받는 순수/cached API를 만든다.

- 줄별 press quality, assigned finger correctness, dwell
- chord hard-ready와 soft bottleneck
- pick entry/exit/velocity, lane, clearance, detector state
- guitar stable dwell
- `strike_permission`

post-physics에서는 fret readiness를 먼저 계산하고 같은 frame의 crossing 판정에 사용한다.

### 완료 조건 — S0 zero-residual equivalence

동일 song/seed/start frame에서 다음이 기존 source 단독 실행과 일치해야 한다.

- source native observation과 normalized observation
- source pre-tanh mean과 log_std
- deterministic source action
- deployment transform 결과
- 공통 EMA 한 step 결과
- 최종 PD target

이 등가성이 실패하면 PPO를 시작하지 않는다.

## 4. I2 — G0 양손 동기화 PPO

### 구현 항목

- Full 전용 rollout transition
  - frozen source proposal 또는 이를 재현할 projected raw observation과 source hash
  - trainable Goal encoder를 다시 실행할 raw `GoalScoreBatch`
  - Readiness·Joint·Guitar·Privileged context
  - FP32 pre-tanh latent, policy action, old log-prob
  - residual authority·execution·PPO-credit mask와 `cap_rad/cap_scale`
  - normalization snapshot ID
  - 이전 residual/rate/EMA state
  - value/reward 11D
- old/new log-prob 모두 저장 latent로 계산하고 action→`atanh` 복원은 학습에서 금지
- 동일 mask·cap·source proposal·schema snapshot으로 PPO epoch 전체를 재평가
- active dimension만 사용하는 PPO ratio, entropy, KL
- source parameter와 RMS가 optimizer에 포함되지 않는 audit
- rule baseline: fret-ready dwell까지 strike gate, deadline 뒤 skip
- zero-residual·rule-only·learned residual의 paired evaluation

### 완료 조건

- frozen source tensor hash 불변
- source finger residual 정확히 0
- Fret/Strike 핵심 지표가 source baseline 대비 허용 범위 안에서 유지
- premature strike 감소와 joint event 성공률 개선
- residual RMS/p95/cap saturation이 허용 범위 이내
- G0 rehearsal에서 catastrophic forgetting 없음

## 5. I3 — Free guitar, physical strap과 hand tether

G0와 G1은 asset-load 계약이 다르므로 같은 environment instance 안에서 root 고정을 토글하지 않는다.

### 물리 구현

- guitar `free root + gravity on` asset profile
- `strap_sim`에서 검증한 `strapped-v1` maximum-length cable을 메인 physics component로 이식
- humanoid surface guide와 per-link reaction force 적용
- guitar button/exit guide와 body·neck collision proxy를 추가하고 전 선분 비관통 검사
- body별 finite positive mass/inertia, total mass/CoM load-time audit
- Fret thumb proxy와 Strike pluck-range를 함께 설정하는 Full collision profile
- reset pose/twist와 anchor constraint energy 검증
- reset 직후 한 frame tether valid latch
- 양손 support anchor의 anisotropic spring-damper
  - hard weld 금지
  - dead zone/slack, force cap, slew-rate cap
  - 가능한 경우 손과 기타에 equal-and-opposite force
  - `c ≈ 2ζ√(k m_eff)`로 stiffness와 damping을 함께 감소

### 안정화 관측·보상

- guitar pose/twist, gravity-in-guitar
- support anchor geometry와 측정 가능한 slip/load proxy
- assist lambda, extension, tension, work와 valid bit
- pose/twist, support/slip/over-force, assist-dependence reward 분리
- strike 동작과 실제 support contact 변화 뒤의 settling metric

Strike detector는 가상 string의 kinematic crossing만 판정한다. Crossing은 기타에 인공
force·torque·impulse를 적용하지 않으며, 이 조건을 physics manifest에 봉인한다.

## 6. I4 — Artificial tether 제거와 strapped G2

- G1a strong tether: Sync 경로 freeze, Support만 학습
- G1b weak/random tether: episode별 lambda, exact zero-tether probe 혼합
- G2 artificial tether=0, physical strap 유지: 짧은 phrase → full song → 물성·외란 randomization
- 현재 stage 50–60%, 직전 stage 20–30%, G0 20% 정도의 rehearsal 후보
- 모든 이전 단계 gate를 동시에 통과한 checkpoint만 승격

승급은 가중합 return이 아니라 다음 AND 조건으로 판단한다.

```text
source performance retained
AND joint timing passed
AND guitar stable
AND assist dependence low
AND safety passed
```

## 7. 파일 경계

| 위치 | 책임 |
|---|---|
| `full/action_residual/` | architecture, pure encoding/action contracts, CPU tests |
| `tab2body/env/tasks/task_full.py` | 한 physics state와 common event를 소유하는 Full environment |
| `tab2body/env/rewards/hold.py` | 기타 안정화 reward와 metric |
| `tab2body/learning/` | Full rollout/PPO wrapper와 checkpoint contract |
| `tab2body/train_full.py` | stage config, source pair loader, train/eval entrypoint |
| `tab2body/tests/test_full_contract.py` | 실제 environment integration과 S0 equivalence |

순수 contract가 Isaac Gym import에 의존하지 않도록 유지한다. simulator tensor를 읽는 코드는 `tab2body/env`에 두고, 검증·encoding 규칙은 `full/action_residual`에서 재사용한다.

## 8. 구현 상태 표기

상태는 `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`만 사용한다. `DONE`은 코드 작성만이 아니라 해당 완료 조건의 자동 test가 통과했음을 뜻한다. calibration 값이 임시이면 `DONE`으로 표시하지 않고 `CALIBRATION_REQUIRED`를 함께 기록한다.
