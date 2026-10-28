# 최초 하중부터 증분 억제 — 실제 단일 timing 비교

matched 전제: **충족**. 원본/2초 지연 조건은 검수된 기존 결과를 재사용하고 첫 접촉 조건만 새로 감사했다.

| 조건 | 달성/128 | clean / wrong 평균 | 물리 / 손목 실패 |
|---|---:|---:|---:|
|original|127|0.992644 / 0.006940|0 / 0|
|no_new_inward|128|1.000000 / 0.000000|0 / 0|
|first_contact|122|0.948085 / 0.041468|0 / 0|

| 조건/구간 | 중지 resultant p50/p95/max N | 엄지 resultant p50/p95/max N |
|---|---:|---:|
|original/audible|89.6102 / 94.9791 / 100.5516|84.1126 / 92.0809 / 102.2836|
|original/after|95.3485 / 103.3956 / 122.6204|88.5225 / 98.1996 / 108.9203|
|no_new_inward/audible|30.2280 / 34.2799 / 39.0267|29.5781 / 34.3685 / 37.1047|
|no_new_inward/after|35.8826 / 41.2740 / 45.0140|32.5723 / 42.2986 / 48.6484|
|first_contact/audible|13.1435 / 16.2053 / 99.2866|14.6786 / 30.4308 / 140.1906|
|first_contact/after|14.4057 / 21.5329 / 78.7177|18.8678 / 31.4204 / 108.2849|

| 신규조건 event | 노출환경/128 | 시각 min/p50/max s | 직전 resultant p50 N | 직전 q-target 오차 norm p50 deg |
|---|---:|---:|---:|---:|
|first_gate|128|1.73333 / 1.75000 / 1.76667|12.878107805427177|10.447520007982751|
|first_change|128|1.73333 / 1.75000 / 1.76667|12.878107805427177|10.447520007982751|

성과/유지/wrong/실패는 모든128 첫 시도 분모다. 힘은240Hz 실패 endpoint부터 제외하며60Hz 개입 통계는 실패로 끝난 control 전체를 제외한다. 환경별 첫실제변경 직전 physics/control prefix와 전체 명령 tape를검사했다. 고정480 gate/mask는 신규조건에 적용하지 않았다.

first_events.csv는 없는 event도null로128환경씩 보존하고, 직전 실제 force·old target/actual4·Jn 오차를 담는다. control_by_phase.csv와 summary.json에는 실제 gate 노출, target/rate/box·부호·접선변경·J 속도잔차·original 대비 teacher 요청차가 있다. reward_payments.csv는 원9지급이며새조건 increment/cumulative/episode/음 원장과대조했다.

body resultant는 접촉쌍 압력이 아니다. 고정material point는 최초any-candidate witness와다를수있다. 큰Jn·관절오차는침투mm가아니다. gate외저장0은0오차로평균하지않았다. 동일tape라도teacher feedback·자세·접선운동이달라질수있으므로 단독인과·자유손production개선·정책학습성과·새힘상한해결로확대하지않는다. 실제값검산과해석은후속독립검수를따른다.
