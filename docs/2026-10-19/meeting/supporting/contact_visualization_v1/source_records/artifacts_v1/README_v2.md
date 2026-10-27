# 접촉 표식 3-view 재현 자료

이는 원래 물리 실행의 trace playback이 아니라 동일 제어로 수행한 물리 재실행이다. 저장된 60 Hz state trace와 240 Hz contact log는 원 실행과 정확히 같다. 재현 기록에서 `trace.json`, `actual_contacts.json`, `initial_values.json`의 exact 일치와 모든 입력 불변을 확인했다.

동영상은 각 481프레임, 30 fps, 표시 길이 16.0333초다. 화면은 전면·오른쪽 옆면·위 순서로 배치했다. 각 view는 native 1280×720 영상 위 220 px 설명 footer가 있어 1280×940이고, 세 view 합본은 1920×470이다.

## 접촉 표식 읽기

- 원형 표식 색: Chest 청록, 오른쪽 위팔 주황, 오른쪽 허벅지 보라, 왼쪽 허벅지 파랑, 왼손 엄지 빨강, 왼손 나머지 손 노랑, 그 밖의 인체 부위 회색.
- 손 모델의 초록·분홍 표면은 원래 재질색이다. 접촉 정보는 표면색이 아니라 원형 점으로만 표시한다.
- 채워진 원은 양의 raw lambda, 속이 빈 원은 접촉 행이 있지만 lambda=0이다. 점 크기는 화면에서 고정되어 힘의 크기를 나타내지 않는다.
- 표식은 X-ray처럼 항상 보이도록 렌더링해 몸체 뒤의 특징도 보인다. 실제 가림을 재현하지 않는다.
- 같은 그룹의 2 mm voxel dedup은 화면 판독용이다. 원시 행을 줄이는 물리 필터가 아니며, 2 mm 접촉 반경·접촉 면적·압력을 뜻하지 않는다.

## 스냅샷별 접촉 관찰

아래 원형 표식의 카운트는 시점별 raw feature 행과 그중 양의 lambda 행이다. 이 값은 접촉 사건 횟수가 아니다.

| 시간·단계 | 스냅샷 | 관찰 |
|---|---|---|
| 0.5 s · 준비 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00015.png) | Chest 2/3, 오른쪽 위팔 2/2, 오른쪽 허벅지 5/11, 왼쪽 검지 1/1 양의 행 |
| 3.5 s · A 유지 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00105.png) | 왼쪽 엄지·검지 양의 표식; Chest 행 0, L_Hip raw 2행 중 양의 행 0 |
| 5.333 s · A 해제 전환 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00160.png) | 오른쪽 허벅지 표식은 없음; 왼쪽 허벅지·위팔·엄지·검지·새끼손가락 표식은 남음. 완전 해제로 볼 수 없음 |
| 14.0 s · B 분리 유지 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00420.png) | 왼팔·손 표식 없음; Chest·오른쪽 위팔·허벅지 표식은 있음 |

### 실제 프레임

![0.5초 준비 시점의 세 시야](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00015.png)

![3.5초 A 유지 시점의 세 시야](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00105.png)

![5.333초 A 해제 전환 시점의 세 시야](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00160.png)

![14초 B 분리 유지 시점의 세 시야](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00420.png)

## 원자료 범위와 해석 한계

7,912 raw feature rows는 여섯 스냅샷만의 합이 아니라 전체 481개 30 fps 프레임 관찰에 걸친 행 수다. 이는 독립 접촉 사건 수가 아니다. Body-local 접촉 특징을 body 원점과 정규화한 native quaternion으로 world 변환해 쌍을 비교한 최대 잔차는 0.000141880 mm다. raw lambda는 보정된 힘(N)이 아니며, 행 수와 표식으로 접촉 면적·압력·지지의 인과 기여를 입증하지 않는다. 30 fps 표식은 순간 관찰로 240 Hz 접촉 로그의 모든 표본이나 solver substep을 보여주지 않는다.

## 전체 annotated native 영상

[전면 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/front.mp4) · [오른쪽 옆면 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/right_side.mp4) · [위 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/top.mp4) · [세 시야 합본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/front_side_top.mp4)

[영상 index V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/README_v2.md) · [원시 contact 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/contact_summary_v1.json) · [render report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/visual_v1/report.json) · [exact replay report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/reproduction.json) · [copy manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/copy_manifest_v1.json)
