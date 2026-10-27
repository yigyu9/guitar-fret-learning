# GPU 왼손 표면 접근·손가락별 학습 개선

사용자가 설계 제안 후 구현을 승인했다. 기본67음 전곡/035v14/자유기타/GPU 물리·기존접촉성공/안전·CPU/오른손 계약을 유지한다. 과거 봉인 결과는 수정하지 않는다. 새 계약으로 fresh 왼손 모델을 사용한다. 탐색 확대와 비용/학습률 조정은 후속 비교 실험이며 이번 기본값에서 바꾸지 않는다.

- [x] 원문/검사/문서를 archive/20261021_before_surface_fretting_v1에 SHA와 보관.
- [x] 실제 지정 손가락 메시 표면→목표영역 오차/속도와 GPU-left 24token 관측; 기하 단위검사.
- [x] 전체 목표/time 기반 potential 접근(press−2..end), per-finger 가중치, 일회 접촉·정규화 유지, 기존 음달성 기준 보존; 경계/실패/선택reset/오른손 회귀 검사.
- [x] GPU 전용 최근256종료곡/손가락별 접근·접촉 단계와 strict checkpoint 연결; CPU 기존단계 보존.
- [x] 음별 후보 탈락 원인·유지시간·성과/보상항목을 종료 로그에 기록; 모델 저장/재개·관련검사·실제GPU1024 실행.
- [x] 독립 change-reviewer 검수/수정·문서/실측 결과/최종입력 SHA 갱신.

검증: 형상만 가까워져도 load 없는 접근보상 유효,같은대상/clock potential 경계와 true-terminal0,H32경계 유지,모든finger 양성경로,40%/min50ms 성공기준 동일,손목alone 승급금지,실패tick 양성억제 및remaining5/s 유지,반대손/CPU 원계약 유지. 관련 유의미한 CPU검사와실제GPU실행을 분리 보고하고 구현 검증을 학습성능 향상으로 주장하지 않는다.

실측: 전체CPU823개PASS,독립통합9개재검사PASS. large1024/H32/seed7 fresh GPU64업데이트·2,097,152전이·708.603초 정상완료,시간축완주1009·물리종료16. 실제64→65재개·572/573입력SHA·427동결소스·3331값전체재생오차0·모든nonmetadata복원·실제oldv2 strict거부를확인했다. 새끼접근률6.41%로진행도0을유지했으며장기성능·고정정책평가향상은미검증이다. [결과](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md).
