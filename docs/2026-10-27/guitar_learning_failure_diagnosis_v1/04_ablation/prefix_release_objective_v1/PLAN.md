# 범위·후속 검증 계획

- [x] 기존 reward_objective_audit/현재 prefix 원5항·9항·원7평가·원3음 일정 읽기
- [x] 현재 CPU 환경 원 substep/end_control/settlement에 지정 라벨4종만 재생; 해제 neutrality tick-exact/full3>partial·할인/공유 press 검산
- [x] 결과·가정·actual 관측/인과 가설을 README와 results.json으로 분리
- [ ] root가 carry 실제검수 완료 뒤 소스·수치 통합 독립검수 위임

소유는 이 새폴더뿐이다. 활성·기존 실험·모델·원자료 수정0/GPU0이다. escrow는 보류 설계이며 구현하지 않는다. 새 warmstart와 섞지 않는다.

후속 별도승인이 있을 때의 정확한 구현대상은 **새 실험폴더**의 PrefixLearningEnvironment 파생 env 보상 adapter뿐이다. `_allocate/_reset_scope`에 per-env A유보/지급상태, `begin_control`에 이전A achieved snapshot, `_reward_components`에 원 A 즉시지급 제거와 유효해제 1회지급을 둔다. 원 `environment.py:substep`의 candidate/achieved/released·음 원장·물리·성공 정의는 고치지 않는다. failure-positive suppression은 원 end_control 이후 새 지급에도 명시적으로 적용해야 한다. 정책 계약의 reward descriptor/보상 schema·입력 SHA를 새 정체성으로 저장하고 원 checkpoint strict 교차로드를 거부한다. 임시 단음 schema/구계약 위장은 하지 않는다.

승인 후 검증목록:

1. A 정상clean→원창해제는 총5항 예산1.5 유지, 미해제는1.25; B7/8 budget/공유gap 유지·추가 해제 요구0. 기존 달성문턱과9항 이름은 같고 계약만 정직하게 달라야 한다.
2. skipA/precontact-only/earlyrelease/deadline-late/wrong-only는 escrow0. 반복접촉·여러falling-edge·계속released latch여도 최대.25 한 번. 원 achieved가 없는 release는0.
3. 성공+release가 같은60Hz control일 때 누락/이중지급0; 실패endpoint에서는 양성0. 실패·정상종료·마지막8·H32 경계에서 tail가짜지급0, 다음episode로 유보액 이전0.
4. 부분reset/생성 중 초기reset은 지정행만 초기화하고 다른행의 유보·원시계 보존. source index/targetID·focus_mask·A→B연결 eligibility가 어긋나면 거부. 미선택원음 skip을 이용해 예산을 늘리지 않음.
5. 모든원9항/원24이벤트·561관측/9보상PPO·gamma/lambda·NN첫tick·손목/guard/035/비선택B·전체범위/rate/cap/90쌍·움직임비용0 보존. 평가에서 music/release/AND 각각 공개하고 물리·손목실패/원3음·전128 첫시도 분모를 유지.

현재 검산은 보상 산술뿐이다. 위 후속항목은 미구현·미검증이며 실제 효과나 필요성을 미리 통과로 표시하지 않는다.
