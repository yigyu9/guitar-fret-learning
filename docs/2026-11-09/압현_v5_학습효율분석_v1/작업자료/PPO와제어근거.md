# 압현 v5 C1의 PPO·제어 구조 점검

2026-11-04 작성. 현재 실행 중인 학습의 코드·설정·결과를 변경하지 않고 읽었다. 아래 경로의 동결 사본을 기준으로 한다.

- 실행 루트: `/home/ajou/yigyu/3/docs/2026-11-09/압현_v5_C1_장기학습_v1/작업자료/runtime`
- 실제 설정: 위 루트의 `study_outputs/학습/attempt01/settings.json`
- 학습 지표: 위 루트의 `study_outputs/학습/attempt01/J/learning_metrics.jsonl`
- 환경 계약: 위 루트의 `study_outputs/학습/attempt01/J/training_contract.json`

이 문서의 코드 경로는 모두 이 실행 루트 아래의 상대 경로다. 활성 프로젝트의 다른 버전 코드를 기준으로 결론을 내리지 않았다. GPU 실험·학습·평가는 실행하지 않았다.

## 1. 실제 설정과 자료 사용량

설정 파일에서 확인한 값은 다음과 같다.

| 항목 | 값 |
|---|---:|
| 환경 수 / 수집 길이 | 1024 / H32 |
| 물리 / 제어 주기 | 240Hz / 60Hz |
| 행동 유지 길이 | 1 tick |
| 탐색 | independent |
| actor / value 학습률 | 0.00003 / 0.0003 |
| reward γ / cost γ | 0.99 / 1.0 |
| GAE λ | 0.98 |
| PPO epoch / minibatch | 2 / 4096 |
| clipping / 목표 KL | 0.2 / 0.02 |
| gradient norm 제한 | 0.5 |
| KL 재시도 / 감소 인자 | 3 / 0.25 |
| advantage 정규화 | joint |
| 비용 가중치 | 1.0 |
| episode cost budget / λ 학습률 | null / 0 |
| 초기 latent std | 팔12·엄지5축 0.15, 다른 손가락16축 0.35 |
| 개선 profile | corrected |

공용 `initial_std=exp(-3)=0.049787...`는 이 실행의 실제 역할별 초기 탐색값이 아니다. v5는 정책 생성 시 0.15/0.35를 넣고, 공용 실행기의 후처리 `log(initial_std)+3`를 0으로 유지한다. 학습 중 실제 역할별 std 변화는 별도 체크포인트 검사 없이는 이 설정만으로 단정할 수 없다.

한 업데이트의 결정 수는 `1024×32=32768`이다. `ppo.py:480–531`은 전체 유효 결정을 무작위 순서로 나눠 처리한다. 별도 학습 표본 상한이나 샘플링 생략 경로는 확인하지 못했다. 실제 u82 진단의 actor/critic 각각 16 minibatch, sample_visits=65536은 `32768/4096×2=16`, 결정당 2회 방문과 일치한다. dataclass의 일반 기본값 256을 이 실행에 적용하면 안 된다.

u82의 actor 학습률은 0.00003, KL 재시도 0, 최종 KL 약 0.00620이었다. 따라서 이 시점에는 학습률 감소나 KL 차단 때문에 갱신이 멈췄다는 근거가 없다. 이후 시점에 대한 결론은 아니다.

## 2. 탐색 요청과 실제 목표각 이동은 다르다

확인된 코드:

- `training/policy.py:308–316`: 매 호출마다 독립 Normal latent를 새로 뽑고 tanh로 행동을 만든다. compact 정책은 이 act 구현을 재사용한다.
- `training/rollout.py:215–260`: 60Hz 매 tick act를 호출한다. 모든 유효 결정 duration은 1이다. 오른손 전달 채널 6개는 0으로 고정한다.
- `gpu/control.py:205–212`: 왼손21축은 native 한계 안의 전체 범위를 사용하며 smoothing α=1, 목표각 속도 제한 4rad/s다.
- `gpu/control.py:446–465`: tanh 행동을 준비 기준각 주변의 비대칭 관절 범위로 변환하고, 이전 **목표각**을 기준으로 속도를 제한한다.

손가락 제어의 핵심은 다음과 같다. `q_ref`는 준비 기준각, `a=tanh(z)`이며 실제 범위의 양·음 방향 폭을 따로 사용한다.

