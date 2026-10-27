# ShortPolicy v2 PPO 경로 읽기 검토

검토일: 2026-10-27. 대상은 `03_short_learning/pilot_incremental_seed7_v2_retry2/train`의 incremental·large·128환경·H32·K1·중지4축·seed7·300updates 실행이다. 이 검토는 소스와 기존 JSON/JSONL만 읽었다. GPU나 새 검사를 실행하지 않았고 활성 Python 소스를 변경하지 않았다.

## 결론과 범위

policy → DecisionCollector → DecisionPPOTrainer의 선택4축 likelihood, K1 discount, GAE, terminal bootstrap, H32 연속 수집, partial reset에서 **이번 회귀를 설명하는 확정적 구현 오류는 발견하지 못했다.** 이는 해당 구현의 완전한 정확성이나 수렴 보장이 아니다. 단일 조건부 중지 과제의 성공을 전체 손가락·여러 음·자유 기타 J33 성과로 확대하지 않는다.

중요한 관측은 raw cost가 전부0이어도 learned cost critic의 GAE는0이 아니라는 점이다. 이 값은 실제 joint advantage에서 차감된다. **검증된 추정 오차의 경로이며 회귀의 원인이라는 증명은 아니다.** 보상 크기나 advantage 표준편차를 인과적 기여율로 해석하지 않는다.

## 확인한 실행 경로

1. [ShortPolicy 생성·선택 mask](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:64)는 middle head만 학습하고 action indices `[21,22,23,24]`만 활성화한다. [log probability와 KL](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:179), [sampling](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:191), [evaluation](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:204)은 같은 `_active_mask()`를 쓴다. tanh Jacobian도 활성 latent4에만 적용한다.
2. [ShortPool teacher 혼합](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:160)은 선택4축 정책 행동을 그대로 실행한다. 비선택 관절의 teacher 행동은 likelihood에 포함되지 않는다. 현재 경로에서 저장된 latent/logp와 실제 선택 행동 사이의 불일치를 찾지 못했다.
3. [collector 입력 복제](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:44)는 observation을 detach/clone하고 sampled latent·old logp·mean/std·value를 저장한다. [보상 집계](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:83)는 첫 reward를 duration0의 `gamma**0`으로 더한 뒤 duration을 증가시킨다. K1에서는 각 decision의 reward가 raw 60Hz reward와 같다.
4. [decision GAE](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:29)는 `delta = r + gamma**d * (not terminated) * Vnext - V`, carry 계수는 `(gamma*lambda)**d`다. terminal/truncation에서 carry를 끊고 return은 advantage+value다. 현재 K1에서 통상 1-step GAE와 일치한다.
5. [환경 종료](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1232)는 실제 실패 또는 local duration 완료를 `terminated=True`로 돌려준다. [collector bootstrap](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:93)은 reset 전 최종 observation으로 next value를 계산하고 true terminal은0으로 만든다. H32 경계 자체는 terminal이 아니다.
6. [collector partial reset](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:120)은 done IDs만 reset한다. [GPU pool reset](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py:61), [환경 reset](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:694), [teacher feedback reset](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:116)은 해당 IDs의 scene/controller·clock/ledger·feedback 상태를 초기화한다. `_reset_scope`가 clock reset보다 먼저 호출되지만 이 경로의 scope 지정은 clock에 의존하지 않는다.
7. [valid decision 선택과 advantage 결합](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:48)은 reward/cost GAE를 따로 계산하고 valid rows만 고른다. [joint normalization](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:56)은 전체 valid rollout의 `A_reward - cost_weight*A_cost`를 하나의 평균/std로 표준화한다. minibatch별 재표준화는 하지 않는다.
8. [actor update](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:79)는 stored old logp와 재평가 logp의 ratio, PPO clipped surrogate, gradient clipping, Adam, full-rollout analytic KL guard를 쓴다. [critic update](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:112)는 별도 optimizer다. actor와 value encoder는 서로 다르다.

