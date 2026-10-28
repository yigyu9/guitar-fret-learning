# 0.25Nm grid 선정 후보의 새4환경 재현

원순위의 검지112 후보를4개 새환경의 첫시도로 검증한다. 중지114는 동일한0.25Nm 목표로 이미검수된4/4 cap실행을 재사용한다. 목표·물리·제어가 같은 중지의 GPU검사를 반복하지 않는다. grid는 목표별1회뿐이므로 통과 횟수를 재현성이나 정책 성능으로 확대하지 않는다. 기존 cap 원래목표115 실패영상도 그대로 보존한다.

1. [ ] cap grid 실제 분석 독립PASS·전체450선언/315분모/원랭킹 검산을 필수 gate로 둔다. 최소변경 순위로 고른 행만 사용하고 실패 포함4분모·원4/4 acceptance를 유지한다.
2. [ ] 기존 cap.execute/4환경 native105 verifier/private16cap/collect/속도관찰/닫기/전후검증을 그대로 재사용한다. 봉인된 원 grid표는 같고, 새 로컬 target문서에는 grid 선정행·원각+offset·서로다른4시도ID를 기록한다. 함수 실행 동안에만 helper모듈의 입력 디렉토리와 선택행 맵을 새 준비값으로 연결하고 finally 복원한다. 원 소스·원 JSON·원 봉인은 수정하지 않는다.
3. [ ] 새CPU 준비·별도검수 뒤 root GPU검지1scene 실행. 새4firstattempts/env0상세trace, 원음/범위/90충돌/PD/속도/wristv3 불변. 장면 종료/실제exit/105readback/loader 및 helper별칭 복원/입력불변을 확인한다. 중지114의 원4시도 입력/target/원acceptance 통과 정합을 별도로 확인한다.
4. [ ] 검지새4+중지기존4 시도와 실패·힘·실제각·손목 추종을 분석/별도검수한다. 두 실행의 출처를 구분하고 원4/4 acceptance와 하중/자세 판단을 분리한다. 적절한 후보를 확보한 뒤에만 해당 손가락 짧은 학습 비교로 진행하며 자유기타/전곡 성공을 주장하지 않는다.

이 디렉토리는 root 소유이며 다른 worker의 analysis 및 video 파일은 수정하지 않는다. 진단자료 정리 제외를 유지한다.


## v2: native 불러오기 전 gate 수정

보존된 reproduction_v1은 실제시작0.969초뒤Isaac import전에실패했다. 중지설정동일성확인에settings()를불러Torch가먼저import된원인이다. 장면/physics0,해당실행성과없음. v2는같은검수된두4환경설정JSON을직접비교해그대로검증하고native전gate를stdlib만사용하도록고친다. 원v1소스·준비·review·실패launcher/log/출력은보존한다. CPU회귀에서실제grid_gate호출뒤torch/isaac미import를검사한뒤별도준비검수한다. 그외로직은한줄불변이다.