```
q_request = q_ref + (a >= 0 ? q_high-q_ref : q_ref-q_low) * a
q_target_next = q_target + clip(q_request-q_target, -4/60, +4/60)
```

한 tick의 목표 이동 한계는 약 0.06667rad=3.82도다. 이 식은 실제 관절이 그 각도만큼 반드시 움직인다는 뜻이 아니다. 물리의 접촉·하중·PD 추종이 추가로 작용한다.

독립 탐색은 매 tick 다른 방향의 요청을 만들 수 있다. 따라서 std를 크게 해도 연속적인 굽힘 탐색이 충분히 커진다고 보장할 수 없다. 현재 정책 평균과 실제 native 움직임의 관계까지 확인한 결론은 아니다.

### CPU 제어식 모사의 재현 조건

실제 학습이나 물리를 실행하지 않고 위 목표각 제한식만 NumPy로 계산했다. 입력 범위는 환경 계약의 `action.target_contract`에서 읽었다.

- NumPy `RandomState(7)` 사용
- N=5000 독립 경로, 각 경로는 검지~소지16축
- dt=1/60초, 120 tick
- `joint_names`에서 `action_order[17:33]`에 해당하는 인덱스를 찾아 `reference105_rad`를 선택
- `action_lower_rad[17:33]`, `action_upper_rad[17:33]` 사용
- 시작 목표각은 reference, 정책 latent 평균은 모든 시각·축에서 0으로 고정
- 초기 latent `z_0 ~ Normal(0,0.35²)`
- 독립 조건: `z_t=ε_t`, `ε_t ~ Normal(0,0.35²)`
- 상관 조건: `z_t=0.9*z_(t-1)+sqrt(1-0.9²)*ε_t`
- 각 조건을 별도의 `RandomState(7)`로 시작하며 같은 모양의 난수를 생성
- 두 조건 모두 `a=tanh(z)`와 위 목표각 요청·속도 제한식을 적용

결과 정의:

- 이동 RMS: 해당 tick에서 `sqrt(mean((q_target-q_ref)²))`, 5000×16개 값의 평균 후 제곱근
- 20도 초과 비율: 해당 tick에서 `abs(q_target-q_ref)>20도`인 경로·축의 비율
- 속도 제한 비율: 모든 120 tick에서 `abs(q_request-q_target_before)>4/60`인 비율의 평균
- 방향 반전 비율: 119개 인접 tick에서 연속 목표 증분의 곱이 음수인 경로·축의 비율 평균

| 제어식 모사 | 독립 ρ=0 | 상관 ρ=0.9 |
|---|---:|---:|
| 0.5초 목표 이동 RMS | 6.205도 | 14.111도 |
| 0.5초 20도 초과 비율 | 0.2475% | 15.4675% |
| 2초 목표 이동 RMS | 6.186도 | 14.143도 |
| 전체 속도 제한 비율 | 78.091% | 56.292% |
| 방향 반전 비율 | 55.036% | 37.477% |

**이는 목표 명령의 기하적 모사이며 native 관절 운동·압현 성공·안정성 검증이 아니다.** 실제 학습은 정책 평균이 0으로 고정되지 않고, 관측과 과거 움직임에 따라 변한다. 상관 조건은 시간적으로 지속된 탐색이 명령 분포를 바꿀 수 있다는 예시다. 해당 AR 필터를 현재 행동에 덧붙이는 것만으로 PPO와 확률 계약이 유지된다고 제안하는 것이 아니다. 상관 탐색을 구현하려면 조건부 확률·logprob·관측 또는 결정 유지 계약을 함께 설계해야 한다.

## 3. H32와 장기 보상 전달

`training/ppo.py:389–419`의 decision GAE 식은 다음과 같다.

```
δ_t = r_t + γ^duration_t * (1-terminated_t) * V(s_next) - V(s_t)
A_t = δ_t + (γλ)^duration_t * (~(terminated_t | truncated_t)) * A_next
```

실제로는 종료 마스크에 논리 연산을 사용한다. truncated는 bootstrap을 허용하되 다음 GAE 연결을 끊는다. 현재 duration=1이므로 매 60Hz tick에 γ와 λ가 각각 적용된다.

