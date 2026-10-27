# Lower-body PD and solver diagnostics v1

작성일: 2026-10-06. 이 묶음은 `comparison_all.json`의 14개 짧은 CPU PhysX 진단(각 0.1초)을 비교한다. 모든 조건은 같은 초기 q/p, 초기 strap 절대 rest length `L_A`를 사용했다. 그래프와 표는 결과 요약이며 안정성 판정기가 아니다.

## 14개 조건 요약

| Preset | 최대 위치 오차 (mm) | 최대 회전 오차 (°) | 최대 raw 하체 target 편차 (°) | 최대 scalar-limit 위반 (°) | 최종 속도 (m/s) |
|---|---:|---:|---:|---:|---:|
| baseline | 65.315 | 7.318 | 107.805 | 101.738 | 1.594 |
| depen01 | 378.454 | 48.277 | 250.586 | 70.586 | 7.717 |
| leg_effort_depen01 | 25.113 | 7.190 | 85.237 | 78.061 | 1.084 |
| leg_effort_pd | 214.159 | 22.346 | 109.784 | 109.784 | 0.747 |
| leg_kd01 | 48.325 | 10.711 | 98.226 | 98.226 | 2.064 |
| leg_passive | 391.171 | 78.852 | 94.894 | 94.894 | 3.414 |
| leg_pd01 | 246.222 | 31.582 | 109.381 | 109.381 | 1.071 |
| pgs | 27.685 | 3.945 | 17.744 | 2.754 | 0.268 |
| pgs16 | 17,582.150 | 174.096 | 149.963 | 119.963 | 410.610 |
| solver16 | 310.808 | 168.170 | 239.077 | 174.491 | 10.953 |
| solver16_depen01 | 121.085 | 16.497 | 240.604 | 76.145 | 0.207 |
| solver16_leg_kd01 | 17.946 | 3.904 | 246.060 | 79.670 | 0.039 |
| substeps4 | 240.044 | 24.845 | 62.981 | 28.783 | 0.394 |
| substeps8 | 339.745 | 41.652 | 52.326 | 25.503 | 2.128 |

![14개 PD/solver 진단의 기타 오차와 raw 하체 target 편차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/images/lower_body_pd_v1_comparison.png)

표의 하체 값은 실제각도에서 target을 뺀 직접 차이며 angle wrapping을 하지 않은 raw 값이다. 위치 오차 축은 큰 폭주 조건이 함께 보이도록 로그 스케일이다. PGS4/2(`pgs`)는 기타 위치/회전 오차를 27.685 mm/3.945°로 줄였지만 하체 raw 편차 17.744°와 scalar-limit 최대 위반 2.754°가 남아 안정 자세로 채택하지 않는다. `solver16_leg_kd01`은 위치 오차가 가장 작지만 하체 raw 편차 246.060°로 실패 조건이다. `pgs16`은 17.582 m 위치 오차와 410.610 m/s 최종 속도로 폭주했다. 모든 report의 `checks`가 true이거나 snapshot이 유한하다는 사실만으로 안정성을 뜻하지 않는다.

별도 격리된 무중력·외부 contact 없는 humanoid-only 확인에서 baseline hold의 최대 target 편차는 6.771702°였고 drive-off에서는 0.000389°였다. 이것은 단일 원인 입증이 아니며 최종 환경 조건도 아니다. 조건 간 원인 귀속이나 성공 기준은 여기서 정하지 않는다.

## 원자료와 재현

- 비교 원자료: `comparison_all.json`; 개별 run report/trace/states/contacts와 로그, 격리 probe 결과는 이 디렉터리에 보존되어 있다. 서로 다른 source snapshot들이 포함되어 있으므로 모든 source 버전이 정확히 함께 보존되었다고 주장하지 않는다.
- 그림 생성기: `/home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py`.
- 재생성: `python /home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py --input /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/comparison_all.json --output /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/images/lower_body_pd_v1_comparison.png`.
- 이미지는 저장된 요약 JSON의 plot이며 native renderer가 아니다. 원자료 제한과 각 실행별 경고는 각 attempt의 로그 및 원래 report에서 확인한다.
