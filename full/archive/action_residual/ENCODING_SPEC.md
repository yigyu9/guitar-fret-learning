# Action Residual 입력·출력 상세 명세

> **상태: HISTORICAL PROTOTYPE.** 75D/Fret-v1/Strike-v1 입력 계약을 보존하며 현재 G0 runtime 계약으로 사용하지 않는다.

> 대상: `full.action_residual.pre_tanh.v1` — 75D, no-gaze baseline  
> 상태: **I0 순수 encoding·action 안전 계약 구현 완료**. field-level packer와 모델 연결은 구현했으며, simulator에서 신호를 만드는 Full runtime과 자유 기타 물리는 아직 구현되지 않았다.

## 1. 전체 흐름

Action Residual은 기존 Fret·Strike 정책을 대체하지 않는다. 각 정책은 원래 입력 형식으로 동결된 채 실행되고, coordinator는 두 정책의 행동 제안과 Full 환경의 공통 상태를 읽어 작은 행동 보정만 만든다.

```text
같은 physics snapshot + 하나의 곡 clock
        │
        ├─ Fret native view 425D ─→ Frozen Fret ─→ μF 30D, log σF
        │
        ├─ Strike native view 327D → Frozen Strike → μS 30D, log σS
        │
        └─ Full context packer
              ├─ Goal/score        128D
              ├─ Readiness          64D
              ├─ Joint/history     600D
              └─ Guitar/support    128D

μF 30 + μS 30 ───────────────────── Source intent 60D
                          │
                          ▼
                Action Residual Actor
                          │
             arm Δu 18D + body Δu 15D
                          │
        joint-name compose + deterministic masks/caps
                          │
             하나의 75D TanhNormal에서 1회 sample
                          │
                  common EMA 1회 → PD target
```

여기서 `μ`는 최종 action도, 신경망 weight도 아니다. 각 frozen actor의 마지막 Linear가 출력한 **tanh 이전 Normal 평균**이다. Action Residual은 source hidden activation을 읽지 않으므로 Latent Sync와 구분된다.

## 2. 두 Frozen source에 들어가는 입력

Coordinator용 입력을 만들기 전에 두 source 정책이 정상적으로 행동을 제안할 수 있어야 한다. 기존 source observation의 shape·순서·정규화는 바꾸지 않는다.

| Source | 기존 observation | 구성 | 출력 |
|---|---:|---|---:|
| Fret | 425D | base 180 + goal 128 + 이전 실행 action 30 + thumb 12 + future 75 | 30D |
| Strike | 327D | base 171 + strike 명시 정보 126 + 이전 실행 action 30 | 30D |

Fret base 180D는 `q 81 + qdot 81 + guitar-local body 위치 18`, Strike base 171D는 `q 81 + qdot 81 + 오른손 wrist/palm/pick 위치 9`다. 과거 문서의 Fret 428D, Strike 321D는 현재 코드와 맞지 않는다.

### 2.1 Projected legacy view

Full 환경에서는 반대 손과 몸통도 함께 움직이므로 source에 모든 live 상태를 그대로 주면 source 학습 분포에서 벗어날 수 있다. 초기 기본값은 다음 `projected_legacy` view로 한다.

- source가 소유한 관절의 `q`, `qdot`: live 값
- 자기 손·wrist·pick·thumb의 기타 상대 geometry: **움직이는 현재 기타를 기준으로 한 live 값**
- source의 goal, phase, detector 정보: 공통 Full event에서 만든 live 값
- source의 이전 action: Full의 공통 EMA 이후 75D 실행값에서 source 관절 이름으로 gather한 30D
- 반대 손, 신규 body 15D, Neck/Head의 `q`, `qdot`: source checkpoint의 raw observation RMS mean으로 치환
- 그 다음에 source checkpoint의 동결된 observation RMS 적용

RMS 적용 뒤 값을 덮으면 안 된다. raw 단계에서 RMS mean으로 치환해야 정규화 결과가 정확히 0이 된다. 기존 source policy API가 내부에서 RMS를 적용하므로 adapter에는 projector가 만든 tagged `raw_projected`를 전달한다. bare tensor 입력은 native raw인지 이미 정규화된 값인지 구분할 수 없어 금지한다. projection 모듈의 `normalized_audit`는 등가성 확인에만 쓰며 actor에 전달하면 안 된다. 반대로 자기 손의 기타 상대 geometry까지 고정하면 움직이는 fretboard와 string을 추종하지 못하므로 반드시 live로 둔다.

