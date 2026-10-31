# 팔 출력의 초기 정렬 bias 제거 비교

집계 시각: 2026-10-30T22:29:29.364305+00:00

기존 full33 fresh seed7과 팔 support_head.bias[:12]만 0으로 초기화한 변형을 비교한다. 관측의 목표·기하 안내와 기존 초기 자세는 유지된다. 따라서 안내가 전혀 없는 학습이 아니다. 학습은 64환경/H32/100회 블록, 고정 평균 정책 평가는 최초32개 episode이며 실패도 분모에 포함한다.

| 조건 | 완료 상태 | 평가 분모 | 안전 성공 | clean 평균(초) | 최장 연속 평균(초) | 보상 | 비용 |
|---|---|---:|---:|---:|---:|---:|---:|
| control_initial | completed | 32 | 0 | 0.0 | 0.0 | -1.8428568169474602 | 0.0 |
| control_100 | completed | 32 | 32 | 2.5 | 2.5 | -0.06676367518957704 | 0.0 |
| control_200 | completed | 32 | 0 | 0.0 | 0.0 | -1.5318922623991966 | 0.0 |
| no_prior_initial | completed | 32 | 0 | 0.0 | 0.0 | -0.24777938798069954 | 0.0 |
| no_prior_100 | completed | 32 | 0 | 0.0 | 0.0 | -0.06936625926755369 | 0.0 |
| no_prior_200 | completed | 32 | 0 | 0.0 | 0.0 | -0.08858186611905694 | 0.0 |

## 증거 통과 조건

초기 직접 텐서/RNG 검증: `{"status": "verified", "checks": {"model_exact_except_zeroed_arm_bias": true, "cpu_rng_equal": true, "cuda_rng_equal": true, "numpy_rng_equal": true, "python_rng_equal": true, "original_bias_nonzero": true, "variant_bias_zero": true}, "native_initial_prior_audit": {"control_initial_checkpoint": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/index_full33_seed7_v1/100/train/J/initial.pt", "control_initial_sha256": "1bdbf4fa92fbd1075044c5c837aa7a3843ac3c76f909caaa7d985d27fff9818c", "model_exact_except_zeroed_arm_bias": true, "cpu_rng_equal": true, "cuda_rng_equal": true}, "native_audit_verified": true, "original_bias12": [0.41654425859451294, 7.247732639312744, -0.050358206033706665, 0.07141205668449402, 0.25507375597953796, 0.0683407336473465, -0.028311602771282196, -0.08823056519031525, 0.013276801444590092, -0.01592191681265831, -0.11327975988388062, 0.1734926402568817], "variant_bias12": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "changed_model_tensors": ["core.support_head.bias"]}`

strict resume 검증: `{"control": {"status": "verified", "checks": {"identity": true, "model": true, "actor_optimizer": true, "value_optimizer": true, "updates": true, "cost_weight": true, "torch_rng": true, "cuda_rng": true, "numpy_rng": true, "python_rng": true, "curriculum": true, "sampler": true}, "source_updates": 100, "target_updates": 100, "scope": "model/Adam/RNG/identity/curriculum/sampler exact; fresh episode resets are separate"}, "no_prior": {"status": "verified", "checks": {"identity": true, "model": true, "actor_optimizer": true, "value_optimizer": true, "updates": true, "cost_weight": true, "torch_rng": true, "cuda_rng": true, "numpy_rng": true, "python_rng": true, "curriculum": true, "sampler": true}, "source_updates": 100, "target_updates": 100, "scope": "model/Adam/RNG/identity/curriculum/sampler exact; fresh episode resets are separate"}}`

동일 명령·설정은 실제 초기 q/hold가 짝지어 같다는 증거가 아니다. 기본 native 평가에 실제 reset 기록이 없으면 paired 비교라고 부르지 않는다. 100회와 200회는 서로 다른 체크포인트 평가이며 100회 최고 성과와 200회 마지막 성과를 별도로 보존한다.

## 각 보상·비용·오압현