## 선택4축 누적 목표각이 관측되는지

**선택 관절의 controller 누적 target은 actual q와 별개로 관측에 들어간다.** [controller.targets](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:399)는 incremental action에서 `target_old + action*(4/60)`을 만든 뒤 bounds/rate/native limits를 적용하고 controller target을 저장한다. [scene.step](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:396)은 이 target을 scene target으로 복사하고 [snapshot](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:350)이 해당 target과 실제 q를 함께 반환한다.

[관측 구성](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1350)은 `q_offset=q-reference`, `target_error=target-q`, 실제 qd, previous_action을 포함한다. [고정 scale/clipping](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1380)은 scale로 나눈 뒤[-10,10]으로 제한한다. 현재 봉인 training_contract에서 중지4축의 q_offset/target_error/previous_action scale은 모두1, q_velocity scale은10이다. clipping이 활성화되지 않은 관측에서는 `q_offset + target_error = target-reference`이므로 고정 reference를 더하면 누적 target 자체를 복원할 수 있다. actual q가 하중 때문에 target을 따라가지 못해도 target_error가 그 차이를 노출한다. 범위 밖 큰 실제 q의 observation clipping 여부는 별도로 확인해야 하며 모든 물리 상태에서 무조건 exact하다고 주장하지 않는다.

중지의 전체561상태 zero-based indices는 q_offset60..63, q_velocity165..168, target_error270..273, previous_action336..339다. [finger-local20](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:60)은 자기 q_offset4+q_velocity4+target_error4+posture sin/cos6+valid/standby_gate2다. previous_action은 local20 직접 입력에는 없지만, [shared finger encoder](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:165)가 전체561상태를 읽고 그 context를 middle head에 제공하므로 접근 가능하다. [previous_action 갱신](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1198)은 실제 실행 action을 쓰며 reset에서0으로 초기화되고 H32에서는 유지된다. 선택4축은 teacher가 바꾸지 않으므로 이 이전 action도 해당 정책 행동이다.

따라서 **“incremental 누적 target이 숨겨져 있어 actual q만 보고 제어한다”는 설명은 현재 코드와 맞지 않는다.** 누적 제어 기억에 필요한 선택4축 target 정보가 존재한다는 범위의 결론이다. 전체 물리/접촉/원장/teacher 내부 상태까지561상태가 완전한 Markov state인지의 증명이나, 숨은 상태가 회귀 원인이라는 주장은 아니다.

## cost0과 cost advantage의 구분

설정은 reward gamma=.99, cost gamma=1, lambda=.98, cost_weight=1, joint advantage, actor_lr=3e-5, value_lr=3e-4, epochs2, minibatch4096, target_KL=.02다. 현재 raw cost가0이라도 `delta_cost = Vcost_next - Vcost`와 terminal의 `-Vcost`는 learned critic이 정확히0이 아니면0이 아니다. [shared value encoder와 두 critic](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:116)은 cost value를0으로 강제하지 않는다.

기존 metrics의 실제 표준편차:

| update | reward advantage std | cost advantage std | combined std |
|---:|---:|---:|---:|
| 100 | .0820095 | .0581924 | .139148 |
| 250 | .00356133 | .00110011 | .00312255 |
| 300 | .00627331 | .00145284 | .00761875 |

모든300회 raw mean_failure_cost는0이다. 따라서 “cost0이므로 actor의 비용 신호도0”이라고 설명하면 틀린다. 다만 이 수치의 크기만으로 cost critic이 회귀를 일으켰다고 결론 내릴 수 없다. 활성4축 score-function gradient와의 정렬을 별도로 측정해야 한다. 설계는 [GRADIENT_PROBE_PLAN.md](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/GRADIENT_PROBE_PLAN.md)에 있다.

## 짧은 음·H32와 기존 수치의 한계

