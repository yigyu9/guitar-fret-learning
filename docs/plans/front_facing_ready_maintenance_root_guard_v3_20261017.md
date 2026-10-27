# 유지제어 Root guard V3 — stage 결과 연결

정규 Root 진입은 `execute_v12.py`다. 원execute10의planes schema오류는execute11에서고쳤고, 두원본과각CPU를보존한다. 추가독립검수에서full_case가external의summary_sha256을현재result와대조하지않는공백을발견했다. execute12는 summary SHA와root_before SHA를모두대조하고그before파일도다음stage입력에포함한다. 원stage의명령/map/log확인은유지한다.

CPU4 11검사는실제source4 producer AST와원summary schema를읽어config_sha256필드가없음을검증하고원execute10오류를재현한뒤새expectedmap검사를확인했다. CPU5 15검사는실제full_case 본문에명시합성external기록을주어missing/mismatch summary/rootbefore를거부하고원execute11의summary누락통과를재현했다. 여섯필수추가감사의실패시다음native차단도확인했다. 합성기록을새물리결과로설명하지않는다.

정규생산run10/analyze9/Scene8/Controller9/Motion2/inputs_maintenance_v2/source4/remaining5/manual7/health4/fretting2/hold1는유지한다. 독립검수FINAL+master SHA+RootACK+사전입력map을완성한뒤baseline정지시험만우선실행한다. 기존20실행/577초와실패·EPS0잔차는그대로다.
