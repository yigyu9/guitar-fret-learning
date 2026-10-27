# 독립 검수

요약 판정: 문제없음. 소비된 코드·원자료·분석·native 미디어와 최종 문서를 읽기 전용으로 대조했다. 검수 중 simulator, actor, solver, 분석 producer 또는 렌더를 실행하지 않았다.

- 현재 native pick 회전으로 보정한 FK 회전식은 실제 관절각에서 identity를 보존한다. 독립 회전 대조 오차는 최대 3.514e-16 rad였다. 저장된 실제 pick/Chest/G 기준점 125개와 모든 actor 표본의 시작 회전 오차도 원자료와 일치했다. 위치 1000, 회전 5 mm/rad, regularizer 3의 soft fit이며 새로운 source 방향 gate가 아니다.
- 초기 native/PD/81관절·rate 3.2·gain 1은 비교 실행과 동일하고 PREPARE 49개 목표도 exact였다. 모든 300개 최종 목표의 float32 native-bound/rate 조립, held36, 30개 source history 역변환과 다음 251개 observation history가 exact였다. 251개 source phase 0 PI의 조건부 적분·antiwindup·요청 목표를 독립 재계산했다. source phase/detector 강제 변경은 없다.
- 실제 1200 physics steps·151 camera frames·251 actor steps·16개 계약 검사 통과를 확인했다. native 입력 1029개와 사전 사본 285개를 대조했고 종료 시 변경 0이다. 이후 승인된 main README/PLAN append 두 개는 사전 prefix가 보존되며 다른 1027개 입력 SHA는 현재도 exact였다. 분석 직접 입력 7개도 전후/current exact다.
- 원자료에서 READY 성공 0, source phase 0만, target/physical hit/physical release/accepted release 0, miss 10을 확인했다. 최소 PLAY 거리 6.379423 mm, 기타 최대/종료 회전 45.290342°/43.959132°, 전체/policy 범위 참 52/300·6/251을 독립 대조했다. 거리 10 mm 이내 native-before-control 표본은 정확히 11개이고 마지막 6연속 거리 구간이 있다. 거리만으로 source의 at_ready·grip_success 복합 조건 성공 또는 실패 원인을 인증하지 않는다.
- capture 151개·302 PNG SHA 및 readonly 기록과 두 실제 MP4의 SHA/ffprobe 151 frames·30 fps·5.033333초를 대조했다. 실제 5초 손 프레임도 확인했다. 물리 종료 5초와 영상 길이를 구별한다.

README:17의 미실행 후속 표현과 거리 표본 ‘한 번’은 원문을 보존한 뒤 정정됐다. 최종 README는 11개 표본·거리상 6연속과 source READY 0을 구별한다. README/CHANGED_FILES의 실제 파일 링크와 미채택·곡 전체 미완료 표현에 미해결 Critical/Warning은 없다. 이 PASS는 음의 진단 결과와 보존·문서의 정확성 판정이며 연주 성공, 방향 잔차 채택, force closure 또는 정식 actor 자격 인증이 아니다.

소비 runner SHA: ab043da73ed4dda0e5aec282200d004ad86764d47133dbff66310e00a6bf08b8. 보존 wrapper SHA: d503a0fdd4931968d0827a86792a11c9dbd934f53fdff75fb5fd8a4b082cf944.

최종 판정: PASS
