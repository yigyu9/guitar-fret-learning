# 전곡 보상 개선과 추가 학습 결과

보상 계산의 두 결함을 수정하고 추가 학습과 전후 고정 평가를 완료했다. **보상 수정은 실제 물리 표본에서 검증했지만, 최종 모델의 연주 성능 향상은 확인되지 않았다.** 기존 코드·모델·실패 기록은 보존했고 새 구현은 [song_reward_v2](/home/ajou/yigyu/3/guitar_learning/song_reward_v2/README.md)에 모았다.

## 최종 고정 정책 평가

각 모델을 엄격하게 불러온 뒤 학습·확률적 탐색 없이 같은 곡의 67개 목표를 평가했다. 각 실행은 32.8167초, 1,969개 제어 단계, 7,876개 물리 표본이다.

| 지표 | 기존 전곡 8업데이트 모델 | 보상 수정 후 추가 24업데이트 모델 |
|---|---:|---:|
| 올바른 압현 | 1/67 | 1/67 |
| 타현 목표 성공: 완화 시간창 | 0/67 | 0/67 |
| 압현·타현 협응 | 0/67 | 0/67 |
| 원래 음악 판정 50ms / 100ms | 0 / 0 | 0 / 0 |
| 오타현 / 전체 기하 통과 | 1 / 1 | 2 / 2 |
| 기존 안전 기준 전곡 완주 | 통과 | 통과 |

두 모델 모두 첫 음만 0.2322초 동안 올바르게 유지했고, 이후 66개 음의 clean 유지시간은 전부 0이었다. 오타현은 오히려 한 번 늘었다. 따라서 총 return이 -80.4674에서 -77.9705로 바뀌었다는 사실을 연주 개선으로 해석하지 않는다. 보상식과 wrong_press_s의 집계 구간이 달라졌기 때문이다.

최종 평가의 기타 최대 이동은 약 10.34mm, 회전은 약 1.455°였다. 240Hz 표본에서 전체 주요 지지·오른허벅지·양발 접촉의 부재시간은 0이었다. 가슴 접촉률은 약 5.47%였으며, 현 기준에서 가슴 접촉 지속은 필수조건이 아니다. 금지 호출·실행 실패·정리 오류는 없었다.

[기존 고정 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/baseline_fixed_evaluation_v1/result.json) · [최종 고정 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/final_evaluation_v1/result.json) · [전체 수치 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/analysis_v1.json)

## 수정한 보상

1. **준비 중의 잘못된 오압현 벌점을 제거했다.** 이전에는 다음 음의 준비가 시작되면, 아직 정상적으로 울리고 있는 이전 음의 높은 프렛을 잘못 누른 것으로 감점했다. 이제 오압현 비용은 해당 음의 발음 구간 onset~end에서만 적분한다. 예를 들어 7프렛 약지를 유지하며 다음 5프렛 검지를 준비할 때, 현재 음의 정당한 유지를 다음 음의 오압현으로 벌주지 않는다. 접촉 분류, 미압현, 유지시간, 실제 타현 매칭과 원래 50/100ms 판정은 보존했다.
2. **오른손의 정지 거리 보상을 제거했다.** 목표 근처에 머무르기만 해도 받던 연속 양성 보상을 없애고, 같은 목표의 고정 출발점에 가까워지는 potential 차이를 60Hz에서 한 번만 작게 부여한다. 식은 `0.25*(0.99*Phi_after-Phi_before)`, Phi의 거리 척도는 3cm다. 목표 진입·교체·이탈에는 별도 보너스가 없고 실패 단계의 양성 보상은 억제한다. 목표 경계를 별도로 처리하므로 전역 최적 정책의 불변성을 입증한 방법이라고 주장하지 않는다.

