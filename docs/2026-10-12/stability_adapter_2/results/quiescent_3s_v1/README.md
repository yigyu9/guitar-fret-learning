# 3초 quiescent pose 관찰 진단

2026-10-07. 동일 초기 humanoid/guitar pose, fixed absolute LA `1.1010801317960974 m`, 기존 joint-error PI 설정으로 저장된 3초 ON run을 정리했다. 이전 1초 run의 raw prefix와 초기 q/zero velocity, root 및 목표·PD·solver 설정이 유지됐다는 comparison checks가 통과했다. Plot 및 source-shape 이미지 생성은 저장 자료만 읽었으며 추가 native 실행은 하지 않았다.

## 저장 trace 요약

| 항목 | 저장값 |
|---|---:|
| 3초 내 최대 기타 위치 오차 | 251.150465 mm |
| 3초 내 최대 기타 회전 오차 | 81.526863° |
| 3초 종료 기타 위치 오차 | 236.386968 mm |
| 3초 종료 기타 회전 오차 | 77.801738° |
| 3초 종료 선속도 / 각속도 | 0.012952304 m/s / 0.038382001 rad/s |
| 3초 내 최대 적용 strap tension | 72.260483 N |
| 팔 실제 q의 초기 기준 대비 최대 편차 | 14.698074° |
| arm scalar limit 초과 최대 | 0.030300° |
| PI 포화된 held physics samples | 692 / 720 |

종단 속도는 낮지만 기타 목표 오차가 여전히 크고 arm drift·scalar-limit 차이 및 접촉 관측이 남아 있다. 따라서 낮은 종단 속도를 안정성이나 연주 성공으로 해석하지 않는다. 3초는 후기 상태를 관찰하는 실행 시간이며 WAIT 조건이나 새 성공 기준이 아니다.

## 시간별 source-shape 재구성

![저장 native pose의 0, 1, 3초 source geometry와 strap route](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/geometry/quiescent_3s_source_geometry.png)

각 panel은 저장된 native pose에서 source collision shapes를 재구성했다. 파랑은 guitar, 초록/자홍은 좌/우 손 형상, 회색은 나머지 humanoid, 점선은 기록된 strap route다. 손바닥 화살표는 저장 landmark에서 만든 normal proxy이며 해부학적 부호를 검증하지 않았다. 이는 Isaac/PhysX native renderer가 아니며 cooked geometry clearance, native contact 또는 지지력 인증이 아니다. 세 panel은 같은 world bounds와 camera를 사용한다.

접촉 필드는 다음처럼 기록됐다. 행 수와 sample 수는 접촉력·원인·연속 지지·관통 깊이를 증명하지 않는다.

| human body | contact rows | unique physics samples | first–last step |
|---|---:|---:|---:|
| Pelvis | 1,070 | 367 | 330–720 |
| R_Elbow | 390 | 373 | 345–720 |
| R_Hip | 675 | 664 | 2–720 |
| Torso | 2 | 2 | 318–319 |
| RH:thumb2 | 7 | 6 | 86–91 |
| RH:thumb3 | 219 | 77 | 86–164 |
| LH / shoulders | 0 | 0 | — |

## 저장 trace 그림과 검증

![저장된 3초 CPU PhysX 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/trace/quiescent_3s_v1.png)

비교 입력의 79 embedded SHA와 전체 comparison checks가 통과했다. Source geometry manifest에는 comparison 및 실제 report/states/trace 입력, plotting helper 체인과 source config/XML/mesh 40개 asset의 SHA가 기록돼 있다. 각 manifest는 output PNG hash를 입력 의존성과 분리해 보존한다.

아래 두 명령은 각각 trace와 geometry 그림을 재생한다. 실행 시 새 빈 출력 디렉터리를 지정하며 저장 trace만 읽는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
  MUJOCO_GL=disable MPLCONFIGDIR=/tmp/quiescent_trace_mpl_repro MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1 \
  --out-dir /tmp/quiescent_3s_user_reproduction/trace

PYTHONPATH=/home/ajou/yigyu/3 LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
  MUJOCO_GL=disable MPLCONFIGDIR=/tmp/quiescent_geometry_mpl_repro MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_quiescent_pose \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1 \
  --out-dir /tmp/quiescent_3s_user_reproduction/geometry
```

Trace provenance는 [trace plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/trace/plot_manifest.json:1), geometry source/input/output provenance는 [geometry plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/geometry/plot_manifest.json:1)에 있다. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/review.md:1), [검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/verification.json:1), [소스 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/source_final_manifest.json:1), [전체 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/file_inventory.json:1)에 재현·검수·보존 정보를 기록한다.

## 이전 동일 자세의 1초 OFF/ON 대조

| 관절 목표각 보정 | 최대 위치 오차 | 최대 회전 오차 |
|---|---:|---:|
| OFF | 144.267967 mm | 36.395296° |
| ON | 73.268255 mm | 13.439339° |

이는 이번 3초 실행의 초기 자세와 같은 이전 비교다.
[OFF trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/off/hold_1s/l_wrist_x_minus0125/trace.json:1)와
[ON trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125/trace.json:1)를 참조한다.
이번에 OFF 3초 실행을 추가하지 않았다. 보정의 1초 개선이 3초 유지로 이어지지 않았다.
