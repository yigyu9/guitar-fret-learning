# 후면 엄지 source catalog 완료 검수

**요약 판정: 문제없음.** Critical / Warning / Suggestion 없음.

검수 범위: 소비된 `catalog_rear_thumb_facets.py`, `catalog_source.py`, `catalog.json`, `attempt.json`, `catalog_execution.json`, 보존 wrapper, 로그 및 실제 `source_pre_review.md`. 이번 검수는 읽기 및 저장 배열 계산만 수행했다. Native scene/physics/catalog main을 재실행하지 않았다.

- [catalog_rear_thumb_facets.py:80](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:80): normalGZ>.75 qualification 367행과 비교 기준786 한 행을 합쳐 368행이다. 최대면적 기준323 및 관측 기준786을 모두 보존했다. 모든 행의 qualification을 저장 normal로 재계산해 일치함을 확인했다.
- [catalog_rear_thumb_facets.py:136](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:136): 저장 행을 필요 이동 norm 순으로 다시 정렬하고 2mm centroid 간격 필터를 적용한 결과 selected303/1462와 exact 일치했다. 두 centroid 간격은 `2.163378933397435 mm`; 필요 이동은 각각 `11.677484672212893 / 11.69891724972613 mm`다.
- [catalog_rear_thumb_facets.py:87](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:87): 저장 원 quad와 inset의 모든 edge–vertex 수직 거리를 재계산했다. 모든 edge에서 2mm 이상, 해당 인접 edge에서 2mm이며 rear plane -8mm와 diagnostic 바깥 offset 0.7mm가 유지된다.
- [catalog_rear_thumb_facets.py:107](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:107): 17좌표마다 ±0.0001rad 두 body FK 평가를 사용하므로 derivative loop는 34 source FK 평가다. 모든 368행의 3×17 Jacobian 크기, 선형 해의 bounds, 저장 residual 및 축별 독립 min/max를 저장 배열에서 재계산해 일치함을 확인했다. 실제 호출 수 계측을 새로 수행하지 않았다.
- [catalog_rear_thumb_facets.py:159](/home/ajou/yigyu/3/stability_adapter_2/catalog_rear_thumb_facets.py:159): 선형 residual은 nonlinear FK·겹침·actual 접촉·물리 지지·제어/안정성 인증이 아님을 명시한다. 약 0인 선형 잔차를 물리 성공으로 설명하지 않는다.
- [catalog_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/catalog_execution.json): exit0, native_calls0 및 catalog native_initializations/physics_steps0이 일치한다. 실행 전후 producer/계획/실제 사전검수 SHA가 동일하고 현재 파일과 일치한다. source 복사본과 소비 producer의 SHA, 실행 로그 SHA, attempt/catalog 입력 목록의 exact 일치 및 목록11361개의 현재 SHA 일치를 확인했다.

소비 producer SHA256: `afd59f108291d61171d519674c0d06e386a760e672388e0840327d94f7713bc5`. 기존 소비 source·입력·출력을 변경하지 않았으며 이번 검수는 이 `review.md`만 생성했다.
