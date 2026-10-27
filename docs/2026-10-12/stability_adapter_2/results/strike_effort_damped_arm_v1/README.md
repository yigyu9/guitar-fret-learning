# Strike EFFORT 오른팔 spring/damping 진단

고정 Strike checkpoint를 바꾸지 않고 5초 native diagnostic을 실행했다. PREPARE 49 control samples 후 PLAY는 251 samples였고, HOLD 0이었다. source actor는 PLAY 구간 30차원 출력을 사용했다(R9 arm targets와 RH 21 finger outputs). 학습 update는 0이다. native recording은 1,200 physics steps·151 camera frames·24/24 contract checks 완료, native input closure 1,078개 변경 0이며 별도 analysis SHA 입력 7개도 변경되지 않았다. 음악 완료는 false다.

이 진단은 R9 (`R_Shoulder`, `R_Elbow`, `R_Wrist`)만 EFFORT/stiffness 0으로 두고, 매 physics step actual q를 읽어 `clip(original_kp * (final_goal - actual_q), ±original_effort_limit)`를 명시적으로 요청했다. 오른팔 R9 damping은 source phase 0에서 원래값, phase 1에서 0.25배였다. 나머지 72 DOF는 POSITION으로 남았다. Torque log는 requested human torque command이며 측정된 drive torque가 아니다. 전체 구동 방식은 source POSITION/외부 torque와 동등한 것으로 검증되지 않았고, source/native CPU·GPU equivalence도 이 결과의 범위가 아니다.

결과는 **NOT ADOPTED**다. timely target hit 0, physical target hit 0, accepted release mask 0, READY success 1, physical release 1, miss 10, wrong crossing 1이 기록됐다. Strike F1은 0이었다. source terminal 상태는 발생하지 않아 5초 physics 실행은 끝까지 유지됐고, 기타 회전 변화는 최대 46.354493°·종료 43.328547°, 위치 변화는 최대 46.353646 mm·종료 30.453770 mm였다. 기타가 playable region 안에 든 표본은 전체 control 49/300, policy 3/251이었다. 이 진단은 hit 성공을 보이지 않았고, 관측된 기타 움직임의 원인이나 축 혼합을 단독으로 입증하지 않는다.

## 실행·checkpoint 근거

| 근거 | 저장된 값 |
|---|---|
| Frozen checkpoint | [`strike_010000.pt`](/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt), SHA-256 `9244b33c87426afb28c10a1176b88f23832a50a57605586d4e28084a48160e87`; official G0 qualification은 false |
| PLAY EFFORT mode | R9 `EFFORT`, stiffness 0, source phase 0 damping 1.0 / phase 1 damping 0.25; phase property switch 2회, readback exact |
| 명시적 R9 spring | 매 physics step original kp × (final target − actual q), original effort limits로 clip; 다른 72개 torque 요소는 0 |
| 결과 기록 | [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/report.json), [phase PD properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/PD_phase_properties.json), [torque commands 및 동시 actual/target](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/human_torque_commands.json) |
| 분석 기록 | [summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/analysis/summary.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/analysis/inputs_after.json) |
| 초기 상태와 추적 | [initial values/native state](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/initial_values.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/checkpoint_connection.json), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/trace.json) |
| 구현·계획·사전검수 | [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_EFFORT_DAMPED_ARM_PLAN.md:1), [actor dimensions](/home/ajou/yigyu/3/stability_adapter_2/run_strike_effort_damped_arm.py:60), [R9 membership](/home/ajou/yigyu/3/stability_adapter_2/run_strike_effort_damped_arm.py:71), [phase property schedule](/home/ajou/yigyu/3/stability_adapter_2/run_strike_effort_damped_arm.py:148), [spring command](/home/ajou/yigyu/3/stability_adapter_2/run_strike_effort_damped_arm.py:103), [analysis pulse counts](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py:22), [trajectory metrics](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py:49), [사전 검수 PASS](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/pre_review.md) |

## 저장된 native 전신 및 손 이미지

아래는 native camera에서 저장한 0·2·5초 전신/손 이미지다. 영상은 각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초, PREPARE 시작 | ![native 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/whole_body/00000.png) | ![native 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/hands/00000.png) |
| 2초, PLAY 중 | ![native 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/whole_body/00060.png) | ![native 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/hands/00060.png) |
| 5초, 기록 끝 | ![native 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/whole_body/00150.png) | ![native 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/frames/hands/00150.png) |

![Strike EFFORT native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/whole_body.mp4)

![Strike EFFORT native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/native/data/images/hands.mp4)

후속 geometry PI 조정은 별도 [Strike EFFORT geometry PI 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_EFFORT_GEOMETRY_PI_PLAN.md:1)과 [별도 phase analysis](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/analysis/summary.json)에서 구분해 다룬다. 본 결과는 해당 후속 단계의 판정이나 원인 증명이 아니다.