현재 `RunningMeanStd` 계약과 동일하게 `(x-mean)/sqrt(var+1e-8)` 후 `[-5,5]` clip을 사용한다. projection, frozen source inference, joint distribution과 log-prob은 FP32로 고정한다. epsilon과 clip도 projection manifest/hash에 포함하고 실제 policy `obs_rms`와 exact 비교해 source 구현과 달라지면 실패시킨다.

Fret에는 현재 field-level observation manifest가 없으므로 Full 학습 전에 425개 항목의 이름과 offset을 새로 봉인해야 한다. 두 source actor, source RMS, source `log_std`는 `eval + no_grad`로 영구 동결하며 optimizer에서 제외한다.

## 3. Actor의 다섯 입력 블록

```text
Source intent   60 → 128 →  64
Goal/score     128 → 128 →  64
Readiness       64 → 128 →  64
Joint/history  600 → 256 → 128
Guitar/support 128 → 128 →  64
                              ───
concat                         384 → 512 → 256
```

각 Linear 뒤에는 ELU를 사용한다. hidden Linear는 orthogonal initialization, bias 0을 사용하며 BatchNorm과 dropout은 사용하지 않는다. 서로 단위가 다른 raw block 전체에 하나의 RMS를 적용하지 않는다.

### 3.1 Source intent 60D

```text
offset  0:30  Frozen Fret pre-tanh mean μF
offset 30:60  Frozen Strike pre-tanh mean μS
```

이 입력은 “source가 어느 관절을 어느 방향으로 움직이려 하는가”를 coordinator에 알려준다.

두 용도를 분리한다.

1. **75D base mean 조립용**: source의 raw `μF`, `μS`를 그대로 사용한다.
2. **신경망 입력용**: source별로 동결된 calibration을 적용한 복사본을 사용한다.

권장 calibration은 각 source·각 관절별 offline rollout에서 center와 robust scale을 계산하고 checkpoint manifest에 저장하는 방식이다.

```text
xj = clip((μj - centerj) / max(scalej, ε), -5, 5) / 5
```

Fret과 Strike 통계를 섞지 않는다. calibration 전 임시값으로 `clip(μ, -5, 5) / 5`를 쓸 수 있지만 checkpoint에는 `CALIBRATION_REQUIRED`로 표시한다. source proposal이 nonfinite이거나 관절 이름·순서·checkpoint SHA가 다르면 zero로 대체하지 않고 즉시 실패시킨다.

v1 actor 입력은 `μF + μS`만 사용한다. `tanh(μ)`와 `1-tanh(μ)^2` 같은 saturation 정보는 유용할 수 있지만, 추가하면 입력 폭과 architecture ID가 바뀌므로 별도 ablation으로 다룬다. source `log_std`는 actor 입력이 아니라 최종 75D 분포의 표준편차 조립에만 사용한다.

### 3.2 Goal/score 128D

악보 정보에는 연속값, mask, 범주형 값이 섞여 있다. finger ID나 방향을 `1, 2, 3, 4` 같은 연속 숫자로 넣으면 숫자 간 거리가 의미가 있는 것처럼 오해하게 된다. 따라서 범주형 값은 one-hot 또는 trainable embedding으로 처리한다.

권장 구조는 현재 event와 다음 3개 event를 **같은 EventTokenEncoder**로 처리하는 것이다.

```text
Global clock 8D
Event[0] raw record → shared EventTokenEncoder → 30D
Event[1] raw record → shared EventTokenEncoder → 30D
Event[2] raw record → shared EventTokenEncoder → 30D
Event[3] raw record → shared EventTokenEncoder → 30D
                                                   ────
Goal context                                      128D
```

`Event[0]`은 현재 해결되지 않은 event, `Event[1:3]`은 다음 세 event다. chord와 strum은 줄마다 별도 event로 쪼개지 않고 하나의 atomic event로 표현한다.

#### Global clock 8D

| offset | 항목 | encoding |
|---:|---|---|
| 0 | song progress | 전체 길이 대비 `[0, 1]` |
| 1:3 | beat phase | `sin(phase), cos(phase)` |
| 3:5 | bar phase | `sin(phase), cos(phase)` |
| 5 | tempo ratio | 기준 tempo 대비 비율을 고정 scale로 clip |
| 6 | clock running | boolean |
| 7 | timeline valid | boolean |

