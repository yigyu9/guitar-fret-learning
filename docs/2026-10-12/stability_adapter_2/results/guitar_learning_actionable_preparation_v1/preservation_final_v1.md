# 정책 준비 전환: 최종 보존 감사

감사 결과: 통과. 추가 native 실행 없이 종료된 원자료·입력·보관본을 검증했다.

- Native 이전 Python 소스 115개 SHA 불변. 기록된 CPU 검사256개 통과와 로그 SHA가 일치한다.
- 여섯 실행 입력 manifest는 각각 left_initial_eval_v1: 1611개, left_ppo_smoke_v1: 1643개, left_ppo_eval_v1: 1611개, right_initial_eval_v1: 1611개, right_ppo_smoke_v1: 1643개, right_ppo_eval_v1: 1611개이며, 합집합1649개 모두 현재 원본 SHA와 일치한다.
- 이전 timing training 봉인 산출물1075개 및 원형 source snapshot143개 사본이 모두 일치한다. 이전 front video 봉인17개와 입력도 모두 보존됐다.
- 변경된 living 문서는 AGENTS.md·README.md·TIMING_TRAINING.md의3개다. documentation_update의 before/after 및 원형 archive SHA가 일치한다. 새 ACTIONABLE_PREPARATION.md를 별도 보관했다.

| 실행 | 동작 episode | 정책 전이 | reset 경계 | create/destroy | 종료 시 native 시각 | episode 물리 step |
|---|---:|---:|---:|---|---:|---:|
| left_initial_eval_v1 | 2 | 840 | 2 | 1/1 | 14.000001s | 1680 |
| left_ppo_smoke_v1 | 1 | 420 | 2 | 1/1 | 7.000000s | 0 |
| left_ppo_eval_v1 | 1 | 420 | 1 | 1/1 | 7.000000s | 1680 |
| right_initial_eval_v1 | 2 | 840 | 2 | 1/1 | 14.000001s | 1680 |
| right_ppo_smoke_v1 | 1 | 420 | 2 | 1/1 | 7.000000s | 0 |
| right_ppo_eval_v1 | 1 | 420 | 1 | 1/1 | 7.000000s | 1680 |

총 native6개가 모두 닫혔고 create/destroy6/6, 동작 episode8회·정책 전이3360개·물리 step13440개다. 모든 실제 준비시간은0초이며 첫2초의120개 action과 비용이 각 episode에 포함된다. 초기 평가2회 실행의 두 번째 reset은 누적 native 시각7초·episode step0이다. PPO 수집기는 완료 뒤 다음 episode를 준비하고 닫으므로 양손 각각 하나의 추가0-step reset이 있으며 이를 동작 episode로 세지 않았다.

각 reset에서 human DOF1회·guitar rigid1회·POSITION 목표1회를 복원했고, human rigid 직접 덮어쓰기0회·금지 호출0회였다. 같은 scene/sim/env/controller/FK 식별자를 유지했다. 첫 생성의 guard 초기 상태 호출4회와 이후 경계마다 추가2회가 최종 누적 수와 일치하여 정책 구간의 반복 상태 주입 증거가 없다. 물성 원형도 각 경계에서 유지됐다.

| 손 | 출처 PPO update | 새 initial | 새 final | 활성 Actor 파라미터 | 출력 |
|---|---:|---:|---:|---:|---:|
| left | 12 | 0 | 1 | 986434 | 33/39 |
| right | 12 | 0 | 1 | 979468 | 6/39 |

새 PPO의 초기 optimizer state는 비어 있고 활성 Actor가 실제 갱신됐다. 비활성 Actor는 그대로이며 최종 모델 계약은 strict 평가 reset 계약과 일치한다. 출처 update12를 새 update에 합산하지 않는다.

현재 source snapshot은 228개이며 원경로·SHA·정확 사본 경로를 source_final_v1.json에 기록했다. 현재 phase의 최종 README·새 계획 문서·최종 검수 문서는 작성 중이므로 포함하지 않았다. 전체 산출물 목록·봉인은 root가 마지막에 작성한다.

이 감사는 보존·회계·native 수명과 입력 일관성 확인이다. 손별 완화된 stage1 성공을 원래 음악50/100ms 성공·현 압력·음향·일반화·Root 자유 균형으로 확대하지 않는다. 숨은 PhysX cache의 완전 복원을 주장하지 않는다.
