# 손가락 함수 보존형 팔 세부 학습 분석

집계 시각: 2026-10-30T22:13:15.607152+00:00

같은 A100·factor0.1·seed7·large/64/H32/B100에서 actor의 학습 가능한 가중치 범위만 바꾼다. 손가락 encoder/heads/std와 actor_extra 가중치를 고정하며 팔·지지 actor와 독립 가치망을 학습한다. **관절 각도나 실행 행동을 고정하는 실험이 아니다.** 관측 변화에 따라 손가락 출력은 계속 변할 수 있다.

## 고정 정책 평가

| 조건 | 완료 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| B0 | 32 | 32 | 2.4339 | 0 |
| old_B100 | 32 | 32 | 1.8887 | 0 |
| variance_initial | 32 | 32 | 2.4339 | 0 |
| variance_final | 32 | 32 | 2.3729 | 0 |
| variance_free_v9 | 32 | 32 | 2.4227 | 0 |
| arm_initial | 32 | 32 | 2.4339 | 0 |
| arm_final | 32 | 32 | 2.3132 | 0 |
| arm_free_v9 | 32 | 32 | 2.3578 | 0 |

B0는 추가 학습 전 기준이다. 기존 분석에서 가장 높았던 B0를 계속 보존하며, 학습 후 성과가 다른100회 모델보다 높다는 사실을 B0 개선으로 해석하지 않는다. B와 free-v9는 초기 분포·지원·활성축이 달라 합산하지 않는다.

실제32환경 q/initial_hold 대응: `{"variance_initial": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "variance_final": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "arm_initial": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "arm_final": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}}`

## 실제 체크포인트 증거

`{"status": "verified", "source_sha256": "517dc84dc322af2d76b787f0bba3fcccbda357674e18c185bc964b0f3b6954db", "frozen_tensor_count": 36, "all_frozen_tensors_exact_equal": true, "source_model_exact_except_active_mask": true, "variance_initial_model_exact_equal": true, "variance_initial_cpu_rng_equal": true, "variance_initial_cuda_rng_equal": true, "support_changed_tensor_names": ["core.support_log_std", "core.support_encoder.state.0.weight", "core.support_encoder.state.0.bias", "core.support_encoder.state.2.weight", "core.support_encoder.state.2.bias", "core.support_encoder.event.0.weight", "core.support_encoder.event.0.bias", "core.support_encoder.event.2.weight", "core.support_encoder.event.2.bias", "core.support_encoder.output.0.weight", "core.support_encoder.output.0.bias", "core.support_encoder.output.2.weight", "core.support_encoder.output.2.bias", "core.support_encoder.output.4.weight", "core.support_encoder.output.4.bias", "core.support_head.weight", "core.support_head.bias"], "value_changed_tensor_names": ["core.value_encoder.state.0.weight", "core.value_encoder.state.0.bias", "core.value_encoder.state.2.weight", "core.value_encoder.state.2.bias", "core.value_encoder.event.0.weight", "core.value_encoder.event.0.bias", "core.value_encoder.event.2.weight", "core.value_encoder.event.2.bias", "core.value_encoder.output.0.weight", "core.value_encoder.output.0.bias", "core.value_encoder.output.2.weight", "core.value_encoder.output.2.bias", "core.value_encoder.output.4.weight", "core.value_encoder.output.4.bias", "core.reward_critic.weight", "core.reward_critic.bias", "core.cost_critic.weight", "core.cost_critic.bias", "value_extra.0.weight", "value_extra.0.bias", "value_extra.2.weight", "value_extra.2.bias"], "initial_optimizer_updates": 0, "final_optimizer_updates": 100, "angles_locked": false, "same_observation_function_preservation": "고정된 가중치·정규화이며 실제 관측 변화에 따른 출력 변화는 허용"}`

## 학습 중 확률 정책

| 조건 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| variance | 513 | 335 | 1.6638 | 1 |
| arm | 512 | 334 | 1.6670 | 0 |

학습 집계는 변화하는 확률 정책의 완료 episode만 포함한다. 고정 정책 최초32 episode 평가와 구별하며 미완료 episode를 성공으로 세지 않는다. 같은 학습률 규칙이라도 KL 재시도로 실제 사용 LR은 달라질 수 있다.

| 조건 | 완료 update | 실제 사용 LR 최소/최대 | KL 재시도 합계 |
|---|---:|---:|---:|
| variance | 100 | 7.5e-06 / 9.375000000000001e-06 | 3 |
| arm | 100 | 3e-05 / 3e-05 | 0 |

## 학습 episode별 보상 평균과 비용

| 항목 | 분산0.1 B100 | 손가락 함수 보존 B100 |
|---|---:|---:|
| 목표 패드 접근 | -1.477141 | -1.477748 |
| 최초 접촉 | 0.250000 | 0.249146 |
| 압현 유지 | 0.665565 | 0.666800 |
| 압현 달성 | 0.163255 | 0.163086 |
| 오압현 | -0.042280 | -0.041985 |
| 음 수행 부족 | -0.022030 | -0.023690 |
| 대기 자세 | 0.102638 | 0.102676 |
| 엄지 안내 | 0.003922 | 0.004094 |
| 행동 변화 | -0.000007 | -0.000007 |

variance 세부 비용(물리 실패 포함): `{"termination_base": 0.009746588693957114, "termination_remaining_time": 0.005068225934956274, "termination_remaining_negative_note_budget": 0.00028346330798857395, "running_physics": 0.0}`

arm 세부 비용(물리 실패 포함): `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`

## 판단

`{"better_than_variance_B100": false, "better_than_B0": false, "free_v9_failure_zero": true, "scope": "단일 목표·seed7; B0 최고 기준과 비교하며 생산 자동 반영 없음"}`

대기 입력: 없음

단일 검지·동일 기하·단일 seed의 실험이다. 새 목표 일반화 검증이 아니며 생산 코드는 변경하지 않는다. 원시32환경 분모·9항 보상·비용·실패·초기 가중치/RNG·동결 tensor·LR·입력 SHA는 동명 JSON에 기록한다.