절대 event ID는 정책 입력에 넣지 않고 logging과 무결성 검사용으로만 쓴다. 시간 gate 때문에 곡 clock을 멈추지 않는다.

#### Event raw record와 30D token

각 event의 semantic record는 다음 정보를 가진다.

| 항목 | raw 표현 | 이유 |
|---|---:|---|
| event valid | 1 | padding과 실제 0값 구분 |
| `dt_fret_window_open`, `dt_strike_window_open`, `dt_onset`, `dt_deadline`, `dt_release` | 5 | 모두 `event_time - song_time`의 signed seconds |
| 줄별 목표 상태 | `4 × 6` one-hot | `DONT_CARE / OPEN / FRETTED / MUTED`를 구분 |
| 줄별 목표 fret | 6 | fretboard 길이 기준 `[0,1]`; FRETTED가 아닐 때 0 |
| 줄별 finger ID | 6 categorical → 각 4D embedding | `NONE / index / middle / ring / little` |
| audible mask | 6 | 최종 발음 대상 줄 |
| traversal mask | 6 | pick이 실제로 지나갈 줄 |
| strike direction | 3 one-hot | `NONE / DOWN / UP` |
| 줄별 strike offset | 6 | chord/strum 내부 상대 시각, signed seconds |
| gesture | 3 one-hot | `single / strum / restrike` |
| atomic event | 1 | 모든 필요한 fret이 함께 준비되어야 하는지 |

finger embedding 후 event 입력은 85D이며, 공유 MLP `85→64→30`으로 token을 만든다. 네 slot이 같은 weight를 사용해야 같은 음의 의미가 slot 위치에 따라 달라지지 않는다. 다만 token의 concat 순서가 현재/미래 거리를 알려준다. invalid slot은 `valid=0`, payload=0으로 만들고 encoder 출력도 valid로 한 번 더 곱해 정확히 0으로 만든다.

시간은 예를 들어 onset은 2초, window 경계는 0.5초, string offset은 0.25초로 나누고 `[-1,1]` clip한다. 이 값은 초기 calibration 후보이며 실제 곡 분포를 측정한 뒤 manifest에 봉인한다. event가 2초 밖에 있다는 이유로 invalid 처리하지 않고, 실제 event가 없을 때만 invalid로 둔다.

`goal_encoder.py`가 EventTokenEncoder를 구현하고 actor와 critic checkpoint에 각각 포함한다. 실제 Full 경로는 `forward_structured_goal*()`을 사용한다. 기존 128D flat 입력은 회귀 테스트와 ablation 호환을 위해 남겨 두었으며, 외부 packer가 숫자 finger ID를 연속 scalar로 넣는 방식은 사용하지 않는다.

### 3.3 Readiness 64D

Goal이 “무엇을 언제 해야 하는가”라면 Readiness는 “지금 실제로 준비되었는가”를 표현한다.

#### 공통 phase와 gate — 15D, offset `0:15`

| offset | 항목 | 크기 |
|---:|---|---:|
| 0:5 | `PREPARE / APPROACH / STRIKE / HOLD / RECOVER` | 5 one-hot |
| 5 | fret global ready | 1 |
| 6 | strike ready | 1 |
| 7 | guitar stable | 1 |
| 8 | strike permission | 1 |
| 9 | deadline missed | 1 |
| 10 | recovery active | 1 |
| 11 | action/history valid | 1 |
| 12:15 | fret-ready, strike-ready, guitar-stable dwell fraction | 3 |

최종 permission은 명시적 deterministic gate다.

```text
strike_permission = fret_ready_dwell
                  AND guitar_stable_dwell
                  AND strike_ready
                  AND strike_window_open
                  AND NOT deadline_missed
                  AND NOT recovery_active
```

`strike_window_open`은 Goal의 signed window time에서 계산해 `ReadinessPacker`의 gate 검증 입력으로 함께 전달한다. 64D에는 결과인 `strike_permission`만 저장해 중복 폭을 늘리지 않는다. deadline을 넘으면 clock을 멈추고 기다리지 않고 해당 strike를 miss/skip 처리한다. packer는 near-zero binary도 먼저 정확한 0/1로 canonicalize하고, permission이 위 AND 결과와 정확히 같은지 검사한다.

