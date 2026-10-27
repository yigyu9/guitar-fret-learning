# Three-face finger target hold

2026-10-08. 두 조건을 각각 새로 5초 실행했다(2 native initializations/2400 physics steps). 같은 초기 81개 관절 좌표, 기타 목표, 절대 strap 길이, PD 및 solver를 사용했고 왼손 손가락 21개 절대 PD target만 달랐다. 팔 12축과 나머지 48축 목표는 유지했으며 최종 제어 인터페이스는 66축이다. 양 조건의 절대 strap rest length는 1.1018469719600776 m였다.

| 조건 | 첫 0.1초 최대 위치/회전 오차 | 5초 최대 위치/회전 오차 | 5초 종료 위치/회전 오차 | 마지막 1초 최대 위치/회전 오차 |
|---|---:|---:|---:|---:|
| Saved finger targets | 4.719 mm / 0.936° | 25.229 mm / 7.771° | 21.913 mm / 7.092° | 21.915 mm / 7.093° |
| Initial finger targets | 3.934 mm / 0.872° | 26.112 mm / 7.725° | 26.047 mm / 7.715° | 26.112 mm / 7.725° |

위치 오차는 world 기타 목표 위치와의 거리(mm), 회전 오차는 world SO(3) 오차(도)다. 초기 손가락 목표는 첫 0.1초 두 오차가 작았다. 5초 최대 위치 오차와 두 종료 오차는 saved target보다 컸고, 최대 회전 오차 7.725°는 saved target의 7.771°보다 약간 작았다. 결과는 목표 유지나 안정성 성공을 보이지 않으며 다음 후보 채택 근거로 해석하지 않는다.

| Trial / body | 마지막 양 raw-lambda step | 양 lambda 고유 physics step 수 |
|---|---:|---:|
| Saved — LH thumb3 | 1200 | 991 |
| Saved — LH index3 | 81 | 23 |
| Saved — LH middle3 | 1200 | 1072 |
| Saved — LH palm | 123 | 30 |
| Initial — LH thumb3 | 1200 | 1052 |
| Initial — LH index3 | 106 | 33 |
| Initial — LH middle3 | 1200 | 1086 |
| Initial — LH palm | 123 | 50 |
| Saved — R_Hip (right thigh) | 1200 | 1200 |
| Initial — R_Hip (right thigh) | 1200 | 1200 |

이 값은 post-physics 저장 contact sample에서 lambda가 양수였던 고유 step과 마지막 step이다. Raw contact row 수·고유 step 수·마지막 step은 서로 다른 집계다. 저장된 양의 lambda는 뉴턴 힘이 아니며 기타의 특정 면 접촉, 그 사이의 연속 접촉, 관통 부재 또는 면 지지를 인증하지 않는다. 누락된 body group은 양 lambda 고유 step 수 0개(empty step set)로 기록하며, 이를 physics step 0의 접촉으로 뜻하지 않는다. 두 trial의 6-body 초기 source-approach 조건은 true였지만 이는 cooked PhysX clearance 인증이 아니다.

두 조건의 손/전신 영상은 각각 151 frames, 30 fps, 5.033333초 길이다. 물리 기록은 step 0–1200의 5초 구간이다. 저장 기준 반복과 이번 saved-target 실행의 states/trace/tasks/contacts/controls raw arrays 및 두 영상은 byte-exact 일치했다. 이 equality는 관측 사실이며 성능 gate가 아니다.

## Figures

### Figure 112 — Guitar error and positive raw-contact samples

![Two trial guitar position and rotation error curves with post-physics positive raw-lambda sample timelines](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/three_face_finger_hold_curves.png)

Saved 240 Hz samples span 0–5 s. Contact marks show distinct post-physics samples with positive raw lambda at step/240 seconds; the two conditions use small vertical offsets. Marks do not encode lambda magnitude or continuous contact.

### Figure 113 — Actual Isaac Gym hand-camera frames

![Actual Isaac Gym hand-camera images at t=0 and t=5 seconds for both trials](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/three_face_finger_hold_hands.png)

The 2×2 montage uses the saved native-camera PNGs at steps 0 and 1200. Each cell is a 640×360 image. These are actual Gym frames; they do not establish face-specific or continuous support.

## Source records

- [Analysis and measured summaries](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/analysis.json>)
- [Approved artifact brief](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifact_brief.json>)
- [Saved-target initial values](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/saved_finger_targets/initial_values.json>) and [initial-target initial values](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/initial_finger_targets/initial_values.json>)
- Actual native recordings: [saved-target hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/saved_finger_targets/hands.mp4>), [saved-target whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/saved_finger_targets/whole_body.mp4>), [initial-target hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/initial_finger_targets/hands.mp4>), [initial-target whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/initial_finger_targets/whole_body.mp4>). Each is 151 frames at 30 fps; the physical record covers steps 0–1200.
- [Native run execution record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/execution.json>) and [artifact producer execution record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifact_execution.json>): artifact command exited 0 in 0.7420416880631819 seconds, with `native_calls: 0`.
- [Artifact input/output manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/artifact_manifest.json>)
- [Final review](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/review.md>) and [final verification record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/final_verification.json>).

## Plan status and next step

The frozen [finger-target plan](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FINGER_TARGET_HOLD_PLAN.md>) is a historical planning artifact whose closing status still says it was unexecuted. The current phase has since completed the two native runs and this saved-data analysis/artifact pass. The saved-target initial finger setting remains the diagnostic reference; the initial-target setting was not adopted. The next step is the unexecuted [support-loss pose and shape-property diagnosis](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md>), while the user's face-layout objective remains recorded in the [multi-face grip plan](</home/ajou/yigyu/3/stability_adapter_2/MULTI_FACE_GRIP_PLAN.md>).

Main tracking: [stability plan](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1489>), [project README](</home/ajou/yigyu/3/stability_adapter_2/README.md:832>), [dated README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:502>), and [next diagnostic plan](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md:1>).
