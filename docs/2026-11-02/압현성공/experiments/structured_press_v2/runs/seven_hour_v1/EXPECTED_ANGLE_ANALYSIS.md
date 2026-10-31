# 요청각 기댓값 배포 규칙 분석

집계: 2026-10-31T00:30:02.859339+00:00

같은 저장 Gaussian의 원래 latent 평균 실행, E[tanh Z] 실행, piecewise 요청각 E[θ(Z)]의 역변환 실행을 비교한다. 이는 새 학습이나 물리 응답의 기댓값이 아니라 **평활화·속도 제한 전 요청의 배포 규칙 진단**이다.

| 자료 | 상태 | 안전성공/분모 | 평균 safe clean초 | 최장연속clean초 | 할인reward(.99) | 할인cost(1) |
|---|---|---:|---:|---:|---:|---:|
| full100_mean | completed | 32/32 | 2.5 | 2.5 | 0.17979536906997678 | 0.0 |
| full100_stochastic | completed | 7/32 | 2.405598958333333 | 0.8341145833333333 | 0.1552965698341615 | 0.0 |
| full200_mean | completed | 0/32 | 0.0 | 0.0 | 0.015306220815731176 | 0.0 |
| full200_stochastic | completed | 31/32 | 2.4919270833333336 | 2.140755208333333 | 0.17668517614534618 | 0.0 |
| index_A100_free_mean | completed | 32/32 | 2.496484375 | 2.496484375 | 0.17937277616595235 | 0.0 |
| index_A100_free_stochastic | completed | 2/32 | 0.6460937499999999 | 0.3494791666666667 | 0.0909684676495699 | 0.0 |
| full200_latent_mean | completed | 0/32 | 0.0 | 0.0 | 0.015306220815731176 | 0.0 |
| full200_normalized_action_mean | completed | 0/32 | 0.0 | 0.0 | 0.015304604808184637 | 0.0 |
| full200_requested_angle_mean | completed | 32/32 | 2.5 | 2.5 | 0.18002765299210605 | 0.0 |
| full100_normalized_action_mean | completed | 32/32 | 2.5 | 2.5 | 0.17979486311999066 | 0.0 |
| full100_requested_angle_mean | completed | 32/32 | 2.5 | 2.5 | 0.17995874961220426 | 0.0 |
| index_A100_free_normalized_action_mean | completed | 32/32 | 2.4958333333333336 | 2.4958333333333336 | 0.17930380312275326 | 0.0 |
| index_A100_free_requested_angle_mean | completed | 32/32 | 2.4983072916666664 | 2.4983072916666664 | 0.1797882309642128 | 0.0 |

실제32환경 q105/hold105와 source checkpoint SHA가 같아야 비교한다. 실패 포함 최초32 episode의9항과 할인 보상/비용을 원시 trace·episode 합에 대조했다. q/hold 대응은 body/root 전체 물리 상태의 exact 대응을 증명하지 않는다.

## 검증 상태

`{"ready": true, "reasons": []}`

full200 latent_mean 기준 재현: `{"verified": true, "mismatched_fields": [], "scope": "기록된32episode 성과·9항·할인reward/cost exact equality; 전체각/실행action journal 동등성 아님"}`

## 실제 관측에서 요청각 차이

| 자료 | 그룹 | 평균절댓값차이(deg) | 최대절댓값차이(deg) | 축×환경 표본수 |
|---|---|---:|---:|---:|
| full200_latent_mean | goal4 | 0.0 | 0.0 | 49152 |
| full200_latent_mean | arm12 | 0.0 | 0.0 | 147456 |
| full200_latent_mean | other17 | 0.0 | 0.0 | 208896 |
| full200_normalized_action_mean | goal4 | 0.04645287158899029 | 0.13515264090120255 | 49152 |
| full200_normalized_action_mean | arm12 | 0.005570451710344312 | 0.016335934262198572 | 147456 |
| full200_normalized_action_mean | other17 | 0.0021895497596092937 | 0.01254258822697302 | 208896 |
| full200_requested_angle_mean | goal4 | 1.0447174653030393 | 3.0576252186249304 | 49152 |
| full200_requested_angle_mean | arm12 | 0.026319758346240948 | 0.3777632797607456 | 147456 |
| full200_requested_angle_mean | other17 | 0.3580594454804299 | 1.0210180321327849 | 208896 |
| full100_normalized_action_mean | goal4 | 0.03676154461940344 | 0.10724743552380821 | 49152 |
| full100_normalized_action_mean | arm12 | 0.00508362180498672 | 0.016006633765437345 | 147456 |
| full100_normalized_action_mean | other17 | 0.0010869765963806715 | 0.007021146161125703 | 208896 |
| full100_requested_angle_mean | goal4 | 1.1064872107491546 | 3.168678895666254 | 49152 |
| full100_requested_angle_mean | arm12 | 0.025303027690121358 | 0.3598714864762856 | 147456 |
| full100_requested_angle_mean | other17 | 0.4759389110272746 | 1.3709006577951972 | 208896 |
| index_A100_free_normalized_action_mean | goal4 | 0.12095806264419155 | 0.2981510761865218 | 49152 |
| index_A100_free_normalized_action_mean | arm12 | 0.003998710613761978 | 0.011585580362912505 | 147456 |
| index_A100_free_normalized_action_mean | other17 | 0.0 | 0.0 | 208896 |
| index_A100_free_requested_angle_mean | goal4 | 0.9612192124874244 | 3.2778950870557138 | 49152 |
| index_A100_free_requested_angle_mean | arm12 | 0.012922057238214447 | 0.07477123216520551 | 147456 |
| index_A100_free_requested_angle_mean | other17 | 0.6202887775641636 | 1.3880672445817377 | 208896 |

