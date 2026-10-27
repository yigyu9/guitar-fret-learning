# 닫힌 시간창 R9 READY 목표 actual-angle rebase 진단

이번 native 실행은 source phase 1의 `approach_open=false` 대기 구간에서 R9 목표를 실제 관절각을 기준으로 다시 계산했다. READY geometry 3을 향한 bounded IK correction을 actual angles에 적용하고, I는 유지했다. 대기 창이 열리면 기존 policy+PI로 돌아가며 RECOVERY에서는 previous actuator goal에 `2×delta`를 적용했다. damping schedule은 유지했다. 이는 goal scheduling 진단이며 관절 상태 자체를 덮어쓰지 않았다. [실행 코드의 대기 분기](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_wait_rebase.py:182), [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1).

실행은 5초, 1,200 physics steps, 151 camera frames, 21/21 checks 완료다. PREPARE/PLAY/HOLD는 49/178/73 control sample이고 닫힌 wait는 42 sample이다. native input closure 1,066개는 변경 0, 별도 analysis input 7개 파일도 before/after SHA가 동일하다. source는 wrong-crossing count로 3.783333초에 종료됐고, 이후 HOLD에서 physics와 기록을 계속했다. [요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/summary.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/report.json).

첫 음표 event 0, string 2 DOWN은 1.350000초에 timing +44.484798 ms로 timely hit였다. READY 1, timely target hit 1, physical target hit 1, accepted release mask 1이며 첫 scheduled recovery는 2.366667초에 완료됐다. 후속 wrong crossing 4회 뒤 source가 종료됐다. Native 집계의 physical release는 4, miss 6, partial F1은 0.166666672다. 이 F1은 조기 종료된 부분 노출의 metric이다. timely hit 1건만 시간 기준 성공으로 기록하며 실행 전체나 완성된 연주의 성공으로 취급하지 않는다.

대기 중 실제 pick의 guitar-local z는 2.750000초에 97.983354 mm였다. 이때 READY reference geometry z는 20.3 mm였으므로 실제 pick은 reference 위쪽으로 벗어나 있었다. 이는 저장된 native trajectory의 한 시점 관측이며, goal rebase가 만든 인과효과나 task의 acoustic/contact force 측정은 아니다. 기타 최대/종료 회전 변화는 7.095455°/5.416182°, 위치 변화는 46.353646/39.772717 mm다. playable-region 표본은 제어 283/300, policy 164/178이며 `music_success=false`, learning updates 0이다.

현재 phase의 before/after prefix 비교 산출물과 독립 최종 검수는 아직 작성 전이다. 이후 대조가 완료되기 전에는 앞선 timed-wait-priority 결과와의 prefix 동일성을 주장하지 않는다.

## 저장된 native 영상

아래는 이번 실행의 Gym native 카메라 영상과 대표 프레임이다. 두 영상은 각각 151 frames, 30 fps, stream duration 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/frames/hands/00150.png) |

![전신 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/whole_body.mp4)

![손 근접 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/hands.mp4)

## 입력·실행 기록

[Native inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/inputs_before.json), [native closure after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/inputs_after.json), [analysis input SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/inputs_before.json), [analysis input SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/inputs_after.json), [PD phase properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/PD_phase_properties.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/initial_audit.json), [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/initial_values.json), [capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/videos.json).
