# 목표각 std 실행 개입: 실제 분석 준비

소유는 analysis/만이다. producer/준비/원70e/기존 결과는 변경하지 않는다. 지금은 source와 합성 완료 guard만 읽으며 두 root job의 실제 종료 통보 전 runs/model 읽기·결과 생성·GPU 실행은0이다.

- [x] parent 01_launcher.json의 completed/returncode0·두 child(job deterministic→stochastic)/argv=cpu_inputs/commands.json exact 조건과 합성 거부검사를 준비한다.
- [x] execution_override.json의 actualmode·sampling/RNG·변환1회·모델고정·원strictload/후보std4·원checkpoint 불변을 구분하는 작은 validator를 준비한다.
- [x] root 실제 두job 종료 뒤 직접 관련 입력 SHA와 원 native105/90쌍/.25Nm/128·close/실패/입력 before/after를 확인한다. 전체2천pin 재귀 재감사는 하지 않는다.
- [x] 조건별128시도/384음·원9항·각음/all3/A해제 교차·음악/해제/AND를 원90% 기준으로 계산한다. 모든 실패를 분모에 남긴다.
- [x] 기존 precheck/goal 분석 helper로 guard/4preobs/env0기하·각·순힘을 재사용한다. det는 원70e126/73과 비교하고 원평균 tanh를 CPU 재생한다. stoch는 저장 sampled rawgoal로 decoded/physical 요청만 재생하며 tanh(mean)과 같다고 검사하지 않는다.
- [x] runtime의 latent→action/logp/실제RNG 전진 assertion을 원 실행 감사로 재사용한다. CPU 추가 표본분포를 native 실제 표본 인증으로 바꾸지 않는다. 원메타데이터의 모델정체성과 std4 실행 개입을 구분한다.
- [x] 작은 all3/A해제 그림·짧은 결론과 source+수치 통합 독립검수1회 위임을 마쳤다. 최종 판정은 review.json에 별도 기록한다. PPO/fit/기준/예산 자동확장0이다.

상세 물리 자료는 기존 env0 60Hz/4환경 제어전 관측 범위다. 다른 환경의 미저장 기하·힘·240Hz 최초사건을 추정하지 않으며 body 순힘은 접촉쌍/현 압력이 아니다. 기존70e fit 종료1·회복평가 출처도 보존한다.
