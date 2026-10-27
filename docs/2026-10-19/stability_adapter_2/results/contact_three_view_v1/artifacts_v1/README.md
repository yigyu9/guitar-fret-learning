# 접촉 표식 3-view 재현 자료

이 실행은 기존 16초 물리 trace의 exact 재생이다. 재현 기록상 `trace.json`, `actual_contacts.json`, `initial_values.json`이 이전 실행과 일치하며 모든 입력은 변경되지 않았다. 화면은 전면·오른쪽 옆면·위 순서로 배치했다. 세 view 각각 native 1280×720 이미지 위에 220 px 설명 footer를 붙였고, 합본은 1920×470이다. 동영상은 각 481 frames, 30 fps, 표시 길이 16.0333초다.

## 접촉 표식 읽기

- 원형 표식 색: Chest 청록, 오른쪽 위팔 주황, 오른쪽 허벅지 보라, 왼쪽 허벅지 파랑, 왼손 엄지 빨강, 왼손 나머지 손 노랑, 그 밖의 인체 부위 회색.
- **손 모델의 초록·분홍 표면은 원래 재질색**이다. 접촉 표식은 그 위에 그려진 원형 점뿐이며, 손 표면색은 접촉 표시가 아니다.
- 원형 점이 채워져 있으면 양의 raw lambda, 속이 비면 접촉 행은 있지만 lambda=0이다. 점 크기는 화면상 고정이며 힘의 크기를 나타내지 않는다.
- 점들은 **X-ray처럼 항상 보이도록** 그려져 몸체 뒤에 있는 접촉 특징도 표시한다. 실제 occlusion이나 가림을 묘사하지 않는다.
- 동일 그룹 안의 2 mm voxel dedup은 시각 판독을 돕기 위한 단계다. 원시 행을 삭제하지 않으며 2 mm 접촉 반경, 면적 또는 압력을 뜻하지 않는다.

## 실제 캡처 예

각 PNG와 MP4는 source 산출물의 바이트 보존 복사다. 캡션은 스냅샷 시점의 raw-row/양의 lambda 분류를 요약하며 인과관계를 주장하지 않는다.

| 시점·단계 | native 3-view frame | 관찰 |
|---|---|---|
| 0.5 s · 준비 | [three_views_00015.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00015.png) | Chest, 오른쪽 위팔·허벅지, 왼쪽 검지 접촉 표식이 보임. |
| 3.5 s · A 유지 | [three_views_00105.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00105.png) | 엄지와 검지 양의 접촉 표식; Chest 0, 왼쪽 허벅지 양의 표본 0. |
| 5.333 s · A 해제 전환 | [three_views_00160.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00160.png) | 오른쪽 허벅지 표식은 없음. 왼쪽 허벅지·위팔·엄지·검지·새끼손가락 표식은 남음; 완전 해제 장면으로 해석하지 않음. |
| 6.5 s · A 분리 유지 | [three_views_00195.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00195.png) | 왼팔·손 표식 없음; Chest·오른쪽 위팔·허벅지 표식은 있음. |
| 10.5 s · B 유지 | [three_views_00315.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00315.png) | Chest·오른쪽 위팔·허벅지 및 왼쪽 엄지·검지 접촉 표식. |
| 14.0 s · B 분리 유지 | [three_views_00420.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00420.png) | 왼팔·손 표식 없음; Chest·오른쪽 위팔·허벅지 표식은 보임. |

아래는 네 시점의 전체 화면 이미지다.

![0.5초 준비, 3.5초 A 유지, 5.333초 A 해제 전환, 14초 B 분리 유지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00015.png)

![A 유지 시점 3.5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00105.png)

![A 해제 전환 5.333초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00160.png)

![B 유지 시점 10.5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/three_views_00315.png)

## 원시자료 범위와 한계

여섯 30 fps snapshot을 합친 요약은 7,912 raw feature rows다. 행 수는 독립 접촉 사건 수가 아니다. body-local contact feature를 body 원점과 정규화된 native quaternion으로 world 변환해 쌍을 비교한 최대 잔차는 0.000141880 mm였다. 양의 raw lambda는 보정된 힘(N)이 아니며, contact area나 압력으로 해석하지 않는다. 표식은 30 fps 순간값이며 모든 240 Hz 표본이나 solver substep을 보여주지 않는다. 각 시점의 동시 접촉만 묘사하며 접촉의 원인이나 지지 기여를 입증하지 않는다.

[네 개 전체 annotated native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1/README.md) · [contact 요약 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/contact_summary_v1.json) · [render report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/visual_v1/report.json) · [exact 재현 보고서](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/reproduction.json) · [copy manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1/artifacts_v1/copy_manifest_v1.json)
