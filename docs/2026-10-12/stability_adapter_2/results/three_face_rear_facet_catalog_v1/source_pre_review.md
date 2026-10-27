# 후면 엄지 source catalog 사전 검수

**요약 판정: 문제없음.** Critical / Warning / Suggestion 없음.

검수 범위는 아직 소비되지 않은 `catalog_rear_thumb_facets.py`와 `THREE_FACE_REAR_FACET_CATALOG_PLAN.md`, `THREE_FACE_REAR_FACET_CATALOG_EXECUTION.md`다. 기존 rear_facet_v2의 네 rejection·native0·검수/보존 감사 완료 사실은 parent 전달에 따라 신뢰했으며 재실행하거나 광범위하게 재감사하지 않았다. 이번 검수에서 Isaac Gym scene, physics, catalog main을 실행하지 않았다.

## 코드와 입력 대조

- [catalog_rear_thumb_facets.py:30](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:30): 이전 입력의 예상 SHA를 승계하고 새 producer·계획·직접 입력을 추가한다. 실제 사용되는 config, saved initial_values/shape_properties, fixed-lower asset, left_fk, build_probe, face_geometry, geometry, pose, environment의 10개 경로가 승계 목록에 포함되고 SHA가 일치함을 읽기 전용으로 확인했다. 종료 전 같은 입력 목록을 다시 검사한다.
- [catalog_rear_thumb_facets.py:50](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:50): saved actual81이 이전 q81과 exact 일치한다. 17좌표 이름은 중복 없이 동일 순서이며 두 `.20` rejection의 실제 lower/upper가 exact 일치한다. 이전 saved81T는 saved initial의 preserved_absolute_targets81과 exact 일치하고 LA는 `1.1018469719600776 m`다. 기타 pose는 같은 saved state를 사용하며 자산 생성 함수나 PD/physics 실행 경로를 호출하지 않는다.
- [catalog_rear_thumb_facets.py:73](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:73): 활성 source hull의 모든 triangle centroid/normal을 고정 초기 G 좌표계로 변환하고 normalZ > .75인 면을 기록한다. 이전 metadata의 367개 조건과 largest triangle323의 local centroid를 검사하며, 관측 기준 triangle786을 qualification과 무관하게 행에 포함한다. 면적 변환은 m²→mm²의 `1e6`이다.
- [catalog_rear_thumb_facets.py:87](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:87): rear quad의 각 edge에 수직 2mm inset을 적용해 인접 직선 교점으로 polygon을 만든다. 같은 rear Z=-8mm의 유한 polygon 최근점에서 -GZ 방향으로 0.7mm offset한다.
- [catalog_rear_thumb_facets.py:107](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:107): 각 좌표 ±0.0001rad의 34개 body FK 평가로 모든 local centroid의 3×17 central derivative를 얻는다. translation은 차분하고 고정 G의 회전 역변환만 적용하므로 point Jacobian의 좌표계와 단위가 맞다. 실제 box를 q0 기준 delta로 옮겨 LSQ와 축별 독립 extrema를 계산하고 m→mm의 `1000`을 적용한다.
- [catalog_rear_thumb_facets.py:136](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:136): qualification 행을 diagnostic goal까지 초기 필요 변위 norm과 triangle ID 순으로 정렬하며 centroid 간격 2mm 이상인 최대 두 anchor를 선택한다. 결과 scope는 선형/정적 source 진단의 한계를 명시한다.
- [catalog_rear_thumb_facets.py:27](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:27): 기존 attempt/catalog이 있으면 쓰기를 중단한다. 기존 source/leaf/output을 수정하거나 native state를 제출하는 경로가 없다. 이 검수는 새 `source_pre_review.md`만 생성했다.

## 검증

- 내장 `compile()` 문법 검증 통과. 실행 모듈은 import하지 않았다.
- rl38의 numpy/scipy/trimesh만 사용한 합성 검증 통과: 실제 저장 rear quad의 모든 inset vertex가 모든 원 edge에서 2mm 이상이고 인접 두 edge에서는 exact 2mm; polygon 내부·바깥·corner의 최근점 및 rear offset 방향; 3좌표 box의 모든 corner 열거와 axis min/max 일치; bounded LSQ 성공 및 bounds 준수; 합성 회전점의 central derivative와 해석적 cross-product derivative 일치 및 고정 G 변환.
- 기본 `python`에는 trimesh가 없어 최초 합성 검증이 import 단계에서 중단되었다. rl38로 같은 검증을 완료했다. catalog 실행 결과, nonlinear FK 달성, source overlap, cooked/native contact, 물리 유지 또는 안정성은 이번 사전 검수 대상이 아니다.

검수한 파일 SHA256:

| 파일 | SHA256 |
|---|---|
| catalog_rear_thumb_facets.py | afd59f108291d61171d519674c0d06e386a760e672388e0840327d94f7713bc5 |
| THREE_FACE_REAR_FACET_CATALOG_PLAN.md | 3f12f011cbb1cdaccf9074a028c327aa633c542995472f81a796e1e182e68f29 |
| THREE_FACE_REAR_FACET_CATALOG_EXECUTION.md | 263c68f9f3a4a89f8c25b1180cdc479742cebe5e7422a0b9a750990b1b7c161e |
