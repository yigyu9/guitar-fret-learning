# Strike POSITION geometry PI 진단

Frozen Strike checkpoint의 5초 native diagnostic이다. PREPARE 49 control samples 뒤 PLAY 251 samples를 기록했고 HOLD는 없었다. 1,200 physics steps·151 native frames·21/21 checks로 완료됐으며 native input closure 1,085개와 분석 입력 7개 SHA는 변경되지 않았다. 학습은 0, `music_success=false`다.

이번 실행은 native POSITION mode와 기존 stiffness/damping을 사용했고 human EFFORT command는 없었다. Source phase 0의 R9 (`R_Shoulder`, `R_Elbow`, `R_Wrist`) 목표는 현재 기타 geometry를 기준으로 한 actual-angle PI adapter가 소유했고 frozen actor의 R9 목표는 기록만 했다. Actor는 30개 출력을 계산해 실행했고 source fingers 21개는 계속 policy가 제어했다. 대기와 recovery ownership은 별도 controller 경계로 정의돼 있지만 이번 저장 trajectory에서 관측한 source motor phase는 `[0]`뿐이다. 따라서 phase 1의 quarter-damping 전환은 실행되지 않았고 native PD switch count는 0이다. Source POSITION/torque CPU/GPU 동등성도 검증되지 않았다.

결과는 **NOT ADOPTED**다. READY success 0, target hit 0, physical target hit 0, accepted release 0, physical release 0, miss 10, wrong crossing 0이었다. 실행은 source terminal 없이 5초 끝까지 이어졌다. 마지막 running Strike F1은 0이다. Minimum policy pick-to-READY distance는 0.024599624 m였지만 READY success는 기록되지 않았다. 기타 회전 변화는 최대 45.020741°·종료 43.477582°, 위치 변화는 최대 46.353646 mm·종료 36.603237 mm였다. 기타가 playable region 안에 있었던 표본은 전체 control 91/300, PLAY policy 45/251이다. Contact/noncontact 및 readiness flag는 저장 센서 관측이며 기타 이동 원인을 인증하지 않는다.

이전 [timed-wait rebase 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/README.md:1)는 한 timely hit와 최대 기타 회전 변화 7.095455°를 기록했다. 이번 실행은 그 run과 PREPARE control 49행·native trace prefix 25행·첫 actor observation/action이 exact지만 이후 PLAY dynamics는 비교 기록에 적힌 대로 다르다. 따라서 결과 차이를 geometry PI 하나의 인과효과로 해석하지 않는다. 이번 결과는 **적시 타현 0회 및 크게 변한 기타 자세**라는 저장된 성과 범위 안에서만 읽는다.

## 실행 및 분석 근거

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/report.json), [native input closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/inputs_after.json): 1,200 steps, 151 frames, 21 checks, closure 1,085개 unchanged.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/analysis/summary.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/analysis/inputs_after.json): source phase·pulse·region·guitar pose summary와 analysis SHA 불변 기록.
- [Prefix comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/prefix_comparison.json): 이전 timed-wait rebase와 PREPARE controls 49행, native trace 25행, 첫 actor observation/action exact. 전체 PLAY/1,200-step trajectory 동일성을 뜻하지 않는다.
- [Goal-owner numerical check](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/numerical_goal_owner_check.json): 3/3 extracted branch cases pass. 이는 pure numerical branch check이며 Gym 실행 또는 전체 controller 인증이 아니다.
- [Checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/checkpoint_connection.json), [initial values/native state](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/initial_values.json), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/trace.json): frozen checkpoint metadata, 초기 상태, 300 control rows와 151 native state samples.
- [Plan](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_POSITION_GEOMETRY_PI_PLAN.md:1), [runner model/action dimensions](/home/ajou/yigyu/3/stability_adapter_2/run_strike_position_geometry_pi.py:57), [R9/finger joint grouping](/home/ajou/yigyu/3/stability_adapter_2/run_strike_position_geometry_pi.py:68), [actual-angle PI goal calculation](/home/ajou/yigyu/3/stability_adapter_2/run_strike_position_geometry_pi.py:149), [POSITION damping schedule/readback](/home/ajou/yigyu/3/stability_adapter_2/run_strike_position_geometry_pi.py:128), [actor execution](/home/ajou/yigyu/3/stability_adapter_2/run_strike_position_geometry_pi.py:265), [pulse/trajectory analyzer](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py:22), [pre-review PASS](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/pre_review.md).

## 저장된 native 전신 및 손 이미지

아래는 Isaac Gym native camera의 0·2·5초 frame이다. 전신/손 영상은 각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초, PREPARE 시작 | ![native 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/whole_body/00000.png) | ![native 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/hands/00000.png) |
| 2초, PLAY 중 | ![native 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/whole_body/00060.png) | ![native 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/hands/00060.png) |
| 5초, 기록 끝 | ![native 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/whole_body/00150.png) | ![native 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/frames/hands/00150.png) |

![Strike POSITION geometry PI 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/whole_body.mp4)

![Strike POSITION geometry PI 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/native/data/images/hands.mp4)

별도 soft-orientation 조정의 설계는 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md:1)에서 분리해 다룬다.
