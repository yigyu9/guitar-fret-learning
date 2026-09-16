# Pre-tanh Action Residual v1 구조 — 75D no-gaze baseline

> **상태: HISTORICAL PROTOTYPE.** 현재 105D FullBody 및 rule Synchronizer 계약과 호환되지 않는다.

이 문서는 양손 연주와 기타 안정화만 포함한다. Neck/Head gaze까지 포함한 81D 설계는 별도 architecture이며 이 v1 checkpoint를 재사용하지 않는다.

## 1. 이 모델이 하는 일

Fret과 Strike 정책을 다시 학습하거나 내부 latent를 수정하지 않는다. 두 정책이 제안한 pre-tanh 평균 행동을 이름 기준으로 합친 뒤, 새 모델이 작은 보정값을 더한다.

```text
μbase = assemble_by_joint_name(μfret, μstrike, μseated-neutral)
Δμ    = authority × cap × tanh(ResidualNetwork(context))
μjoint = μbase + scatter_by_joint_name(Δμ)
ajoint ~ tanh(Normal(μjoint, σjoint))
```

여기서 `σjoint`는 Fret/Strike의 동결된 `log_std`와 신규 body용 `log_std`를 이름 기준으로 조립한다. 각 source에서 먼저 action을 뽑아 다시 더하지 않는다. 그래야 PPO가 평가하는 log-prob과 실제로 실행한 확률분포가 일치한다.

## 2. Actor 입력

| 입력 블록 | raw 크기 | encoder 출력 | 포함할 정보 |
|---|---:|---:|---|
| Source intent | 60 | 64 | Fret 30 + Strike 30 pre-tanh 평균 |
| Goal/score | 128 | 64 | 현재·미래 음, 줄, 프렛, finger mapping, 타현 방향, deadline |
| Readiness | 64 | 64 | fret-ready dwell, pick 거리·속도, strike-ready, phase |
| Joint/history | 600 | 128 | 75 DoF별 각도·속도·limit margin·직전 action·직전 residual 등 8값 |
| Guitar/support | 128 | 64 | pose/twist, 접촉·slip, tether 강도·늘어남·힘, mode, 다음 충격 |

Goal 범주형 값은 checkpoint 내부 EventTokenEncoder가 처리한다. 나머지 블록은 Full runtime의 typed context packer에서 고정 물리 scale로 정규화한 뒤 encoder를 통과한다. packer 순서와 scale은 checkpoint manifest에 저장한다. 특히 G0에서 값이 0인 tether channel은 G1에서 RMS가 폭발하지 않도록 online RMS가 아니라 물리 단위 기반 고정 scale을 사용한다.

각 field의 정확한 의미, offset, 범주형 encoding, 좌표계와 valid-mask 계약은 [`ENCODING_SPEC.md`](ENCODING_SPEC.md)에 정의한다. `goal_encoder.py`, `context_encoding.py`, `context_pipeline.py`가 이 계약을 구현한다.

인코딩 결과 `64+64+64+128+64=384`를 합쳐 `384→512→256` ELU trunk에 넣는다.

## 3. Actor 출력과 관절 권한

| 출력 | 크기 | 역할 |
|---|---:|---|
| Arm residual | 18 | 양쪽 shoulder·elbow·wrist의 동기화 및 제한된 지지 보정 |
| Body residual | 15 | L/R Thorax와 Torso/Spine/Chest의 기타 안정화 |
| Finger residual | 0 | 양손 finger 42 DoF는 source 정책 전용 |

두 출력 head는 `256→128→출력`이고 마지막 layer의 weight와 bias를 모두 0으로 초기화한다. 보정은 raw 출력에 바로 더하지 않고 다음 순서를 거친다.

```text
raw residual
→ sign별 tanh bound
→ stage/phase residual authority mask
→ curriculum cap scale [0, 1]
→ cap_rad를 현재 base mean 주변의 방향별 pre-tanh cap으로 변환
→ 75D 위치로 name-based scatter
```

별도의 학습형 Arbiter는 두지 않는다. 이 deterministic mask·cap·name composer가 필요한 arbitration 역할을 수행한다.

## 4. 75D action 조립

현재 profile은 다음과 같다.

```text
Frozen Fret  : 왼 shoulder/elbow/wrist 9 + 왼손 finger 21 = 30
Frozen Strike: 오른 shoulder/elbow/wrist 9 + 오른손 finger 21 = 30
Body support : L/R Thorax 6 + Torso/Spine/Chest 9          = 15
합계                                                         75
```

