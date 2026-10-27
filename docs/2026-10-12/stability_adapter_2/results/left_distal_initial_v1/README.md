# 왼팔 distal 단일축 초기각 비교

2026-10-07. 오른팔/wrist reference, absolute LA `1.1010801317960974 m`를 고정하고 왼팔 elbow·wrist 한 축씩 움직인 초기 입력 9개를 검사했다. 기준 포함 6개가 통과했고, 후보 3개는 signed source query의 negative pair 때문에 제외했다.

## 초기 입력 검사

아래 간격은 각 조건에서 가까운 `LH:palm`–guitar geometry pair 중 최소 signed source-query 값이다. RH palm/body unsigned proxy와는 다른 비교값이며, PhysX clearance·관통 깊이·접촉·지지력 인증이 아니다.

| 조건 | 입력 변화 | 통과 | negative pair 수 | 최소 LH:palm signed query (mm) |
|---|---|:---:|---:|---:|
| 기준 | 없음 | 예 | 0 | 0.440263 |
| L_Elbow_x | −0.025 rad | 예 | 0 | 2.012430 |
| L_Elbow_x | +0.025 rad | 아니오 | 2 | −1.089537 |
| L_Elbow_y | −0.025 rad | 아니오 | 4 | −5.855340 |
| L_Elbow_y | +0.025 rad | 예 | 0 | 7.133252 |
| L_Wrist_x | −0.025 rad | 아니오 | 2 | −0.096390 |
| L_Wrist_x | +0.025 rad | 예 | 0 | 0.994751 |
| L_Wrist_y | −0.025 rad | 예 | 0 | 0.072963 |
| L_Wrist_y | +0.025 rad | 예 | 0 | 0.815109 |

`L_Wrist_y −0.025 rad`에서 최소 LH:palm signed source query가 0.072962668 mm였지만 native run에서 LH contact 행은 0이었다. 이 가까운 source query만으로 접촉이나 물리 지지를 추정하지 않는다. 거부된 세 조건은 native 실행하지 않았다.

## 저장 ON trace 결과

통과한 기준 및 후보 다섯 개에 대해 0.1/0.5/1초 저장 ON run 18개를 비교했다. 표는 각 trace의 최대 기타 위치·회전 오차다.

| 구간 | 초기 조건 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|---:|---:|
| 0.1 s | 기준 | 6.872551 | 1.519351 |
| 0.1 s | L_Elbow_x −0.025 rad | 6.880257 | 1.520679 |
| 0.1 s | L_Elbow_y +0.025 rad | 6.872128 | 1.519235 |
| 0.1 s | L_Wrist_x +0.025 rad | 6.872493 | 1.519332 |
| 0.1 s | L_Wrist_y −0.025 rad | 6.874233 | 1.519687 |
| 0.1 s | L_Wrist_y +0.025 rad | 6.879653 | 1.520692 |
| 0.5 s | 기준 | 35.481509 | 4.991410 |
| 0.5 s | L_Elbow_x −0.025 rad | 35.490196 | 4.993275 |
| 0.5 s | L_Elbow_y +0.025 rad | 35.507412 | 4.982244 |
| 0.5 s | L_Wrist_x +0.025 rad | 35.486406 | 4.980165 |
| 0.5 s | L_Wrist_y −0.025 rad | 35.480725 | 4.991248 |
| 0.5 s | L_Wrist_y +0.025 rad | 35.485940 | 4.980152 |
| 1.0 s | 기준 | 73.660431 | 13.502121 |
| 1.0 s | L_Elbow_x −0.025 rad | 73.939937 | 13.592789 |
| 1.0 s | L_Elbow_y +0.025 rad | 118.207233 | 28.828275 |
| 1.0 s | L_Wrist_x +0.025 rad | 116.776036 | 28.168761 |
| 1.0 s | L_Wrist_y −0.025 rad | 73.723358 | 13.527902 |
| 1.0 s | L_Wrist_y +0.025 rad | 116.973804 | 28.272243 |

![왼팔 distal 통과 조건 및 기준의 0.1·0.5·1초 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/left_distal_initial_v1.png)

1초 후보 다섯 개는 모두 기준 73.660431 mm/13.502121°보다 위치와 회전 오차가 컸다. 따라서 새 각도를 채택하거나 OFF run으로 연장하지 않고 오른팔/wrist와 초기 법칙 장력 0 N에 해당하는 고정 LA reference를 유지한다(실제 strap tension은 시간에 따라 변한다). 이 reference도 큰 drift와 종료 속도가 남아 안정 연주 성공이 아니다.

각 1초 ON run은 보정 대상인 arm 24개 관절 중 하나 이상이 212 held physics samples에서 PI 포화됐다. 주요 66 관절 연결은 유지하고, fingers42·torso9·C02 하체는 PD 목표를 유지했지만 실제 상태가 고정된 것은 아니다. 종료 선속도는 0.297622–0.460234 m/s, 각속도는 1.204088–2.748397 rad/s였다. 최대 적용 tension은 15.028950–15.099994 N 범위에서 run별로 달랐다. 다섯 후보와 기준 모두 LH/어깨 contact 행은 0이다. Contact rows/samples와 첫·마지막 step은 접촉력·원인·연속 지지·관통 깊이를 증명하지 않는다. 1초 native target bounds 검사는 통과했으나 최대 arm scalar-limit 차이 0.030273–0.030515°가 남는다.

다음에는 결정 기록대로 현재 reference에서 측정된 LH source 경계를 향해 한 축씩 source 검사한다: `L_Elbow_x +0.003125/+0.00625`, `L_Elbow_y −0.0015625/−0.003125`, `L_Wrist_x −0.00625/−0.0125`, `L_Wrist_y −0.0375 rad`. 이는 기존 C02±0.3/model 범위의 초기 source 검사다. 거부 조건은 실행하지 않으며 새 gate·controller·gain·goal·learning을 추가하지 않는다.

재생성은 저장 trace만 읽으며 native run을 추가하지 않는다. comparison 전역·개별 checks와 198개 embedded input SHA를 확인한다. 기존 파일을 보존하도록 새 빈 출력 디렉터리를 지정한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/left_distal_initial_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1 \
  --out-dir /tmp/left_distal_initial_user_reproduction
```

비교·plotter·그림 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/plot_manifest.json)에 기록했다.
