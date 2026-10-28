# 고정225 grid 압현 진단의 결과 분석 준비

상위 PLAN/probe/준비봉인/source는 수정하지 않는다. 두 finger의 실제 GPU 종료를 root가 통보하기 전에는 결과 분석을 실행하지 않는다.

1. [x] 분석 틀을 준비한다. 원 probe의 grid/choose/complete/read/sha와 기존 ledger를 재사용하며 새 판정이나 후보 순위를 만들지 않는다.
2. [x] root actualexit0/70.260730635초 통보 뒤 두 launcher와 report/scene/inputs_before·after/settings/690준비핀을 확인했다. 전체225표/제외사유와 검지135·중지180 첫 시도, env_id→grid_index·baseline112를 검증했다.
3. [x] 원 ledger를 독립 집계하고 probe.choose와 별도의 순위 계산도 일치했다. 검지 eligible21의 선정115, 중지 eligible4의 선정114이며 두 행 clean100%/wrong0이었다. 실제4반복 재현은 아직 미완료다.
4. [x] MCP x/z25조합×PIP/DIP9조합의 전체225 clean heatmap을 그렸고 범위외는 회색x로 표시했다. 모든450선언행은 CSV에 보존했다.
5. [x] baseline/선정 후보의 음 중 body1/2/3 하중·selected actual/target·손목/패드/gate를60Hz 요약으로 대조했다. 중지114는 사전 상세trace 밖이라 경량통계·ledger만 사용했다.
6. [x] 상세16trace의3,512끝점 helper와 phase통계를 재생·대조했다. 전체315시도의240Hz ledger와 구분했다. mean/max/RMS를 median/240Hz max·현별압력·접촉쌍·자연스러움으로 확대하지 않는다. 한국어 표/그림/CSV/SHA를 고정한 뒤 기존 reviewer에게 actual 검수를 요청한다.

후보가 있어도 새4시도 재현과 힘/자세 검토 전에는 학습 단계의 준비 완료나 성공 모델로 취급하지 않는다. 후보가 없다고 전체 도달 불가능을 주장하지 않는다. 새 GPU/native 실행은 분석 범위가 아니다.
