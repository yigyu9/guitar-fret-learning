# 7. PPO·시간 범위·진단과 검토 쟁점

## v24의 결정 단위 PPO와 진단

명시적 `--learning-family finger-skill-v24`(557상태)는 `DecisionPPOTrainer`를 사용한다. F의 최대3/6tick 유지 옵션에서는 한 번 샘플링한 손가락 행동을 유지하며 support는60Hz 결정론적으로 갱신한다. 할인된 보상 합·`gamma^d` bootstrap·`(gamma*lambda)^d` GAE를 실제 지속 d로 계산한다. 다음 가치는 다음 결정의 계획 길이를 입력받고 padding은 모든 학습·KL·진단에서 제외한다. 관절 상관 탐색은 역기저의 밀도/KL과 실제 관절 latent의 tanh 보정을 사용한다.

원시60Hz 로그와 결정 로그를 따로 저장한다. 새 family의 `mean_reward`/`mean_cost`는 할인된 결정 합의 평균이므로 기본 경로의 raw tick 평균과 직접 비교하지 않는다. 실제 raw 평균은 원시 로그로 계산하고, 반복 횟수 외에 실제 전이·결정 수·최적화량을 함께 보고한다. 고정128개 패드점의 팔/기타 상대 변위와 내부 손가락 변위를 준비·압현·유지·해제·idle로 기록한다. 이 수치를 압현 힘의 인과 기여율로 해석하지 않는다. [v24 검증·한계](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/README.md).

현존 [구동 검증](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/support/final_native_data_verification.json)에서 F 1024환경2회는 원시전이65,536개, 재개1회는32,768개이며 두 실행 모두 종료곡0개다. 상관 탐색·F3 검사는 원시전이32,768개/결정12,389개, 종료곡46개·물리실패3개이며 할인 합과 원시 기록의 오차는 reward 약3.1e−7, cost 약9.2e−7이었다. R/J 단기 검사도 각각8,192전이·종료곡0개다. 이는 데이터·동결·수치 구동 범위이며 전곡 성능이나 장기 수렴 결과가 아니다. [엄격 재개 검증](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_skill_v24/support/final_resume_verification.json)은 같은 단계 모델/optimizer/RNG 복원을 확인하며 물리 상태의 중간 재개를 뜻하지 않는다.

근거: [지속시간 GAE와 PPO](/home/ajou/yigyu/3/guitar_learning/training/ppo.py), [v24 상세](11_v24학습구조와보상.md).

아래 7.1~7.7은 기본 `song`의 전이 단위 PPO이며, 7.8은 최신 v22 결과, 7.9~7.10은 과거 실행이다.

**적용 범위(2026-10-26):** 기본 `--learning-family song`은 보상 v22·552상태·`incremental` 제어다. v23 위치 제어는 [별도 비교 옵션](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_structure_v23/README.md)이며, `--learning-family finger-skill-v24`는 557상태의 별도 R/F/J 경로다.

[전체 목차](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/README.md)

이 장은 확인한 계산 구조와 그 구조에서 따져볼 가설을 나눈다. 현재 v22의 계산 구조·누적600회 결과와 완료된 이전 v17/v16/v8 장기 실행을 구분하고, 특정 보상 항을 원인으로 단정하지 않는다.

## 7.1 reward와 cost를 PPO가 합치는 지점

환경은 매 60Hz 전이에 reward와 cost를 따로 반환한다. 정책에는 reward value와 cost value가 있으며 각각의 미래값을 추정한다.

~~~text
A_reward = GAE(reward, reward_value, reward_gamma=0.99, lambda=0.98)
A_cost   = GAE(cost,   cost_value,   cost_gamma=1.00, lambda=0.98)
N(x) = (x−mean(x)) / max(population_std(x), 1e−8)
A_reward_normalized = N(A_reward)
A_cost_normalized = N(A_cost)
A = A_reward_normalized − cost_weight × A_cost_normalized
A_normalized = N(A)
~~~

