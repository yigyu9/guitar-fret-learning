# Solver 비교기의 내부 raw 요청과 실제 제출 명령 구분

기존 compare_native_limit_solver_v1.py 및 solver_comparison_v1 결과는 보존한다. V1은 두 solver의 zero8 내부 raw 요청에도 0을 요구하여 original_targets_caps_zero8_explicit를 실패시켰다. 사용자가 요구한 명시적 zero8 제어 명령 0은 실제 native 제출값 기준이다. V1의 이 묶음은 집계기 오류이며 실제 제출 명령 위반의 증거가 아니다.

원 controller_horizontal_v4.py의 effort는 gravity+posture+task로 내부 request를 만든 뒤 float32 effort를 구성하고 effort[zero_indices]=0을 적용한다. 이어 lower_effort 결과로 lower24를 교체하지만 이 결과도 zeros24에서 출발하여 zero_indices를 제외한 active16에만 값을 넣는다. 반환된 raw_requested105_Nm는 마스크 전 내부 진단값이고 submitted105_Nm가 실제 제출값이다. 이 순서를 원 소스 AST로 검증한다. 센서 반력은 두 명령값과도 별개의 측정량이다.

- [ ] 새 compare_native_limit_solver_v2.py만 작성한다. 실제 제출 zero8=0, 원 목표 zero8 reference, 원 bounds/caps/finite의 필수 검사는 유지한다.
- [ ] zero8 raw=0 여부·각축 최대절댓값·발생step을 별도 진단으로 보존하고 필수 gate에서만 분리한다. 내부 raw가 비영이고 제출이0인 합성 사례는 허용하고, 제출이 비영인 사례는 거부한다.
- [ ] 원105축 q/dq·범위 eps0·발생시간/지속/solver 비교·body SO3 수학과 실제 수치는 변경하지 않는다. V1 실제 결과·실패·stdout·사전map·Root 사후 provenance를 새 감사의 입력 SHA로 닫는다.
- [ ] 원 controller의 계산/마스크/하체 active16 순서와 변경 전후 q 수학 동일성을 CPU로 검사하고 독립검수의 명시적 완료·Root ACK 뒤 새out에서 실제 집계를 실행한다.

이 정정은 관절 잔차의 solver 원인 확정이나 후보 채택이 아니다. 반복수 증가의 개선·무개선·악화 및 원actual eps0 False를 그대로 남긴다. 5초 준비 진단을28초 전체나 준비 후11초 이상의 성공으로 설명하지 않는다. 새 native 실행/제어/자산/목표/수치 문턱 변경은 없다. 이 leaf는 실행 전 정의이며 체크리스트 완료 기록은 별도 CPU·검수 자료가 담당한다.
