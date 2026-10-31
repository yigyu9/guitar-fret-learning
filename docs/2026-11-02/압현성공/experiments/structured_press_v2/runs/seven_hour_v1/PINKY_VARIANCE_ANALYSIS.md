# 소지 탐색 분산 비교

집계 시각: 2026-10-30T23:13:22.184598+00:00

목표는 소지·물리 줄3·프렛9이다. 같은 A200에서 B100으로 이전하고 목표 소지4축 sigma만0.1배로 변경한다. 기본 잡음 대조군과 초기 모델·CPU/CUDA RNG·64/H32/100·seed7·물리·보상·학습률 규칙을 확인한다. 실제 사용 LR은 KL 재시도에 따라 달라질 수 있다.

## 고정 정책 최초32환경 평가

| 조건 | 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| control_initial | 32 | 30 | 2.3438 | 0 |
| control_final | 32 | 21 | 1.6406 | 0 |
| control_free_v9 | 32 | 32 | 2.5000 | 0 |
| variant_initial | 32 | 30 | 2.3438 | 0 |
| variant_final | 32 | 30 | 2.3438 | 0 |
| variant_free_v9 | 32 | 32 | 2.5000 | 0 |

B0는 control_initial이다. B0보다 낮으면 다른100회 모델보다 높아도 개선 채택 후보로 올리지 않는다. B와 free-v9는 지원·초기 분포·활성축이 달라 별도로 해석한다. 동일 기하 반복32환경은 새 목표 일반화가 아니다.

## 학습 중 변화하는 확률 정책

| 조건 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| control | 513 | 96 | 2.2235 | 1 |
| variant | 512 | 490 | 2.4123 | 0 |

학습은 확률 표본화와 정책 갱신이 계속되는 완료 episode 집계이고, 평가는 고정 모델의 결정적 최초32 episode이다. 실패 episode를 분모에 포함하며 미완료 episode를 성공으로 세지 않는다. 잠재 Gaussian μ 불변이 tanh 이후 기대 행동 평균 불변을 뜻하지 않는다.

## 완료 episode별 평균 보상과 비용

| 항목 | 기본 잡음 B100 | 소지 sigma0.1 B100 |
|---|---:|---:|
| 목표 패드 접근 | -1.669604 | -1.672668 |
| 최초 접촉 | 0.245695 | 0.244263 |
| 압현 유지 | 0.889402 | 0.964934 |
| 압현 달성 | 0.046784 | 0.239258 |
| 오압현 | -0.003029 | -0.004724 |
| 음 수행 부족 | -0.039811 | -0.003381 |
| 대기 자세 | 0.102001 | 0.102120 |
| 엄지 안내 | 0.007127 | 0.007364 |
| 행동 변화 | -0.000006 | -0.000006 |

control 비용(물리 실패 포함): `{"termination_base": 0.009746588693957114, "termination_remaining_time": 0.0145549058449431, "termination_remaining_negative_note_budget": 0.0004873294346978557, "running_physics": 0.0}`
control 실제 LR 최소/최대 7.5e-06/3e-05; KL 재시도 합계 2.

variant 비용(물리 실패 포함): `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`
variant 실제 LR 최소/최대 7.5e-06/7.5e-06; KL 재시도 합계 3.

## 초기 모델/RNG

`{"status": "verified", "source_sha256": "009d7f0f4a9c3380e1c6d630e4fb444e7d4ee6c9229df7de4789a8f68f4ca2ea", "source_model_exact_except_active_mask": true, "initial_models_exact_equal": true, "cpu_rng_exact_equal": true, "cuda_rng_exact_equal": true}`

## 단일 요인 설정

`{"status": "verified", "matching_settings_keys": ["ppo", "initial_std", "structured_press", "simple_start", "finger_skill", "song", "song_training", "physics_backend"], "factor": 0.1, "selected_axes": [29, 30, 31, 32], "learning_rate_rule_same": true, "realized_learning_rates_may_differ": true}`

## 실제 q/hold 대응

`{"control_final": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "variant_initial": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "variant_final": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}}`

## 완료 증거 gate

`{"ready": true, "reasons": []}`

## 판단

`{"better_than_control_B100": true, "better_than_B0": false, "variant_free_v9_failure_zero": true, "eligible_for_further_experiment": false, "production_unchanged": true, "scope": "단일 소지 목표·seed7이며 formal B 승급 실험 아님"}`

학습 완료·실제 초기 가중치/RNG·설정·모든 평가 raw32·실제 q/hold·native 감사가 모두 검증되기 전에는 효과를 판단하지 않는다. 생산 코드와 기존 최고 체크포인트를 유지한다. 이100회 비교를 formal B 단계 승급으로 취급하지 않는다. 입력 SHA·원시 분모·9보상·비용·실패·LR 세부 내역은 동명 JSON에 저장한다.
