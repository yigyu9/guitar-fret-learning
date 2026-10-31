# V4 capture 실제 결과 검수

**요약 판정: 문제없음 — PASS.** 미해결 Critical / Warning / Suggestion 없음. 검수 중 추가 native·NN 실행은 없다.

504개 런타임 핀과 inputs_after가 현재 SHA와 일치한다.128회 완료·scene close·실패/cleanup/변경/미봉인소스0·NN/체크포인트/PPO/fit0을 확인했다.1416행은 env0..3 순서로354제어를 정확히 교차하며 clock0..1412(간격4),time=clock/240인 제어 전 자료다. state[557],events[64,24],priority[8,24]와4목표·105이전target은float32,mask는bool이고 전부유한하다.

원 V2 env0 trace와 raw/decoded라벨이 exact이고 네환경의 라벨도 동일하다. 두번째 제어부터 old_target105는 직전 원 trace target과 exact다. 원 q/target/body/candidate 및 force를 제외한 모든 trace 필드,128개 전체 원장·acceptance·현재 training_contract·native PD readback이 정확히 일치한다.

증거 범위를 구분한다. net_body_force_n만112572성분 중46개에 최대3.814697e−6N 차이가 있다. 이필드는 사전선언4개 exact 필드에 포함되지 않으며 원장·판정은 exact다. 따라서 전체 trace byte동일이라고 확대하지 않는다. 과거 V2의 제어 전557관측 자체는 저장되지 않았으므로 관측전체의 과거 byte직접대조를 주장하지 않는다. 검수는 원 native상태·시점·라벨·전체원장·계약의 동일성을 증명하며 학습정책 성과를 의미하지 않는다.
