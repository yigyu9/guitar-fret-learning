# PLAY 오른팔 damping 단일 변경 진단

## 실험과 native readback

PREPARE의 POSITION PD 설정은 그대로 두고, PLAY handoff에서 오른팔의 어깨·팔꿈치·손목 9축 damping만 기존값의 0.25배로 바꿨다. handoff는 step 196, 0.816667초에 일어났다. native readback은 요청 속성과 정확히 일치했다. stiffness와 effort limit, drive mode 등 나머지 속성은 유지됐다.

| 관절 | handoff 전 damping | PLAY native readback | stiffness |
|---|---:|---:|---:|
| R_Shoulder_x/y/z | 50 | 12.5 | 200 |
| R_Elbow_x | 37.5 | 9.375 | 150 |
| R_Elbow_y/z | 15 | 3.75 | 60 |
| R_Wrist_x/y/z | 12.5 | 3.125 | 50 |

이것은 POSITION drive 안에서 damping만 바꾼 진단이며, EFFORT 명령이나 측정 토크 실험이 아니다. PREPARE는 49 control step, PLAY는 11, 이후 HOLD는 240 step이다. 전체 실행은 1,200 physics step(5초)과 151 native 카메라 프레임으로 완료됐고, 20개 계약 검사와 1,048개 입력 closure 검사가 통과했다.

| 관측 | 결과 |
|---|---:|
| PLAY 시작 | 0.816667초 |
| source terminal 및 HOLD 진입 | 1.0초 |
| PREPARE 최소 pick-to-ready 거리 | 25.2113 mm |
| PLAY 최소 pick-to-ready 거리 | 22.5653 mm |
| HOLD 최소 pick-to-ready 거리 | 18.8805 mm |
| 기타 최대 위치 변화 | 59.1930 mm |
| 기타 최대 회전 변화 | 8.8433° |
| target hit / physical target hit / accepted release | 0 / 0 / 0 |
| physical release / wrong crossing / miss | 4 / 4 / 0 |

HOLD 진입 표본에서 `pick_behind_guitar_body`는 false였고, 기록된 rear-plane 값은 -0.041700 m였다. 종료는 source terminal로 기록됐으며 5초 실행이 계속되어 나머지 시간은 HOLD로 관측됐다. 이 damping 변경은 채택하지 않았다. 이번 진단은 연주 성공을 보이지 않았고, 한 번의 비교로 damping을 실패 원인 또는 응답 개선의 원인으로 단정할 수 없다.

free guitar, strap 해제, root와 하체 고정, 몸통 PD, self-collision, frozen checkpoint, source weights와 RMS 상태, READY·타현·회복 로직은 그대로였다. 학습 갱신은 0이다.

## 저장된 native 영상과 대표 프레임

아래 영상은 실제 Isaac Gym 카메라의 저장 자료다(151 frames, 30 fps, ffprobe stream duration 5.033333초). 기타 움직임은 source geometry 재생 영상이 아니라 해당 native 실행에서 기록됐다.

![전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/hands.mp4)

대표 프레임: [전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/whole_body/00000.png) · [손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/hands/00000.png) · [전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/whole_body/00060.png) · [손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/hands/00060.png) · [전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/whole_body/00150.png) · [손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/frames/hands/00150.png)

## 원자료와 구현 참조

- [요약 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/summary.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/report.json), [handoff 전후 PD 요청/readback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/PD_handoff_properties.json), [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/initial_values.json), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/trace.json).
- 입력 closure: [native 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/inputs_before.json), [native 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/inputs_after.json), [분석 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/inputs_before.json), [분석 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/inputs_after.json).
- [단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PLAY_DAMPING_PLAN.md:1), [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_play_damping.py:218), [보존 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_play_damping_preserved_run.py:12).
