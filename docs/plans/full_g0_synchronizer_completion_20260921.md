# Full G0 Synchronizer 완성 계획

> 작성일: 2026-09-21  
> 상태: 1차 물리 진단 완료 · gate 실패 후속 구현 필요  
> 대상: 고정 기타 G0에서 Fret·Strike checkpoint를 하나의 Isaac Gym 환경으로 결합

## 목표

현재 CPU 계약으로 구현된 Rule Synchronizer를 실제 한 개의 humanoid·기타 물리 환경에 연결한다.
동일한 물리 프레임에서 왼손 readiness, 오른손 readiness, 줄 crossing을 계산하고, 타현 허가와
hold가 실제 관절 명령에 반영되는지 검증한다. 마지막으로 지정된 Fret·Strike checkpoint의
deterministic rollout 영상과 지표를 저장한다.

## 범위와 전제

- 이번 구현은 기타가 월드에 고정된 `G0`만 대상으로 한다.
- Rule Synchronizer는 계속 비학습 timing supervisor로 유지한다.
- Fret와 Strike actor는 동결하며 원래 관측·action 후처리 계약을 보존한다.
- StabilityAdapter 학습과 고정 해제 G1/G2는 이번 영상의 범위에 포함하지 않는다.
- 기준 checkpoint는 다음으로 고정한다.
  - Fret: `fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt`
  - Strike: `strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt`
- 영상은 실제 Isaac Gym 물리 rollout만 결과로 인정한다. CPU tensor preview를 물리 결과처럼
  대체하지 않는다.

## 구현 단계와 검증 기준

### 1. 단일 simulator `FullG0Task`

- [x] `GuitarEnvBase` 하나만 생성한다.
- [x] 동일 humanoid에서 Fret 30D와 Strike 30D를 named 105D action에 병합한다.
- [x] 나머지 관절 45D는 명시적 seated hold를 사용한다.
- [x] 한 control frame에 common EMA, PD target 계산, physics step을 각각 한 번만 수행한다.
- [x] post-physics 상태에서 readiness와 crossing을 계산한다.

검증:

- actor와 simulator 수를 assert한다.
- step counter로 frame당 physics step이 한 번임을 검사한다.
- 실제 post-EMA 105D action이 다음 Fret·Strike history에 들어가는지 검사한다.

### 2. Source 관측 및 후처리 parity

- [x] 기존 `FretTask`의 Fret-v2 420D 관측을 동일 상태에서 생성한다.
- [x] 기존 `StrikeTask`의 Strike-v2 303D 관측을 동일 상태에서 생성한다.
- [x] Fret adjacent-finger synergy를 공통 EMA 전에 적용한다.
- [x] Strike pick-grip constraint를 공통 EMA 전에 적용한다.
- [x] frozen actor가 보는 Synchronizer 2D block은 학습 분포대로 `(1, 0)`을 유지한다.
- [x] Strike native timing field에만 rule delay를 반영한다.

검증:

- standalone task와 Full task를 같은 초기 상태·goal·action으로 한 프레임 실행한다.
- 관측 block별 차이와 postprocessor 출력 차이를 저장한다.
- 계약상 동일해야 하는 값은 허용 오차 이내가 아니면 실행을 중단한다.

### 3. Current-pose hold와 물리 release gate

- [x] Strike entry readiness가 확인된 뒤 permission이 닫혀 있으면 현재 자세를 유지한다.
- [x] 현재 관절 각도에서 normalized pre-EMA action을 역산한다.
- [x] common EMA를 통과한 PD target이 현재 자세가 되도록 첫 hold frame을 보정한다.
- [ ] permission이 닫힌 상태의 실제 줄 crossing은 차단 또는 안전 후퇴 명령을 적용한다.
- [x] 관성으로 발생한 closed crossing은 숨기지 않고 contract violation으로 기록한다.
- [ ] Fret은 준비되지 않았을 때 계속 움직이고, 준비된 뒤 Strike를 기다릴 때만 유지한다.

검증:

- hold 진입 전후 오른손 target jump, 관절 속도, entry-plane 침범량을 기록한다.
- closed permission에서 accepted crossing이 0인지 검사한다.
- blocked crossing이 발생하면 G0 합격을 실패시킨다.

### 4. 결합 충돌 및 안정성 감사

- [x] 기존 humanoid↔guitar 충돌 필터와 contact offset을 보존한다.
- [ ] 양손 동시 실행에서 왼손·오른손·기타의 비정상 관통을 기록한다.
- [x] G0의 `guitar_stable`은 고정 상태 certificate로 명시적으로 생성한다.
- [ ] 향후 G1을 위해 permission open 이후 traversal 중 안정성 손실 지표를 추가한다.

검증:

- NaN, 관절 속도 blow-up, 관절 한계 초과, 비정상 관통이 없어야 한다.
- Fret/Strike standalone 성공 사건의 결합 retention을 별도 집계한다.

### 5. 평가와 영상

- [x] 1-env 짧은 physical smoke를 실행한다.
- [x] 실패 시 frame별 sync trace와 관절·readiness·crossing 진단 JSON을 저장한다.
- [ ] smoke 통과 후 deterministic 곡 rollout을 실행한다.
- [ ] 영상에 event id, score frame, Fret ready, Strike ready, permission, delay, outcome을 표시한다.
- [x] MP4와 대응 JSON summary를 `docs/2026-09-21/synchronizer/full_g0/`에 저장한다.

최소 보고 지표:

- full / partial / missed event 수
- on-time / delayed-by-fret / delayed-by-strike / delayed-by-both
- blocked / unplanned / wrong-direction / order-violation crossing
- `strike_time - fret_ready_time`
- Fret 및 Strike standalone-success retention
- 최대 관절 속도와 관절 한계 margin

### 6. 회귀 검사와 문서 갱신

- [x] CPU Synchronizer 기존 테스트를 유지한다.
- [x] FullG0Task transaction, shared view, hold, name mapping 테스트를 추가한다.
- [x] 실행 명령과 산출물 경로를 문서화한다.
- [x] 구현 체크리스트에서 실제로 검증된 항목만 완료 표시한다.
- [ ] 변경 사항을 별도 검수한다.

## 중단 조건

다음 경우 영상을 성공 결과로 저장하지 않고 진단 산출물만 남긴다.

- CUDA 또는 Isaac Gym 물리 실행이 불가능함
- source checkpoint strict-load 또는 관측 parity 실패
- closed permission에서 물리 crossing 발생
- 원본 standalone task에서 성공하지 못하는 checkpoint 사건만으로 결합 결과를 평가하게 됨
- NaN, 관절 폭주 또는 충돌 계약 위반 발생

## 완료 정의

다음을 모두 만족할 때 이번 작업을 완료로 본다.

1. 실제 single-simulator `FullG0Task`가 지정 checkpoint 쌍을 strict-load한다.
2. 동일 프레임의 물리 상태로 양손 관측과 detector를 계산한다.
3. current-pose hold와 closed release gate가 물리 rollout에서 검증된다.
4. deterministic MP4, sync trace JSON, summary JSON이 함께 저장된다.
5. 실행 명령과 알려진 한계가 문서에 기록된다.