같은 고정 Actor·행동·실제 240Hz 표본으로 6초 대조를 수행했다. 360개 제어 단계와 1,440개 물리 표본에서 기존/새 보상을 나란히 계산했으며, 잘못된 준비 구간 비용 0.6869가 제거됐다. 기존 오른손 거리 보상 +0.669738은 0으로 바뀌고, 새 progress 합은 -0.139929였다. 성공·매칭·clean 유지·미압현 판정은 같았다. 이는 보상 회계 수정의 적용 검증이며 학습 효과의 인과 비교가 아니다.

[대조 원자료와 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/reward_probe_v1/result.json) · [독립 대조 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/reward_probe_audit_v1.json)

## 실제 추가 학습

설정은 2환경, rollout 256단계, 24업데이트, seed7이다. 최대 1시간 예산에서 **3,186.18초, 약 53.1분**으로 완료됐다. sampled / logged / durable / committed 전이는 모두 **12,288개**, discarded / unresolved는 0이었다. 물리 실패와 정리 오류도 0이었다. 각 worker는 시뮬레이터를 한 번 만들고 episode 경계에서만 reset했다. persistent 감사도 통과했다.

기존 전곡 모델의 전체 500입력 Actor 두 개와 표준편차만 이전했다. 새 보상에 맞춰 Critic·Adam·업데이트 수를 초기화했으며 이전 8업데이트를 새 counter에 상속하지 않았다. 최종 checkpoint의 신규 업데이트는 24, Actor/Value Adam step은 각각 96이다. 양 Actor의 가중치는 실제로 변경됐지만 최대 변화량은 약 2.63e-5 / 3.13e-5로 작았고 latent 표준편차는 약 0.02로 유지됐다.

상태 500, 미래 4초의 이벤트 입력, 행동 39, 원곡의 67개 음, 음악 시계, 학습률, 기존 비용·안전 종료·gain은 유지했다. 새 보상 metadata와 초기화 방식은 모델 계약에 명시했다. 이전 보상 모델의 strict resume 계약은 완화하지 않았다.

| 전곡 반복 | worker0 압현 / 타현 / 협응 | worker1 압현 / 타현 / 협응 | 각 실행의 분모 |
|---|---|---|---:|
| 1 | 1 / 0 / 0 | 1 / 1 / 0 | 67 |
| 2 | 1 / 0 / 0 | 1 / 1 / 0 | 67 |
| 3 | 1 / 2 / 0 | 1 / 1 / 0 | 67 |

총 402개 목표에서 압현 6회·타현 5회·협응 0회다. 모든 압현은 첫 음이었다. 타현 4회는 14번 음에서 약 107~149ms 늦었고, 나머지 한 번은 23번 음에서 약 89.28ms 빨랐다. 해당 음의 올바른 압현이 없어 원래 음악 판정은 모두 0이다. 전곡 6개와 별도로 마지막 부분 episode 2개가 있으며, 이를 전곡 성과 분모에 넣지 않았다. 이 기록은 학습 중 정책이 바뀌는 episode이므로 위 최종 고정 평가와 구분한다.

훈련 여섯 실행의 240Hz 전체 기록에서 주요 지지·오른허벅지·양발 접촉 부재시간은 0이었다. 기타 최대 이동은 약 11.55mm, 회전은 약 1.54°였다. PPO KL은 0.00130~0.01523으로 목표 0.02 이내였으며 재시도·거부·비유한값은 없었다. 최소 가용 RAM은 약 23.93GiB였다. 가중 비용 advantage의 표준편차는 보상 advantage의 약 0.7~20.8%였으므로, 현재 기록에서 안정성 비용이 학습을 압도한다고 단정할 근거는 없다. 이 비율은 분산 규모의 진단이며 gradient 크기나 인과 기여도를 뜻하지 않는다.

[학습 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_settings_v1.json) · [학습 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1/song_report.json) · [실시간 로그 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1.log) · [최종 모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1/final.pt) · [체크포인트 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/checkpoint_audit_v1.json)

## 현재 판단과 다음 우선순위