#### 왼손 줄별 readiness — 30D, offset `15:45`

Goal과 동일한 canonical string order `high_e, B, G, D, A, low_E`의 각 줄마다 다음 5개를 둔다.

```text
[press_required,
 measurement_valid,
 press_quality,
 assigned_finger_correct,
 ready_dwell_fraction] × 6 strings
```

`press_quality`는 단순 contact bit가 아니라 fret 위치 오차, 접촉, 누름 유지 상태를 `[0,1]`로 합친 soft 값이다. hard ready는 event 성공 판정과 gate에, soft quality는 PPO shaping에 사용한다. chord는 필요한 모든 줄의 hard ready를 AND한 값과 soft-min/bottleneck 품질을 함께 계산하되, actor vector에는 줄별 값과 global ready를 넣는다.

#### 오른손 pick readiness — 19D, offset `45:64`

| 상대 offset | 항목 | 크기 |
|---:|---|---:|
| 0 | pick geometry valid | 1 |
| 1:4 | pick에서 entry까지 벡터, guitar frame | 3 |
| 4:7 | pick에서 exit까지 벡터, guitar frame | 3 |
| 7:10 | pick의 string 대비 상대속도, guitar frame | 3 |
| 10 | 목표 lane 오차 | 1 |
| 11 | traversal 방향 속도 | 1 |
| 12 | clearance margin | 1 |
| 13:19 | 줄별 detector armed | 6 |

거리·속도는 world frame이 아니라 움직이는 기타/string frame에서 계산한다. 초기 scale 후보는 일반 거리 0.20m, lane 0.03m, clearance 0.05m, pick 속도 2m/s다.

Readiness 입력 `s_t`는 action을 만들기 직전 하나의 snapshot에서 계산한다. simulation 뒤 `s_{t+1}`에서 fret readiness를 먼저 갱신한 후 같은 frame의 strike crossing 성공을 판정해야 한다. Fret과 Strike가 서로 다른 event cursor를 사용하거나 전 frame의 압현 상태를 재사용하면 1-frame timing bug가 생긴다.

### 3.4 Joint/history 600D

75개 관절을 `ActionResidualManifest.joint_action_names` 순서로 놓고, 관절마다 연속 8개 feature를 둔다. 관절 `j`의 시작 offset은 `8j`다.

| `8j + k` | 항목 | encoding |
|---:|---|---|
| 0 | 현재 관절각 `q` | `2(q-lo)/(hi-lo)-1` |
| 1 | 현재 관절속도 `qdot` | 관절군별 물리 `vmax`로 나누고 clip |
| 2 | lower limit margin | `(q-lo)/(hi-lo)`, `[0,1]` |
| 3 | upper limit margin | `(hi-q)/(hi-lo)`, `[0,1]` |
| 4 | 직전 최종 실행 action | source transform과 공통 EMA 이후 normalized action |
| 5 | 직전 residual / cap | cap 대비 `[-1,1]` |
| 6 | residual 변화량 / rate cap | 직전 두 residual의 차이, `[-1,1]` |
| 7 | effective authority | `authority_mask × cap_scale`, `[0,1]` |

검산은 `75 × 8 = 600`이다. source finger 42D는 residual authority가 없으므로 residual·rate·authority가 0이다. inactive body 관절의 직전 실행 action은 숫자 0이 아니라 seated-hold normalized action이다.

PPO minibatch는 시간순이 아니므로 minibatch의 앞 행을 “이전 step”으로 사용하면 안 된다. rollout 시점에 이전 residual과 rate를 계산해 transition에 직접 저장한다. asynchronous reset에서는 EMA, residual history, detector, dwell, contact filter를 초기화하고 `history_valid=0`으로 한 step 표시한다.

### 3.5 Guitar/support 128D

두 좌표계를 사용한다.

- `G`: 매 step 갱신되는 guitar-local frame. pick, support site, contact, force, slip 표현에 사용
- `B`: 사람 기준 support frame. 권장값은 Pelvis 원점 + world-up + pelvis yaw다. 기타 기준자세 오차와 전체 rigid twist 표현에 사용

