# 현재 기타 기준 양손 준비 gate 진단

이번 단계는 현재 기타 좌표에서 오른손 타현 준비점 추종과 왼손 넥 아래 palm/finger 접촉을 함께 요구하는 준비 gate를 5초 동안 측정했다. 준비 gate가 획득되지 않아 실제 PLAY는 0회다. 학습 업데이트는 없고, 기타는 자유 물리·strap OFF였으며 root/하체는 고정했다. 몸통 9축과 기타 이외 36축은 목표 유지 상태다. 최종 제어 인터페이스는 66축이며, 준비 구간의 오른손은 현재 기타 기준점으로 준비 target을 추종한다.

최종 v4는 추가한 오른팔 PI를 제거해 기본 IK 경로를 복원한 진단 기준이다. v4 trace는 v1과 byte-exact이고, v3 trace는 v2와 byte-exact다. v3에서는 handoff 직전 task reset을 제거했지만 이 단계에서는 gate가 열리지 않아 PLAY handoff를 관찰하지 못했다. v4의 14개 contract check가 모두 통과했고, 981개 보존 입력은 실행 전후 바뀌지 않았다. 네 실행의 초기 native 상태와 PD 설정은 exact 일치한다.

## 네 번의 5초 native 실행

| 실행 | 구성 차이 | 준비 gate | LH palm / finger contact frame | RH 준비점 거리 max / 마지막 (mm) | 기타 위치 max / 끝 (mm) | 기타 회전 max / 끝 (°) |
|---|---|---:|---:|---:|---:|---:|
| v1 | 기본 RH IK | 0/300 | 1 / 298, 동시 0 | 60.255 / 56.300 | 59.579 / 37.427 | 9.526 / 5.157 |
| v2 | RH PI 추가 진단 | 1/300, 최장연속 1 | 28 / 299, 동시 28, 최장 20 | 123.844 / 104.324 | 57.673 / 24.943 | 9.107 / 2.304 |
| v3 | v2 handoff 연속성 수정, 물리 trace는 v2와 exact | 1/300, 최장연속 1 | 28 / 299, 동시 28, 최장 20 | 123.844 / 104.324 | 57.673 / 24.943 | 9.107 / 2.304 |
| v4 | RH PI 제거, 기본 RH IK 복원 | 0/300 | 1 / 298, 동시 0 | 60.255 / 56.300 | 59.579 / 37.427 | 9.526 / 5.157 |

표의 거리는 native control 표본에서 읽은 RH pick과 현재 기타 기준 ready point 사이의 거리다. `right_near_strike`는 외부 준비 근접 gate인 50 mm 조건이고, 원본 READY의 10 mm 및 6 연속 프레임 획득과는 다른 조건이다. 그림에는 두 거리선을 별도로 표시했다. 어느 거리선 하나만으로 전체 gate가 열리지는 않는다. 전체 조건에는 왼손 palm/finger contact, palm-up, RH front/grip/noncontact 등이 모두 포함되며 여섯 control frame 연속 만족해야 한다.

v4에서 palm underside contact는 1/300, finger-to-neck contact는 298/300이었지만 같은 표본에서 둘이 함께 참인 frame은 0이었다. RH는 외부 50 mm 근접 조건을 9/300 표본에서 만족했고, right-front/grip/noncontact 조건은 각 300/300이었다. 전체 readiness는 0/300이며 actor는 실행되지 않았다. contact의 raw lambda는 gate 증거로 사용한 기록값이지 뉴턴 단위의 힘이나 지지력 인증이 아니다.

검색 후보의 2.201253 mm target error는 검색 시 선택한 lane을 기준으로 한 값이다. 실제 native 초기화에서는 task lane이 y=-0.325232 m에서 y=-0.308915 m로 바뀌어, native 첫 표본의 RH pick-to-ready 거리는 33.711651 mm였다. 검색 error와 native 거리, 그리고 stand-off 목표 오차는 서로 다른 양이다. 실제 native 첫 표본 stand-off 목표 오차는 16.862091 mm였다.

## v4 저장 곡선과 native 이미지

