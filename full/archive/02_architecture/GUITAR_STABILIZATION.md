# 기타 고정 해제와 안정화 구조

> **상태: SUPERSEDED AS CONTRACT.** 초기 안정화 검토 기록이다. 현재 StabilityAdapter·G0/G1/G2·가상 strap 계약은 [`master_plan/06_stability_adapter.md`](../../master_plan/06_stability_adapter.md)와 [`master_plan/09_curriculum_and_evaluation.md`](../../master_plan/09_curriculum_and_evaluation.md)를 따른다.

> 상태: **설계 검토 중 — 구현 전 계약 초안**  
> 목표: `고정 기타 → physical strap + 손 보조 → physical strap만 남은 자유 기타`를 동일한 정책·관측·action ABI로 학습한다.

## 1. 문제 정의

Full 정책은 두 가지 책임을 동시에 수행한다.

1. **연주 조정**
   - 왼손 Fret 준비와 오른손 Strike 시각을 맞춘다.
   - 기존 단일손 기술과 source action transform을 보존한다.
2. **물리적 지지**
   - 기타의 6DoF pose와 선·각속도 드리프트를 억제한다.
   - 팔·손의 실제 접촉 변화와 외란에서도 허용 범위로 회복한다.
   - 인공 보조가 사라져도 실제 strap과 손·팔·몸통 접촉으로 기타를 유지한다.

따라서 안정화는 세 번째 독립 actor가 아니다. 독립적으로 sample한 안정화 action을 양손 action에 더하면 관절 소유권과 PPO log-prob이 불명확해진다. 대신 하나의 Full actor 안에 다음 두 trainable branch를 둔다.

```text
Frozen Fret proposal --------> SyncBranch --------+
                                                    |
Frozen Strike proposal ------> SyncBranch --------+--> Named Arbiter
                                                    |        |
Live guitar/support state ---> SupportBranch ------+        v
                                              one joint TanhNormal
```

- `SyncBranch`: 이벤트 타이밍과 기존 동작 내부의 작은 수정
- `SupportBranch`: 기타 6DoF를 폐루프 안정화하는 bounded action-logit residual
- `Named Arbiter`: 관절별 소유권·phase mask·총 residual cap 적용
- 최종 mean/std를 조립한 뒤 공동 분포에서 한 번만 sample

두 branch는 입력을 공유할 수 있지만 trainable trunk와 optimizer group은 분리한다. 그래야 고정 기타에서 배운 sync를 안정화 gradient로부터 동결할 수 있다.

---

## 2. 기타 상태 세 단계

### G0 — Fixed

```text
guitar root       fixed
gravity           off
physical strap    force disabled
artificial assist none
SupportBranch     exact zero + frozen
```

목적은 source 등가성, 양손 action 조립, Fret-ready→Strike 계약, SyncBranch 비교다. 안정화 reward는 계산할 수 있지만 학습 신호로 사용하지 않는다.

현재 구현이 정확히 이 모드다. [`tab2body/env/base.py`](../../tab2body/env/base.py)는 asset 로딩 시 `fix_base_link=True`, `disable_gravity=True`를 사용한다.

### G1 — Hand-assisted free guitar

```text
guitar root       free
gravity           on
physical strap    strapped-v1 always on
artificial assist force-capped compliant hand tether
assist level λ    strong → weak → mixed with zero
SupportBranch     active
```

이 단계부터 기타는 처음부터 자유 rigid body여야 한다. G0 asset의 고정을 episode 도중 해제하지 않는다. G1과 G2는 같은 free asset과 같은 `strapped-v1` 물리 스트랩을 쓰고, 인공 보조력의 계수 `λ`만 바꾼다.

여기서 “손에 묶는다”는 말은 다음으로 정의한다.

- fret fingertip이나 pick을 기타에 rigid weld하지 않는다.
- 왼쪽은 palm/thumb-side와 neck support anchor 사이를 보조한다.
- 오른쪽은 pick이 아닌 palm/wrist/forearm-side와 body support anchor 사이를 보조한다.
- 연주 방향에는 dead-zone/slack을 크게 두고, 분리·낙하 방향에 더 큰 복원력을 둔다.
- 힘과 토크에는 cap과 rate limit을 둔다.
- 가능하면 기타와 사람에게 equal-and-opposite force를 적용한다.

### G2 — Fully free

```text
guitar root       free
gravity           on
artificial tether exactly zero
physical strap    strapped-v1 remains on
support           strap + physical body/arm contact
```

