# BC 초기화 이후 PPO 학습 기록

**두 실행의 report.json 기록까지 확정 집계**했습니다.

집계 기준은 첫 음표 고정, 양손 독립 기술(left/hold·right/cross), 준비 2초·기술 4초, 환경 2개·수집 길이 240입니다. BC actor에서 출발했으며, 학습 중의 확률적 episode 성공률과 별도 결정적 모델 검증은 구분합니다.

| 구분 | 왼손 hold | 오른손 cross |
|---|---:|---:|
| 기록 상태 | updates_complete | updates_complete |
| 완료된 PPO update | 24/24 | 24/24 |
| optimizer 반영 transition | 11520 | 11520 |
| 미반영 로그 transition | 0 | 0 |
| 기술 성공/완료 episode | 48/48 | 48/48 |
| 물리 실패 episode | 0 | 0 |
| 음악 strict 50ms 매칭 | 0 | 0 |
| 음악 목표음 유지 합(s) | 11.068933 | 0.000000 |
| 수용된 KL 최대 | 0.007025725673884153 | 0.01789822056889534 |
| 거절 시도 포함 KL 최대 | 0.7545285224914551 | 0.06413312256336212 |
| KL guard 총 재시도 | 2 | 1 |
| 초기 actor learning rate | 1e-05 | 1e-05 |
| 마지막 실효 actor learning rate | 6.25e-07 | 2.5e-06 |
| 전체 지지 끝점(%) | 100.0 | 100.0 |
| 삼중 동시 지지 끝점(%) | 7.430555555555555 | 99.93055555555556 |
| 양발 접지 끝점(%) | 100.0 | 100.0 |
| 실제 wall time(s) | 1585.2355757619953 | 1581.7938035970437 |
| wall 예산(s) | 1800 | 1800 |
| 사용 가능 RAM 최소(GiB) | 24.442707061767578 | 24.45977020263672 |

## BC fit와 PPO 앞·뒤 구간 비교

BC 수치는 단일 시범 trajectory의 action training fit입니다. 정한 수치 tolerance 달성 여부를 별도로 기록하며, native 기술 성공·수렴·일반화와 동일하지 않습니다.

| BC 항목 | 왼손 | 오른손 |
|---|---:|---:|
| fit step | 2000 | 2000 |
| 초기 training MSE | 0.15290290117263794 | 0.13634787499904633 |
| 최종 training MSE | 2.4802362531772815e-05 | 5.431588942883536e-05 |
| 최대 action 오차 | 0.23446300625801086 | 0.11396244168281555 |
| 수치 tolerance 도달 | False | False |
| tolerance | 1e-06 | 1e-06 |

| PPO 확률적 학습 구간 | 성공/episode | 평균 reward | 평균 cost | longest dwell 평균(s) |
|---|---:|---:|---:|---:|
| left first_up_to4_updates | 8/8 | 7.004138933398327 | 0.1746730798235247 | 2.877083333333374 |
| left last_up_to4_updates | 8/8 | 7.304138956745454 | 0.17463302146196735 | 3.0083333333333777 |
| right first_up_to4_updates | 8/8 | 1.6621738577868999 | 0.0009360206927797526 | 0.0 |
| right last_up_to4_updates | 8/8 | 1.7068089244793367 | 0.0023908645305470906 | 0.0 |

앞·뒤 구간은 서로 다른 확률적 episode입니다. reward나 fit의 차이만으로 BC 대비 향상 또는 최종 정책의 검증 완료를 주장하지 않습니다.

## 지지·접지와 기술의 증거 범위

아래 최대값과 접촉 비율은 optimizer에 반영된 transition의 60Hz 끝점 기록입니다. 실제 실패 검사는 기존 240Hz 경로에 남아 있습니다. 연속 dwell·기하 타현 건수는 episode에 저장된 240Hz 원래 측정 ledger 집계이며, 끝점 비율을 모든 물리 순간의 접촉 비율로 확대하지 않습니다.

