# Frozen checkpoint의 첫 정책 gradient 분해 계획

2026-10-27 설계 문서. **아직 probe를 구현하거나 실행하지 않았다.** 현재 활성 소스는 봉인되어 있으며 이 작업은 이 문서와 [PPO_PATH_AUDIT.md](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/PPO_PATH_AUDIT.md)만 작성한다. 향후 실행도 활성 collector/PPO의 알고리즘을 바꾸는 작업과 구분한다.

## 목적과 해석 범위

동일 short-learning 계약의 frozen checkpoint50/100/300에서 새 on-policy rollout을 수집하고, 실제 active4 likelihood에 대한 **첫 optimizer step 이전의 gradient**를 reward9항·reward-value residual·cost advantage로 정확히 분해한다. reward/value/advantage 배열의 합과 gradient의 합을 production 수식과 검증한다.

이것은 학습 당시 저장되지 않은 물리 상태나 batch를 복원하는 절차가 아니다. **과거 학습 gradient 재현이 아니라 frozen 모델의 새 상태분포에서 국소 방향을 측정하는 진단**이다. raw reward/advantage std나 gradient norm의 비율을 성능의 인과적 기여율로 부르지 않는다. cost0인데 cost GAE가0이 아닌 사실도 회귀 원인이라는 증거로 선해석하지 않는다.

## 1. 원본 로드와 수집

- 각 cp의 SHA·원본 settings/input pins·정책 architecture·PPO config를 기록한다. 원본 `ShortPool`/`ShortPolicy`/`DecisionPPOTrainer`를 구성하고 [strict load](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:255)로 읽는다. 원본 schema/계약/pins 검사를 완화하지 않는다.
- source 검사가 봉인 이후 경로 변경으로 실패하면 원본 manifest에 부합하는 소스를 복원하는 별도 재현 경로가 필요하다. 이 계획은 검사를 건너뛰도록 지시하지 않는다.
- actor와 reward/cost critic 모두 fixed checkpoint 값으로 유지한다. `trainer.update()`/optimizer.step을 호출하지 않는다. GPU 장면은 원본 prepared reset에서 시작한다.
- cp 간 paired 비교는 명시한 같은 진단 seed로 할 수 있다. strict load 후 별도 seed를 설정했다면 그 사실과 RNG를 기록한다. 같은 noise seed도 정책 차이로 생기는 state 궤적 차이를 제거하지 않는다.
- [기존 DecisionCollector](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:10)를 한 번 만들고 H32를7회 연속 수집한다. 224tick으로 첫218tick episode와 다음 episode6tick을 포함한다. collect마다 reset하거나 collector를 다시 만들지 않는다. 실제 조기 실패가 생기면 done/episode ID를 그대로 기록한다.
- **각32×128=4096 batch의 경계와 normalization을 유지한다.** 7개batch를 이어 붙여218/224tick GAE나 하나의 normalization을 계산하지 않는다. 처음6번째 batch의 tick160..191은 onset3초와 end3.1174초 부근을 포함하고7번째는 말미·terminal·reset을 포함한다.

## 2. 소스 변경 없는 reward9 계측 지점

[collect의 transition_callback](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:114)은 pool.step 뒤, reset 전 실행된다. 이 callback에서 `pool.environment._reward_components({})`의9개 최종 tensor를 detach/clone하여 읽는다. [해당 메서드](/home/ajou/yigyu/3/guitar_learning/gpu/simplified_finger_environment.py:227)는 순수 반환이며, [실제 end_control](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1219)이 합산하는 것과 같은 계수다. contact/hold/success의.5나 wrong의.15를 다시 곱하지 않는다. runtime monkeypatch나 활성 소스 편집은 필요 없다.

매tick `sum(reward9)==callback reward`를 검증한다. 이 메서드가 미래 버전에서 순수 함수가 아니게 바뀌면 이 hook도 다시 검토한다. 현재 K1에서는 callback `[tick,env,term]`가 buffer `[decision,env]`와 직접 대응한다. duration1/valid-all/identity 정렬을 확인한 뒤 사용한다.

