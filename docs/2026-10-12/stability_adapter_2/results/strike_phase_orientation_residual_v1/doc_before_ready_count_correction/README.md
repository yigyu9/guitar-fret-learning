# Phase별 방향 잔차 보정 진단

이 5초 진단은 현재 기타 자세를 기준으로 원본 READY/ENTRY/EXIT waypoint에 phase별 기하 잔차를 더하고, 오른팔 9축 FK·PI 목표에 bounded correction을 적용했다. 위치 residual scale은 1000, soft orientation residual scale은 5 mm/rad, joint regularizer는 3이다. source phase, detector, 시간, weights/RMS는 유지했다. 별도 source 방향 제한을 추가하거나 손바닥 접촉을 필수 조건으로 만들지 않았다.

실행은 1200 physics steps, 151 native camera frames, actor 251 steps로 완료됐다. 계약 검사 16개와 입력 closure 1029개가 통과했고 closure 변경은 0이다. PREPARE 49표본 뒤 0.816667초에 PLAY가 시작해 나머지 251표본까지 계속됐다. 실행 끝까지 HOLD나 source terminal은 없었다.

| 관측 | 결과 |
|---|---:|
| target hit / physical target hit / accepted release | 0 / 0 / 0 |
| physical release / miss / wrong crossing | 0 / 10 / 0 |
| 마지막 running strike F1 | 0 |
| guitar 범위 안 표본: 전체 / policy | 52/300 / 6/251 |
| 최소 준비점 거리: PREPARE / PLAY | 25.211255 / 6.379423 mm |
| 기타 위치 변화: 최대 / 종료 | 46.353646 / 31.995380 mm |
| 기타 회전 변화: 최대 / 종료 | 45.290342 / 43.959132° |

이 결과는 타현 유지 개선이나 연주 성공을 뜻하지 않는다. 준비 거리 10 mm 안 표본은 한 번 관측됐지만, 원본 READY의 6연속 frame 조건을 충족한 획득은 아니다. 이전 first-hit 실행은 actor 111 step 후 HOLD였고 이번 실행은 actor가 251 step 모두 PLAY에 있었다. 따라서 두 실행의 wrong-crossing 수를 보정 전후 성능 차이로 해석하지 않는다. 이번에 적용한 soft orientation 잔차는 READY/hit 관측을 개선하지 못해 채택하지 않았다. 이후에는 방향 잔차를 반복 추가하는 대신, 기존 source 회복 경로를 우선하는 별도 recovery-priority 단계를 시험했다. 그 결과는 [회복 우선 단계 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/README.md:1)에 별도로 정리했다.

## 실제 native 카메라 기록

프레임 00000, 00060, 00150은 각각 0, 2, 5초다. 아래는 저장된 native camera frame이며 재렌더하거나 source geometry로 만든 그림이 아니다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/whole_body/00060.png) | ![손 근접 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/hands.mp4)

## 자료와 구현

- [승인된 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/analysis.log)
- [native report 및 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/inputs_after.json:1)
- [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/videos.json:1) · [native 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native.log)
- [phase residual 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PHASE_ORIENTATION_RESIDUAL_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_phase_orientation_residual.py:24) · [보존 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_phase_orientation_preserved_run.py:12)
