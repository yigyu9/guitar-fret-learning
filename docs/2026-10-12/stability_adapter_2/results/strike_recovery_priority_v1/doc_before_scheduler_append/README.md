# 타현 뒤 회복 경로 우선 제어 진단

이 진단은 기존 READY와 첫 타현 경로를 유지하고 source phase 2의 recovery 동안에만 오른팔 9축 목표의 우선순위를 바꿨다. 현재 pick과 원본 clearance waypoint 간 오차로 계산한 FK 증분을 이전 오른팔 목표에 더하고, 0.5 gain과 기존 ±0.15 rad delta 제한을 적용했다. 손가락 21축은 frozen policy, Thorax 3축과 나머지 목표는 기존 설정을 유지했다. source phase, READY/ENTRY/EXIT/clearance waypoint, release latch, detector, 시간, weights/RMS를 덮어쓰지 않았다.

5초 native 실행은 1200 physics steps, 151 camera frames, 계약 검사 16/16, 입력 closure 1032/1032 변경 없음으로 완료됐다. PREPARE는 49표본, PLAY는 182 actor steps, source terminal 이후 HOLD는 69표본이었다. source terminal은 3.85초였으며 물리 기록은 5초까지 계속됐다.

| 관측 | 결과 |
|---|---:|
| target hit / physical target hit / accepted release | 1 / 1 / 1 |
| physical release / miss / wrong crossing | 5 / 7 / 4 |
| 마지막 partial running strike F1 | 0.153846 |
| 범위 참 표본: 전체 / policy | 229/300 / 126/182 |
| 최소 준비점 거리: PREPARE / PLAY / HOLD | 25.211255 / 1.931564 / 12.290379 mm |
| 기타 위치 변화: 최대 / 종료 | 46.353646 / 40.366381 mm |
| 기타 회전 변화: 최대 / 종료 | 9.019638 / 5.485612° |

2.483333초에 string 2의 실제 hit과 accepted release가 기록됐고, 기존 측정 타이밍 오차는 45.179844 ms였다. recovery clearance는 2.883333초에 lifted, 3.266667초에 reached가 기록됐으며 같은 시점에 scheduled recovery-complete pulse가 참이 됐다. source phase는 3.35초에 2에서 1로 전이했다. recovery 구간에서 잘못된 release는 없었지만, 전체 실행에는 miss 7회와 wrong crossing 4회가 남았고 3.85초에 source terminal이 발생했다. 따라서 회복 경로의 한 성공 관측이지, 곡 전체 완료나 연주 성공은 아니다.

## 실제 native 카메라 기록

프레임 00000, 00060, 00150은 0, 2, 5초이며 각 영상은 151 frames, 30 fps, ffprobe stream duration 5.033333초다. 3.85초 이후 HOLD 중에도 물리 및 카메라 기록은 5초까지 이어진다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/whole_body/00060.png) | ![손 근접 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/hands.mp4)

## 자료와 구현

- [승인된 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/analysis.log)
- [native report/검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/inputs_after.json:1)
- [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/videos.json:1) · [native 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native.log)
- [회복 우선 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_PRIORITY_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_recovery_priority.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_recovery_priority_preserved_run.py:12)
