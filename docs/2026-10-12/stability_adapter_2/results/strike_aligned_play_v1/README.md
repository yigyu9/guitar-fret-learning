# Aligned-play 진단: 실제 준비점에서의 5초 기록

이 실행은 준비 목표를 stand-off 0으로 두고, 2초/80 mm handoff 시점에 source 정책을 연결하는 진단이었다. 다만 2초 시점의 current ready 거리는 17.874040 mm였어도 playable-region 회전 판정이 거짓이어서 actor는 한 step도 실행되지 않았다. 5초 동안 1200 physics steps와 native 영상을 기록했고 phase는 `PREPARE`에서 끝났다. 실행 계약 15개가 통과했으며 보존 대상 입력의 변경은 없었다.

## 관측 결과

| 기록 | 값 |
|---|---:|
| 전체 physics steps / actor steps | 1200 / 0 |
| phase 종료 / 정책 시작 | `PREPARE` / 시작하지 않음 |
| 준비점 거리 최소 | 17.060965 mm |
| 준비 범위 참 제어 표본 | 113/300 |
| 2초 handoff 표본 | 거리 17.874040 mm, playable region 거짓 |
| 기타 위치 변화 최대 / 5초 종료 | 46.353646 / 30.876120 mm |
| 기타 회전 변화 최대 / 5초 종료 | 7.095455 / 3.051304° |
| source target hit / physical target hit / accepted release | 0 / 0 / 0 |

회전 범위 검사는 등가 Euler 표현을 포함한 실제 membership 판정이다. 등가 각 표현이 달라 보인다는 이유만으로 gimbal 버그로 분류하지 않았고, 판정 범위를 사후 변경하지 않았다. 2초 표본은 준비점 거리만으로 정책 진입 여부를 결정할 수 없음을 보여준다. 원본 source의 10 mm/6연속 표본 READY 및 detector는 유지됐다. actor가 실행되지 않았으므로 source의 타현·release 성능이나 연주 성공을 평가한 결과가 아니다.

## 실제 native 카메라 자료

각 프레임은 실제 native 카메라 출력이며, index `00000`, `00060`, `00150`은 0초·2초·5초다. 두 영상은 각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![aligned-play 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/whole_body/00000.png) | ![aligned-play 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![aligned-play 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/whole_body/00060.png) | ![aligned-play 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![aligned-play 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/whole_body/00150.png) | ![aligned-play 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/frames/hands/00150.png) |

![aligned-play 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/whole_body.mp4)

![aligned-play 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/hands.mp4)

## 원자료와 구현 색인

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/analysis.log) · [native report/checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/report.json:1)
- [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/checkpoint_connection.json:1) · [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/trace.json:1)
- [native 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/inputs_before.json:1) · [native 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/inputs_after.json:1) · [capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/capture.json:1) · [영상 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native/data/images/videos.json:1) · [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_aligned_play_v1/native.log)
- [aligned-play 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_ALIGNED_PLAY_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_aligned_play.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_aligned_play_preserved_run.py:12)
- [메인 PLAN 경과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:232) · [메인 README 경과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1537)