현재 GPU 왼손은 advantage_normalization=separate다. 두 advantage를 각각 정규화한 뒤 결합하고 마지막에 다시 정규화한다. critic 학습 target은 이 정규화로 바꾸지 않는다. PPOConfig의 공용 기본값 joint/λ0.95 대신 GPU 왼손 설정에서 separate/λ0.98을 선택한다. 확인한 설정의 cost_weight는 1이고 episode_cost_budget은 null이므로 예산에 따른 자동 계수 갱신은 활성화되어 있지 않다.

reward_components의 합은 환경의 reward와 비교할 수 있다. 그러나 “reward 합−cost 합”을 그대로 PPO actor의 실제 advantage라고 해석할 수는 없다. 할인율·미래값·GAE·정규화가 사이에 있다.

근거: [PPO 설정](/home/ajou/yigyu/3/guitar_learning/training/ppo.py), [GAE와 결합](/home/ajou/yigyu/3/guitar_learning/training/ppo.py), [예산 계수 갱신](/home/ajou/yigyu/3/guitar_learning/training/ppo.py).

## 7.2 시간 범위를 숫자로 읽기

| 값 | 확인한 값 | 뜻 |
| --- | --- | --- |
| 물리 표본 | 240Hz | 기하·접촉·보상 적분·안전 |
| 정책 행동 | 60Hz | 행동 하나당 물리 4표본 |
| GPU rollout H | 32 | 환경당 약 0.5333초 수집 |
| reward gamma | 0.99 / 정책 tick | 1초 뒤 보상 계수 약 0.5472 |
| cost gamma | 1 | cost return의 할인 없음 |
| GAE lambda | 0.98 | advantage의 표본 TD 오차 전파 |
| gamma×lambda | 0.9702 | reward GAE의 carry 감쇠 |
| 전체 곡 | 1969tick | 약 32.8167초 |

reward의 할인 반감기는 약 69tick, 1.15초다. 2초 뒤의 계수는 약 0.2994다. 따라서 원래 보상은 시간적으로 가까운 결과를 더 크게 본다. 곡 전체의 모든 결과가 같은 무게인 무할인 목적은 아니다.

GAE의 reward carry가 절반이 되는 시간은 약 22.9tick, 0.382초다. 이 값은 “정책이 기억할 수 있는 시간”이나 “가치함수가 볼 수 있는 최대 미래”가 아니다. 표본 TD 오차를 가중 합하는 계수의 특성이다.

H32 바깥의 미래는 next value 추정으로 이어진다. H32이기 때문에 0.5333초 뒤 보상이 완전히 사라지는 것은 아니지만, 먼 결과의 학습은 가치 추정의 정확성에 더 의존한다.

## 7.3 H32 경계와 진짜 종료

수집기에서는 종료 관측의 미래값을 평가한 뒤 종료 환경을 reset한다. terminated=True이면 next value 기여를 0으로 한다.

H32의 마지막 전이가 정상 진행 중이면 terminated=False이며 다음 상태 value를 bootstrap한다. 에피소드를 끝내거나 potential을 0으로 바꾸지 않는다. 다음 rollout은 같은 장면·곡 시계·원장으로 이어간다.

다만 GAE를 한 번 계산할 때 표본으로 직접 쓰는 범위는 현재 수집 버퍼 안이다. 수집 길이를 늘리는 효과와 곡을 끊지 않는 효과를 같은 것으로 보지 않는다.

근거: [수집과 reset 순서](/home/ajou/yigyu/3/guitar_learning/training/rollout.py), [GAE](/home/ajou/yigyu/3/guitar_learning/training/ppo.py).

## 7.4 접근 potential의 수학적 주의점

F_t=γΦ_(t+1)−Φ_t이면 할인된 합은 다음과 같이 정리된다.

~~~text
Σ_(t=0..T−1) γ^t F_t = −Φ_0 + γ^T Φ_T
실제 terminal에서 Φ_T=0 → −Φ_0
~~~

