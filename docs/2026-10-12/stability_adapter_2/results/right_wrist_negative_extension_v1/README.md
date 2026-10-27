# 오른손 손목의 추가 음수 초기각 비교

2026-10-06. `negative_pose_late_v1` wrist reference에서 `R_Wrist_x`만 더 음수 방향으로 바꾼 source 검사 및 저장 run 비교다. 세 입력 모두 기존 범위·source 검사를 통과했다.

| 조건 | `R_Wrist_x` 초기각 (rad) | RH palm/body unsigned source proxy gap (mm) |
|---|---:|---:|
| 기준 | −0.42467687010765076 | 2.313745 |
| 추가 −0.0025 rad | −0.42717687010765076 | 2.342578 |
| 추가 −0.005 rad | −0.42967687010765077 | 2.371586 |

이 source gap은 geometry proxy이며 cooked PhysX clearance나 실제 접촉·관통 깊이를 인증하지 않는다. 공통 절대 strap rest length는 1.1010801317960974 m다. 기타 +5 mm 목표 p/q, root, torso9·fingers42·C02 하체의 초기 목표, native PD/solver는 기준과 같다. PI 보정은 팔24에만 적용하며 주요66 제어 연결을 유지했다.

아래 값은 저장 trace의 최대 기타 위치·회전 오차다. 세 초기조건을 0.1/0.5/1.0초 ON으로 비교했다.

| 구간 | 초기각 조건 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|---:|---:|
| 0.1 s | 기준 | 6.872551 | 1.519351 |
| 0.1 s | 추가 −0.0025 rad | 6.870813 | 1.519096 |
| 0.1 s | 추가 −0.005 rad | 6.876060 | 1.519943 |
| 0.5 s | 기준 | 35.481509 | 4.991410 |
| 0.5 s | 추가 −0.0025 rad | 35.733898 | 5.010188 |
| 0.5 s | 추가 −0.005 rad | 36.275960 | 5.087703 |
| 1.0 s | 기준 | 73.660431 | 13.502121 |
| 1.0 s | 추가 −0.0025 rad | 114.478578 | 27.196448 |
| 1.0 s | 추가 −0.005 rad | 124.274325 | 31.128511 |

![오른손 손목 세 초기각의 기간별 저장 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/right_wrist_negative_extension_v1.png)

두 추가 음수 각도는 1초 기준보다 위치·회전 오차가 모두 높았으므로 OFF로 연장하지 않았고 채택하지 않았다. 기존 손목 기준각과 0 N 길이는 다음 진단 reference로 남지만, 큰 1초 오차가 있어 안정 연주 성공으로 보지 않는다.

모든 1초 ON run에서 PI 포화는 212 physics samples였다. LH와 어깨 contact 행은 모두 0이다. RH thumb3는 기준 221 rows/78 samples(step 86–163), −0.0025는 136/54(step 86–139), −0.005는 121/41(step 87–138)이다. 적용 tension 최대값은 각각 15.034899/15.024511/15.039238 N으로, 초기 길이 설정이 runtime 고정 힘이라는 뜻이 아니다. 접촉 행·sample 및 첫·마지막 step은 힘, 원인, 연속 지지 또는 관통 깊이를 증명하지 않는다.

재생은 저장 JSON trace만 사용하고 추가 native 실행은 하지 않는다. Plot CLI는 전역·run별 checks와 138개 embedded input SHA를 확인한다. 아래 출력 경로는 비어 있는 새 경로로 바꿔 실행한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_wrist_negative_extension_mpl MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1 \
  --out-dir /tmp/wrist_extra_luna_reproduction
```

comparison·plotter·이미지 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/plot_manifest.json)에 있다. 다음 승인 방향은 현재 reference에서 `R_Wrist_x ±0.00125 rad`를 기존 범위 안에서 fresh source 검사하는 것이다. 새 제어기·gain·목표·물리 설정은 이 결과에 추가하지 않았다.
