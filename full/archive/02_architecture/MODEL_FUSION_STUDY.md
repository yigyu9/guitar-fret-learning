# Fret·Strike 병합 모델 구조 비교 연구

> **상태: HISTORICAL STUDY.** 후보 비교와 기각 근거를 보존한다. 현재 선택은 frozen Fret·Strike + rule Synchronizer + StabilityAdapter + 105D ActionArbiter이며 [`master_plan`](../../master_plan/README.md)이 우선한다.

> 상태: **설계 검토 중 — 아직 구조를 고정하지 않음**  
> 조사일: 2026-08-25  
> 기타 고정 해제 요구 반영: 2026-08-26  
> 목적: 독립적으로 학습한 Fret·Strike 정책을 보존하면서 양손 타이밍과 `고정→손 보조→완전 자유` 기타 안정화를 학습할 수 있는 구조를 비교한다.

이 문서의 결론은 “어떤 MLP 크기를 쓸지”보다 앞단의 **불변 인터페이스**를 정하는 것이 먼저라는 것이다. Action·observation·checkpoint 계약을 안정적으로 둘 수 있으면, 내부 coordinator를 MLP에서 TCN이나 GRU로 바꾸는 일은 두 단일손 정책을 다시 학습하지 않고도 가능하다.

---

## 1. 결론 요약

### 1.1 우리의 문제는 두 action을 평균내는 문제가 아니다

현재 두 정책의 제어 관절은 하나도 겹치지 않는다.

| 정책 | 행동 | 소유 관절 |
|---|---:|---|
| Fret | 30 | 왼팔 9 + 왼손 21 |
| Strike | 30 | 오른팔 9 + 오른손 21 |
| 겹치는 이름 | 0 | 없음 |

따라서 기본 결합은 다음 곱연산이다.

```text
π0(aF, aS | oF, oS) = πF(aF | oF) · πS(aS | oS)
```

구현으로는 출력을 섞지 않고 **관절 이름으로 배치**하면 된다. 학습이 필요한 부분은 다음 세 가지다.

1. 스트라이크 순간에 왼손이 준비되도록 하는 이벤트 협업
2. 한쪽 움직임이 같은 몸·기타를 통해 반대쪽을 교란하는 물리 결합
3. 고정이 풀린 기타의 자세·속도·지지 안정화

### 1.2 현재의 1순위 가설

현재 가장 유력한 구조는 다음 하이브리드다.

```text
Frozen Fret policy ----+----> separate SyncBranch ----+
                       |                               |
Frozen Strike policy --+----> separate SyncBranch ----+--> Named Arbiter
                                                       |        |
event/readiness -------------------------------> gates |        |
live guitar/support + assist λ ---> SupportBranch -----+        v
                                                   단일 joint TanhNormal
                                                             |
                                       source transform + common EMA/PD
```

- **SyncBranch**: 기존 기술 내부에서 양손 타이밍을 미세 조정한다.
- **SupportBranch**: 기타 pose/twist/contact를 폐루프 제어하고, 기존 정책이 출력하지 않던 `R_Thorax`와 몸통 자유도에 새 행동을 만든다.
- **분리된 trunk**: G1에서 Sync를 동결하고 Support만 학습할 수 있게 해 timing의 망각을 막는다.
- **Named Arbiter**: 두 branch가 같은 관절을 보정할 때 phase mask와 하나의 관절별 총 residual cap을 적용한다.
- **Event state machine**: 신경망에게 안전 조건 정의까지 넘기지 않고, 조기 타현을 성공으로 인정하지 않는 규칙을 고정한다.
- **Joint TanhNormal**: Fret, Strike, residual을 각각 sample한 뒤 억지로 합치지 않고, 최종 공동 분포에서 한 번만 sample한다.

다만 이 구조를 아직 확정하지 않는다. **pre-tanh action residual 단일 모델**이 같은 성능을 낸다면 그쪽이 더 단순하고 외부 모델 구조에 덜 종속적이다. 최종 선택은 고정 기타에서 동일한 예산·seed로 두 injection 지점을 비교한 후 하고, 선택된 구조의 SupportBranch를 손 보조 기타에서 별도로 학습한다.

### 1.3 현재 checkpoint를 반영한 75차원 ABI 후보

현재 source는 Fret 30개와 Strike 30개로 총 60개다. 기타 고정 해제 후 양쪽 Thorax 6개와 `Torso/Spine/Chest` 9개가 필요해지면 action head shape을 바꾸고 재학습해야 한다.

따라서 다음을 장기 action ABI 후보로 둔다.

```text
75 = Fret 30
   + Strike 30
   + L_Thorax/R_Thorax 6
   + reserved Torso/Spine/Chest 9
```

- G0 active action은 source 60개이며, G1에서 `R_Thorax`, 이후 `L_Thorax`를 단계적으로 연다.
- 중앙 몸통 9개는 seated hold에 해당하는 관절별 neutral action으로 강제하고 PPO log-prob에서 mask한다.
- 필요성이 입증될 때만 SupportBranch에 해제한다.
- `Neck/Head` 6개와 하체 24개는 기타 지지 권한이 아니므로 현재 계약에서는 제외한다.

이 75차원 선택 역시 아직 확정이 아니다. 그러나 모델 크기보다 **action 이름·순서·neutral 값·active mask**가 checkpoint 호환성에 더 큰 영향을 주므로, 이 선택은 모델 구조보다 먼저 결정해야 한다.

여기서 neutral은 숫자 `0`이 아니다. 현 action 0은 각 관절 hard range의 midpoint이므로 reserved 몸통을 0으로 덮으면 seated pose가 움직인다. `actions_for_pd_targets(init_pose)`로 얻은 per-DOF hold action 또는 PD target 직접 bypass를 manifest에 저장해야 한다. Pre-tanh neutral logit이 필요하면 이 hold action의 clipped `atanh`를 사용한다.

---

## 2. 현재 저장소의 실제 제약

### 2.1 두 actor는 구조는 같지만 observation 계약이 다르다

