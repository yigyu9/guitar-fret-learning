# 오른팔 전방 이동 native 영상 색인

기준, 5초 선택 결과, 거절된 partial의 전신·손 영상 여섯 개를 원본 MP4에서 byte-exact로 복사했다. source/copy SHA, frame 크기·fps·프레임 수·재생시간, report 완료 상태는 [manifest_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/manifest_v3.json)에 기록했다.

## 비교 기준: wrap55 static (5초 완료)

![기준 wrap55 static 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/baseline_wrap55_static_whole_body_v3.mp4)

![기준 wrap55 static 손·기타 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/baseline_wrap55_static_hands_v3.mp4)

## 선택 결과: elbow10 static (5초 완료)

![선택 elbow10 static 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/native_elbow10_static_whole_body_v3.mp4)

![선택 elbow10 static 손·기타 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/native_elbow10_static_hands_v3.mp4)

## 거절 후보: forward5 static (partial, 152 physics steps/0.633333초)

![거절 forward5 partial 전신 영상, 실제 확보분 20 frames/0.666667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/native_forward5_static_whole_body_v3.mp4)

![거절 forward5 partial 손·기타 영상, 실제 확보분 20 frames/0.666667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/native_forward5_static_hands_v3.mp4)

[정정 이미지 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/README_V2.md)