`fully free`의 검증 가능한 정의는 **인공 hand tether·root wrench·kinematic reset injection이 정상 step 동안 0**인 것이다. 실제 physical strap은 제거 대상이 아니다. `free root`와 `strap 없음`은 같은 뜻이 아니므로 체크포인트에 다음 값을 명시한다.

```text
support_hardware = strapped-v1
```

메인 학습과 G2 주 평가의 기본값은 `strapped-v1`이다. `none`은 unstrapped ablation에서만 사용하며, 인공 tether를 strap으로 부르지 않는다.

신체의 기타 지지는 상세 mesh contact 대신 rigid body에 부착된 단순 box/capsule support
proxy를 사용한다. 초기 집계 단위는 `body_contact`(양쪽 허벅지·몸통)와
`arm_contact`(양쪽 손바닥·전완)이며, 손가락 끝은 연주 접촉으로만 취급한다. 이 proxy는
가상 spring이 아니라 기타와 실제 contact·friction force를 주고받는다.

현재 사람 root와 하체는 고정·재주입되므로 여기서 `fully free`는 **기타 root만 완전히 자유롭다**는 뜻이다. 허벅지는 사실상 고정된 지지면이다. 나중에 사람의 균형까지 풀 경우에는 별도 단계와 action ABI 재검토가 필요하다.

---

## 3. 왜 hard weld가 아닌 soft tether인가

| 방법 | 장점 | 치명적 문제 | 사용 판단 |
|---|---|---|---|
| 양손 hard weld | 초기 pose를 확실히 유지 | 과구속, 큰 solver impulse, fret/strike 방해, 해제 시 dynamics cliff | 학습에 사용하지 않음 |
| 한 점 hard weld | smoke test가 쉬움 | 실제 지지 전략을 배우지 못함 | free asset 진단에만 제한 |
| Rest-pose assistive wrench | 구현과 annealing이 단순 | 손을 사용하지 않고 외력에 기대는 해 | rescue/비교 baseline |
| 두 support anchor soft tether | 손과 기타의 관계를 유지하면서 점진 해제 가능 | stiffness·slack·force cap 조율 필요 | **G1 권고안** |

권장 보조력의 개념식은 다음과 같다.

```text
e_i    = anchor_guitar_i - anchor_support_i
v_i    = relative anchor velocity
F_i    = clip( K_i(λ) · deadzone(e_i) + C_i(λ) · v_i, Fmax_i )
λ      ∈ [0, 1]
K_i(λ) = λ K_i0
C_i(λ) ≈ 2 ζ sqrt(K_i(λ) m_eff)
```

- episode 안에서는 `λ`를 고정해 hidden non-stationarity를 만들지 않는다.
- actor와 critic 모두 현재 `λ`와 mode mask를 관측한다.
- 두 anchor 모두 full 6D orientation을 강제하지 않는다. 위치·분리 방지 중심으로 두고, 필요한 경우 기타 rest-pose에 대한 약한 회전 damping만 별도로 둔다.
- strike 직후의 정상 충격까지 제거하지 않도록 event phase별 force·reward envelope를 사용한다.

고강성 tether는 reset 직후 stale body pose로 계산하면 폭발할 수 있다. Reset된 환경은 live rigid-body state가 유효해질 때까지 최소 한 physics frame 동안 tether를 비활성화하고 `tether_valid` latch가 열린 뒤에만 보조력을 적용한다.

---

## 4. 모델 구조에 미치는 영향

### 4.1 Sync와 Support의 경계를 고정한다

```text
SyncBranch inputs
  source intent embeddings
  fret-ready/strike event
  local hand geometry and next-event context

SyncBranch outputs
  ΔhF, ΔhS 또는 제한된 timing residual

SupportBranch inputs
  live guitar pose/twist
  body-relative support geometry
  contact/slip state
  assist mode and λ
  source proposed joint mean
  next strike time/direction

SupportBranch outputs
  bounded Δμsupport[action ABI]
```

SupportBranch는 다음 strike phase를 관측해 안정화 residual이 오른손의 접근·통과를 방해하지
않도록 한다. 가상 string crossing 자체는 기타에 충격을 주지 않는다. Strike 전후 안정화는
물리적 pick-string 반력 대응이 아니라 실제 팔·손 support contact 변화와 기타 운동을 다룬다.

### 4.2 공유 trunk 한 개를 피한다

고정 기타의 sync reward와 자유 기타의 stability reward는 같은 shoulder/elbow에 반대 gradient를 줄 수 있다. 처음부터 한 trunk로 강결합하면 G1 학습이 G0 timing을 망가뜨렸을 때 원인을 분리하기 어렵다.

