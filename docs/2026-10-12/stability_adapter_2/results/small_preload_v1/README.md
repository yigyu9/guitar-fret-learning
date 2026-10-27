# 개선 wrist 자세의 작은 초기 strap preload 비교

2026-10-06. `negative_pose_late_v1`의 `R_Wrist_x −0.005 rad` 자세에서 초기 law-tension 0/1/2 N에 해당하는 고정 절대 strap rest length를 비교했다. 기존 0 N 입력은 이전 설정과 byte-exact라 그대로 재사용했다. 0/1/2 N 입력 세 건은 fresh source 검사에 통과했으며, native 비교는 세 길이×0.1/0.5/1.0초 ON, 총 9개 저장 run이다. 기타 +5 mm 목표와 quaternion, torso9·fingers42·C02 하체의 초기 목표, root, native PD/solver를 유지했다. PI 보정은 팔24에만 적용하며 주요66 제어 연결을 유지했다.

| 초기 law-tension 설정 | 절대 strap rest length (m) |
|---:|---:|
| 0 N | 1.1010801317960974 |
| 1 N | 1.1009134651294308 |
| 2 N | 1.1007467984627641 |

run 중 rest length는 고정값이다. 초기 law-tension 값은 strap이 내내 같은 힘을 가한다는 뜻이 아니며, 실제 적용 tension은 시간에 따라 변한다. 아래 표는 저장 trace의 최대 기타 위치·회전 오차다.

| 구간 | 초기 law tension | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---:|---:|---:|
| 0.1 s | 0 N | 6.872551 | 1.519351 |
| 0.1 s | 1 N | 6.841501 | 1.519078 |
| 0.1 s | 2 N | 6.811997 | 1.521482 |
| 0.5 s | 0 N | 35.481509 | 4.991410 |
| 0.5 s | 1 N | 35.468898 | 4.990968 |
| 0.5 s | 2 N | 35.576670 | 4.998614 |
| 1.0 s | 0 N | 73.660431 | 13.502121 |
| 1.0 s | 1 N | 79.221741 | 15.027785 |
| 1.0 s | 2 N | 120.773180 | 30.086380 |

![개선 wrist 자세에서 세 초기 strap 설정의 세 기간별 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/small_preload_v1.png)

1 N은 0.1초와 0.5초에서 두 오차가 아주 조금 낮았지만 1초에서는 기준보다 높았다. 2 N은 1초에 위치·회전 오차가 더 크게 증가했다. 어떤 새 길이도 1초 기준보다 두 지표를 함께 낮추지 못해 OFF run으로 연장하거나 길이를 채택하지 않았다. 0 N과 기존 개선 wrist 자세는 다음 진단의 reference로만 유지하며 안정 연주 성공으로 보지 않는다.

세 1초 ON run은 각각 212 physics sample 동안 PI 포화됐다. 최대 적용 tension은 0/1/2 N 조건에서 15.034899/15.463361/15.991668 N이었다. LH·어깨 contact 행은 모두 0이다. RH thumb3는 각각 221/78, 194/74, 137/53 contact rows/samples이며 마지막 관측 step은 163/160/138이다. 접촉 행·sample 수와 관측 끝점은 힘, 원인, 연속 지지 또는 관통 깊이를 입증하지 않는다. 초기 source 검사도 cooked PhysX clearance 인증이 아니다.

재생성은 저장 trace만 읽으며 native simulation을 다시 실행하지 않는다. 전역·run별 checks와 139개 embedded input SHA를 확인한 뒤 그린다. 아래 출력 경로는 비어 있는 새 경로로 바꿔 실행한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/small_preload_luna_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1 \
  --out-dir /tmp/small_preload_luna_reproduction
```

comparison·plotter·산출물 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/plot_manifest.json)에 기록했다. 기존 결과 범위에서 이어갈 다음 설정 후보는 현재 자세에서 `R_Wrist_x −0.0025/−0.005 rad`, 0 N 길이의 fresh source 검사다. 새 제어나 학습, 결과 채택은 이 보고서에서 수행하지 않는다.
