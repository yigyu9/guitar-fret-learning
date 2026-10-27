# 유지제어 Root guard V2

독립검수가 실행 전 발견한 execute10의 planes 결과 schema 가정을 수정한다. 원source4 summary는 run/case/seconds/input_sha256을 제공하고 별도 config_sha256 필드는 없다. 따라서 새Root wrapper `execute_v11.py`에서 source4의 canonical cfg가 실제expected input map에 같은 SHA로 포함되는지 확인한다. 다른단계의config_sha256검사는유지한다.

원execute10/CPU85+37/fixture실패·검수지적을모두보존한다. CPU3은summary fixture에config_sha256을일괄주입한한계가있었다. 새CPU는원producer AST가만드는summary key 집합과가상새경로에서의expected map을구분해검사한다. producer기하수학·threshold·native동작은변경하지않는다.

정규입력inputs_maintenance_v2/native생산run10/source4/remaining5/fretting2는유지한다. Root진입만execute11로대체한다. 아직새producer main/native/성공선언0. 독립검수완료FINAL+RootACK+사전SHA전실행하지않는다.