요청각 차이는 원래 latent-mean 요청각을 기준으로 한다. 실제 몸/관절 이동 차이가 아니다. 영향 통계는 평가 중 모든 batch act 관측을 집계하므로 일부 환경이 첫 episode를 마친 뒤의 act도 포함할 수 있다. 최초32 episode 성과 분모와 별개다. 실제 μ/σ minmax,3개 축 그룹과 분모,39축 실제 span·catalog 출처는 JSON에 기록한다.

## 해석

`{"deployment_rule_contrasts": {"full100": {"angle_minus_normalized_success": 0, "angle_minus_normalized_safe_clean_s": 0.0, "angle_minus_normalized_discounted_reward": 0.00016388649221360518, "angle_minus_normalized_cost": 0.0}, "full200": {"angle_minus_normalized_success": 32, "angle_minus_normalized_safe_clean_s": 2.5, "angle_minus_normalized_discounted_reward": 0.16472304818392142, "angle_minus_normalized_cost": 0.0}, "index_A100_free": {"angle_minus_normalized_success": 0, "angle_minus_normalized_safe_clean_s": 0.0024739583333328596, "angle_minus_normalized_discounted_reward": 0.00048442784145952267, "angle_minus_normalized_cost": 0.0}}, "limitation": "같은 checkpoint·실제 q/hold·물리·분포에서 요청 변환 규칙을 바꾼 실행 차이; 물리 기댓값/단독 실패 원인/새 학습 성공 아님"}`

E[tanh Z]와 E[θ(Z)]의 차이는 비대칭 span을 포함하는 요청각 평균을 실제로 실행했을 때의 결과를 분리한다. 이 비교만으로 전체 실패의 단독 원인이나 접촉·평활화·rate 제한의 독립 기여를 확정하지 않는다. 포화 시에는 active action을 ±(1−dtype eps)로 제한하고 latent를 계산한 뒤 반환action=tanh(latent)로 맞춘다. 보정량은 JSON의 finite_latent_adjustment에 기록한다. inactive6축은 원본 pin helper의 보존 로직과 CPU bitwise 검사 근거이며 전체 실행각 journal을 새로 감사한 주장은 아니다. latent_mean 기준 재현도 현재 기록된 episode 성과/9항/할인값 exact equality 범위에 한정한다. 단일 목표/명목 초기 자세의 반복이며 일반화 검증이나 생산 자동 채택이 아니다.

GH64는 analytic E|Z| 보정으로 절댓값 kink를 분리했다. CPU에서 검증한 σ≈.049787/.15, μ∈[−8,8]의64↔128 오차와 MC 검증은 helper 검사 근거다. 실제 관측 범위를 JSON에 남기며 그 밖의 범위를 검증한 것으로 확대하지 않는다.

## 다른 기존 A200 모델의 별도 진단

이 추가6조건은 기존 핵심7조건 gate와 분리한다. 중지·약지·소지 각각의 별도 A200 모델을0학습 free-v9로 내보내 새 latent baseline과 요청각 기댓값을 비교한다. 과거 free probe32/32와 새 baseline의 q/hold가 직접 같다고 주장하지 않는다. 새 pair 자체의 source SHA·q/hold·39codec를 검증한다. 이는 새 학습이나 한 정책의 새 목표 일반화 검증이 아니다.

| 손가락 | 실행 | 상태 | 안전성공/분모 | 평균safe clean초 | 할인reward | cost |
|---|---|---|---:|---:|---:|---:|
| middle | latent_mean | completed | 32/32 | 2.5 | 0.18045834834911081 | 0.0 |
| middle | requested_angle_mean | completed | 32/32 | 2.5 | 0.18062638996256591 | 0.0 |
| ring | latent_mean | completed | 32/32 | 2.5 | 0.18019629633385448 | 0.0 |
| ring | requested_angle_mean | completed | 32/32 | 2.5 | 0.1803499813124053 | 0.0 |
| pinky | latent_mean | completed | 32/32 | 2.5 | 0.18059233810589653 | 0.0 |
| pinky | requested_angle_mean | completed | 32/32 | 2.5 | 0.18094186963697909 | 0.0 |

추가 진단 gate: `{"ready": true, "reasons": []}`

추가3pair 비교 완료; 제한된 기존 A200 모델의 진단이며 일반 무손상 보장/자동 채택은 아님

기존 핵심 결론의 준비 여부는 main gate로 판단하고, 손가락 전반의 무손상 적용 판단은 추가3pair가 완료되기 전에는 보류한다. 세 pair가 완료되어도 제한된 기존 저장 모델의 진단이며 일반적인 무손상 보장은 아니다.
