# 병합 관측과 보상 구조

> **상태: SUPERSEDED.** 아래 고정 shape와 reward head는 초기 후보다. 현재 source view는 Fret-v2 420D, Strike-v2 303D이며 Full 계약은 [`master_plan/08_shared_contracts.md`](../../master_plan/08_shared_contracts.md)를 따른다.

> 상태: **고정 shape 계약 초안**

## 1. 관측 view 분리

```text
Fret adapter      source 428D native view
Strike adapter    source 321D native view
Coordinator       live full-body + guitar/support/event view
Central critic    coordinator view + privileged physics
```

Source view 원칙:

- Source 자신의 손과 움직이는 기타 사이의 상대 geometry는 live다.
- 반대편 손 q/qdot은 초기에는 source `obs_rms.mean`으로 가린다.
- Source actor/RMS/log_std/action transform은 영구 freeze한다.
- Tether나 새 guitar dynamics 채널을 source observation에 추가하지 않는다.

## 2. Coordinator 고정 slot

G0/G1/G2에서 dimension과 순서를 바꾸지 않는다.

- 두 source intent/proposed mean
- full q/qdot와 previous executed action/residual
- event phase, fret-ready/strike deadline/direction
- guitar pose relative Chest/Pelvis와 rest error
- guitar linear/angular velocity와 guitar-frame gravity
- support anchor별 relative pose/velocity
- contact/proxy, slip/drop/over-force margin
- guitar mode, assist `λ`, tether valid/extension/tension/cap state
- optional fixed-size history embedding

G0에서 없는 tether 신호는 zero+valid/mode mask로 표시한다. Pose, velocity, force block은 실제 허용 단위의 고정 scale+clip을 우선 사용한다. G0의 zero variance로 인해 G1 관측이 폭주하지 않게 일반 running RMS만 사용하지 않는다.

정확한 mass/friction/hidden physics 값은 actor에 주지 않고 central critic이나 진단에만 사용할 수 있다.

## 3. 11개 reward/value head 후보

| 그룹 | 수 | 의미 |
|---|---:|---|
| Fret | 6 | 줄별 압현·유지 |
| Strike | 1 | 순서·방향·시각·회복 |
| Joint event | 1 | ready→strike→sustain 계약 |
| Guitar pose/twist | 1 | 자세·속도·settling |
| Physical support | 1 | 지지 분포·slip·over-force |
| Assist/action safety | 1 | tether 의존·residual cost·recovery |
| 합계 | 11 | |

11개 head는 G0부터 shape을 예약한다. G0에서는 물리 head를 diagnostic 또는 reward weight 0으로 두고 G1부터 활성화한다.

## 4. 안정화 reward 원칙

- 정확한 한 pose를 강제하지 않고 허용 dead-zone/envelope를 둔다.
- Contact force 크기 자체가 아니라 `[Fmin,Fmax]` band와 slip margin을 보상한다.
- Strike 직후에는 정상 충격을 위한 짧은 grace envelope를 두고 이후 settling을 평가한다.
- Tether force/torque/impulse/work와 physical support를 분리한다.
- Drop·penetration·over-force를 음악 reward에 묻지 않고 별도 gate로 본다.

타현 허용 조건:

```text
fret_ready_dwell AND guitar_stable_dwell AND strike_ready
```

음악 clock은 계속 진행하며 deadline을 넘으면 miss/skip한다.

세부 커리큘럼은 [`CURRICULUM.md`](../04_training/CURRICULUM.md)를 참조한다.