저장할 배열과 메타데이터:

| 자료 | 형태/내용 |
|---|---|
| 원래 buffer 전체 | state/events/masks, latent39, old logp/mean/std, reward/cost values·next values, reward/cost, duration/valid/terminated/truncated, episode ID·start tick |
| raw reward9 | batch별 `[32,128,9]`; 최종 합산 계수 적용 후 값 |
| raw tick 문맥 | local tick·score time·done·reset·선택 target ID와 source interval |
| advantage 분해 | valid 순서 보존; production reward/cost·combined·normalized, 아래11개 성분 |
| 실행 identity | cp/settings/source/metrics SHA, RNG 및 진단 seed, 원본 PPO config, batch 순서 |
| gradient 결과 | production actor parameter 이름/shape, 전체 및 encoder/head/active std group별 결과, 합 일치 오차 |

K1 검증: valid4096, duration 모두1, reward9 합=buffer reward, old logp=같은 frozen policy 재평가 logp, initial ratio≈1. true terminal의 next values0과 H32 비terminal bootstrap,218tick reset도 원래 buffer에서 확인한다.

## 3. reward GAE의 정확한 가법 분해

[compute_decision_gae](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:9)를 그대로 호출한다. GAE의 duration/valid/terminal/truncation은 같은 buffer를 사용하며 모든 value/advantage는 detach한다. reward gamma=.99, cost gamma=1, lambda=.98을 서로 혼동하지 않는다.

각 최종 보상 성분 `r_i`에 대해:

`A_i = GAE_reward(r_i, value=0, next_value=0)`

원래 reward critic의 residual은 독립적인 한 항이다:

`B_reward = GAE_reward(reward=0, value=V_reward, next_value=V_reward_next)`

GAE는 주어진 masks/duration에 대해 선형이므로:

`A_reward_production = sum_i A_i + B_reward`

**원래 value baseline을 임의로9개의 reward에 분배하지 않는다.** `B_reward`는 critic residual의 GAE 전파분이며 별도 음악 보상 항목이 아니다.

비용은 [production 계산](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:50) 그대로 유지한다:

`A_cost = GAE_cost(cost, V_cost, V_cost_next)`

`C = -cost_weight * A_cost`

따라서11개 성분 `{A_1..A_9, B_reward, C}`의 합은:

`X = A_reward_production - cost_weight*A_cost`

이다. cost0이어도 cost critic이 정확히0이 아니면 `C`는0이 아닐 수 있다. 추가 분해가 필요할 때만 zero-value raw-cost GAE와 cost-value residual로 나누며 최소 결과는 production 비용항 하나를 유지한다.

## 4. normalization 뒤의 정확한 합

[production joint normalization](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:56)과 같이 **batch 전체 valid4096개**에서 계산한다.

`sigma = max(std(X, unbiased=False), 1e-8)`

각 성분 `x_j`에 대해:

`z_j = (x_j - mean(x_j)) / sigma`

그러면 부동소수 오차 범위에서:

`sum_j z_j = (X-mean(X))/sigma = production normalized advantage`

이다. 성분마다 자기 std로 정규화하지 않는다. 성공/실패·음 구간·minibatch별로 다시 정규화하지 않는다. denominator와 성분 평균도 detach한다. 원래 `A_reward`, `A_cost`, `X`, normalized advantage를 production helper로 따로 계산하여 위 합과 비교한다. 계산 결과의 오차 tolerance는 dtype과 합산 순서를 명시하고 raw/normalized/gradient 수준별로 보고한다.

## 5. 첫 optimizer 이전의 gradient

[ShortPolicy의 active mask](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:80)와 [원래 evaluate/logp](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:204)를 그대로 쓴다. 저장된 latent를 고정하고, active4 likelihood를 따로 구현하지 않는다. 동일 frozen policy에서 수집한 batch이므로 최초 ratio는1이고 clipping은 활성화되지 않는다.

각 성분에 대해:

`g_j = grad_theta( -mean(z_j.detach() * logp_theta(stored_latent | stored_inputs)) )`

