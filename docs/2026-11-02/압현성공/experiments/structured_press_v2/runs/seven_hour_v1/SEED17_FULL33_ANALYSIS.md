# seed17 전축 fresh 독립 재현

집계: 2026-10-31T00:23:36.671483+00:00

동일 검지 줄3/프렛4·동일 기하에서 seed만 변경한 독립 학습 재현; 새 목표 일반화 아님

A 가중치를 이전하지 않고 원래 Gaussian·large64/H32·100+100을 유지한다. 학습 seed7→17만 변경한다. 평가는 고정reset4242의 실제 q/hold 대응으로 조건을 확인하며 서로 다른 seed의 학습 가중치가 같다고 주장하지 않는다.

| 자료 | 상태 | 안전성공/분모 | 평균safe clean초 | 최장연속clean초 | 할인reward(.99) | 할인cost(1) |
|---|---|---:|---:|---:|---:|---:|
| seed7_reference 100_latent_mean | completed | 32/32 | 2.5 | 2.5 | 0.17979536906997678 | 0.0 |
| seed7_reference 100_requested_angle_mean | completed | 32/32 | 2.5 | 2.5 | 0.17995874961220426 | 0.0 |
| seed7_reference 100_stochastic | completed | 7/32 | 2.405598958333333 | 0.8341145833333333 | 0.1552965698341615 | 0.0 |
| seed7_reference 200_latent_mean | completed | 0/32 | 0.0 | 0.0 | 0.015306220815731176 | 0.0 |
| seed7_reference 200_requested_angle_mean | completed | 32/32 | 2.5 | 2.5 | 0.18002765299210605 | 0.0 |
| seed7_reference 200_stochastic | completed | 31/32 | 2.4919270833333336 | 2.140755208333333 | 0.17668517614534618 | 0.0 |
| seed17 initial_latent_mean | completed | 0/32 | 0.0 | 0.0 | 0.016404252654596933 | 0.0 |
| seed17 100_latent_mean | completed | 32/32 | 2.5 | 2.5 | 0.1801530018126612 | 0.0 |
| seed17 100_requested_angle_mean | completed | 32/32 | 2.5 | 2.5 | 0.18030032655744388 | 0.0 |
| seed17 100_stochastic | completed | 28/32 | 2.474739583333333 | 1.5899739583333332 | 0.17248257464115938 | 0.0 |
| seed17 200_latent_mean | completed | 0/32 | 0.0 | 0.0 | 0.01606122445385434 | 0.0 |
| seed17 200_requested_angle_mean | completed | 0/32 | 0.0 | 0.0 | 0.0161990717425246 | 0.0 |
| seed17 200_stochastic | completed | 27/32 | 2.130989583333333 | 2.097916666666667 | 0.15716756794726927 | 0.0 |

## 학습

| 블록 | 상태 | 완료episode | 안전성공 | 실패 |
|---|---|---:|---:|---:|
| 100 | completed | 512 | 30 | 0 |
| 200 | completed | 512 | 408 | 0 |

## 단일 요인 설정

`{"status": "verified", "blocks": {"100": {"only_seed_changed": true, "from_seed": 7, "to_seed": 17, "no_A_transfer": true}, "200": {"only_seed_changed": true, "from_seed": 7, "to_seed": 17, "no_A_transfer": true}}}`

## 100→200 strict 모델/두Adam/전체RNG

`{"status": "verified", "exact_equal": {"model": true, "actor_optimizer": true, "value_optimizer": true, "updates": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true}, "source_updates": 100, "resume_initial_updates": 100, "source_sha256": "266126e1b4248d97320b2247cbbf5adeab6d2a6d546bd2f7333d54a54f2ad02b", "note": "seed7과 초기 가중치가 같다는 주장이 아님; seed17 안의 strict100→200 복원 검증"}`

## 실제 초기 q105/hold105와 source 대응

`{"100_requested_angle_mean": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "100_stochastic": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "seed7_vs17_100": {"verified": true, "scope": "32행 실제 q105/hold105만 exact; body/root 전체 상태 동등성 아님"}, "200_requested_angle_mean": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "200_stochastic": {"verified": true, "scope": "32환경 q/hold 행별 동일; body/root 전체 초기 상태는 미감사"}, "seed7_vs17_200": {"verified": true, "scope": "32행 실제 q105/hold105만 exact; body/root 전체 상태 동등성 아님"}, "initial_vs100": {"verified": true, "scope": "32행 실제 q105/hold105만 exact; body/root 전체 상태 동등성 아님"}}`

## 완료 gate

`{"ready": true, "reasons": []}`

## 재현 판단

`{"100": {"latent_mean": {"seed7_success": 32, "seed17_success": 32, "seed17_safe_clean_s": 2.5}, "requested_angle_mean": {"seed7_success": 32, "seed17_success": 32, "seed17_safe_clean_s": 2.5}, "stochastic": {"seed7_success": 7, "seed17_success": 28, "seed17_safe_clean_s": 2.474739583333333}}, "200": {"latent_mean": {"seed7_success": 0, "seed17_success": 0, "seed17_safe_clean_s": 0.0}, "requested_angle_mean": {"seed7_success": 32, "seed17_success": 0, "seed17_safe_clean_s": 0.0}, "stochastic": {"seed7_success": 31, "seed17_success": 27, "seed17_safe_clean_s": 2.130989583333333}}}`

같은 checkpoint의 Gaussian과 가중치는 유지하되 요청각 기댓값은 별도의 진단 배포 규칙이다. 원래 latent 평균·확률 실행과 구분한다. 물리 응답의 기댓값이나 새 학습 성공이라고 표현하지 않는다. q/hold 일치는 body/root 전체 초기 상태 대응의 증거가 아니다. 단일 명목 자세의 반복32환경이며 새 곡/목표 일반화가 아니다. 실패 포함 최초32·원시9항·보상γ.99/비용γ1·native lifecycle·source SHA를 검증한 자료만 판단한다. 미실행/미완료 조건을0점 성과로 만들지 않는다. 남은 시간 때문에 실행하지 못한 경우도 pending으로 정직하게 남긴다. 생산 코드와 기존 최고 모델을 자동 교체하지 않는다. 세부 보상/비용·source/model·입력 SHA는 JSON에 있다.
