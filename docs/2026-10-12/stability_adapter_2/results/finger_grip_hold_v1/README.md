# 왼손 finger seed, preload 및 palm-feedback 저장 결과

2026-10-07. 이 단계는 기존 source probe와 native 저장 trace의 grip/preload 비교, 후속 world-palm/guitar feedback 진단, 마지막 1초 run의 Isaac Gym camera 영상을 모은다. 그림과 영상 후처리는 저장된 자료만 사용했다. 카메라 캡처용 1초 run 한 번을 포함해 관련 누적 실행 카운터는 79 native initialization / 1,872 physics steps다.

## 비교 조건

초기 seed 조건은 `LH:index/middle/ring/pinky`의 12개 finger joint angle을 바꿨다. 기준 기타 위치(Z +5 mm)와 기존 회전에 near2 µm 접근 보정 translation (−0.415437, +0.012261, −1.026976) mm을 적용한 position/quaternion target, absolute strap length 1.1018469719600776 m, native PD는 유지한다. 하체와 humanoid root는 고정하고 기타는 자유 상태다. torso 9개 목표는 hold 대상이며 실제 torso 각은 움직일 수 있다. source-hull gap은 PhysX cooked clearance나 접촉력 인증이 아니다.

결과를 finger seed 하나의 효과로 읽을 수 없다. `seed120_preload050_hold`는 arm runtime static bias와 0.5 rad target-delta cap도 기준의 0 bias/0.15 rad에서 바꿨다. 이후 `seed120_palm_feedback_v2`에는 runtime palm/world-position feedback도 추가됐다. 따라서 아래 표는 조건 묶음의 관측값이다.

## 저장 기타 오차

위치 오차는 millimetres, 회전 오차는 degrees다. “최대”와 종료값은 별도다.

| 저장 run | 구간 | 최대 위치 / 회전 | 종료 위치 / 회전 | LH–기타 contact 기록 |
|---|---:|---:|---:|---|
| baseline | 0.1 s | 4.035079 mm / 0.639349° | 4.035079 mm / 0.639349° | 0행 |
| seed + preload/hold | 0.1 s | 3.526166 mm / 0.638752° | 3.526166 mm / 0.638752° | 25행, step 14–22 |
| palm feedback short prefix* | 0.1 s | 3.150733 mm / 0.658176° | 3.150733 mm / 0.658176° | 32행, step 14–24 |
| `contact005` short attempt | 0.1 s | 3.048302 mm / 0.733724° | 3.048302 mm / 0.733724° | 42행, step 11–20 |
| baseline | 0.5 s | 18.740199 mm / 2.842119° | 16.043103 mm / 2.842119° | 0행 |
| seed + preload/hold | 0.5 s | 26.522614 mm / 3.497190° | 26.522614 mm / 3.497190° | 84행, steps 14–22 및 37–59 |
| palm feedback `v2` | 0.5 s | 16.170221 mm / 2.379811° | 16.155080 mm / 2.379811° | 206행, step 범위 14–120 (중간 소실 있음) |
| palm cap 0.30 rad | 0.5 s | 16.170221 mm / 2.379811° | 16.155080 mm / 2.379811° | `v2`와 trace/contact exact |
| baseline | 1.0 s | 20.341143 mm / 5.282789° | 20.341143 mm / 5.282789° | 0행 |
| palm feedback `v2` | 1.0 s | 16.170221 mm / 2.517144° | 15.322712 mm / 2.488597° | raw contact 마지막 step 131 |
| palm cap 0.30 rad | 1.0 s | 16.170221 mm / 2.517144° | 15.240242 mm / 2.454898° | raw contact 마지막 step 131 |

![저장 trace의 기타 위치·회전 오차, 0.5초 및 1초 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/artifacts_feedback_v2/guitar_error_feedback_hold.png)

0.5초 feedback `v2` 오차는 baseline보다 낮았지만, 같은 0.5초의 이전 finger-seed/preload/hold 조건은 더 높았다. 1초 `v2` 종료에서 기타 오차는 baseline보다 작지만 남아 있다. palm-cap 0.30 조건은 같은 1초 최대오차와 LH 접촉 마지막 step을 보였고, 종료오차만 `v2`보다 약 0.08247 mm 및 0.03370° 낮았다. 이 작은 차이만으로 cap 확대를 채택하지 않았다. `contact005` short run은 위치 오차가 작고 회전 오차가 큰 tradeoff라 연장하지 않았다.

*0.1초 “palm feedback short prefix” 값은 anti-windup 수정 전 `short/seed120_palm_feedback`의 raw다. 해당 0.1초 state/trace는 `hold_05s/seed120_palm_feedback_v2`의 prefix와 일치하지만, 별도 v2 short run은 아니다.