| 항목 | Fret | Strike |
|---|---:|---:|
| Observation | 425 | 327 |
| Action | 30 | 30 |
| Value head | 6 | 1 |
| Actor | 425→512→256→30 | 327→512→256→30 |
| 분포 | tanh-squashed diagonal Gaussian | 동일 |
| 순환 상태 | 없음 | 없음 |

공통 구현은 [`tab2body/learning/models.py`](../../tab2body/learning/models.py)의 `ActorCritic`이다. 두 정책은 각자의 `obs_rms`, actor, critic, `log_std`를 갖는다.

Fret 425차원은 다음으로 나뉘다.

```text
base proprio/body       180
fret goal               128
previous action          30
thumb geometry           12
long future context      75
total                   425
```

Strike 327차원은 다음으로 나뉘다.

```text
base proprio/body       171
strike/event context    126
previous action          30
total                   327
```

따라서 full policy가 하나의 관측을 잘라 두 actor에 넣는 것만으로는 부족하다. 두 source의 정확한 native observation을 각각 재구성하는 adapter가 필요하다.

### 2.2 가장 큰 즉시 위험: 반대쪽 손이 움직이면 source actor가 OOD에 들어간다

공통 base observation은 자신이 제어하는 관절만이 아니라 하체를 제외한 **81개 전체 non-locked DOF의 q, qdot**을 모두 포함한다. 단일손 학습 중 반대편 팔·손은 PD로 초기 자세 근처에 유지되었다.

실제 source checkpoint의 normalization 통계를 조사하면:

- Fret이 보는 오른쪽 q/qdot 66채널 중 44개의 분산이 `1e-6` 미만이다.
- Strike가 보는 왼쪽 q/qdot 66채널 중 44개도 같다.
- 그런데 첫 actor layer의 해당 가중치는 0이 아니다.
- 결합 후 반대편 손이 움직이면 normalized input이 즉시 RMS clamp `±5`에 도달할 수 있다.

합성한 ±5σ 입력 민감도 검사에서 Fret의 평균 action 변화는 0.331, Strike는 0.154였다. 이는 full rollout 성능값은 아니지만, live 전신 proprioception을 source actor에 그대로 넣는 것이 위험하다는 강한 증거다.

따라서 초기 권고는 **counterfactual native view**다.

```text
Fret actor view:
  왼쪽 자신 상태       = live
  왼손-기타 기하     = live
  오른쪽 proprioception = source obs_rms.mean
  source previous action  = full action의 Fret slice

Strike actor view:
  오른쪽 자신 상태     = live
  pick-기타 기하       = live
  왼쪽 proprioception   = source obs_rms.mean
  source previous action    = full action의 Strike slice

Coordinator view:
  양쪽 전체 상태       = live
```

raw 초기 자세가 아니라 `obs_rms.mean`을 쓰는 이유는 normalization 후 정확히 0이 되게 하기 위함이다. `live` 대 `counterfactual_mean`은 반드시 독립 ablation을 하고 checkpoint 계약에 봉인해야 한다.

### 2.3 Raw actor action을 바로 병합하면 Fret 정책을 재현한 것이 아니다

Fret은 actor action을 받은 후 물리 명령 전에 다음을 적용한다.

- curriculum action mask
- fine-reach action scale
- adjacent-finger synergy
- 비활성 action의 이전 명령 유지
- 공통 EMA와 normalized-action-to-PD-target map

Full-song에서도 finger synergy가 적용될 수 있다. 따라서 source actor 출력만 재사용하고 이 transform을 누락하면 “frozen policy 보존”이 아니다.

권장 순서는 다음이다.

```text
1. source native observation 재구성
2. source actor에서 latent mean/feature 추출
3. coordinator correction을 반영한 joint raw distribution 구성
4. joint raw action을 한 번 sample
5. Fret/Strike source action transform을 각 slice에 적용
6. 관절 이름으로 full action 배치
7. reserved action neutral 강제
8. common EMA + PD target
```

이 transform은 `FrozenPolicyAdapter`의 출력 계약에 포함하고 구현 fingerprint를 저장해야 한다.

### 2.4 기타 고정 해제는 runtime asset switch와 연속 assist curriculum의 조합이다

현재 기타 asset은 로드 시 `fix_base_link=True`, `disable_gravity=True`다. 자유 기타는 별도 asset mode로 로드해야 하므로, G0 고정 기타와 G1 자유 기타는 서로 다른 환경 계약이다. 한 episode 중 `fix_base_link`를 끄는 구조로 설계하면 안 된다.

```text
G0 fixed:          fixed root, gravity off, SupportBranch zero
G1 hand-assisted:  free root, gravity on, bounded soft hand tether λ>0
G2 fully free:     same free asset, artificial tether λ=0
```

G1에서 손에 묶는다는 의미는 fingertip/pick hard weld가 아니다. Palm/thumb-side와 wrist/forearm-side support anchor에 dead-zone, 방향별 stiffness, damping, force cap을 둔 compliant tether다. G1→G2는 같은 free asset에서 `λ`만 0으로 낮춰 dynamics cliff를 피한다. 세부 계약은 [`GUITAR_STABILIZATION.md`](GUITAR_STABILIZATION.md)와 [`CURRICULUM.md`](../04_training/CURRICULUM.md)에 정리했다.

---

## 3. 비교한 모델 계열

### 3.1 평가 기준

모델을 다음 일곱 기준으로 비교한다.

1. **Source retention**: residual 0에서 단일손 기술을 보존하는가.
2. **Timing authority**: 왼손-ready→strike 순서를 바꿀 통로가 있는가.
3. **New-DOF authority**: `R_Thorax`와 중앙 몸통을 새로 제어할 수 있는가.
4. **Free-guitar authority**: 기타 pose/velocity/support를 피드백 제어할 수 있는가.
5. **Checkpoint stability**: source model 내부와 불필요하게 강결합하지 않는가.
6. **PPO correctness**: 실제 sample한 action의 log-prob을 정확히 계산할 수 있는가.
7. **Diagnosis**: 왜 실패했는지 head-off, mask, residual norm으로 나눌 수 있는가.

### 3.2 후보 요약표

`VH/H/M/L`은 각각 매우 높음/높음/중간/낮음을 뜻한다. 이는 선행 연구와 현재 저장소 계약을 합친 엔지니어링 판단이지 보편적 성능 순위가 아니다.

