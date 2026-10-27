# Phase-target READY 잔차 5초 진단

기존 READY P/I와 source 정책을 유지하면서 source phase에 따라 기타 기준 READY·ENTRY·EXIT 기하 오차를 오른팔 9축의 bounded PI 보정에 더한 단일 진단이다. 실제 PREPARE/PLAY/HOLD 구분은 [교정 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/analysis_phase_corrected/summary.json:1)을 기준으로 한다. 이전 분석 summary는 보존되어 있으며, 교정 분석은 phase별 제어 표본을 분리해 기록한다.

실행은 5초/1200 physics steps와 151 native camera frames를 완료했다. 16개 계약 검사와 1025개 입력 closure 검사가 통과했고 closure 변경은 0이다. 제어 기록은 PREPARE 49, PLAY 111, HOLD 140 표본으로 나뉜다. PLAY actor는 0.816667초에 시작해 111 actor steps 실행했고, source wrong-crossing terminal은 2.666667초에 발생했다. 이후에는 source 정책 actor가 아니라 HOLD 목표를 유지하면서 native 물리 기록을 5초까지 계속했다.

## 주요 관측

| 지표 | 결과 |
|---|---:|
| source terminal / phase | 2.666667초 / `HOLD` |
| target hit / physical target hit / accepted release | 1 / 1 / 1 |
| physical release / miss / wrong crossing | 5 / 2 / 4 |
| 마지막 partial running strike F1 | 0.25 |
| 범위 참 전체 제어 / PLAY 표본 | 143/300 / 66/111 |
| 최소 준비점 거리: PREPARE / PLAY / HOLD | 25.211255 / 3.240488 / 13.844196 mm |
| 기타 위치 변화 최대 / 5초 종료 | 46.353646 / 28.357006 mm |
| 기타 회전 변화 최대 / 5초 종료 | 44.171368 / 43.983681° |

실제 target hit 1건은 기록됐지만, full-song completion이나 연주 성공은 아니다. 1.033333초에는 READY phase 0에서 string 3 physical release와 `release_phase_violation=true`가 기록됐다. 이후 2.483333초에는 string 2 hit이 기록됐고, 해당 hit의 `info.timing_error_ms`는 45.17984390258789 ms였다. source recovery 기록에서 `recovery_clearance_required=true`, `recovery_clearance_lifted=false`, `recovery_clearance_reached=false`였다. 2.533333초 이후 recovery 중에도 잘못된 crossing이 이어져 source wrong-crossing-count terminal로 전환됐다. clearance 획득/회복은 해결되지 않았다.

Adapter는 source phase·entry 판정·타현 detector·시간·weights를 덮어쓰지 않는다. 실제 pick이 original entry 거리 안에 들어온 것을 확인해 adapter waypoint를 EXIT으로 바꾸고, RECOVERY에서는 source의 exit/clearance 기하를 따른다. 이는 모델 기반 phase-target 보정 진단이며 pure checkpoint 성능 평가가 아니다. 손바닥 접촉 지속은 필수 gate가 아니고, root·하체·기타 외력이나 state overwrite는 사용하지 않았다.

## 실제 native 카메라 자료

프레임 index `00000`, `00060`, `00150`은 0초·2초·5초다. 전신 및 손 근접 native 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다. 영상은 5초까지 이어지지만 source actor는 2.666667초 terminal 이후 HOLD였다.

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![phase-target 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/whole_body/00000.png) | ![phase-target 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![phase-target 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/whole_body/00060.png) | ![phase-target 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![phase-target 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/whole_body/00150.png) | ![phase-target 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/frames/hands/00150.png) |

![phase-target 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/whole_body.mp4)

![phase-target 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/hands.mp4)

## 원자료와 구현 색인

- [교정 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/analysis_phase_corrected/summary.json:1) · [교정 분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/analysis_phase_corrected.log) · [기존 분석 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/analysis/summary.json:1)
- [native report/검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/inputs_after.json:1)
- [capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/capture.json:1) · [video metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/videos.json:1) · [native log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native.log)
- [phase-target 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PHASE_TARGET_RESIDUAL_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_phase_target_residual.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_phase_target_preserved_run.py:12)
