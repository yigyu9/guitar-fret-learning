# 손목 위치 미분 좌표 보정 v2

기존 승인된 실패 진단 계획의 후속 최소 수정이다. 동시 q/qd/nativeJ/body 감사의 실제 분석 독립 PASS 이후에만 활성 소스를 수정한다. 현재 보존·정리 중단 지시를 유지한다.

가정과 범위: 팔의 네 3축 관절은 현재 q와 독립 FK/native pose 일치를 검증했다. 속도 Jacobian을 q-position 증분에 곧바로 쓰는 diagnostic wrist helper만 교정한다. 기본 raw J33 학습 실패의 원인으로 확대하지 않는다. 손가락 MCP2축·발 IK·엄지 helper·과거 docs filter는 이번 변경 대상이 아니다.

1. [x] 실제 좌표 감사 독립 검수 완료 → verify: 같은시각 16표본, COM/순서/4개 env와 env0 delta4개, 잔차/한계 확인.
2. [x] 현재 활성 Python 및 README/AGENTS를 새 archive에 보존 → verify: 원경로/byte/SHA 전항목 일치. 기존 archive/결과/봉인 수정 금지.
3. [x] wrist helper의 qpos 미분 Jacobian만 구현 → verify: source XML/이름 기반 4개 3축 group, analytic SO(3) left derivative와 ownbody native angular basis 변환. reset행은 basis solve 이전부터 제외. 속도/힘용 nativeJ를 바꾸지 않는다.
4. [x] 의미 있는 CPU 검사·별도 코드 검수 → verify: 독립 FK 유한차분/실제 동시 표본, 0/작은 회전/축 순서/회전 frame/reset NaN, 이전 계약 strict 거부와 새 동일계약 로드.
5. [x] 현재 소스의 새 initial로 검지 bootstrap/reference/zero/random(각4 첫시도)을 GPU 직렬 실행 → verify: 입력/모델/장면 종료, 실제240Hz 판정·손목 추종·부하를 기존 기준과 비교. 원 .5도 cap/2초 ramp/3초 음 시작/PD/범위/보상/codec 유지. gain 추가 탐색 없음.
6. [x] 중지 및 나머지 손가락 회귀·결과 독립 검수 → verify: 일부 성공을 모든 손가락 학습·자유 기타·전곡 성과로 확대하지 않음. 결과에 따라 짧은 학습/음 전환/자유 기타 단계로 돌아감.

구현은 wrist.py/runtime.py 및 관련 검사만 담당 worker가 수정한다. root는 보관/계획/현재 안내 문서/새 실행 준비를 담당한다. 기존690pin 관찰과 결과를 덮어쓰지 않는다. 새로운 계약은 wrist_control v2로 명시하고 기존 checkpoint source/contract 검증을 완화하지 않는다.

성공 기준은 정확한 미분 좌표 및 실제 재검증이다. 손목 수학 수정만으로 압현/학습 문제가 해결됐다고 보고하지 않는다. 전체 목표의 나머지 사항은 master plan을 계속 따른다.

실제 분석 독립 검수 PASS. 보관 519항목(활성 Python517+문서2)의 byte/SHA가 원본과 일치했다. 보관 manifest: `guitar_learning/archive/20261027_before_wrist_position_jacobian_v2/manifest.json`.

실행 전 CPU 4모듈38검사 PASS(작업자 보고 7.031초), 별도 코드검수/새 current-source 준비검수 진행 중이다. 수치/입력 SHA는 implementation_verification.json에 기록했다.

별도 code review PASS. 원519 보관 SHA·변경범위·실제16표본 fixture 전배열·18개 핵심 CPU검사를 독립 검산했다. 현재 native_precheck 준비검수만 남았으며 GPU는 실행 전이다.

검지 새 GPU4단계 종료0/103.875초, reference/zero/random 모두0/4·전체12평가시도 종료실패0. actual initial73tensor동일/모든sidecar검증 PASS. 압현개선은미달이며 actual분석독립검수 및 다른손가락회귀는 남았다. 새 gain탐색 없이 별도 wrist_target_feedback_audit에서 요청가상FK/실제추종을 기존raw로 분리한다.

다른finger12단계종료0/307.505초·694준비핀·actual73tensor/hash·전체36평가시도·1,995끝점CPU판정재현및독립검수PASS다. ref중지0/4·약지4/4·소지3/4로압현미해결을기록하고새candidate v3후속으로진행한다. 전체진단목표의완료를뜻하지않는다.