그래서 장기 할인 목적에서는 접근 점수의 중간 증감이 상쇄되는 구조다. 가까이 가서 positive shaping을 얻고 종료 전에 멀어지는 방식이 보장된 순이득을 만드는 것은 아니다.

반면 episode reward_components는 보통 할인을 곱하지 않은 실제 수신 reward의 합이다. 그 로그의 song_left_approach가 음수라고 바로 접근 성능이 나쁘다고 판정하면 안 된다. 같은 창에서 정지해도 −0.01Φ가 생기고 창 종료에는 potential이 빠진다. 실제 거리·near_time을 함께 읽어야 한다.

이 수학적 관계가 짧은 PPO 수집·근사 가치함수에서도 동일한 학습 속도를 보장하지는 않는다.

## 7.5 업데이트·탐색 설정에서 보상과 연결되는 부분

확인한 설정은 actor 학습률 3e−5, value 학습률 3e−4, epoch 2, GPU minibatch 4096, clip ratio 0.2, target KL 0.02다. KL 예산을 초과하면 actor와 optimizer를 복원하고 낮은 학습률로 재시도하는 보호가 있다.

초기 latent Gaussian std는 exp(−3)≈0.049787이다. 행동은 latent를 변환한 값이고 실제 관절 변위나 힘의 표준편차가 아니다. 현재 actor loss에는 별도 entropy bonus 계수를 더하는 항이 없다. 정책에서 entropy를 계산한다는 사실과 entropy를 목적함수로 보상한다는 사실은 다르다.

이 값들이 과제에 충분한지는 설정만으로 판단할 수 없다. 현재 문서 작업에서는 H64, std 확대, 학습률 변경 등을 같이 적용하지 않았다.

근거: [actor 목적함수](/home/ajou/yigyu/3/guitar_learning/training/ppo.py), [기본 탐색 설정](/home/ajou/yigyu/3/guitar_learning/training/runner.py).

## 7.6 로그를 읽는 순서

| 단계 | 읽을 기록 | 구분할 것 |
| --- | --- | --- |
| 1 | 완료곡 reason, task_time_s, safety_invalidated | 물리 실패인지 정상 시간축 완료인지 |
| 2 | finger_metrics의 target_count, near/contact/success_fraction | 손가락별 목표 수·접근·접촉·달성 |
| 3 | left_note_ledger | 실패한 특정 음의 거리·노출·하중·wrong 원인 |
| 4 | reward_components | 실제로 어느 항에서 얼마를 받거나 잃었는지 |
| 5 | update reward_component_means, left_curriculum | 전이 평균과 진급 조건의 변화 |
| 6 | PPO diagnostics | reward/cost advantage, KL, value 오차·갱신 |
| 7 | 실제 자세·동작 자료 | 숫자의 측정 정의와 시각적 수행의 일치 |

episode의 component는 실제 적용된 단계 계수 이후 누적값이다. 업데이트 평균은 해당 수집의 합을 H×환경 수로 나눈 **전이당 평균**이다. 곡당 합이나 초당 rate와 직접 크기를 비교하지 않는다.

진행 중인 곡의 전이는 업데이트 평균에 들어갈 수 있지만 아직 완료 episode 행은 없다. H32 평균이 작다는 이유로 그 음의 전체 유지 보상이 없다고 판단하지 않는다. 단계가 곡 중간에 바뀌면 episode에는 여러 단계 계수가 섞일 수 있다.

원장의 surface_min=0은 exposure_time=0일 수 있다. “거리 0 도달”이라고 단정하지 않는다. body_load_time은 선택된 표면 샘플의 몸체 하중 시간이고 실제 해당 현 접촉쌍의 시간은 아니다.

근거: [보상 창 평균](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py), [종료 기록](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py).

## 7.7 구조에서 확인한 사실과 아직 가설인 것

