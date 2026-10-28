# Goal codec reference128 실제 검산 준비

root PLAN의 선행 단계만 다룬다. 새 raw goal reference가 새 GoalPool decode를 거쳐 실행됐는지 확인한 뒤, 원 음악/해제/AND 기준을 분리해 보고한다. 원 incremental reference를 직접 투입한 실행으로 대신하지 않는다. producer/원 봉인/자료/다른 작업자의 파일을 바꾸지 않으며 GPU/native 실행은 root만 한다.

- [x] producer 담당자와 reference CLI·launcher·report/sidecar·fit gate 인터페이스 확정.
- [x] 합성 완료 guard/자가검증. 실제 종료 통보 전 raw/model 읽기·결과 생성0.
- [ ] 실제 launcher 종료0, reference NN0, raw goal→decoded goal→물리 요청→guard 최종 목표를 구분하고 원 reference 물리 요청과 비교.
- [ ] 128전체 첫시도/384음과 실패, 원9항·67행/3선택·354tick·native105/cap.25/90쌍·장면닫기·관련 입력 불변 검산.
- [ ] 기존 acceptance/guard/trace·arm helper 재사용: env0 60Hz 기하/각/목표/순힘/손목, env0..3 제어전관측/시계, 원 native release latch를 각 범위대로 보고.
- [ ] 한국어 RESULTS와 verification/acceptance를 고정하고 source+실제수치 통합 독립 검수1회. reference 통과 및 review PASS 전 fit gate 불가.

전체 과거 입력을 다시 수천 개씩 순회하는 검사를 추가하지 않는다. 이번 실행과 직접 연결된 준비/실행 핀·실제 readback·원 관련 검수근거를 사용한다. `reviewed_sha256`, `input_sha256`, `verified_input_sha256`는 기존 gate schema를 유지한다.

원 기준은 각음 달성·clean≥.9/wrong≤.1, all3≥.9/물리·손목실패0의 music_passed, A native release≥.9의 release_passed, 둘의 AND인 stage_ready다. 상세 다른127환경 힘은 추정하지 않는다. body resultant는 접촉쌍 압력이 아니며 reference 성공을 후속 NN 성과로 상속하지 않는다. full-native 목표 출력은 원 증분 출력과 행동 단위가 달라 표준편차의 같은 수치가 같은 물리 탐색을 뜻하지 않는다. 이번에는 새 reference만 검증하며 fit/NN·100PPO의 성과나 실행을 미리 가정하지 않는다.