| 미래 간격 | reward 할인 γ^(60s) | GAE 전달 계수 (γλ)^(60s) |
|---|---:|---:|
| 0.25초 | 0.86006 | 0.63521 |
| 0.5초 | 0.73970 | 0.40349 |
| 1초 | 0.54716 | 0.16281 |
| 2초 | 0.29938 | 0.026507 |
| 4초 | 0.089629 | 0.00070259 |
| 8초 | 0.0080333 | 0.00000049364 |

계산은 γ=0.99, λ=0.98을 사용했다. 반감기는 `log(.5)/log(base)/60`으로 계산하며 reward 할인은 약 1.14946초, GAE 전달은 약 0.381861초다.

H32는 0.5333초다. 창 밖의 실제 미래 TD residual은 같은 업데이트에서 직접 역전파되지 않고, 마지막 상태의 가치 예측으로 연결된다. **장기 보상을 전혀 고려하지 않는다는 뜻은 아니다.** 충분히 학습된 가치망은 짧은 창에서도 미래 가치를 전달할 수 있다. 다만 가치 예측이 미숙한 초기에는 수초의 준비·유지·전환을 학습하는 데 불리할 가능성이 있다.

정상 종료/물리 실패의 실제 마스크는 환경에서 결정한다. collector 주석만 보고 모든 정상 곡 종료가 truncated라고 해석하면 안 된다.

## 4. 가치망: 정적 연결 오류는 확인되지 않았다

- `training/compact_press.py:104–109`: value optimizer 대상은 독립 value encoder와 reward/cost head 전체다. actor encoder와 공유하지 않는다.
- 같은 파일 `:111–121`: 실제 state와 손가락별 priority goal 8슬롯을 value encoder에 전달한다.
- 같은 파일 `:33–35`: 마스크는 무효 goal 슬롯만 0으로 만든다. state를 마스크로 지우지 않는다. goal 인코딩 후에도 mask를 곱한다.
- `training/compact_press_v5.py:67–78`: actor/value encoder를 별도로 생성한다. actor head만 zero 초기화하며 가치 head는 일반 `nn.Linear` 기본 초기화다.
- `training/ppo.py:519–531`: reward/cost 반환 목표의 MSE를 평균하고 value optimizer로 역전파한다. 공통 value encoder에는 양 가치 손실의 gradient가 들어간다.
- `training/compact_press.py:18–21`: 인코더는 Tanh MLP이며 LayerNorm이나 학습 중 running observation normalization은 없다.
- 관측은 고정 scale로 나누고 ±10으로 clip한다(`gpu/environment.py:1526`, `gpu/compact_press.py:108–136`, `gpu/compact_press_v3.py:131–147`). 고정 scale이 있다는 것과 실제 각 입력의 분산이 균일하다는 것은 다르다.

### CPU gradient 연결 검사

동결 모듈을 sys.path 첫 위치에 두고 실제 `training_contract.json`을 사용해 새 CPU 정책을 생성했다. 기존 checkpoint는 수정·덮어쓰기하지 않았다.

- torch seed7, CPU threads1
- batch8, state=`randn(8,state_dim)*0.1`
- 일반 events는 `(8,0,26)`, mask는 빈 bool
- priority goals=`randn(8,8,26)*0.1`, priority mask는 모두 true
- 손실: `MSE(reward_value, arange(8)/8) + MSE(cost_value, arange(8)/3)`

역전파 결과 value state/goal/fusion 각 4개 parameter tensor 모두, 양 head 각 2개 tensor 모두 nonzero gradient가 있었다. actor encoder는 이 가치 손실에서 gradient가 없었고 이는 독립 구조에 맞는다. value optimizer 대상 총 parameter 수는 453,890이다. 이 검사는 연결이 존재한다는 증거이며 실제 관측에서 activation 포화나 유효 학습이 없다는 것을 배제하지 않는다.

## 5. 초기 로그에 한정한 사실

읽은 시점의 u68~87, 20개 업데이트 중앙값:

| 항목 | reward | cost |
|---|---:|---:|
| 가치망 explained variance | 0.00008091 | -0.00002611 |
| 가치 출력 표준편차 | 0.0009390 | 0.0001795 |
| 가치 목표 표준편차 | 0.24516 | 0.91250 |

