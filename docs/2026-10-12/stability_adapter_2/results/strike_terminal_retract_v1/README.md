# Strike terminal retract v1

이번 5초 진단은 원본 연주 구간이 wrong-crossing terminal로 끝난 뒤, 기타 좌표계에서 실제 RH:pick을 위쪽으로 회수하는 R9 bounded IK 목표를 HOLD에 추가했다. 회수는 사람 팔 관절 목표만 바꾸며 기타 pose/힘을 직접 쓰거나 손을 기타에 붙이지 않는다. Source clock/history와 나머지 72개 관절 목표는 HOLD 동안 고정하고, phase0·1·2 연주 구간의 목표·타현·recovery 조건은 바꾸지 않았다. [HOLD 회수 목표와 실제 위치 feedback](/home/ajou/yigyu/3/stability_adapter_2/run_strike_terminal_retract.py:300), [R9 목표 적용과 나머지 목표 고정](/home/ajou/yigyu/3/stability_adapter_2/run_strike_terminal_retract.py:318), [단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TERMINAL_RETRACT_PLAN.md:1).

**현재 비교에서 가장 나은 부분 결과지만, 완성 연주 성공은 아니다.** Native 실행은 1,200 physics steps, 151 camera frames, 26/26 checks로 5초까지 완료했다. Native input closure 1,106개, analysis input 7개, terminal retraction audit input 8개의 SHA가 unchanged였다. PREPARE/PLAY/HOLD control samples는 49/169/82이고 actor는 PLAY에서만 169 steps를 실행했다. 학습 update는 0이다.

음악 구간은 직전 incremental-approach phase와 terminal까지 exact하게 같았다. [Terminal retraction audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/terminal_retraction_audit.json)은 PREPARE/PLAY controls 218개 전체 JSON, terminal까지 native trace 111개, actor observation/action 포함 비교를 확인했다. 따라서 네 적시 hit과 이후 잘못된 crossing 네 번은 이번 HOLD 회수로 바뀐 결과가 아니다. 적시 physical/accepted hit은 zero-based events 0–3, string 2 DOWN으로 네 번이며, scheduled recovery 완료도 1.516667/1.8/2.65/3.25초 네 번이다. Physical release 8, miss 2다. Wrong crossing 네 번은 3.466667/3.483333/3.5/3.616667초에 이어졌고 source는 3.633333초에 terminal 됐다. [앞 단계 incremental-approach 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/README.md:1)와 음악 구간을 분리해 읽어야 한다. 전체 곡 성공은 아니다.

Terminal 시각의 첫 HOLD 표본에서 실제 pick은 기타 좌표계 `Gz = −0.244896 mm`였고, 회수 anchor는 같은 XY에 `Gz = 50.3 mm`로 설정됐다. 이후 HOLD에서도 bounded 위치 feedback으로 R9 목표를 갱신했다. Source clock/history와 다른 72개 목표는 고정됐고, native POSITION damping은 원본값으로 돌아와 81개 속성이 정확히 readback됐다. PD schedule 기록은 총 10개(기존 phase 기록 9개와 terminal restore 1개)다. HOLD 82개 goal 공식과 rate limit이 exact했고, 41개 sampled native pick anchor를 확인했다. 이 회수는 terminal 뒤 실제 물리가 멈춘 상태를 뜻하지 않는다.

HOLD 최대 기타 회전 변화는 4.624625°였으며 전체 실행 최대/종료 회전 변화는 7.095455°/2.720263°였다. 최대/종료 위치 변화는 46.353646/27.763443 mm다. 직전 phase 전체 실행 회전 최대/종료는 43.828938°/43.582017°였지만, 두 phase의 음악 prefix는 exact하게 같다. 따라서 전체 최대 회전 개선은 terminal 뒤 HOLD 구간에 한정된다. Playable-region 표본은 전체 control 225/300, PLAY policy 107/169였고 HOLD noncontact는 80/82였다.

저장 contact 자료에서 positive RH-guitar contact는 첫 HOLD 표본 3.633333초의 RH:pinky3 한 행(lambda 24.441927)에만 나타났다. 이는 terminal과 회수 시작 시각에 겹친 관측이며 인과 효과를 증명하지 않는다. 엄격한 접촉 gate도 사용하지 않았다. [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/report.json)은 `music_success=false`이고 source terminal 이후에도 physics가 5초까지 진행됐음을 기록한다.

Root는 별도 후속 후보로 UP 방향 오류를 다루기 전에 4 mm 측방 staging을 검토 중이다. 이는 현재 실행의 조작이나 검증 범위에 포함되지 않았다.

## 실행·분석 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/report.json), [native closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/inputs_after.json): 1,200 steps·151 camera frames·26 checks·1,106 unchanged inputs.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/analysis/summary.json), [inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/analysis/inputs_before.json), [inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/analysis/inputs_after.json): pulse·phase·pose 요약과 analysis input 7개 SHA.
- [Terminal retraction audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/terminal_retraction_audit.json): 8 input SHA, prefix exactness, PD restore, HOLD goal formulas 및 sampled anchors.
- [Native controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/trace.json): 300 control rows 및 terminal 중복 표본을 포함한 152 trace rows. Physics step 872/time 3.633333초의 PLAY/HOLD 두 행은 같은 terminal sample이며 camera frame 수와 다르다.
- [Native initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/initial_audit.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/checkpoint_connection.json), [PD properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/PD_phase_properties.json): 시작 상태·checkpoint·damping readback.
- [Capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/videos.json): frame 시각 및 영상 provenance.
- [HOLD retraction implementation](/home/ajou/yigyu/3/stability_adapter_2/run_strike_terminal_retract.py:300), [source terminal gate and HOLD loop](/home/ajou/yigyu/3/stability_adapter_2/run_strike_terminal_retract.py:274), [plan](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TERMINAL_RETRACT_PLAN.md:1).

## 저장된 native 전신·손 capture

정지 이미지는 native camera frame이다. 1.333333초 frame 40은 첫 적시 hit 이후, 3.633333초 frame 109는 source terminal 및 첫 HOLD 회수 표본 시각, 5초 frame 150은 HOLD 지속 상태를 담는다. 두 MP4는 각각 151 frames, 30 fps, 5.033333초다.

| 카메라 시각 | 전신 | 손 |
|---|---|---|
| 0초, 초기 상태 | ![전신 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/whole_body/00000.png) | ![손 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/hands/00000.png) |
| 1.333333초, 첫 적시 hit 이후 | ![전신 1.333333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/whole_body/00040.png) | ![손 1.333333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/hands/00040.png) |
| 3.633333초, source terminal·HOLD 시작 | ![전신 terminal 시각](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/whole_body/00109.png) | ![손 terminal 시각](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/hands/00109.png) |
| 5초, HOLD 물리 지속 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/frames/hands/00150.png) |

![전신 native video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/whole_body.mp4)

![손 native video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/images/hands.mp4)
