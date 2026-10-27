# 오른쪽 10 mm 후보 — initial archive

이 archive는 기존 current neck-support initial archive와 별도로 저장된 오른쪽 10 mm native 후보입니다. 기존 baseline을 대체하거나 갱신하지 않습니다. candidate JSON의 경로와 config의 asset/model 절대참조는 원본 그대로 보존했습니다. 따라서 이는 설정·초기상태·native 증거를 보관하는 기록물이며 모든 공용 Isaac Gym 모델/mesh를 포함한 독립 실행 bundle은 아닙니다.

## 포함한 설정과 증거

원본 `initial_values.json`에는 81개 joint 각도 및 전체 native body initial state가 있고, PD 속성 배열은 `initial_values.json`의 `PD_properties`에 있습니다. `native_properties.json`은 기타 imported/requested/applied 질량·COM·관성 기록을 담습니다. 원본 config_v1의 config/candidate/inputs/report, native report/initial verification/initial three-face measurements, comparison·face·strike·command audit, V2의 10/20 mm source search audit를 바이트 그대로 복사했습니다. native capture/videos metadata와 세 native 초기 프레임 및 세 개의 완전 5초 영상도 함께 둡니다.

## Native 초기 프레임

### 전신

![오른쪽 10 mm native 초기 전신](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/frames/whole_body/00000.png)

### 손

![오른쪽 10 mm native 초기 손](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/frames/hands/00000.png)

### 엄지 뒤

![오른쪽 10 mm native 초기 엄지 뒤](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/frames/thumb_back/00000.png)

## Native 5초 영상

### 전신

![오른쪽 10 mm native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/whole_body.mp4)

### 손

![오른쪽 10 mm native 손 영상](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/hands.mp4)

### 엄지 뒤

![오른쪽 10 mm native 엄지 뒤 영상](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/archive_v2/native_right10_v1/media/thumb_back.mp4)

측정과 비교 해석은 [결과 README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README_v4.md:1)를 참조하세요.
영상 색인은 [성공 native MP4 납품 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v4.md:1)을 참조하세요.
보존 파일별 색인은 [/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/FILES_v2.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/FILES_v2.md:1), copy SHA와 ffprobe는 [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/provenance_v2.json:1)입니다.
기존 current baseline은 [/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README_v3.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README_v3.md:1)에 별도로 보존되어 있습니다.
