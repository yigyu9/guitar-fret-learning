# Elbow/wrist 준비 자세 native 산출물

세 개의 완료된 Isaac Gym native 실행만 포함합니다. 각 5초 실행은 1200 physics step, 300 control step입니다. 이미지와 영상은 native 결과 파일의 바이트 그대로 복사했으며, 재렌더·자르기·주석·재인코딩하지 않았습니다. 캡처 메타데이터상 frame 0/60/150은 physics step 0/480/1200, 즉 0/2/5초입니다.

공통 조건은 strap OFF, 기타 free, root/lower 고정, self-collision ON, 유한한 human PD/gravity와 current-G upper-point 제어입니다. 왼손 접촉 0 step, 오른손/손목/손가락 접촉 0 step입니다. 여섯 타현 목표만 허용되며 나머지 75개 target은 유지된 목표 상태이지 실제 움직임이 고정됐다는 뜻은 아닙니다.

분석 기준 최대 기타 body-center 이동은 11.4104487 mm, 최대 SO(3) 변화는 3.8725479°입니다.

## Static — `native_static_v1`

전신/손 확대 캡처: 0초, 2초, 5초.

### 0초 · 전신

![Static 0초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t00_whole_body.png)

### 0초 · 손 확대

![Static 0초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t00_hands.png)

### 2초 · 전신

![Static 2초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t02_whole_body.png)

### 2초 · 손 확대

![Static 2초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t02_hands.png)

### 5초 · 전신

![Static 5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t05_whole_body.png)

### 5초 · 손 확대

![Static 5초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_static_v1_t05_hands.png)

타현 검출 0회.

Native 영상: 전신

![Static 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_static_v1_whole_body.mp4)

Native 영상: 손 확대

![Static 손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_static_v1_hands.mp4)

## Strike — `native_strike_v1`

전신/손 확대 캡처: 0초, 2초, 5초.

### 0초 · 전신

![Strike 0초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t00_whole_body.png)

### 0초 · 손 확대

![Strike 0초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t00_hands.png)

### 2초 · 전신

![Strike 2초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t02_whole_body.png)

### 2초 · 손 확대

![Strike 2초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t02_hands.png)

### 5초 · 전신

![Strike 5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t05_whole_body.png)

### 5초 · 손 확대

![Strike 5초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_strike_v1_t05_hands.png)

down 순서 6→1 완료, up 방향은 string 1만 검출되어 6현 up 완료로 볼 수 없습니다.

Native 영상: 전신

![Strike 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_strike_v1_whole_body.mp4)

Native 영상: 손 확대

![Strike 손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_strike_v1_hands.mp4)

## Velocity — `native_velocity_v1`

전신/손 확대 캡처: 0초, 2초, 5초.

### 0초 · 전신

![Velocity 0초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t00_whole_body.png)

### 0초 · 손 확대

![Velocity 0초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t00_hands.png)

### 2초 · 전신

![Velocity 2초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t02_whole_body.png)

### 2초 · 손 확대

![Velocity 2초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t02_hands.png)

### 5초 · 전신

![Velocity 5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t05_whole_body.png)

### 5초 · 손 확대

![Velocity 5초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/native_velocity_v1_t05_hands.png)

down 순서 6→1 완료. up 방향은 1, 2, 6만 검출되어 불완전합니다.

Native 영상: 전신

![Velocity 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_velocity_v1_whole_body.mp4)

Native 영상: 손 확대

![Velocity 손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_velocity_v1_hands.mp4)

## Provenance

- 입력과 producer의 실행 전·후 SHA, 프레임 출처, byte-copy 결과와 ffprobe 정보: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/provenance_v1.json)
- 실행 전 pin: [{A}/preflight_pin_v1.json]({A}/preflight_pin_v1.json)
- 배포 영상 색인: [{V}/INDEX_v1.md]({V}/INDEX_v1.md)
- 이 묶음은 위 세 완료 실행만 대상으로 합니다. 진행 중일 수 있는 다른 실행은 읽거나 포함하지 않았습니다.
