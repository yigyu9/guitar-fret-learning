# READY 잔차 PI 5초 진단

P-only READY 잔차 기준과 같은 초기 조건에서 비례 보정에 적분항을 더한 한 번의 native 진단이다. READY 잔차는 실제 pick 위치와 현재 기타 READY 목표의 FK 차이를 이용해 오른쪽 Shoulder·Elbow·Wrist 9축에서 계산했다. 보정은 P 최대 ±0.15 rad, I 최대 ±0.3 rad, 합산 보정 최대 ±0.3 rad로 제한하고, 적분 증분은 `0.2 × P 보정`이며 target rate 경계를 고려한 anti-windup을 적용했다. source phase 0에서만 P/I를 갱신하며 READY 이후에는 마지막 I bias를 정책 목표에 더해 유지했다. PREPARE 초기 IK의 오른팔 12축과 이 9축 잔차 fit은 서로 다른 처리다. `R_Thorax` 3축, 왼팔, 손가락 21축과 torso 목표는 변경하지 않았다.

## P-only 기준과 관측 비교

두 실행은 각각 5초/1200 physics steps 및 151 native frames를 완료했다. 적분 실행의 16개 계약 검사와 1019개 입력 closure 검사는 모두 통과했고, 검사된 입력 변경은 없었다.

| 지표 | P-only READY 잔차 v2 | P+I READY 잔차 |
|---|---:|---:|
| PLAY 시작 / actor steps | 0.816667초 / 251 | 0.816667초 / 251 |
| PLAY 중 최소 READY 거리 | 10.439381 mm | 3.240488 mm |
| 범위 안 제어 표본 / 정책 표본 | 119/300 / 73/251 | 251/300 / 205/251 |
| 기타 위치 변화 최대 / 종료 | 46.353646 / 25.494146 mm | 46.353646 / 39.285219 mm |
| 기타 회전 변화 최대 / 종료 | 46.014401 / 44.083734° | 8.991360 / 5.300883° |
| source motor phase 관측 | `[0]` | `[0, 1]` |
| target hit / accepted release | 0 / 0 | 0 / 0 |
| physical release / miss / wrong crossing | 2 / 10 / 3 | 1 / 10 / 1 |

P+I 조건은 source READY success 기록이 1이었지만 target hit과 accepted release는 0이다. 하나의 physical release는 1.033333초에 기록됐고 source phase 0, string 3, target 2였으며 `release_phase_violation=true`였다. source phase 1의 첫 기록은 1.266667초였다. 따라서 READY 지표 변화나 물리 release 한 건을 연주 성공으로 읽지 않는다. 또한 기타 위치 종료 변화는 P-only보다 커졌고, 범위·손 접촉의 지속적 유지를 인증한 결과가 아니다.

P+I 업데이트가 0.2초가 아니라 0.2 계수로 누적된 I는 source phase 0 종료 후 고정 bias로 남는다. 저장 control에서 P/I/합산 보정 최대 절대값은 각각 0.065323/0.107322/0.121735 rad였다. 이는 이번 실행의 기록값이며 일반적인 제어 성능이나 장기 안정성의 보증이 아니다.

## 실제 native 카메라 자료

0/2/5초 프레임은 실제 native 카메라 기록의 index `00000`, `00060`, `00150`이다. 전신 및 손 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![P+I 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/whole_body/00000.png) | ![P+I 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![P+I 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/whole_body/00060.png) | ![P+I 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![P+I 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/whole_body/00150.png) | ![P+I 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/frames/hands/00150.png) |

![P+I 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/whole_body.mp4)

![P+I 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/hands.mp4)

## 원자료 및 구현 색인

- [P+I 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/analysis.log)
- [native report 및 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/inputs_after.json:1)
- [capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/capture.json:1) · [video metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/videos.json:1) · [native log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native.log)
- [P-only 분석 기준](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/analysis/summary.json:1) · [PI 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_INTEGRAL_PLAN.md:1) · [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_integral.py:24) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_ready_integral_preserved_run.py:12)
- [메인 PLAN 결과 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:285) · [메인 README 결과 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:1590)
