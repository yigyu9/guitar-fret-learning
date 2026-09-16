# Action 소유권과 병합 규칙

> **상태: SUPERSEDED.** 아래 75D 후보는 폐기되었다. 현재 계약은 이름이 봉인된 105D이며 G0에서 60D source-active + 45D held다. 정본은 [`master_plan/07_full_body_player.md`](../../master_plan/07_full_body_player.md)다.

> 상태: **75D ABI 잠정 권고 — 최종 확정 전**

## 1. 장기 action manifest 후보

| 그룹 | 차원 | Base owner | G0 | G1 초기 | G2 후보 |
|---|---:|---|---|---|---|
| Fret source | 30 | Frozen Fret | active | active | active |
| Strike source | 30 | Frozen Strike | active | active | active |
| `L_Thorax` + `R_Thorax` | 6 | SupportBranch | hold | 단계적으로 active | active |
| Torso/Spine/Chest | 9 | SupportBranch reserved | hold | hold | 증거가 있을 때 해제 |
| 합계 | 75 |  |  |  |  |

Neck/Head 6과 하체 24는 현재 manifest에서 제외한다. Guitar root는 직접 action으로 제어하지 않는다.

## 2. Reserved neutral

Reserved/inactive action의 neutral은 숫자 `0`이 아니다. 현 normalized action 0은 관절 hard range의 midpoint다.

```text
hold_action[joint] = actions_for_pd_targets(init_pose[joint])
```

- Inactive slot은 `hold_action`으로 deterministic override한다.
- 해당 slot은 PPO log-prob/entropy에서 mask한다.
- Pre-tanh neutral mean이 필요하면 clipped `atanh(hold_action)`을 사용한다.
- Action manifest에 관절별 neutral과 그 계산 버전을 봉인한다.

## 3. Branch 소유권

| 관절군 | Source | SyncBranch | SupportBranch |
|---|---|---|---|
| 양손 finger | 독점 | 금지 | 금지 |
| 양 wrist | base | 제한된 timing | 초기 금지, 최후 후보 |
| 양 shoulder/elbow | base | 제한 | 단계적으로 제한 허용 |
| `L_Thorax` | 없음 | 금지 | 후기 후보 |
| `R_Thorax` | 없음 | 금지 | 첫 신규 권한 |
| 중앙 몸통 9 | 없음 | 금지 | G2에서 증거가 있을 때만 |

같은 관절에서 두 residual이 겹치면 각각 cap을 적용한 뒤 다시 하나의 총 joint cap을 적용한다.

```text
delta_mu_total_j = cap_total_j(delta_mu_sync_j + delta_mu_support_j)
```

## 4. 적용 순서

```text
source μ/std 제안
→ Sync correction
→ Support correction
→ phase/authority mask
→ per-joint total cap
→ one joint TanhNormal sample
→ source Fret/Strike transforms
→ inactive seated-hold override
→ common EMA/PD
```

낙하·과도한 접촉력 hard safety가 임박할 때의 우선순위는 다음과 같다.

```text
hard safety > source finger integrity > event timing > posture comfort
```

안정 조건을 deadline 전에 만족하지 못하면 늦게 타현하지 않고 miss/skip한다.

세부 모델 비교는 [`MODEL_FUSION_STUDY.md`](MODEL_FUSION_STUDY.md), 물리 단계는 [`GUITAR_STABILIZATION.md`](GUITAR_STABILIZATION.md)를 참조한다.
