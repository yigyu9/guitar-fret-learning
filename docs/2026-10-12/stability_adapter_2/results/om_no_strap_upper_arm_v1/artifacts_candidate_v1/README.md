# 초기 기타 목 옆 상완 유지 후보 · native 11/12

두 번의 동일 초기조건 5초 평가에서 종료 시점 바디 bounding-box 중심 변화는 각각 40.206626858 mm, actor-root 위치 변화는 각각 53.017169762 mm였고, 초기 대비 SO(3) 회전은 11.070531790°였습니다. 2초에서 5초까지는 중심 변화 0.073932230 mm, 회전 변화 0.028842817°였습니다. 이 결과는 동일 초기조건의 5초 유지 후보를 보여줄 뿐, 움직이는 연주 강건성이나 학습 성공을 뜻하지 않습니다.

![native 11 초기 자료와 0, 0.5, 2, 5초 whole_body 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v1/native11_initial_and_timeline.png)

![native 11 whole_body 0초와 5초 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v1/native11_zero_to_five_comparison.png)

## 수치 및 관찰 범위

| 구분 | native 11 | native 12 반복 |
|---|---:|---:|
| 바디 bounding-box 중심 종료 변화 | 40.206626858 mm | 40.206626858 mm |
| actor-root 위치 종료 변화 | 53.017169762 mm | 53.017169762 mm |
| 초기 대비 종료 SO(3) 회전 | 11.070531790° | 11.070531790° |
| 2초→5초 바디 중심 변화 | 0.073932230 mm | 0.073932230 mm |
| 2초→5초 SO(3) 변화 | 0.028842817° | 0.028842817° |

actor-root 이동과 바디 bounding-box 중심 변화는 서로 다른 지표입니다. actor-root 이동 53.017 mm를 바디 중심 변화로 읽지 않도록 구분했습니다.

검증 자료의 1200-step endpoint 기록은 오른상완 presence 1187/1200, positive raw lambda 1181/1200, 왼팔/손과 Head 각각 0/1200입니다. raw lambda는 힘 단위 N이 아닙니다. 별도 raw contacts 파일은 초기 step 0과 60 Hz 표본 299개(physics step 4–1196)입니다. 이 표본에서 Chest/RHip/RShoulder 관련 접촉 기록이 있고 RH finger 접촉은 관찰되지 않았지만, 전 기간 RH finger 무접촉을 인증하는 240 Hz 전체 끝점 검사는 없습니다.

두 실행은 실제 strap OFF, strap force call 0, music actor 0, policy/checkpoint 0으로 기록됐으며 root/lower body는 고정 조건입니다. 이번 산출물은 기록된 native 이미지와 동영상의 조합·복사 및 설명이며 native 물리/제어 실행을 추가하지 않았습니다.

## 원본 이미지와 대표 영상

- 초기 native 원본 이미지: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media/initial_native.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v11/upper_arm_neck_side/media/initial_native.png)
- native 11 최종 whole_body 영상: [/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native11_whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native11_whole_body.mp4)

## 원본 영상

- [native 11 · whole_body 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native11_whole_body.mp4)
- [native 11 · hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native11_hands.mp4)
- [native 12 · whole_body 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native12_whole_body.mp4)
- [native 12 · hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native12_hands.mp4)

## 기록

- [candidate 영상 README](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/README.md)
- [candidate 영상 INDEX](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/INDEX.md)
- [manifest_v3.json: source/copy SHA-256](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/manifest_v3.json)
- [입력·출력 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v1/provenance_v1.json)
- [effort_verification_v10_cases4.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/effort_verification_v10_cases4.json)
