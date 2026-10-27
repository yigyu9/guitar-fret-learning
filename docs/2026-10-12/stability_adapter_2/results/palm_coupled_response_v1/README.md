# 12축 손바닥·기타 결합 응답

이 분석은 α=.45 상수 목표 기준의 동일 초기 상태에서 12개 왼팔 축을 각각 +0.005 rad 바꾼 0.1초 native run과, 모든 12축을 +0.001 rad 바꾼 heldout을 비교한다. 같은 seed, 절대 strap 길이 1.1018469719600776 m, PD, torso 9축, root·하체 고정, 기타 초기 상태와 self-collision 조건을 유지했다. 총 14회 초기화와 336 physics step이며 추가 native run은 하지 않았다.

| 조건 | 요청 목표 변화 | 종료 손바닥 point 오차 (mm) | 기타 최대 위치/회전 오차 (mm / °) | 양의 raw palm λ step / 행 |
|---|---:|---:|---:|---|
| α=.45 기준 | 없음 | 9.288558 | 5.341201 / 1.006166 | 2 / 2 |
| L_Thorax_x | +.005 rad | 9.170356 | 5.163317 / 0.979721 | 2 / 2 |
| L_Thorax_y | +.005 rad | 9.366849 | 5.210811 / 0.992070 | 2 / 2 |
| L_Thorax_z | +.005 rad | 9.317834 | 5.294625 / 0.999091 | 2 / 2 |
| L_Shoulder_x | +.005 rad | 9.388558 | 5.226875 / 0.990378 | 2 / 2 |
| L_Shoulder_y | +.005 rad | 9.194598 | 5.162679 / 0.984789 | 2 / 2 |
| L_Shoulder_z | +.005 rad | 9.393145 | 5.359593 / 1.006226 | 2 / 3 |
| L_Elbow_x | +.005 rad | 9.319838 | 5.425644 / 1.013867 | 2 / 2 |
| L_Elbow_y | +.005 rad | 9.075644 | 5.061444 / 0.967492 | 없음 / 0 |
| L_Elbow_z | +.005 rad | 9.336408 | 5.417106 / 1.011822 | 2 / 3 |
| L_Wrist_x | +.005 rad | 9.348919 | 5.368086 / 1.009995 | 2 / 2 |
| L_Wrist_y | +.005 rad | 9.218347 | 5.301567 / 0.999538 | 2 / 2 |
| L_Wrist_z | +.005 rad | 9.292876 | 5.385352 / 1.011523 | 2 / 3 |
| heldout | +.001 rad × 12 | 9.295099 | 5.197744 / 0.985742 | 2 / 2 |

![단일축 response 및 heldout terminal 예측 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/palm_coupled_response.png)

그림의 첫 세 패널은 12축 위치 probe별 종료 손바닥 오차와 0.1초 구간 기타 최대 위치·회전 오차다. 축은 관측값 주변으로 확대한 범위라 실제 단위와 눈금값을 함께 읽어야 한다. 마지막 패널은 heldout의 선형 예측과 실제 terminal 출력 차이를 출력 block별 원래 단위로 표시한다: 손 위치 0.030036 mm, 손 법선 회전벡터 0.002525°, 기타 위치 0.024734 mm, 기타 회전벡터 0.003647°. 이 차이는 분석 관측값이지 형식적 통과 기준이 아니다.

이 자료는 고정 PD 목표에서 측정한 0.1초 응답으로, FK 자체나 feedback/controller 검증이 아니다. 기준 run의 states/trace/tasks/contacts/controls 다섯 배열은 이전 α=.45 run과 exact 비교됐고, report·실행 metadata는 별도 run 계약으로 검사됐다. 대부분 조건에서 양의 raw palm λ는 step 2에만 기록됐고 L_Elbow_y probe는 양의 raw λ가 없었다. λ는 힘(N)으로 환산하지 않았으며 짧은 기록은 지속 지지나 연주 성공을 의미하지 않는다. L_Elbow_y는 이 sample의 손·기타 지표가 비교적 낮았지만 후보 채택이나 새 α/feedback을 정당화하지 않는다. heldout 차이는 별도 합격 판정이 아니다. 다음 분석은 접촉이 생기는 조건 주변의 12축 응답을 손과 기타에서 함께 맞춰 보는 범위로 제한한다.

## 재생성

```bash
MUJOCO_GL=disable MPLBACKEND=Agg MPLCONFIGDIR=/tmp/stability2_palm_coupled_plot \
  python3 stability_adapter_2/plot_palm_coupled_response.py \
  --out-dir /tmp/stability2_coupled_replot
```

기본 실행은 기존 파일을 덮어쓰지 않으므로 재생성에는 새 출력 경로를 사용한다. [6개 분석 검사와 14 init/336 step 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/analysis.json:1), [입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/plot_manifest.json:1), [plot 실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/plot_execution.json:1), [plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_coupled_response.py:1).
