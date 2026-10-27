# 왼손 task 없이 기타 자세 유지: native 결과 자료

이 자료는 `native_upper50_v13_static`과 `native_upper50_v14_elbow5`의 실제 5초 native 결과 및 같은 탐색 단계에서 생성된 부분/실패 run의 원본 미디어를 정리한다. MP4와 PNG는 원본 파일의 바이트 그대로 복사했다. 자르기·montage·주석·재인코딩·프레임 추가는 하지 않았다.

## 선택된 정지·팔꿈치 wave 결과

두 실행 모두 1200 physics step/300 control step까지 5.0초 완료했고, 왼손 task/접촉은 0, strap OFF다. 초기 body-centre world 위치는 `(0.099992, 0.009666, 0.704884) m`다. 정지 v13의 최대 BB-centre 이동/회전은 15.856 mm/5.557°, 최종값은 10.214 mm/3.494°다. v14에서 실제 R_Elbow_y scalar 범위는 9.983° peak-to-peak이며, 정지 대비 같은 시점의 추가 기타 변화 최대는 0.01414 mm/0.00854°다. 이는 완전한 팔꿈치 파형 실행 동안 측정한 값이다.

인체에는 유한 virtual PD와 중력이 작동하고, 오른쪽 현재 기타 G점 제어도 켜져 있었다. 따라서 결과는 무제어 또는 수동 평형 시험이 아니며 checkpoint 연결이나 연주 성공을 뜻하지 않는다. 왼손 task가 없는 조건에서도 이 제어들이 유지됐다는 범위로 해석한다. static v13의 4→5초 BB-centre/SO(3) 변화는 0.000381 mm/0.000803°이고, 이는 1200-step 물리 실행의 측정이다. 영상을 정지하거나 프레임을 늘려 만든 결과가 아니다.

### 실제 native PNG (복사본)

아래는 native 캡처의 frame index 0/60/150, 즉 physics step 0/480/1200의 파일이다. 각 PNG는 1280×720 원본 바이트와 SHA가 일치한다.

**정지 v13 — native_upper50_v13_static**

| view | frame 0 / 0초 | frame 60 / 2초 | frame 150 / 5초 |
|---|---|---|---|
| whole_body | [0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_whole_body_frame_00000_step_0000.png) | [2초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_whole_body_frame_00060_step_0480.png) | [5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_whole_body_frame_00150_step_1200.png) |
| hands | [0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_hands_frame_00000_step_0000.png) | [2초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_hands_frame_00060_step_0480.png) | [5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v13_static_hands_frame_00150_step_1200.png) |

**팔꿈치 wave v14 — native_upper50_v14_elbow5**

| view | frame 0 / 0초 | frame 60 / 2초 | frame 150 / 5초 |
|---|---|---|---|
| whole_body | [0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_whole_body_frame_00000_step_0000.png) | [2초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_whole_body_frame_00060_step_0480.png) | [5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_whole_body_frame_00150_step_1200.png) |
| hands | [0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_hands_frame_00000_step_0000.png) | [2초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_hands_frame_00060_step_0480.png) | [5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/native_upper50_v14_elbow5_hands_frame_00150_step_1200.png) |

## 영상과 추적 정보

[전체 native MP4 16개 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/INDEX.md)에서 8개 run의 전신·손 영상을 확인할 수 있다. report가 실제 MP4를 기록한 실행만 복사했다. `native_upper50_static`은 0 physics step의 constructor 오류로 report에 영상이 없어 영상 사본을 만들지 않았다. 실패 실행의 짧은 영상을 5초로 연장하지 않았고, report의 실제 실행시간과 ffprobe 프레임 수/재생시간을 색인에 구분했다.

[입력/producer 전후 SHA, MP4 byte equality와 ffprobe, PNG source/copy SHA](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/provenance_v1.json) · [실행 전 SHA pin](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/preflight_pin_v1.json) · [생성 producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/build_artifacts_v1.py)