asset 축의 정확한 방향은 load-time audit 뒤 manifest에 고정한다. 예상 convention은 `+xG: 6번줄→1번줄`, `+yG: bridge/body→nut`, `+zG: fretboard 바깥쪽`이다. actor에 world 절대 위치를 직접 넣지 않는다.

#### 기타 rigid 상태 — 24D, offset `0:24`

| offset | 항목 | 크기 |
|---:|---|---:|
| 0 | pose valid | 1 |
| 1 | twist valid | 1 |
| 2:5 | 기준자세 대비 position error, B frame | 3 |
| 5:11 | 기준자세 대비 orientation error, continuous 6D | 6 |
| 11:14 | linear velocity, B frame | 3 |
| 14:17 | angular velocity, B frame | 3 |
| 17:20 | gravity direction, G frame | 3 |
| 20:24 | position/drop, tilt, linear-speed, angular-speed safety margin | 4 |

orientation은 quaternion의 부호 불연속이나 Euler singularity를 피하기 위해 `RrefᵀR`의 첫 두 column을 사용하는 6D 표현으로 한다. identity의 두 column을 빼서 기준자세가 0이 되도록 center한다.

#### Support site — 65D, offset `24:89`

초기 후보 site는 다음 5개다.

1. 왼 palm/thumb-side ↔ neck support
2. 오른 palm/wrist ↔ guitar body
3. 오른 forearm ↔ upper bout
4. Chest/back support
5. 오른 thigh/lap support

각 site는 13D다. body-state로 얻는 기하 정보와 contact attribution이 필요한 힘 정보를 서로 다른 valid bit로 분리한다.

```text
[kinematics_valid 1,
 anchor position error_G 3,
 relative velocity_G 3,
 contact_valid 1,
 normal load proxy 1,
 tangential load proxy 1,
 slip speed 1,
 conservative friction reserve 1,
 contact_on 1]
```

실제 body·anchor 이름은 collision/contact audit 뒤 manifest에 봉인한다. 현재 simulator의 net contact force에는 상대 collision body 정보가 없으므로 5개 site별 정확한 접촉력을 바로 얻을 수 없다. dedicated proxy나 contact-pair attribution을 만들기 전까지 anchor geometry는 `kinematics_valid=1`로 계속 쓰고, force·slip payload만 0과 `contact_valid=0`으로 두며 reward와 승급 판정에 사용하지 않는다.

#### Aggregate support — 15D, offset `89:104`

```text
aggregate contact valid                    1
total normal load                         1
net tangential force_G                    3
net contact torque_G                      3
center of pressure xy_G                   2
support polygon margin                    1
overforce margin                          1
global slip margin                        1
guitar stable dwell fraction              1
post-impact grace fraction                1
                                           ──
                                           15
```

contact 관련 13D(valid 1 + payload 12)는 `aggregate_contact_valid`로 mask하지만, pose/twist로 계산 가능한 stable dwell과 event clock 기반 post-impact grace는 contact 센서와 독립적으로 항상 유지한다. contact force 자체를 크게 보상하면 기타를 과도하게 쥐는 해가 생길 수 있다. `[Fmin,Fmax]` support band, friction reserve, slip, over-force를 분리해 평가한다.

#### Assist/tether — 24D, offset `104:128`

```text
guitar mode one-hot [FIXED, HAND_ASSISTED, FREE]  3
assist lambda                                      1
transition blend                                   1
assist state valid                                 1

left tether  [valid, extension_G 3, relative velocity_G 3,
              tension/cap fraction, artificial power fraction] 9
right tether [동일]                                           9
                                                               ──
                                                               24
```

`lambda=0, tether_valid=1`은 실제로 보조가 0인 G2 상태이고, `tether_valid=0`은 sensor/anchor 자체가 없음을 뜻한다. 둘을 같은 0으로 표현하지 않는다. 다음 strike 시각과 방향은 Goal block을 통해 shared fusion에 전달하므로 Guitar block에 중복하지 않는다.

## 4. 정규화와 missing signal 규칙

| 데이터 | 권장 정규화 |
|---|---|
| source native observation | 각 source checkpoint의 frozen RMS |
| source pre-tanh mean | source별 offline frozen robust calibration |
| 관절각 | authored lower/upper range로 `[-1,1]` |
| 관절속도 | shoulder/elbow/wrist/finger/body 그룹별 rad/s scale |
| 시간 | signed seconds를 fixed horizon으로 나누고 clip |
| 위치·거리 | m 단위 fixed scale |
| 선속도·각속도 | m/s, rad/s 단위 fixed scale |
| 힘·토크 | N, Nm 단위 fixed scale |
| boolean·one-hot·valid | 정규화하지 않음 |
| action·residual history | 이미 정의된 bounded action/cap 단위 |

