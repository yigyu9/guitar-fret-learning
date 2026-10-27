# 오른팔 팔꿈치 Y 음수 각도 저장 결과

2026-10-06에 생성한 저장 결과 비교다. 입력 후보 5개 중 기준과 `R_Elbow_y −0.00125 rad`만 source 검사를 통과했다. `−0.0025`, `−0.005`, `−0.01 rad` 후보는 각각 signed source query에서 음수 pair 1개가 나와 제외했으며 native 실행하지 않았다. 이 source 검사는 PhysX clearance나 관통 깊이 인증이 아니다.

기준과 통과 후보의 ON 저장 run을 0.1초와 0.5초씩 비교했다. 네 run의 전역·개별 검증과 비교 입력 SHA가 모두 일치한다. 0.1초 개선량은 매우 작고, 0.5초에는 후보가 두 오차 모두 약간 더 컸다.

| 기간 | 초기 조건 | 최대 기타 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|---:|---:|
| 0.1 s | 기준 | 6.872016 | 1.519281 |
| 0.1 s | `R_Elbow_y −0.00125 rad` | 6.871872 | 1.519261 |
| 0.5 s | 기준 | 34.975339 | 4.871416 |
| 0.5 s | `R_Elbow_y −0.00125 rad` | 35.237610 | 4.909962 |

![저장된 기준 및 음수 각도 후보의 0.1/0.5초 두 기간별 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/right_elbow_y_negative_v1.png)

그림은 실제 저장된 native-run trace의 기타 위치·회전 오차를 표시한다. 짧은 구간의 미세한 차이를 장기 개선으로 해석하지 않는다. 1초 실행과 OFF 조건은 수행하지 않았으므로 후보의 후기 악화를 주장할 근거가 없다. 결정 기록은 후보를 채택하지 않고 기존 fine c02 기준을 유지한다.

두 0.5초 run에서 PI가 92개 physics sample 동안 포화됐다. LH와 어깨 contact 행은 0이다. 기준의 RH thumb3는 119행/37개 physics sample(step 84–120), 후보는 97행/30개 sample(step 85–120)이며, RH thumb2는 각각 6행/4개 sample(step 85–88), 1행/1개 sample(step 86)이다. 행 수와 첫·마지막 관측 step은 접촉력, 원인, 연속 지지 또는 관통 깊이를 증명하지 않는다.

초기 관절각 후보 외에는 fine c02 기준을 유지했다. 기타 +5 mm 목표와 quaternion, 절대 strap rest length 1.1010801317960974 m, root, 몸통·손가락·하체 목표, native PD/solver, PI 설정 및 제어 연결을 바꾸지 않았다. 새 controller나 학습 조건은 추가하지 않았다.

재생성은 native 시뮬레이션을 실행하지 않고 기존 JSON trace만 읽는다. 검증된 비교 SHA 목록은 104개 입력 파일을 포함한다. 결과 그림과 manifest는 새 출력 경로에서 생성한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_elbow_y_negative_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1 \
  --out-dir /tmp/right_elbow_y_negative_v1_reproduction
```

이전 고정 패널 그림·manifest는 `artifacts/` 및 `artifacts_v1/`에 보존했다. 현재 재사용 가능한 plotter로 만든 canonical 그림·manifest는 [artifacts_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/right_elbow_y_negative_v1.png)와 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/plot_manifest.json)에 있다. 선택 근거와 시험 범위는 [계획/분석 문서](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ELBOW_Y_NEGATIVE_COMPARE.md)에 있다.
