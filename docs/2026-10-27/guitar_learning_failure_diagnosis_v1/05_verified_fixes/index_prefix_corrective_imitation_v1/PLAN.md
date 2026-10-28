# 저장된 NN 관측의 교정 명령을 이용한 자료 보강 비교

작성일: 2026-10-28. 상태: root 승인으로 최소 CPU 준비 구현 중·GPU 실행 전. warmstart actual 독립 검수는 완료했다.

## 질문과 변경 하나

참고 요청을1000회 지도학습한 NN은 원128평가에서 세 음91/128·A해제67/128로 개선됐지만90% 기준에 미달했다. 사전지정4환경에는 참고 궤적 밖의 누적 목표오차가 남았다. 저장 preclock/oldtarget4로 원 reference_action을 CPU에서 다시 호출하면 원참고1416행 요청을 bit-exact 재현할 수 있다는 분석을 독립 검수한다.

보상·codec·범위·속도·물리·std는 유지한다. 같은 NN에서 같은1000회를 더 학습하는 두 조건을 비교해 **학습 자료 보강 효과와 추가 최적화 횟수 효과**를 구분한다. 원자료·실패collect exit1·회복 수용·원model은 보존한다. 새 물리 자료 수집은 없다.

## 1. 실제 원 함수로 교정 label 만들기 → 검증

- 기존 reference 수집과 NN-only 평가의 env0..3 제어 직전 관측·clock·oldtarget4를 사용한다. 요청 끝점 시간 t+1/60과 원 reference/N 시간표를 보존한다.
- 원 reference_action/trajectory_actions를 CPU에서 호출해 참고 자료의 **실제 요청4열**과 bit-exact 일치를 먼저 요구한다. 임의 새 FK·근사 제어기·손가락 범위·N각도를 만들지 않는다.
- NN 자료에는 그 상태에서 원 참고 제어가 요청했을 **counterfactual 교정 명령**을 별도 label로 저장한다. NN의 실제 요청·실행·원 guard와 섞지 않는다. 교정 label을 실제로 물리에 적용해 검증했다고 말하지 않는다.
- 원자료 출처/condition/그 시점 실제 행동/교정 label·생성함수와 SHA를 구별한다. 초기 train은 env0/1/2, env3은 같은 장면의 미사용 관측 검산이다. 독립seed나 일반화 검증은 아니다.
- native candidate는 원 guard가 유지한다. 일부 교정 양의 DIP 요청이 guard에 막힐 수 있음을 기록한다. label을 사후 강제로0으로 바꾸지 않는다.

## 2. 동일 추가 예산의 두 조건 → 검증

출발 모델은 warmstart recovery의 initial.pt(SHA162c617a28e548757bea8b0721c13c740d452fc430ae1601f01ed8411e2e480a)이다. 원 strict identity load를 사용하고 원 PPO optimizer·critic·std를 위장 초기화하지 않는다. 두 조건 모두 새 supervised Adam으로1000회, lr3e-4, batch192, seed7, gradient norm.5, 기존6구간 동등 비중을 쓴다. finger_encoder와indexhead만 학습하고 나머지 state/critic/std/head 파라미터는 출발 모델과 exact여야 한다.

| 조건 | 각 구간32행 | 원인 분리 |
|---|---|---|
| reference_only | 기존 참고 요청32행 | 같은 추가1000회 효과 |
| corrective_mixed | 기존 참고16행+저장NN상태의 교정label16행 | 자료 보강 효과 |

각 조건은 최종 모델 한 개만 저장한다.1000회/192표본 반복과 PPO 반복은 구분하며, 원모델의 이전1000회 이력도 기록한다. 새 metadata/schema/provenance에 자료·누적 지도학습2000회·새PPOempty/updates0을 명시한다. 원 PrefixPolicy와 환경의 실제 구조/의미는 같다. 각 구간 같은16+16 추출 형태의 추출 난수 소비를 맞출 수 있으면 유지하되, 물리/시드 전체 동일성을 과장하지 않는다.

CPU 검증은 실제 label 재현·출처 분리·6구간/학습분할·배치·loss4열·허용 파라미터·기타 state exact·새PPOempty0·metadata·strictload·scope복원/종료/출력보호에 한정한다. 기존 검증을 전부 재작성하지 않는다.

## 3. NN-only128 두 조건 → 판정

- root가 두fit와 두evaluation을 GPU에서 직렬 실행한다. 원 current-goal guard/고정기타/유한손목/비선택B/원9항/범위/속도/std/128cap·충돌을 유지한다. 첫 tick부터 선택4축은 NN이며 N/참고 목표 주입0이다.
- 원각음 달성·clean≥90%, wrong≤10%, 전체≥90%, A해제≥90%, 물리/손목실패0 기준을 바꾸지 않는다. all3와 A해제 교차값 및 Aachieved/ever를 구분하고 미저장240Hz 해제 사건을 추정하지 않는다.
- 원128 원장/9항·새4환경 사전관측/NN요청·관절·누적목표·원 guard·거리/방향·하중·손목을 필요한 범위로 보존한다. old evaluation을 새 조건 성과로 합치지 않는다.
- mixed만 통과하면 저장NN 관측 보강이 기여한 근거다. 둘다 통과하면 추가 최적화만의 가능성도 남고 단순한reference_only를 우선한다. 둘다 미달이면 예산을 자동 확장하거나 기준을 내리지 않는다. 보상 escrow·position codec·std 변경을 이 비교에 섞지 않는다.
- 통과한 경우에만 다음100PPO/50·100평가 유지 검사를 별도로 진행한다. 이 비교는 RL만의 학습·자유기타/J33·다른목표/seed·67음 성능을 뜻하지 않는다.

## 체크리스트

- [x] warmstart actual/교정 label 근거 독립검수 완료
- [ ] 최소 CPU 구현·검사·change-reviewer 독립검수
- [ ] 원참고 bit-exact label 재현·저장NN 교정label/출처 검증
- [ ] 추가1000회 두조건·NN-only128 두조건 실제 검증
- [ ] 실제 결과·한계/그림·독립검수와 다음100PPO 여부 결정

영상은 이미별도준비중인 warmstart91/128 모델과 후속모델을 혼동하지 않는다. 저장공간 정리 중지와 진단/기준자료 보호는 계속 유지한다.
