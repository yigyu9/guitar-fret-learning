# 기타 안정성 우선 학습 사전 독립 검수

요약 판정: **문제없음 — 명시한 pilot 범위의 실행 차단 오류 없음.** 이는 새 보상 전체 인증이나 안정화·음악 성공·학습 완료 판정이 아니다. 검수자는 소스를 읽고 기존 CPU 원로그와 초기 이식 기록을 대조했으며, 별도 native 실행·정책 추론·학습을 수행하지 않았다. 검수 중 두 조건의 native 초기 평가가 진행 중이었다.

## Critical

없음.

## 확인한 변경과 계약

- [새 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:7), [보상 함수](/home/ajou/yigyu/3/stability_adapter_2/deadline_stability_reward_v1.py:7): 원본 `pilot_reward`가 만든 ledger의 `position`, `rotation_upper_proxy`만 정확히 4배로 바꾸고 합을 다시 계산한다. 음악·접근·몸통·목표 변화 항은 유지한다. 범위 안 두 비용은 0이고 새 물리 힘을 추가하지 않는다.
- [native v4](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:19): v3 대비 변경은 새 profile/ABI, floor −8, 이전 보상 ABI 생성 및 부모 step 동안 새 보상 함수 적용에 한정된다. 스트랩 경로·힘 guard·초기화·825 관측·81 제어·안전 판정은 그대로다. 부모 raw reward를 한 번 정산하고 최종 scale 0.1을 적용한다.
- [안전 정산](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:31): 남은 tick이 `n`일 때 fatal raw는 `−8 Σ(k=0..n) γ^k −1`이다. 정상 전이가 각 raw ≥−8이면 동일한 남은 horizon의 최악 정상 수익보다 엄격히 작다. 현재 tick을 합의 k=0으로 포함하고 남은 수는 부모 step 뒤 `horizon_ticks−tick`으로 계산한다. γ는 [기존 PPO 설정](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:38)의 60 Hz/10초 반감기와 일치한다. 이는 할인 수익에 대한 하한 부등식이며 가치함수 추정이나 실제 학습 유인의 완전 인증은 아니다.
- [정책 이식](/home/ajou/yigyu/3/stability_adapter_2/deadline_priority_transfer_v1.py:19): mode별 등록 CP SHA, schema·ABI digest·이전 물리/음악/관측/제어 ABI, 소비된 source SHA, PPO 설정·모델 key/shape/유한성, 새 learner/Adam 조건을 검사한 뒤 모델을 변경한다. 기존 Actor·log_std·RMS를 복사하고 `critic.*`는 새 모델의 값을 유지한다. 이전 Adam·갱신 횟수·RNG resume를 이식하지 않는다. `fail-before-mutation`은 learner 변경에 대한 계약이며 runner가 그 전에 만드는 초기 물리 장면까지 없었다는 의미는 아니다.
- [runner](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v5.py:100): Isaac Gym 경로를 Torch 전에 import한다. 새 v4 환경과 transfer helper를 사용하며 평가 subprocess도 v5로 진입한다. CP 자체 SHA는 attempt 입력에 기록하되 학습 ABI의 source SHA에서는 `.pt`를 제외해 자가참조를 피한다. 유효한 이식 뒤 CPU/CUDA RNG를 이식 전 새 실행 상태로 복구한다. 새 보상 CP의 exact load와 이전 정책 transfer는 배타적이다.

## 확인한 증거와 보존 범위

[순수 검사 원로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/pure_tests_v1.log)는 5개 검사 모두 통과했다. [검사 소스](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_stability_priority_v1.py:23)는 두 항의 4배/나머지 동일, 범위 안 0·밖 단조 비용, floor 및 fatal tail, 잘못된 측정/남은 horizon 거절, 이식 후 tensor와 ABI/source/CP 오류 시 learner 불변을 확인한다. 이는 합성 CPU 검사이며 새 보상으로 실제 PPO 갱신·episode reset·영상 완료를 검증한 로그는 아니다.

[ON 초기 이식 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/transfer_policy.json)과 [OFF 초기 이식 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/transfer_policy.json)은 각각 원본92회/23,552전이와127회/32,512전이를 구분한다. 양쪽 실제 t0+합성32관측의 action/latent/log_prob 최대 오차는 모두 0이며 fresh Critic·빈 Adam·새 갱신 카운터0을 기록했다. 이 출력은 helper의 코드와 일치한다.

검수자가 두 등록 원본 CP의 현재 SHA 및 각 이식 기록의 원본 source 971개 SHA를 읽기 전용으로 독립 대조했고 모두 일치했다. [실행 전 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/before_native_verification_v1.json)의 새 소스·계획·launcher SHA도 현재 파일과 전부 같았다. 저장된 원본 중단/보존 경위는 [transition](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/transition_v1.json)에 남아 있다. 전체 과거 결과 및 진행 중 결과의 최종 보존 봉인은 이 사전 검수 범위가 아니다. 검수자는 이 새 보고서만 작성했다.

## Warning

- [보상/정산](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:300): 두 raw component는 4배지만 최종 scalar에는 floor 및 fatal 대체 정산이 있다. 결과 설명에서도 **전체 reward가 4배**라고 쓰지 말고 raw component·floor 조정량·최종 reward를 구분해야 한다. 현재 계획은 이를 구분한다.
- [출발 이력](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:20): ON92와 OFF127은 서로 다른 정책 이력이다. 실제 ON/OFF 차이를 스트랩만의 인과 효과로 해석할 수 없다. 향후 결과에서도 mode별 이전/새 갱신 카운터를 별도로 표시해야 한다.
- [마감/영상](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v5.py:64), [subprocess 제한](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v5.py:125): native 제어와 optimizer 내부는 선점하지 않으며 평가에는 최대600초·TERM/KILL 정리 시간이 있다. 30분 저장은 rollout/갱신 경계에서 수행한다. 11:40 학습 cutoff와 11:59 영상은 설정된 실행 제한으로 설명해야 하며 엄격한 시각 완료 보장은 아니다.

## Suggestion

추가 구조 변경 제안 없음. 후속 검수는 새 보상으로 실제 갱신·안전 종료/reset·입력 불변·영상 길이와 종료 사유를 확인한 완료 결과를 대상으로 한다. 현재의 읽기 전용 사전 검수만으로 안정성 개선, 곡 완주, 음악 성공 또는 production reward 인증을 선언하지 않는다.
