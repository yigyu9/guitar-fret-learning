# 팔 초기각 음수 후보의 후기 구간 진단

2026-10-06 저장 run 비교다. 기준, `R_Wrist_x −0.0025/−0.005 rad`, `R_Elbow_y −0.00125 rad`의 네 초기 설정은 모두 fresh source 검사에서 통과했다. 각도를 바꾼 나머지 초기 조건은 그대로다. 절대 strap rest length는 1.1010801317960974 m이며, 기타 +5 mm 목표와 quaternion, root, 몸통·손가락·하체, native PD/solver 및 24팔 PI와 주요66관절 제어 연결도 유지했다.

아래 값은 기타 위치·회전 오차의 각 run 최대값이다. `ON`은 PI 보정 활성, `OFF`는 선택된 손목 −0.005 rad 설정에서만 실행했다.

| 구간 | 초기 설정 | Mode | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|:---:|---:|---:|
| 0.1 s | 기준 | ON | 6.872016 | 1.519281 |
| 0.1 s | elbow Y −0.00125 rad | ON | 6.871872 | 1.519261 |
| 0.1 s | wrist X −0.0025 rad | ON | 6.875953 | 1.519916 |
| 0.1 s | wrist X −0.005 rad | ON | 6.872551 | 1.519351 |
| 0.1 s | wrist X −0.005 rad | OFF | 6.872551 | 1.519351 |
| 0.5 s | 기준 | ON | 34.975339 | 4.871416 |
| 0.5 s | elbow Y −0.00125 rad | ON | 35.237610 | 4.909962 |
| 0.5 s | wrist X −0.0025 rad | ON | 35.206641 | 4.912436 |
| 0.5 s | wrist X −0.005 rad | ON | 35.481509 | 4.991410 |
| 0.5 s | wrist X −0.005 rad | OFF | 54.801345 | 7.940387 |
| 1.0 s | 기준 | ON | 76.099207 | 14.183879 |
| 1.0 s | elbow Y −0.00125 rad | ON | 112.841326 | 26.625913 |
| 1.0 s | wrist X −0.0025 rad | ON | 116.186913 | 27.908480 |
| 1.0 s | wrist X −0.005 rad | ON | 73.660431 | 13.502121 |
| 1.0 s | wrist X −0.005 rad | OFF | 144.260293 | 36.309554 |

![네 초기 조건과 선택 wrist 조건 OFF의 세 기간별 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/artifacts/negative_pose_late_v1.png)

후보 wrist X −0.005 rad는 0.5초에서 기준보다 두 오차가 컸지만 1초 ON에서는 73.660431 mm/13.502121°로 기준보다 낮았다. 짧은 구간의 순위가 후기 구간 성능을 확정하지 못한다. 같은 손목 초기 설정의 1초 OFF는 144.260293 mm/36.309554°였고, ON에서도 큰 drift와 종료 속도(선속도 0.297622 m/s, 각속도 1.204088 rad/s)가 남았다. 결정 기록은 이 설정을 다음 진단의 reference로만 선택하며 안정 연주 성공으로 보지 않는다.

1초 ON에서 PI 보정은 212 physics samples 동안 포화됐다. RH thumb3는 ON 221 contact rows/78 samples(step 86–163), OFF 113 rows/37 samples(step 109–145), 이전 기준 ON 187 rows/69 samples(step 84–160)였다. LH와 어깨 접촉 행은 모두 0이다. 행 수와 첫·마지막 관측은 힘, 원인, 연속 지지 또는 관통 깊이를 증명하지 않는다. controller에는 기타 위치·회전 오차 feedback이 없고 residual q error만 사용한다.

재생성은 저장 trace만 읽으며 추가 native run은 수행하지 않는다. CLI는 세 기간을 실제 comparison rows에서 구성하고, plot 전 전역·run별 check와 176개 입력 SHA를 확인한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/negative_pose_late_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1 \
  --out-dir /tmp/negative_pose_late_v1_reproduction
```

plotter, comparison 입력, embedded source 및 이미지 hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/artifacts/plot_manifest.json)에 있다. 다음 단계 제안은 이전 거친 손목 초기각에서 얻은 preload 비교를 더 나은 wrist 자세에서 고정 strap 길이로 다시 비교하는 것이다. 새 제어 범위는 추가하지 않으며, 선택 설정은 다음 진단 기준으로만 사용한다.
