# 고정 LA에서 어깨 목표 offset 응답 비교

현재 `joint_only_fixed_strap_v1`의 current18 초기 자세를 기준선으로 두고, 같은 고정 LA rest length `1.1018469719600776 m`에서 `L_Shoulder_y` 유지 target에 상수 `−0.008 rad` 또는 `+0.008 rad` offset만 적용한 실제 native 응답을 비교한다. 세 조건 모두 같은 G 초기 위치/자세와 나머지 common 초기 조건을 사용했고, 두 probe에서 나머지 관절 80개의 1200-step 적용 target과 clock/wrist waveform이 기준선과 정확히 일치했다. 초기 q 자체 및 초기 target 필드는 바꾸지 않고 유지 목표 shoulder target만 달리했다.

각 probe는 native 초기화 1회, 1200 step, 0–5초 trace 1201행, 151 frame 영상 2개로 완료됐다. 분석 29개 check와 두 실행의 fresh 검사 14개, source self-screen 1188쌍이 통과했다. 두 probe 모두 human self-contact step 0, palm–guitar positive raw lambda step 0이다. Cable law peak tension은 기준선 `24.625970525 N`, −0.008 조건 `30.18033 N`, +0.008 조건 `24.94381 N`이다. raw contact lambda를 힘 N으로 해석하지 않는다.

## 저장 trace 결과

| 지표 | current18 기준선 | −0.008 rad target | +0.008 rad target |
|---|---:|---:|---:|
| 초기 world 기준 최대 위치 오차 (mm) | 14.084222893 | 15.989064226 | 11.926351230 |
| 초기 world 기준 최대 회전 오차 (°) | 2.920042117 | 2.862552945 | 3.169993195 |
| 5초 위치 오차 (mm) | 13.788517868 | 15.471011383 | 11.848155822 |
| 5초 회전 오차 (°) | 2.919708139 | 2.862350027 | 3.138566142 |
| t=2초 world pose 대비 2–5초 최대 위치 변화 (mm) | 0.257785610 | 0.794536077 | 0.286205939 |
| t=2초 world pose 대비 2–5초 최대 회전 변화 (°) | 0.051002962 | 0.136578782 | 0.052760892 |

두 panel의 curve는 각 시간에서 초기 world 기타 pose와의 위치·회전 오차를 나타낸다. 표의 late 변화는 그 값들의 scalar 차가 아니라 저장된 t=2초 기타 위치 벡터와 quaternion을 기준으로 한 최대 상대 변화이며, 보존된 `analyze_small_wrist_motion.metrics(rows)` helper로 직접 검산했다. 회색 영역은 평가창 위치만 보여준다.

![세 조건의 초기 world pose 위치·회전 오차 curves. 단위는 각각 mm와 degree이며 음영은 2–5초 구간이다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/fixed_strap_shoulder_response.png)

−0.008 조건은 최대/종료 회전 오차가 줄었지만 위치 오차와 후기 변화량이 커졌다. +0.008 조건은 위치 오차는 줄었지만 최대/종료 회전 오차는 커졌고 후기 변화량도 current18보다 약간 컸다. 어느 조건도 초기 world 자세의 완전 복원이나 6D 안정성 향상으로 채택하지 않는다. 단일 shoulder 축의 이 세 점 응답은 순위 상한 1인 한 개 열 자료다. 4–5초 창에서 forward/backward 차이는 central norm 대비 `50.7539%`이며, 비제약 1D least-squares 추정 `+0.027680 rad`는 측정한 `±0.008 rad` 범위 밖이므로 외삽 후보로 채택하지 않는다. 후속 방향은 기준 초기 자세에서 다른 축의 응답을 별도로 측정하는 것이다.

## 실제 native 프레임과 영상

아래 시작/종료 이미지는 shoulder target probe 각각의 손 카메라 native frame이며 CPU 차트와 구별된다. `00000.png`는 초기 프레임, `00150.png`는 약 5초 시점이다.

### −0.008 rad

| 시작 | 약 5초 |
|---|---|
| ![−0.008 rad 조건 hands camera 시작 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/minus008/frames/hands/00000.png) | ![−0.008 rad 조건 hands camera 마지막 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/minus008/frames/hands/00150.png) |

![−0.008 rad shoulder target 조건의 실제 native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/minus008/hands.mp4)

![−0.008 rad shoulder target 조건의 실제 native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/minus008/whole_body.mp4)

### +0.008 rad

| 시작 | 약 5초 |
|---|---|
| ![+0.008 rad 조건 hands camera 시작 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00000.png) | ![+0.008 rad 조건 hands camera 마지막 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png) |

![+0.008 rad shoulder target 조건의 실제 native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/hands.mp4)

![+0.008 rad shoulder target 조건의 실제 native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/whole_body.mp4)

각 영상은 151 frame, 30 fps, 5.033333초 파일이다. 각 trial의 시작 관절값/PD target은 [−0.008 initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/minus008/initial_values.json:1)과 [+0.008 initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/initial_values.json:1)에서 확인할 수 있다. [current18 기준선 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/initial_values.json:1)도 함께 보존했다.

## 범위 및 재현 기록

이 결과는 단일 축 target의 정적 offset 응답 비교다. native feedback controller, 기타 오차 기반 실시간 보정, 전체 66관절 controllability, 연주 성공, 재현성 반복을 입증하지 않는다. Actor inference와 학습은 없다. 세 trace curves는 저장 native raw 기록의 CPU 분석 그림이며 실제 Isaac Gym 영상과 별도다.

- [29개 검사와 요약 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/analysis.json:1)
- [current18/minus/plus trace 및 입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/analysis.json:1)
- [v2축 아닌 이번 producer source](/home/ajou/yigyu/3/stability_adapter_2/make_fixed_strap_shoulder_artifacts.py:1)
- [source snapshot 및 11개 producer/helper 사본 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/source_snapshot.json:1)
- [artifact input/output SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/artifact_manifest.json:1)
- [실행 command/environment/exit 및 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/producer_execution.json:1), [producer log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/producer.log:1)
- [Root 실제 비교 결정과 다음 wrist-y 응답 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:1), [Root 실행·그림 QA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/ROOT_VERIFICATION_NOTES.md:1)
- [메인 README 결과 항목](/home/ajou/yigyu/3/stability_adapter_2/README.md:1013), [실험 계획 결과 항목](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1811), [누적 시각 보고서 §102](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1877), [전체 영상 색인 v7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v7.md:1)
