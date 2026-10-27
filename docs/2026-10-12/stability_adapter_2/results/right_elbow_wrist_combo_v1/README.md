# 오른팔 팔꿈치·손목 조합 초기각 비교

2026-10-06. 고정한 wrist reference에서 `R_Elbow_x`만 바꾼 세 초기각의 source 검사와 저장 ON trace 비교다. 세 설정 모두 source 음수 pair 0으로 통과했다.

| 조건 | `R_Elbow_x` 초기각 (rad) | RH palm/body unsigned source-hull gap (mm) |
|---|---:|---:|
| 기준 | −0.14782950282096863 | 2.313745 |
| 추가 −0.0025 rad | −0.15032950282096863 | 2.747716 |
| 추가 −0.005 rad | −0.15282950282096863 | 3.180791 |

source gap은 형상 proxy이며 cooked PhysX clearance, 접촉·관통 깊이 인증이 아니다. 절대 strap rest length는 모두 1.1010801317960974 m였다. 전체105개 중 `R_Elbow_x` 외104개 초기 q(손목각 `−0.42467687010765076 rad` 포함), 기타 +5mm 목표p/q·root·native PD/solver를 유지했다. torso9·fingers42·C02 하체 목표는 유지하며 PI 보정은 팔24에만 적용하고 주요66 제어 연결을 유지했다.

아래는 저장된 0.1/0.5/1.0초 ON trace의 최대 기타 위치·회전 오차다.

| 구간 | 팔꿈치 초기각 조건 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|---:|---:|
| 0.1 s | 기준 | 6.872551 | 1.519351 |
| 0.1 s | −0.0025 rad | 6.879172 | 1.520551 |
| 0.1 s | −0.005 rad | 6.872682 | 1.519359 |
| 0.5 s | 기준 | 35.481509 | 4.991410 |
| 0.5 s | −0.0025 rad | 35.981824 | 5.047246 |
| 0.5 s | −0.005 rad | 36.292373 | 5.113359 |
| 1.0 s | 기준 | 73.660431 | 13.502121 |
| 1.0 s | −0.0025 rad | 119.343878 | 28.970036 |
| 1.0 s | −0.005 rad | 119.009665 | 28.632557 |

![고정 손목 자세에서 세 팔꿈치 X 초기각의 기간별 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/right_elbow_wrist_combo_v1.png)

두 팔꿈치 조정각 모두 1초 위치·회전 오차가 기준보다 높아 채택하지 않았고 OFF run으로 연장하지 않았다. 손목·LA reference는 다음 진단용으로 유지하며 안정 연주 성공으로 보지 않는다.

세 1초 ON run은 PI가 각각 212 physics samples 동안 포화됐다. LH·어깨 contact 행은 0이다. RH thumb3는 기준 221 rows/78 samples(step 86–163), elbow −0.0025는 134/54(step 86–141), −0.005는 125/42(step 87–142)였다. 최대 적용 tension은 15.034899/15.044201/15.044990 N이었다. strap force는 고정값이 아니며 contact counts/times는 힘·원인·연속 지지나 관통 깊이를 인증하지 않는다.

재생은 저장 JSON trace를 사용하고 추가 native 실행은 하지 않는다. 비교 checks와 138개 embedded input SHA를 plot 전에 확인한다. 기존 산출물을 보존하기 위해 CLI에는 새 빈 `--out-dir`를 지정한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_elbow_wrist_combo_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1 \
  --out-dir /tmp/elbow_combo_luna_reproduction
```

다음 방향은 오른팔/LA를 유지하고 `L_Elbow_x/y`와 `L_Wrist_x/y` 한축씩 ±0.025rad를 기존 승인 범위에서 fresh source 검사하는 것이다. 다음 후보의 새 초기 조합과 후기 성능은 아직 미측정이며 이전 결과를 승계하지 않는다. comparison·plotter·출력 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/plot_manifest.json)에 기록했다.
