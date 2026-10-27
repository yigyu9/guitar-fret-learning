# 무스트랩 상완 지지 후속 진단 · 시각 자료

이 폴더에는 완료된 native 10의 원본 Isaac Gym `whole_body` 캡처 프레임으로 만든 시간 패널 한 장과 생성 출처 기록이 있습니다. 패널은 프레임을 축소·배치하고 캡션을 더한 정적 조합이며 시뮬레이션을 다시 실행하지 않았습니다.

![native 10의 0, 0.1, 0.3, 0.5, 5초 캡처 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_diagnostics_v2/native_v10_whole_body_timeline.png)

패널은 native 10의 기록 장면을 시간순으로 보여줍니다. 힘 분포, 실제 접촉력, 관통 또는 안정성을 시각적으로 측정하거나 인증하는 그림이 아닙니다. 오른쪽 상완 접촉은 검증 자료의 endpoint contact query 수치로 별도 기록되어 있습니다.

보관한 영상 10개와 조건별 설명은 [영상 README](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/README.md) 및 [영상 INDEX](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/INDEX.md)에 있습니다. 기존 trial 1–4 보관본은 [manifest_v1](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/manifest_v1.json)에 남아 있습니다.

## 집계값

아래 root 이동·회전은 해당 trial 시작 상태 대비 actor-root 변위이며 body 중심 변위가 아닙니다. endpoint 접촉 수는 1200 physics step 중 query 결과입니다. raw lambda는 힘 단위(N)가 아니며, 접촉 query는 힘 분포나 연속 시간 접촉을 보증하지 않습니다.

| Trial | actor-root 종료 변위 | actor-root 회전 | 핵심 endpoint 기록 |
|---|---:|---:|---|
| 시험 5 · 오른상완 hold | 462.505 mm | 106.208° | 오른상완 0/1200 · 왼팔 0/1200 |
| 시험 6 · 상대 피드백 | 477.357 mm | 108.661° | 오른상완 0/1200 · 왼팔 0/1200 |
| 시험 7 · 3지점 지지·기울기 12 | 306.010 mm | 50.005° | 오른상완 0/1200 · 왼팔 0/1200 · Head 다수 |
| 시험 9 · 오른쪽 effort | 302.707 mm | 49.459° | 오른상완 0/1200 · 왼팔 0/1200 · Head 1086/1200 |
| 시험 10 · 상대 effort·microgap | 432.659 mm | 120.114° | 오른상완 53/1200 (raw λ 양성 37) · 왼팔 0/1200 · Head 60/1200 |

## 첫 step에서 멈춘 native 8

native 8은 첫 step assert 실패로 physics step 0에서 종료됐습니다. 생성된 whole_body/hands 파일은 각각 1 frame, ffprobe duration 0.034초로 확인되어 완료 trial 영상과 분리합니다. 이 짧은 원본은 복사본 manifest에 포함하지 않았습니다.

- [native 8 짧은 whole_body 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/whole_body.mp4)
- [native 8 짧은 hands 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/hands.mp4)

## 출처

- [verification_v8.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/verification_v8.json) · trial 5–7 포함
- [effort_verification_v9_cases2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/effort_verification_v9_cases2.json) · trial 9–10
- [provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_diagnostics_v2/provenance_v2.json) · 입력 전후 및 출력 SHA-256
