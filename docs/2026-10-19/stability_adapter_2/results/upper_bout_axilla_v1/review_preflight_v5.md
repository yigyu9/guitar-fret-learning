# 제한된 초기 기타 이동 source 사전 검수

판정: **문제없음 — 거절 결과 유지, 실행 가능한 native 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. 변경 코드·저장 source만 검토했으며 native/학습을 실행하지 않았다.

[최적화:35](/home/ajou/yigyu/3/stability_adapter_2/search_upper_bout_axilla_v5.py:35)는 기타 초기 world Y [−20,0]mm/Z [0,12]mm만 변수로 추가하고 X·회전은 유지한다. 기존 전완 인간 material점의 목표와 손 위치 목표에 동일 초기 기타 이동을 더하며, 양 Hip 음수 간격 barrier를 추가한다. [수락 gate:38](/home/ajou/yigyu/3/stability_adapter_2/search_upper_bout_axilla_v5.py:38)의 전체 캡슐 최소 0.05mm·source_clear·모델/고정 scalar 및 기존 지역 조건은 완화하지 않았다.

[저장 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/search_v5/search.json)의 전체 상완 간격 −0.022549mm, 근위 간격 8.902034mm, 전완 기준점 오차 6.796760mm는 각각 gate를 통과하지 못한다. 기타 이동은 수치상 거의 0이며 selected=[]/native_runs=0이 정확하다. 입력 608개 SHA 불일치 0 확인. runner5는 runner4 대비 계획·검색 경로만 달라져 제어/guard 변경이 없다.

Warning 1 — [결과 scope:39](/home/ajou/yigyu/3/stability_adapter_2/search_upper_bout_axilla_v5.py:39): `source_clear=true`는 별도 analytic 캡슐의 음수 간격과 동일한 판정이 아니다. 두 검사 중 하나라도 실패하면 현재처럼 거절해야 한다. 전완 목표는 초기 기타 이동에 맞춰 이동한 기준이며 이전 world 목표의 정확한 유지라고 표현하지 않는다. 음수 source 간격은 cooked penetration 측정이 아니다.

검수 SHA256: source5 `10e2e5e61c08294846a835e1d90382b468e0c528aa611f12b04a94bd526dc0be`; runner5 `3a930d53ee4b95e67bf07b60517a0c8cc6183723daa975d8e80fe6b36665b771`; search5 JSON `c77f86b2c9010528b90bbc9cedecac5f257e505b81f2f955ff5733f390d548b6`.
