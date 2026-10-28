# fresh112 v2 import 순서 delta 검수

요약 판정: **문제없음 / PASS**. 남은 Critical·Warning·Suggestion 없음.

v1 검수는 Torch가 이미 import된 CPU 환경에서 gate를 검사해 실제 새 프로세스의 import 순서를 놓쳤다. 보존된 v1 launcher는 exit1이고 로그는 Isaac import 시 Torch 선행 import 오류를 보여준다. 별도 새 CPU subprocess에서도 v1 grid_gate가 Torch/NumPy를 import하는 원인을 재현했다. 해당 실행을 음악 성과로 세지 않는다.

v2는 middle 설정 검사를 검수된 두4환경 JSON의 동일성 비교로 교체했다. 새 Python3.8 subprocess에서 probe import 전후 및 실제 전체 grid_gate 실행 전후 torch/numpy/isaacgym 부재를 독립 확인했다. 원886개 근거경로 검증과112/114 선택이 통과한다. 기존 전체 review·입력 SHA가 두 설정도 보호하므로 원 검증을 생략하지 않는다.

AST 비교상 변경은 grid_gate와 prepare뿐이며 launch·selected_inputs는 동일하다. 원 v1 검토파일7개 SHA는 그대로다. 새 target/settings3파일은 byte exact, effort 선언은 JSON 값이 같고 dict 출력순서만 다르다.893개 핀 확인, 메모리 prepare 재생6JSON 일치,112 동적 문서/정상·예외 alias복원 및 pending/기존/깨진출력의 native 전 거부를 확인했다.

원cap.execute/4환경 verifier·판정·분모·닫기 경로를 재사용하며 신규 GPU 대상은 검지112의4시도뿐이다. 중지114는 기존4/4를 출처와 함께 재사용한다. GPU/native 실행과 기존파일 수정은 하지 않았고 v2 runs는 없다. 실제 성과·하중은 후속 실제 검수 대상이다. 최종7파일 SHA·pending 입력 fingerprint·v1 실패근거 SHA는 [review.json](review.json)에 기록했다.
