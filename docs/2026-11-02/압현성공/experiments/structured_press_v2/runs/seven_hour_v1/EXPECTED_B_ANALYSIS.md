# B16 요청각 기댓값 배포 진단

집계: 2026-10-31T00:35:00.647580+00:00

저장 BASE B16의 aligned 초기 후보·reset4242·팔 press 지원/clamp·물리·분포·가중치를 유지하고 실행 요청만 비교한다. B clamp 제거 실험이나 free33 평가와 합산하지 않는다. 새 학습/목표 일반화 검사가 아니다.

| 자료 | 상태 | 안전성공/분모 | safe clean초 | wrong초 | missing초 | raw reward | raw cost |
|---|---|---:|---:|---:|---:|---:|---:|
| index_B0 | completed | 32/32 | 2.433854166666667 | 0.0 | 0.06406249999999991 | 0.08916158461943269 | 0.0 |
| index_B100 | completed | 32/32 | 1.888671875 | 0.0 | 0.5955729166666667 | -0.12259163241833448 | 0.0 |
| pinky_B0 | completed | 30/32 | 2.34375 | 0.15625 | 0.0 | -0.08673115161946043 | 0.0 |
| pinky_B100 | completed | 21/32 | 1.640625 | 0.859375 | 0.0 | -0.5451032233831938 | 0.0 |
| pinky_B100_latent_mean | completed | 21/32 | 1.640625 | 0.859375 | 0.0 | -0.5451032233831938 | 0.0 |
| index_B0_requested_angle_mean | completed | 32/32 | 2.438541666666667 | 0.0 | 0.0593749999999999 | 0.10135699319653213 | 0.0 |
| index_B100_requested_angle_mean | completed | 32/32 | 1.8876302083333332 | 0.0 | 0.598828125 | -0.12557602231390774 | 0.0 |
| pinky_B0_requested_angle_mean | completed | 30/32 | 2.34375 | 0.15625 | 0.0 | -0.09694995760219172 | 0.0 |
| pinky_B100_requested_angle_mean | completed | 21/32 | 1.640625 | 0.859375 | 0.0 | -0.5571031974395737 | 0.0 |

## 실제source/39codec/qhold 대응

`{"pinky_B100_latent_mean": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "index_B0_requested_angle_mean": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "index_B100_requested_angle_mean": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "pinky_B0_requested_angle_mean": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "pinky_B100_requested_angle_mean": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}}`

## 소지B100 latent 재현

`{"verified": true, "mismatched_fields": [], "scope": "원시32episode 성과/9항/cost/clean/wrong/missing exact; 전체각/실행action journal 동등성 아님"}`

## 완료 gate

`{"ready": true, "reasons": []}`

## 진단 결과

`{"index_B0_requested_angle_mean": {"requested_minus_latent_success": 0, "requested_minus_latent_safe_clean_s": 0.004687500000000178, "requested_minus_latent_cost": 0.0}, "index_B100_requested_angle_mean": {"requested_minus_latent_success": 0, "requested_minus_latent_safe_clean_s": -0.0010416666666668295, "requested_minus_latent_cost": 0.0}, "pinky_B0_requested_angle_mean": {"requested_minus_latent_success": 0, "requested_minus_latent_safe_clean_s": 0.0, "requested_minus_latent_cost": 0.0}, "pinky_B100_requested_angle_mean": {"requested_minus_latent_success": 0, "requested_minus_latent_safe_clean_s": 0.0, "requested_minus_latent_cost": 0.0}}`

보상9항과 비용은 실패 포함 원시 최초32 episode의 비할인 평균이다. 저장된 PPO gamma를 JSON에 기록하지만 per-step trace가 없어 할인 보상을 계산했다고 주장하지 않는다. latent baseline 재현은 기록된 성과/보상/비용/clean·wrong·missing 범위의 exact 비교이며 전체각 journal 동등성은 아니다. q105/hold105의 실제32행 대응은 body/root 전체 물리 상태 동등성을 보장하지 않는다.

요청각 기댓값은 **유지한 B 지원 clamp·평활화·속도제한 이전**의 요청에 적용된다. 최종 supported target이나 실제 물리 응답의 기댓값이 아니다. 결과가 달라도 비대칭 decoder를 모든 실패의 단독 원인으로 확정하지 않는다. inactive23/active16의 실제act 검증과 유한 latent/logp·source 모델0update provenance가 있어야 판단한다. 기존 최고 모델과 생산 코드는 자동 교체하지 않는다. source SHA·9항·cost·실제실패·원시분모·gammas는 JSON에 있다.
