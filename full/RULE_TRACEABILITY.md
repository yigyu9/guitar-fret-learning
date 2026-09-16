# 규칙 추적표

> 상태: **현재 상위 계약 연결표**

| 책임 | 설계 정본 | 구현·검증 |
|---|---|---|
| Canonical PlayEvent | `master_plan/05_synchronizer.md`, `08_shared_contracts.md` | `tab2body/full/events.py`, `test_full_events.py` |
| 공통 clock/cursor | `master_plan/05_synchronizer.md` | `tab2body/full/clock.py`, `test_full_contract.py` |
| Fret readiness | `master_plan/03_fret.md`, `05_synchronizer.md` | `tab2body/full/readiness.py` |
| Rule Synchronizer | `master_plan/05_synchronizer.md` | `tab2body/full/synchronizer.py` |
| Source checkpoint | `master_plan/08_shared_contracts.md` | `tab2body/full/source_policies.py` |
| 105D action ownership | `master_plan/07_full_body_player.md` | `tab2body/full/action.py` |
| G0 runtime transaction | `master_plan/07_full_body_player.md` | `tab2body/full/runtime.py`, `env/tasks/task_full.py` |
| StabilityAdapter | `master_plan/06_stability_adapter.md` | 미구현 |
| G1/G2 curriculum | `master_plan/09_curriculum_and_evaluation.md` | 미구현 |
| Strap constraint | `master_plan/06_stability_adapter.md` | `strap_sim/` probe만 구현 |

과거 `AdaptNet`, `JointCoordinator`, 75D action-residual 문서는 현재 Rule Synchronizer의
구현 근거가 아니라 비교·폐기 이력이다.
