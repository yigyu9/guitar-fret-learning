# 무스트랩 오른상완 지지 trial 5–10 영상 색인 (v2)

아래는 새 보관본 10개입니다. trial 5, 6, 7, 9, 10의 전신 및 손 영상을 원본 bytes 그대로 복사했습니다. 각 source/copy SHA-256은 [manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/manifest_v2.json)에 있습니다. 영상은 각 30 fps, 151 frames, 5.033333초입니다.

## 결과 요약

다섯 완료 trial 모두 오른상완의 독립 지지 성공으로 확인되지 않았습니다. trial 5–7은 오른상완과 왼팔 접촉이 0/1200입니다. trial 9도 양쪽 팔 접촉이 0/1200이고 Head 접촉이 1086/1200입니다. trial 10은 오른상완 접촉 53/1200(positive raw lambda 37), 왼팔 0/1200, Head 60/1200이며 actor-root 종료 변위 432.659 mm, 회전 120.114°였습니다. raw lambda는 힘(N)이 아니며 접촉 수는 그 자체로 지지 성능을 뜻하지 않습니다.

## 완료 trial 영상

### 시험 5 · 오른상완 hold

오른상완 접촉 0/1200, 왼팔 접촉 0/1200. 기타 지지 성공으로 확인되지 않았습니다.

- 전신: [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial05_upper_arm_right_hold_whole_body.mp4)
- 손: [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial05_upper_arm_right_hold_hands.mp4)

### 시험 6 · 상대 피드백

오른상완 접촉 0/1200, 왼팔 접촉 0/1200. 기타 지지 성공으로 확인되지 않았습니다.

- 전신: [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial06_upper_arm_relative_feedback_whole_body.mp4)
- 손: [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial06_upper_arm_relative_feedback_hands.mp4)

### 시험 7 · 3지점 지지·기울기 12

오른상완 접촉 0/1200, 왼팔 접촉 0/1200. 여러 샘플에서 Head 접촉이 관찰됐으며 지지 성공으로 확인되지 않았습니다.

- 전신: [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial07_three_support_lean12_whole_body.mp4)
- 손: [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial07_three_support_lean12_hands.mp4)

### 시험 9 · 오른쪽 effort

오른상완 접촉 0/1200, 왼팔 접촉 0/1200, Head 접촉 1086/1200. 기타 root 변위가 컸고 독립 지지가 확인되지 않았습니다.

- 전신: [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial09_three_support_right_effort_whole_body.mp4)
- 손: [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial09_three_support_right_effort_hands.mp4)

### 시험 10 · 상대 effort·microgap

오른상완 접촉 53/1200(positive raw lambda 37), 왼팔 접촉 0/1200, Head 접촉 60/1200. 큰 root 변위와 회전이 관찰되어 지지 성공으로 볼 수 없습니다.

- 전신: [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial10_three_support_relative_effort_microgap_whole_body.mp4)
- 손: [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v2/trial10_three_support_relative_effort_microgap_hands.mp4)

## 별도 기록: 실패한 native 8

native 8은 첫 step assert 실패, physics step 0입니다. 1 frame/0.034초 파일은 정상 완료 영상과 분리해 원본 위치로 연결하며, 이번 복사 manifest에는 넣지 않았습니다.

- [native 8 원본 whole_body (1 frame)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/whole_body.mp4)
- [native 8 원본 hands (1 frame)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/hands.mp4)

## 이전 보관

첫 네 trial의 보관은 [기존 manifest_v1](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/manifest_v1.json)와 [diagnostics_v1 README](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/diagnostics_v1/README.md)에서 확인할 수 있습니다. 이번 v2는 이전 산출물을 덮어쓰지 않습니다.

## 시각 자료 및 해시

- [native 10 시간 패널 및 해석 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_diagnostics_v2/README.md)
- [native 10 시간 패널 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_diagnostics_v2/native_v10_whole_body_timeline.png)
- [입력·출력 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_diagnostics_v2/provenance_v2.json)