| 후보 | 보존 | 타이밍 | 새 DOF/자유 기타 | 계약 안정성 | 진단성 | 현 판단 |
|---|---:|---:|---:|---:|---:|---|
| Frozen union | VH | L | L | VH | VH | 필수 baseline |
| 규칙 gate/time-warp | VH | H | L | VH | VH | 타이밍만으로 충분한지 먼저 검사 |
| Pre-tanh action residual | H | H | H | H | H | 가장 강한 단순 대안 |
| SDH형 latent adapter | VH | VH | L~M | L~M | M | 고정 기타 sync에 강함 |
| Latent sync + action stabilize | VH | VH | VH | M | H | 현재 1순위 가설 |
| Progressive/new joint column | H | H | VH | M | M | 큰 분포 이동 시 대안 |
| CTDE/MAPPO 두 actor | M | H | H | M | L | 분산 실행 이점이 없음 |
| GRU/TCN/Transformer | - | H | H | L~M | L~M | 주 merger가 아닌 temporal modifier |
| MoE/PoE/MCP | L~M | L~M | L | L | M | 현 action 분할과 맞지 않음 |
| Monolithic joint fine-tune | L | H | VH | L | L | 최후 수단 |
| Distillation | teacher 의존 | teacher 의존 | teacher 의존 | M | M | 성공한 joint teacher 후 배포용 |
| QP/MPC safety layer | VH | L | M | H | H | 최소 개입 보조층 |

---

## 4. 후보별 상세 분석

### 4.1 Frozen union: 관절 이름으로 두 정책을 그대로 실행

```text
a0[name] = aF[name]  if name in Fret
a0[name] = aS[name]  if name in Strike
a0[name] = seated-hold neutral   otherwise
```

장점:

- 학습이 없고 가장 쉽게 검증할 수 있다.
- 성공하면 synchronizer를 만들 이유가 없다.
- 이후 모델이 실제로 개선했는지 판별하는 절대 baseline이다.

한계:

- source policy가 반대편 움직임을 OOD로 받을 수 있다.
- 왜 왼손이 늦었는지 오른손은 모른다.
- 새로운 기타 동역학과 `R_Thorax`를 학습하지 못한다.

판단: **최종 구조는 아니지만 반드시 먼저 만들어야 한다.**

### 4.2 규칙 기반 event gate / time-warp supervisor

오른손 low-level action을 바꾸지 않고, 오른손 정책이 보는 motor phase를 `READY`에 유지하다가 왼손 readiness가 충족되면 `APPROACH/CROSSING`을 연다.

이 구조의 gate는 세 개로 나눠야 한다.

1. **성공 판정 gate**: crossing 순간 target fret·sustain이 아니면 joint 실패다.
2. **보상 gate**: readiness 전에 strike 성공 보상을 주지 않되 approach/recovery shaping은 남긴다.
3. **물리 phase gate**: 조기 crossing을 방지하되, gate 대기 시간을 왼손 성공으로 위장하지 않는다.

음악 시계 전체를 멈추면 뒤 이벤트가 모두 밀린다. 권장 계약은 공통 song clock은 계속 가고, deadline을 넘긴 이벤트는 **늦게 성공**이 아니라 **miss/skip**으로 처리하는 것이다. SDH 코드의 timer escape처럼 deadlock 방지 규칙을 두더라도 escape 후 strike를 joint success로 계산하면 안 된다.

판단: **고정 기타 타이밍 문제의 가장 유력한 무학습 해법**이며, residual 학습 전에 반드시 평가한다.

### 4.3 Pre-tanh action-logit residual

관절 이름으로 배치한 base latent mean 위에 작은 보정을 더한다.

```text
μ0 = assemble_by_name(μF, μS, μneutral)
μ  = μ0 + M ⊙ c ⊙ tanh(Δμθ(x))
a  ~ tanh Normal(μ, σjoint)
```

- `M`: residual이 허용된 관절 mask
- `c`: 관절별 logit residual cap
- 마지막 layer: weight·bias 모두 0 초기화

장점:

