# READY 잔차 보정 5초 진단

자동 시작 기준 실행과 같은 초기 상태에서 READY 잔차 보정을 붙여 비교했다. 실행은 5초/1200 physics steps, 151 native camera frames로 끝났고 16개 계약 검사와 1016개 입력 closure 검사가 모두 통과했다. 고정 2초 대기는 없고, 진입은 0.8166667초였다.

보정은 실제 pick 위치를 기준으로 계산했다. 측정된 native pick 위치에 현재 Chest 회전 변화로 FK 변위를 옮겨 current-G READY 목표와 맞추는 오른쪽 Shoulder·Elbow·Wrist 9축 fit을 만들고, fit 보정량을 source 정책의 팔 목표에 더하되 각 축 변화는 ±0.15 rad 이내로 제한했다. `R_Thorax` 3축은 이 보정에 포함되지 않았다. 이 보정은 source phase 0에서만 계산했다. 저장된 최대 절대 보정은 0.138927550 rad로 한계 안이었고 경계 포화는 없었다. stand-off 0, 준비 반경 0.3 rad, 오른팔 정책 rate 3.2 rad/s, 오른팔 PD scale 1 및 기존 native PD를 유지했다. 원본 10 mm/6연속 표본 READY와 phase 전이는 바꾸지 않았다. PREPARE의 초기 IK가 사용하는 오른팔 12축과 이 9축 잔차 보정은 별도다.

## 관측 결과

| 지표 | 자동 시작 기준 | READY 잔차 보정 |
|---|---:|---:|
| PLAY 시작 / actor steps | 0.8166667초 / 251 | 0.8166667초 / 251 |
| 최소 PLAY 준비점 거리 | 10.766370 mm | 10.439381 mm |
| 범위 안 제어 표본 / 정책 표본 | 103/300 / 57/251 | 119/300 / 73/251 |
| 기타 위치 변화 최대 / 종료 | 46.353646 / 29.535285 mm | 46.353646 / 25.494146 mm |
| 기타 회전 변화 최대 / 종료 | 46.860685 / 45.653964° | 46.014401 / 44.083734° |
| source target hit / physical target hit / accepted release | 0 / 0 / 0 | 0 / 0 / 0 |
| physical release / miss / wrong crossing | 2 / 10 / 2 | 2 / 10 / 3 |

두 조건 모두 관측된 source motor phase는 `[0]`뿐이고 learning update는 0이다. 보정 조건에서 준비 거리·범위 표본 및 종료 자세 수치가 변했지만 인정 타현과 accepted release는 없었다. 따라서 이를 연주 성공이나 지속적인 안정성으로 해석하지 않는다. 정책 중 기타 위치·회전이 계속 변했고, 접촉 소실은 중단 조건으로 쓰지 않았다.

## 실제 native 카메라 자료

각 시점 이미지는 저장된 native 카메라 프레임이다. 두 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![잔차 보정 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/whole_body/00000.png) | ![잔차 보정 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/hands/00000.png) |
| 2초 | ![잔차 보정 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/whole_body/00060.png) | ![잔차 보정 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/hands/00060.png) |
| 5초 | ![잔차 보정 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/whole_body/00150.png) | ![잔차 보정 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/frames/hands/00150.png) |

![READY 잔차 보정 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/whole_body.mp4)

![READY 잔차 보정 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/hands.mp4)

## 원자료와 구현 색인

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/analysis.log)
- [native report 및 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/trace.json:1) · [inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/inputs_before.json:1) · [inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/inputs_after.json:1) · [checkpoint 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/checkpoint_connection.json:1)
- [capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/capture.json:1) · [video metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native/data/images/videos.json:1) · [native 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/native.log)
- [기존 자동 시작 비교 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/analysis/summary.json:1) · [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_RESIDUAL_V2_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_residual_v2.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_ready_residual_preserved_run_v2.py:12)
- [메인 PLAN 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:263) · [메인 README 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:1568)
