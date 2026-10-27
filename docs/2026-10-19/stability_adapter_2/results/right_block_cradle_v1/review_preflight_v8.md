# 사전 검수 — 몸통 외부 PD150/1 재진단

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 동일 static_body9_effort 설정에서 새 계수로 bounded5초 진단을 진행할 추가 코드 차단은 발견하지 않았다. 안정성/두 접촉/팔꿈치 독립성 성공은 실제 결과 검수 대상이다.

- helper2의 물리 변경은 body9 외부 PD600→150Nm/rad,60→1Nms/rad뿐이며 설정 기록과 실제 수식이 일치한다. 같은 초기/ref33EFFORT·48POSITION·gravity+현재G 두 task·native cap300·단일human81·state guard를 유지한다. 초기 PD 모드와 물성/기타/rootlower/finger42는 바꾸지 않는다. runner6도 helper import만 변경됐다.
- 이전 body9 시도는5physics/.020833초/1control 뒤 기존 point Jacobian 속도 불일치 guard로 중단된 조건이다. 마지막 최대17.1597rad/s가50rad/s 이하였으므로 속도 한계 초과 종료라고 바꾸어 설명하지 않는다. 낮은 damping의 원인 해결을 이 코드만으로 확정하지 않는다.
- encode의 scoped_save는 패치한 parent save가 아니라 bodyhelper 모듈에 보존된 원 save를 호출하므로 재귀하지 않는다. 실제 POSITION48/33EFFORT 및 two_block final이 body9 추가 전임을 기록하도록 보완했다. body_effort_rows와 갱신 tracking이 실제 최종 명령이다. 원 helper1/runner5·실패 기록은 별도 보존한다.
- native 전체 q/qdot finite와50rad/s 초과의 각 물리 제출 전 중단 및 기존 점 J 속도 guard는 유지한다. BODY9 COM-J z계수 기록은 후처리 mass×9.81 중력 합산 대조에 사용한다. helper2/runner6 AST는 통과했다.

Warning 1 — 새 분석기3의 max_body9_scalar_deviation_deg는60Hz trace에서 계산하는 최대다. 계획의.08rad 'actual 최대' 선택 기준을 적용할 때 저장된240Hz body_rows.q_body_rad와최종 상태도 대조하거나60Hz 측정 최대라고 명시해야 한다. 어느 경우든 연속 solver 내부 최대를 인증하는 것은 아니다. body9 scalar 오차와 몸통 world 회전각도 구분한다.

Warning 2 —150/1로 줄이는 것이 안정화 보장은 아니며 body PD·gravity·두 점 task가 함께 작용한다. cap/포화·실제 q/qdot·기타 변화·두 영역의 양성 rawlambda와왼thumb/허벅지 관여를 보고 선택해야 한다. .08rad 한계만 충족해도 무왼손/오른 두블록만의 받침 성공이 되는 것은 아니다. 같은 조건의 제한된 elbow 동작 비교를 후속 실제 자료로 검증해야 한다.

검수는 계획V6·helper/runner diff·합산/guard/encode 호출과 AST에 한정했다. 분석기3의 새BODY9/48/J속도/raw/clamped 분류 코드는 앞선 검토 범위를 이어 실제 분석 결과 준비 뒤 확인한다. 추가 native/학습/추론·다른 담당 파일 편집은0이다.

검수 SHA256은 아래 실행 전 파일을 따른다.

- 계획V6: `4342cfaec028b3dfcf91b320d35f993bc1af79e839506e411fd7035a1612bde2`
- helper2: `dce1d20e88a711e623d32cc2041880788d2f21eb15ddb6c29754284694e2d0c4`
- runner6: `021aeec2e8b93e5de48d1a6c2cf57508ea3e62747ee1af732358fb39d3004d53`
