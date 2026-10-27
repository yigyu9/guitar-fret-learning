# release_v6 후처리 SIGFPE 보존·재시도

실제 native_release_v6는34초/8160step 정상종료했고 외부입력불변이다. feet/media 검사는 통과했다. analyze_v6의 후처리 프로세스만 returncode−8(SIGFPE)로 중단됐다. 원인 미확정이며 원자료·기존32py·실패로그/외부기록·partial analysis_release_v6는 수정하지 않는다. summary가 없으므로 기존분석을PASS로 취급하거나 후속 native로 넘어가지 않는다.

- [ ] 새execute_v7은 기존execute_v6에서 사전입력map 이름을v7로 바꾸고, 선행 release core의 경로만 명시적 `analysis_release_v6_retry_v1`로 바꾼다. 기존case순서/모든core gate/feet/실제config·spec·RAW SHA 검증을 그대로 유지한다.
- [ ] 새freeze_analysis_retry_v1은 기존before_v6 전체와 현재baseline/repeat/release actual/native/완료분석·실패분석/feet/media 및wrapper/provenance, 새wrapper와이leaf를 사전에 pin한다. 원코드·입력은 그대로다. 실패closure도 보존한다.
- [ ] 문법·동일원검증수식/명시경로치환·완료summary없으면차단을CPU·독립검수하고 reviewer 완료/SHA를RootACK한 뒤 실행한다.
- [ ] `PYTHONFAULTHANDLER=1`로 동일analyze_v6를 새out에서 재실행한다. 새tag도 `analysis_release_v6_retry_v1`이다. 원물리실행은 반복하지 않는다. 재시도분석이 실제core+feet를 모두통과해야 다음free_strike_v6를실행한다.
- [ ] 실패/재시도와 실제물리시도수·완료수는 구분한다. 신규PPO0/새물리0. 결과가 또중단되면 새version에서원인/스택을진단한다.

Root는 새wrapper/closure/이계획과 실행을 소유하고 reviewer는 독립검수만 소유한다. 분석담당 추가감사에는 명시적 completed core경로인자를 사용하고 실패폴더를 자동탐색하거나 덮어쓰지 않는다.
