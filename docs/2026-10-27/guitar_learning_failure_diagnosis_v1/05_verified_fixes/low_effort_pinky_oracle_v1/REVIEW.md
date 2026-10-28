# 소지 유한 grid 준비 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

1069개 입력 SHA와 새 프로세스의 실제 선행 actual gate를 확인했다. gate 전후 Torch/NumPy/Isaac은 import되지 않았다. 원reference+같은4축 offsets225개를 독립 계산해 native범위 안72개·제외153개·0offset112와6개 유효 상세기록행을 확인했다. 범위나 판정·랭크를 완화하지 않는다.

원 grid/grid수집/선정/execute/settings를 재사용하며 HERE/INPUTS·runtime.ShortPool만 scope 내 연결한다. task/control 기대값은 검수된 소지reference4 기록에서 진단필드 하나만 제외한 사본이며 실제생성 basecontract와 비교한다. 이를 새20Nm 실행으로 보고하지 않는다.

실제72환경용 verifier는 원cap helper의 expected_properties/private loader를 쓰고105전필드·16effort만0.25·나머지89/엄지5·원90쌍·72 readback·physics0·controllercaps를 검사한다. 기존 hard4/135180 검증을 우회하지 않는다. 실제 nested wrapper CPU fixture에서 정상, native검사 실패, 계약불일치 및 각각close동시실패를 시험했다. 원 AssertionError 보존·close1회·별도cleanup·loader/pool/input 객체복원이 모두 통과한다.

prepare5JSON을 메모리로 재생해 exact 대조했다. pending/기존/깨진출력은 native 전에 거부되며 runs가 없다. 실제72시도 성과·자원적합성은 미검증이고 random성공env3의 누락자세를 역산하지 않는다. 성공선정 뒤 새4재현과 하중/손목 검토가 별도다. GPU/native 실행이나 기존파일 수정은 하지 않았다. 최종6파일 SHA·pending1069 입력 fingerprint는 [review.json](review.json)에 기록했다.