동일 20개 업데이트에서 `std(cost_advantage)/std(reward_advantage)` 비율 중앙값은 약 3.72345다. `ppo.py:160–171`의 joint 정규화는 각각을 따로 정규화하지 않고 `A_reward-weight*A_cost`를 만든 뒤 전체를 표준화한다. 이 실행은 weight=1이고 비용 예산 기반 가중치 갱신은 꺼져 있다.

확인되는 것은 가치 출력이 이 초기 구간에서 거의 상수였다는 점과 비용 advantage 변동이 더 컸다는 점이다. 비용이 항상 actor gradient를 지배한다는 결론은 아니다. 행동과의 공분산·보상/비용 advantage 상관·예측 불가능한 탐색 변동을 함께 봐야 한다. 가치 손실의 절대 크기도 reward/cost 목표의 단위와 분산이 달라 그대로 비교할 수 없다. 초기 87회 결과만으로 가치망이 수렴하지 못할 구조라고 단정할 수 없다.

추후 확인할 가설은 실제 입력의 Tanh 포화, 관측 분포의 유사성, 목표·단계별 가치 구분 부족, 높은 탐색 변동에 따른 낮은 예측 가능성이다. 이번 읽기 전용 점검에서는 이를 확정하지 않았다.

## 6. 단계와 학습 일정의 의미

`gpu/finger_skill_environment.py:350–371`은 패드 높이·접선 오차·방향으로 준비 상태를 계산하고, press 직전 0.20초 구간에 quintic 하강 blend를 적용한다. 이것은 공동 33축 정책의 목표 품질이 시간에 따라 바뀌는 구조다. 독립 손목 정책이 완료되면 정렬 정책, 다음으로 압현 정책을 실행하는 세 개의 순차 정책 구조는 아니다.

`training/finger_skill_runner.py:23–51`의 노출 일정은 최초 계획 전이 수의 1/4 이후 전곡으로 전환한다. 실제 계획은 65,536,000전이, 문턱은 16,384,000전이로 H32/1024에서 500업데이트에 해당한다. reset 때 적용되며 성취도에 따른 전환이 아니다. u87까지의 로그는 이 일정상 phrase 단계다. 현재 초기 phrase 결과를 전곡 결과로 보고해서는 안 된다.

## 7. 단독 변경 비교의 우선순위

현재 학습은 유지하고, 종료 후 별도 실험으로 비교할 후보다.

1. **탐색의 지속성**: 주변 std 증가보다 시간적으로 일관된 탐색을 우선 검토한다. 조건부 logprob를 정확히 정의한 상관 탐색 또는 duration-aware 결정 유지 구조가 필요하다. 단순 AR 후처리를 PPO와 동치로 취급하지 않는다. 실제 관절 이동·속도 제한 비율·접촉 성공·안정성을 비교해야 한다.
2. **H32 대 H128**: 총 물리 전이 수·환경 수·초기 std·보상·노출 문턱을 같게 둔다. 예를 들어 H32/2000회와 H128/500회는 총 전이와 총 minibatch 방문 수를 맞출 수 있다. 정책 갱신 빈도 차이는 이 변경에 수반되는 효과로 명시한다. γ/λ는 동시에 바꾸지 않는다.
3. **비용 가중치**: joint advantage 구조를 유지하고 cost_weight 한 항만 낮춰 비교한다. 음 달성만 보지 말고 물리 실패와 유효 episode 분모를 함께 보고한다. actor 행동과 reward/cost advantage의 관계를 확인하기 전 비용 가중치를 원인으로 단정하지 않는다.

H128과 할인율 변경, 탐색 지속성과 std 변경, 비용 가중치와 보상 계수 변경을 한 번에 합치지 않는다. critic gradient·activation·단계별 설명력 진단은 원인 판별 자료이며, 현행 학습의 구조 변경으로 실행하지 않았다.

## 보충: 최초 100회 가치 진단의 집계 확인

이 보충은 u1~100의 완결된 learning_metrics.jsonl 행만 읽었으며 원래 학습·결과는 변경하지 않았다.

`training/ppo.py:450–466`은 입력·latent와 GAE advantage/return을 같은 `valid` 마스크 및 순서로 선택한다. `:519–531`에서 가치망을 갱신한 뒤, `:540–556`은 같은 전체 유효 입력을 4096개씩 **평가용으로만** 나누어 다시 계산·연결한다. 다음 지표는 마지막 minibatch가 아니라 연결된 전체 결과다.