- control_initial: 보상9항 `{"song_left_approach": -1.7223479002714157, "song_left_contact": 0.0, "song_clean_hold": 0.0, "song_left_success": 0.0, "song_wrong_press": -0.12661336711607873, "song_performance_deficit": -0.0999999875202775, "song_finger_standby": 0.10269990796223283, "song_thumb_support": 0.003409422301047016, "action_change": -4.562566573440563e-06}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 2.1102213541666663, "missing": 0.3897786458333336, "own_wrong_string_time": 0.0, "own_wrong_fret_time": 0.0, "other_higher_time": 2.110416666666667, "geometry_time": 2.5, "loaded_target_time": 0.04531249999999984, "body_load_time": 0.04531249999999984, "facing_time": 2.5, "contact_time": 0.0}`
- control_100: 보상9항 `{"song_left_approach": -1.6733088307082653, "song_left_contact": 0.25, "song_clean_hold": 0.9999992251396179, "song_left_success": 0.25, "song_wrong_press": 0.0, "song_performance_deficit": 0.0, "song_finger_standby": 0.10255582351237535, "song_thumb_support": 0.003993956110207364, "action_change": -4.6678255785082e-06}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 0.0, "missing": 0.0, "own_wrong_string_time": 0.0, "own_wrong_fret_time": 0.0, "other_higher_time": 0.0, "geometry_time": 2.5, "loaded_target_time": 2.5, "body_load_time": 2.5, "facing_time": 2.5, "contact_time": 2.5}`
- control_200: 보상9항 `{"song_left_approach": -1.3891024105250835, "song_left_contact": 0.0, "song_clean_hold": 0.0, "song_left_success": 0.0, "song_wrong_press": -0.15000012516975403, "song_performance_deficit": -0.10000000149011612, "song_finger_standby": 0.10274234903044999, "song_thumb_support": 0.004472743356018327, "action_change": -4.660436843550997e-06}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 2.5, "missing": 0.0, "own_wrong_string_time": 2.5, "own_wrong_fret_time": 0.0, "other_higher_time": 0.0, "geometry_time": 0.0, "loaded_target_time": 0.0, "body_load_time": 2.5, "facing_time": 0.0, "contact_time": 0.0}`
- no_prior_initial: 보상9항 `{"song_left_approach": -0.27125793509185314, "song_left_contact": 0.0, "song_clean_hold": 0.0, "song_left_success": 0.0, "song_wrong_press": 0.0, "song_performance_deficit": -0.09999980032444, "song_finger_standby": 0.10269971191883087, "song_thumb_support": 0.020779053447768092, "action_change": 0.0}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 0.0, "missing": 2.5, "own_wrong_string_time": 0.0, "own_wrong_fret_time": 0.0, "other_higher_time": 0.0, "geometry_time": 0.0, "loaded_target_time": 0.0, "body_load_time": 0.0, "facing_time": 0.0, "contact_time": 0.0}`
- no_prior_100: 보상9항 `{"song_left_approach": -0.12813046481460333, "song_left_contact": 0.0, "song_clean_hold": 0.0, "song_left_success": 0.0, "song_wrong_press": 0.0, "song_performance_deficit": -0.09999980032444, "song_finger_standby": 0.10284166247583926, "song_thumb_support": 0.05592239915858954, "action_change": -7.738630292131177e-10}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 0.0, "missing": 2.5, "own_wrong_string_time": 0.0, "own_wrong_fret_time": 0.0, "other_higher_time": 0.0, "geometry_time": 0.0, "loaded_target_time": 0.0, "body_load_time": 0.0, "facing_time": 0.0, "contact_time": 0.0}`
- no_prior_200: 보상9항 `{"song_left_approach": -0.1467662206850946, "song_left_contact": 0.0, "song_clean_hold": 0.0, "song_left_success": 0.0, "song_wrong_press": 0.0, "song_performance_deficit": -0.09999980032444, "song_finger_standby": 0.10310638090595603, "song_thumb_support": 0.055077911471016705, "action_change": -1.0305269526611482e-08}`; 비용 `{"termination_base": 0.0, "termination_remaining_time": 0.0, "termination_remaining_negative_note_budget": 0.0, "running_physics": 0.0}`; raw note 초 `{"wrong": 0.0, "missing": 2.5, "own_wrong_string_time": 0.0, "own_wrong_fret_time": 0.0, "other_higher_time": 0.0, "geometry_time": 0.0, "loaded_target_time": 0.0, "body_load_time": 0.0, "facing_time": 0.0, "contact_time": 0.0}`

학습 중 집계는 변화하는 확률 정책의 완료 episode이며 고정32환경 평가와 합산하지 않는다. 전체 집계·LR·원시 SHA는 JSON에 저장한다.

판단 가능: True

대기: 없음

완료: 수치 비교 가능. 단일 seed·reset 비대응 비교이므로 인과·일반화 판단은 제한한다.
