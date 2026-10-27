# 왼손 task 없는 native run 영상 색인

원본 MP4를 decode/re-encode하지 않고 byte-exact 복사했다. report에 `videos`와 실제 MP4가 있는 8개 run만 수록한다. 각 파일의 실제 물리 경과시간과 ffprobe 영상 프레임 수·재생시간은 [provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/provenance_v1.json)에 있다. 실패한 부분 영상은 기록된 프레임/시간 그대로 두었으며 5초로 늘리지 않았다. `native_upper50_static`은 0-step constructor 오류로 MP4가 없어 제외했다.

## native_upper50_v12_static — 부분 실행 · safety displacement

Report: 104 physics steps, 26 controls, 0.433333초; report completed=False.

![native_upper50_v12_static whole_body; 실제 14 frames, 0.466667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v12_static_whole_body.mp4)

![native_upper50_v12_static hands; 실제 14 frames, 0.466667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v12_static_hands.mp4)

## native_upper50_v13_static — 정지 조건 · 5초 완료

Report: 1200 physics steps, 300 controls, 5.000000초; report completed=True.

![native_upper50_v13_static whole_body; 실제 151 frames, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v13_static_whole_body.mp4)

![native_upper50_v13_static hands; 실제 151 frames, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v13_static_hands.mp4)

## native_upper50_v14_elbow5 — R_Elbow_y elbow5 wave · 5초 완료

Report: 1200 physics steps, 300 controls, 5.000000초; report completed=True.

![native_upper50_v14_elbow5 whole_body; 실제 151 frames, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v14_elbow5_whole_body.mp4)

![native_upper50_v14_elbow5 hands; 실제 151 frames, 5.033333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v14_elbow5_hands.mp4)

## native_upper50_v4_static — 부분 실행 · 2 physics steps

Report: 2 physics steps, 0 controls, 0.008333초; report completed=False.

![native_upper50_v4_static whole_body; 실제 2 frames, 0.066667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v4_static_whole_body.mp4)

![native_upper50_v4_static hands; 실제 2 frames, 0.066667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v4_static_hands.mp4)

## native_upper50_v5_static — 부분 실행 · 2 physics steps

Report: 2 physics steps, 0 controls, 0.008333초; report completed=False.

![native_upper50_v5_static whole_body; 실제 2 frames, 0.066667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v5_static_whole_body.mp4)

![native_upper50_v5_static hands; 실제 2 frames, 0.066667초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v5_static_hands.mp4)

## native_upper50_v6_static — 부분 실행 · safety displacement

Report: 84 physics steps, 21 controls, 0.350000초; report completed=False.

![native_upper50_v6_static whole_body; 실제 12 frames, 0.400000초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v6_static_whole_body.mp4)

![native_upper50_v6_static hands; 실제 12 frames, 0.400000초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v6_static_hands.mp4)

## native_upper50_v8_static — 부분 실행 · safety displacement

Report: 96 physics steps, 24 controls, 0.400000초; report completed=False.

![native_upper50_v8_static whole_body; 실제 13 frames, 0.433333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v8_static_whole_body.mp4)

![native_upper50_v8_static hands; 실제 13 frames, 0.433333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v8_static_hands.mp4)

## native_upper65_v6_static — 부분 실행 · safety displacement

Report: 92 physics steps, 23 controls, 0.383333초; report completed=False.

![native_upper65_v6_static whole_body; 실제 13 frames, 0.433333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper65_v6_static_whole_body.mp4)

![native_upper65_v6_static hands; 실제 13 frames, 0.433333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper65_v6_static_hands.mp4)

[결과·native frame 사본 링크](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/README.md)