아래 v2 그림은 v4의 300개 native control 표본에서 얻은 거리와 readiness condition을 표시한다. 이전 v1 렌더도 보존했고, 범례가 거리 곡선을 가리지 않도록 범례를 축 바깥으로 옮겼다. 이는 저장 기록의 그래프이며 native 카메라 렌더가 아니다. 왼손 근접 카메라 장면은 손 확대 시점이라 오른손이 화면 가장자리에 일부만 보인다. 전신 이미지는 양손을 포함한다.

![v4 RH 거리와 LH palm/finger 및 전체 readiness 조건의 저장 표본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/figures/v4_readiness_v2/readiness_v4.png)

![v4 실제 Isaac Gym native camera 전신 — 시작](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/frames/whole_body/00000.png)

![v4 실제 Isaac Gym native camera 전신 — 5초 종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/frames/whole_body/00150.png)

![v4 실제 Isaac Gym native camera 왼손 근접 — 시작](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/frames/hands/00000.png)

![v4 실제 Isaac Gym native camera 왼손 근접 — 5초 종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/frames/hands/00150.png)

## 모든 실행의 초기값과 실제 영상

각 실행은 1200 physics steps, 151 native camera frames를 기록했다. v1 영상은 26 frame / 0.866667초에서 종료된 초기 시도다. v2–v4 영상은 151 frame, 30 fps, ffprobe stream duration 5.033333초다. 각 실행의 초기값 JSON, 보고서 및 전신·왼손 근접 영상을 아래에서 확인할 수 있다.

### v1 — 기본 RH IK, 26 frames / 0.866667초

- [초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v1/data/initial_values.json) · [실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v1/data/report.json)

![v1 실제 native 전신 영상 — 26 frames, 0.866667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v1/data/images/whole_body.mp4)

![v1 실제 native 왼손 근접 영상 — 26 frames, 0.866667초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v1/data/images/hands.mp4)

### v2 — RH PI 추가 진단, 151 frames / 5초 물리

- [초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v2/data/initial_values.json) · [실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v2/data/report.json)

![v2 실제 native 전신 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v2/data/images/whole_body.mp4)

![v2 실제 native 왼손 근접 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v2/data/images/hands.mp4)

### v3 — task reset 없는 handoff 연속성 수정, v2 trace와 exact

- [초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v3/data/initial_values.json) · [실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v3/data/report.json)

![v3 실제 native 전신 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v3/data/images/whole_body.mp4)

![v3 실제 native 왼손 근접 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v3/data/images/hands.mp4)

### v4 — 기본 RH IK 복원, 최종 준비 진단

- [초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/initial_values.json) · [실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/report.json) · [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/analysis/summary.json)

![v4 실제 native 전신 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/whole_body.mp4)

![v4 실제 native 왼손 근접 영상 — 151 frames, 5초 물리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/images/hands.mp4)

## 구현·후처리 기록과 다음 범위

- [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_RELATIVE_READY_PLAN.md:1) · [최종 제어 기준 선택](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_READY_BASELINE_SELECTION.md:1) · [최종 preserved-run entry](/home/ajou/yigyu/3/stability_adapter_2/preparation_preserved_run_v4.py:1)
- [readiness helper](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness_v2.py:18) · [CPU 검색 진입점](/home/ajou/yigyu/3/stability_adapter_2/search_strike_ready_pose.py:19) · [readiness 회귀 테스트](/home/ajou/yigyu/3/stability_adapter_2/tests/test_guitar_relative_readiness_v2.py:25)
- [최종 native 초기화/실행 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/data/initial_audit.json) · [981개 입력 사전 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/inputs_before.json) · [사후 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/native_v4/inputs_after.json)
- [v4 readiness 그림 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/figures/plot_readiness_v4_v2.py:1) · [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/figures/v4_readiness_v2/manifest.json) · [후처리 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/figures/v4_readiness_v2/artifact_execution.json)
- [main PLAN 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:142) · [main README 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1447)

다음에는 왼손 넥 underside 지지의 지속 여부와 오른손 현재 ready point 추종 잔여 오차를 구분해 검토해야 한다. 이 문서는 그 후속 실험을 선택하거나 승인하지 않는다. 실제 PLAY/연주 성공, 연속 기하 안전 모니터, 접촉력 인증은 이번 실행에서 확인하지 않았다.
