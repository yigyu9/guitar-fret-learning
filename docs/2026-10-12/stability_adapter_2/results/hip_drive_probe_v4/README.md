# Isolated hip drive fixture v4

작성일: 2026-10-06. `report.json`에 기록된 24개 독립 0.1초 CPU PhysX fixture 조건을 정리한다. 1-hinge/3-hinge, authored/wide ±180° bounds, 초기 L_Hip_x 0/−90°, position/off/effort drive의 조합이다. position fixture의 PD readback은 stiffness 300, damping 75, effort cap 300이다. 메인 humanoid의 실제 각도·범위, baseline backend, 기타 목표는 바꾸지 않았다.

## 결과 요약

각 행은 초기 자세에서 세팅한 L_Hip_x와 drive 조합이며, 최대 편차는 전체 DOF에서 계산한 직접 actual−target 차의 절댓값 최댓값이다. wrapping하지 않은 raw 값이다.

| Joint fixture | Bounds | Initial L_Hip_x | Drive | Max raw target deviation (deg) |
|---|---|---:|---|---:|
| 1-hinge | Authored | 0° | Position | 0.000000 |
| 1-hinge | Authored | 0° | Off | 0.000000 |
| 1-hinge | Authored | 0° | Effort | 0.000000 |
| 1-hinge | Authored | −90° | Position | 0.000000 |
| 1-hinge | Authored | −90° | Off | 0.000000 |
| 1-hinge | Authored | −90° | Effort | 0.000000 |
| 1-hinge | Wide ±180° | 0° | Position | 0.000000 |
| 1-hinge | Wide ±180° | 0° | Off | 0.000000 |
| 1-hinge | Wide ±180° | 0° | Effort | 0.000000 |
| 1-hinge | Wide ±180° | −90° | Position | 0.000000 |
| 1-hinge | Wide ±180° | −90° | Off | 0.000000 |
| 1-hinge | Wide ±180° | −90° | Effort | 0.000000 |
| 3-hinge | Authored | 0° | Position | 0.000000 |
| 3-hinge | Authored | 0° | Off | 0.000000 |
| 3-hinge | Authored | 0° | Effort | 0.000000 |
| 3-hinge | Authored | −90° | Position | 4.291274 |
| 3-hinge | Authored | −90° | Off | 0.000014 |
| 3-hinge | Authored | −90° | Effort | 0.000014 |
| 3-hinge | Wide ±180° | 0° | Position | 0.000000 |
| 3-hinge | Wide ±180° | 0° | Off | 0.000000 |
| 3-hinge | Wide ±180° | 0° | Effort | 0.000000 |
| 3-hinge | Wide ±180° | −90° | Position | 4.196023 |
| 3-hinge | Wide ±180° | −90° | Off | 0.000014 |
| 3-hinge | Wide ±180° | −90° | Effort | 4.186622 |

3-hinge, −90° 시작에서 authored bounds position drive의 최대 raw 편차는 4.291274°였고 wide bounds에서도 4.196023°였다. 한계 범위를 넓혀도 이 fixture의 position-drive 이탈은 해소되지 않았다. authored bounds에서는 drive off/effort가 target 근처에 머물렀지만, wide bounds explicit effort에서도 4.186622° 편차가 나타났다. 따라서 drive mode 변경이 항상 문제를 해결한다고 일반화할 수 없다. 표와 곡선의 편차는 실제 DOF 측정값이다. EFFORT trace의 `previous_submitted_torque_nm` 필드만 제출 명령을 기록하며, 실측 토크가 아니다. position mode의 implicit torque는 별도 측정하지 않았다.

![3-hinge −90° fixture의 L_Hip_y raw actual−target 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/images/hip_drive_probe_v4_three_hinge_minus90.png)

그래프는 3-hinge fixture에서 L_Hip_y actual−target 직접 차를 시간별로 보이며 각도 wrapping을 하지 않았다. 범례의 최대치는 그 fixture 조건에 속한 x/y/z DOF 전체의 raw 차 최대 절댓값이다. 모든 hinge는 native `Revolute`로 보고되었다. 이 이름만으로 구면 joint라 추정하지 않는다.

모든 24조건은 초기 실제 DOF velocity 0, 초기 자세 일치, PD property/solver readback, 중력 runtime getter 0, 종료 시 native velocity-target getter 0, 유한 q 상태 및 contact 없음 검사를 통과했다. position target 일치 검사는 해당되는 position drive 조건에 적용된다. 중력은 초기화 후 `get_sim_params`로 확인했고, velocity-target getter는 24 physics steps 종료 시점이다.

이것은 단순 fixture 결과다. 실제 사람의 고관절 각도 범위·모델·기타 결합을 검사하지 않았고, 전체 human 문제의 단일 원인을 확정하지 않으며 stable candidate나 성공 결과가 아니다.

## 생성·이력

- 원자료: `report.json`, 개별 condition JSON, fixture XML과 `run.log`.
- 그림 생성기: `/home/ajou/yigyu/3/stability_adapter_2/plot_hip_drive_probe.py`.
- 재생성: `python /home/ajou/yigyu/3/stability_adapter_2/plot_hip_drive_probe.py --input /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/report.json --output /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/images/hip_drive_probe_v4_three_hinge_minus90.png`.
- 이력: v1은 첫 8개 position 진단을 [원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v1/report.json)에 보존했다. v2는 drive off에서도 native position-target getter를 비교하는 검사 오류로 중단했으며 [실패 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v2/failed.log)와 [실패 스크립트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v2/run_hip_drive_probe_failed.py.txt)를 보존했다. v3의 [24조건 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v3/report.json)는 완료되었고 v4는 중력 runtime·종료 시 velocity-target getter 메타데이터를 추가했다. v3와 v4의 24 trace는 모두 정확히 일치한다.
