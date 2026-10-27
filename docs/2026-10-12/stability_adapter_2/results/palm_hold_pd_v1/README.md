# palm_hold_pd_v1 기록 안내

이전 v1의 세 실행(3 init/72 physics steps)과 원자료는 당시 상태 그대로 보존한다. v1 runner에서 setter의 boolean 반환값 확인이 누락되었으므로 그 결과는 수정하지 않고 이력으로 남겼다. 같은 조건의 원자료 5개 배열이 v2와 정확히 일치하는지 재검증했고, setter 반환값 검사를 보완한 별도 실행과 분석은 [palm_hold_pd_v2 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/README.md)를 참조한다. 이 문서는 v1 보존 상태를 설명하며 v1 결과를 새 검증으로 소급 변경하지 않는다.
