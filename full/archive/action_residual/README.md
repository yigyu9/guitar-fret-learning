# Action Residual Coordinator — 75D no-gaze baseline

> **상태: HISTORICAL PROTOTYPE / NOT CURRENT SYNCHRONIZER.** 구현과 테스트는 비교용으로 보존한다. 현재 FullBody는 105D이고 Synchronizer는 관절 residual을 출력하지 않는다.

> 상태: **I0 encoding·action 안전 계약 구현 완료**. 아직 `task_full.py`와 PPO 학습 루프에는 연결하지 않았다.

이 디렉터리는 사용자가 처음 생각한 단순 병합안을 별도 구조로 보존한다.

이 구현은 과거 양손 연주와 기타 안정화에 집중한 **75D/no-gaze 기준선**이다. 당시 검토한
81D+Gaze 후보 문서는 현재 저장소에 없으며, 현재 105D FullBody 계약과 호환되지 않는다.

```text
Frozen Fret 행동 제안 + Frozen Strike 행동 제안
                    + 악보·준비도·관절·기타 상태
                              ↓
                    Action Residual 모델
                              ↓
              제한된 pre-tanh 행동 보정 Δμ
                              ↓
                    하나의 75D 행동 분포
```

소스 정책의 256차원 hidden activation은 읽거나 수정하지 않는다. 따라서 이 구조는 이후 만들 수 있는 `full/latent_sync/`와 모델·checkpoint가 섞이지 않는다.

## 현재 코드에서 확인한 기준

2026-09-01 현재 최신 코드와 checkpoint shape은 다음과 같다.

| 항목 | 실제 구조 |
|---|---|
| Fret actor | observation 425 → 512 → 256 → action 30 |
| Strike actor | observation 327 → 512 → 256 → action 30 |
| Frozen source 합계 | 60 DoF |
| 신규/예약 body | 양쪽 Thorax 6 + Torso/Spine/Chest 9 = 15 DoF |
| 장기 Full action ABI | 75 DoF |

과거 문서의 Fret 33 DoF는 현재 checkpoint와 맞지 않는다. 구현은 위 숫자를 slice로 하드코딩하지 않고 checkpoint의 정렬된 관절 이름으로 action을 조립한다. v1 coordinator를 만들 때는 30+30+15=75, arm residual 18, protected finger 42, `joint_context=75×8`을 모두 fail-closed 검증한다.

또한 현재 가장 최신인 Fret과 Strike checkpoint는 서로 다른 곡에서 학습됐다. 실제 Full 학습에서는 반드시 **같은 곡·같은 goal timeline**의 두 checkpoint를 한 쌍으로 선택해야 한다. 현재 구현은 source 관절 이름·순서와 checkpoint SHA-256까지 강제하며, 곡 ID와 goal timeline hash 검증은 Full checkpoint loader를 연결할 때 추가해야 한다.

## 모델 규모

현재 60D source/75D Full profile 기준 actor는 다음과 같다.

```text
소스 행동 평균 60 → 128 → 64
목표·악보 정보 128 → 128 → 64
압현·타현 준비 정보 64 → 128 → 64
상체 관절·이력 600 → 256 → 128
기타·접촉·보조 상태 128 → 128 → 64

concat 384 → 512 → 256
                  ├─ 팔 보정 head 256 → 128 → 18
                  └─ 몸통 보정 head 256 → 128 → 15
```

두 head의 마지막 Linear는 정확히 0으로 초기화한다. 학습 시작 시 출력은 기존 Fret/Strike 결과와 완전히 같고, PPO가 필요성을 확인한 관절에만 작은 보정을 배운다.

Goal은 모델에 포함된 shared EventTokenEncoder가 categorical 값을 처리한다. Readiness/joint/guitar context는 이름·offset·물리 scale·valid 규칙이 봉인된 typed packer가 만든다. 실제 Full runtime은 semantic 입력을 이 packer에 공급해야 한다.

Actor 674,914개, 별도 11-head central critic 665,213개로, 새로 학습하는 전체는 1,340,127개 parameter다. 동결된 Fret/Strike 모델은 이 수치에서 제외한다.

## 중요한 실행 규칙