선택 원곡 note의 local press=2.9787초, onset=3초, end=3.1174초이고 audible duration은117.4ms다. episode는218tick=3.633333초다. H32는.533333초이므로 직접 note 보상이 없는 rollout도 많고 그 앞의 준비 행동은 critic bootstrap에 의존한다. `(gamma*lambda)**32=.379805`, 같은 계수의180tick 값은.00431548, `gamma**180=.163808`이다. 이는 credit assignment 조건에 관한 설명이지 발견된 코드 오류가 아니다. 실제 실패가 없는 동일218tick episode들은 시간상 동기화되므로 batch별 준비/연주/말미 비중도 달라진다.

300개 metrics 모두 valid decisions4096, physical transitions4096, duration min/mean/max1이다. latent Gaussian entropy의 전체 범위는 약−1.38527..−1.38340, accepted analytic_KL 최대.0104091, KL retry 총1회, 최대 attempted_KL .0251778, post-update ratio nonfinite0이다. 이 기록에는 std 붕괴·지속적 KL 거부·비유한값으로 회귀를 설명할 근거가 없다. 작은 update의 누적으로 mean이 이동할 가능성까지 배제하지는 않는다.

기존 CPU 테스트는 선택 mask/logp/gradient, 짧은 collector+PPO update에서 frozen parameter 유지, fake pool의 reset/bootstrap을 다룬다. 실제218tick native episode·H32 반복·3초 뒤117.4ms note의 장기 학습 회귀를 검증한 것은 아니다. 이번 읽기 검토에서 새 테스트는 실행하지 않았다.

## 읽은 증거의 SHA-256

아래 파일들은 이 문서 작성 직전 읽은 버전이다. 다른 작업자가 소유한 문서/산출물은 수정하지 않았다. 링크의 줄 번호는 이 소스 버전에서 확인했다.

| 파일 | SHA-256 |
|---|---|
| [short runtime](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runtime.py:61) | `74e67024b8962dbf522dacf4f945c14356acdd5ec50770d6eab0d94c6b0dfa34` |
| [short runner](/home/ajou/yigyu/3/guitar_learning/tool/experiments/short_finger_learning/runner.py:149) | `15973645910d944d7d3c84f941f76816d5a08f93e8b23b84bfa19bd1a2994c25` |
| [simplified environment](/home/ajou/yigyu/3/guitar_learning/gpu/simplified_finger_environment.py:227) | `82a6df2f4777d17146bb954d0ab07c4150e4534004b21a860769a96b8dc86478` |
| [base GPU environment](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1167) | `854796448eb47f3fbb25ff1dfaa5f83c1fee5ff9fec431deef26c0ff8fb503a4` |
| [decision collector](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py:10) | `89b4ee9f2e0e8d55328c31b7a739293387d9fc69f8397116d77ca025b9f667d5` |
| [decision PPO](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py:41) | `bbcc4b548594494dd777dafe48d4d081e084a02010f938d9256812708fea5951` |
| [PPO common](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:56) | `62a71cec9724225873538f7ae4785f2a97e9eb7a3333adb75fb74989782cafdb` |
| [finger policy](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py:179) | `9ff0101f1779b0e5736164358edff235dab286c045b82d75e86bed4b89f4f247` |
| [GPU pool](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py:61) | `675fa199778a9760bd292f3265d57393a3f540748840308d8fa16e0d84bd468d` |
| [GPU controller](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:399) | `9583f01b6badd7eabb6d86c20d1a8949150e4981971dee83498761f3b52734a7` |
| [GPU scene](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:350) | `0e0b2298dccbb38395b3d15c009704ab092fd372b478063e275232c6da061e45` |
| [봉인 training contract](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/pilot_incremental_seed7_v2_retry2/train/training_contract.json) | `56b9e11cc50282e9e1463e80a02b0f3a743273e3e577a496eca8d7b59bf0c4ee` |
| [metrics evidence](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/pilot_incremental_seed7_v2_retry2/train/metrics.jsonl) | `dc8c7bb70cdc610cc6045d6b289fbe7c09e28dfdb68cca96c24626743b0f577e` |
