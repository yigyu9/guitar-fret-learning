# 그룹별 고정 표본 실행 진단

원본 full200의 Gaussian·가중치·물리·보상은 유지한다. 매 호출에서 원래 활성33축을 한 번 모두 draw한 후 선택 그룹 외 활성축만 latent mean으로 되돌린다. 출력은39축이고 inactive6은 원본 그대로다. all은 원래 stochastic 정책, 나머지는 hybrid 진단이며 새 학습이 아니다.

## seed7 실행 결과

| seed | 실행 그룹 | 상태 | 안전성공/분모 | safe clean초 | 실패 |
|---|---|---|---:|---:|---:|
| seed7 | all | completed | 31/32 | 2.4919270833333336 | 0 |
| seed7 | goal | completed | 32/32 | 2.495833333333333 | 0 |
| seed7 | arm | completed | 24/32 | 1.830859375 | 0 |
| seed7 | other | completed | 0/32 | 0.0 | 0 |

## seed7 actual_pairing

`{"all": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "goal": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "arm": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "other": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}}`

## seed7 all_baseline_reproduction

`{"verified": true, "exact": {"trace.npz": true, "initial.npz": true}, "scope": "trace8열 전체 및 initial q/hold 행별 exact; 저장되지 않은 전체 관측·몸 root journal까지 동등하다는 주장은 아님"}`

## seed7 gate

`{"ready": true, "reasons": []}`

## seed7 interpretation

`{"all": {"safe_success": 31, "safe_clean_s": 2.4919270833333336, "failure_episodes": 0}, "goal": {"safe_success": 32, "safe_clean_s": 2.495833333333333, "failure_episodes": 0}, "arm": {"safe_success": 24, "safe_clean_s": 1.830859375, "failure_episodes": 0}, "other": {"safe_success": 0, "safe_clean_s": 0.0, "failure_episodes": 0}}`

## seed17 실행 결과

| seed | 실행 그룹 | 상태 | 안전성공/분모 | safe clean초 | 실패 |
|---|---|---|---:|---:|---:|
| seed17 | all | completed | 27/32 | 2.130989583333333 | 0 |
| seed17 | goal | completed | 16/32 | 1.317578125 | 0 |
| seed17 | arm | completed | 10/32 | 0.7977864583333334 | 0 |
| seed17 | other | completed | 0/32 | 0.0 | 0 |

## seed17 actual_pairing

`{"all": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "goal": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "arm": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "other": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}}`

## seed17 all_baseline_reproduction

`{"verified": true, "exact": {"trace.npz": true, "initial.npz": true}, "scope": "trace8열 전체 및 initial q/hold 행별 exact; 저장되지 않은 전체 관측·몸 root journal까지 동등하다는 주장은 아님"}`

## seed17 gate

`{"ready": true, "reasons": []}`

## seed17 interpretation

`{"all": {"safe_success": 27, "safe_clean_s": 2.130989583333333, "failure_episodes": 0}, "goal": {"safe_success": 16, "safe_clean_s": 1.317578125, "failure_episodes": 0}, "arm": {"safe_success": 10, "safe_clean_s": 0.7977864583333334, "failure_episodes": 0}, "other": {"safe_success": 0, "safe_clean_s": 0.0, "failure_episodes": 0}}`

원시 최초32 episode에서 실패를 분모에 포함하며9항 시점별 trace와 gamma0.99/cost gamma1을 검증한다. 실제 q105/hold105가 원본과 대응하고 all의 trace8열이 exact 재현되어야 효과를 해석한다. 전체 몸 root와 모든 관측 journal은 저장되지 않아 동등성을 과장하지 않는다. 같은 단일 검지 목표·한 고정 난수 궤적에서 어느 그룹의 표본 실행이 결과를 바꾸는지 검사하며 독립적인 원인 분해나 새 목표 일반화는 아니다. logp는 선택 latent의 원래 Gaussian 밀도 기록일 뿐 hybrid 분포의 밀도가 아니고 PPO에 사용하지 않는다. 학습·생산 정책을 교체하지 않는다.
