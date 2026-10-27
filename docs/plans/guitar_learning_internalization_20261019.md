# guitar_learning 실행 의존성 내부화

사용자 요청: tab2body와 stability_adapter_2에서 가져와 사용하는 코드·자산을 guitar_learning 내부에 구현한다. 기존 외부 디렉토리·과거 결과·봉인 원본을 수정하지 않고 현행 실행 경로를 전환한다.

- [x] 프로젝트 규칙·현행 실행 진입점 확인, 변경 전 활성 패키지 전체 보존.
- [x] 물리 환경·제어·접촉·렌더의 실제 의존 코드와 모델·설정 파일을 추적해 내부 패키지로 옮긴다.
- [x] 곡 이벤트 compiler와 음악 입력 처리를 내부로 옮기고 동일 입력의 결과를 대조한다.
- [x] 현행 환경·학습·평가·기록 코드의 import·자산 경로·검증 목록을 내부 경로로 전환한다.
- [x] CPU 검사와 외부 두 패키지를 차단한 import·입력 검사를 수행한다.
- [x] 실제 Isaac Gym 초기화·짧은 물리 실행과 reset을 확인하고 기존 수치·물리 계약을 대조한다.
- [x] 문서·출처·범위·남은 의존성을 기록하고 독립 변경 검수를 완료한다.

성공 기준: 현행 guitar_learning의 실행 코드·모델·설정 로딩이 최상위 tab2body 및 stability_adapter_2를 필요로 하지 않는다. 곡 데이터·Isaac Gym 설치·과거 checkpoint/실험 결과는 별도 데이터로 보존하며, source/archive를 현행 코드에서 import하거나 sys.path 별칭으로 우회하지 않는다. 동작이 검증된 제어 로직을 우선 보존하고 불필요한 물리·보상 변경은 하지 않는다.

작업 기억·결과: docs/2026-10-12/stability_adapter_2/results/guitar_learning_internalization_v1/. 변경 전 활성 패키지: guitar_learning/archive/20261019_before_dependency_internalization/.