실제 보상 결함은 있었지만 **보상 문제만으로 전곡 학습의 부진을 설명하기 어렵다.** 미래 목표는 존재하며 시간에 따라 다음 프렛·손가락으로 교체된다. 첫 목표가 입력에 고정되는 버그는 발견되지 않았다. 반면 기존 단음 성공은 7프렛·2번 현·약지 중심이고, 전곡은 4~12프렛·1~4번 현·네 손가락을 사용한다.

행동은 reset 자세 주변의 절대 관절 목표이며 누적 이동 명령이 아니다. 왼팔 ±0.35rad, 왼손 ±0.5rad 등의 설정 범위가 원래 관절 제한으로 다시 잘리고, 일부 축의 여유는 작다. 탐색도 작다. 이것만으로 특정 목표가 물리적으로 불가능하다고 단정할 수는 없지만, 현재 범위의 목표별 도달성을 확인하지 않은 채 전곡 PPO만 길게 돌리는 것은 우선순위가 낮다.

다음은 실제 목표 조합의 안정적 도달·해제 가능성을 검사하고, 여러 단음의 성공 동작을 확보한 뒤 **첫 7프렛 약지→5프렛 검지의 두 음 전환**부터 학습하는 것이 우선이다. 이어서 짧은 구절, 양손 결합, 전곡 순으로 확장한다. 범위나 탐색 폭을 늘리는 것은 안전성과 필요성을 확인한 새 버전에서 비교해야 한다. 이번 실행 도중에는 범위·속도·노이즈를 바꾸지 않았다.

[목표 입력 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/GOAL_INPUT_AUDIT.md) · [행동 범위·탐색 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/ACTION_AUTHORITY_AUDIT.md)

## 검증과 자료 보존

신규 CPU 검사 34개가 한 process에서 모두 통과했다. 초기 테스트 fixture의 모듈 복원 실패 기록도 cpu_tests_v1.log에 보존했으며, 수정 후 통과 기록은 cpu_tests_v2.log다. 독립 에이전트가 코드, 실제 보상 대조, 여섯 훈련 episode, 전후 고정 평가의 연속 표본과 입력 SHA를 검수했다.

CPU만 보이는 sandbox에서 전체 checkpoint resume는 저장된 CUDA RNG와 장치 수가 달라 정상적으로 거절됐다. 별도 CPU 모델·Adam 복원은 정확히 통과했고, GPU가 보이는 실제 최종 native 평가에서는 계약과 RNG 검사를 포함한 PPOTrainer.load가 통과했다. 이 차이는 checkpoint_audit_v1.json에 구분해 기록했다.

기존 자료를 포함한 14개 입력 manifest와 snapshot의 실제 SHA를 재확인했으며 변경은 없었다. 신규 소스·검사 19개는 source_snapshot_v1/source_pins_v1로 봉인했다. Root 고정·하체 유한 제어·105입력/97비영범위/8원래영범위 구분, 자유 기타·중력 ON·스트랩 OFF, 기존 관절 제한과 gain을 보존했다. 기타 고정·직접 보조 힘·매 step 상태 덮어쓰기를 사용하지 않았다.

이번 안전 완주는 기존 안전 기준 안의 결과다. 자유 Root의 균형·보행, 재접촉 후 왼손 하중 비의존성, 실제 현 압력·진동·음향, 다른 곡의 일반화는 이번 실험에서 입증하지 않았다. 고정 평가는 전후 각각 한 번이므로 통계적 재현성이나 보상 변경만의 인과 효과를 주장하지 않는다. 기존 모델 평가는 학습과 병렬로 진행했으므로 두 평가의 wall time 차이도 처리속도 개선으로 해석하지 않는다.

[CPU 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/cpu_tests_v2.log) · [소스 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/source_pins_v1.json) · [전체 보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/preservation_audit_v1.json) · [persistent 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1/persistent_audit.json)