| 논점 | 코드로 확인한 사실 | 아직 검증되지 않은 가설 | 필요한 비교 |
| --- | --- | --- | --- |
| 손목 영역의 영향 | v9는 안0·밖 감점이며 단계0의 하한은 −0.2/s에 점근 | 영역 밖 벌점이 압현 탐색을 과도하게 제한한다 | 영역 초과 거리·벌점·손끝 거리·clean 동시 확인 |
| 충분한 굽힘 | 전체 native 범위·독립 누적제어, LH21 움직임 비용 0 | 비용 제거만으로 자연스러운 분담이 만들어지는가 | 실제 각도·끝관절 편중·압현 성과를 함께 비교 |
| DIP 편중 | 기본coordination0·명시shape는tracking중≤.004/s | 작은분담선호가말단편중을줄이지만압현에간섭할수있다 | A와A+B의실제각도·접촉·달성비교 |
| B대기권고 | 악보 압현 합집합 보호·음 사이 direct/partial/full·추종 1−idle 동기화·기본전체 .02/s | 긴대기복귀가늘거나압현준비가늦어질수있다 | 손가락별시간idle/차단노출·B품질·압현성과 |
| 손가락 성과 편중 | v15감점에도b・wrong/missingD정규화・missed최장부족률적용 | 정규화가손가락별성과유지에영향을준다 | 음별분모/b/deficit・손가락별기여・기존조건대조 |
| 단계 정체 | 모든 등장 손가락의 기준을 요구, 진급만 있고 강등 없음 | 정체가 유지·전환 학습을 실제 지연한다 | 현재 단계·gate 지표·동일 예산 비교 |
| 긴 곡의 credit | H32 bootstrap, reward gamma 0.99 | 현재 시간 범위가 곡 전환에 짧다 | 가치 오차·전환 성과와 H32/H64의 분리 비교 |
| 접근과 접촉 불일치 | v10은 같은 패드/지판면을 쓰지만 positive만 법선·몸체하중을 요구 | 거리 접근만으로 방향·하중을 확보하지 못한다 | 동일 시각 패드거리·cos·signed높이·횡오차·하중·rejected시간 |
| 해제 | 현재 v22 기록은 후보 소멸, 직접 해제 비용 없음 | 이전 위치 잔류가 다음 음을 지연시킨다 | v7 기하 잔류와 다음 음 적시 성과 |

표는 수정 목록이나 실패 원인 순위가 아니다. 이미 구현된 장치가 있으므로 각 장치가 실제로 언제 활성화되고 어떤 규모였는지를 확인한 뒤 작은 비교를 선택해야 한다.

## 7.8 최신 기본 v22: 누적600회 고정 평가

보상 v22/552상태·large·128환경·H32·seed7의 기존100회 모델에서500회 추가해 누적600회를 완료했다. 추가 전이는2,048,000개(누적2,457,600개)다. 소스·보상·제어·초기자세를 바꾸지 않고 모델·두 optimizer·RNG·curriculum을 정확히 복원했다.

동일 곡·동일128환경의 **고정 정책 첫 종료곡 전체**를 비교하며 물리 실패를 제외하지 않는다. 최고 모델을 골라낸 결과가 아니라 한 정책을 이어 학습한 비교다.

| 지표 | 100회 모델 | 600회 모델 |
| --- | ---: | ---: |
| 평균 달성음/67 | 2.015625 | 2.515625 |
| 안전 시간축 완료/128 | 112 | 127 |
| clean/고정 전체 목표 음길이 | 2.873% | 4.681% |
| audible wrong/고정 전체 목표 음길이 | 81.561% | 35.178% |
| audible missing/고정 전체 목표 음길이 | 14.373% | 60.025% |
| 검지 B 계획창 점유 | 22.79% | 25.08% |
| 중지/약지/소지 B 계획창 점유 | 0%/0%/0% | 0%/0%/0% |
| 엄지 후보/고정 전체 곡시간 | 0.002381% | 0.011209% |

