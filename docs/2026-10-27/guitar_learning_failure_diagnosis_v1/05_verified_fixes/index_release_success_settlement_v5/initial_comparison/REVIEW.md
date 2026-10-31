# 초기 V4/V5 비교 독립 검수

**요약 판정: 문제없음 — PASS.** 미해결 Critical / Warning / Suggestion 없음.

실제 rl38 CPU에서 compare.compare 두 모드를 독립 재실행했다. deterministic은 fit_deterministic, stochastic은 acceptance의 true를 확인한 fit_stochastic_actual을 사용한다. 두 모드 모두 원128명 전체 음악 원장이 V4와 exact이며, env0 첫 시도의 q/target/body/candidate/정규화·decoded NN 목표 배열도 exact이다.9보상 중 차이는 song_left_success뿐이며 원래 A 달성 .25를 회수하고 달성+해제를 만족한 경우에만 돌려준 금액과 총보상 차이가 일치한다. A 실수령은 고정22회(합5.5), 확률20회(합5.0)이며 실패 억제액은0이다.

힘 배열은 bitwise 동일하지 않다. 최대차 고정7.62939453125e-6N·확률3.814697265625e-6N을 별도로 기록한다. 전체128명의 물리 trace exact나 학습 개선을 주장하지 않는다. 실수로 --stochastic을 누락한 runs/fit_stochastic은 보존된 추가 고정 평가이며 확률 비교에서 제외한다.
