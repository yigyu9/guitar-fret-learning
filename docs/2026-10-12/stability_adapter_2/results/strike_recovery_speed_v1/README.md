# 회복 증분 속도 비교

이 5초 진단은 직전 recovery-priority 조건에서 RECOVER 구간의 R9 증분 gain만 0.5에서 1.0으로 바꿨다. RECOVER 목표는 이전 제출 목표에 현재 측정 IK delta를 더하며, delta는 기존 ±0.15 rad 범위와 model/rate 제한을 따른다. source phase 0/1의 policy+PI, source waypoint와 clearance, 손가락 policy, 나머지 PD·시간·weights는 유지했다.

실행은 1200 physics steps와 151 camera frames를 완료했다. 계약 검사 16개가 참이고 입력 closure 1035개에서 변경은 없었다. PREPARE 49표본 후 0.816667초에 PLAY가 시작되어 actor 180 steps를 실행했다. source terminal은 3.816667초에 발생했고, 이후 HOLD 71표본 동안에도 물리·카메라 기록은 5초까지 이어졌다.

| 관측 | 결과 |
|---|---:|
| target hit / physical target hit / accepted release | 1 / 1 / 1 |
| 전체 physical release / miss / wrong crossing | 5 / 7 / 4 |
| 마지막 partial running strike F1 | 0.153846 |
| guitar 범위 안 표본: 전체 / policy | 238/300 / 132/180 |
| 최소 준비점 거리: PREPARE / PLAY / HOLD | 25.211255 / 1.907328 / 14.148093 mm |
| 기타 위치 변화: 최대 / 종료 | 46.353646 / 38.303635 mm |
| 기타 회전 변화: 최대 / 종료 | 9.019638 / 5.132309° |

hit 1건은 2.483333초 string 2에서 발생했고 타이밍 오차는 45.179844 ms였다. RECOVER 중 physical release는 0이었다. clearance lifted는 2.783333초, clearance reached와 scheduled recovery-complete pulse는 3.15초에 기록됐다. 이는 기존 단계보다 각각 약 0.1초, 0.116667초 이르지만 source phase 2에서 1로 바뀐 시각은 두 실행 모두 3.35초였다. 다음 source 이벤트 시각이 그 사이에 있었기 때문에 회복 완료가 빨라진 것이 다음 타현 성공을 뜻하지 않는다. 전체 wrong crossing 4회는 초기 READY의 1회와 회복 후 APPROACH의 3회로 나뉘며 miss는 7회였다. full-song completion이나 연주 성공은 아니다.

## 실제 native 카메라 기록

프레임 00000, 00060, 00150은 0, 2, 5초다. 두 native 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/whole_body/00060.png) | ![손 근접 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/hands.mp4)

## 자료와 구현

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/analysis.log)
- [native report/검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/trace.json:1) · [실행 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/inputs_before.json:1) · [실행 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/inputs_after.json:1)
- [video metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/videos.json:1) · [native 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native.log)
- [회복 속도 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_SPEED_PLAN.md:1) · [runner 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_strike_recovery_speed.py:24) · [RECOVER gain 적용 기록](/home/ajou/yigyu/3/stability_adapter_2/run_strike_recovery_speed.py:256) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_recovery_speed_preserved_run.py:12)
