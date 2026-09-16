# 양손 병합 계약

> 상태: **SUPERSEDED**
>
> 이 문서의 기존 learned pre-tanh Sync correction과 one-joint-sample 초안은 현재 G0
> rule-based 구조에 적용하지 않는다. 현재 규범은
> [`master_plan/05_synchronizer.md`](../../master_plan/05_synchronizer.md),
> [`master_plan/08_shared_contracts.md`](../../master_plan/08_shared_contracts.md)와
> `tab2body/full/runtime.py`다.

현재 G0 병합 규칙은 다음과 같다.

1. 같은 곡의 Fret-v2 30D와 Strike-v2 30D checkpoint를 strict contract/hash 검증 후 동결한다.
2. 두 actor가 보는 Synchronizer 입력은 학습 때와 같은 `(1, 0)`으로 유지한다.
3. Rule-based Synchronizer가 actor 밖에서 readiness permission, bounded delay, hold와 skip/partial을 결정한다.
4. 두 source action은 평균내지 않고 관절 이름으로 external 105D ABI에 scatter한다.
5. G0의 source-active slot은 60개이며 나머지 45개는 명시적 seated-hold action을 유지한다.
6. 하나의 향후 `FullG0Task`가 common EMA/PD와 physics step을 각각 한 번만 수행하고, 그 실제 실행 action을 다음 source history로 되돌린다.
7. event cursor와 score clock은 각각 하나뿐이며 event 결과는 정확히 한 번 resolve한다.

현재 구현은 CPU contract/runtime integration까지다. 별도 FretTask와 StrikeTask simulator를
나란히 실행하는 것은 하나의 물리 시스템 병합으로 인정하지 않는다.
