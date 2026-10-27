# EW 준비 자세 추가 native 결과 — v2

두 실행 모두 5.0초 native 관측(1200 physics step, 300 control step)을 완료했습니다. 영상은 30 fps 151프레임, 인코딩 duration 5.033333초입니다. 프레임 0/60/150은 native capture 메타데이터에서 0/2/5초에 대응합니다. 아래 이미지와 영상은 원본을 바이트 그대로 복사했으며 변형하거나 재인코딩하지 않았습니다.

두 조건 모두 left contact 0, 오른손/손목/손가락 contact 0, 최대 기타 body-center 이동 11.4104486918 mm, 최대 SO(3) 변화 3.8725478784°였습니다. Strap은 OFF, checkpoint 연결과 training update는 0입니다. 나머지 75 target은 목표값 유지이며 실제 자세 변화를 고정했다는 뜻은 아닙니다. 상체 finite control은 계속 활성입니다.

## Slow-up (`native_slow_up_v1`)

down 6→1은 검출됐지만 up은 1·3·5만 검출되어 여섯 현 up 조건은 통과하지 못했습니다.

### 0초 · 전신

![Slow-up 0초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t00_whole_body.png)

### 0초 · 손 확대

![Slow-up 0초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t00_hands.png)

### 2초 · 전신

![Slow-up 2초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t02_whole_body.png)

### 2초 · 손 확대

![Slow-up 2초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t02_hands.png)

### 5초 · 전신

![Slow-up 5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t05_whole_body.png)

### 5초 · 손 확대

![Slow-up 5초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_slow_up_v1_t05_hands.png)

전신 영상

![Slow-up 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_slow_up_v1_whole_body.mp4)

손 확대 영상

![Slow-up 손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_slow_up_v1_hands.mp4)

## Pick-feedback (`native_pick_feedback_v1`)

slow-up과 같은 close 90 초기값, 기하, 시간 조건에 Cartesian pick feedback을 더하고 EW6 effort를 사용했습니다. Feedback 설정은 4000/40, norm 20 N입니다. down 6→1과 up 1→6 모두 통과했고 12개 release 모두 lane_core=True였습니다. 최대 이동·회전은 slow-up과 같았고, 최종 이동은 9.91742481 mm, 최종 SO(3)는 3.35878752°였습니다. 여섯 현 통과는 해당 분석의 접촉/release 검출 판정이며 실제 악기 연주 품질을 보장하지 않습니다.

### 0초 · 전신

![Pick-feedback 0초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t00_whole_body.png)

### 0초 · 손 확대

![Pick-feedback 0초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t00_hands.png)

### 2초 · 전신

![Pick-feedback 2초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t02_whole_body.png)

### 2초 · 손 확대

![Pick-feedback 2초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t02_hands.png)

### 5초 · 전신

![Pick-feedback 5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t05_whole_body.png)

### 5초 · 손 확대

![Pick-feedback 5초 손 확대](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t05_hands.png)

전신 영상

![Pick-feedback 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_pick_feedback_v1_whole_body.mp4)

손 확대 영상

![Pick-feedback 손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_pick_feedback_v1_hands.mp4)

## 검증 자료

- 실행 분석 및 입력 핀: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/analysis_v4.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/analysis_v4.json)
- 패키지 입력 사전 pin: [{A}/preflight_pin_v2.json]({A}/preflight_pin_v2.json)
- 전후 SHA, 프레임 출처, ffprobe 및 출력 SHA: [{A}/provenance_v2.json]({A}/provenance_v2.json)
- 앞선 세 케이스: [{V}/INDEX_v1.md]({V}/INDEX_v1.md)
