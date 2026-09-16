# Full: Fret·Strike 병합

> 현재 상태: 고정 기타 G0의 offline canonical event compiler, rule-based Synchronizer,
> frozen Fret/Strike strict loader, 105D named action bridge와 CPU integration probe까지 구현.
> 하나의 Isaac Gym simulator에서 두 native observation/detector를 계산하는 physical
> `FullG0Task` backend는 다음 구현 단계다.

현재 정본 action ABI는 105D(실질 가동 관절 97D, zero-range fixed hold 8D)이며, G0에서는 Fret 30D와 Strike 30D만 source-active이고
Thorax/body·lower body·Neck/Head의 나머지 45D는 명시적 seated hold로 유지한다.
`full/action_residual/`의 과거 75D/no-gaze coordinator는 비교용 독립 프로토타입이며 현재
rule-based G0 Synchronizer 구현으로 사용하지 않는다.

실제 실행 코드는 `tab2body/`에 둔다. 전체 연구 설계의 정본은 [`master_plan`](../master_plan/README.md)이며,
이 디렉터리는 Full 결합의 구현 상태와 과거 구조 비교를 보존한다.

## 작업 구역

- `01_goal_contract/`: 공통 이벤트와 양손 동기화 계약
- `archive/02_architecture/`: 현재 구조를 선택하기 전 검토한 역사적 후보
- `03_implementation/`: 구현 순서와 진행 상태
- `04_training/`: 커리큘럼, checkpoint 계약, 실행 기록
- `05_evaluation/`: 공동 성공 지표와 합격 기준
- `90_references/`: GPS·SDH 등 참고 연구
- `action_residual/`: 75D/no-gaze 과거 prototype 코드
- `archive/action_residual/`: 해당 prototype의 역사 문서
- `latent_sync/`: 향후 latent 보정안을 구현할 별도 위치(현재 미생성)

## 현재 문서

- [`03_implementation/README.md`](03_implementation/README.md): 현재 G0 rule Synchronizer 구현
- [`03_implementation/STATUS.md`](03_implementation/STATUS.md): 구현·미구현 경계
- [`01_goal_contract/EVENT_TIMELINE.md`](01_goal_contract/EVENT_TIMELINE.md): Canonical PlayEvent 계약
- [`04_training/CHECKPOINT_CONTRACT.md`](04_training/CHECKPOINT_CONTRACT.md): G0/G1/G2 checkpoint 계약
- [`05_evaluation/JOINT_METRICS.md`](05_evaluation/JOINT_METRICS.md): 양손 공동 평가 지표

`archive/SYSTEM_DESIGN_OVERVIEW.md`, `archive/02_architecture/`, `archive/action_residual/`의 문서는 현재 105D·rule supervisor
구조를 확정하기 전의 비교·prototype 기록이다. 문서 첫머리의 `SUPERSEDED` 안내를 따른다.

## 실제 코드 위치

독립 구조 프로토타입:

- `full/action_residual/`

현재 G0 계약 코드와 향후 물리 backend 위치:

- `tab2body/env/tasks/task_full.py`
- `tab2body/full/`
- `tab2body/train_full.py`
- `tab2body/tests/test_full_contract.py`