- **left**: 기타 변위 최대 0.005291466088175012m, 회전 최대 0.017356049637546386rad, 발 변위 최대 0.002923983616695877m, 관절 속도 최대 0.3523387014865875rad/s. 접촉 끝점 비율 `{'any_main_support': 1.0, 'triple_support': 0.07430555555555556, 'chest': 0.07430555555555556, 'right_upper_arm': 0.9995659722222222, 'thigh': 1.0, 'both_feet': 1.0, 'left_foot': 1.0, 'right_foot': 1.0, 'target_fret_candidate': 0.7178819444444444}`. 최장 연속 목표 후보 dwell 3.2166666666667214s, episode별 longest dwell 분포(s) `{'count': 48, 'minimum': 1.6374999999999955, 'median': 3.0354166666667126, 'mean': 2.8357638888889256, 'population_std': 0.44742207297046765, 'maximum': 3.2166666666667214}`. 방향·줄 일치 기하 타현 0회. 회계 일치 `True`, 실행 완료 `True`.
  - 물리 회계: 과제 측정 46080 step, 준비 24000 step, 합계 70080 step. 에피소드 초기화 50회, simulator 생성/종료 2/2회.
- **right**: 기타 변위 최대 0.0009023800032094958m, 회전 최대 0.0032199841633202544rad, 발 변위 최대 0.0001392823553159754m, 관절 속도 최대 0.8293704986572266rad/s. 접촉 끝점 비율 `{'any_main_support': 1.0, 'triple_support': 0.9993055555555556, 'chest': 0.9993055555555556, 'right_upper_arm': 1.0, 'thigh': 1.0, 'both_feet': 1.0, 'left_foot': 1.0, 'right_foot': 1.0, 'target_fret_candidate': 0.0}`. 최장 연속 목표 후보 dwell 0.0s, episode별 longest dwell 분포(s) `{'count': 48, 'minimum': 0.0, 'median': 0.0, 'mean': 0.0, 'population_std': 0.0, 'maximum': 0.0}`. 방향·줄 일치 기하 타현 99회. 회계 일치 `True`, 실행 완료 `True`.
  - 물리 회계: 과제 측정 46080 step, 준비 24000 step, 합계 70080 step. 에피소드 초기화 50회, simulator 생성/종료 2/2회.

## 해석과 한계

- hold는 원래 native 목표 접촉 후보를 연속 0.05초 확보한 독립 기술입니다. 실제 현 압력·음향 검증이 아닙니다.
- cross는 선택한 줄·방향의 적격 기하 통과 기술이며 왼손 압현 조건과 음악 시각 일치가 없는 경우에도 성공할 수 있습니다.
- 현 안전 gate는 전체 주요 지지의 유지와 발 접지를 검사합니다. 이 gate 통과가 초기 V3의 삼중 동시 지지 95% 조건이나 왼손 하중 비의존 검증을 뜻하지 않습니다. any_main_support와 triple_support·개별 chest/upper-arm/thigh 접촉을 구분해 기록합니다.
- 안정성 비용 가중치 1과 초기 std 0.02를 사용했습니다. 초기 설정 actor learning rate는 1e-5이며, KL guard 재시도 뒤 마지막 실효 learning rate는 왼손 6.25e-07, 오른손 2.5e-06입니다. 수용된 KL과 거절 시도 포함 최대 KL·재시도를 구분합니다. 24 update 또는 1800초 예산은 update 시작 전에 검사하므로 진행 중 update만큼 wall 예산을 초과할 수 있습니다.
- BC 이전과의 무작위 대조군 비교나 수렴·일반화 입증을 수행한 집계가 아닙니다. 최종 모델 승격은 별도 결정적 native checkpoint 검증 결과로 판단합니다.
- 진행 중 gzip은 종료 trailer가 없을 수 있습니다. 완전한 JSON record만 집계하고 미완결 여부를 JSON에 기록합니다. 이 문서는 두 report 종료 후 재집계한 확정 기록입니다.

[상세 canonical 집계](ppo_progress_v1.json) · [그래프](ppo_progress_v1.png)
