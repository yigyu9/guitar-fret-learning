# Shoulder stiffness 200→300 비교 산출물

2026-10-07. 사용자 승인 범위에서 양쪽 Shoulder 6개 DOF의 stiffness만 200에서 300으로 바꾸고, damping·effort·초기 자세·기타 목표와 PALM_RATE 제어를 유지했다. 네 fresh native rollout은 0.1초와 0.5초 각각 stiffness 200/300이며 총 288 physics steps다. 비교 JSON은 7개 계약과 131개 원자료 SHA를 검증한다.

## 저장된 0.5초 trace

![0.5초 기타 오차, LH source 이탈, L_Shoulder_x gap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/artifacts_v3/shoulder_pd_hold_05s.png)

위 두 panel은 trace의 실제 기타 위치 norm error와 회전오차다. 왼쪽 아래는 저장된 LH source point에서 최초 palm goal까지의 거리이며 해부학적 palm이나 물리 접촉점으로 보정된 값이 아니다. 오른쪽 아래는 physics step 1–120의 완료 상태에서 `L_Shoulder_x` 제출 목표와 DOF 좌표 간 절대 scalar 차이다. 121개 trace timestamp는 0–0.5초를 포함하지만 이 gap은 완료된 120개 상태만 그렸고 t=0 값을 추정하지 않았다. 모든 panel은 독립 x축으로 0–0.5초를 표시한다. 그림은 저장 PhysX 수치 그래프이며 native renderer 출력이 아니다.

## 네 측정행

| 구간 | stiffness | 위치오차 최대 (mm) | 위치오차 최종 (mm) | 회전오차 최대 (°) | 회전오차 최종 (°) | LH source 최대 이탈 (mm) | LH/RH contact 행 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.1 s | 200 | 6.874401 | 6.874401 | 1.519676 | 1.519676 | 47.473935 | 0 / 0 |
| 0.1 s | 300 | 6.858439 | 6.858439 | 1.519430 | 1.519430 | 58.774513 | 0 / 0 |
| 0.5 s | 200 | 36.091149 | 34.773068 | 4.761921 | 4.316934 | 90.540508 | 0 / 135 |
| 0.5 s | 300 | 35.780031 | 35.780031 | 4.550541 | 4.236367 | 91.485370 | 0 / 100 |

0.5초 최대값 기준 stiffness 300의 기타 위치오차는 0.311117902 mm, 회전오차는 0.211379932° 작았다. 하지만 시점 끝의 위치오차는 35.780031 mm로 stiffness 200의 34.773068 mm보다 1.006963534 mm 컸다. 따라서 최대값의 감소를 끝 시점 개선이나 후기 유지 개선으로 해석하지 않는다. 끝 회전오차는 4.236367° 대 4.316934°였다. LH source 이탈은 0.944861679 mm 커졌다.

0.5초 `L_Shoulder_x` 완료-state 최대 target–actual scalar gap은 21.619762°에서 22.803789°로, `R_Shoulder_z`는 17.266792°에서 17.915964°로 커졌다. 이는 개별 Euler 축의 몸통 방향오차가 아니라 joint scalar 좌표 차이다. 최대 실제 arm scalar 한계위반도 약 0.030300°에서 0.043885°로 증가했다. Target-limit 통과 여부와 실제 상태의 제한 위반은 별도 값이다.

Contact 행 개수는 힘, 지속 지지, 인과관계 또는 cooked-clearance 증명이 아니다. 관측된 upward/local-neck proxy 조건도 실제 형상 clearance나 손 지지 인증이 아니다. 같은 제어 수식이어도 상태 피드백이 달라져 전달 목표가 완전히 같다고 볼 수 없다. stiffness 300은 일부 최대 기타 오차만 조금 낮았으며 LH 이탈·최종 위치오차·shoulder gap·scalar 한계위반이 악화됐다. 새 stiffness를 채택하지 않고 200을 진단 기준으로 유지한다. 1초는 측정하지 않았고, 어느 조건도 안정 또는 연주 성공으로 판정하지 않았다. 총 DOF force 기록을 actuator-only torque, 접촉력, 포화 또는 PD 원인으로 해석하지 않는다.

## 재현 및 보존

최신 그림은 [artifacts_v3/shoulder_pd_hold_05s.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/artifacts_v3/shoulder_pd_hold_05s.png)이며 producer·입력·출력 SHA는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/artifacts_v3/shoulder_pd_hold_05s.manifest.json)에 있다. 재생성 명령은 기존 파일을 덮지 않는 새 경로를 쓴다.

```bash
MPLCONFIGDIR=/tmp/shoulder_pd_compare_reproduction MPLBACKEND=Agg \
python /home/ajou/yigyu/3/stability_adapter_2/plot_shoulder_pd_compare.py \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1 \
  --out /tmp/shoulder_pd_compare_reproduction.png
```

플로터는 validated comparison의 7개 계약·131개 입력 SHA, 두 0.5초 trace·query·state의 121개 시점, 120개 control/state schedule 및 유한값을 확인한다. 실제 생성 명령·환경·종료 코드·log는 [plot_execution_v3.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/plot_execution_v3.json)과 [plot_run_v3.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/plot_run_v3.log)에 기록했다. 이전 그림과 producer snapshot도 `source_artifacts_v1`, `source_artifacts_v2`, `source_artifacts_v3`, `source_plot_v1`, `source_plot_v2`, `source_plot_v3`에 보존했다. `py_compile`과 이미지 직접 검토를 마쳤으며 독립 검수도 완료됐다.

`source_plot_v2`는 v2 실행 뒤 검증을 추가한 working snapshot이다. 실제 v2 실행 소스는 [source_plot_v2_executed](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/source_plot_v2_executed/plot_shoulder_pd_compare.py)로 별도 복원해 실행 기록·manifest의 producer SHA와 정확히 맞음을 확인했다. [복원 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/source_plot_v2_executed/RESTORE_CHECK.json)에 방법을 기록했고 기존 자료와 최종 플로터는 보존했다.

독립 검수 완료: [runtime_review.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/runtime_review.md:7). 미해결 finding은 없으며, 최종 보존·SHA 검증은 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/verification.json)에 기록했다.