를 구한다. 이는 ratio1에서 [production clipped surrogate](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:83)의 첫 gradient와 같다. 저장된 latent·advantage를 통해 gradient가 역전파되지 않게 한다. 같은 frozen 상태에서 production의 actual ratio/clipped surrogate로 total gradient도 계산해 `sum(g_j)≈g_total`을 검증한다. ratio≈1 검증이 실패하면 이 선형 score-function 해석을 진행하지 않는다.

parameter 집합은 [actor_parameters()](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:128)와 일치시킨다. 반환된 전체 `finger_log_std`에는 inactive12가 포함되므로 group 보고에서는 active4와 inactive0을 구분한다. group은 shared finger encoder / middle head / active4 std로 나눌 수 있다. 비선택 head·support가 학습 대상이 된 결과는 허용하지 않는다.

현재 minibatch4096은 전체 valid batch4096과 같다. production은2epochs지만 이 계획은 **첫 epoch 첫 gradient**다. 두 번째 epoch는 이미 이동한 parameter, clipping·Adam·global gradient clipping의 비선형 효과를 포함하므로 이 분해를 최종 parameter 변화의 정확한 원인별 분해라고 부르지 않는다. gradient clip/Adam 전 계산하고 optimizer.step은 수행하지 않는다.

## 6. 결과 표현과 판정

- 필수 검증: reward9 합, reward GAE 분해 합, combined advantage 합, normalization 후 합, gradient 합이 각각 production과 일치.
- 보고: batch별·cp별 `||g_j||`, total gradient와의 signed dot product/cosine, group별 방향 및 상쇄. total norm이 거의0이면 cosine 등 불안정한 지표는 계산 불가로 표시.
- 정규화 전 성분 std도 보조 자료로 남길 수 있지만 gradient 영향이나 인과적 성능 기여율을 대신하지 않는다. signed dot/cosine도 이 fixed batch에서의 국소 정렬이다.
- batch별 값을 보존한 채 준비/음/말미·reset 문맥과 함께 읽는다. 7batch 평균을 내더라도 한 번의 학습 update나218tick 재정규화 결과라고 설명하지 않는다.
- 이 진단만으로 자연스러움/음악 성능/자유 기타 이전 성공을 판정하지 않는다. 결과에 따라 새 버전의 별도 대조 실험을 설계한다.

## 검토한 production 및 evidence SHA-256

줄 번호는 아래 읽은 소스 버전에서 확인했다. 기존 metrics는 이번 설계의 동기와 확인 수치에만 사용하며 per-tick reward9나 과거 gradient가 저장되어 있었다고 가정하지 않는다.

| 파일 | SHA-256 |
|---|---|
| [short runtime](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:61) | `74e67024b8962dbf522dacf4f945c14356acdd5ec50770d6eab0d94c6b0dfa34` |
| [short runner](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runner.py:149) | `15973645910d944d7d3c84f941f76816d5a08f93e8b23b84bfa19bd1a2994c25` |
| [simplified environment](/home/ajou/yigyu/3/guitar_learning/gpu/simplified_finger_environment.py:227) | `82a6df2f4777d17146bb954d0ab07c4150e4534004b21a860769a96b8dc86478` |
| [base GPU environment](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1219) | `854796448eb47f3fbb25ff1dfaa5f83c1fee5ff9fec431deef26c0ff8fb503a4` |
| [decision collector](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:114) | `89b4ee9f2e0e8d55328c31b7a739293387d9fc69f8397116d77ca025b9f667d5` |
| [decision PPO](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:9) | `bbcc4b548594494dd777dafe48d4d081e084a02010f938d9256812708fea5951` |
| [PPO common](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:56) | `62a71cec9724225873538f7ae4785f2a97e9eb7a3333adb75fb74989782cafdb` |
| [finger policy](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:204) | `9ff0101f1779b0e5736164358edff235dab286c045b82d75e86bed4b89f4f247` |
| [metrics evidence](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/pilot_incremental_seed7_v2_retry2/train/metrics.jsonl) | `dc8c7bb70cdc610cc6045d6b289fbe7c09e28dfdb68cca96c24626743b0f577e` |
