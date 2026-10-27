# 자동 시작 5초 진단

이 진단은 고정 2초 대기 없이 현재 ready 거리 25 mm 이하, 기존 초기 준비 조건, 기타 playable-region 조건이 함께 참일 때 source 정책을 연결했다. 원본 source의 10 mm/6연속 표본 READY와 motor detector는 변경하지 않았다. 실행은 5초/1200 physics steps를 끝까지 기록했고 15개 실행 계약과 입력 closure 검사를 통과했다.

## 관측 결과

| 기록 | 값 |
|---|---:|
| 전체 physics steps / actor steps | 1200 / 251 |
| phase 시작 / PLAY 시작 | `PREPARE` / 0.8166667초 |
| PLAY 중 최소 준비점 거리 | 10.766370 mm |
| 준비 범위 참 제어 표본 | 103/300 |
| 정책 중 범위 참 표본 | 57/251 |
| 기타 위치 변화 최대 / 5초 종료 | 46.353646 / 29.535285 mm |
| 기타 회전 변화 최대 / 5초 종료 | 46.860685 / 45.653964° |
| source motor phase 관측 | `[0]` |
| source target hit / physical target hit / accepted release | 0 / 0 / 0 |
| physical release / miss / wrong crossing | 2 / 10 / 2 |

정책 actor는 실행됐지만 인정 target hit과 accepted release는 0이며, 원본 source READY 10 mm/6연속 표본 gate는 그대로 유지됐다. 따라서 시작 gate 통과 자체를 타현·운지·연주 성공으로 해석하지 않는다. 정책 중 범위 안 표본은 57/251이었고, 기타 위치·회전 변화도 기록 시간 전체에서 각각 최대 46.353646 mm와 46.860685°였다. 이 결과는 시작 시점을 앞당긴 단일 진단이며 지속 연주 성능을 인증하지 않는다.

시작 gate 판정 표본은 phase 전이 시점의 값이고, 요약의 PREPARE/PLAY 최소 거리 집계는 각 phase에 분류된 표본 기준이다. 전이 표본은 PLAY로 분류되므로 서로 다른 집계값을 같은 시점의 값으로 해석하지 않는다.

## 실제 native 카메라 자료

각 프레임은 실제 native 카메라 출력이며, index `00000`, `00060`, `00150`은 0초·2초·5초다. 두 영상은 각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![automatic-start 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/whole_body/00000.png) | ![automatic-start 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![automatic-start 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/whole_body/00060.png) | ![automatic-start 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![automatic-start 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/whole_body/00150.png) | ![automatic-start 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/frames/hands/00150.png) |

![automatic-start 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/whole_body.mp4)

![automatic-start 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/hands.mp4)

## 원자료와 구현 색인

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/analysis.log) · [native report/checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/report.json:1)
- [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/checkpoint_connection.json:1) · [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/trace.json:1)
- [native 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/inputs_before.json:1) · [native 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/inputs_after.json:1) · [capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/capture.json:1) · [영상 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native/data/images/videos.json:1) · [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/native.log)
- [자동시작 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_AUTOMATIC_START_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_automatic_start.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_automatic_preserved_run.py:12)
- [메인 PLAN 경과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:232) · [메인 README 경과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1537)