오압현 감소와 누락 증가를 함께 읽어야 한다. clean/wrong/missing은 완전한 분할이 아니며 실패 뒤 미관측 꼬리도 고정 분모에 남긴다. 600회 달성 합계는 검지0·중지0·약지322·소지0으로 약지 편중이 유지됐다. 세 손가락의 B 복귀와 엄지 지속 접촉도 미충족이다. 기존 약지 극단 조합 지표가27.86%→0%로 바뀌었어도 다른 한계 근처 관절 목표가 남아 자연스러움 해결로 해석하지 않는다.

학습 말미 최근256종료의 안전94.92%, 손가락 근접2.48/6.97/46.84/0%로 progress0이 유지됐다. 이 창은 변하는 정책의 학습 기록이다. 추가 실행 전체1,027종료곡의 학습 평균3.244/67도 위 고정 모델 평균2.515625/67과 분리한다.

실행 검증은 sampled/logged/durable/committed 모두2,048,000, discarded0, 입력변경0을 확인했다. 실제 최대 적용 후 analytic KL은0.017145, 재시도0회, 최종 actor학습률은7.5e−6이었다. 이 실행의 수치 안정성 확인이며 PPO 설정의 최적성이나 보상 항의 인과효과를 증명하지 않는다. 단일 seed의 연속 학습이므로 일반적 수렴으로 확대하지 않는다.

근거: [누적600회 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/RESULTS.md), [고정 평가·학습 창·PPO 분석](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/learning_analysis.json), [저장·GPU·입력 검증](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_v22_continue_500/verification.json).

## 7.9 이전 v18/v17/v16의 구현·실행 기록

아래는 현재 v22 결과와 구분하는 과거 기록이다. 구동·저장재개나 고정 명령 자세를 장기 학습 효과로 해석하지 않는다.

이전 v18은 B 대기 시간창과 관련 목표 제외를 조정했다. [v18 구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_idle_standby_v1/README.md)의 검증 범위를 따른다. 저장 자세를 같은 조건으로 재계산한 중지의 시간 idle 비율은 26.61%→61.66%, 이벤트를 제외한 시간·기하 gate 허용 비율은 18.44%→51.70%였다. 60Hz 저장 자세 비교이며 실제 240Hz 보상·접촉 이벤트·새 학습 성능을 뜻하지 않는다. 권고 기회 증가가 자세나 압현 개선으로 이어지는지는 새 학습으로 확인해야 한다.

**이전 v17 장기 학습 완료(2026-10-24).** large/1024환경/H32/seed7의 새 2,000업데이트·65,536,000전이와 평가·분석·영상 저장을 완료했다. 고정 1024환경 첫 종료곡의 평균 달성음은 초기 0.2979/67, 평가한 학습모델 중 최고 1,000회 5.9961/67(safe949), 최종 2,000회 5.6045/67(safe887)이다. 연속 clean 달성의 학습 지표이며 현행 v22 성과나 음향 성공률이 아니다. [v17 결과·영상](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/RESULTS.md).

이전v16은large/1024환경/H32/seed7 새2,000업데이트·65,536,000전이와검증·고정평가·로그분석·최고/최종전신·손영상후처리를완료했다. 고정1024환경 첫종료곡평균은초기0.2334/67·평가한학습모델중최고1,500회7.2949/67(safe937)·최종2,000회5.2803/67(safe949)다. 최고선택은평가한500/1000/1500/2000모델의전체1024평균→안전수→최신순이며모든저장본/곡/seed의최고라는뜻이아니다. 학습중달성음과고정정책평가를혼합하지않는다.

학습전fresh12+resume1의정확복원은사전구동검사이며장기성능의분모로합산하지않는다. [v16결과·영상](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_long_training_v16/README.md), [완료상태원문](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_long_training_v16/pipeline_status.json)을따른다. v16은연속clean달성이므로아래누적clean달성의v8과같은성공정의로직접비교하지않는다. 보상항의인과효과·자연스러움·다중seed일반화는별도비교가필요하다.

