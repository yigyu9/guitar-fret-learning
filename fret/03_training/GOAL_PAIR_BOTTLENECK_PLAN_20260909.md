# Goal-pair 병목 진단 및 개선 계획 (2026-09-09)

## 현재 판단

실행 중인 `20260909_0822_02_Jazz1-200-B_solo`는 mixed level 0에서 회복 중이다. 전역 F1은 약 0.93이지만 조건부 지표에서는 다음 병목이 확인된다.

- 소지 next-target evidence 426/1024, 거리 8.79 cm/허용 5 cm
- 기존 압현 보존 품질 0.731/최종 요구 0.90
- 전환 압현 성공: 검지 0.683, 중지 0.727, 약지 0.344/최종 요구 0.80
- finger signature 9(검지+소지): 950 frame, 성공 0, 거리 2.36 cm
- full-song 성공은 검지 0.978, 중지 0.568, 약지 0.861, 소지 0.526으로 불균형

## A. 현재 실행 중 적용

학습 코드와 reward는 수정하지 않는다. 실행 도중 source를 바꾸면 이후 checkpoint의 구현 fingerprint와 실제 메모리에서 실행된 코드가 달라질 수 있기 때문이다.

`tab2body.tools.diagnose_fret_goal_pair`를 사용해 다음을 자동 판정한다.

1. 현재 stage/phase/level/recovery/rollback이 같은 suffix만 선택
2. 손가락별 rehearsal, transition, full-song 결과를 evidence count로 가중
3. current-level gate와 final-promotion gate를 분리
4. 전역 F1에 가려지는 희귀 finger/chord를 경고
5. append 중인 마지막 JSON line이 불완전하면 안전하게 제외

500 iteration 간격으로 진단 결과를 갱신한다. 다음 조건이 한 phase window 동안 지속될 때만 다음 실행의 샘플링 또는 reward를 변경한다.

- 손가락별 evidence가 1024 이상인데도 current-level gate 실패
- pretransition preservation quality가 두 창 연속 0.80 미만
- signature 9 evidence가 1024 이상인데 성공률 0.20 미만
- mixed F1이 0.95 미만이고 weakest full-song finger가 0.60 미만

## B. 현재 실행 종료 후 추가할 계측

1. transition group ID별 count/success/next-distance를 기록한다.
2. incoming finger뿐 아니라 outgoing-held finger별 preservation quality를 기록한다.
3. sampler가 요청한 focus 비율과 실제 pretransition evidence 비율을 함께 기록한다.
4. shape signature 9를 실제 `(previous frame, next frame, string, fret, finger)` 목록으로 분해한다.
5. phase 전환 전후 value loss와 explained variance를 별도 기록한다.

## C. 계측 후 허용할 개선

- evidence 부족이면 해당 incoming transition group의 sampling quota만 높인다.
- evidence가 충분하지만 next distance가 크면 해당 group의 preview lead와 next-goal shaping을 조정한다.
- outgoing press가 먼저 풀리면 이미 존재하는 preservation-conditioned reward의 가중치를 제한적으로 높인다.
- signature 9가 특정 한두 자세에 집중되면 전체 chord reward를 바꾸지 않고 해당 자세의 짧은 rehearsal cohort를 추가한다.
- 각 변경은 한 번에 하나씩 적용하고, F1뿐 아니라 기존 세 손가락 retention과 wrong press를 함께 비교한다.

## 통과 기준

- current mixed level: 모든 손가락 evidence 충족, next distance와 full-song gate 통과
- final goal-pair: pretransition preservation ≥ 0.90
- 손가락별 transition success ≥ 0.80
- 손가락별 full-song press success ≥ 0.50
- wrong press ≤ 0.06
- sequence press ≥ 0.75, no-press ≥ 0.90
- 두 연속 평가 창에서 통과하고 이미 mastered된 손가락 하락이 0.05 이내

