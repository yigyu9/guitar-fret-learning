# 준비 자세에서 Strike 진단 연결

이 기록은 선택된 prepared candidate 1에서 0–2초 동안 기존 IK와 LH PI로 준비한 뒤, 별도의 진단 시작 조건으로 Strike checkpoint를 연결해 5초까지 실행한 결과다. strict 준비 조건을 통과한 뒤 PLAY로 전환한 실험은 아니다. 실행 report의 15개 contract check가 모두 참이고, 986개 입력 closure는 실행 전후 변경되지 않았다. 기존 strict gate(오른손 50 mm 준비 거리와 왼손 palm 접촉을 포함한 6개 연속 control 표본)는 유지됐지만, 이 진단 entry에서는 사용하지 않았다. 2초 전이 시점의 strict 준비 상태는 false였고, 왼손 palm-under-neck 조건도 false였다.

기타는 strap OFF로 자유 운동하고 root와 하체는 고정했다. 몸통 9축 목표도 초기 PD 목표로 유지했다. 연결 후에는 30차원 checkpoint action, LH 12축 PI, R Thorax 3축 prepared hold, 나머지 36축 hold를 결합해 81관절 목표를 단일 제출했다. native joint limits와 0.8 rad/s 목표 변화율 제한을 사용했다. 학습·외력·기타 고정·상태 덮어쓰기는 없었다.

## 구간별 기록

| 구간 | 기록된 동작 | 결과 |
|---|---|---|
| 0–2초 | 기존 준비 IK와 LH PI; Strike actor 없음, 준비 clock 정지 | 2초에 진단 시작. relaxed 80 mm 기준은 통과했으나 strict 50 mm/palm gate는 false |
| 2–5초 | frozen Strike checkpoint로 180 control step 실행 | 정책 모드는 PLAY로 연결됐지만 readiness motor phase는 계속 0이었고, 실제 인정 타현은 없었다 |
| 전체 | 1200 physics step, 151 frame / 카메라별, 30 fps | 종료·HOLD 없이 5초 기록 완료. PLAY 종료 시각 5초는 성공한 episode 종료를 뜻하지 않는다 |

2초 전이 표본의 오른손 pick-to-ready 거리는 57.003 mm였다. 이는 이번 진단의 80 mm 기준과 원래 50 mm strict 근접 gate가 서로 다른 기준임을 보여준다. 전이 사전검사에서 목표 형상·목표 연속성·history 보존과 native 목표 범위 검사는 통과했지만, strict 왼손 palm 지지는 인증되지 않았다.

정책 180개 sample의 현재 기타 사용자 범위 monitor는 64/180에서 참, 116/180에서 거짓이었다. 처음 범위를 벗어난 sample은 3.066667초다. 이 monitor는 중단이나 경계 복귀 제어가 아니어서 정책은 이후에도 실행됐다. 기타 위치 오차의 최대/끝 값은 59.579/23.034 mm, 회전 오차는 46.151/46.036°였다. 큰 회전 오차가 남아 있고, 사용자 범위 안에서 계속 연주했다는 뜻은 아니다.

왼손 palm contact는 정책 표본 75/180, finger-neck contact는 180/180에 기록됐지만 palm과 finger가 함께 지속 지지했다는 증거로 해석하지 않는다. 오른손 접촉 행은 0이었다. saved source-event pulse 집계는 target hit 0, physical target hit 0, physical release 1, miss 8, wrong crossing 1, accepted release 0이었다. 원본 motor phase는 관측 구간 내내 readiness phase 0이었다. source song은 마지막 sample에서 2.523098초 지점까지 진행했고 전체 episode는 끝나지 않아 완전한 곡의 성능 지표는 없다. 따라서 이 연결 진단은 실제 Strike episode 성공을 입증하지 않는다.

이번 실행은 공식 G0 checkpoint qualification이 아니며, source의 명시적 stiffness torque와 native implicit-PD/rate-limit actuator가 다르다. 이 차이만으로 원본 정책의 일반 호환 여부를 결론내리지 않는다. source geometry의 지속 안전, 전체 상체 자세 안전 또는 접촉력은 이 5초 기록으로 인증하지 않았다.

## 저장된 native 장면과 영상

아래 still은 실제 Isaac Gym native camera 출력이며, `00000`, `00060`, `00150`은 각각 0초, 2초, 5초 표본이다. hands 카메라는 왼손 근접 시점이라 오른손은 화면 가장자리에 일부만 보인다. 전신 카메라는 두 손을 함께 보여준다.

### 전신 카메라

![0초 native 전신 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/whole_body/00000.png)

![2초 native 전신 프레임, 진단 정책 시작 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/whole_body/00060.png)

![5초 native 전신 프레임, 기록 종료 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/whole_body/00150.png)

### 왼손 근접 카메라

![0초 native 왼손 근접 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/hands/00000.png)

![2초 native 왼손 근접 프레임, 진단 정책 시작 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/hands/00060.png)

![5초 native 왼손 근접 프레임, 기록 종료 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/hands/00150.png)

각 영상은 151 frames, 30 fps이며 ffprobe stream duration은 5.033333초다. 영상은 실제 native 카메라 녹화이고 후처리 source-shape 그림이 아니다.

![전신 실제 native 영상 — 5초 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/whole_body.mp4)

![왼손 근접 실제 native 영상 — 5초 기록, 오른손은 일부만 보임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/hands.mp4)

## 실행 및 분석 자료

- [승인된 준비-Strike 연결 계획](/home/ajou/yigyu/3/stability_adapter_2/PREPARED_STRIKE_CONNECTION_PLAN.md:1) · [메인 PLAN 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:160) · [메인 README 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1465)
- [준비 조건과 진단 시작 predicate](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_start.py:25) · [실행 runner](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:24) · [preserved-run entry](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_preserved_run.py:12)
- [실행 report 및 native checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/report.json) · [checkpoint connection 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/checkpoint_connection.json) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/initial_values.json)
- [통합 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/analysis/summary.json) · [source event pulse 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/event_analysis/summary.json) · [실행 입력 사전/사후 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/inputs_before.json)
- [CPU 진단 분석기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/analyze_connection.py:12) · [phase 봉인 도구](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/seal_phase.py:13) · [결과 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/CHANGED_FILES.md:1)
