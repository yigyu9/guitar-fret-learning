# B 비용 head: 완료된300회 학습의 CPU 감사

평가 파이프라인 완료·성과 수용 판정과 분리한 학습 내부 감사다. 활성 소스·기존 결과·GPU는 변경하지 않았다. 원자료·checkpoint·판정 코드 SHA는 [COST_AUDIT.json](COST_AUDIT.json)에 기록했다.

- `B_zero_cost_head_seed7/train/metrics.jsonl`의 update1~300을 빠짐없이 검사했다. 유효 결정/전이는 **1,228,800개**다.
- 실제 rollout 비용의 저장 평균 `mean_failure_cost`는300/300행 정확0이었다.
- 비용 GAE advantage(`diagnostics.advantages.cost_raw`)의 mean/std/min/max와 비유한 수는300/300행 정확0이었다.
- post-update 비용 critic의 value/target mean/std/min/max·비유한 수·MSE는300/300행 정확0이었다.
- `cost_value_loss`/last, value minibatch의 sample-weighted cost loss와 최대 cost loss도300/300행 정확0이었다.
- 완료된 학습 에피소드 **5,632개**는 모두 `timeline_complete`, 비용0이었다.
- initial.pt(update0)와 final.pt(update300)의 `cost_critic.weight[1,512]`, `cost_critic.bias[1]`는 모든 원소가 유한한 정확0이었다. CPU 로드 후 CUDA 초기화는 false였다.

실제 초기73개 model tensor를 기준선 initial과 재대조했다. cost head2개만0으로 바뀌었고 나머지71개는 정확히 동일했다. 기존 `B_actual_initial_comparability.json`의 B initial SHA도 일치했다. 비용 계수는 모든300회에서1로 유지됐다.

이 실행에서 비용 초기화 개입의 실효성은 확인됐다. 원래 실패 비용을 없애거나 비용 계수를0으로 만든 실험은 아니다. 실패가 없는 이번 학습에서는 비용 advantage와 critic의 가짜 초기 신호가 정확0으로 유지되었다는 범위다. 이후 실제 실패 비용이 발생하는 조건에도 계속0이라는 주장은 하지 않는다.

**로그 이름 주의:** `diagnostics.advantages.cost_raw`는 `decision_ppo.py:50`에서 계산한 비용 advantage이며 실제 순간 비용이 아니다. 순간 비용 min/max·전체 전이 tape는 저장되지 않았다. 따라서 직접 검사한 raw min/max라고 보고하지 않는다. 기존 비용이 비음수라는 계약과 매행 평균0에서 수집 비용 전체0을 추론할 수는 있다.

이 문서는 전체10평가와 launcher 종료를 확인하지 않았다. baseline/A/B의 성과 비교·기존 acceptance 판정은 평가 완료 뒤 별도로 작성한다.
