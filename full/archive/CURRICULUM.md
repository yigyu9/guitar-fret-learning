# 병합·기타 고정 해제 학습 커리큘럼

> **상태: SUPERSEDED INITIAL CURRICULUM.** 아래 S2 learned Sync, 63-source action,
> 영구 source freeze, held-out-song 조건과 11-head critic은 현재 확정 구조가 아니다.
> 현재 G0/G1/G2, rule Synchronizer, StabilityAdapter, 제한적 fine-tuning 계약은
> [`master_plan/09_curriculum_and_evaluation.md`](../../master_plan/09_curriculum_and_evaluation.md)를 따른다.

> 상태: **설계 검토 중 — 수치는 초기 제안이며 실측 후 보정**  
> 원칙: 모델 shape은 유지하고 환경 보조와 action 권한만 점진적으로 바꾼다.

## 1. 전체 단계

```text
S0 Source equivalence
  ↓
S1 Fixed guitar frozen union
  ↓
S2 Fixed guitar synchronization
  ↓ stage promotion: fixed asset → free asset
S3 Physical strap + strong soft hand assistance, SupportBranch-only
  ↓
S4 Weak/random assistance + zero-assist probes
  ↓
S5 Physical strap, artificial assist=0, short phrase → full song
  ↓
S6 Robustness and held-out physics
```

G0 fixed asset과 G1/G2 free asset은 별도 환경이다. G0→G1은 episode 안의 mode switch가 아니라 새 run으로의 명시적 promotion이다. G1 이후에는 같은 free asset을 유지하면서 assist level `λ`만 연속적으로 0으로 낮춘다.

---

## 2. 단계별 학습 대상

| 단계 | 기타 | 학습 모듈 | Action 권한 | 핵심 목표 |
|---|---|---|---|---|
| S0 | Fixed | 없음 | source 그대로 | zero-injection/source transform 등가 |
| S1 | Fixed | 없음 | 63 source | 무학습 양손 union과 rule gate baseline |
| S2 | Fixed | Sync만 | 제한된 proximal/wrist | 왼손-ready→strike timing |
| S3 | Free + virtual strap constraint + 강한 hand assist | Support만 | `R_Thorax`, proximal 순차 | 중력·접촉 변화·외란 아래 pose/support |
| S4 | Free + virtual strap constraint + 약한/무작위 assist | Support, 후기 low-LR joint | 이전 권한 유지 | 인공 assist 의존 제거 |
| S5 | Free + virtual strap constraint, assist=0 | 후기 low-LR joint | 필요할 때만 확대 | strap·실제 접촉으로 전곡 유지 |
| S6 | Free + virtual strap constraint, assist=0 | 최소 fine-tune | 검증된 최소 mask | 곡·tempo·물성 robustness |

Source Fret/Strike actor, source `obs_rms`, `log_std`, action transform은 모든 단계에서 영구 freeze한다.

### S0 — Source equivalence

- 각 source의 native observation 재구성
- deterministic mean, sampled raw action, source transform, EMA/PD target 비교
- 반대편 손 `live` 대 `counterfactual_mean` view 비교
- reserved action이 숫자 0이 아니라 seated-pose hold target으로 override되는지와 PPO mask 검증

이 단계가 실패하면 Full 학습을 시작하지 않는다.

### S1 — Fixed frozen union

- Fret 30 + Strike 30을 관절 이름으로 조립
- constant timing offset, readiness dwell, bounded phase hold 비교
- coordinator residual과 SupportBranch는 exact zero
- 실패 event는 늦게 실행하지 않고 deadline에서 miss/skip

학습 없는 규칙만으로 목표를 달성하면 SyncBranch를 만들지 않는다.

### S2 — Fixed synchronization

- action-logit residual과 latent SyncAdapter를 같은 budget으로 비교
- SupportBranch는 frozen zero
- protected finger residual은 금지
- 같은 성능이면 단순 action residual을 선택

