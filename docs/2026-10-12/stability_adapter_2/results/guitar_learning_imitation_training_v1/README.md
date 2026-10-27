# 성공 궤적 초기화와 손별 PPO 학습 결과

교사 동작을 Actor에 학습시킨 뒤 양손을 따로 PPO로 보완했다. 양손 각각24업데이트·11,520전이·48에피소드를 완료했고, 학습 중 손별 기술 성공은 각각48/48이었다. 최종 모델도 실제 결정적 평가에서 각각2/2 안전하게 성공했다. **현재 첫 단음·동일 준비 시작에서 손 기능을 재현하는 학습 정책을 얻었다. 음악 타이밍·양손 결합·초기 자세의 정밀 지지 요구까지 완료한 것은 아니다.**

## 최종 모델과 자료

| 구분 | 왼손 hold | 오른손 cross |
| --- | --- | --- |
| 최종 PPO 모델 | [left_ppo_v1/final.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/left_ppo_v1/final.pt) | [right_ppo_v1/final.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/right_ppo_v1/final.pt) |
| 초기 BC 모델 | [left_bc_v1/actor_initialization.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/left_bc_v1/actor_initialization.pt) | [right_bc_v1/actor_initialization.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/right_bc_v1/actor_initialization.pt) |
| 실제 최종 평가 | `left_ppo_eval_v1` | `right_ppo_eval_v1` |
| 학습 성공 / 완료 | 48 / 48 | 48 / 48 |
| 최종 반복 평가 성공 | 2 / 2 | 2 / 2 |
| 학습 / 최종 평가 물리 실패 | 0 / 0 | 0 / 0 |
| 음악50/100ms 매칭 | 0 / 0 | 0 / 0 |
| 학습 소요 시간 | 약26.42분 | 약26.36분 |

두 학습은 동시에 진행했다. `final.pt`는 해당 실행의 마지막 모델이며 최적 모델로 선정한 뜻은 아니다. BC와 PPO 모두 현재 손별 성공 후보로 보존했고, 양손 결합에는 자동 승격하지 않았다. [후보 경로·SHA·범위 정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/policy_candidates_v1.json).

## 어떤 학습을 했는가

목표는 `05_BN2-131-B_solo` 첫 단음의 물리2번줄·7프렛·약지·down이다. 상태505, 이벤트64×24, 우선 이벤트2×24, 행동39(LH33/RH6), medium 전체 모델2,920,528파라미터를 유지했다. 선택한 손의 Actor만 움직이며 반대 손은 행동0의 기준 목표를 따른다. Root고정·하체유한제어·105입력/97비영범위/8원래영범위, 기타자유·중력ON·스트랩OFF, 기존 물성·접촉·gain·의자·행동범위·평활화·속도와 물리 종료 조건을 유지했다. 준비는 저장된 자세에서 실제2초, 손별 기술 구간은4초다. 기타 직접 힘·부착·연속 상태 덮어쓰기는 사용하지 않았다.

새 `imitation_environment`는 실제 성공 경로에 맞는 profile을 계약에 명시한다. LH는 distal원점 거리 보상만0으로 하고 원래 native 접촉과50ms 연속유지 성공을 쓴다. 실제 접촉에 성공한 교사도 원점거리15mm를 만족하지 않았기 때문이다. RH는 기존 허용 영역 안의 y−.36m/depth4mm/앞뒤8mm guide를 쓴다. 원래 타현 속도·방향·깊이·유한 현 범위·재준비 판정은 유지한다. 이 profile에서 기존 교사 행동을 실제 재생해 새 관측240행을 수집했다.

BC는 활성 Actor의 인코더·출력만2000step, full batch240, lr3e−4, seed7로 학습했다. 수치fit 목표1e−6는 미달했다(LH2.480236e−5/RH5.431589e−5, `converged=false`). 이를 숨기지 않고, 실제 학습 정책의2/2 안전 성공을 별도 PPO 진입 조건으로 삼았다. Critic·반대 손·std는 BC에서 최적화하지 않는다. PPO는 활성 Actor와 명시std.02만 전달하고 새 Critic·optimizer·counter0으로 시작했다. [실제 저장 모델 초기화 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/initialization_audit_v1.md).

PPO는 손별2환경/H240/24업데이트, cost_weight1, 초기actor_lr1e−5, value_lr3e−4, std.02, soft wall1800초로 실행했다. 첫 업데이트의 큰 정책 변화는 KL 보호 장치가 복원·재시도했고, 이후 실효Actor lr는 LH6.25e−7/RH2.5e−6였다. 수용된KL 최대는.007026/.017898, 거절 시도까지 포함한 최대는.754529/.064133이다. 반복 시도2/1과 낮아진lr를 초기 설정과 구분한다. 입력 변경·guard 위반·정리 오류 없이 두 실행이 `updates_complete`로 종료됐다. 각worker의 시뮬레이터는 한 번 생성해 reset을 재사용했고 종료 후 모두 닫혔다.

