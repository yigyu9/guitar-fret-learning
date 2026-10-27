# HUMAN EFFORT damping 4조건 관절 반응 진단

같은 native 초기 상태에서 오른쪽 팔 12 DOF를 첫 4 physics step(0–3) 동안 EFFORT/stiffness 0으로 전환하고, damping을 0으로 두거나 기존값으로 유지한 네 조건을 비교했다. ON 조건은 첫 torque command에서 오른팔 12축에 요청 10 Nm를 주며, float32 readback 요청값은 10.000001907 Nm다. OFF는 0 Nm다. step 4에서 original POSITION properties를 복원하고 이후 요청 torque를 명시적으로 0으로 둔다. 목표는 원래 목표로 돌아가지 않는다. `R_Shoulder_z` 목표에 +0.05 rad를 더한 값이 복원 뒤에도 유지된다. 이는 requested torque와 scalar joint-state 반응을 보는 짧은 probe이며 측정된 drive torque가 아니다.

네 조건 모두 1,200 physics steps·151 native camera frames·9/9 checks로 5초 기록을 완료했다. 시작 native 상태는 네 조건에서 exact였다. 기존 zero-damping OFF/ON EFFORT 기록도 각각 152/152 저장 상태가 exact 재현됐다. 실행 입력 closure 변경은 d0_off 1,074개, 나머지 각 1,075개에서 모두 0이며, 별도 분석 입력 27개 SHA도 before/after 동일하다. Actor/music/learning은 사용하지 않았다.

아래 표는 `summary.step4_responses`의 실제 `R_Shoulder_x/y/z` scalar DOF 좌표 차이와 속도 차이다. scalar q suffix는 world/physical rotation axis를 뜻하지 않는다. torque 비교는 ON−OFF, damping 비교는 retained−zero이며 단위는 q=rad, qdot=rad/s다.

| 비교 (step 4) | R_Shoulder_x q / qdot | R_Shoulder_y q / qdot | R_Shoulder_z q / qdot |
|---|---:|---:|---:|
| torque ON−OFF, damping 0 | −0.009787589 / +0.135631800 | +0.009568721 / +0.745662495 | +0.039242268 / +3.846986488 |
| torque ON−OFF, damping retained | −0.000386737 / −0.007634805 | +0.000181705 / −0.005667746 | +0.002287090 / +0.044148592 |
| damping retained−zero, torque OFF | +0.000469461 / +0.010758470 | +0.000189543 / +0.033588570 | −0.002405614 / −0.213907313 |
| damping retained−zero, torque ON | +0.009870313 / −0.132508134 | −0.009197474 / −0.717741672 | −0.039360791 / −4.016745207 |

요청 torque ON−OFF의 shoulder-z step-4 차이는 damping 0에서 0.0392422676086 rad / 3.84698648750782 rad/s, damping 유지에서 0.00228708982468 rad / 0.04414859227836 rad/s였다. 요청 damping 조건에 따라 scalar q 응답 차이가 관측됐다. 이는 네 조건의 짧은 응답이며 다른 관절 집합의 damping 모델, source hybrid 동등성, 측정 torque, 연주 성공이나 안정성을 인증하지 않는다. body 상대 회전·force 측정으로 해석하지 않는다. Mass matrix는 초기 상태에서 read-only로 기록했고 torque 제어에는 쓰지 않았다.

## 저장된 native 전신 및 손 이미지

각 조건에서 아래는 0초, 2초, 5초에 저장한 Isaac Gym native 전신 및 손 camera frame이다. 각 MP4는 native 151-frame·30 fps 영상이며 duration은 5.033333초다.

### d0_off — damping 0, 요청 torque OFF

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![d0_off 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/whole_body/00000.png) | ![d0_off 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/hands/00000.png) |
| 2초 | ![d0_off 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/whole_body/00060.png) | ![d0_off 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/hands/00060.png) |
| 5초 | ![d0_off 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/whole_body/00150.png) | ![d0_off 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/frames/hands/00150.png) |

![d0_off 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/whole_body.mp4)

![d0_off 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_off/data/images/hands.mp4)

### d0_on — damping 0, 요청 torque ON

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![d0_on 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/whole_body/00000.png) | ![d0_on 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/hands/00000.png) |
| 2초 | ![d0_on 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/whole_body/00060.png) | ![d0_on 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/hands/00060.png) |
| 5초 | ![d0_on 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/whole_body/00150.png) | ![d0_on 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/frames/hands/00150.png) |

![d0_on 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/whole_body.mp4)

![d0_on 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d0_on/data/images/hands.mp4)

### d1_off — damping retained, 요청 torque OFF

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![d1_off 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/whole_body/00000.png) | ![d1_off 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/hands/00000.png) |
| 2초 | ![d1_off 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/whole_body/00060.png) | ![d1_off 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/hands/00060.png) |
| 5초 | ![d1_off 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/whole_body/00150.png) | ![d1_off 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/frames/hands/00150.png) |

![d1_off 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/whole_body.mp4)

![d1_off 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_off/data/images/hands.mp4)

### d1_on — damping retained, 요청 torque ON

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![d1_on 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/whole_body/00000.png) | ![d1_on 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/hands/00000.png) |
| 2초 | ![d1_on 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/whole_body/00060.png) | ![d1_on 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/hands/00060.png) |
| 5초 | ![d1_on 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/whole_body/00150.png) | ![d1_on 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/frames/hands/00150.png) |

![d1_on 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/whole_body.mp4)

![d1_on 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/d1_on/data/images/hands.mp4)

## 근거 파일

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/analysis/summary.json), [분석 rows](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/analysis/rows.json), [분석 입력 SHA 전후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/analysis/inputs_before.json) / [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/analysis/inputs_after.json)
- 각 조건의 `report.json`, `commands.json`, `states.json`, `initial_values.json`, `native_EFFORT_PD_properties.json`, `mass_matrix_initial.json`, input SHA 기록은 [조건별 자료 폴더](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/)에서 확인한다.
- [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_EFFORT_DAMPING_PROBE_PLAN.md:1), [실행기](/home/ajou/yigyu/3/stability_adapter_2/run_human_effort_damping_probe.py:26), [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_human_effort_damping_probe.py:23), [사전 검수 PASS](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/pre_review.md)

후속 Strike EFFORT spring/damping 적용은 별도 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_EFFORT_DAMPED_ARM_PLAN.md:1)과 [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/pre_review.md) 단계에서 다룬다. 이 probe는 그 연주시험을 대신하지 않는다.
