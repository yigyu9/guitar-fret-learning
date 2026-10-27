# 세 면 지지: 엄지 후면 facet V1 중단 기록

작성일: 2026-10-08. 이 phase는 첫 source 후보의 partial 결과를 기록한 뒤 두 번째 거리 QP의 수치 중단으로 종료됐다(exit 1). 완료된 네 후보 batch로 해석하지 않는다.

첫 후보는 partial 기록에 남아 있고 V2 복구 실행에서 반복됐다. 첫 후보의 q, source anchor와 source intersection 목록은 V1 partial 결과와 V2 proposal에서 exact 일치한다. V1 원 source, 실행 wrapper, log, partial selection과 preservation 기록은 보존되어 있다. 복구 전 source 검수 및 이전 후처리 독립 검수 기록은 아래 파일을 참조한다.

- 부분 후보: [partial_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/partial_selection.json)
- 실행 결과: [search_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/search_execution.json)
- 원 log: [search.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/search.log)
- 복구 전 source 검수: [source_pre_review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/source_failure_v1_snapshot/source_pre_review.md)
- 이전 후처리 검수: [previous_postprocessing_review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/source_failure_v1_snapshot/previous_postprocessing_review.md)
- 후속 완료 후보 요약: [V2 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md)

V1 자체의 새로운 그림이나 native 실행은 추가하지 않았다.
