# 닫힌 시간창 R9 증분 목표 실행 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / 미해소 Suggestion 없음. 저장 코드·원자료·영상·문서만 검수했으며 native 초기화·물리 실행은 하지 않았다. 사전 변경 범위는 동결된 `pre_review.md`에 기록했다.

- 실제 1200 physics steps/300 controls/151 camera frames, native21계약을 확인했다. trace152개에는 terminal step716 추가표본이 포함된다. PREPARE/PLAY/HOLD `49/130/121`, source 종료2.983333초 이후 HOLD 물리/녹화를 음악 완료와 구분한다.
- closed phase1의22개 명령에서 geometry3 READY 및 대기 gain2를 확인했다. 실제 raw 요청 R9 목표가 `clip(previous_actuator_goal+2*bounded_IK_correction, native bounds)`와 float32 정밀도에서 일치하고, I는 매번 직전값을 유지했다. phase별 damping 요청/전체81 native property readback·setter state 보존도 재대조했다.
- **이번 phase의** `pre_wait_comparison.json`과 script를 확인하고 timed-ENTRY retry 대비 2.5초 전 controls150개·2.5초까지 전체 native trace76개를 직접 대조했다. 선택 목표/observation/action/history/time/phase/**info**와 비교6 SHA가 exact다. 첫 timely hit·첫 scheduled recovery 포함 prefix의 증거이며 전체1200-step 같음을 뜻하지 않는다.
- raw 합계는 timely/physical/accepted hit 각1, release5, miss3, wrong4다. 첫 event0/string2 DOWN/1.35초/+44.484798ms timely hit와 첫 scheduled recovery2.366667초는 유지됐다. 이후 wrong은 2.716667/2.95/2.966667초에 string2/3/4, raw direction−1, source phase1에서 발생했다. 최초 READY wrong1.033333초/string3의 raw direction은+1이며 혼동하지 않는다.
- 기타 최대/끝 위치 `46.353646/41.235741mm`, 회전 `8.126144/5.421837°`, 사용자 범위 안 전체/policy 표본 `235/300`, `120/130`, partial F1 `0.222222239`가 저장자료와 일치한다. native1063개 입력은 현재1061개와 exact 실행 source 사본2개로 모두 해결했고 분석 입력7개 SHA도 일치한다.
- 두 MP4 SHA·실제 ffprobe `1280×720/30fps/151프레임/5.033333초`, 5초 hands native PNG를 직접 확인했다. 문서의 영상은 이번 완료 실행의 자료로 한정된다.

해소한 Warning: prefix 링크가 이전 timed-ENTRY의 동명 파일을 가리키던 오류를 current priority phase 경로로 정정하고 `info` 포함150행/76trace/6 SHA로 설명했다. 별도 미기록 info 비교 서술은 제거됐다. 해소한 Suggestion: 다음 rebase의 이미 통과한 사전 검수를 pending이라고 적던 상태를 PASS/별도 실행 단계로 좁혔다. 정정 전 문서는 `doc_before_manifest_path_fix/`에 보존된다.

검수 SHA256: runner `5abc50c214ff8e64be727a1e77c058fdbf3002e8b8cc31b073ee320ea08eaf97`; summary `d6e42104d1f2e38b190d29c2fa4034adfb318d06672f37d75a805003f0556c80`; prefix 결과 `bddd4c726b34d151df5f7f2b3f1b93a0b9b14d08cffee111316e80d1466b3405`.

최종 범위: 대기 제어 계약·첫 회복 완료는 관측됐지만 이후 연결 타현은 실패했다. raw geometry crossing은 실제 현력·음향·지속 지지의 인증이 아니며 목표 소유권과 실패의 단독 인과도 확정하지 않는다. 부분 F1·다른 PLAY 길이를 전체 성능 승리로 해석하지 않고 조건 미채택으로 기록한 판정이 적절하다. 남은 actionable finding 없이 동결한다.
