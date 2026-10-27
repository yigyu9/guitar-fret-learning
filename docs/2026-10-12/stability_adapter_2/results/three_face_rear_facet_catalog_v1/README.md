# 엄지 후면 source facet catalog

저장된 CPU source geometry의 rear-facing catalog다. 368개 행 가운데 367개가 rear-facing 조건을 만족하며, 나머지 triangle 786은 이전 native contact에서 관측된 source triangle을 위치 비교에 포함한 행이다. 세 점은 모두 기타 root 좌표 기타 frame `G`의 source centroid이며, 기타의 움직임이나 PhysX cooked 형상을 나타내지 않는다.

![367개 적격점, 후면 patch와 2 mm inset, 선택 triangle 303·1462 및 기준 triangle 323](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/rear_facet_catalog_Gxy.png)

2 mm inset은 XY 투영에서 patch 경계 안쪽으로 표시한 선이다. 가장 가까운 선택점은 triangle 303의 필요 이동 11.677484672 mm와 1462의 11.698917250 mm다. 이전 가장 큰 triangle 323은 17.136177920 mm다. 이는 선형 source fit과 점 위치의 비교이며 물리/FK 성공, 해부학적 후면 패드, 실제 clearance를 뜻하지 않는다.

입력 수치와 봉인 결과는 [catalog.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/catalog.json) 및 [catalog 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/catalog_execution.json)에 있다. 저장 source 산출물의 사전 검토는 [source pre-review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/source_pre_review.md), catalog 검토는 [review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/review.md)다. 그림 producer·PNG와 근접 후보 비교는 [near-rear artifacts phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/README.md)에 기록한다.
