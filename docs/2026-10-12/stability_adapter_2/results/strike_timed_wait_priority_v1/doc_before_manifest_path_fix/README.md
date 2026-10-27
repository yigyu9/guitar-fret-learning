# 닫힌 source 창의 R9 READY 목표 소유권 진단

이 native 진단은 source phase 1이지만 `approach_open=false`인 닫힌 시간창에서만 adapter가 R9 READY 증분 목표를 소유하게 했다. 22개 대기 command에서 actual I는 유지했고 READY geometry 3을 사용했다. R9 goal은 previous goal에 bounded IK correction의 2배를 더하는 방식이었다. source phase·clock·timing 판정은 강제하지 않았고, phase 1 damping 0.25배 및 phase 0/2 baseline schedule을 유지했다. [실행기와 대기 owner 기록](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_wait_priority.py:123), [다음 rebase 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1).

5초 실행은 1,200 physics steps, 151 camera frames, 21/21 checks로 완료됐다. native 입력 closure 1,063개는 변경 0이며, 별도 분석기 입력 7개 파일도 before/after SHA가 동일하다. PREPARE/PLAY/HOLD는 49/130/121 control sample이었다. source는 wrong-crossing count로 2.983333초 terminal 됐고 그 뒤 HOLD에서 physics 및 기록을 이어갔다. [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/summary.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/report.json).

첫 음표(event index 0) string 2 DOWN의 timely hit는 1.350000초, timing +44.484798 ms였다. READY 1, timely target hit 1, physical target hit 1, accepted release mask 1이었다. 첫 scheduled recovery는 2.366667초에 완료됐다. Physical release 5, miss 3, wrong crossing 4, partial F1=0.222222239다. 최초 READY wrong crossing은 1.033333초 string 3이며 그 sample의 raw `physical_release_direction`은 +1이다. 이후 source phase 1에서 2.716667초 string 2, 2.950000초 string 3, 2.966667초 string 4에서 wrong crossing이 발생했으며, 각 sample의 raw `physical_release_direction`은 −1이다. 따라서 wrong crossing 전체가 같은 방향 code였던 것은 아니다. source는 마지막 crossing 뒤 종료됐다.

기타 최대/종료 회전 변화는 8.126144°/5.421837°, 위치 변화는 46.353646/41.235741 mm다. playable-region 표본은 제어 235/300, policy 120/130이다. 이는 해당 waypoint/goal scheduling을 사용한 한 saved trajectory의 결과다. 목표 소유권 방식과 관측 성능의 연관은 보여주지만, 실제 trajectory에서 원인 단독효과나 기여를 증명하지 않는다. source의 geometry sensor 기반 hit는 물리적 현력이나 acoustic string vibration 측정이 아니다. `music_success=false`, learning updates 0이며 이 설정을 채택하거나 full-song 성공으로 판정하지 않는다.

다음 검토는 닫힌 source 창에서 R9 READY 목표를 actual angles 기준 IK fit으로 재기준화하는 단계다. [STRIKE_TIMED_WAIT_REBASE_PLAN](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1). 해당 계획은 아직 사전 검수 대기이며, 이 결과가 다음 단계를 완료했다는 뜻은 아니다.

## 저장된 native 영상

아래 영상과 대표 프레임은 완료된 이 실행의 Gym native camera recording이다. 각각 151 frames, 30 fps, stream duration 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/frames/hands/00150.png) |

![전신 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/whole_body.mp4)

![손 근접 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/hands.mp4)

## 기록 및 입력 closure

[Native input SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/inputs_before.json), [native closure after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/inputs_after.json), [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/inputs_before.json), [analysis SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/inputs_after.json), [phase별 native damping property](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/PD_phase_properties.json), [초기 상태 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/initial_audit.json), [프레임 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/capture.json), [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/videos.json).

## 첫 closed-window 명령 전 prefix 대조

[기존 대조기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/compare_before_wait.py)와 [결과 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/pre_wait_comparison.json)는 첫 closed-window command 시작 2.5초 전까지 직전 timed-ENTRY retry와 controls 150개 및 2.5초까지의 complete native-state trace 76개가 같고, 비교 입력 6개 SHA가 불변임을 기록한다. 첫 timely hit와 첫 scheduled recovery는 이 shared prefix 안에 있다. Manifest의 listed control keys는 command/observation/history/time 등의 선택 필드이므로 `info`를 포함하지 않는다. 별도로 두 저장 controls의 같은 150행에서 target/physical hit, release, miss, wrong count, clearance lifted/reached, scheduled recovery complete, event index와 timing 관련 `info` field를 읽어 비교했고 해당 값들이 일치했다. 이 추가 대조를 manifest가 비교했다고 표현하지 않는다. 이 결과는 shared prefix만 다루며 전체 1,200-step 상태가 같다는 뜻은 아니다. [대조 JSON 및 script](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/pre_wait_comparison.json).