초기 물리 scale 후보는 기타 position 0.20m, linear velocity 0.5m/s, angular velocity 5rad/s, force 100N, torque 20Nm, slip 0.5m/s, tether extension 0.10m이다. 이는 확정 상수가 아니라 실제 rollout p95/p99와 안전 한계를 보고 calibration해야 한다.

모든 선택적 sensor는 `value + valid`를 함께 가져야 한다. 0은 실제 측정값 0일 수도 있기 때문이다. padding event, contact-pair force, tether, history reset도 같은 원칙을 쓴다. 필수 state나 source proposal이 nonfinite인 경우에는 조용히 valid를 0으로 만들지 않고 안전 종료와 진단을 수행한다.

G0에서 tether나 guitar twist가 오랫동안 0이어도 G1 첫 nonzero 값이 폭발하지 않도록, 이 block에는 일반 online RMS 대신 fixed physical scale이나 variance floor를 쓴다. running normalization을 사용한다면 rollout 수집과 PPO 재평가 중 snapshot을 고정하고 update 사이에서만 갱신한다.

## 5. Actor 출력과 action 조립

Actor의 fusion feature는 256D이며 두 head가 보정값을 출력한다.

```text
Arm head : 256 → 128 → 18
Body head: 256 → 128 → 15
```

- Arm 18D: 양쪽 Shoulder·Elbow·Wrist 각 3축
- Body 15D: L/R Thorax, Torso, Spine, Chest 각 3축
- Finger 42D: residual 0, source 전용

두 head 마지막 Linear의 weight와 bias를 정확히 0으로 초기화한다. 따라서 학습 시작 시 residual mean은 0이고, base mean은 frozen source 결과와 같아야 한다.

```text
u0 = assemble_by_joint_name(μF, μS, useated_hold)
Δu = bounded_residual(context)
ujoint = u0 + scatter_by_joint_name(Δu)
ajoint ~ tanh(Normal(ujoint, σjoint))
```

숫자 slice가 아니라 관절 이름으로 조립한다. body neutral은 action 0이 아니라 seated pose를 유지하는 normalized action을 `atanh`한 값이다. Fret·Strike의 source 표준편차와 신규 body 표준편차도 같은 이름 순서로 한 75D `log_std`를 만든다.

### 5.1 Residual cap

회귀 비교를 위한 legacy 경로는 다음처럼 **고정 pre-tanh logit cap**을 지원한다.

```text
Δu = tanh(raw) × fixed_logit_cap × stage_scale × authority
```

이 cap은 radian 한계가 아니다. production 경로는 `action_safety.py`에서 관절별 허용 radian을 현재 base action 주변의 방향별 logit cap으로 변환한다.

```text
a0 = tanh(u0)
cap_action = cap_rad / (action_scale × ctrl_half)
cap_u_plus  = atanh(clamp(a0 + cap_action)) - u0
cap_u_minus = u0 - atanh(clamp(a0 - cap_action))
```

raw residual의 부호에 따라 plus/minus cap을 선택하는 계산과 모델 경로는 구현했다. 실제 학습 전에 source와 Full의 `ctrl_mid`, `ctrl_half`, `action_scale`, EMA 계약이 같다는 audit와 관절별 `cap_rad` calibration이 필요하다. cap은 mean 보정만 제한하며 exploration sample, EMA 뒤 속도, torque와 contact force까지 보장하지 않으므로 별도 safety envelope가 필요하다.

### 5.2 세 종류의 mask

production PPO에서는 다음 세 mask를 분리한다.

1. `residual_authority_mask`: coordinator가 residual을 낼 수 있는 33D
2. `stochastic_execution_mask`: 실제 joint distribution에서 sample할 75D
3. `ppo_credit_mask`: coordinator PPO의 log-prob·entropy·KL에 포함할 33D

