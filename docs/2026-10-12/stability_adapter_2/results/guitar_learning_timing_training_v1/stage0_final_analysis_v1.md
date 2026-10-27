# Stage0 학습 경과 분석

최종 분석

| 손 | 완료 update | 커밋 전이 | 학습 episode 성공 | KL retry 합계 | 실제 LR 최소 | 실제 LR 최대 |
|---|---:|---:|---:|---:|---:|---:|
| left | 24 | 14400 | 46/48 | 2 | 6.25e-07 | 6.25e-07 |
| right | 24 | 14400 | 48/48 | 2 | 6.25e-07 | 2.5e-06 |

설정 LR와 실제 적용 LR, accepted/attempted KL, reward/cost critic loss는 그래프와 JSON에 각각 기록했다. 학습 로그의 완료 episode는 확률적 행동의 결과이며 별도의 결정적 native 평가와 구분한다.

왼손은 원 audible 구간의 유지율·연속 유지와 확장 시간창의 긴 유지 보상을 분리했다. 전체 hold 보상 중 audible 성분은 held_second×audible_valid_s이고, 나머지는 audible 밖의 유지 보상이다. pre/post 전용60Hz tick 보상과 경계 tick도 따로 기록했다. 보상이 늘어도 audible 유지율이 이미1이면 정밀 수행 개선으로 단정하지 않는다.

오른손은 최초 목표 down의 signed/absolute error와 후속 최소 오차, 추가 down/up 및 불필요 crossing을 구분했다. 원래 contact-conditioned joint music50/100ms 기록도 유지했다.

학습 중 안전 수치는60Hz endpoint 집계이며240Hz 내부 최대를 대신하지 않는다. 최종 native 평가는 별도로 저장된1,200개240Hz 표본에서 기타·발 최대 편차, 접촉, 비용, 깊이·속도와 시계 연속성을 재집계한다.

left: native 평가 기록 — 평가모델 24 updates / 동시 학습로그 스냅샷 24 updates

| 회차 | 성공 | 첫 목표 down 오차(ms) | best 오차(ms) | audible 유지율 | 불필요 crossing | 기타 최대 이동(mm) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | True | None | None | 1.000000 | 0 | 5.500400 |
| 2 | True | None | None | 1.000000 | 0 | 5.747094 |

right: native 평가 기록 — 평가모델 24 updates / 동시 학습로그 스냅샷 24 updates

| 회차 | 성공 | 첫 목표 down 오차(ms) | best 오차(ms) | audible 유지율 | 불필요 crossing | 기타 최대 이동(mm) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | True | 17.680343990953418 | 17.680343990953418 | 0.000000 | 1 | 0.222710 |
| 2 | True | 17.680343990953418 | 17.680343990953418 | 0.000000 | 1 | 0.222710 |

단계1 이전 사전평가 진입 조건: **통과**. 각 손2회 안전 단계성공, 왼손 각 audible coverage≥.95, 오른손 각 최초 목표 down의 절대오차≤.5초를 확인했다. 이는 단계1의 이전 평가를 시작할 근거이며 단계1 성공을 인증하지 않는다.

초기 BC 대비 기술적 변화

| 손 | 초기 BC | 평가 모델 | 해석 범위 |
|---|---:|---:|---|
| left audible coverage 평균 | 1.000000 | 1.000000 | 원 음 구간 수행과 긴 창 유지 보상을 구분 |
| right 최초 down 절대오차 평균(ms) | 19.449144 | 17.680344 | 동일 시작2회 기술적 비교; 일반화·통계적 개선 증거 아님 |
| right 추가 목표 down 평균 | 1.000 | 1.000 | 불필요 동작 억제 여부 |

왼손 학습 episode에서 hold 보상의 audible 밖 성분 비율 평균은 91.156%다. 이 보상 증가는 이미1인 audible coverage의 개선과 같지 않다.

left 학습 rollout: timing 성공 46/48, 물리 실패0, retry 총2. 실제 actor LR 범위6.25e-07~6.25e-07(설정1e-05)다. Accepted KL이 예산 안에 있더라도 큰 시도 KL 때문에 실제 학습률이 감소했는지를 함께 봐야 한다.

right 학습 rollout: timing 성공 48/48, 물리 실패0, retry 총2. 실제 actor LR 범위6.25e-07~2.5e-06(설정1e-05)다. Accepted KL이 예산 안에 있더라도 큰 시도 KL 때문에 실제 학습률이 감소했는지를 함께 봐야 한다.

전체 수치·입력 byte 스냅샷 SHA: [stage0_final_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_final_analysis_v1.json)
학습 지표: ![KL·LR·critic](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_final_analysis_v1.png)
