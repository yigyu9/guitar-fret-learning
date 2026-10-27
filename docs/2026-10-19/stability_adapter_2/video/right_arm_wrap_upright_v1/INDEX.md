# 오른팔 wrap/upright native 영상 색인

네이티브 원본 MP4 16개(기준 2개와 일곱 trial의 전신·손 영상)를 재인코딩 없이 복사했다. 원본/사본 SHA256, ffprobe 해상도·fps·프레임 수·재생시간, 해당 native report의 실제 물리 step/완료 여부는 [manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/manifest_v1.json)에 있다. 부분 실행은 확보한 원래 프레임과 실제 종료 시간을 그대로 유지한다.

## 비교 기준: waist straighten 추가 8°

![이전 waist 추가 8도 기준 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/baseline_add8_static_whole_body.mp4)

![이전 waist 추가 8도 기준 손·기타 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/baseline_add8_static_hands.mp4)

## 선택: native_wrap55 정지와 팔꿈치 목표 wave

![선택 wrap55 정지 전신 5초 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap55_static_whole_body.mp4)

![선택 wrap55 정지 손·기타 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap55_static_hands.mp4)

![선택 wrap55 팔꿈치 wave 전신 5초 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap55_elbow_wave_whole_body.mp4)

![선택 wrap55 팔꿈치 wave 손·기타 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap55_elbow_wave_hands.mp4)

## 부분 중단된 native 진단

아래 다섯 조건은 5초 완료 영상이 아니며 각각 저장된 원래 길이를 유지한다.

- `native_relief12_static`: guitar safety displacement, 424 physics steps, 1.766667초.

![native_relief12_static 전신 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_relief12_static_whole_body.mp4)

![native_relief12_static 손·기타 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_relief12_static_hands.mp4)

- `native_relief20_static`: guitar safety displacement, 128 physics steps, 0.533333초.

![native_relief20_static 전신 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_relief20_static_whole_body.mp4)

![native_relief20_static 손·기타 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_relief20_static_hands.mp4)

- `native_upper20_static`: guitar safety displacement, 148 physics steps, 0.616667초.

![native_upper20_static 전신 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_upper20_static_whole_body.mp4)

![native_upper20_static 손·기타 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_upper20_static_hands.mp4)

- `native_upper40_static`: guitar safety displacement, 232 physics steps, 0.966667초.

![native_upper40_static 전신 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_upper40_static_whole_body.mp4)

![native_upper40_static 손·기타 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_upper40_static_hands.mp4)

- `native_wrap40_static`: guitar safety displacement, 180 physics steps, 0.750000초.

![native_wrap40_static 전신 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap40_static_whole_body.mp4)

![native_wrap40_static 손·기타 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap40_static_hands.mp4)

[초기 이미지, 선택 결과와 측정 한계](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/README.md)
