# 오른손 손목 국소 초기각 비교

2026-10-06. `negative_pose_late_v1`의 wrist reference를 중심으로 `R_Wrist_x ±0.00125 rad`만 조정한 source 통과 조건을 비교했다. 세 입력은 같은 절대 strap rest length 1.1010801317960974 m를 사용했다.

| 초기 조건 | `R_Wrist_x` (rad) | RH palm/body unsigned source proxy gap (mm) |
|---|---:|---:|
| 기준 | −0.42467687010765076 | 2.313745 |
| −0.00125 rad | −0.42592687010765073 | 2.328165 |
| +0.00125 rad | −0.4234268701076508 | 2.299420 |

source proxy 값은 cooked PhysX clearance나 접촉·관통 깊이를 인증하지 않는다. 세 입력 모두 fresh source 검사를 통과했고 signed negative pair는 0이며 LH 조건은 동일했다. 공통 초기 조건과 제어는 기준과 같게 유지했다. 아래는 0.1/0.5/1.0초 ON 저장 trace의 최대 기타 위치·회전 오차다.

| 구간 | 초기 조건 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|---:|---:|
| 0.1 s | 기준 | 6.872551 | 1.519351 |
| 0.1 s | −0.00125 rad | 6.871947 | 1.519217 |
| 0.1 s | +0.00125 rad | 6.875860 | 1.519900 |
| 0.5 s | 기준 | 35.481509 | 4.991410 |
| 0.5 s | −0.00125 rad | 35.613875 | 4.995615 |
| 0.5 s | +0.00125 rad | 35.351546 | 4.948202 |
| 1.0 s | 기준 | 73.660431 | 13.502121 |
| 1.0 s | −0.00125 rad | 117.748239 | 28.362203 |
| 1.0 s | +0.00125 rad | 119.007568 | 29.302065 |

![오른손 손목 기준각과 양옆 0.00125 rad의 세 기간 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/right_wrist_local_v1.png)

+0.00125 rad는 0.5초에서 기준보다 위치·회전 오차가 조금 낮았지만 1초에서는 둘 다 더 높았다. 두 조정각 모두 1초 기준보다 악화되어 채택하거나 OFF로 연장하지 않았다. 현재 wrist reference와 LA는 다음 진단용으로 유지할 뿐 안정 연주 성공으로 보지 않는다.

세 1초 ON run은 모두 PI 포화가 212 physics samples였다. LH·어깨 contact 행은 0이다. RH thumb3는 기준 221 rows/78 samples(step 86–163), −0.00125는 143/53(step 86–143), +0.00125는 141/55(step 85–139)였다. 최대 적용 tension은 세 조건에서 15.034899/15.027130/15.037921 N으로 약간 다르며 고정 힘이 아니다. contact row/sample 수나 첫·마지막 관측은 힘·원인·연속 지지·관통 깊이를 증명하지 않는다.

이 결과에서는 `R_Wrist_x` 외 초기 q와 torso9·fingers42·C02 하체 목표, 기타 +5mm 목표 p/q·root·native PD/solver를 유지했다. PI 보정은 팔24에만 적용하며 주요66 제어 연결을 유지했다. wrist X의 더 작은 세분화는 보류한다. 다음 비교는 같은 wrist 자세·LA에서 `R_Elbow_x −0.0025/−0.005 rad`를 fresh source 검사하는 것이며, 이전 elbow 실험은 다른 wrist 자세라 source 및 후기 성능을 대신 인증하지 않는다.

재생성은 저장 trace만 읽는다. 추가 native 실행 없이 전역·run별 checks와 138개 embedded input SHA를 확인한다. `--out-dir`에는 기존 그림을 덮어쓰지 않도록 새 경로를 사용한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_wrist_local_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1 \
  --out-dir /tmp/wrist_local_luna_reproduction
```

comparison·plotter·PNG SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/plot_manifest.json)에 기록했다.
