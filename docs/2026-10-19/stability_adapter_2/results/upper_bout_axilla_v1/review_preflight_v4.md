# 전경 추가 source 사전 검수

판정: **문제없음 — 거절 결과 유지, 실행 가능한 native 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. 신규 물리 실행 없이 변경 코드와 저장 source/지역 접촉 자료를 읽고 수치를 대조했다.

[수락 gate:38](/home/ajou/yigyu/3/stability_adapter_2/search_upper_bout_axilla_v4.py:38)와 [source 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/search_v4/search.json)를 대조했다. 근위 간격 7.635703mm는 6mm 미만 조건, 전완 기존 인간 motor점 오차 8.448274mm는 3mm 미만 조건, Gz −0.088246736m는 [−0.085, −0.025]m 조건에 각각 미달한다. source_clear=true만으로 수락하지 않았으며 selected=[]/native_runs=0이 맞다. 입력 606개 현재 SHA 불일치 0을 확인했다. 몸통·머리·오른팔만 변경하고 기타 p/q와 나머지 scalar를 유지하는 mask, 모델 범위, 실제 source audit를 적용한다. runner4는 이전 runner3에서 계획·검색 경로만 달라진다.

Warning 1 — [지역 판정:22](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analyze_contact_region_v1.py:22): 이 판정은 캡슐 근위 0~35%와 Gx/Gy 범위이며 새 mid-depth Gz 조건을 포함하지 않는다. 해당 범위로만 보고한다. 세 조건 raw endpoint를 독립 재계산하여 지정 지역 접촉·양의 raw lambda 표본 모두 0/1200, feature pair 최대 약 1.11e−7m 및 캡슐 반지름 차이 최대 0.219321mm를 재현했다. localPos+offset의 origin 좌표 변환은 이 자료와 정합하지만 해부학적 겨드랑이·힘 기여·연속시간 접촉 인증은 아니다.

검수 SHA256: source4 `5affddf8c9690d1e32ac18e1ff7b348a3897f3a74497807ffbb5a5b5aecc2b97`; runner4 `6f23823b3a9badb78d130f5382fe70770a3f6c8aeb711b068be810c6cc6febe1`; search4 JSON `536358deb03d39d0a959912d4157cc44078cd76ee1ca9eaaf1b1bcd268f2aa26`.
