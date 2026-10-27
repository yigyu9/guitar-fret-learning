# Fret-v2 물리 압현

현재 Fret 물리 환경의 계약은 [`master_plan/03_fret.md`](../../master_plan/03_fret.md)와 [`03_training/README.md`](../03_training/README.md)를 기준으로 한다.

- 제어: 30 action
- 관측: 420D named-block observation
- 보상/value: 6 / 6
- 현재 태스크: 월드에 고정된 기타에서 지정 손가락으로 PRESS·NO_PRESS·DONT_CARE goal을 수행
- 현재 정책: block encoder actor-critic, bounded action, EMA, 명시적 checkpoint contract

실행 명령과 재개·평가는 [`tab2body/TRAINING.md`](../../tab2body/TRAINING.md)를 따른다. 이전 425D Fret-v1의 상세 규칙과 구현 근거는 [`../archive/FRET_V1_PHYSICAL_CONTROL.md`](../archive/FRET_V1_PHYSICAL_CONTROL.md)에 보존되어 있으며 현재 Fret-v2 계약으로 사용하지 않는다.