## 7.10 완료된 과거 v8 장기 실행에서 확인한 점

아래 값은 과거 v8의 누적 clean 달성 기준이다. 현행 v22는 연속 clean 달성이므로 결과를 같은 성공 정의로 해석하거나 현행 v22 성과로 상속하지 않는다.

fresh 2,000업데이트·65,536,000전이를 완료했다. 고정 1,024환경 첫 종료곡 평가의 평균 달성음은 초기 3.8633/67, 평가한 학습 모델 중 최고 1,500회 7.8262, 최종 2,000회 6.7383이다. 안전 완료는 각각 1,023/999/990곡이며 모든 평가에서 전체 67음 성공은 0이다. 1,500회와 최종에서 공통으로 안전한 965환경도 평균 7.9233→6.8187음으로 하락했다.

최고 모델의 안전 완료곡은 약지·소지 달성에 편중됐고 최종 소지 달성은 0이었다. 최종 안전 목표의 87.24%는 목표 geometry에 진입하지 못했다. 접근 부족과 성과 보존 실패를 단순 유지시간 부족으로 축약하지 않는다.

안전 완료곡의 목표 발음 시간 중 wrong 비율은 초기 43.01%, 최고 60.36%, 최종 49.25%다. 분모는 목표별 onset~end 시간 합이며 겹친 음은 따로 센다. 원장의 higher/lower/assignment 시간은 press_s~end_s에서 누적되어 이 비율과 직접 합산할 수 없다. wrong은 하중+기하 proxy이며 음향 오류율이 아니다.

학습 로그에서 actor minibatch 32,000개를 수락하고 1개를 거절했다. update 282의 KL 재시도 후 학습률은 3e−5→7.5e−6으로 낮아졌다. 최종 latent std 평균 0.04951은 초기보다 약 0.55% 낮아, 이 실행의 퇴행을 탐색 분산 붕괴로 설명할 근거는 없다. 개별 advantage 정규화는 확인했지만 항별 gradient 지배나 보상 하나의 인과 효과를 입증하지는 않는다.

[학습 로그 분석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/result_log_analysis.md), [고정 평가와 자세](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/fixed_evaluation_analysis.md), [엄지 및 오압현 후속 분석](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_thumb_wrong_press_analysis/verification.json)을 따른다.


## 7.11 v22 진단에서 함께 볼 항목

- B240Hz 실제 gate와 악보로 고정한 회복창의 B±15도 체류는 별도다. 회복창은 이전 음 끝+1.05초부터 다음 press−.35초까지(초기1.05초, 마지막은곡끝)다. 1초 복귀예산은 잠정 진단값이며 실제 도달시간 보장이 아니다. 완전 관측된 길이≥.5초 창에서 계획시간 대비80% 체류를 평가하고 짧은 창은 전환으로 따로 본다. 정책이 gate를 바꿔 분모를 줄이는 평가는 사용하지 않는다.
- 극단 자세는 MCP/PIP/DIP 조합을 전체·idle·press 노출별로 나눈다. 이전 DIP−PIP 편중 하나만으로 검지/소지 조합을 놓치지 않도록 한다. 진단은 새 벌점이 아니다.
- 진단v5의 엄지240Hz 공유 helper에서 gap·normal cosine·영역 초과거리·유효시간·기하근접·접촉후보/near_unloaded시간·바깥법선하중/유효시간·음수gap/깊은gap·원시잠재보상·실제지급을 기록한다. 기존 thumb2/3 지지정점60Hz 거리와 섞지 않는다. native thumb3 몸체합력은 별도 기록하며 넥접촉쌍·현압력·음향의 증거로 사용하지 않는다.
- 동일 곡·초기화·평가분모에서 clean/wrong·물리실패·기타 이동·손가락 충돌 반응을 함께 비교한다. 엄지 근접이나 기타 안정성 하나만으로 엄지가 지지에 기여했다고 결론내리지 않는다.
