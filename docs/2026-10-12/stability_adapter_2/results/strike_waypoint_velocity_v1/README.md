# Strike waypoint velocity v1

이 5초 native 진단은 원본 strike waypoint와 source 판정 조건을 유지하면서, phase 0 READY·닫힌 phase 1 APPROACH·phase 2 RECOVER에서만 현재 기타 좌표계의 실제 RH:pick 위치 차분으로 만든 제한된 속도 보정을 IK 목표에 더했다. 열린 APPROACH는 기존 policy+PI가 소유한다. 보정은 표본 속도 기반의 servo 목표 조정이며 순간 속도나 타현 인과관계를 인증하지 않는다. [목표·phase 분기 구현](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:157), [속도 및 보정 계산](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:173), [계획과 제한](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_WAYPOINT_VELOCITY_PLAN.md:5).

**결과: 적시 타현 및 완성 연주 성공 미달.** Native 실행은 1,200 physics steps, 151 camera frames, 24/24 contract checks로 5초까지 끝났다. 입력 closure 1,100개는 모두 unchanged였고, 분석 입력 7개와 velocity audit 입력 6개의 SHA도 각각 유지됐다. PREPARE/PLAY/HOLD는 49/239/12 control samples이며 source phase 0·1·2가 모두 기록됐다. Source wrong-crossing 종료는 4.8초였지만 HOLD에서 physics와 camera 기록은 5초까지 계속됐다. 학습 update는 0이다.

두 번의 physical hit은 있었지만 둘 다 적시 target hit이 아니었다. 1.483333초의 첫 physical·accepted hit은 zero-based event 1, string 2 DOWN으로 −107.446640 ms 일렀고, 2.616667초의 다음 hit은 event 3, string 2 DOWN으로 −191.687698 ms 일렀다. 따라서 timely target hit은 0이다. 합계는 physical target hit 2, accepted release mask 2, physical release 6, miss 9, wrong crossing 4다. 일반 recovery pulse는 1.716667초와 2.816667초, scheduled recovery 완료 pulse는 2.0초와 3.6초에 기록됐다. 두 회복 진전에도 적시 타현은 없었고 full-song 성공으로 해석할 수 없다.

기타 최대/종료 회전 변화는 9.242948°/5.682394°, 위치 변화는 46.353646/44.526546 mm였다. Playable region 표본은 전체 control 216/300, PLAY policy 158/239였고 최소 PLAY policy pick-to-READY 거리는 0.416931 mm였다. 이 값들은 실행 중 저장된 궤적 요약이며 원인 판정은 아니다.

[Velocity goal audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/velocity_goal_audit.json)는 6개 입력 SHA 불변, PREPARE control 49개와 sampled native prefix 25개 일치, 첫 actor observation/action exact를 확인했다. 저장된 239개 유한 속도 기록의 차분 공식 최대 오차는 0, 적용 보정 공식 최대 오차는 0이며 보정 크기는 최대 5 mm였다. sampled native pick anchor 119개를 확인했다. 이는 감사된 goal 산식과 표본 prefix 범위에 한정되며 전체 궤적 동일성, 접촉 인과성, source drive 동등성 또는 연주 성공을 인증하지 않는다.

## 실행 및 저장 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/report.json), [native closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/inputs_after.json): 실행 횟수, 24개 check, terminal, 카메라 및 input closure.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/analysis/summary.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/analysis/inputs_after.json): pulse·phase·region·pose 요약과 분석 입력 SHA.
- [Velocity goal audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/velocity_goal_audit.json): 목표 소유권, finite difference 및 제한 보정 산식, 비교 prefix.
- [Initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/initial_audit.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/checkpoint_connection.json): 시작 상태 및 frozen checkpoint 연결 자료.
- [Native controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/trace.json): controls 300행, native trace 152행. Trace는 8-step grid 표본 151행에 terminal 시점 4.8초·physics step 1152의 PLAY/HOLD 행이 함께 있어 같은 step/time이 중복된다. Camera frame은 별도 151장이다. [Capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/capture.json)와 [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/videos.json)에서 frame provenance를 확인할 수 있다.
- [Runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_waypoint_velocity.py:157), [실험 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_WAYPOINT_VELOCITY_PLAN.md:1).

## 저장된 native capture

아래 정지 이미지는 30 fps native camera frame이다. 첫 타현 control 시각 1.483333초와 정확히 일치하는 카메라 프레임은 없으며, 표에는 가장 가까운 1.466667초(frame 44)를 표시했다. 2초 및 5초 frame도 camera 시각이다. 5초 frame은 4.8초 source terminal 이후 HOLD 중 저장됐다. 두 영상은 각각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 native frame | 손 native frame |
|---|---|---|
| 0초, 초기 상태 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/hands/00000.png) |
| 1.466667초, 첫 physical/accepted hit에 가장 가까운 camera frame | ![전신 1.466667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/whole_body/00044.png) | ![손 1.466667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/hands/00044.png) |
| 2초, PLAY | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/hands/00060.png) |
| 5초, source terminal 뒤 HOLD·physics 지속 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/frames/hands/00150.png) |

![전신 native video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/whole_body.mp4)

![손 native video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_waypoint_velocity_v1/native/data/images/hands.mp4)
