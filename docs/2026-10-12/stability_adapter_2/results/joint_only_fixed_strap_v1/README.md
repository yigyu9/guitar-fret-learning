# 고정 스트랩 길이·관절만 조절 실제 비교

이 phase는 기존 original LA 기준 `small_wrist_motion_v1`과 관절 초기각/대응 PD목표만 바꾼 후보를 같은 고정 LA rest length `1.1018469719600776 m`에서 비교한다. 새 native 실행은 1회 초기화·1200 physics steps이며, 전신과 손 카메라에서 각 151 frame을 저장했다. 추가 actor inference와 학습은 0이다. 두 조건은 body9 PD×2, 기타 초기 위치/자세, root·하체, ±0.005 rad·1 Hz 손목 파형 등 공통 초기 조건을 유지했고, 초기 왼팔 12개 좌표와 LH 단일 hinge 6개 좌표 및 해당 PD 목표만 이동했다. 초기각 최대 차이는 `0.002616494894 rad`였다. 나머지 63개 좌표/목표와 기존 33개 target offset은 유지했다.

## 수치 결과

| 지표 | 기존 original LA 기준 | 관절만 조절 후보 |
|---|---:|---:|
| 초기 world 기타 위치 최대 오차 (mm) | 14.132607728 | 14.084222893 |
| 초기 world 기타 회전 최대 오차 (°) | 2.894327802 | 2.920042117 |
| 5초 종료 위치 오차 (mm) | 13.817898232 | 13.788517868 |
| 5초 종료 회전 오차 (°) | 2.894219060 | 2.919708139 |
| t=2초 기준, 2–5초 최대 위치 변화 (mm) | 0.481766500 | 0.257785610 |
| t=2초 기준, 2–5초 최대 회전 변화 (°) | 0.091929111 | 0.051002962 |
| passive cable 최대 장력 (N) | 24.129230476 | 24.625970525 |

2–5초 변화량은 각각 46.4916%와 44.5192% 작아졌지만, 이는 한 후보의 실제 native 결과이지 합격 문턱이나 반복 검증이 아니다. 최대 초기 회전 오차는 0.025714316° 증가했고 초기 world 기타 오차도 약 14 mm/2.92° 남았다. 한 번의 비교로 후기 유지성 개선은 관찰했으나 초기 자세 복원, 완전한 grip, 전 구간 연주 성공으로 판정하지 않는다. 후보는 고정-LA 후속 유지성 비교 기준으로 보존하고, 스트랩 탐색변수는 다시 열지 않는다.

![저장된 native trace의 초기 world 기타 위치·회전 오차. 음영은 2–5초 구간이며 두 패널의 단위는 각각 mm와 degree다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/joint_only_fixed_strap_timeseries.png)

차트는 저장된 actual trace를 분석해 그린 CPU 그림이며 native 카메라 프레임이 아니다. 위치는 각 시각의 기타 위치와 초기 world 위치 간 거리, 회전은 초기 world 자세와의 각도다. 회색 음영은 후기 구간 표시다. 2–5초 요약 변화는 저장된 t=2초 자세를 기준으로 원본 분석 helper의 벡터 위치차 및 quaternion 상대각 metric을 직접 호출해 재검산했다.

## 실제 native 캡처

후보 실행에서 저장된 손 카메라 프레임이다. `00000.png`는 초기 프레임, `00150.png`는 30 fps로 저장한 약 5초 시점의 마지막 프레임이다.

| 시작 프레임 | 마지막 프레임 |
|---|---|
| ![후보 hands camera frame 00000, 초기 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00000.png) | ![후보 hands camera frame 00150, 약 5초 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png) |

손 카메라 실제 native 영상:

![관절만 조절 후보의 실제 native 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/hands.mp4)

전신 카메라 실제 native 영상:

![관절만 조절 후보의 실제 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/whole_body.mp4)

두 영상은 각각 151 frame, 30 fps, 5.033333초 파일이며 시뮬레이션 trace의 0–5초 관측을 담는다. passive strap rest length는 두 조건에서 같지만 관절 변화로 route length가 `1.085833274828 m`에서 `1.085744687068 m`로 달라졌고, cable law peak tension도 `24.129230476 N`에서 `24.625970525 N`로 바뀌었다. 길이를 고정한 것은 strap을 제거하거나 힘을 0으로 만든 것과 다르다.

## 접촉 및 범위

실제 native 검사에서 사람 self-contact step은 두 조건 모두 0이다. 손바닥의 기타 접촉 positive raw lambda 기록도 0이며, 검지/엄지 등의 기록을 지속적인 palm 지지 또는 해부학적 pad 접촉 인증으로 확대하지 않는다. raw lambda는 힘의 N 단위가 아니다. source 형상 검사는 동적 PhysX 비관통이나 연속 접촉의 증명도 아니다. 새 후보의 최대 actual 관절 제한 초과는 약 `9.98e−5 rad`로 기록됐다.

이 후보는 정적인 초기각/PD목표 변경이다. 현재 G 연주 오차를 읽는 feedback 보정, 전체 grip 성공, 반복 재현, 학습 또는 actor 연결은 구현·검증하지 않았다. 기존 Fret profile의 6개 관절 호환 문제가 남아 있다. 후속 작업은 현재 G 연주 정확도와 초기 world 기타 유지 목표를 함께 다루는 설계를 기준으로 하며, 작은 고정-LA native 시험으로 계속 검증한다.

## 원자료와 재현성

- [17개 분석 검사와 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/analysis.json:1)
- [초기 상태 및 PD 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/initial_values.json:1)
- [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/trace.jsonl:1), [contacts](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/contacts.jsonl:1), [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/states.jsonl:1)
- [Root 비교 결정](/home/ajou/yigyu/3/stability_adapter_2/JOINT_ONLY_FIXED_STRAP_DECISION.md:1)
- [v2 producer source](/home/ajou/yigyu/3/stability_adapter_2/make_joint_only_fixed_strap_artifacts_v2.py:1), [v2 source snapshot 및 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/source_snapshot.json:1)
- [v2 artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/artifact_manifest.json:1), [실행 기록 및 0-call 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/producer_execution.json:1), [producer log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/producer.log:1)
- [v1 producer의 보존된 실패 시도](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v1_failed_attempt/producer_execution.json:1), [v1 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v1_failed_attempt/producer.log:1)

첫 v1 producer는 t=2초 이후 변화를 scalar initial-error 값의 차로 계산해 저장된 분석 요약과 일치하지 않아 그림/manifest 생성 전에 종료했다. 원본 producer, 실패 로그와 메타데이터를 보존했다. metric 정의를 바로잡은 독립 v2 source에서 보존된 `analyze_small_wrist_motion.py`의 `metrics(rows)`를 직접 호출하여 다시 생성했다. v2는 Python 3.8 환경에서 exit 0으로 실행됐고, 입력과 producer의 실행 전후 SHA-256이 일치했다. 이 artifact 생성에는 native 초기화/physics, actor inference, training이 없었다. 실패한 v1의 입력 전후 SHA 맵은 당시 기록되지 않아 복구되지 않았으며, v2 manifest는 성공한 v2 실행의 봉인 기록이다.
