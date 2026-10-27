# 가슴 미소이동·Spine 여유 후보의 보정 후 동작 검증

최신 REQUIREMENTS_v2 및 사용자 보완 조건을 기준으로 한다. 원 baseline10 전체 통과/반복10 source 실패·모든 소비 파일을 보존한다. 강성·감쇠·힘 제한·Root·큐브·기타·충돌 필터·105/97/zero8 구분을 바꾸지 않는다. 후보의 conditional 결과와 실제 동작을 분리하며 새 PPO를 시작하지 않는다. 사용자의 기존 실험 자율진행 승인 범위에서 단계별 검사 후 이어간다.

- [ ] 두 point 후보의 oldstress28 조건부 전기간 결과를 검사한다. 하나라도 모든 gate를 통과한 경우에만 새 vector를 선정한다. 두 후보가 모두 통과하면 source 여유·Chest/후손 이동을 비교해 선택 근거를 사전 기록한다. 미통과를 epsilon이나 문턱 수정으로 바꾸지 않는다.
- [ ] 새 Scene/runtime13은 Scene8의 command 연산을 보존하고16..16.5 증분만 기존 vector+선정δ로 바꾼다. Controller12/protocol4/Motion3을 사용한다. 새 cfg·runner·analyzer·선정 경로를 새 버전으로 만들고, 원gain/cap/제어수학과 source·발·물리 건강 기준을 유지한다.
- [ ] 정지 검사를17..22로 옮기되 보정 후 유지IK가 동작하는 LH26을2396 목표에 고정됐다고 가정하지 않는다. R12는2396 유지, LH는기존fullperiod target/FK/ownership 검증과AND한다. Body9는 원upper+oldBody9+새increment+Chestlast 순서로 확인한다. 실제22초 첫동작 boundary와직전제출목표를확인한다. 상태/힘1201·목표301·원물리문턱과기타world/몸통상대 측정은보존한다.
- [ ] 저장공간 때문에 신규raw4만 gzip3 무손실 저장/명시manifest/선택된4개 text 경로 해독을 사용한다. 기존 plain 자료는 변환·삭제하지 않는다. 원시 compact JSON bytes와 복원 일치, physical/decoded SHA·CRC fullEOF·행수/step 범위를 검수하고 reader 연결을 새 Root 실행 경로에 명시한다. 영상3view·준비/실패구간을 유지한다.
- [ ] 원코드와 새코드의 수학 동일성·실제CLI/config공통성·기존원자료 작은표본·부정fixture를 검사하고 독립FINAL·동결SHA·Root사전대조/ACK를 마친다. 이 단계 전 새 native는 실행하지 않는다.
- [ ] 새 baseline28초에서 정지17..22 및 모든 필수 후처리(core/발/media/source전체/remaining/manual/health/fretting)를 검증한다. 정지모양통과를실제동작성공으로설명하지않는다.
- [ ] 정지 후보가 전부 통과한 경우 왼손 해제40초를 우선 개별 진단해 실제접촉0 후연속15초/왼팔대체지지0/기타·발을검사한다. repeat34/free_strike40/regrasp49도 각각검사한다. 개별진단실패는최종AND 실패이며낙하·중대중단원인미해결시후속을억지로진행하지않는다.
- [ ] 모든개별검사후별도83초동일실행과동일초기조건재시작을검증한다. 이전77/기존실행시간을고쳐쓰지않는다. strict EPS0와유한수치예산/물리좌표·solver원인미확정은별도이며,설명되지않은잔차를최종채택에서숨기지않는다.

검증은Root고정환경의기타지지·관절제어에한정한다. 현통과/압현준비기하와실제현힘·진동·음향·선택현압력성공은구분한다. 이 계획은아직새실제성공을주장하지않는다.