숫자 구간으로 복사하지 않는다. `ActionResidualManifest`가 다음을 봉인하고 모든 조립을 관절 이름으로 수행한다.

- 정렬된 Full/Fret/Strike 관절 이름
- residual 허용 관절과 cap
- seated-hold pre-tanh neutral
- Fret/Strike checkpoint SHA-256
- architecture ID `full.action_residual.pre_tanh.v1`

Fret과 Strike action 이름이 겹치거나, source에 없는 팔을 arm residual로 지정하거나, SHA·neutral·cap이 잘못되면 시작 단계에서 실패한다.

## 5. 단일 확률분포

`MaskedJointTanhNormal`은 FP32 75D latent Normal에서 한 번만 sample하고 tanh를 한 번 적용한다. execution과 PPO credit mask는 별개다.

- PPO buffer에는 샘플 당시의 **FP32 pre-tanh latent**, `policy_action=tanh(latent)`, old log-prob을 함께 저장한다.
- update에서는 action을 `atanh`로 복원하지 않고 같은 latent를 새 분포에서 직접 평가한다. 포화된 action은 원래 latent 정보를 잃기 때문이다.
- 환경에는 stochastic-execution이 꺼진 slot을 seated-hold로 덮은 `executed_action`을 전달한다.
- PPO credit이 꺼진 slot은 log-prob·entropy·KL 합에서 제외한다. 따라서 frozen source finger는 sample·실행하면서 coordinator gradient에서는 제외할 수 있다.
- source 60D는 항상 실행하고, 신규 body 15D는 해당 residual authority가 꺼지면 stochastic noise까지 끄고 정확한 seated neutral로 고정한다.
- 이후 source별 PD scale 변환, 공통 EMA, PD target 계산은 환경에서 한 번만 수행한다.

## 6. Central critic

Actor와 parameter를 공유하지 않는 별도 critic을 둔다. Actor 입력에 더해 simulator에서만 정확히 얻을 수 있는 128D privileged context를 사용한다.

```text
actor-observable encodings 384
+ privileged encoding 64
= 448 → 512 → 256 → value 11
```

11개 value head는 현재 Fret의 줄별 6개, Strike 1개, joint event/sync 1개, guitar pose/twist 1개, support/slip/force 1개, assist/recovery/safety 1개다. guitar mass/inertia, 정확한 tether wrench처럼 실제 실행 시 알 수 없는 값은 critic에만 넣는다.

## 7. 학습 단계

| 단계 | 기타 | residual 권한 | 핵심 목적 |
|---|---|---|---|
| G0 | root 고정, gravity off | 팔 위주, body mask | 양손 timing 병합과 source 성능 보존 |
| G1a | free root + gravity + 강한 soft hand tether | body를 작은 cap부터 개방 | 안정화 동작 학습 |
| G1b | 약한/random tether + zero-tether probe | 팔·body 제한적 공동 보정 | 보조 연결 의존 제거 |
| G2 | tether 0 | 검증된 권한만 유지 | 실제 접촉만으로 완곡 연주 |

G1 이후에도 G0와 이전 단계 rollout을 섞어 학습한다. 총 reward만 보고 checkpoint를 고르지 않고, source 연주 성능·기타 안정성·보조 의존도 gate를 동시에 통과한 checkpoint만 승격한다.

## 8. Latent Sync와의 경계

| 항목 | 이 디렉터리 | 향후 `full/latent_sync/` |
|---|---|---|
| source hidden activation | 사용하지 않음 | 256D feature를 읽고 보정 |
| 보정 위치 | 최종 Linear 이후의 pre-tanh action mean | 최종 Linear 이전 latent |
| source actor API 변경 | 불필요 | feature hook/decoder 계약 필요 |
| 단순성·진단성 | 높음 | 낮음 |
| 표현력 | cap으로 제한된 직접 관절 보정 | source 내부 동작 표현까지 수정 가능 |

먼저 이 Action Residual을 G0에서 baseline으로 학습하고, 같은 평가 조건에서 성능이 부족할 때만 Latent Sync의 추가 복잡성을 정당화한다.

현재 패키지는 actor·critic·Goal embedding·context manifest/packer·source projection/calibration·물리 cap·분리 mask·joint distribution 계약까지 구현한다. `forward_structured_goal_physical_caps()`가 production actor 경로이며, 고정 logit cap과 단일 active mask 경로는 회귀 비교용이다. 공용 PPO의 단일 `obs` API와는 아직 다르므로, Full runtime에서는 source native observation 두 개와 coordinator context, pre-tanh latent, `policy_action`/`executed_action`을 분리하는 전용 wrapper가 필요하다.
