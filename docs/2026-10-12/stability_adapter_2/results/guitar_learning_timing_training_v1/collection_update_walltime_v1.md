# 수집과 PPO update 시간

수집 시간은 시뮬레이션·정책 추론·통신을 포함한다. 아래 비율의 분모는 로그의 collection_s+update_s이며 전체 실행시간이나 순수 물리 계산 비율이 아니다. 양손 병렬 실행의 시간을 합산해 실제 경과시간으로 해석하지 않는다.

| 실행 | update | 전이 | 수집 합계(s) | update 합계(s) | 수집 비율 | 수집 평균(s/update) |
|---|---:|---:|---:|---:|---:|---:|
| left_stage0_v1 | 24 | 14400 | 1889.243 | 2.007 | 99.8939% | 78.718 |
| right_stage0_v1 | 24 | 14400 | 1881.220 | 2.041 | 99.8916% | 78.384 |
| left_stage1_v1 | 12 | 7200 | 942.209 | 1.091 | 99.8844% | 78.517 |
| right_stage1_v1 | 12 | 7200 | 934.452 | 1.082 | 99.8843% | 77.871 |

학습 전이 합계: 43200. 수집/통신/추론의 구체적인 병목 분해는 별도 프로파일이 필요하다.

[원수치와 입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/collection_update_walltime_v1.json)
