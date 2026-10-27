# 상완 정적 지지 조건의 native 비교

## 실험 범위

이는 동일한 초기 기타 위치·orientation, 동일한 root lower-body q와 finger/head 초기 q, 동일한 PD 속성으로 수행한 네 개의 5초 native 물리 진단입니다. 조건은 reference, 상완 고정 목표 0°, 3°, 5°이며, 모든 실행은 저장된 `q_ref`를 5초 내내 일정하게 제출했습니다. 음악 policy, checkpoint, reset noise는 사용하지 않았고 training-ready 실행도 아닙니다. Root 검증은 native 32개 검사와 same-condition 8개 검사를 모두 통과했습니다. 네 실행은 각각 1,200 physics steps, 300 control steps, 5.0초를 완료했고, 입력 봉인은 unchanged입니다.

상완 0°/3°/5° 조건의 이름 `gap500`은 source 설정에서 요청한 0.5 mm 간격을 뜻합니다. `verification_v2.json`의 `predicted_initial_support_gap_mm`는 reference 45.46323995 mm, 상완 0° 1.32916649 mm, 3° 0.50359291 mm, 5° 0.50350287 mm입니다. 이 값은 원본 FK로 계산한 오른쪽 상완 capsule 지지점과 기타 상단 평면 사이의 signed gap 예측이며, PhysX cooked 형상의 실제 최단 간격이나 native contact 측정값이 아닙니다. 3°와 5°는 각도 조건 라벨이고 간격의 정수 부분이 아닙니다. 요청 간격과 source-FK 예측 간격을 구분하며, 양의 예측 gap만으로 native 접촉이나 지속 지지를 인증하지 않습니다.

v1 준비 설정은 `prep_seconds=5`, `diagnostic_seconds=5`로 준비 구간과 전체 horizon이 같아 0초 분모가 되는 설정 오류가 확인됐습니다. 이 보고서의 실제 비교는 해당 산출물을 사용하지 않고 `prep_seconds=2`로 수정된 v2 native 실행만 다룹니다. 사전 source 점검 단계의 plugin-load 경고는 native 물리 실행 결과가 아니며, 아래 네 v2 native 실행은 모두 정상 완료됐습니다.

## 실제 native frame

각 패널은 실제 native capture의 0초(frame 0), 2초(frame 60), 5초(frame 150)를 표시합니다. 캡션에 적힌 상완 각도는 초기 Chest 목표 차이이고, 움직이는 동안의 실제 Chest 변화는 표에 따로 기록했습니다.

![네 조건의 native 전신 프레임: 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/native_whole_body_frames_v1.png)

![네 조건의 native 손 프레임: 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/native_hands_frames_v1.png)

## 기타 actor-root 움직임

위치 변화는 각 실행의 자기 초기 actor-root 위치로부터의 world 거리이고, 회전은 자기 초기 quaternion에 대한 SO(3) 거리입니다. 이는 body-center 자연범위나 허용 orientation 기준이 아닙니다. 2–5초 패널은 실제 native trace에서 2초 상태를 다시 기준으로 계산했습니다.

![실제 native actor-root 위치 및 quaternion 변화, 전체 0–5초와 후기 2–5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/root_motion_traces_v1.png)

| 조건 | 초기 Chest 목표 차이 | 5초 actor-root 위치 변화 | 5초 초기 대비 SO(3) | 2→5초 위치 변화 | 2→5초 SO(3) 변화 | 5초 actor-root Z |
|---|---:|---:|---:|---:|---:|---:|
| reference | 0° | 112.7597 mm | 19.6282° | 1.17461 mm | 0.228258° | 0.614418 m |
| 상완 0° | 0° | 100.4937 mm | 15.9601° | 0.304823 mm | 0.124557° | 0.624504 m |
| 상완 3° | 3° | 105.9062 mm | 17.4057° | 0.062397 mm | 0.016754° | 0.621017 m |
| 상완 5° | 5° | 107.8307 mm | 18.3376° | 0.465878 mm | 0.167869° | 0.619541 m |

late 2–5초 변화량은 작았지만 네 조건 모두 초기에 약 100–113 mm와 16–20°가량 움직인 뒤의 후기 값입니다. 시작 자세 유지 성공이나 안정화 성공으로 볼 수 없습니다. 모든 종료 actor-root Z는 기존 비교값 0.65 m보다 낮지만, 이것만으로 body-center 자연범위 판정을 내리지 않습니다. 실제 native Chest는 초기 대비 최대 reference 3.9965°, 상완 0° 3.7042°, 3° 4.2899°, 5° 4.6618° 변했습니다. 초기 Chest 목표 차이 0°/0°/3°/5°와 dynamic 실행 중 변화를 구분해야 합니다.

## 접촉 관측

Contact query는 60 Hz control 업데이트 직전의 300개 시점입니다. R_Elbow는 전완 capsule을 가리킵니다. 표는 해당 이름의 contact가 관측된 시점 수이며, raw λ의 크기를 힘(N)으로 환산하지 않습니다.

| 조건 | R_Elbow | R_Shoulder | LH palm | R_Hip | Chest/Torso/Spine |
|---|---:|---:|---:|---:|---:|
| reference | 282/300 | 0/300 | 286/300 | 296/300 | 0/300 각각 |
| 상완 0° | 289/300 | 0/300 | 277/300 | 296/300 | 0/300 각각 |
| 상완 3° | 288/300 | 0/300 | 280/300 | 296/300 | 0/300 각각 |
| 상완 5° | 287/300 | 55/300 | 282/300 | 296/300 | 0/300 각각 |

상완 5°의 R_Shoulder 접촉은 0.4333–1.3333초 사이 55개 시점에서만 나타났습니다. 모든 조건에서 전완 접촉은 거의 전체 구간에 걸쳐 관측됐고, 어깨 접촉은 대부분 없었습니다. 따라서 이번 자료만으로 요청한 겨드랑이/상완 지지가 실현됐다고 말할 수 없습니다. Raw λ는 원시 solver 관측이며 N 단위 힘, 압력 또는 지지력으로 취급하지 않습니다.

## 제어·strap 및 판정 범위

모든 조건은 같은 초기 기타 위치·orientation, PD 속성, finger/head 초기 q, 원래 strap L0 법칙으로 실행했습니다. Strap route는 초기 상완 배치에 따라 달라질 수 있습니다. Strap callback은 각 1,200 physics step에서 15,600회(13×1,200) 기록됐으며 호출 수는 힘의 크기를 나타내지 않습니다. 금지 API 호출과 music actor/policy/checkpoint 호출은 모두 0입니다. 3°/5° 초기 Chest 회전은 native 측정상 각각 3.0000035°/5.0000009°이고, 고정 target은 실행 중 움직이는 q_ref가 아닙니다.

이 결과는 조건별 초기 기하와 5초 정적 PD 반응을 비교합니다. 초기 위치 유지, 상완 지지 구현, 음악 수행 또는 학습 성능의 성공을 판정하지 않습니다.

## 자료

- [전체·후기 이동 그래프 생성기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/make_static_support_figures_v1.py)
- [native 실행 검증 32개 항목](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/verification_v2.json)
- [동일 조건 검증 8개 항목](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/same_conditions_verification_v1.json)
- [조건별 분석 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/analyze_static_v2.py)
- [네 조건·8개 원본 영상의 SHA 매니페스트](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/manifest.json)
- [8개 영상 모음과 설명](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/README.md)
- [산출물 입력·출력 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/provenance_v1.json)
