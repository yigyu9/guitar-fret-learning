# 원본 접근 시간에 맞춘 adapter EXIT 진단

이 실행은 adapter가 entry latch를 얻자마자 EXIT waypoint로 바뀌던 조건에 source의 원래 `approach_open` 시점을 추가했다. EXIT 선택은 adapter 안에서만 entry latch와 원본 source clock·offset·approach lead가 함께 충족될 때 허용한다. source phase, clock, flag, detector, latch, weight는 덮어쓰지 않았다. RECOVER 증분 gain 2와 나머지 실행 설정은 직전 조건 그대로다.

5초 native 실행은 1200 physics steps, 151 camera frames, 계약 검사 17/17, 입력 closure 1044개 변경 없음으로 완료됐다. PREPARE 49표본 뒤 0.816667초에 PLAY가 시작해 actor는 251 steps를 수행했다. 5초 동안 source terminal이나 HOLD는 없었다.

| 관측 | 결과 |
|---|---:|
| target hit / physical target hit / accepted release | 1 / 1 / 1 |
| physical release / miss / wrong crossing | 3 / 9 / 2 |
| 마지막 partial running strike F1 | 0.153846 |
| 범위 안 표본: 전체 / policy | 241/300 / 195/251 |
| 최소 준비점 거리: PREPARE / PLAY | 25.211255 / 3.240488 mm |
| 기타 위치 변화: 최대 / 종료 | 46.353646 / 36.279258 mm |
| 기타 회전 변화: 최대 / 종료 | 9.074870 / 6.594995° |
| source terminal / HOLD | 없음 / 없음 |

hit은 2.783333초 event 3의 string 2 DOWN에서 발생했고 공식 timing error는 −33.181908 ms였다. 이는 이전 단계의 2.483333초 event 2 hit과 다른 scheduled event이므로 두 timing 값을 같은 타현 비교로 취급하지 않는다. 저장 기록에서 adapter EXIT 활성 표본 21개 모두 source `approach_open` 이후였고, 열리기 전 활성은 0이었다. 이 실행은 5초 동안 PLAY에 머물렀으나 full-song completion은 아니며, RECOVER clearance는 4.583333초에 lifted만 기록되고 reached와 scheduled completion은 5초 내에 관측되지 않았다. RECOVER gain은 직전 조건과 같고 초기 경로도 달라졌으므로 결과를 gain 단독 효과로 설명하지 않는다.

## 실제 native 카메라 자료

프레임 00000, 00060, 00150은 각각 0, 2, 5초다. 전신과 손 근접 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00060.png) | ![손 근접 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/hands.mp4)

## 자료와 구현

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/analysis.log)
- [native report/검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/inputs_after.json:1)
- [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/videos.json:1) · [native 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native.log)
- [timed EXIT 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_EXIT_PLAN.md:1) · [runner 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_exit.py:25) · [EXIT 시간 gate](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_exit.py:136) · [보존 wrapper 진입점](/home/ajou/yigyu/3/stability_adapter_2/strike_timed_exit_preserved_run.py:12)
