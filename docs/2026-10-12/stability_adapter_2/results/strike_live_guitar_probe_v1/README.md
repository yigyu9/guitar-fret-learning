# 현재 기타 기준 Strike 연결 진단

원본 Strike 체크포인트를 현재 수평·무스트랩 기타 자세에 연결한 1회 정책 실행을 기록한다. 49개 제어 단계, 196개 물리 단계(0.816667초)에서 `wrong_crossing_count_termination`으로 정책 실행이 끝났다. TP=0, FP=4, FN=1, F1=0이며 종료 시 피크와 목표의 거리는 152.024 mm였다. 이후 1200개 물리 단계까지 이어진 기록은 정책 재생이 아니라, 마지막 81개 관절 PD 목표를 고정한 자유 물리 연속 구간이다.

첫 native 기록은 49개 제어 단계와 196개 물리 단계에서 끝났고 요청한 5초를 채우지 못했다. 두 번째 기록은 같은 초기 입력에서 정책 제어·관측·최종 목표·history를 정확히 재현한 뒤 총 1200개 물리 단계까지 기록했다. 두 번째 실행은 151개 프레임, 30 fps, ffprobe stream duration 5.033333초의 실제 Isaac Gym native 전신·손 카메라 영상을 남겼다.

| 구간/측정 | 값 |
|---|---:|
| 정책 구간 | 49 control steps / 196 physics steps / 0.816667 s |
| source episode | TP 0 / FP 4 / FN 1 / F1 0 |
| 정책 종료 시 피크-목표 거리 | 152.024 mm |
| 첫 정책 후 물리 step 거리 | 351.936 mm |
| 정책 후 최소 피크-목표 거리 | 131.526 mm |
| 5초 기록 전체 기타 최대 위치 변화 | 63.386 mm |
| 5초 기록 전체 기타 최대 회전 변화 | 14.883° |
| 5초 기록 종료 기타 위치/회전 변화 | 44.061 mm / 11.768° |

![정책 종료와 passive continuation 구간의 기타 위치·회전 변화. 세로선은 step 196이며 저장 표본 step 192와 200 사이에 있다. 음영은 마지막 81개 PD 목표만 유지한 구간이다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/policy_passive_timeline_v3.png)

그림은 저장된 trace에서 계산한 기타 상태 변화량이며 PhysX 렌더가 아니다. 종료 step 196의 p/q는 v2 trace에 저장되지 않았고, trace 표본은 8 physics steps 간격이므로 step 192와 200 사이 종료시점의 자세를 보간하거나 추정하지 않는다.

## 두 번째 실행의 실제 native 영상

두 영상은 저장 상태를 재생성한 그림이 아니라 실제 Isaac Gym native camera 캡처다. 각 영상은 step 0부터 1200까지의 151 프레임을 담는다. 영상은 passive continuation을 포함하며 정책 연주 평가로 해석하지 않는다.

![실제 Isaac Gym native camera — 전신, 시작 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/frames/whole_body/00000.png)

![실제 Isaac Gym native camera — 전신, 5초 기록 끝](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/frames/whole_body/00150.png)

![실제 Isaac Gym native camera — 손, 시작 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/frames/hands/00000.png)

![실제 Isaac Gym native camera — 손, 5초 기록 끝](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/frames/hands/00150.png)

![실제 Isaac Gym native camera 전신 영상 (151 frames, 30 fps)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/whole_body.mp4)
![실제 Isaac Gym native camera 손 영상 (151 frames, 30 fps)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/hands.mp4)

## 해석 범위

기타만 10 mm 이동한 입력은 관측 최대 절대 변화 0.0100004, actor 출력 0.00381613을 보였다. 기타만 Z축 5° 회전한 입력은 각각 0.0847581, 0.00815072였다. 같은 강체 변환을 장면 전체에 적용한 두 CPU counterfactual은 관측 차이 약 1.2–1.3×10⁻⁶, 출력 차이 약 2.2–2.5×10⁻⁷였다. 현재 기타 좌표 갱신을 확인한 결과이며 물리적 전이 성공을 뜻하지 않는다.

이번 체크포인트 1회 실행에서 학습 업데이트는 0회였고, 원본 source episode의 연주 분류 성능은 실패했다. 종료 뒤에는 actor, PI 지원, 노래 진행, detector를 중단하고 마지막 81개 PD 목표를 유지했다. 기록된 사후 검사는 q/qd/G 유한성, qd<50, root/하체 고정, 목표 상수 유지에 한정된다. 연속 source geometry 관통·복구불능 검사나 상체 pose 유한성 검사는 이어서 수행하지 않았다. 따라서 passive continuation의 후기 움직임은 안정 평형이나 연주 성공의 증거가 아니다.

이 구현의 현재 native PD 및 관절 변화율 제한은 원본 체크포인트의 명시적 stiffness torque 구현과 다르므로, 이 단일 실패만으로 원본 체크포인트의 일반 성능을 단정하지 않는다. 자세·스트랩이 다른 이전 실험과도 직접 성능 비교하지 않는다.

## 재현·입력 기록

- 분석 요약: [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/analysis/summary.json)
- 첫 실행 보고서와 제한된 입력 보존: [native_v1/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v1/report.json), [native_v1/attempt.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v1/attempt.json)
- 두 번째 실행 보고서/trace: [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/report.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/trace.json)
- 실행 전·후 입력 목록: [inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/inputs_before.json), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/inputs_after.json) — wrapper가 956개 입력을 보존·대조했고 변경은 없었다.
- 그림 생성 manifest 및 실행 기록: [manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/manifest.json), [artifact_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/artifact_execution.json), [artifact_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/artifact_execution.log)
- 실패/이전 후처리 보존: [probe_v1.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/probe_v1.log), [probe_v2.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/probe_v2.log), [attempt_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/attempt_v1), [attempt_success_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/attempt_success_v2)
- 계획과 진입점: [probe 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LIVE_GUITAR_PROBE_PLAN.md:1), [기록 연장 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_RECORDING_CONTINUATION.md:1), [기존 실행 진입점](/home/ajou/yigyu/3/stability_adapter_2/strike_probe_preserved_run.py:1), [v2 실행기](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe_v2.py:69), [native view 생성 함수](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:103), [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_live_probe.py:11)

그림 재생성은 추가 native 초기화 없이 저장 자료만 사용한다. 생성 환경·입력/출력 SHA-256과 시각 점검 결과는 manifest 및 실행 기록에 남겼다.
