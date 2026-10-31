# V3 실제 실행 검수

**요약 판정: 문제없음 — 실험 무결성 PASS. 음악 성능 기준은 실패했으므로 마스크 채택은 거부한다.** 미해결 Critical / Warning / Suggestion 없음.

515개 런타임 입력 SHA와 inputs_after를 독립 확인했다. 고유128환경이 각354제어를 완료했고 전체384음 기회 분모를 유지했다. 물리·손목 실패0, close 완료, cleanup 오류0, NN·체크포인트·PPO0이다. 각128에피소드의9보상항이 보존됐고 합과 총보상의 최대 오차는5.33e−6이다. 원 acceptance 함수를 에피소드에서 다시 계산해 저장 결과와 정확히 일치했다.

V2의 저장1416×4 scaled_noise와 env/start_clock가 bit exact이고 전체128잡음 stream SHA도 동일하다. 별도 applied_noise의0열만 모두0이며 나머지3열은 원 scaled_noise와 bit exact다.105축 native PD readback와 training_contract는 V2 noisy 원본과 JSON 동일하다. guard의 다른104축·memory·submit·observation 오차0과 원 rate 허용오차를 확인했다. baseline/candidate 자료는 byte 동일 재사용이며 신규 실행으로 보지 않는다.

실제 결과는 음별 달성45/7/33회, 세음 공동5/128회, clean평균64.105%/70.833%/76.968%, A해제97/128회다. V2 noisy의 공동34/128회보다 나빠졌으며 music/release/stage_ready 모두 false다. 이번 고정기타·seed7·noNN 비교에서는 index1_x 적용잡음 삭제가 개선안이 되지 않았다. 이를 일반적인 잡음의 유익성이나 개별축 인과미분, 학습정책 성과로 확대하지 않는다.
