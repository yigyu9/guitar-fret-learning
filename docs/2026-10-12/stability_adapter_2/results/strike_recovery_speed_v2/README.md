# 회복 증분 gain 2 진단

이 5초 native 진단은 이전 회복 증분 gain 1 조건에서 RECOVER 구간 gain만 2로 높였다. source phase 2에서 이전 오른팔 9축 목표에 실제 current-pose 앵커 IK delta의 2배를 더하며, 기존 ±0.15 rad local fit, model bounds, 3.2 rad/s frame rate 제한을 유지한다. READY/APPROACH policy+PI, 손가락 policy, clearance waypoint, source phase·latch·시간·weights, PD와 나머지 설정은 그대로다.

실행은 1200 physics steps와 151 native camera frames로 완료됐고 계약 검사 16/16, 입력 closure 1038개에서 변경은 0이었다. PREPARE 49표본 뒤 0.816667초에 PLAY가 시작해 actor는 146 steps 실행했다. source terminal은 3.25초에 났고 남은 105표본은 HOLD로 기록되어 물리·영상은 5초까지 이어졌다.

| 관측 | 결과 |
|---|---:|
| target hit / physical target hit / accepted release | 1 / 1 / 1 |
| 전체 physical release / miss / wrong crossing | 5 / 4 / 4 |
| 마지막 partial running strike F1 | 0.200000 |
| guitar 범위 안 표본: 전체 / policy | 182/300 / 101/146 |
| 최소 준비점 거리: PREPARE / PLAY / HOLD | 25.211255 / 2.938625 / 16.182470 mm |
| 기타 위치 변화: 최대 / 종료 | 46.353646 / 23.937022 mm |
| 기타 회전 변화: 최대 / 종료 | 9.019638 / 2.250558° |

첫 hit은 이전 실행과 같은 2.483333초 string 2였고 타이밍 오차는 45.179844 ms였다. RECOVER 중 physical release는 0이다. clearance lifted는 2.55초, clearance reached와 scheduled recovery-complete pulse는 2.95초였다. source phase 2→1은 3.033333초, phase 1의 첫 control은 3.05초로 gain 1 조건보다 앞당겨졌다. 그러나 이후 3.166667초 string 3, 3.2초 string 2, 3.233333초 string 1에서 비-hit crossing이 관측되고 3.25초 terminal이 났다. 전체 wrong crossing 4회 중 1회는 초기 READY, 3회는 recovery 이후 phase 1이었다.

F1은 이전 gain 1의 0.153846에서 0.2로 보이지만, 이번에는 source terminal과 PLAY 종료가 더 빨라 이벤트 기회가 적었다. 이를 성능 향상으로 해석하지 않는다. 한 회복 구간의 clearance 완료가 빨라졌지만, 이후 타현 성공이나 full-song completion은 확인되지 않았다.

## 실제 native 카메라 자료

프레임 00000, 00060, 00150은 각각 0, 2, 5초다. 전신과 손 근접 영상은 각각 151 frames, 30 fps, ffprobe stream duration 5.033333초다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/hands/00000.png) |
| 2초 | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/whole_body/00060.png) | ![손 근접 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/hands/00060.png) |
| 5초 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/frames/hands/00150.png) |

![전신 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/whole_body.mp4)

![손 근접 native 영상: 151 frames, 30 fps, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/hands.mp4)

## 자료와 구현

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/analysis.log)
- [native report/검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/report.json:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/checkpoint_connection.json:1)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/controls.json:1) · [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/trace.json:1) · [입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/inputs_before.json:1) · [입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/inputs_after.json:1)
- [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/videos.json:1) · [native 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native.log)
- [gain 2 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_RECOVERY_SPEED_V2_PLAN.md:1) · [runner 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_strike_recovery_speed_v2.py:24) · [RECOVER gain 적용](/home/ajou/yigyu/3/stability_adapter_2/run_strike_recovery_speed_v2.py:159) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_recovery_speed_v2_preserved_run.py:12)