예를 들어 source finger는 residual authority 0, stochastic execution 1, PPO credit 0이다. `ActionSafetyMasks`와 `MaskedJointTanhNormal`이 이 세 역할을 분리해 구현한다. 다만 공용 PPO trainer가 아직 이 credit mask를 rollout과 재평가에 전달하지 않으므로 Full 전용 wrapper 연결은 남아 있다.

별도의 학습형 Arbiter는 두지 않는다. joint-name ownership, stage/phase authority, 방향별 cap, hard safety gate가 deterministic arbiter 역할을 한다.

## 6. Central critic 입력 128D

Critic은 actor가 보는 다섯 raw block을 **자기 encoder로 다시 인코딩**한다. actor의 384D feature tensor나 parameter를 공유하지 않는다. 여기에 simulator에서만 정확히 알 수 있는 privileged 128D를 추가한다.

```text
critic actor-visible encodings 384
privileged 128 → 128 → 64
concat 448 → 512 → 256 → value 11
```

### 6.1 Privileged field layout

#### Exact hidden physics — 24D, offset `0:24`

```text
log guitar mass ratio       1
center of mass_G            3
symmetric inertia terms     6
linear/angular damping      2
5 support-site friction     5
contact stiffness/damping   2
guitar geometry scale xyz   3
gravity magnitude ratio     1
restitution                 1
                             ──
                             24
```

#### Exact contact — 60D, offset `24:84`

동일한 5개 support site마다 다음 12D를 둔다.

```text
[pair_valid,
 exact contact point_G 3,
 exact force_G 3,
 relative tangential velocity_G 3,
 penetration depth,
 true friction utilization] × 5
```

#### Exact tether — 24D, offset `84:108`

왼쪽·오른쪽 tether마다 12D다.

```text
[valid,
 extension_G 3,
 exact force_G 3,
 exact torque_G 3,
 mechanical work rate,
 saturation fraction] × 2
```

#### Domain/reset — 20D, offset `108:128`

```text
exact external disturbance wrench, force+torque   6
reset guitar pose offset, position+rotation-log   6
initial guitar twist, linear+angular               6
curriculum difficulty                              1
assist randomization severity                      1
                                                   ──
                                                   20
```

true mass·inertia·friction, exact pair attribution, exact tether wrench와 randomization parameter는 actor에 전달하지 않는다. 반대로 미래 reward나 다음에 발생할 랜덤 충격처럼 현재 시점에서 simulator도 알면 안 되는 결과를 critic에 넣어서는 안 된다.

11개 value head는 다음 reward channel과 1:1로 대응한다.

```text
fret_high_e, fret_B, fret_G,
fret_D, fret_A, fret_low_E       6
strike                            1
joint_event_sync                  1
guitar_pose_twist                 1
support_slip_force                1
assist_recovery_safety            1
                                  ──
                                  11
```

## 7. 한 simulation step의 정확한 순서

1. 한 개의 authoritative `score_frame`과 한 physics snapshot을 읽는다.
2. 같은 common event로 Fret 425D와 Strike 327D projected view를 만든다.
3. frozen source actor를 `no_grad`로 실행해 `μF/logσF`, `μS/logσS`를 얻는다.
4. Goal, Readiness, Joint, Guitar context를 위 manifest 순서로 pack한다.
5. Action Residual actor가 18D arm, 15D body residual을 출력한다.
6. deterministic ownership·authority·cap을 적용해 75D pre-tanh mean을 조립한다.
7. 하나의 FP32 joint TanhNormal에서 한 번 sample하고 **pre-tanh latent**, `policy_action=tanh(latent)`, old log-prob을 저장한다.
8. inactive body slot만 seated-hold action으로 덮고, 필요한 deployment transform을 이름 기준으로 한 번 적용한다.
9. 최종 75D에 공통 EMA를 정확히 한 번 적용하고 PD target을 만든다.
10. physics를 한 step 진행한다.
11. 같은 post-physics snapshot에서 readiness, strike crossing, guitar 안정성, reward를 계산한다.
12. buffer에는 source proposal을 재현할 입력, raw GoalScore, context, FP32 latent, policy action, log-prob, value 11D, 세 mask, physical cap, normalization/schema snapshot ID와 history를 저장한다.

PPO update는 저장된 latent를 `log_prob_from_latent()`로 재평가한다. 포화된 `policy_action`에서 `atanh`로 latent를 복원하면 같은 정책에서도 importance ratio가 1이 되지 않을 수 있으므로 학습 경로에서는 금지한다.

