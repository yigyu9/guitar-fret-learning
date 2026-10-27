# 기타 형상과 표시 범위 · v2

이 v2는 기존 형상 설명을 유지하고, 요청된 과거 기타 중심 native 이미지를 추가하며 현재 후보와 구분합니다. v1 문서는 보존했습니다.


## 형상

현재 회색 OM 바디는 Grellier 도면 자료를 바탕으로 만든 외부 형상 근사입니다. 바디 길이는 491.957 mm, 최대 폭은 380.632 mm이며, 국소 두께는 넥 쪽 약 85 mm에서 최대 약 107.198 mm까지 달라집니다. 꼬리 쪽 표본은 약 104 mm입니다. 최대 중심선 깊이와 전체 mesh의 z bounding-box 폭 108.476 mm는 서로 다른 값입니다. 앞·뒤 곡선의 입력 반지름은 각각 7.620 m, 4.572 m이고 바디 collision은 63개 convex 조각으로 표현됩니다. 이는 source 형상 자료이며 PhysX cooked 접촉 여유를 인증하지 않습니다.

![원본 도면 기반 바디 mesh의 정면·측면·사선 source view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/source_mesh_three_views.png)

![바디 길이축을 따른 국소 깊이 표본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/local_depth_samples.png)

기존 넥, 프렛 및 fret/strike 물리 영역은 유지됐습니다. 여섯 개 밝은 회색 현은 카메라 이미지에 투영하는 2 px 표시선으로, native 깊이 기반 가림을 사용합니다. 실물 현의 두께·진동이나 별도 충돌 형상을 추가하지 않습니다. source/collision 형상과 영상 표시 설명은 [기존 6현 표시 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/README.md:1) 및 [기타 형상 원자료 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/README.md:1)에서 확인할 수 있습니다.

## 과거 기타 초점 화면 참고

아래는 실제 Isaac Gym의 기타 중심 카메라에서 얻은 이미지이며 물리 없는 6현 표시를 포함합니다. 이 이미지는 `guitar_focused_view_v1`의 과거 다른 초기 자세 모델 보기입니다. 현재 native 11/12 후보의 초기 화면이 아니며 현재 자세의 근거로 사용하지 않습니다.

![과거 다른 초기 자세의 기타 중심 Isaac Gym 화면; 현재 후보 장면이 아님](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/guitar_focus_reference.png)

- [원본 설명 복사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/focus_source_README.md)
- [원래 source 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/native_v1/media/initial_strings.png)

## 질량과 출처 범위

모델의 총 질량 약 4.648716 kg은 앞선 모델 질량값을 유지한 것입니다. 외형 mesh는 중공 구조나 목재 내부·밀도·음향을 모델링하지 않으므로 실제 기타 질량·재료·공명을 나타내지 않습니다. 제품 사진과 정확히 일치하는 재현이라고 볼 수 없습니다. 출처 고지와 기존 라이선스 표기는 [복사한 attribution 노트](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/ATTRIBUTION_source.md) 및 [원본 v3 attribution](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/ATTRIBUTION.md:1)을 따릅니다. 새 법률 해석은 추가하지 않았습니다.

## 복사 자료

- [원본 형상 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/geometry_v3_manifest.json)
- [깊이 표본 JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/depth_v1.json)
- [복사본 해시·입력 해시 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/provenance_v1.json)
