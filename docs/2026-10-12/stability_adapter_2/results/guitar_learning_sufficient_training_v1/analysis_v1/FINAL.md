# 장기 학습과 최종 평가

**후반에 완만한 개선은 있었지만, 탐색 중 안정적으로 압현하는 정책은 아직 완성되지 않았다.** 같은 초기 자세의 왼손 단음을 B32에서 추가 128업데이트(245,760전이, 학습 내부 약 2시간 41분) 학습했다. 훈련 1,024회 중 529회 성공, 물리 실패 0이며 모든 전이가 학습에 반영되고 폐기된 전이는 없다.

| 별도 정책 평가 | 기준 B32 | 중간 누적64 | 최종 누적160 |
|---|---:|---:|---:|
| 결정적 정책 | 20/20 | 20/20 | 20/20 |
| 확률적 정책·같은 20개 seed | 8/20 | 11/20 | 11/20 |
| 확률적 정책·새 프로세스 6개 | 3/6 | 미실행 | 4/6 |

모든 별도 평가에서도 물리 실패는 0이다. 최종 checkpoint 경로·SHA·strict 누적160·입력/source/runtime·원자료 검증을 통과했다. 새 프로세스 기준/최종 12회의 저장된 초기 상태는 접촉 이력까지 정확히 같았다. 다만 작은 표본·한 준비 자세·단일 학습 계보의 결과다.

학습 첫/뒤 절반 성공률은 48.24%→55.08%로 올랐다. 중간과 최종은 같은 20개 seed를 평가해 모두 11/20 성공했지만, 성공한 조건의 집합은 서로 다르다. 5개는 성공→실패, 다른 5개는 실패→성공했다. 최종 확률적 평균 유지율은 기준보다 높지만 중간보다 낮고, 미압현 시간은 두 모델보다 길다. 따라서 최종 모델이 모든 면에서 좋아졌다고 보기는 어렵다. persistent reset에서는 초기 자세·목표는 같아도 접촉 측정 이력이 달라지는 한계도 있다.

훈련 실패 495회 중 487회는 마지막 200ms 준비 구간 clean 접촉이 0이었다. Actor와 출력은 실제로 바뀌고 Critic 예측도 개선됐으며, LR 붕괴·KL 복원 반복은 없었다. 안전 비용이 음악 학습을 압도한다는 지표도 없다. 현재는 단순히 더 오래 같은 설정을 반복하는 것보다 **준비 구간의 학습 신호와 접촉 획득·회복 범위를 보완하는 후속 비교**가 우선이다.

다음 방향은 R1 준비 전 구간 신호, 실제 접촉 상실·회복 데이터 확보, R2 획득 latch의 관측·보상·해제 자격 연결이다. 이는 **아직 구현·학습하지 않은 후속 작업**이다. 현재 결과를 회복·전곡·양손·음향·초기 자세 일반화의 성공으로 설명하지 않는다. 평가 132회는 훈련량에 합산하지 않았고, 과거 C와 정확히 재현되는 첫 14회도 독립 실험으로 더하지 않았다.

![학습 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1/summary_learning_curve.png)

상세: [최종 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1/FINAL_POLICY_EVALUATION.md) · [학습 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1/TRAINING_FINAL.md) · [파라미터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1/PARAMETER_FINAL.md) · [고정 관측 출력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1/analysis_v1/ACTOR_OUTPUT_FINAL.md)