권고 구조:

```text
SyncEncoder    → SyncHead
SupportEncoder → SupportHead
                    |
         phase-aware Named Arbiter
                    |
          per-joint total residual cap
```

- 두 head 마지막 layer는 zero-init한다.
- G1 초기는 Sync 전체를 freeze하고 Support만 학습한다.
- 두 branch를 함께 미세조정하는 것은 zero-tether probe가 통과한 뒤로 미룬다.
- 공유가 필요하면 고정 크기 context embedding만 교환하고, 전체 trunk를 합치지 않는다.

### 4.3 Action ABI

완전 자유 기타가 최종 목표이므로 장기 후보는 75차원이 더 타당하다.

```text
75 = Fret source 30
   + Strike source 30
   + L_Thorax/R_Thorax 6
   + reserved Torso/Spine/Chest 9
```

초기 권한 순서:

```text
G0: source 60 only
G1a: + R_Thorax
G1b: + bilateral shoulder/elbow support residual
G1c: + L_Thorax if needed
G2:  + central torso 9 only after prior masks fail
```

- Guitar root는 action에 넣지 않는다.
- Fret/Strike finger는 source 독점으로 유지한다.
- 예약 9개는 seated-hold neutral override와 PPO log-prob mask로 fail-closed한다. 현 action의 숫자 0은 관절 범위 midpoint이므로 neutral로 쓰지 않는다. `actions_for_pd_targets(init_pose)`의 per-DOF action 또는 PD init-target bypass를 사용한다.
- 같은 proximal joint에 Sync와 Support가 겹치면 합산 결과에 하나의 총 cap을 적용한다.
- 낙하·과도한 힘 hard safety가 임박하면 늦은 타현을 만들지 말고 해당 event를 miss/skip한다.

---

## 5. Observation 계약

G0/G1/G2에서 observation shape은 동일하다. 존재하지 않는 신호는 zero와 mode mask를 함께 제공한다.

### Actor에 필요한 정보

- guitar pose relative to Chest/Pelvis
- rest pose position error + 6D orientation error
- guitar linear/angular velocity
- gravity vector in guitar frame
- support site별 guitar-relative pose와 relative velocity
- contact on/off, normal/tangential force proxy, friction/slip margin
- drop margin과 support polygon/분포
- `guitar_mode`, `assist_level λ`, tether extension와 actor가 감지 가능한 tension
- event phase, fret-ready dwell, strike deadline/direction
- source proposed mean/intents
- previous Support residual과 executed action

배포 때 알 수 없는 정확한 mass, friction, hidden tether wrench는 actor 입력으로 쓰지 않는다. 이런 privileged physics 값은 central critic과 진단 로그에만 줄 수 있다.

### Source actor view

Source의 반대편 손 q/qdot은 `obs_rms.mean`으로 가릴 수 있지만, 움직이는 기타 때문에 바뀌는 **자기 손과 기타의 상대 geometry는 live로 유지**해야 한다. 이를 고정하면 Fret과 Strike가 움직이는 fretboard/string을 볼 수 없게 된다.

```text
source own-hand guitar geometry = live
source opposite-hand channels  = counterfactual mean initially
coordinator full physical view = live
```

Source actor/RMS/log_std/transform은 영구 freeze하고 coordinator normalization은 별도로 관리한다.

G0에서 tether·velocity 채널이 오랫동안 0이라고 일반 running RMS만 사용하면, G1의 첫 nonzero 값이 과도하게 정규화될 수 있다. Guitar pose/error, velocity, force는 물리적 허용 범위로 나눈 고정 scale+clip을 우선 사용하고, running RMS를 사용한다면 block별 variance floor를 둔다.

---

## 6. Reward와 event gate

안정화 reward는 단일 contact-force 보상이 아니다.

```text
guitar_pose           rest/envelope position and orientation
guitar_twist          linear/angular velocity and settling
support_quality       useful load distribution and friction margin
slip_drop             drift, slip, drop and recovery
contact_safety        penetration and over-force
assist_dependence     tether force/torque/work fraction
action_quality        support residual magnitude/rate/jerk
```

Contact force 자체를 크게 보상하면 기타를 과도하게 조이는 해를 만든다. 각 support site는 `[Fmin, Fmax]` band와 slip margin을 사용한다. 현 net contact tensor만으로는 접촉 상대 pair를 직접 알 수 없으므로, support attribution은 전용 proxy 또는 geometry gate와 함께 사용해야 한다.

