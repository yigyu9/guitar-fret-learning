# 실제 articulation motion의 읽기 전용 관측 제안

정적 검사에서 같은 설치 binary의 `setMotion`/`getMotion` 및 enum 대응을 확인했지만 현재 actor의 실제 적용 경로는 미확인이다. 기존 USD는 source descriptor와 actor 배치를 포함하므로 이 공백을 대신하지 못한다.

목표는 별도의 **0 physics-step 생성자 진단**에서 실제 관절에 전달된 motion과 최종 getter 값을 읽는 것이다. 원래 함수 호출·인자·반환을 그대로 전달하는 관측용 shim을 새 경로에 작성할 수 있는지 먼저 검토한다. 실제 동작 시험의 환경·소스·library bytes는 변경하지 않는다. 현재 반복/왼손 시험은 기존 동결 실행기로 계속한다.

1. 정확한 설치 symbol·vtable·ABI를 정적 근거로 고정한다. 조회에 필요한 layout이 불명확하면 추측한 메모리 읽기를 추가하지 않는다.
2. 최소 관측 shim과 fake joint ABI 반례 검사를 작성한다. 원 호출 한 번 전달·인자/반환 보존·읽기만 수행하는지 확인한다. 후킹이 적용되지 않거나 이름/축 연결이 불명확하면 명시적으로 실패한다.
3. 별도 probe는 실제 scene만 만들고, 읽기 전후 native state/property의 의미 있는 필드를 대조한 뒤 닫는다. simulate·state setter 추가·힘/목표 변경·export는 하지 않는다. 원래 scene 초기화 호출과 관측 코드를 구분한다.
4. 독립 검수 FINAL과 Root의 입력 사전 봉인/ACK 전에는 실제 probe를 실행하지 않는다. 실제 실행은 진행 중인 native scene이 닫힌 구간에만 허용한다.
5. 실제 요청/최종 motion·limit 및 source 채널 연결이 확인돼도 정량 solver 잔차의 단독 원인이 증명됐다고 확대하지 않는다. EPS0/cause/final adoption은 별도 판정한다.

현재는 계획이며 새 shim·probe·native 실행은0이다. 이 제안이 구현 가능한지 확인하기 위해 원 모델을 수정하거나 원래 0범위8축을 삭제하지 않는다.
