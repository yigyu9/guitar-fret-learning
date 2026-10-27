# APPROACH-only 오른팔 damping 진단

이 결과는 기존 PREPARE/READY 구성을 유지하고, 원본 source motor phase가 APPROACH(phase 1)일 때만 오른팔 shoulder/elbow/wrist 9축 damping을 0.25배로 설정한 저장 native 실행이다. 그 밖의 source phase에서는 기준 damping으로 복원했다. 값은 native getter readback으로 확인했고 전환은 4회였다: 1.266667초 phase 1 → 0.25, 1.366667초 phase 2 → 1, 2.383333초 phase 1 → 0.25, 2.766667초 phase 2 → 1. 81개 property와 상태 보존 검사는 모두 정확히 통과했다. 별도 baseline 대조에서 첫 기준 damping 복원 직전의 controls 82개와 복원 시점까지 native 전체 상태 trace 42개가 직전 APPROACH-damping 실행과 정확히 같았다. 이는 복원 전 구간(첫 hit 포함)의 명령·관측·행동·history와 저장 상태가 같다는 범위의 근거이며, 1,200 step 전체 trajectory가 같다는 뜻은 아니다. 대조에 사용한 6개 입력 SHA는 불변이다. [대조 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/pre_recovery_comparison.json), [대조기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/compare_before_recovery.py), [원본 property 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/PD_phase_properties.json), [실행 코드의 phase별 설정 및 기록](/home/ajou/yigyu/3/stability_adapter_2/run_strike_approach_only_damping.py:141).

5초 실행은 1,200 physics step, 151 camera frame, 20/20 검사 통과로 끝났다. native 실행 입력 closure는 1,056개이며 변경은 0이었다. 분석기 입력은 별도 7개 파일이며 before/after SHA 대조에서 변경이 없었다. PREPARE/PLAY/HOLD 제어 표본은 49/135/116이다. source는 wrong-crossing count로 3.066667초에 종료됐고 이후 남은 시간은 HOLD에서 physics와 기록을 계속했다. [native 입력 closure 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/inputs_before.json), [분석 입력 SHA 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/inputs_before.json), [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/summary.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/report.json).

첫 타현은 1.350000초, 첫 음표(event index 0)의 string 2 DOWN으로 timing 오차 +44.484798 ms였으며 timely `target_hit`로 인정됐다. 뒤의 2.750000초 string 2 DOWN은 event index 3에서 geometry-accepted/physical target hit였지만 premature이며 timing −64.536217 ms여서 timely `target_hit`는 아니었다. 따라서 물리적/geometry hit 두 건과 source timing 기준 hit 한 건은 구분해야 한다. 집계는 READY 1, `target_hit` 1, physical target hit 2, accepted release mask 2, physical release 6, miss 3, wrong crossing 4다. 마지막 partial strike F1은 0.400000006이며 짧고 다른 길이의 PLAY 노출이므로 성능 완료나 비교 우위로 해석하지 않는다.

첫 clearance는 lifted 1.400000초, reached 2.183333초, scheduled completion 2.366667초에 관측됐고 source phase 2→1 복귀 뒤 회복이 완료됐다. 단, 최초 READY 오교차는 1.033333초 string 3이었고 RECOVER 중에도 2.783333초 string 1, 3.016667초 string 2, 3.050000초 string 1 오교차가 이어져 source가 종료됐다. 기타 최대/종료 회전 변화는 7.095455°/4.927969°, 위치 변화는 46.353646/36.393910 mm였다. playable-region 표본은 제어 287/300, policy 125/135이다. `music_success=false`, learning updates 0이며 전체 곡 성공은 관측되지 않았다.

이 시험은 damping을 APPROACH에서만 낮추고 RECOVER 전에 기준값을 복원할 수 있음을 보여주는 진단이다. 이를 채택하거나 연주 성능 완료로 판정하지 않는다. 후속 timed-ENTRY 시험은 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1)에 따라 geometry-accepted hit와 timely target hit를 분리해 평가한다.

## 저장된 native 시각 자료

아래 MP4는 저장된 Gym native 카메라 영상이다. 각 영상은 151 frames, 30 fps이며 stream duration은 5.033333초다. 대표 프레임은 0, 2, 5초다.

| 시점 | 전신 프레임 | 손 프레임 |
|---|---|---|
| 0 s | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/hands/00000.png) |
| 2 s | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/hands/00060.png) |
| 5 s | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/frames/hands/00150.png) |

### 전신 영상

![전신 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/whole_body.mp4)

### 손 영상

![손 근접 native 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/hands.mp4)

### 입력 및 절차

[초기 상태 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/initial_audit.json), [초기값 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/initial_values.json), [화면 캡처 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/capture.json), [저장 영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/videos.json), [분석 입력 전후 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/inputs_before.json) (분석기 입력 7개 파일; SHA 불변).