- source actor 내부 layer에 종속되지 않는다.
- `R_Thorax`와 reserved torso에 새 명령을 만들 수 있다.
- head-off, per-joint cap, mask로 분석하기 쉽다.
- tanh 후 action을 더하고 clamp하는 방식보다 분포 계산이 깔끔하다.
- [Residual RL](https://arxiv.org/abs/1812.03201)은 기존 controller와 RL residual을 중첩해 접촉 조립 작업을 학습하는 근거를 제공한다.
- [Policy Decorator](https://arxiv.org/abs/2412.13630)는 동결한 다양한 base policy에 bounded residual을 덧붙이고 점진적 exploration을 적용하는 model-agnostic 선례다.

한계:

- residual이 커지면 source policy를 사실상 덮어쓴다.
- 기존 관절 협응 구조를 벗어난 노이즈를 만들 수 있다.
- base mean이 tanh 포화 구간에 있으면 같은 logit residual의 물리 action 권한이 작아진다.
- 두 의미별 head가 같은 proximal joint를 반대 방향으로 고치면 상쇄·chattering이 나타날 수 있다.

판단: **구조·성능 균형이 가장 좋은 단일 모델 대안**이다. Hybrid 대비 baseline으로 반드시 비교한다.

### 4.4 SDH/AdaptNet형 latent synchronizer

[SDH](https://arxiv.org/abs/2409.16629)는 두 단일손 정책을 동결한 뒤 두 표현을 함께 읽는 제로 초기화 offset을 잠재공간에 주입한다. 구체적인 논문·코드 비교는 [`FRET_STRIKE_MERGE_REFERENCE_RESEARCH.md`](../../docs/2026-08-26/FRET_STRIKE_MERGE_REFERENCE_RESEARCH.md)에 정리했다.

우리 actor에 대응하는 두 주입 지점은 다음이다.

```text
early hidden:     512D hidden에 Δh 주입 → 256D layer → output
penultimate:      256D hidden에 Δh 주입 → output
```

SDH의 구조에 더 가까운 것은 early hidden 주입이다. 256D penultimate 뒤에는 선형 output layer만 남으므로, output weight가 full row rank면 사실상 대부분의 action-logit residual을 만들 수 있어 “manifold 내부”라는 해석이 약해진다.

장점:

- 0 injection에서 source 표현을 정확히 보존할 수 있다.
- 기존 tail을 통과하므로 기존 관절 협응을 유지할 가능성이 높다.
- [AdaptNet](https://arxiv.org/abs/2310.00239)은 encoder/policy를 동결하고 0-초기화 latent/internal adaptation을 학습해 행동 적응을 가속한다.
- 2026년의 최근 preprint [ZPRL](https://arxiv.org/abs/2605.19919)도 action residual보다 bottleneck latent perturbation이 더 구조화된 탐색을 제공할 수 있다는 결과를 보고한다. 다만 그 방법은 base 사전학습 시 bottleneck을 설치하므로 현재 checkpoint에 바로 적용할 수 없다.

한계:

- source layer 위치·크기가 full checkpoint ABI의 일부가 된다.
- source head에 없는 `R_Thorax`를 만들 수 없다.
- 고정 기타에서만 학습한 tail이 자유 기타 지지 행동을 표현한다는 보장이 없다.
- actor를 나중에 바꾸면 adapter도 다시 학습해야 한다.

판단: **고정 기타 양손 타이밍에는 가장 직접적인 선행 연구 근거**이지만, 새 DOF 안정화 head를 대체하지는 못한다.

### 4.5 Latent sync + action stabilize hybrid

두 문제의 성격을 나눈다.

```text
SyncBranch:
  대상 = 기존 Fret/Strike hidden state
  목적 = readiness, onset, sustain 미세 조정
  출력 = ΔhF, ΔhS

SupportBranch:
  대상 = named full action logits
  목적 = guitar pose/twist/contact/assist 의존 제어
  출력 = bounded Δμsupport[75]
```

장점:

- sync는 기존 기술 tail을 재사용한다.
- stabilization은 source에 없는 DOF를 직접 만든다.
- 두 branch를 서로 끌 수 있어 실패 원인을 나눌 수 있다.
- fixed sync → hand-assisted Support-only → low-LR joint 순서의 staged training이 가능하다.

한계:

- 모델 구조가 action residual 하나보다 복잡하다.
- latent sync와 action stabilizer가 같은 shoulder/elbow를 반대로 조정할 수 있다.
- 두 보상 그래디언트가 shared trunk에서 충돌할 수 있다.

이를 막기 위한 계약:

1. Sync와 Support의 trainable trunk/optimizer group을 분리한다.
2. 초기에 head mask를 겹치지 않게 한다.
3. overlap을 허용할 때는 두 보정을 합친 후 **하나의 관절별 총 residual budget**으로 제한한다.
4. head contribution, cosine conflict, cap saturation을 항상 기록한다.
5. finger action은 마지막까지 source 독점으로 둔다.

판단: **현재 제1 가설**이다. 단, 단일 action-logit residual이 비열등이 아니면 더 단순한 그 구조를 선택한다.

### 4.6 Progressive network / 새 joint column

[Progressive Neural Networks](https://arxiv.org/abs/1606.04671)처럼 두 frozen column의 표현을 lateral connection으로 읽는 새 full column을 학습한다.

```text
frozen fret column -----+
                         +--> new full column --> joint action
frozen strike column ---+
```

장점:

- 기존 policy를 바꾸지 않으면서 표현력이 큰 새 정책을 만든다.
- 자유 기타처럼 source 분포에서 큰 변화가 필요할 때 action cap에 덜 구속된다.

한계:

- 새 모델이 source action을 완전히 덮어쓸 수 있다.
- zero-residual 등가성이 자연스럽게 보장되지 않는다.
- 학습 비용과 reward conflict가 커진다.

판단: residual cap이 지속적으로 포화되고 hybrid와 action residual이 둘 다 plateau에 도달할 때 검토한다.

### 4.7 Mixture of Experts / Product of Experts / MCP

[Composable Deep RL](https://arxiv.org/abs/1803.06773)은 공통 action space에서 soft-Q policy를 조합하고, [Soft Modularization](https://arxiv.org/abs/2003.13661)은 task/state 조건 routing으로 모듈을 soft combination한다. 이 계열은 여러 expert가 **같은 action space에서 대안 또는 조합 가능한 primitive**로 학습되었을 때 강하다.

현재 문제에 맞지 않는 이유:

- Fret과 Strike는 선택지가 아니라 동시에 실행돼야 한다.
- 두 action set이 분리되어 convex mixture/PoE가 의미 있는 절충을 만들지 못한다.
- 독립적으로 학습한 `log_std`는 서로 비교 가능한 confidence가 아니다.
- 새 `R_Thorax` action을 만들 expert가 없다.

판단: full output merger로 사용하지 않는다. 나중에 sync/stabilize residual 크기를 조절하는 scalar gate 또는 여러 곡/style을 학습하는 routing으로만 재검토한다.

### 4.8 Hierarchical/options

[Option-Critic](https://arxiv.org/abs/1609.05140)처럼 상위 정책이 하위 skill을 선택·종료하는 계층이다.

현재 문제에서 적합한 용도:

```text
GUITAR_FIXED
  → RELEASE_TRANSITION
  → WAIT_FOR_SETTLING
  → STABILIZE
  → PLAY
  → RECOVERY
```

적합하지 않은 용도:

- Fret 대 Strike 중 하나를 선택하는 hard option
- 60 Hz 모터 action을 option switch로 직접 만드는 것

판단: hierarchy는 **행동 merger가 아니라 phase manager**로 쓴다. 중요한 상태 전이는 초기에 학습 옵션이 아니라 명시적 state machine으로 둔다.

### 4.9 CTDE/MAPPO와 monolithic fine-tuning

[MADDPG](https://arxiv.org/abs/1706.02275)같은 centralized-training/decentralized-execution은 각 agent actor를 유지하고 critic만 joint state/action을 본다.

현재 프로젝트에서:

- 두 손은 하나의 몸과 하나의 process에서 실행된다.
- 분산 실행이나 communication 제약이 없다.
- 두 actor가 같이 바뀌면 서로에게 non-stationary environment가 된다.
- 중앙 critic이 문제를 평가할 수는 있어도 actor에 cross-hand correction 통로가 없으면 문제를 고치지 못한다.

따라서 **central joint critic은 사용하되, two-agent algorithm은 사용하지 않는다.**

Full fine-tuning은 표현력은 가장 높지만 source 스킬 망각, reward 간섭, 높은 학습 비용이 있다. residual·latent adapter가 cap 포화와 plateau를 보인 후에만 source tail 마지막 layer를 점진적으로 해제한다.

### 4.10 Distillation / ACT / Diffusion·Transformer

[Policy Distillation](https://arxiv.org/abs/1511.06295)은 여러 teacher를 하나의 student로 압축할 수 있다. 그러나 unsynchronized Fret·Strike를 teacher로 쓰면 실패한 병합을 잘 복제할 뿐이다.

따라서 distillation은:

1. 성공한 joint coordinator teacher를 먼저 만든 뒤,
2. 배포 비용을 줄이기 위해 쓰고,
3. student 자신이 만든 recovery 상태에서도 teacher label을 받도록 [DAgger](https://proceedings.mlr.press/v15/ross11a.html)형 데이터 수집을 하는

후기 단계다.

ACT와 Diffusion Policy는 bimanual action chunk와 multimodal trajectory에 강하지만 대량의 시연 joint trajectory가 필요하고, 독립 RL policy 두 개를 사후 결합하는 구조가 아니다. Action chunk temporal ensemble이 날카로운 strike onset을 평균낼 수도 있다. 현 병목이 곡의 장기 planning이라고 입증될 때만 상위 planner로 검토한다.

### 4.11 MLP, frame stack, TCN, GRU

현 source policy가 MLP인 이유는 q, qdot, goal lookahead, song phase, previous EMA action이 observation에 명시되어 있기 때문이다. Full coordinator도 다음을 모두 보면 고정 기타 sync와 rigid-body 안정화는 거의 Markov로 만들 수 있다.

- full q, qdot
- guitar pose, linear/angular velocity
- gravity in guitar frame
- event phase, ready dwell, sustain/recovery state
- previous executed action, previous residual
- support/contact state

따라서 **초기 모델은 GRU 없는 MLP**를 원칙으로 한다. GRU를 바로 넣으면 hidden reset, truncated BPTT, song memorization, rollout batching 복잡도가 추가된다.

다만 free guitar에서 마찰·strap hysteresis·slip trend처럼 숨은 물성을 추론해야 할 수 있다. [RMA](https://arxiv.org/abs/2107.04034)처럼 빠른 base policy와 history adaptation module을 나누는 구조가 근거가 된다.

초기에는 다음 순서로 반증한다.

```text
current-state MLP
  → selected slow signals 4-frame stack
  → fixed-window small causal TCN
  → coordinator-only GRU(about 128), if still necessary
```

모델 외부 계약에는 고정 크기 `history_context` slot을 두어, current-only/TCN/GRU encoder가 같은 크기 embedding을 내도록 한다. 이렇게 하면 coordinator core와 action/checkpoint manifest를 바꾸지 않고 temporal encoder만 교체할 수 있다.

### 4.12 QP/MPC/safety projection

[OptLayer](https://arxiv.org/abs/1709.07643)처럼 policy action에서 관절·충돌 제약을 만족하는 가장 가까운 action을 풀 수 있다.

```text
minimize    ||u - unominal||W² + ρ||slack||²
subject to  joint/rate/load/stability constraints
```

적합한 hard/soft constraint:

- joint position, velocity, action rate
- 명백한 충돌 금지 영역
- guitar pose/angular-velocity gross envelope
- support force 상한

주 merger로 적합하지 않은 이유:

- fret contact·string crossing은 hybrid·non-convex·model-error가 큰 이벤트다.
- 잘못된 constraint가 올바른 strike를 취소하거나 QP infeasible를 만들 수 있다.
- 시스템의 normalized joint target은 task-space acceleration/metric을 결합하는 RMP류와 직접 호환되지 않는다.

판단: 저속 reduced-order guitar safety shield 또는 fail-closed action envelope로만 쓴다. Intervention rate·slack·infeasibility를 항상 기록한다.

---

## 5. 잠정 권고 모델의 정확한 계약

### 5.1 정책 adapter

Coordinator가 `actor[:-1]`을 직접 호출하지 않고, source 구조를 숨기는 adapter를 둔다.

```text
FrozenPolicyAdapter
  input
    native_observation
    optional latent_injection

  output
    action_names
    raw_latent_mean
    raw_latent_log_std
    intent_embedding
    effective_action_transform_id
    source_contract_sha256
```

현 source에서 `intent_embedding` 256D를 제공할 수 있지만, adapter 외부는 내부 layer index를 몰라야 한다. 나중에 source architecture가 바뀌면 adapter projection만 새로 만든다. 다만 full checkpoint은 정확한 source checkpoint SHA-256에 어차피 반드시 귀속돼야 한다.

### 5.2 Coordinator input

```text
xcoord = concat(
  project(fret intent),
  project(strike intent),
  event/readiness context,
  live bimanual physical state,
  guitar/support context,
  guitar mode and assist λ,
  previous executed action/residual,
  optional fixed-size history context
)
```

최소 guitar/stability context:

- guitar pose relative to Chest/Pelvis
- rest pose와의 position + 6D orientation error
- guitar linear/angular velocity
- gravity vector in guitar frame
- strap extension/tension/stiffness mode
- hand-tether extension, relative velocity, normalized strength/cap/valid bit
- 허벅지·가슴·엄지·팔뚝 support contact/force
- support distribution, slip/drop margin
- previous SupportBranch residual

G0에서 zero인 물리 채널은 일반 RMS만 쓰지 않고 고정 물리 scale+clip 또는 block variance floor를 둔다. Source actor에는 반대편 손만 counterfactual masking하고, 움직이는 기타에 대한 자기 손의 guitar-relative geometry는 live로 유지한다.

모든 contact force를 크게 만드는 보상은 기타를 과도하게 조이는 해를 만든다. Pose, velocity, support distribution, penetration, over-force를 분리한다.

### 5.3 Core와 head

실험 전 후보 구조는 완전 공유 trunk가 아니라 두 branch를 분리한다.

```text
Fret/Strike intents + event ----------> SyncEncoder ----> SyncHead

live guitar/support + assist + event -> SupportEncoder -> SupportHead
                                                             |
                                                  phase-aware Arbiter
```

- activation은 현 source와 독립적으로 선택하되 checkpoint에 봉인한다.
- Sync/Support 마지막 layer는 정확히 zero-init한다.
- history context를 쓰면 fusion input 크기를 바꾸지 않도록 고정 projection slot으로 넣는다.
- 각 encoder의 정확한 hidden width는 512→256을 첫 baseline으로 쓴다. Width 자체보다 branch 경계·correction injection point·action ABI가 더 중요하다.

### 5.4 Joint distribution: sample은 한 번만 한다

피해야 할 구조:

```text
sample Fret
sample Strike
sample residual
세 sample을 더한 뒤 joint log_prob을 임의로 계산
```

권장 구조:

```text
μF, logσF = frozen Fret proposal
μS, logσS = frozen Strike proposal

μbase = assemble_by_name(μF, μS, neutral logits)
μjoint = latent_sync_tail(…) assembled + bounded Δμsupport

logσjoint[source slots] = copied source logσ
logσjoint[new slots]    = coordinator-owned small initial logσ

z ~ Normal(μjoint, σjoint)
araw = tanh(z)
```

원본 source `log_std`·actor·RMS는 별도 frozen object로 남긴다. Joint model은 source 분산 값을 복사한 자신의 distribution buffer/parameter를 쓴다.

- source slot의 std correction은 초기 freeze한다.
- `R_Thorax` 새 slot만 작은 std로 학습한다.
- 만약 탐색 부족이 입증되면 이미 구조에 포함된 `Δlogσ` 중 허용 group만 순차적으로 풀고 0 규제를 건다.
- reserved central-torso slot은 action override + log-prob mask로 정확히 neutral을 유지한다.
- inference는 `tanh(μjoint)`를 쓴다.

이렇게 하면 residual 0에서 source 두 diagonal Gaussian의 곱을 하나의 joint diagonal Gaussian으로 정확히 표현할 수 있다. 조정자가 joint mean을 공통 상태에 조건화하므로 action noise covariance가 diagonal이어도 타이밍 협업은 가능하다. SDH 공개 코드도 최종 sigma를 좌우로 concat한다.

### 5.5 Source action transform과 PPO 변수

PPO가 저장하는 action 변수는 `araw`이다. 환경이 실제로 실행하는 명령은 다음 deterministic transform의 결과다.

```text
aF_effective = FretSourceTransform(araw[Fret], source_prev_action, goal)
aS_effective = StrikeSourceTransform(araw[Strike], source_prev_action, phase)
afull        = NamedComposer(aF_effective, aS_effective, new/reserved slots)
executed     = CommonEMAAndPD(afull)
```

환경 transform이 deterministic이고 rollout에 raw sampled action/log-prob을 저장하면 PPO likelihood ratio를 일관되게 계산할 수 있다. 이는 현 Fret PPO가 curriculum action transform을 다루는 방식과 같은 분리다.

### 5.6 Action ownership 초기안

| 관절군 | Base owner | Sync | Support | 초기 규칙 |
|---|---|---|---|---|
| 왼손 finger | Fret | 금지/매우 작게 | 금지 | source 보존 |
| 왼 wrist | Fret | 작게 허용 | 초기 금지 | timing 후보 |
| 왼 shoulder/elbow | Fret | 제한 허용 | 제한 허용 | 총 budget 적용 |
| `L_Thorax` | neutral/new | 금지 | 허용 | 후기 안정화 후보 |
| 오른 finger | Strike | 초기 금지 | 금지 | pick grip 보존 |
| 오른 wrist | Strike | 제한 허용 | 초기 금지 | timing 후보 |
| 오른 shoulder/elbow | Strike | 제한 허용 | 제한 허용 | 총 budget 적용 |
| `R_Thorax` | neutral/new | 금지 | 단독 소유 | 첫 새 DOF |
| Torso/Spine/Chest | neutral/reserved | 금지 | 초기 금지 | 75D shape만 예약 |
| Guitar root | 없음 | 금지 | 직접 제어 금지 | 접촉·strap으로만 지지 |

초기 권한 확대 순서:

```text
1. 오른 proximal sync
2. R_Thorax support
3. 양쪽 proximal support
4. 왼 proximal sync
5. reserved central torso, 필요성이 입증될 때
6. finger residual, 마지막
```

### 5.7 Central multi-head critic

Source critic 6+1을 억지로 이어 붙이지 않고 full state를 보는 새 critic을 학습한다. 고정→보조→자유 전 단계에서 shape을 유지할 초기 reward/value head 후보는 11개다.

```text
fret strings          6
strike                1
joint event           1
guitar pose/velocity  1
guitar support        1
assist/action safety  1
total                11
```

이 11개 head는 G0부터 예약하되 물리 head는 diagnostic/weight 0으로 시작한다. G1 진입 시 value shape을 바꾸지 않는다. 현 PPO가 사용하는 “value-head advantage를 reward weight로 합성한 뒤 한 번만 standardize” 계약을 유지한다. 단순히 reward를 하나로 더하면 안정화 reward scale이 연주 reward를 압도하는 원인을 찾기 어렵다. [Composite Motion Learning](https://arxiv.org/abs/2305.03286)도 서로 다른 부분 동작·task objective를 multi-objective critic으로 다룬다.

---

## 6. 지금 고정해야 할 것과 내부 실험으로 남겨야 할 것

### 6.1 먼저 고정할 불변 계약

1. **FullActionManifest**
   - action name, order, source owner, neutral action
   - source slot, active/reserved mask
   - sync/support authority·cap
2. **FrozenPolicyAdapter**
   - native observation 버전
   - `counterfactual_mean` 대 `live` 규칙
   - source action transform 버전
   - source checkpoint/contract hash
3. **Event contract**
   - event id, target time, ready dwell, crossing, sustain, recovery
   - deadline/miss/escape 정의
   - success/reward/action gate 분리
4. **Joint distribution contract**
   - tanh 전 correction
   - one joint sample
   - source/new/reserved std 소유권
   - raw action 대 executed action 분리
5. **FullObservationManifest**
   - source 428/321 native view와 coordinator live view 분리
   - guitar/world/body coordinate frame
   - guitar mode, assist `λ`, tether/support slot과 fixed physical scale
   - history context/reset 계약
6. **Full checkpoint schema**
   - source 두 개의 exact hash/contract
   - coordinator/critic/optimizer/RMS
   - action/observation manifest
   - guitar asset mode·strap·mass/inertia/CoM/collision profile
   - tether anchor·stiffness·damping·slack·cap과 stage parent

### 6.2 외부 계약 안에서 비교할 수 있는 부분

- action-logit-only 대 latent+action hybrid
- early-512 latent 대 penultimate-256 latent injection
- coordinator width/depth/activation
- Sync/Support 분리 encoder 크기와 context 교환 방식
- per-joint residual cap
- source std correction 해제 순서
- MLP 대 frame stack/TCN/GRU history encoder
- critic hidden size와 reward weight
- SupportBranch action authority 확대 순서

이 변경은 full coordinator checkpoint는 다시 학습해야 할 수 있지만 Fret·Strike source checkpoint, event compiler, environment/action ABI를 다시 설계하게 만들지는 않는다.

---

## 7. 구조를 확정하기 전의 반증 실험

가장 단순한 가설부터 실패시켜야 한다. 복잡한 모델이 성공했다는 결과만으로는 그 복잡도가 필요했는지 알 수 없다.

### E0. Zero-injection equivalence

```text
guitar fixed
counterpart held
coordinator off
deterministic mean
```

검증:

- source native observation이 채널별로 동일한가
- source raw mean/action이 frame별로 동일한가
- source action transform 후 effective action이 동일한가
- common EMA/PD target이 동일한가
- Fret/Strike 단일손 지표가 허용 오차 내에서 보존되는가

이 단계가 실패하면 학습을 시작하지 않는다.

### E0b. Source observation OOD ablation

```text
live full proprioception
vs
counterfactual obs_rms.mean masking
```

비교:

- source mean action drift
- RMS clamp rate
- 단일손 지표 유지율
- 양손 실행 시 물리 상호작용

### E1. 학습 없는 타이밍 보정

1. constant offset sweep
2. readiness dwell gate
3. bounded local phase hold/time-warp
4. deadline miss/skip

이 단계만으로 joint 성공 목표를 달성하면 SyncAdapter를 학습하지 않는다.

### E2. Injection point matched comparison

같은 parameter 수, seed, environment step 예산, residual cap으로 비교한다.

```text
A: pre-tanh action-logit residual
B: early hidden latent residual
C: latent sync + action stabilize hybrid
```

선택 규칙:

- A가 C와 통계적으로 비열등이 아니고 보존 지표도 같으면 A를 선택한다.
- B/C가 source retention, sample efficiency, residual norm에서 명확히 나으면 latent sync를 선택한다.
- 평균만이 아니라 여러 seed 실패율과 worst-case metric을 본다.

### E3. Correction authority ablation

```text
오른 proximal only
  → + 왼 proximal
  → + wrist
  → + finger, only if necessary
```

동일 성능이면 가장 작은 action mask를 선택한다.

### E4. 고정 해제와 assist baseline

```text
G0 fixed asset
  → G1 free asset + strong bounded soft hand tether
  → G1 weak/random tether + exact-zero probes
  → G2 same free asset + tether exactly zero
```

- 양손 hard weld와 fingertip/pick attachment는 학습 후보에서 제외한다.
- Free asset의 mass/inertia/CoM와 collision profile을 먼저 audit한다.
- SupportBranch off 상태의 물리 scaffold-only baseline을 측정한다.
- `λ`, tether force/torque/work, cap saturation을 기록한다.
- Zero-tether probe가 실패하면 평균 assist 성능으로 진급하지 않는다.

물리 support만으로 안정하면 학습 SupportBranch의 권한을 줄인다. 단계별 상세는 [`CURRICULUM.md`](../04_training/CURRICULUM.md)를 따른다.

### E5. SupportBranch authority

```text
R_Thorax only
  → + bilateral shoulder/elbow
  → + L_Thorax
  → + reserved Torso/Spine/Chest
```

중앙 9 DOF는 “나중에 쓸 수 있다”가 아니라 “위 경로가 실패했음이 입증될 때만 해제한다”는 계약으로 둔다.

### E6. Temporal context

```text
current MLP
  → 4-frame selected stack
  → 0.25~0.5 s small TCN
  → coordinator-only GRU
```

다음이 입증될 때만 상위 모델로 간다.

- 같은 순간 observation에서 필요 residual 방향이 반복적으로 다르다.
- mass/friction/strap stiffness held-out 성능이 유의미하게 개선된다.
- current-state 채널 누락을 추가하는 것으로는 해결되지 않는다.

### E7. 최후 확장

1. residual cap sweep에서 지속 포화 + 성능 plateau
2. latent/action hybrid 둘 다 실패
3. source tail 마지막 layer 점진 해제
4. 그래도 실패할 때만 progressive/monolithic joint policy
5. 성공 joint teacher 후에만 distillation

---

## 8. 판정 지표

음원 최종 F1 하나로 구조를 고르지 않는다.

### 8.1 양손 이벤트

- `strike_crossing_time - fret_ready_time` 분포
- scheduled onset 대 fret-ready·crossing 시각
- premature crossing rate
- joint onset precision/recall/F1
- onset timing MAE/p95/signed quantile
- crossing 구간 fret hold rate
- chord/strum 내 줄별 readiness
- deadline miss/skip/late-gated rate

### 8.2 Source retention

- Fret 정확도·sustain·thumb support
- Strike string/direction/order/timing/recovery
- source 대 full deterministic mean drift
- source RMS clamp rate
- source action transform 등가성

### 8.3 기타 안정화

- guitar rest-pose position/orientation RMS·p95
- linear/angular velocity RMS·p95
- drop/slip/recovery rate
- strap extension/tension envelope
- 지지 부위별 contact distribution
- over-force, penetration, body collision
- strike 동작과 실제 support contact 변화 이후 settling time
- assist level별 tether force/torque/impulse/mechanical work
- physical support 대비 artificial assistance fraction
- exact-zero-tether success와 full-song survival

### 8.4 모델 개입

- sync/support residual norm by joint group
- per-joint cap saturation rate
- base 대 final action drift
- head-off performance drop
- sync/support overlap cosine/conflict rate
- action saturation, rate, jerk
- safety layer intervention/infeasibility

### 8.5 일반화

- held-out song/phrase
- tempo perturbation
- guitar mass/inertia/friction
- strap stiffness/damping/anchor variation
- source checkpoint variation
- reset pose/support contact variation

---

## 9. 최종 결정 전 checklist

- [ ] Fixed-guitar frozen union baseline을 실제로 측정했다.
- [ ] residual 0에서 source observation·mean·transform·PD target 등가를 검증했다.
- [ ] `live` 대 `counterfactual_mean` source view를 비교했다.
- [ ] 학습 없는 offset/readiness/phase gate baseline을 비교했다.
- [ ] 66 대 75 action ABI를 확정했다.
- [ ] source Fret action transform의 full-song 계약을 봉인했다.
- [ ] action-logit residual 대 latent hybrid를 matched budget으로 비교했다.
- [ ] joint distribution에서 한 번만 sample하고 log-prob을 raw action으로 계산한다.
- [ ] source actor, source `log_std`, source RMS가 모두 frozen임을 검증했다.
- [ ] reserved action이 숫자 0이 아니라 seated-hold neutral override + PPO mask로 fail-closed되는지 검증했다.
- [ ] success/reward/physical gate를 서로 다른 지표로 기록한다.
- [ ] Free guitar의 mass/inertia/CoM/body-order와 gravity/root mode를 audit했다.
- [ ] Full 전용 thumb-support+pluck-range collision profile을 atomic하게 구성했다.
- [ ] G1 soft hand-tether scaffold-only baseline을 측정했다.
- [ ] G1→G2에서 같은 free asset을 쓰고 exact-zero-tether probe를 통과했다.
- [ ] Observation과 11개 value head shape이 G0/G1/G2에서 동일하다.
- [ ] GRU는 current state/frame stack/TCN 한계가 증명된 후에만 추가한다.
- [ ] full checkpoint에 source hash, manifests, native-view mode, injection point, masks/caps, guitar mode를 봉인한다.

---

## 10. 최종 해석

현재 구조 선택의 핵심은 “두 모델의 결과를 어떻게 섞을까”가 아니다.

```text
두 source action은 관절 이름으로 그대로 조립한다.

조정자는
  1) source actor의 OOD observation을 막고,
  2) 왼손-ready→strike event 계약을 지키며,
  3) 같은 몸·기타에서 생기는 물리 교란을 보정하고,
  4) source에 없던 안정화 DOF만 새로 만든다.
```

그 관점에서 현재 가장 타당한 가설은 **명시적 event supervisor + frozen source adapters + 분리된 SyncBranch/SupportBranch + named arbiter + central multi-head critic**이다. SupportBranch는 별도 actor가 아니라 하나의 joint distribution mean을 구성하는 제한된 residual controller다. 그러나 고정 기타 sync에서 동일한 성능을 내는 단순 action-logit residual이 확인되면 SyncBranch는 더 단순한 그 모델을 선택해야 한다.

따라서 지금 할 일은 코드 구현이 아니라 다음 결정을 순서대로 닫는 것이다.

1. 66/75 action ABI
2. source `counterfactual_mean` native view
3. source Fret action transform 보존 계약
4. action-logit residual 대 latent+action hybrid matched ablation
5. Free guitar mass/inertia와 Full collision profile
6. Hand-tether anchor/force law와 `fully free`의 strap 계약

---

## 11. 참고 자료

### 프로젝트 내부

- [GPS·SDH 양손 병합 논문/코드 분석](../../docs/2026-08-26/FRET_STRIKE_MERGE_REFERENCE_RESEARCH.md)
- [현 `ActorCritic`](../../tab2body/learning/models.py)
- [현 base observation/action semantics](../../tab2body/env/base.py)
- [Fret task/source transform](../../tab2body/env/tasks/task_fret.py)
- [Strike task/observation manifest](../../tab2body/env/tasks/task_strike.py)
- [현 PPO multi-head advantage/checkpoint](../../tab2body/learning/ppo.py)

### 주요 1차 자료

- [Synchronize Dual Hands for Physics-Based Dexterous Guitar Playing](https://arxiv.org/abs/2409.16629), [official code](https://github.com/xupei0610/guitar)
- [AdaptNet: Policy Adaptation for Physics-Based Character Control](https://arxiv.org/abs/2310.00239), [official code](https://github.com/xupei0610/AdaptNet)
- [Residual Reinforcement Learning for Robot Control](https://arxiv.org/abs/1812.03201)
- [Policy Decorator: Model-Agnostic Online Refinement for Large Policy Model](https://arxiv.org/abs/2412.13630), [official code](https://github.com/tongzhoumu/policy_decorator)
- [Progressive Neural Networks](https://arxiv.org/abs/1606.04671)
- [Composable Deep Reinforcement Learning for Robotic Manipulation](https://arxiv.org/abs/1803.06773)
- [Multi-Task Reinforcement Learning with Soft Modularization](https://arxiv.org/abs/2003.13661)
- [The Option-Critic Architecture](https://arxiv.org/abs/1609.05140)
- [Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments](https://arxiv.org/abs/1706.02275)
- [Composite Motion Learning with Task Control](https://arxiv.org/abs/2305.03286)
- [Policy Distillation](https://arxiv.org/abs/1511.06295)
- [DAgger](https://proceedings.mlr.press/v15/ross11a.html)
- [RMA: Rapid Motor Adaptation for Legged Robots](https://arxiv.org/abs/2107.04034)
- [OptLayer: Practical Constrained Optimization for Deep RL](https://arxiv.org/abs/1709.07643)
- [Beyond Action Residuals: Bottleneck Latent RL (2026 preprint)](https://arxiv.org/abs/2605.19919)
