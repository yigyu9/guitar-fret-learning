# 오른손 손목 초기각 유지 비교

2026-10-06 기록. fine c02 시작 자세에서 `R_Wrist_x`만 미세 조정하고, 기존 고정 strap rest length와 승인된 PI OFF/ON 설정을 유지한 13개 native run 결과다. 기준 조건도 이번 묶음에서 실행했으며, 이전 c02 reference raw 값 재현 검사가 통과했다. plot 생성은 저장 trace만 읽었다.

7개 초기 입력 recipe 중 `+0.010 rad`만 source query에서 음수 pair 1개로 제외했고, 나머지 6개는 통과했다. native 비교는 reference와 −0.0025/−0.005/+0.0025 rad의 네 조건이다. +0.0025 rad만 이후 연장 비교에 포함됐다. 초기 입력의 negative pair 수는 source query 관측이며 깊이 보정이나 PhysX clearance 인증이 아니다.

모든 조건에서 절대 rest length 1.1010801317960974 m, 기타 초기 목표 Z +5 mm, proximal/left/finger/torso/C02 하체 자세, root와 PI/gain/cap을 유지했다. 새 controller나 strap 제어는 추가하지 않았다.

## 저장 run의 최대 기타 오차

| 기간/조건 | mode | 최대 위치오차 (mm) | 최대 회전오차 (°) |
|---|---|---:|---:|
| 0.5초 reference | ON | 34.975339 | 4.871416 |
| 0.5초 −0.0025 rad | ON | 35.206641 | 4.912436 |
| 0.5초 −0.005 rad | ON | 35.481509 | 4.991410 |
| 0.5초 +0.0025 rad | ON | 34.743287 | 4.817860 |
| 1초 reference | ON | 76.099207 | 14.183879 |
| 1초 +0.0025 rad | ON | 84.746456 | 16.983471 |
| 1초 +0.0025 rad | OFF | 137.369031 | 33.307159 |

+0.0025 rad는 0.5초 ON에서 두 지표 모두 기준보다 낮았지만, 1초 ON에서는 둘 다 더 커졌다. 0.5초 오차 개선만으로 유지 성공이라 볼 수 없다. 사용한 PI는 관절각 오차 보정이며 기타 p/q 오차 feedback은 아니다. 이전 fine c02 자세와 LA를 다음 진단 기준으로 유지하고, 이 새 손목각은 채택하지 않는다.

## 접촉 관측과 제한

LH와 어깨 contact 행은 모두 0이다. 1초 reference ON의 RH thumb3는 187행/69개 physics sample(첫 step 84, 0.350000초; 마지막 step 160, 0.666667초), thumb2는 6행/4개 sample(step 85–88)이다. +0.0025 ON은 thumb3 168행/58개 sample(step 84–141, 0.350000–0.587500초), thumb2 1행/1개 sample(step 85)이다. +0.0025 OFF thumb3는 133행/41개 sample(step 108–148, 0.450000–0.616667초)다. 첫·마지막 관측은 접촉이 연속이었다는 뜻이 아니며 행·sample 수도 지지력, 원인, 깊이를 입증하지 않는다.

그림 위쪽은 0.5초 ON의 네 wrist 조건, 아래쪽은 1초 reference ON 및 +0.0025 ON/OFF trace다. 0.5초와 1초는 별도 축 범위로 표시했다. manifest는 comparison에 선언된 158개 입력/source hash를 출력 전에 재검증하고, plotter와 PNG hash를 기록한다.

![오른손 손목 offset의 0.5초 4조건 및 1초 유지 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_retention_v1/artifacts/right_wrist_retention_v1.png)

재생성 예시:

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_wrist_retention_v1_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_wrist_retention \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_retention_v1 \
  --out-dir /tmp/right_wrist_retention_v1_reproduction
```