S2의 timing checkpoint는 이후 안정화 단계의 고정 anchor다.

### S3 — Strong hand assistance

- 자유 root, 중력 on, 검증된 guitar mass/inertia 사용
- 검증된 `strapped-v1` 물리 스트랩 상시 활성화
- palm/thumb-side와 wrist/forearm-side의 soft support tether 활성화
- SyncBranch freeze, SupportBranch만 학습
- 첫 권한은 `R_Thorax`, 이후 bilateral shoulder/elbow
- strike 직전 brace와 strike 후 settling 학습
- exact weld·teleport·fingertip/pick attachment 금지

처음부터 보조력이 너무 강하면 정책이 외력에만 의존한다. Stable reset을 확보할 최소 stiffness부터 시작하고 force/work 의존도를 항상 로그한다.

### S4 — Weak/random assistance

단일한 `λ`를 선형으로 내리는 대신 episode별 분포를 사용한다.

```text
초기: high-assist band + 바로 아래 단계 probe
중기: medium/low band + zero-assist probe 증가
후기: low/zero 중심 + 일부 이전 assist rehearsal
```

- actor가 `λ`와 mode를 관측한다.
- `λ`는 한 episode 안에서 고정한다.
- 현재 band 평균 return이 아니라 **zero-assist probe**와 tether assistance fraction으로 진급한다.
- Zero-assist가 일정 수준에 도달한 뒤에만 Sync와 Support를 작은 learning rate로 함께 미세조정한다.
- 두 branch가 같은 관절에서 충돌하면 권한을 늘리기 전에 cap saturation과 conflict를 조사한다.

### S5 — Fully free

- 인공 tether force/torque/work를 정확히 0으로 강제
- `strapped-v1` 물리 스트랩은 유지하며 tension/work/비관통을 계속 기록
- 안정된 접촉 reset에서 짧은 phrase부터 시작
- phrase 길이, chord 전환, strike 세기, 곡 길이를 순차 확대
- 이전 단계의 G0 timing과 G1 support gate도 함께 평가
- `R_Thorax`와 proximal 권한으로 실패한 증거가 있을 때만 `L_Thorax`, 중앙 torso 9개 순으로 해제
- Finger residual은 최후까지 source 독점

### S6 — Robustness

- held-out song과 tempo
- guitar mass/inertia/CoM
- contact friction과 reset support pose
- 외부 disturbance, actuator delay/noise
- virtual strap stiffness/damping/anchor와 surface route

Randomization은 nominal zero-assist 성능이 안정된 뒤 도입한다. 너무 일찍 넓히면 모델 구조 실패와 물성 다양성 실패를 구분할 수 없다.

---

## 3. 단계 전환 gate

수치는 초기 acceptance proposal이며, G0 실측 분포를 얻은 뒤 확정한다.

### 모든 단계 공통

- 5 seeds, 3개 연속 evaluation window 통과
- Fret/Strike 핵심 지표가 G0 대비 95% 이상 유지
- 절대 하락 2%p 이하
- premature strike/crossing 악화 1%p 이하
- residual cap saturation 5% 미만
- action rate/jerk와 penetration/over-force hard gate 통과

### S3→S4

- 현재 assist에서 nominal 500 rollout drop 0
- 현재보다 한 단계 낮은 assist probe에서 음악·안정화 gate 통과
- Tether force/torque cap saturation이 지속적으로 높지 않음
- Strike 후 settling p95가 잠정 0.5초 이하

### S4→S5

- zero-assist probe 성공률 잠정 90% 이상
- tether assistance fraction p95 잠정 10~15% 미만
- guitar pose error 잠정 RMS 1.5 cm/4° 이하
- guitar pose error 잠정 p95 3 cm/8° 이하
- zero-assist에서 source 음악 지표 보존 gate 통과

### S5 완료

