# APPROACH-only 감쇠 실행 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / 미해소 Suggestion 없음. 저장 원자료·영상·문서를 검수했으며 새 native 초기화·물리 실행은 하지 않았다. 동결된 사전 검수는 `pre_review.md`에 있다.

- 실제 1200 physics steps/300 controls, native report 20계약 통과를 확인했다. trace는 terminal step736 중복표본 포함152개이며 고유 매8 step 표본은151개다. 영상은 각151프레임이다. native 입력1056개는 현재1053개와 실행 당시 exact source 사본3개로 해결했고 별도 분석 입력7개 SHA도 현재 일치한다.
- `run_strike_approach_only_damping.py:124–145`의 전환 기록4개를 재검증했다: step304/phase1 quarter, step328/phase2 baseline, step572/phase1 quarter, step664/phase2 baseline. R9 damping 이외 전체81 properties의 원본 유지·요청/native readback exact·setter 전후 state 보존이 모두 일치한다.
- 첫 baseline 복원 전 controls82개와 복원 시각까지 전체 native trace42개를 직전 APPROACH-damping과 직접 대조했다. 목표·phase·관측·행동·history/time 및 비교6개 SHA가 exact다. 전체1200-step 동일성으로 확대하지 않는다.
- raw pulse 합계는 timely target hit1, physical target hit2, geometry accepted release2, physical release6, miss3, wrong4다. 첫 hit는 zero-based event0/string2 DOWN/1.35초/+44.484798ms다. 두 번째 event3/2.75초는 physical hit지만 premature `−64.536217ms`, timely target_hit=false다.
- clearance 첫 lifted/reached/scheduled completion 시각 `1.4/2.183333/2.366667초`와 source 복귀를 확인했다. 이후 RECOVER wrong3과 최초 READY wrong1로 source는3.066667초에 종료된다. PREPARE/PLAY/HOLD 표본 `49/135/116`, 부분 running F1 `0.400000006`을 전체 곡 성공·비교 우위로 해석하지 않는다.
- 기타 위치 최대/끝 `46.353646/36.393910mm`, 회전 최대/끝 `7.095455/4.927969°`, 사용자 범위 안 전체/policy 표본 `287/300`, `125/135`가 원자료와 일치한다. 두 MP4 SHA와 실제 ffprobe `1280×720/30fps/151프레임/5.033333초`, 2초 hands 및5초 whole-body PNG를 직접 확인했다. 한국어 문서의 실제 절대 링크·원자료 출처를 대조했다.

해소한 Warning: CHANGED_FILES:17–18 및 README:5는 native closure1056과 **별도 분석 입력7개**를 각각의 before/after 기록으로 구분했다. 정정 전 문서는 `doc_before_closure_clarification/`에 보존된다.

검수 SHA256: runner `2b7f8b71fa91e11705f46f019252bb4987e8bea4cedfa12a5e0a9ef839437ddd`; summary `9adbcf66f7e334fb9865b5afa2aad530424c6e762bb845c843bb0fd5866f54da`; 복원 전 비교 결과 `52990ec173684bdf9adcfcfd7d54068b3782c53ea8ff3589c831fdb41fa85f35`.

최종 범위: 실제 source phase에 따른 감쇠 변경·복원과 첫 회복 완료는 관측됐다. 원인 규명, 지속 접촉·지지, 전체 음악 성공은 인증하지 않는다. source 종료 이후는 HOLD 물리/녹화이며 현재 조건 미채택·후속 시간창 진단이라는 문서 판정은 적절하다. 남은 actionable finding 없이 이 검수 기록을 동결한다.
