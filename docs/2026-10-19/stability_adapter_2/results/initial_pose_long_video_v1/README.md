# 초기 자세 native 재생 길이 확장 — 15초

이 결과는 5초 native 타현 실행을 **같은 초기값·처음 5초 상태 trace·접촉·effort·목표**로 유지해 15초까지 연장한 한 번의 native 실행이다. 처음 5초 prefix 비교가 확인됐으며 달라진 제어 metadata는 이전 5초 끝의 진단 시간 제한뿐이다. 15초 물리는 완료됐고 postprocessing은 물리 상태를 실행하지 않았다.

## 시간 구간과 결과

- **0–2초:** 준비.
- **2–5초:** 기존 EW6 스크립트의 down/up 한 번 왕복.
- **5–15초:** 마지막 local waypoint를 현재 기타에 상대적으로 유지한다. 스트럼 반복이나 고정 프레임 연장이 아니다.
- 15초 native 종료, 451개 camera sample(0–15초 포함), 30fps MP4 재생 15.033333초다. 재생 격자의 마지막 프레임은 추가 물리 시간이 아니다.
- 전체 15초 최대 기타 BB 중심 이동 **5.116316 mm**, SO(3) **2.203204°**; 끝값은 **4.873566 mm / 2.125131°**다.
- 왼팔·손 접촉은 3263/3600표본, 무접촉은 337/3600표본이었다. 오른 손목·손 접촉은 0/3600이다. LH가 계속 완전히 분리된 연주나 손 독립 지지는 확인하지 않았다.
- 13–15초 마지막 2초 동안 BB 최대 변화 0.000486 mm, SO(3) 0.000127°였으나 유한한 능동 인체 제어와 지지가 유지된다. 이를 수동 평형으로 해석하지 않는다.

## 시작과 끝 프레임

초기 이미지는 native 전면 카메라 t=0이다. 끝의 설명 포함 이미지는 X-ray 접촉 표식과 설명 footer가 있는 postprocessed 전면 프레임이다. clean 이미지는 native 전면 프레임이며 설명/footer와 접촉 표식이 없다. 두 영상 종류 모두 기타 6줄 overlay를 포함한다.

![시작 t=0 native 전면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/artifacts_v1/initial_front_t0.png)

![끝 t=15초 설명·X-ray 표식 포함 전면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/artifacts_v1/final_front_t15_with_description.png)

![끝 t=15초 clean 전면 — 6줄 overlay 포함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/artifacts_v1/final_front_t15_clean.png)

## 영상

**설명 포함** 영상은 native 카메라에 깊이 판정된 기타 6줄, 고정 픽셀 반경의 X-ray 접촉 표식, 한국어 footer를 더했다. **clean** 영상은 같은 native 카메라와 6줄 overlay를 쓰며 footer와 접촉 표식은 없다. 그러므로 clean도 6줄 overlay가 있는 영상이지 원래 native pixels를 그대로 인코딩한 영상은 아니다. 표식은 힘(N), 압력, 접촉 면적이 아니다.

### 전면 · 설명 포함

재생시간 15.033333초 · 451프레임 · 30fps

![전면 설명 포함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/with_description/front.mp4)

### 전면 · 설명·접촉표식 없음

재생시간 15.033333초 · 451프레임 · 30fps

![전면 설명·접촉표식 없음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/clean/front.mp4)

### 오른쪽 옆면 · 설명 포함

재생시간 15.033333초 · 451프레임 · 30fps

![오른쪽 옆면 설명 포함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/with_description/right_side.mp4)

### 오른쪽 옆면 · 설명·접촉표식 없음

재생시간 15.033333초 · 451프레임 · 30fps

![오른쪽 옆면 설명·접촉표식 없음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/clean/right_side.mp4)

### 위 · 설명 포함

재생시간 15.033333초 · 451프레임 · 30fps

![위 설명 포함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/with_description/top.mp4)

### 위 · 설명·접촉표식 없음

재생시간 15.033333초 · 451프레임 · 30fps

![위 설명·접촉표식 없음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/clean/top.mp4)

### 전면·옆면·위 합본 · 설명 포함

재생시간 15.033333초 · 451프레임 · 30fps

![전면·옆면·위 합본 설명 포함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/with_description/front_side_top.mp4)

### 전면·옆면·위 합본 · 설명·접촉표식 없음

재생시간 15.033333초 · 451프레임 · 30fps

![전면·옆면·위 합본 설명·접촉표식 없음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/clean/front_side_top.mp4)

## 조건과 범위

기타는 자유 상태, 스트랩 OFF, self-collision ON, root·하체 고정, 상체의 유한한 active human control이다. 기타 고정·손 부착·기타 외력·지속 pose 덮어쓰기는 사용하지 않았다. 이 시험은 checkpoint 연결/학습 없이 EW6 스크립트 한 번을 유지한 검증이다. 왼손 접촉이 남아 있어 독립 지지나 곡 수행 성공을 뜻하지 않는다.

[brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/artifact_brief_v1.json) · [15초 analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/analysis_v1.json) · [처음 5초 prefix 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/prefix_report_v1.json) · [native report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/native_v1/report.json) · [postprocess report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/post_v2/report.json) · [설명 포함 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/post_v2/annotated/report.json) · [변경 파일 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/changed_files_v1.md) · [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/README.md) · [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/artifacts_v1/artifact_manifest_v1.json)
