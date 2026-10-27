# 사전 코드 검수 보완 — AABB 분리 조기 판정

요약 판정: **문제없음.** 추가 Critical 0 / Warning 1 / Suggestion 0. source2의 broad phase는 겹침을 통과시키는 완화가 아니다. 후보 계산은 진행 중이며 native 수락/실행 성공을 승인하지 않는다.

- [source2:28](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v2.py:28)는 같은기타좌표의 convex vertex집합 min/max에서 축간격을 계산한다. 한축의 `Bmin−Amax` 또는 반대방향이 양수이면 모든점이 그축에서 분리되므로 해당간격은 실제 Euclidean 최소거리의 하한이다. axis_gap≥2mm이면 neck잔차의2mm 기준 및 finger-pair의.5mm 기준을 모두 충족해 penalty0을 안전하게 반환한다. 2mm미만은 기존 face-plane 계산을 유지한다.
- V1 대비 source diff는 이 조기 판정·PLAN2/search2 경로·station progress출력뿐이다. 목표면/5·8mm gap·모델bounds·left33/frozen48·실제float32 FK·genuine poses 및 최종 [source2:104](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v2.py:104)의 전체source audit가 유지된다. runtime controller/helper/수정runner는 바뀌지 않았다.
- [중단 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/source_v1_interrupted.json:1)은 source1 SHA·로그·입력맵을 보존하고 후보 출력 전 CPU SIGINT/native0을 명시한다. 원source1 SHA가 기록과 일치한다. source 중단을 native 실패 또는 정상 후보 완료로 집계하지 않는다.

Warning 1 — 축간격은 convex **source** vertex집합의 거리 하한이며 PhysX cooked 형상/실제손 pad·연속시간 contact 인증이 아니다. 원[사전 코드 검수1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v1.md:1)의 면proxy·실제달성gap·후보/native 구분과 준비/연주 미인증 한계도 유지한다. source2 최종수락과 후보별 모델·genuine FK·입력SHA는 결과가 완성된 뒤 별도로 확인해야 한다.

추가 source 실행/native/정책추론/학습·원본 수정0. 읽기전용 diff와 수학적 분리 조건에 한정한 검수이며 소유한 새 리뷰만 작성했다.

검수 SHA256:

- 보존source1: `ed88558733fec8421a9d3fb91d569c18e22d29e4243dc69137f838af715345ef`
- 새source2: `9480c44815a39df4a2eec6dff7493125c0555dee382cc1ad089e8b5b18e70cbd`
- 새계획V2: `29da6d9112b66e4c3674fb539be26427f843a3c5c72cc24b6179c73bcca8f0a0`
- 동일runner: `20706636076b71bd44cb6a792e9e8e268695f5380ff698565a31b4ded2a63a7d`
