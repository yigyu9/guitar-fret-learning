# 실제 준비점 기준 3조건 정밀 준비 진단

세 조건은 같은 새 초기 후보에서 시작해 각각 5초(1200 physics steps)를 기록했다. 모두 실행 계약 15개가 통과하고 입력 closure 변경은 0이었다. 다만 세 조건 모두 `PREPARE`에서 끝났고 actor는 0 step이다. 외부 준비 진단의 10 mm 거리·grip 6연속 표본 조건을 만족하지 못해 source 정책은 실행되지 않았다. 따라서 이 결과는 준비 정밀도 비교이지 Strike 정책이나 연주 능력 평가가 아니다.

## 조건과 결과

| 조건 | RH 목표 rate 상한 (PLAY 설정, 미실행) | RH PD 배율 | 준비 반경 | 오차 보정 배율 | actor step | 준비 범위 참 제어 표본 | 최소 준비점 거리 (mm) | 기타 위치 변화 최대 / 종료 (mm) | 기타 회전 변화 최대 / 종료 (°) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `aligned` | 3.2 rad/s | 1× | 0.3 rad | 0 | 0 | 113/300 | 17.060965 | 46.353646 / 30.876120 | 7.095455 / 3.051304 |
| `wider` | 3.2 rad/s | 1× | 0.6 rad | 0 | 0 | 295/300 | 28.334011 | 52.839307 / 35.290633 | 8.258381 / 4.812527 |
| `compensated` | 3.2 rad/s | 4× | 0.6 rad | 0.5 | 0 | 93/300 | 33.711651 | 104.212739 / 45.628534 | 22.635532 / 4.784525 |

표의 준비 범위 참 제어 표본은 각 300개 기록 중 해당 범위 안에 든 표본 수다. 2초 시점의 준비점 거리는 `aligned` 17.874040436 mm/region 거짓, `wider` 28.341782288 mm/region 참, `compensated` 185.879104028 mm/region 거짓이었다. 세 조건 모두 최소 준비점 거리가 10 mm보다 커 외부 10 mm/grip 6연속 표본 조건에는 도달하지 못했다. 위치·회전 변화량은 각각 초기 기타 자세에서의 최대 변화와 5초 종료 변화다. 기타의 종료 오차만으로 중간 궤적이나 안정성을 판단하지 않는다. `wider`는 반경만 넓힌 조건이고, `compensated`는 반경·RH gain·오차 보정 배율을 함께 바꿨으므로 이를 한 요인의 효과로 분리할 수 없으며 미채택이다. 정책 actor 표본은 세 조건 모두 0이므로 범위 표본을 정책 성능이나 실패로 읽어서는 안 된다.

세 실행은 PREPARE에서 5초를 기록했다. PLAY에 설정될 RH 목표 rate 상한은 3.2 rad/s였지만 실행되지 않았고, PREPARE에서 적용된 cap은 0.8 rad/s였다. 정책 task가 시작되지 않아 source motor phase는 초기 READY 상태값 0에 남았으며, 이를 phase를 강제로 고정한 것으로 해석하지 않는다. 원본 source의 10 mm READY와 motor detector는 바꾸지 않았다. 손바닥 접촉 지속은 준비·정책 진입 조건으로 강제하지 않았다. strap은 없고 기타는 자유 운동하며 root와 하체는 고정했다. 이 단계에서는 학습이나 정책 actor 실행이 없다.

다음 진단은 stand-off 0에서 기존 80 mm handoff로 source 정책을 연결해, source가 자체 10 mm READY를 획득하는지 기록하는 계획이다. 이는 다음 단계의 계획이며 이번 세 조건에서 정책 성공이 확인됐다는 뜻은 아니다. 세부 조건은 [aligned-play 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_ALIGNED_PLAY_PLAN.md:1)에 있다.

## Native 카메라 자료

아래 프레임은 실제 native 카메라 저장 이미지다. index `00000`, `00060`, `00150`은 각각 0초, 2초, 5초이며, 각 카메라 영상은 151 frames, 30 fps, ffprobe stream duration 5.033333초다. `전신`과 `손`은 별도 카메라다.

### `aligned` — 반경 0.3 rad, RH gain 1×

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![aligned 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/whole_body/00000.png) | ![aligned 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/hands/00000.png) |
| 2초 | ![aligned 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/whole_body/00060.png) | ![aligned 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/hands/00060.png) |
| 5초 | ![aligned 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/whole_body/00150.png) | ![aligned 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/frames/hands/00150.png) |

![aligned 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/whole_body.mp4)

![aligned 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/images/hands.mp4)

### `wider` — 반경 0.6 rad, RH gain 1×

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![wider 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/whole_body/00000.png) | ![wider 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/hands/00000.png) |
| 2초 | ![wider 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/whole_body/00060.png) | ![wider 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/hands/00060.png) |
| 5초 | ![wider 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/whole_body/00150.png) | ![wider 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/frames/hands/00150.png) |

![wider 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/whole_body.mp4)

![wider 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/images/hands.mp4)

### `compensated` — 반경 0.6 rad, RH gain 4×, 오차 보정 0.5×

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![compensated 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/whole_body/00000.png) | ![compensated 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/hands/00000.png) |
| 2초 | ![compensated 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/whole_body/00060.png) | ![compensated 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/hands/00060.png) |
| 5초 | ![compensated 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/whole_body/00150.png) | ![compensated 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/frames/hands/00150.png) |

![compensated 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/whole_body.mp4)

![compensated 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/images/hands.mp4)

## 분석·실행 자료와 코드 색인

- [세 조건 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/analysis_three/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/analysis_three.log)
- 실행별 입력·초기값·설정·검사·시계열은 [aligned 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned/data/initial_values.json:1), [wider 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider/data/initial_values.json:1), [compensated 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated/data/initial_values.json:1)에서 확인할 수 있다. 각 실행의 `report.json`, `checkpoint_connection.json`, `trace.json`, `controls.json`, `inputs_before.json`, `inputs_after.json`, `data/images/videos.json`도 같은 실행 디렉터리에 보존했다.
- [aligned 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/aligned.log) · [wider 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/wider.log) · [compensated 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_alignment_v1/compensated.log)
- [alignment 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_ALIGNMENT_PLAN.md:1) · [정책 재진입 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_ALIGNED_PLAY_PLAN.md:1)
- [runner 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_alignment.py:24) · [보존 실행 진입점](/home/ajou/yigyu/3/stability_adapter_2/strike_ready_preserved_run.py:12) · [분석 진입점](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials.py:9)
- [메인 PLAN 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:218) · [메인 README 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1523)
