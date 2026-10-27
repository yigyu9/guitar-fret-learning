# 손별 사전학습과 공동 적응 구조 구현 계획

사용자 승인 범위: 2026-10-18 손별 성공을 먼저 확보할 수 있도록 구조 구현. 자유 기타와 안정성 조건은 모든 단계에서 유지한다. 장시간 학습은 이번 구현 범위에 포함하지 않는다.

## 설계와 성공 기준

- 왼손33/오른손6 독립 Actor 인코더, 전체 관측 기반 reward/cost Critic. 기존 468 상태·음악 토큰·39 행동 ABI 유지.
- left/right/joint 단계. 단독 학습의 비학습 손은 기준 목표를 유한 제어로 유지한다. 전문가 결합 후에는 동결한 반대 손을 결정적으로 실행하고 선택한 손만 탐색/갱신할 수 있다.
- inactive/frozen 역할은 행동뿐 아니라 log probability·entropy·KL·optimizer에서 제외한다. 전문가 전체 branch를 이식하며 가중치 전달은 strict resume와 구분한다.
- 왼손 실제 접촉·연속 유지와 오른손 접촉 비의존 기하 타현·시간을 별도 판정한다. 기존 통합 음악 이력을 조작하거나 성공으로 대체하지 않는다. 통합 단계는 기존 음악 기준 사용.
- Root 고정·하체 유한 제어·105/97/8·자유 기타/중력ON/스트랩OFF·2초 준비·240Hz 비용과 실패 종료를 유지한다. 모델·자세·gain·충돌 정책 변경 없음.
- 거리 보상·접촉 후보·기하 타현·통합 음악 성공을 구분하여 로그에 기록한다. 후처리로 물리 성공을 가장하지 않는다.

## 체크리스트

- [x] 현재 제어·측정·정책·PPO·persistent runner와 지침 확인.
- [x] 이전 변경 대상 소스/관련 검사/문서의 SHA 보관.
- [x] 독립 Actor, 활성 역할 분포, 전문가 전달과 엄격한 재시작 구현 및 CPU 검사.
- [x] 단계별 환경·보상·성공 지표와 공통 안정성 연결 및 CPU 검사.
- [x] persistent 병렬 실행·설정·checkpoint·지표 저장 연결.
- [x] CPU 전체 검사와 짧은 실제 native 실행으로 역할 분리·물리/저장 계약 확인. 전체168개+최종 runner5개, 실제5실행/444전이/1776정책물리표본/완료5episode/물리실패0. 성공한 손 기술은0회이며 연결 확인용 fixture다.
- [x] 별도 change-reviewer 검수·지적 수정·결과/실행법/한계 문서화. 원자료·checkpoint·전체 branch/std·88개 동결 출력·strict resume와 source SHA를 독립 대조해 미해결 지적 없음. 실행법은 guitar_learning/SPECIALIST_TRAINING.md, 실제 근거는 결과 README/native_verification_v1.json/review.md.

결과 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1`.
실제 학습 성공과 양손 결합 성능은 별도 후속 검증이며 연결 검증 결과로 주장하지 않는다.