- Fret/Strike actor, observation RMS, source `log_std`는 동결한다.
- Runtime은 raw mean tensor가 아니라 이름·checkpoint SHA를 보존한 `SourceProposal`로 coordinator를 호출한다.
- source observation은 bare tensor로 adapter에 넘기지 않고 tagged native/projected 입력을 사용한다. projected raw는 source RMS를 정확히 한 번만 거친다.
- 보정은 최종 action이 아니라 **tanh 이전 평균**에 더한다.
- 팔 18 DoF와 body 15 DoF만 보정 가능하며, 양손 finger 42 DoF의 residual은 항상 0이다.
- residual authority, stochastic execution, PPO credit mask를 분리한다. source finger는 실행하되 coordinator credit에서는 제외할 수 있다.
- 관절별 `cap_rad`를 현재 base mean 주변의 방향별 pre-tanh cap으로 변환해 보정 범위를 제한한다.
- source 평균과 body seated-hold neutral을 75D로 조립한 뒤, 하나의 joint `TanhNormal`에서 한 번만 sample한다.
- PPO는 FP32 pre-tanh latent를 저장·재평가하며 포화 action을 `atanh`로 복원하지 않는다.
- inactive body slot은 숫자 0이 아니라 seated pose에서 계산한 neutral action으로 덮는다.
- 기타 root는 action으로 직접 제어하지 않는다.

## 파일

- [`model.py`](../../action_residual/model.py): zero-initialized pre-tanh residual actor
- [`critic.py`](../../action_residual/critic.py): training-only privileged 입력을 지원하는 11-head central critic
- [`manifest.py`](../../action_residual/manifest.py): 관절 이름, 소유권, neutral, cap, source SHA 계약
- [`checkpoint_utils.py`](../../action_residual/checkpoint_utils.py): checkpoint tensor finite 선검증
- [`source_adapter.py`](../../action_residual/source_adapter.py): 기존 정책을 동결하고 평균·표준편차만 읽는 adapter
- [`source_projection.py`](../../action_residual/source_projection.py): non-owned raw observation을 source RMS 평균으로 치환한 뒤 동결 RMS를 적용하는 projected legacy view
- [`source_intent.py`](../../action_residual/source_intent.py): source pre-tanh mean의 encoder용 frozen robust calibration
- [`distribution.py`](../../action_residual/distribution.py): 75D를 한 번만 sample하는 masked joint distribution
- [`action_safety.py`](../../action_residual/action_safety.py): 세 action mask와 관절별 radian→방향별 pre-tanh residual cap
- [`config.py`](../../action_residual/config.py): 입력 encoder와 hidden 크기
- [`goal_encoder.py`](../../action_residual/goal_encoder.py): 현재+다음 3 event의 categorical embedding과 128D Goal context
- [`context_encoding.py`](../../action_residual/context_encoding.py): Readiness·Joint·Guitar·Privileged field manifest와 fixed-scale packer
- [`context_pipeline.py`](../../action_residual/context_pipeline.py): 75D 관절 layout에 packer를 묶고 통합 schema hash를 만드는 상위 API
- [`ARCHITECTURE.md`](ARCHITECTURE.md): 데이터 흐름과 학습 규칙
- [`ENCODING_SPEC.md`](ENCODING_SPEC.md): 각 입력 field, offset, 좌표계, 정규화, valid mask와 critic 정보의 상세 명세
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md): encoding부터 G0 Full runtime, free guitar, tether 제거까지의 구현 순서와 완료 조건
- [`diagrams/action_residual_architecture.png`](../../action_residual/diagrams/action_residual_architecture.png): 상세 구조 그림
- [`tests/run_all.py`](../../action_residual/tests/run_all.py): pytest 없이 전체 계약 테스트 실행

검증:

```bash
python full/action_residual/tests/run_all.py
```

최소 호출 흐름은 `FrozenSourcePolicyAdapter → SourceProposal → ActionResidualCoordinator → distribution()`이다. source adapter에서 나온 `mean`은 tanh 전 값이며, joint distribution이 75D를 한 번 sample한 뒤에만 tanh를 적용한다.

## 아직 남은 연결 작업

I0 순수 tensor 계층은 구현했다. 다음 작업은 같은 곡 source checkpoint와 goal timeline hash 선정, 실제 simulator 신호를 typed context 입력으로 변환하는 adapter, 실제 joint limit을 포함한 context-pipeline hash의 Full checkpoint binding, `task_full.py`의 75D PD target mapping, pre-tanh latent·`policy_action`·`executed_action`을 분리하는 Full 전용 PPO wrapper, 고정 기타 G0 baseline 순서다. 현재 공용 `PPOTrainer`에 그대로 꽂을 수 있다고 간주하면 안 된다.
