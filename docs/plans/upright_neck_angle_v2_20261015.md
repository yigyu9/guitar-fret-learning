# 기타 목 상향 후보의 높은 초기 탐색

source13은Chest/양손근접을얻었지만R_Hip gap−59.8mm(중심선이convex내부)로실패/native미사용이다. 최소거리0인경우gap이−radius에고정되어국소미분기반solver가탈출하기어렵다. 이실패가허용공간전체의불가능성을증명하지않는다.

source14는동일source9몸통/Head/하체를유지하며기타initialZ범위를+.13~.35m로높여상부seed에서다시시작한다. 기타목worldY추가+.25~.55rad/양손guitar-local5mm·2°/모든sourcegap양수/Chest·RShoulder근접/BOX·의자·지면·자기충돌audit조건유지. 통과시에만scene8/controller10유한제어로새정지5초;실제Chest/RShoulder>95%1초후와기울기total5°/right3°/모든guard통과후15초해제. 코드/입력/원자료보존,Root고정,기타자유중력ON/strapOFF,105/97/zero8,PPO없음.

- [ ] source14 계산 및 원범위·손 도달 확인
- [ ] 독립 전체sourceaudit
- [ ] 실제 정지5초 지지 확인
- [ ] 통과시에만 왼손15초
