# 다음 물리실행 전 원자료 불변 확인

정규Root진입은 `execute_v13.py`다. 독립검수의추가범위제한을해소한다: 원Root12는외부기록과summary SHA는연결하지만, 감사뒤raw가바뀌었는지직접재확인하지않았다. 새Root13은external.summary SHA에연결된manual7 summary의input_sha256을기준으로당시native11파일(원10+actual16참조),canonical cfg와ready_spec13개만재대조하고다음실행입력에포함한다. 전체조상파일을다시읽는검사는추가하지않는다.

원Root10/11/12와모든CPU를보존한다. CPU6은합성external의native report SHA를잘못지정하여실제guard가정상거부한fixture실패이며before/entry/failure를보존했다. 새CPU7은해당fixture SHA만고쳐31검사통과: 원manual의10raw 실제스키마·SHA,새reference16 pin선언,11raw 각각누락/변조거부,cfg/spec변조거부,실제full_case연결및states변조시다음native차단을확인했다. 새생산코드수정0이며합성future경로를실제동역학성공으로설명하지않는다.

다른생산기능/기하수학/threshold/설정은master1그대로다. 새master2/독립검수FINAL/RootACK이완료되면baseline28초정지시험을시작한다. 아직새native0이다.