- nominal 500 rollout drop 0
- randomized rollout drop rate 1% 미만
- 완전한 곡 길이 동안 artificial assist zero assertion 통과
- held-out song/tempo/physics gate 통과
- G0/S2/S3 회귀 평가도 계속 통과

절대 수치보다 먼저 G0 source 분포와 실제 기타 크기·허용 motion envelope를 측정해야 한다. 위 threshold를 측정 없이 checkpoint contract에 고정하지 않는다.

---

## 4. 망각과 shortcut 방지

### 기능 보존

- Source 두 정책과 source normalization을 영구 freeze
- G1 초기에 SyncBranch freeze, SupportBranch-only
- Protected finger residual exact zero
- Source mean drift/KL, head-off 성능, source transform 등가성 기록
- 이전 단계 gate를 모두 통과한 checkpoint만 다음 단계로 promotion

### Rehearsal

G0 fixed와 G1 free asset은 같은 vector environment에서 섞지 않는다. Batch/run 수준에서 별도 환경을 교대하거나, 최소한 매 promotion 시 이전 단계 evaluation suite를 실행한다.

초기 rehearsal 비율 후보:

```text
current stage     50~60%
previous stage    20~30%
G0/S2 anchor      약 20%
```

이는 고정값이 아니다. Source는 frozen이므로 EWC보다 branch freeze, action mask, previous-stage rehearsal이 우선이다.

### Tether shortcut 방지

- `λ`를 actor에 숨기지 않는다.
- Tether wrench/work와 physical support load를 분리해 기록한다.
- Assist usage penalty만 믿지 않고 zero-assist 평가를 필수로 둔다.
- Rest-pose wrench가 손 지지를 대신하는지 head-off로 검사한다.
- Strike impulse를 tether가 전부 흡수하지 않는지 event별 외력 로그를 본다.

---

## 5. Reward·critic 운영

Central critic은 mode와 `λ`를 보고 최소 11개 head를 유지한다.

```text
fret 6 + strike 1 + joint event 1
+ guitar pose/twist 1
+ support/slip/over-force 1
+ assist/action cost 1
```

이 observation slot과 11개 value head는 S0부터 같은 shape으로 존재한다. S0/S1에서는 물리 head의 reward weight를 0 또는 diagnostic으로 두고 S3에서 활성화한다. Stage 진입 때 observation/value dimension을 추가하지 않는다.

- 안정화 reward가 연주 실패를 상쇄하지 않게 source 지표를 promotion gate로 둔다.
- Contact force 최대화 대신 support band와 friction margin을 보상한다.
- Strike 직후 짧은 허용 envelope와 settling reward를 분리한다.
- Privileged mass/friction/정확한 외력은 critic에만 제공할 수 있다.
- Actor observation은 배포 가능한 상태와 알려진 assist mode로 제한한다.
- G0에서 0이던 pose/velocity/tether block은 고정 물리 scale 또는 variance floor로 정규화해 S3 첫 nonzero 관측의 폭주를 막는다.

G0→G1의 return distribution은 크게 바뀐다. 일반 resume로 가장하지 않고 새 stage run을 만들며 parent checkpoint를 기록한다. Actor/branch weights는 promotion하되 critic·optimizer state를 유지할지 재초기화할지는 별도 ablation으로 결정한다.

---

## 6. 매 단계 저장할 증거

- stage/mode/assist 분포와 parent checkpoint
- source 두 checkpoint hash와 observation view mode
- action active/reserved/authority mask
- guitar asset/mass/inertia/CoM fingerprint
- tether anchor/stiffness/damping/slack/cap 정의
- Fret/Strike/joint event metrics
- guitar pose/twist/drop/slip/settling metrics
- tether force/torque/work/assistance fraction
- contact safety와 support distribution
- branch별 residual norm/conflict/cap saturation
- zero-assist probe 결과와 모든 이전 단계 regression 결과

물리·모델 상세는 [`GUITAR_STABILIZATION.md`](02_architecture/GUITAR_STABILIZATION.md)를 참조한다.