각 source task를 독립적으로 한 step씩 실행한 뒤 결과를 합치면 clock, contact, reset이 서로 다른 환경이 되므로 금지한다.

## 8. 현재 구현된 것과 추가 구현할 것

| 항목 | 현재 상태 |
|---|---|
| 60/128/64/600/128 tensor 폭과 MLP 골격 | 구현됨 |
| 75D name-based compose, source SHA 검사, zero-init heads | 구현됨 |
| 단일 75D TanhNormal prototype | 구현됨 |
| field name·offset·단위·frame·scale·valid manifest와 typed packer | 구현됨 |
| Goal EventTokenEncoder와 categorical embedding | 구현됨 |
| source mean encoder용 calibration·checkpoint 계약 | 구현됨, 실제 통계 수집 전 `CALIBRATION_REQUIRED` |
| source projected legacy observation 순수 API | 구현됨, 실제 Fret 425D field/index manifest는 미연결 |
| 하나의 Full event compiler/clock/readiness API | 미구현 |
| 75D production action builder와 common EMA wrapper | 미구현 |
| direction-dependent physical residual cap | 구현됨, 실제 관절별 `cap_rad` calibration은 미완료 |
| authority/execution/PPO-credit 3-mask와 joint distribution 연결 | 구현됨 |
| FP32 pre-tanh latent log-prob 재평가와 포화 action fail-close | 구현됨 |
| same-shape 관절/value-head/static context semantic checkpoint 검증 | 구현됨 |
| concrete joint-limit context-pipeline hash 생성 | 구현됨, Full envelope binding은 I1 미구현 |
| free guitar, gravity, hand tether와 G0/G1/G2 전환 | 미구현 |
| support-site contact attribution·slip proxy | 미구현 |
| Full PPO wrapper와 rollout storage | 미구현 |

Strike는 물리적 string 충돌이 아니라 kinematic crossing detector로 발음을 판정한다.
Crossing은 자유 기타에 force·torque·impulse를 전달하지 않는다. StabilityAdapter는 중력,
strap, 실제 support contact 변화와 별도 외부 교란만 관측·학습 대상으로 삼는다.

## 9. Shared trunk에 관한 결정

현재 prototype은 `384→512→256` trunk를 arm/body head가 공유한다. 구조는 단순하지만 G1에서 body head만 학습해도 shared trunk가 변하면 G0에서 익힌 arm timing 출력이 함께 달라진다.

본 학습 전 다음 중 하나를 선택해야 한다.

- **간단한 baseline**: shared trunk 유지, G1에서 trunk와 arm head를 모두 freeze하고 body head만 학습. 이후 작은 learning rate와 G0 rehearsal로 공동 미세조정
- **단계별 격리를 우선한 구조**: 공통 block encoder 뒤 Sync tower와 Support tower를 분리하고, G1에서 Sync tower에 stop-gradient 적용

첫 G0 baseline은 현재 shared 구조로 측정할 수 있다. 다만 fixed→tether→free의 단계별 동결을 강하게 보장하려면 두 번째 구조가 더 안전하며, 변경 시 architecture ID와 checkpoint를 분리해야 한다.

## 10. Checkpoint에 봉인할 manifest

각 observation field마다 다음을 저장한다.

```text
name, offset, size, ordered_components, dtype, unit, coordinate_frame,
normalization_center, normalization_scale, clip,
valid_field, invalid_fill_rule, stage_availability
```

추가로 다음 hash를 함께 저장한다.

- Full observation schema와 75D action name/order
- 실제 75개 lower/upper limit·velocity scale을 포함한 JointHistory/context-pipeline schema SHA
- Fret/Strike checkpoint SHA-256
- Fret/Strike source observation manifest와 frozen RMS
- source deployment transform, `ctrl_mid/half`, action scale, EMA alpha
- 곡 ID, common goal timeline, string order, finger map
- guitar asset mass/inertia, support anchor, collision profile, tether law
- residual cap version과 세 action mask 규칙

학습 시작 전 dimension 합계, name/order, actor privileged-invariance, zero-residual source equivalence를 자동 test로 검증한다. 특히 G0의 deterministic source action, common EMA 이후 action, PD target이 기존 단독 실행과 일치하지 않으면 PPO 학습을 시작하지 않는다.