```
error = target.double() - post_update_value.double()
MSE = mean(error²)
EV = 1 - Var(error, unbiased=False) / Var(target, unbiased=False)
```

목표는 수집 당시 가치 예측으로 만든 고정 GAE λ-return이다. 갱신 후 새로 GAE를 계산하지 않는다. 평가 입력은 stochastic rollout에서 모은 관측이며 별도 deterministic 평가의 EV가 아니다. 마지막 minibatch 손실인 최상위 scalar 값과 이 post_update 전수 MSE를 구분해야 한다.

모든 100회에서 유효 결정은 32768개였고 reward/cost 각각 value·target의 count도 모두 32768개였다. 가치 minibatch는 매번 16회, sample_visits는 65536이었다. value nonfinite_steps는 모두 빈 dict다. 패딩이 포함되거나 일부 minibatch만으로 EV를 계산했다는 증거는 없다.

| 중앙값 항목 | u1~20 | u81~100 | u1~100 |
|---|---:|---:|---:|
| reward EV | 0.23849 | 0.00034659 | 0.00026113 |
| cost EV | 0.64686 | 0.0000026019 | -0.000033539 |
| reward 전수 MSE | 0.035056 | 0.063793 | 0.050941 |
| cost 전수 MSE | 4.60279 | 0.62267 | 1.22656 |
| value gradient norm, clipping 전 | 12.7983 | 0.61288 | 1.04770 |

표의 gradient norm은 각 업데이트의 `diagnostics.minibatches.value.sample_weighted_mean.grad_norm_pre_clip`를 먼저 취한 뒤 해당 구간의 중앙값을 계산했다. reward/cost 양 head와 공통 value encoder를 합친 값이므로 각 부분의 gradient 크기를 따로 입증하지는 않는다. 제한값은 0.5이며, 이 통계는 gradient가 0이라 갱신되지 않은 상황과 맞지 않는다. gradient clipping이 자주 작용할 수 있으나 gradient norm만으로 그것이 학습 부진의 원인이라고 단정할 수 없다.

최초 100회 reward EV 범위는 −0.00021081~0.65967, cost EV 범위는 −0.00172296~0.83494였다. 즉 **가치망이 처음부터 한 번도 변별하지 못한 것이 아니라, 초기에는 높은 EV도 있었고 이후 수집분에서 거의 0인 구간이 나타났다.** 시간에 따라 관측·목표·탐색 분포가 함께 달라지므로 이 사실만으로 네트워크 붕괴를 확정하지 않는다. 서로 다른 분산·단위의 reward/cost MSE 감소량도 가치 학습 품질의 직접 비교로 쓰지 않는다.

배제 가능한 범위는 코드상의 단순 마스크/배치 순서 불일치, 마지막 minibatch만을 전체 EV로 잘못 표시한 집계, 가치 optimizer에서 모든 파라미터가 빠진 경우다. 실제 관측 분포에서의 포화·상태 정보 부족·수집된 return의 예측 가능성·공통 가치 인코더에 대한 두 손실의 영향은 여전히 미검증이다.

보충 수치의 직접 출처는 `/home/ajou/yigyu/3/docs/2026-11-09/압현_v5_C1_장기학습_v1/작업자료/runtime/study_outputs/학습/attempt01/J/learning_metrics.jsonl`의 optimizer_updates 1~100이다. 집계 정의의 출처는 같은 동결 루트의 `guitar_learning/training/ppo.py:450–466`, `:519–556`이다. 요약하면 **가치망 연결 오류는 확인되지 않았고, 초반에는 구분 능력이 나타난 뒤 u81~100 구간에서 설명력이 낮아졌으며 원인은 미확정**이다.

수집량을 늘리지 않는 별도 후보로 PPO epoch 2→4 비교를 둘 수 있다. 현재 공통 `config.epochs`는 actor 루프(`ppo.py:482`)와 critic 루프(`:519`) 모두에 적용된다. 공통 값만 바꾸면 actor·critic 갱신이 각각 16→32 minibatch로 함께 늘어나므로 가치망만 개선한 실험으로 해석하면 안 된다. 이 후보는 제안일 뿐 이번 점검에서 실행하지 않았다.
