# Goal codec 회복 평가 실제 검산

**음악 기준은 통과했으나 A 해제 기준은 미달했다.** all3 126/128, A 해제73/128로 AND readiness=False이며100PPO는 시작하지 않는다. 상세 해제창과 token 대조는 [INTERPRETATION.md](INTERPRETATION.md)에 기록했다.

원fit은 종료1이며 감사 보고서가 없는 원상태를 보존했다. 별도 독립검수된 회복 수용과 새 NN 평가 종료0을 구분한다. 새fit/추가1000회는 없다.

| A/B7/B8 달성률 | all3 | A 해제 | 음악/해제/AND | 물리/손목 실패 |
|---|---:|---:|---|---|
| 0.984375,1.000000,1.000000 | 0.984375 | 0.570312 | True/False/False | 0/0 |

원128시도/384음·실패·9항을 보존했다. raw 정규화목표·decode 각·물리요청·guard 최종목표를 구분하고 genuine GoalPolicy로 CPU 요청만 재현했다. fit 모델 자체 감사는 별도 recovery 검수 근거를 재사용했다.

상세 기하/각/힘/손목은env0 60Hz, precontrol 관측은4환경 한정이다. body 순힘은 접촉쌍 압력이 아니며 같은 std도 같은 물리 탐색은 아니다. reference 성공을 NN에 상속하지 않으며100PPO/예산확장/새GPU 실행 없음.
