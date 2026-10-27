# Stage1 학습·실제 평가 분석

검증 조건 충족: **True**. stage1 범위의 판단이며 다음 단계 승격을 뜻하지 않는다.

stage0의24회 학습 source와 새 stage1의 학습 횟수를 구분한다. 시간창은 ±0.5초이며 정책 pre-roll1초·전체5초·native 정착2초는 유지한다.

| 손 | 회차 | 단계 성공 | audible 유지율 | 최초 down 절대오차(ms) | 추가 목표 down | 반대 up | 기타 최대 이동(mm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| left | 1 | True | 1.000000 | None | 0 | 0 | 5.806433 |
| left | 2 | True | 1.000000 | None | 0 | 0 | 5.757609 |

left: stage0 최종 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 None ms. 동일 시작 조건의 기술적 비교다.

left: 같은 stage1 계약의 이전 사전평가 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 None ms. 이 비교를 stage1 PPO 변화의 근거로 사용한다.

left 학습: 12 updates / 7200전이, timing 성공24/24, 물리실패0. 실제 LR 6.25e-07~6.25e-07, KL retry2.

왼손 hold 보상 중 audible 밖 성분 비율 평균 82.828%. 시간창 변경으로 보상 적분 구간이 바뀌므로 stage0 총보상과 직접 비교하지 않는다.
| right | 1 | True | 0.000000 | 12.285673 | 1 | 1 | 0.242961 |
| right | 2 | True | 0.000000 | 12.285673 | 1 | 1 | 0.242961 |

right: stage0 최종 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 -5.394671 ms. 동일 시작 조건의 기술적 비교다.

right: 같은 stage1 계약의 이전 사전평가 대비 audible 유지율 평균 변화 0.000000, 최초 down 절대오차 평균 변화 -3.426388 ms. 이 비교를 stage1 PPO 변화의 근거로 사용한다.

right 학습: 12 updates / 7200전이, timing 성공24/24, 물리실패0. 실제 LR 2.5e-06~2.5e-06, KL retry1.

현재 타이밍 보상은 기존 보상 중 action_change·terminal_failure와 timing 항으로 구성된다. release 이력은 측정값이며 명시적인 해제 보상이 아니다. 따라서 단음의 긴 접촉 유지와 audible 밖 hold 보상을 연주 시간 정밀성으로 해석하지 않는다. stage0에서 이 성분은 평균 약91%였다.

다음 과제는 필요한 시점의 해제·다음 프렛 전환과 목표 다양화를 별도로 평가하는 것이다. 오른손의 추가 up/down 억제도 남아 있다. 현재 결과만으로 네트워크 확대나 안전 기준 완화를 우선할 근거는 없으며, 다음 목표와 시간창 단계를 선택해 평가하는 편이 적절하다.

240Hz 비용 적분·시계·실제 crossing 깊이/속도·inactive 행동0·원 joint music·입력 SHA는 JSON에 보존했다.

[전체 수치와 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_final_analysis_v1.json)

![KL·실제 LR·critic](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_final_analysis_v1.png)
