# 전축 fresh 목표 손가락 분산 비교

집계 시각: 2026-10-30T23:42:41.245153+00:00

동일601열·33활성축·원래v9·검지 줄3/프렛4·seed7에서 처음부터100+100회 학습한다. 변경 요인은 목표4축 sigma0.1배뿐이다. A 가중치 이전이 없고 기존 IK 팔 출력 bias와 초기 물리 자세를 유지한다. 같은 적응 LR 규칙이지만 실제 사용 LR은 KL 재시도에 따라 달라질 수 있다.

## 고정 모델 결정적 최초32환경 평가

| 조건 | 분모 | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| control_100 | 32 | 32 | 2.5000 | 0 |
| control_initial | 32 | 0 | 0.0000 | 0 |
| control_200 | 32 | 0 | 0.0000 | 0 |
| variant_100 | 32 | 0 | 0.0000 | 0 |
| variant_initial | 32 | 0 | 0.0000 | 0 |
| variant_200 | 32 | 14 | 1.0440 | 0 |

## 학습 중 변화하는 확률 정책

| 블록 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |
|---|---:|---:|---:|---:|
| control_100 | 512 | 4 | 1.3626 | 0 |
| control_200 | 513 | 133 | 2.1088 | 1 |
| variant_100 | 512 | 164 | 1.8262 | 0 |
| variant_200 | 512 | 373 | 1.9240 | 0 |

학습 완료 episode와 고정 정책 평가를 구분한다. 실패를 분모에서 빼지 않으며 미완료 episode는 성공이 아니다. 100회와200회 학습 표는 각100회 블록에서 완료된 episode이고,200회 평가는 누적200회 모델이다.

## 학습 블록별9항 보상 평균

| 항목 | 기본100 | 분산0.1 100 | 기본200블록 | 분산0.1 200블록 |
|---|---:|---:|---:|---:|
| 목표 패드 접근 | -1.652306 | -1.641346 | -1.660751 | -1.620977 |
| 최초 접촉 | 0.242513 | 0.231689 | 0.242162 | 0.205282 |
| 압현 유지 | 0.545058 | 0.730491 | 0.843706 | 0.769589 |
| 압현 달성 | 0.001953 | 0.080078 | 0.064815 | 0.182129 |
| 오압현 | -0.009143 | -0.007865 | -0.009386 | -0.031158 |
| 음 수행 부족 | -0.073581 | -0.040996 | -0.033502 | -0.022982 |
| 대기 자세 | 0.102942 | 0.103156 | 0.102937 | 0.103201 |
| 엄지 안내 | 0.003872 | 0.003689 | 0.003907 | 0.003710 |
| 행동 변화 | -0.000021 | -0.000021 | -0.000021 | -0.000021 |

control_100 비용(물리 실패 포함): `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`
control_100 실제 LR 최소/최대 9.375000000000001e-06/3e-05; KL 재시도 2.

control_200 비용(물리 실패 포함): `{"termination_base": 0.009746588693957114, "termination_remaining_time": 0.007927225347150835, "termination_remaining_negative_note_budget": 0.0003347953392980624, "running_physics": 0.0}`
control_200 실제 LR 최소/최대 9.1552734375e-06/1.8310546875e-05; KL 재시도 1.

variant_100 비용(물리 실패 포함): `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`
variant_100 실제 LR 최소/최대 7.5e-06/3e-05; KL 재시도 2.

variant_200 비용(물리 실패 포함): `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`
variant_200 실제 LR 최소/최대 7.5e-06/1.46484375e-05; KL 재시도 1.

## 실제 초기 전체 모델/RNG 및 strict 재개

`{"status": "verified", "initial_control_exact": {"model": true, "torch_rng": true, "cuda_rng": true, "numpy_rng": true, "python_rng": true}, "strict_resume_exact": {"model": true, "torch_rng": true, "cuda_rng": true, "numpy_rng": true, "python_rng": true, "actor_optimizer": true, "value_optimizer": true, "updates": true}, "source_updates": 100, "resume_initial_updates": 100, "no_A_weights_transferred": true}`

## 단일 요인 설정

`{"status": "verified", "blocks": {"100": {"only_sigma_variant_and_fresh_identity_fields_differ": true, "same_initial_pose_physics_rewards_gamma_ppo": true, "goal_axes": [17, 18, 19, 20], "factor": 0.1}, "200": {"only_sigma_variant_and_fresh_identity_fields_differ": true, "same_initial_pose_physics_rewards_gamma_ppo": true, "goal_axes": [17, 18, 19, 20], "factor": 0.1}}}`

## 실제 실행의 native 감사

`{"100": {"source": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/index_full33_seed7_v1/100/train/J/initial.pt", "source_sha256": "1bdbf4fa92fbd1075044c5c837aa7a3843ac3c76f909caaa7d985d27fff9818c", "strict_resume": false, "exact_equal": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true}}, "200": {"source": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runs/100/train/J/final.pt", "source_sha256": "1fb192e9e45987e6851f43160166d86680aa65db0fe2d8791b425ea28b4acbe2", "strict_resume": true, "exact_equal": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true, "actor_optimizer": true, "value_optimizer": true, "updates": true}}}`

## 완료 증거 gate

`{"ready": true, "reasons": []}`

## 판단

`{"100": {"better_deterministic_than_control": false, "variant_failure_zero": true}, "200": {"better_deterministic_than_control": true, "variant_failure_zero": true}}`

## 동일 예산 개선과 기존 최고 보존

분산0.1은200회 동일 예산에서 기존200회 0/32 대비 14/32로 개선되었다. 그러나 기존 full33 최고100회 모델의 32/32·평균 safe clean 2.5000초보다 새200회 모델의 14/32·1.0440초가 낮으므로 대체하지 않는다.

선택 판단: `{"status": "verified", "best_control": "control_100", "best_variant": "variant_200", "better_than_existing_full33_best": false, "replace_existing_best": false, "production_unchanged": true, "reason": "동일 예산 비교와 기존 최고 모델 대체 여부를 구분하며 단일 목표 실험으로 자동 교체하지 않음"}`

B 후보 전용 fixed-reset 보정은 사용하지 않고 원래 full33 공식 평가를 유지한다. 전체 초기 모델/RNG와 동일 초기화 코드·설정의 증거를 기록하며, 환경별 실제 q/hold를 별도 캡처해 정확 비교한 실험으로 표현하지 않는다. 단일 검지 목표·seed7·동일 기하의 비교이고 새 목표 일반화나 과거557열 production 재현이 아니다. 이 full33 실험에서는 원래 full33 최고100회 체크포인트를 보존한다. 별도 절차에서 확보한 A/B0 후보도 함께 보존하며, 서로 다른 절차의 최고 성과를 이번 동일 예산 비교와 혼동하지 않는다. 생산 코드는 자동 변경하지 않는다. 입력 SHA·원시 분모·보상·비용·실패·LR 전체는 동명 JSON에 기록한다.