## 실제 최종 평가와 초기 모델 비교

아래는 최종 정책을 탐색 없이 실행한240Hz 측정이며 학습의60Hz 끝점 집계와 구분한다. 전체 시간의 기술 ledger와 원래 악보 시간창 ledger도 서로 구분한다.

| 지표 | LH 최종 평가1 / 2 | RH 최종 평가1 / 2 |
| --- | --- | --- |
| 최초 손별 성공 | .9875 / .954167초 | 2.329167 / 2.329167초 |
| 연속 목표 접촉 후보 최장 | 3.0625 / 2.6125초 | 해당 없음 |
| 적격 기하 통과 | 해당 없음 | 각각4회, 목표down2회 |
| 기타 최대 이동 | 5.264 / 5.097mm | 각각.5884mm |
| 기타 최대 회전 | .9977 / .9397° | 각각.1249° |
| 발 최대 이동 | 3.2098 / 2.9557mm | 각각.04467mm |
| 주요 지지 존재 / 양발 접지 | 모두100% | 모두100% |
| 세 부위 동시 지지 | 6.667 / 6.563% | 모두100% |

초기 BC도 각각2/2 성공했다. LH BC 연속유지는2.875/2.870833초였으므로 최종 PPO가 모든 평가에서 더 오래 유지한 것은 아니다. RH BC 최초 성공2.079167초보다 최종2.329167초가 늦다. 기타·발 편차도 일률 개선되지 않았다. 이번 결과는 **성공 초기화와 제한 PPO 후 기능 유지의 확인**이며, PPO 추가 학습의 일관된 우월성·수렴·일반화 증거는 아니다. 같은 조건에서 BC만 바꾼 무작위 대조 실험도 수행하지 않았다.

왼손은 오른상완·허벅지 접촉과 양발을 유지했지만 가슴 접촉이 대부분 끊겼다. 현 학습의 주요 지지 존재 조건을 통과해도 원초기 자세V3의 삼중 지지95%를 통과한 것이 아니다. 왼손의 하중 기여가 필요했는지도 직접 검증하지 않았다. 기타가 떨어지지 않았다는 사실로 이 문제를 대신 설명하지 않는다. 이 때문에 먼저 지지 유지·왼손 하중 비의존을 보완하고 검증한 뒤 결합을 검토해야 한다.

손별 성공은 실제 접촉 후보와 기하 통과다. 현 압력·진동·음향과 사람 동작 유사성은 검증하지 않았다. 원래 악보 시간 매칭50/100ms는 초기·최종 모두0이며 다른 음·곡·시작 자세와 양손 동시 성공도 미검증이다. LH 원score창 유지값은 별도 결과에 남겨 전체4초의 최장 유지와 혼동하지 않았다.

[BC 실제240Hz 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/bc_native_analysis.md) · [최종 PPO 실제240Hz 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/ppo_native_analysis_v1.md) · [학습 전체 집계와 앞뒤 구간 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/ppo_analysis_v1.md).

![24업데이트 학습 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/ppo_progress_v1.png)

## 실행·로그·보존

[코드와 재실행 설명](/home/ajou/yigyu/3/guitar_learning/IMITATION_TRAINING.md) · [계획과 체크리스트](/home/ajou/yigyu/3/docs/plans/guitar_learning_imitation_training_20261018.md). 현행 실행기는 `guitar_learning.train_imitation_ppo_v2`, 실제 평가는 `guitar_learning.evaluate_imitation_v2`다. 설정은 `left_ppo_settings_v1.json`과 `right_ppo_settings_v1.json`이고 새 출력 경로를 사용한다.

학습 디렉토리에 initial/final/4업데이트마다checkpoint, `update_*.json`, `transitions.jsonl.gz`, `status.json`, `events.jsonl`, `resources.jsonl`, `report.json`, specialist/skill/persistent 보고서를 남겼다. 평가에는 각episode reset·행동 직전 관측·정책 행동·4physics표본/tick·result를 남겼다. CPU검사207개를 통과했고 실제 결과는 [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/review_results_v1.md)로 별도 확인한다.

v1 BC 평가2개는 JSON list/native tuple 계약 표현 비교로 정책 실행 전에 거부됐다. 실패 기록과 닫힌 장면을 보존하고, v2는 계약의 값·키·크기·역할 검증을 유지한 채 동일 JSON 표현만 정규화했다. [구현 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/review_implementation_v2.md). 작업 이전87파일은 `guitar_learning/archive/20261018_before_imitation/`, 사용한v1파일5개는 `archive/20261018_before_imitation_contract_v2/`에 원 경로와SHA로 보관했다. 활성 의존성은 원 경로를 유지한다. 이전 실행·실패·원자료를 덮어쓰지 않았다. 최종 보존 감사의 정본은 `final_verification_v1.json`이다.
