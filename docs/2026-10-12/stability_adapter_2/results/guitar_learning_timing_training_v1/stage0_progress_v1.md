# Stage0 학습 경과 분석

중간 스냅샷 — 최종 평가 전 결론을 내리지 않는다.

| 손 | 완료 update | 커밋 전이 | 학습 episode 성공 | KL retry 합계 | 실제 LR 최소 | 실제 LR 최대 |
|---|---:|---:|---:|---:|---:|---:|
| left | 4 | 2400 | 8/8 | 2 | 6.25e-07 | 6.25e-07 |
| right | 4 | 2400 | 8/8 | 1 | 2.5e-06 | 2.5e-06 |

설정 LR와 실제 적용 LR, accepted/attempted KL, reward/cost critic loss는 그래프와 JSON에 각각 기록했다. 학습 로그의 완료 episode는 확률적 행동의 결과이며 별도의 결정적 native 평가와 구분한다.

왼손은 원 audible 구간의 유지율·연속 유지와 확장 시간창의 긴 유지 보상을 분리했다. 전체 hold 보상 중 audible 성분은 held_second×audible_valid_s이고, 나머지는 audible 밖의 유지 보상이다. pre/post 전용60Hz tick 보상과 경계 tick도 따로 기록했다. 보상이 늘어도 audible 유지율이 이미1이면 정밀 수행 개선으로 단정하지 않는다.

오른손은 최초 목표 down의 signed/absolute error와 후속 최소 오차, 추가 down/up 및 불필요 crossing을 구분했다. 원래 contact-conditioned joint music50/100ms 기록도 유지했다.

학습 중 안전 수치는60Hz endpoint 집계이며240Hz 내부 최대를 대신하지 않는다. 최종 native 평가는 별도로 저장된1,200개240Hz 표본에서 기타·발 최대 편차, 접촉, 비용, 깊이·속도와 시계 연속성을 재집계한다.

left: 최종 native 평가 자료가 아직 없다.

right: 최종 native 평가 자료가 아직 없다.

전체 수치·입력 byte 스냅샷 SHA: [stage0_progress_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_progress_v1.json)
학습 지표: ![KL·LR·critic](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_progress_v1.png)