기록된 LH–기타 contact pair는 `G:fret10`–`LH:middle3`, `G:fret11`–`LH:ring3`, 나중에는 기타 root body–`LH:ring3`였다. 반대 엄지 접촉은 기록되지 않았고 LH:palm–기타 접촉도 없으므로 이를 완성된 grip으로 읽지 않는다.

1초 `v2`에서 raw LH contact rows는 step 131 (0.545833 s)까지 관찰됐고 이후 행은 없다. 양의 raw lambda의 마지막 step은 130 (0.541667 s)다. 접촉 행·lambda는 힘 단위, 지속적인 지지, 인과 또는 안정성 성공을 인증하지 않는다. native `LH:palm` link 원점의 최대 world 변위는 `v2` 31.381602 mm, baseline 100.702130 mm였다. `v2`의 종료 링크 원점 Z 변화는 −31.052768 mm이고 torso 최대 drift는 3.899911°였다. 위쪽 palm proxy 최소값 0.927708은 관측치일 뿐 해부학적 방향 인증이 아니다.

현재 진단 기준은 finger seed + preload + palm-feedback `v2`이며 안정화/연주 성공으로 선정하지 않는다. 0.30 rad cap 조건은 큰 최대오차 개선 없이 종료값만 조금 낮췄고 채택하지 않았다. 후속 방향은 엄지 opposing contact 및 상체 목표 drift를 별도 검토하는 것이며, 이 문서에서 새 제어 변경을 승인하지 않는다.

## Isaac Gym native camera 영상

![초기, 0.2초, contact 마지막 구간 직전, 종료의 native camera montage](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/native_camera_montage.png)

[전체 1초 저장 run의 0.2× native camera 영상 (61 frames, 12 fps)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/finger_grip_hold_0p2x.mp4)

두 시야는 Isaac Gym native camera가 저장한 전신/손 visual scene이다. 각 시점은 physics step 0부터 240까지 4 step 간격으로 61회 캡처했고, slow playback은 그 자료를 12 fps로 보여준다. 캡처 run의 trace/state/contact/control/torque 자료는 선택한 `hold_1s/seed120_palm_feedback_v2`와 byte-level JSON exact다. 그래픽 장치 id는 0, PhysX는 CPU이며 graphics backend identity는 조회되지 않았다. 이는 실제 camera visual render이지 MuJoCo source-geometry 재생은 아니지만, 충돌력·cooked collider·안정성 인증은 아니다.

## 재현과 원자료

feedback figure 재생성 시 기존 출력 폴더를 덮어쓰지 않도록 빈 경로를 사용한다.

```bash
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/finger_grip_feedback_mpl \
python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/plot_finger_grip_feedback.py \
  --out-dir /tmp/finger_grip_feedback_reproduction
```

저장 native camera frame의 montage/video post-process도 새 빈 출력 경로로 실행한다.

```bash
python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/render_finger_grip_video.py \
  --out-dir /tmp/finger_grip_video_reproduction
```

- 기존 0.5초 그림은 [plot_finger_grip_hold.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/plot_finger_grip_hold.py:1), summary는 [analysis_summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/artifacts/analysis_summary.json)에 있다.
- feedback 비교 plotter [plot_finger_grip_feedback.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/plot_finger_grip_feedback.py:1)는 저장 report/trace/control/contact JSON만 읽는다. [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/artifacts_feedback_v2/plot_manifest.json)는 입력/producer/output SHA를 기록한다. [실제 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/artifacts_feedback_v2/plot_execution.json)과 [stdout log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/logs/plot_feedback_execution_v2.log)도 보존했다.
- native camera 원본은 [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/frames/capture.json)과 그 frame PNG들이다. [video postprocessor](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/render_finger_grip_video.py:1)는 저장된 PNG만 합성한다. 실행·ffprobe·SHA는 [render execution](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/render_execution.json)과 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/render_manifest.json)에 있다.
- 이전 seed/preload raw는 [`hold_05s/seed120_preload050_hold`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/hold_05s/seed120_preload050_hold/report.json), feedback `v2`는 [`hold_05s`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/hold_05s/seed120_palm_feedback_v2/report.json)와 [`hold_1s`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/hold_1s/seed120_palm_feedback_v2/report.json)에 저장돼 있다. cap 0.30의 1초 자료는 [`hold_1s/seed120_palm_cap030`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/hold_1s/seed120_palm_cap030/report.json)에 있다.

- [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/CHANGED_FILES.md:1)에는 입력·산출 경로가 모여 있다. [VISUAL_REPORT §55](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1002)에는 그림·영상 설명이 있다. 별도 최종 검수는 [review.md:28](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/review.md:28)에 기록됐으며, Critical/Warning/Suggestion 지적사항은 없다.