권장 value/reward head 수는 최소 11개다.

```text
Fret strings                 6
Strike                       1
Joint event                  1
Guitar pose/twist            1
Support/slip/over-force      1
Assist dependence/action     1
total                       11
```

이 11개 shape은 G0부터 예약한다. Fixed 단계에서 물리 head는 diagnostic 또는 weight 0으로 두고 G1에서 활성화한다. G1 진입 시 value dimension을 늘리는 방식은 동일 모델·checkpoint ABI라는 목표와 충돌한다.

타현 허용 조건은 다음과 같이 확장한다.

```text
strike_permission =
  fret_ready_dwell
  AND guitar_stable_dwell
  AND strike_ready
```

`guitar_stable_dwell`은 pose error, twist, support/slip margin이 연속 시간 동안 허용 범위 안에 있었음을 뜻한다. 음악 clock은 멈추지 않는다. Deadline 안에 조건을 만족하지 못하면 늦게 치지 않고 miss/skip한다.

---

## 7. 현재 코드에서 먼저 해결할 물리 blocker

1. [`guitar_asset.xml`](../../tab2body/assets/guitar_asset.xml)의 물리 target mass/inertia/CoM을 명시하고 자유 asset 로딩을 검증한다.
2. Geometry/inertial이 없는 string marker를 포함한 39-body asset에서 mesh, fret, helper box의 자동 밀도가 의도치 않게 질량에 포함되지 않는지 body별 property를 dump한다.
3. 모든 동역학 body mass/inertia의 finite·positive 조건과 total mass/CoM을 load-time audit한다. Marker lookup이 body name/order에 의존하므로 fixed body를 무심코 collapse하지 않는다.
4. Free mode에서 `fix_base_link=False`, `disable_gravity=False`가 실제 적용됐는지 fail-fast audit한다.
5. Reset 직후 tether one-frame disable과 `tether_valid` latch를 둔다.
6. Guitar root pose/velocity와 assist 상태를 Full observation manifest에 추가한다.
7. Tether force/torque/work와 cap saturation을 매 step 기록한다.
8. G2에서는 인공 force tensor가 정확히 zero인지 평가 시 assertion한다.
9. Fret의 thumb-support collision과 Strike의 pluck-range 비충돌 설정을 순서대로 재사용하지 않는다. Full 전용 atomic collision profile과 startup audit을 만들고, 새 palm/thigh support proxy도 같은 manifest에 봉인한다.
10. Rest-pose/tether target은 asset XML의 예시 주석이 아니라 실제 [`seated_pose.json`](../../tab2body/assets/seated_pose.json)과 runtime 계산값을 정본으로 사용한다.

현재 live guitar-local 좌표 경로와 root reset snapshot은 [`base.py`](../../tab2body/env/base.py)에 이미 준비돼 있다. Fret geometry와 Strike string도 live guitar frame을 사용한다. 따라서 주요 누락은 자유 asset 물성, 보조력, 안정화 관측·보상이다.

---

## 8. 체크포인트 불변 계약

Full checkpoint에는 다음을 봉인한다.

- `guitar_mode`: fixed / hand_assisted / free
- `support_hardware`: none / physical_strap
- guitar asset fingerprint, mass/inertia/CoM
- anchor body·point·frame 정의
- tether stiffness/damping/slack/cap/rate limit와 `λ` 분포
- observation manifest와 zero/mode mask 의미
- active/reserved action mask와 Sync/Support authority
- source 두 checkpoint hash와 native-view rule
- source action transform version
- reward/value heads와 event/guitar-stable gate
- 부모 단계 checkpoint와 promotion reason

G0→G1은 asset 계약이 바뀌므로 일반적인 같은-run resume가 아니라 명시적 **stage promotion**으로 기록한다. G1→G2는 같은 free asset에서 `λ`를 0으로 만드는 연속 curriculum이다.

---

## 9. 아직 닫지 않은 결정

1. 완전 자유 상태에 실제 물리 strap을 남길지
2. 왼쪽·오른쪽 support anchor의 정확한 body/point
3. Tether가 tension-only인지 작은 compression도 허용할지
4. 75D ABI를 최종 확정할지
5. G2에서 중앙 몸통 9개가 실제로 필요한지
6. SupportBranch에 current-state MLP만 쓸지 작은 TCN이 필요한지

단계와 전환 기준은 [`CURRICULUM.md`](../04_training/CURRICULUM.md)를 참조한다.
