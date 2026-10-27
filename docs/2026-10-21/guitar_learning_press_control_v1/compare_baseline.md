# 동일100회 예산 비교

이전 누적 제어와 새 압현면·감속 보상의 실제100회 학습 수집 및 고정0/100 평가다. 근접/거리 목표와 보상은 달라 평균 우열로 비교하지 않는다.

| 고정 정책 | 이전 안전/1024 | 새 안전/1024 | 이전 전체 달성/67 | 새 전체 달성/67 | 공통 안전 ID 수 |
| --- | ---: | ---: | ---: | ---: | ---: |
| initial | 1023 | 1024 | 4.200195 | 3.804688 | 1023 |
| final | 311 | 1021 | 0.977539 | 0.000000 | 311 |

안전 전곡·공통 안전ID의 별도 분모, 손가락별 달성 합계/접촉, clean 시간, 물리실패 사유·길이, 단계와 LH21 움직임 원자료 요약은 JSON을 따른다. 같은 안전ID도 독립 seed나 같은 궤적은 아니다.

| 학습 수집100회 | 이전 | 새 |
| --- | ---: | ---: |
| 종료 곡 | 1181 | 1222 |
| 안전 완주 | 913 | 785 |
| 물리실패 | 268 | 437 |
| 종료곡 평균 달성 | 2.0025402201524134 | 1.4378068739770868 |

수집은 각3,276,800전이이며 계속 변하는 확률 정책이다. 반복 곡과 실패 후 재시작을 포함하고 진행 중 곡은 종료 분모에서 제외한다. 고정 정책 결과를 수집 평균으로 대체하지 않는다.

옛 활성 경로의 소스가 현재와 다른 것은 예상된 변경이다. 이전 결과는 지정 SHA의 봉인 manifest와 source_training 사본으로 검증했으며 옛 소스는 실행하지 않았다. 새 입력과 동결435소스는 실제 SHA를 검증했다. 제어·scene·기하·PPO·policy·native gain 소스가 동일하다.

- Old and new near/surface_min use wire versus physical press-plane targets: no comparable improvement delta.
- Reward adds tracking and changes geometry: do not rank average rewards as equivalent objectives.
- Curriculum progress is recorded state; its near gate now uses a different physical target, not an equivalent achievement scale.
- Existing contact/clean/success and safety contracts agree; candidate success is not pressure or audible sound.
- Same seed/song/prepared pose, correlated IDs, different safe cohorts; matched IDs are descriptive, not randomized causal proof.
- PPO collections contain changing stochastic policies; fixed evaluations use deterministic0/100 checkpoints. No absolute-control2000 score8.301 comparison.
- Equal-episode motion ranges differ with episode duration, include t0 and sample60Hz; no240Hz extrema claim.
