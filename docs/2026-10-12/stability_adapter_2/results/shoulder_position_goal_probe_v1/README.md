# POSITION 어깨 goal pulse 관절 반응 진단

이 진단은 원래 81-DOF POSITION PD 목표를 유지한 네 native 실행이다. `off`에는 pulse가 없고, `x`, `y`, `z` 조건은 해당 오른쪽 어깨 goal 한 축에만 +0.02 rad를 첫 4 physics step(0–3)에 제출한 뒤 step 4부터 초기 목표로 복귀했다. 네 실행 모두 5초·1,200 physics steps·151 native frames·7/7 checks가 완료됐다. 조건 간 initial state와 PD properties는 정확히 같았고, 모든 target 81개 native readback이 요청값과 정확히 일치했다. Actor/music/learning은 사용하지 않았다. [진단 계획](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_POSITION_GOAL_PROBE_PLAN.md:1), [사전 검수 PASS](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/pre_review.md).

step 4의 `summary.step4_shoulder_response_columns_x_y_z_rad`는 실제 `R_Shoulder_x/y/z` scalar DOF 좌표 변화(단위 rad)다. 행은 해당 실제 DOF 좌표, 열은 command한 target x/y/z pulse다. 이 scalar q label은 물리축 방향 표기가 아니다. XML의 physical basis는 XZY이며 parent-relative 회전 변화와 FK 검증은 아래에 별도로 기록한다:

| 실제 R_Shoulder DOF 좌표 \ target pulse 축 | x | y | z |
|---|---:|---:|---:|
| x | +0.001144283 | +0.000235923 | −0.000080861 |
| y | −0.000147730 | +0.001002938 | −0.000537902 |
| z | +0.000024319 | +0.000623137 | +0.000881344 |

세 축 모두 자기축에 양의 반응이 관측됐고 일부 교차축 변화도 있었다. parent-relative 회전 변화는 [analysis rows](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/rows.json)에 별도로 저장했다. native state에서 FK로 재구성한 어깨 회전의 최대 오차는 1.832856931×10⁻⁵°였다. 이 짧은 pulse 결과는 dynamic coupling을 관측하지만 target axis permutation/chart 교환을 인증하지 않으며, 더 큰 tracking error의 단독 원인도 확정하지 않는다. DOF force getter의 값은 합성 total force여서 drive 전용 토크를 뜻하지 않는다. Mass matrix는 읽기만 했고 제어에는 사용하지 않았다.

분석기 입력은 별도 33개이며 before/after SHA가 변경되지 않았다. Native 실행 closure는 조건별로 달랐고 모두 불변이다: OFF 1,069; X 1,070; Y 1,074; Z 1,074 files. 상세 응답 원자료는 [분석 rows](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/rows.json), [summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/summary.json)에 기록돼 있다.

Pulse는 첫 4 step뿐이므로 30 Hz 영상에서 보이는 차이가 작아도 정상이다. 영상은 prepared-strike baseline이나 연주 시연이 아니라 동일 초기 상태의 관절 반응 진단이다. 후속 EFFORT damping 분리 검토는 별도 사전 검수 PASS를 받았으며, 물리 실행과 결과는 별도 [HUMAN EFFORT damping 단계 계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_EFFORT_DAMPING_PROBE_PLAN.md:1) 및 [사전 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/pre_review.md)에서 다룬다. 이 진단의 final review는 예정돼 있다.

## 저장된 native 전신 및 손 영상

각 시점의 전신/손 이미지는 해당 조건의 Gym native camera frame이다. 아래 각 영상은 151 frames, 30 fps, stream duration 5.033333초다.

### OFF — pulse 없음

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![OFF 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/whole_body/00000.png) | ![OFF 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/hands/00000.png) |
| 2초 | ![OFF 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/whole_body/00060.png) | ![OFF 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/hands/00060.png) |
| 5초 | ![OFF 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/whole_body/00150.png) | ![OFF 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/frames/hands/00150.png) |

![OFF 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/whole_body.mp4)

![OFF 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/images/hands.mp4)

### X — R_Shoulder_x +0.02 rad

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![X 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/whole_body/00000.png) | ![X 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/hands/00000.png) |
| 2초 | ![X 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/whole_body/00060.png) | ![X 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/hands/00060.png) |
| 5초 | ![X 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/whole_body/00150.png) | ![X 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/frames/hands/00150.png) |

![X 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/whole_body.mp4)

![X 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/images/hands.mp4)

### Y — R_Shoulder_y +0.02 rad

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![Y 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/whole_body/00000.png) | ![Y 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/hands/00000.png) |
| 2초 | ![Y 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/whole_body/00060.png) | ![Y 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/hands/00060.png) |
| 5초 | ![Y 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/whole_body/00150.png) | ![Y 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/frames/hands/00150.png) |

![Y 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/whole_body.mp4)

![Y 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/images/hands.mp4)

### Z — R_Shoulder_z +0.02 rad

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![Z 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/whole_body/00000.png) | ![Z 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/hands/00000.png) |
| 2초 | ![Z 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/whole_body/00060.png) | ![Z 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/hands/00060.png) |
| 5초 | ![Z 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/whole_body/00150.png) | ![Z 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/frames/hands/00150.png) |

![Z 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/whole_body.mp4)

![Z 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/images/hands.mp4)

## 원자료 및 입력 closure

- 분석: [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/summary.json), [rows.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/rows.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/inputs_before.json), [analysis inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/analysis/inputs_after.json).
- 각 조건의 native 자료는 해당 폴더 [OFF](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/off/data/report.json), [X](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/x/data/report.json), [Y](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/y/data/report.json), [Z](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/z/data/report.json) reports, `commands.json`, `states.json`, `initial_values.json`, and `mass_matrix_initial.json` files.
