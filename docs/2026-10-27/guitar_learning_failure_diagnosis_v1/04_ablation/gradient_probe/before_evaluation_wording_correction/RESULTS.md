# Frozen 정책의 첫 기울기 측정 결과

체크포인트50·100·300의 실제 GPU 진단을 각각 완료했다. 세 모델 모두 고정 상태에서224틱(896물리step),128환경을 실행했으며 소스·체크포인트·모델 불변성과 scene 종료를 통과했다. 각32틱 배치를 따로 정규화했다. 새 학습이나 optimizer 갱신은 수행하지 않았다.

| 체크포인트 | 새 완료 에피소드 / 달성 | clean 평균 | wrong 평균 | 기울기 합 최대오차 | raw cost 합 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 50 | 128 / 47 | 0.3653 | 0.2935 | 1.34e-07 | 0 |
| 100 | 128 / 40 | 0.2997 | 0.2568 | 4.47e-08 | 0 |
| 300 | 128 / 0 | 0.0000 | 0.0000 | 1.1e-07 | 0 |

위 에피소드 값은 이 **확률적 frozen rollout**의 부수 결과이며 별도 deterministic10회 평가와 동일한 표본이 아니다. 동일 seed도 서로 다른 정책의 궤적을 같게 만들지 않는다.

세 모델 모두7배치 평균 norm은 reward value residual이 가장 컸다. cp300은 최초 접촉·압현 유지·달성·오압현 성분의 gradient가 모두0인 반면, 대기 자세·엄지 안내·critic residual은 남았다. 이 새 rollout에서 올바른 접촉까지 이르는 표본과 그 직접 보상 신호가 사라졌다는 관측이며, 대기/엄지/critic이 퇴행을 일으켰다는 인과 증거는 아니다.

| 성분 | cp50 평균 norm | cp100 평균 norm | cp300 평균 norm |
| --- | ---: | ---: | ---: |
| Approach | 0.1019 | 0.1123 | 0.1031 |
| First contact | 0.02005 | 0.01633 | 0 |
| Clean hold | 0.0643 | 0.06205 | 0 |
| Achievement | 0.0163 | 0.0209 | 0 |
| Wrong press | 0.008257 | 0.006864 | 0 |
| Deficit | 0.005559 | 0.002699 | 0.1359 |
| Standby | 0.007992 | 0.005651 | 0.5024 |
| Thumb | 0.003923 | 0.002791 | 0.2531 |
| Action change | 1.47e-05 | 9.348e-06 | 0.0008659 |
| Reward value residual | 0.4255 | 0.2486 | 1.448 |
| Negative cost GAE | 0.06138 | 0.1777 | 0.3389 |

![성분별 기울기 크기](gradient_norm_heatmaps.png)

![전체 기울기와의 방향 정렬](gradient_alignment_heatmaps.png)

행별 크기는 공유 전체 actor 파라미터에 대한 clipping·Adam 이전의 norm이다. 양의 cosine은 해당 성분의 손실 기울기가 전체 손실 기울기와 같은 방향이고, 음수는 반대 방향이라는 뜻이다. 회색은 성분 norm이0에 가까워 cosine을 정의하지 않은 칸이다. gradient descent는 이 벡터의 음의 방향으로 움직인다. 성능의 인과적 기여율이나 최종 parameter 변화의 정확한 분해로 해석하지 않는다.

보상9항에 value baseline을 임의 분배하지 않고 reward critic residual을10번째로 분리했다. 이 residual 자체는 예측오차가 아니며 정당한 baseline 효과를 포함할 수 있다. 별도 [완결 return 기반 가치 예측 점검](VALUE_CALIBRATION.md)에서 Vr/Vc와 실제 표본 return을 직접 비교했다. 마지막은 원래 cost GAE 전체에 -cost_weight를 곱한 성분이다. raw cost가0이어도 학습된 critic이0이 아니면 마지막 성분은0이 아닐 수 있다. 이는 이 고정 모델과 새 배치에서의 수치적 현상이며 회귀의 원인이라는 증거는 아니다.

배치6은 원래 음 시점, 배치7은 말미·자연 종료와 다음 에피소드 초반을 포함한다. 초기 실패가 있으면 실제 종료·리셋이 그대로 반영된다. 배치별 원본 시간·episode ID·terminal/truncation과 실제 완료 에피소드를 보존했다. 저장된 보상·값에서 GAE와 정규화 성분을 CPU로 다시 계산해 전부 일치했다.

[기계 판독 비교](comparison.json) · [구현·실행 계약](README.md)
