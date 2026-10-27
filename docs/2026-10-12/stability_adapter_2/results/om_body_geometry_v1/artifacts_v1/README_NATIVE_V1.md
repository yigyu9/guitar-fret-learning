# OM 바디 형상: source 자료와 native 화면

이 자료는 OM 바디의 실제 OBJ source 뷰와 완료된 두 native 평가를 분리해 기록한다. source 3D 뷰는 Isaac Gym 화면이 아니며, native 캡처는 완료된 실행의 카메라 프레임이다. 이 turn에서 물리 실행은 하지 않았다.

## Source 형상

[OBJ source 세 방향 보기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/source_mesh_three_views.png)와 [기록된 로컬 깊이 샘플](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/local_depth_samples.png)은 source geometry 설명이다. 바디 시각 mesh는 `body_visual.obj`를 읽어 그렸으며 Isaac Gym 렌더가 아니다. 평면 림은 약 49.1957 × 38.0632 cm이고, source 샘플의 최대 중심선 깊이는 107.19786 mm다. side 길이 491 mm와 plan 길이 491.957431 mm는 서로 다른 축 기준이다. 이 깊이 값은 bbox z=108.476 mm와 구분한다.

Build 자료는 63개 convex 조각과 표본 XY 경계 오차 0.5 mm 이하를 기록한다. 이는 source 표본 비교이며 PhysX cooked shape의 3D 오차나 실제 접촉 여유를 보증하지 않는다. 내부 공동, 목재 물성, 음향 모델은 만들지 않았다.

## Native 캡처와 평가

native_v2에서 넥을 포함한 시각 표시가 확인되어 아래 v2 영상을 최종 화면 자료로 사용한다. native_v1 영상에는 넥 시각화가 빠져 있다. 이 차이는 화면 표시 누락이며 native_v1 물리 실패라는 뜻은 아니다. v2는 visual-only 넥 표시를 추가했고 물리 모델은 동일했다.

![native_v2 전신, 0·2·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/native_v2_whole_body_0_2_5s.png)

![native_v2 손과 기타, 0·2·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/native_v2_hands_0_2_5s.png)

![native_v2 초기 외관 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/native_v2_initial_appearance_captioned.png)

두 실행은 각각 5초, physics 1,200 step, control 300회다. 초기→5초 actor-root 이동은 113.199839 mm, 회전은 4.857745°였고, 2→5초 endpoint 변화는 0.000490 mm와 0.0000473°였다. 별도 settled-window 기록은 2~5초 181개 표본에서 2초 대비 최대 0.000887495 mm, 0.000157702° 변화를 보였다. 따라서 처음 이동 후 거의 정지한 관측이며 초기 pose 유지나 연주 성공을 뜻하지 않는다. 오른팔 초기 관절 변경 최대는 0.07442474 rad, 기타 질량은 4.6487157 kg, strap rest length는 1.10184697 m로 기록됐다. [검증 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/verification_v1.json)와 [settled-window 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/settled_window_v1.json)를 참조한다.

보고서상 music actor 0, policy call 0, checkpoint load 0, forbidden call 0이며 strap force API 호출은 15,600회다. 이는 이 평가 범위의 실행 요약으로 학습·연주·음악 성공 또는 일반적인 안정성 판정이 아니다. native_v2 영상은 [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_body_geometry_v1/native_v2_whole_body.mp4), [손 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_body_geometry_v1/native_v2_hands.mp4)에서 볼 수 있다.

네 개 원본 영상은 재인코딩 없이 exact copy로 보관했다. [영상 목록 및 SHA-256 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/om_body_geometry_v1/manifest_v1.json)를 참조한다. 파일별 frame rate·크기는 manifest의 ffprobe 정보에 기록했다.

## 출처와 범위

[Source 단계 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/README_SOURCE_V1.md)과 [재현/해시 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/native_media_provenance_v1.json)을 함께 둔다. 파생 바디 mesh의 라이선스 범위는 [연구 노트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/LICENSE_RESEARCH_NOTES_V1.md)에 따른다. 해당 범위를 기존 넥·프렛·현 또는 전체 프로젝트로 확대 해석하지 않는다.
