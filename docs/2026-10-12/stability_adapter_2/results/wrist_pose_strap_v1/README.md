# 개선된 wrist 자세의 초기 strap 길이 비교

2026-10-06. 이전 strap 비교보다 wrist 자세를 `negative_pose_late_v1`의 `R_Wrist_x −0.005 rad`로 바꾸고, 0/5/10/20 N 초기 law-tension 설정에 해당하는 절대 rest length를 비교했다. 기타 +5 mm 목표와 quaternion, torso9, fingers42, C02 하체, root, native PD, solver, PI24/main66 설정은 고정했다. 각 run 동안 rest length는 고정이고, strap law tension은 시간에 따라 달라질 수 있다.

| 초기 law tension 설정 | 절대 strap rest length (m) |
|---:|---:|
| 0 N | 1.1010801317960974 |
| 5 N | 1.1002467984627642 |
| 10 N | 1.0994134651294307 |
| 20 N | 1.0977467984627640 |

source 입력 audit에는 5개 항목이 통과했으며, 그중 기존 0 N과 같은 legacy 중복은 새로 실행하지 않았다. 비교 파일에는 네 설정의 ON 저장 trace가 세 구간씩, 총 12개 run row로 기록되어 있다. 아래 표는 각 trace의 최대 기타 위치·회전 오차다.

| 구간 | 초기 law tension | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---:|---:|---:|
| 0.1 s | 0 N | 6.872551 | 1.519351 |
| 0.1 s | 5 N | 6.799980 | 1.558750 |
| 0.1 s | 10 N | 6.914132 | 1.691398 |
| 0.1 s | 20 N | 7.702071 | 2.164250 |
| 0.5 s | 0 N | 35.481509 | 4.991410 |
| 0.5 s | 5 N | 35.611339 | 5.065101 |
| 0.5 s | 10 N | 35.431617 | 5.191976 |
| 0.5 s | 20 N | 39.161926 | 6.064343 |
| 1.0 s | 0 N | 73.660431 | 13.502121 |
| 1.0 s | 5 N | 122.290835 | 32.067454 |
| 1.0 s | 10 N | 101.491973 | 23.490280 |
| 1.0 s | 20 N | 155.299893 | 65.533423 |

![네 초기 strap 설정의 0.1, 0.5, 1초 저장 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/wrist_pose_strap_v1.png)

1초에서 어떤 길이도 0 N 기준보다 위치·회전 오차를 모두 낮추지 못해 새 길이를 채택하지 않았다. 0 N + 개선된 wrist 자세는 다음 비교를 위한 진단 reference일 뿐 안정 연주 성공이 아니다. 1초 ON에서는 네 설정 모두 PI가 212 physics sample 동안 포화됐다. 최대 적용 tension은 0/5/10/20 N 설정에서 각각 15.0349/17.5787/15.0292/53.2533 N이었다. 이는 초기 law 설정값이 일정한 strap force로 유지된다는 뜻이 아니다.

1초 run에서 LH·어깨 contact 행은 모두 0이다. RH thumb3 contact row/sample 수는 0 N 221/78, 5 N 128/44, 10 N 122/43, 20 N 61/23이다. 20 N run은 Torso 2행/1 sample(step 231)도 기록했다. 접촉 행·sample은 힘, 원인, 관통 깊이 또는 연속 지지를 인증하지 않는다. 이전 0 N 설정과 비교한 source shape query도 PhysX cooked clearance 인증이 아니다.

재생성은 저장 trace만 읽고 native simulation은 실행하지 않는다. CLI 전역·run별 checks와 157개 embedded input SHA를 확인한 뒤 기간별 그림을 만든다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/wrist_pose_strap_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1 \
  --out-dir /tmp/wrist_pose_strap_v1_reproduction
```

comparison·plotter·출력 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/plot_manifest.json)에 기록했다. root의 다음 방향은 같은 자세에서 이전 0–5 N 구간 안의 더 작은 초기 preload를 비교하는 것이다. 이 보고서에서는 새 설정이나 controller를 제안·적용하지 않는다.
