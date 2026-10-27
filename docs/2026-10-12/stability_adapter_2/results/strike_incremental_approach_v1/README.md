# Strike incremental approach v1

이 5초 native 진단은 열린 APPROACH에서 오른팔 R9의 source policy 목표 대신 `이전 제출 목표 + 2δ`의 기타 기준 증분 목표를 사용했다. READY, 닫힌 APPROACH, RECOVER도 같은 증분 목표를 사용한다. 적분 상태는 모든 phase에서 0으로 유지했고, R9 policy 목표는 기록용이다. 손가락 21개 목표는 actor policy가 소유하며, free-finger 4개에는 기존 +0.2 rad residual을 적용했다. 타현 기준·source phase·timing·recovery 경로는 유지했다. [목표 소유권 구현](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:194), [source phase와 기타 기준 목표](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:157), [실험 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_INCREMENTAL_APPROACH_PLAN.md:5).

**음악 구간에서는 네 번의 적시 타현을 기록했지만, 완성 연주 성공은 아니다.** Native 실행은 1,200 physics steps, 151 camera frames, 24/24 checks로 5초까지 완료했다. Native input closure 1,103개와 analysis input 7개, all-phase goal audit input 6개의 SHA가 unchanged였다. PREPARE/PLAY/HOLD는 49/169/82 control samples이고 actor는 PLAY에서 169 steps를 실행했다. Source phase 0·1·2가 기록됐으며, learning updates는 0이다.

첫 열린 APPROACH는 1.283333초였다. 그 전 controls 77개와 sampled native state 39개, 첫 open actor observation/action이 직전 waypoint-velocity phase와 exact 일치했다. [All-phase goal audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/allphase_goal_audit.json)은 전체 169 PLAY goal의 `previous_goal + 2δ` 오차 최대 5.9541e−8 rad, velocity 및 feedback 산식 오차 0, feedback 최대 5 mm, 84 sampled native pick anchors를 기록했다. 감사 범위는 계산된 goal 및 표본 prefix이고, 전체 궤적 동등성이나 접촉 인과성 증명은 아니다.

적시 physical·accepted hit 네 번은 모두 string 2 DOWN이었다: zero-based event 0 at 1.316667초(+16.481113 ms), event 1 at 1.583333초(−17.500996 ms), event 2 at 2.433333초(−0.714421 ms), event 3 at 2.816667초(−3.153205 ms). Scheduled recovery 완료 pulse도 1.516667, 1.8, 2.65, 3.25초에 각각 기록됐다. 합계는 timely/physical/accepted hit 각 4, physical release 8, miss 2다.

그 뒤 wrong crossing 네 번이 3.466667, 3.483333, 3.5, 3.616667초에 기록돼 source가 3.633333초에 terminal 됐다. 이는 4.0초 이후의 HOLD 안정성이나 전체 곡 완주를 뜻하지 않는다. Source terminal 뒤에도 physics와 camera 기록은 5초까지 이어졌고 HOLD에서 기타 회전 변화가 계속 증가했다. 3.633333초 이후 native trace에는 physics step 872/time 3.633333의 PLAY/HOLD 중복 terminal 표본이 있어 trace는 152행이다. Camera frame은 별도 151장이다.

전체 run의 기타 최대/종료 회전 변화는 43.828938°/43.582017°, 최대/종료 위치 변화는 46.353646/28.668464 mm다. 회전 변화는 terminal 뒤 HOLD에서 커져 4.0초 25.834587°, 4.5초 43.640884°였다. Playable region 표본은 전체 control 153/300, PLAY policy 107/169였다. PLAY 중 168/169 samples는 noncontact였다. 저장된 contact row에서 RH:pinky3와 기타의 첫 positive-lambda 접촉은 3.633333초에 나타났고 최대 lambda는 24.441927이었다; RH:thumb3 접촉은 뒤에 기록됐다. 이 접촉은 terminal 시각과 겹친 저장 관측일 뿐, wrong crossing이나 회전 변화의 원인으로 판정하지 않는다.

따라서 이 phase는 네 번의 적시 타현과 scheduled recovery를 보였지만 wrong-crossing terminal로 끝났으며 full-song success는 아니다. Root는 다음 단일 요인 단계에서 음악 prefix를 보존하며 terminal 뒤 안전 후퇴만 비교하는 계획을 진행 중이고, 그 이후 별도로 UP 오류 개선을 검토할 예정이다. 이는 현재 결과에 포함된 실행이나 효과가 아니다.

## 실행·분석 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/report.json), [native closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/inputs_after.json): 1,200 steps·151 camera frames·24 checks·5초 완료 및 input closure.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/analysis/summary.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/analysis/inputs_after.json): hit·phase·region·pose 집계와 analysis SHA.
- [All-phase goal audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/allphase_goal_audit.json): audit input 6개 SHA, velocity phase와의 prefix 비교, goal ownership 산식 검증.
- [Native initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/initial_audit.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/checkpoint_connection.json): 시작 상태 및 checkpoint provenance.
- [Native controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/trace.json): control 300행, native trace 152행과 terminal 중복 sample.
- [Capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/videos.json): native camera provenance.
- [Runner goal/phase logic](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:157), [position-goal ownership](/home/ajou/yigyu/3/stability_adapter_2/run_strike_incremental_approach.py:194), [plan](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_INCREMENTAL_APPROACH_PLAN.md:1).

## Native 전신·손 capture와 영상

이미지는 저장된 30 fps native camera frame이다. 1.333333초 frame 40은 첫 적시 hit(1.316667초) 직후에 가장 가까운 capture다. 2.833333초 frame 85는 네 번째 적시 hit(2.816667초) 직후다. 3.633333초 frame 109는 wrong-crossing terminal 시각과 같은 camera 시각이며, 5초 frame 150은 terminal 뒤 HOLD 상태다. 두 MP4는 각각 151 frames, 30 fps, 5.033333초다.

| 카메라 시각 | 전신 | 손 |
|---|---|---|
| 1.333333초, 첫 적시 hit 직후 | ![전신 1.333333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/whole_body/00040.png) | ![손 1.333333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/hands/00040.png) |
| 2.833333초, 네 번째 적시 hit 직후 | ![전신 2.833333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/whole_body/00085.png) | ![손 2.833333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/hands/00085.png) |
| 3.633333초, wrong-crossing terminal | ![전신 3.633333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/whole_body/00109.png) | ![손 3.633333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/hands/00109.png) |
| 5초, terminal 뒤 HOLD | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/frames/hands/00150.png) |

![Native whole-body video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/whole_body.mp4)

![Native hand video, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/images/hands.mp4)
