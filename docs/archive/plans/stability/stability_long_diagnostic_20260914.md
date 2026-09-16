# Stability 장기 진단 학습 실행

사용자 요청: 장기 학습을 시도하고 로그를 확인할 수 있는 실제 실행 명령 제공.
기존 `--allow-unverified-reference`를 장기 진단에도 허용한다. 기준 자세 검증 상태와
물리 실패 조건은 유지하고 자동 승급·지지 성공 인증은 허용하지 않는다.

- [x] 실행 인자·평가 승급 분리와 회귀 검사.
- [x] 256환경 짧은 일반 PPO·주기 평가·로그 저장 확인.
- [x] 기존 사용 안내 갱신과 독립 검수, 실행·로그 명령 제공.

사용자의 3,000회 본 학습은 자동으로 시작하지 않는다. 실행 검증만 수행한다.

검증: CPU 36개 및 독립 runner 검사 12개 통과. GPU 256환경·2iteration·5 PPO epoch,
16,384표본 및 64episode 평가를 완료했다. 평가 행에 reference_verified=false,
curriculum_action=diagnostic_no_promotion을 확인했고 현재 source 지문도 일치했다.
이는 실행 검사이며 장기 학습의 성능 검증이 아니다.
