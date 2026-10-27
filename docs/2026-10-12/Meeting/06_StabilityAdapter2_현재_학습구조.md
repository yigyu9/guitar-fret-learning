# StabilityAdapter 2의 현재 네트워크·입력·출력·보상

2026-10-12 작성. 현재 코드와 완료된 실행 검증 기록을 기준으로 교수님께 설명할 자료다. 기존 상세 설계안과 실제 실행 중인 실험용 pilot을 구분한다. 이 문서 작성은 학습·환경·보상 설정을 변경하지 않는다.

## 교수님께 설명할 핵심

고정 기타에서 학습한 Fret와 Strike 정책은 동결해 연주 기준 관절 목표를 만든다. 새 StabilityAdapter 2는 자유 기타와 상체의 실제 상태 및 음악 목표를 관측하고, 상체 81관절의 제한된 보정을 학습한다. 기준 목표와 보정을 하나의 최종 PD 목표로 합쳐 기타의 허용 범위 유지와 정확한 압현·타현을 함께 달성하려는 구조다.

현재 구현은 **825D 관측 → 512 → 256 → 81D 보정 Actor**, 별도의 **825 → 512 → 256 → 1 Critic**, **PPO**다. root와 하체는 고정하고 Torso부터 손가락까지 제어한다. 몸통과 머리의 보정 폭은 작고 Thorax부터 손가락까지는 더 큰 폭을 허용한다. 기타는 자유 물리이며 스트랩은 수동 케이블로 작용한다.

![현재 구현된 StabilityAdapter 2 구조](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/image/08_learning/I2001__stability_adapter_2_current_network.png)

## 1. 현재 구조와 과거 제안의 구분

| 구분 | 의미 |
|---|---|
| 과거 왼손 33관절·256→256 | 초기 설계 제안. 현재 학습 사양이 아님 |
| 전체 상체 v2·관측 D 미정 | 상체81와512→256을 결정한 설계 단계 |
| 739D 관측·production gate | 물리548와음악191을 정의한 초기 계약. 상세 보상 gate는 별도로 닫혀 있음 |
| 실제 pilot825 | 739D + 기준 관절 목표81 + 스트랩 상태5. 등록 기준선과 제한된 잔차 PPO를 실행 |
| 최신 초기 자세 노이즈판 | 같은825D·81D 구조에서 검증된 기타·양팔 초기 자세 묶음5개를 선택 |

이 문서의 보상표는 실제 pilot 코드다. UPPER_BODY_REWARD_DESIGN_V4.md의 완성형 Fret/Strike ledger·시선·해제·지속 유지 예산을 모두 구현했다고 설명하지 않는다.

## 2. 학습하는 네트워크

| 구성 | 현재 사양 |
|---|---|
| Actor |825 → Linear512 → ELU → Linear256 → ELU → latent 평균81 |
| 분포 |관절별 diagonal Normal, 학습 가능한 log_std81, a=tanh(u) |
| Critic |825 → Linear512 → ELU → Linear256 → ELU → V1 |
| 구조 |Actor/Critic 별도 가중치. 단일 프레임 MLP이며 GRU/LSTM 없음 |
| 정규화 |관측 RunningMeanStd를 적용하고 현재 guarded PPO에서는 통계를 고정 |
| 학습 행동 |환경별 독립 샘플링. 초기 상태가 같아도 행동 샘플을 한 번만 복사하지 않음 |
| 영상 평가 |평균에 tanh를 적용한 결정론 행동 |
| 파라미터 |Actor 575,057 / Critic 554,497 / log_std81. 합계 1,129,635개. 동결 Fret/Strike와 정규화 buffer 제외 |

새 정책을 처음 만들 때 Actor 마지막 층의 평균을0으로 초기화해 보정0을 기준으로 시작한다. log_std 초기값은 body/head=-5, arm/finger=-4다. 이는 latent 행동 공간의 표준편차이며 관절각 rad가 아니다. 실제 checkpoint를 불러오면 저장된 가중치와 log_std를 사용하므로 이 초기값이 현재 checkpoint 값이라고 단정하지 않는다.

[현재 Actor/Critic](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:50) · [MLP와 관측 정규화](/home/ajou/yigyu/3/tab2body/learning/models.py:204)

## 3. 입력: 825차원의 의미

| 입력 묶음 | 차원 | 내용 |
|---|---:|---|
| 실제 물리 상태 |548|관절·목표·한계, 몸통 변화, 기타 pose/속도/경계 여유, 양손 상대 상태, 시간 |
| 음악 및 검출 상태 |191|현재 목표·음높이·dwell·hit, press cells, 피크 검출 이력 |
| 현재 기준 관절 목표 |81|동결 기준선 목표에 nominal guard를 적용한 상체81 목표 |
| 스트랩 상태 |5|ON/OFF, 현재 경로 길이, 기준 길이, 길이 변화율, 계산 장력/300N |
| 합계 |**825**|현재 상태와 판정에 필요한 이력. 미래 실제 성공 결과는 입력하지 않음 |

### 물리 상태 548D

| 항목 | 차원 |
|---|---:|
| 실제 관절각 q |81|
| 실제 관절속도 qdot |81|
| 직전 최종 제출 목표 |81|
| 유효 목표 하한·상한 |162|
| 몸통9의 초기 기준 대비 실제각 변화 |9|
| 초기 대비 Chest 회전 표현 |6|
| 기타 환경 위치3·회전6·선속도3·각속도3 |15|
| 위치 상자의 여섯 면에 대한 signed 여유 |6|
| 양쪽 손목·손바닥·엄지/손끝·피크15개의 기타 상대 위치 |45|
| 같은15개의 움직이는 기타 좌표계 상대속도 |45|
| 양쪽 손바닥의 기타 상대 회전 |12|
| PREP/PLAY와물리·음악 시간·잔여 시간 |5|
| 합계 |**548**|

손의 상대속도는 기타 병진뿐 아니라 회전 때문에 생기는 속도도 빼서 계산한다. 회전6D는 회전행렬의 두 열벡터 표현으로 Euler 특이점 문제를 줄인다. 입력에 native contact force·압력 센서·손바닥 접촉 mask가 별도 블록으로 포함돼 있다고 설명하지 않는다. press cell 판정과 일반 물리 접촉은 다른 측정이다.

### 음악 및 검출 상태 191D

| 항목 | 차원 |
|---|---:|
| joint_music: 목표프렛6·관측 음높이6·dwell6·인정hit6·event유효/진행/시간/오류4 |28|
| 현별 목표 crossing까지 남은 시간 |6|
| 타현 필수 현 mask |6|
| down/up 방향 |2|
| 현재 이벤트 시작·종료까지 시간 |2|
| 실제 압현 cell: 6현×22프렛 |132|
| 피크 detector의 현별 상태 |6|
| 현별 재무장 진행률 |6|
| 직전 피크의 기타 상대 위치 |3|
| 합계 |**191**|

기타 위치 입력과 위치 비용은 현재까지 기타 actor-root를 기준으로 한다. 최근 별도로 제안한 바디 중심 박스 X[0.11,0.23], Y[0.015,0.105], Z[0.67,0.77]m는 현재 학습에 적용하지 않았다.

[물리548 인코더](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:106) · [음악191 블록](/home/ajou/yigyu/3/stability_adapter_2/joint_learning_observation_v1.py:12) · [기준 목표81 추가](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:226) · [스트랩5 추가](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:225)

## 4. 출력: 상체81의 관절 목표 보정

| 부위 | 차원 | 정책 보정 cap | 목표 변화율 상한 |
|---|---:|---:|---:|
| Torso·Spine·Chest |9|±0.03rad, 약1.72°|0.10rad/s|
| Neck·Head |6|±0.10rad, 약5.73°|0.50rad/s|
| 양측 Thorax·Shoulder·Elbow·Wrist |24|±0.30rad, 약17.19°|1.00rad/s|
| 양손 손가락 |42|±0.20rad, 약11.46°|1.50rad/s|
| 합계 |**81**|각각 현재 q_nominal을 기준으로 한 보정|60Hz 제출 시 적용 |

정책은 위치·토크·기타 pose를 직접 출력하지 않는다. a81은 [-1,1] 정규화 보정이다.

```text
q_requested = clip(q_nominal + cap × a, 유효 관절 한계)
q_final     = 직전 목표에서 부위별 속도 한도만큼 이동한 q_requested
q_final81   → 하나의 POSITION PD 명령
```

몸통 목표의 바깥 한계는 모델 범위와 초기 q_ref±5°의 교집합이다. 실제 몸통각을 강제로 고정하는 조건은 아니다. 목표 rate 제한과 실제 관절속도 제한도 다르다. PD와 중력·접촉 때문에 실제 관절각은 목표와 차이가 날 수 있다.

### 동결 기준선과 제어권

Fret035000은420D→30D, Strike010000은303D→30D를 그대로 추론한다. 준비2초 동안은 preload를 기본 목표로 쓰고, 이후에는 같은 실제 장면과 음악 시계에서 두 정책의 요청을 가져온다. 원본 두 네트워크의 가중치는 갱신하지 않는다. 두 source의 reward 총합을 새 학습 reward에 그대로 더하지도 않는다.

현재 nominal guard는 팔24의 기준 목표를 reset preload±0.15rad, 왼엄지5를 preload±0.10rad로 제한한다. 기존 source 팔 목표가 새 배치와 크게 달라져 작은 residual로 상쇄하기 어려웠던 문제에 대한 진단 조치다. 나머지 손가락의 동결 기준 목표는 유지한다. guard 자체가 실제 손목 위치를 고정하는 것은 아니다.

nominal 제한과 정책 residual은 다른 한도다. 예를 들어 팔은 preload±0.15rad의 nominal에 최대±0.30rad의 보정이 더해져, 모델 한계 이전에는 preload 대비 최대±0.45rad를 요청할 수 있다. 최종 제출은 관절 한계와 rate를 다시 적용한다. 원본 checkpoint의 행동을 완전히 재현하는 구조로 설명하지 않는다.

최종 실제 제출 목표를 source action history에 회신해 두 정책이 자신이 요청한 것과 실제 실행된 것을 구분하도록 한다. source/native 범위 차이에 따른 history 역변환 제한은 로그로 확인해야 한다.

[부위별 보정](/home/ajou/yigyu/3/stability_adapter_2/deadline_bounded_residual_v1.py:5) · [nominal guard](/home/ajou/yigyu/3/stability_adapter_2/deadline_support_nominal_v1.py:5) · [단일 rate 제한](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:86)

## 5. 실제 실행 중인 보상

현재는 기타 안정성 가중치를 강화한 pilot이다. 60Hz에서 연속 항은 초당 계수를1/60로 적분하고, 타현과 이벤트 완료 항은 발생했을 때 한 번 지급한다. 아래 계수는 전체 reward에 최종0.1 배율을 적용하기 전의 원값이다.

Huber 함수는 H(x)=0.5x² (|x|≤1), 그 밖에서는 |x|−0.5다. 위치와 회전은 허용 범위 안이면 비용0이다.

| 항목 | 실제 계산 / 원계수 | 점수를 얻거나 비용이 생기는 조건 |
|---|---|---|
| 기타 위치 이탈 |**−8 ΣH(d_axis/0.05)/초**|actor-root 상자 밖으로 벗어난 축별 거리. 안쪽에서는0 |
| 기타 회전 이탈 |**−4 H(θ_upper/0.15)/초**|허용 회전 집합 밖의 SO(3) 거리 상한 proxy. 안쪽에서는0 |
| 음높이 일치 |**+0.6×match/초**|필요한 현의 실제 sounding fret가 목표와 같은 비율. 최대0.6/초 |
| 왼손 접근 |**+0.15×A/초**|활성 압현 손가락의 source 접근 목표 거리 d에 exp(−d/0.04)를 평균. 최대0.15/초 |
| 피크 접근 |**+0.15×K/초**|현재 구현이 선택한 phase 목표까지 거리 d에 exp(−d/0.04). 최대0.15/초 |
| 실제 몸통각 변화 |**−0.1 mean H(excess/5°)/초**|각 몸통 관절의 초기 대비 변화가±2°를 넘는 부분 |
| 최종 목표 변화 |**−0.01 mean(rate_fraction²)/초**|실제 제출 목표 변화량을 부위별 허용량으로 나눈 값. 급한 목표 변경 억제 |
| 인정된 crossing |**+1/회**|필수 현·방향·순서·영역·타이밍·음높이·dwell 조건을 충족 |
| 잘못된 PLAY crossing |**−0.25/회**|인정되지 않은 crossing. PREP의 crossing은 이 벌점에서 제외 |
| 완료한 joint 이벤트 |**+1/event**|필요한 현 모두 인정됐고 잘못된 crossing이 없는 이벤트 |
| 누락·오류 이벤트 |**−0.5/event**|고정 deadline에서 위 성공 조건을 만족하지 못함 |

기타 위치와 회전 비용만 최초 pilot의4배다. 원래 위치−2/초와회전−1/초에서−8/초와−4/초로 바뀌었다. 음악·몸통·목표변화 계수는 이 강화에서 그대로다.

### 보상 크기를 읽는 예시

- 한 축이 상자 밖으로5cm 벗어나면 위치 원비용은−4/초다. 최종0.1 배율 뒤 학습 보상은−0.4/초다.
- 회전 거리 상한이0.15rad, 약8.59°이면 회전 원비용은−2/초, 학습 보상은−0.2/초다.
- 음높이·양손 접근을 모두 최대치로 유지하면 연속 원보상은+0.9/초, 학습 보상은+0.09/초다.
- 인정 crossing은 최종+0.1/회, joint 이벤트 성공은+0.1/event, 실패는−0.05/event, 잘못된 crossing은−0.025/회다.

### 최대 점수와 하한

100점 만점 구조가 아니다. 이벤트 수와 PLAY 길이에 따라 합계가 달라진다. 현재 Jazz1의42개 single-pick 이벤트, PLAY862/60초에 대해 비용0·모든 음악 및 접근 항이 최대라고 놓은 **항별 상한의 합**은 `0.1×(42+42+0.9×862/60)=9.693`이다. 지표들의 동시 달성 가능성을 보장하거나 곡 간 동일 만점을 정의한 값이 아니다. Critic은 이 scalar의 미래 할인 합계를 예측한다.

정상 transition에서는 `reward = 0.1×max(−8, raw_sum)`으로 하한을 적용한다. 따라서 일반 제어 tick의 학습 보상 하한은−0.8이다. 실제 |qdot|>50rad/s의 유한 속도 안전 종료에서는 현재−8과 남은 horizon의 할인된−8 비용 및 추가−1을 정산한 뒤0.1을 곱한다. 그 terminal 보상은−0.8보다 작아질 수 있다. invalid/nonfinite/API 위반은 정상 비용0으로 처리하지 않고 전이를 중단한다.

### 현재 pilot의 해석 한계

- 시선 보상, 지속 압현·해제 ledger, 접촉력 보상은 현재 pilot 합계에 없다. 목·머리는 행동에 포함돼 있고 작은 보정 cap과 목표 rate 비용을 받지만, 계획한 시선 선호를 이미 받고 있다고 말하면 안 된다.
- 왼손 접근은 hover/source 접근 목표까지의 거리다. 실제 압현 성공을 뜻하지 않으며 press cell과 음높이 일치, joint 이벤트 판정이 별도로 필요하다.
- 현재 `_approach()`는 READY에서entry, APPROACH에서ready, RELEASE_RECOVER에서exit를 선택한다. 원본 motion phase 의도 및 상세 보상 설계와의 정합성은 후속 점검 항목이다. 이번 설명 작업에서 고치지 않았다.
- 회전 비용의 θ_upper는 유효한 허용 자세까지 찾은 거리 상한이며, 인증된 정확한 최단 거리라고 설명하지 않는다. 같은 quaternion의 부호 및 Euler 두 표현과 특이점을 별도로 처리한다.
- joint crossing 판정은 현재240Hz 독립 진단 ledger다. 원본 Strike의 phase/permission 성공 판정과 완전히 동등하다고 인증된 것은 아니다. 원본 source 판정은 별도 로그로 유지한다.

[실제 pilot 계산](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:52) · [안정성4배](/home/ajou/yigyu/3/stability_adapter_2/deadline_stability_reward_v1.py:5) · [현재 하한·배율](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:18) · [접근 목표 구현](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:255) · [joint 판정](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:38)

## 6. 상세 계획서의 보상과 무엇이 다른가

상세 v4는 이벤트마다 정규화한 Fret 음높이 성공·지속 유지·필요 해제·간섭·조기 해제, Strike의 인정hit·gesture 완료·타이밍 품질을 분리하고, 하위 보상이 음악 성공 손실을 덮지 못하도록 예산을 제한하는 설계다. 시선은 매우 작은 보조 예산을 주고, 관통·도달성·실제 접촉도 검증된 신호로 연결하려는 방향이다.

현재 pilot은 시간당 dense 보상과 crossing/event pulse를 사용하는 별도 간소화 구성이다. 상세 설계의 β/event 정규화, press-depth 유효영역 접근, 전체 지속/dropout ledger, tiny gaze 예산을 모두 적용한 학습이라고 발표하면 안 된다. 실제 지지·압현 신호와 phase 정합성을 확인한 뒤 보상 확장 효과를 따로 비교하는 것이 다음 과제다.

[상세 보상 설계 v4](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:1)

## 7. 환경과 학습 실행

| 항목 | 확인된 현재 구조 |
|---|---|
| 물리·제어 |CPU PhysX 240Hz, 관절 목표60Hz, 한 목표당4물리step |
| 제어권 |root·하체 고정, 상체81은정책 보정 가능, 내부 충돌 |
| 기타 |자유 상태. 강제 부착·실행 중 pose 덮어쓰기·기타 pose servo 없음 |
| 스트랩 |현재 검증 pilot은ON. 원본 길이1.1018469719600776m, stiffness6000N/m, damping120N·s/m, max300N, tension-only13점 경로 |
| 준비·음악 |2초 PREP 후 같은score clock으로연주. 새 정책은PREP에도제어하며 음악 dense 항은0 |
| 종료 |현재 곡 전체16.366667물리초 또는유한 관절속도 안전 종료. source done은진단값 |
| 병렬 수집 |독립CPU 환경 여러 개, GPU에서새 정책의 행동을batch 계산 |
| 초기분포 |고정 초기版과검증된자세5개선택版을구분 |
| 영상 |별도graphics0 평가 프로세스, 학습은graphics−1 |

원본 스트랩 법칙에 따른 케이블 힘은 물리 owner에서만 제출한다. 이것은 학습 정책이 기타 pose를 직접 복원하는 힘을 출력하는 것과 다르다.

최신 초기 노이즈판은 world actor-root X/Y ±5mm, Z 0~5mm와 world rotation-vector 각 성분 ±1°에서 제안한 뒤, 양팔 24관절의 초기각을 함께 맞춰 검증했다. 기준 1개와 노이즈 4개를 균일 이산 선택한다. 팔 초기 보정은 기준 ±0.15rad와 모델 한계 안이며 body/head/finger 초기각은 유지한다. 매 reset에 IK를 다시 푸는 것이 아니라 검증된 묶음을 선택한다. 전체 범위의 연속 균일 노이즈라고 설명하지 않는다.

현재 두 대표 noisy 평가도 전체 영상과 정책 실행은 완료했지만 음악 성공은 각각 0/42이며 큰 기타 이탈은 남았다. 초기화·네트워크·실제 CUDA 갱신의 검증과 연주 성공을 구분한다. 이전 Meeting 문서의 초기 노이즈 0 표기는 당시 수집 시점의 기록이다.

[초기 노이즈 구현 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/README.md:1)

## 8. PPO 설정과 학습 보호

| 설정 | 값 |
|---|---:|
| optimizer / learning rate |Adam / 3×10⁻⁵ |
| PPO epochs |4|
| minibatch size |128|
| policy clip / value clip |0.2 / 0.2|
| value loss weight / entropy weight |0.5 / 0.001|
| gradient norm 상한 |1.0|
| 전체 rollout 평균 KL 상한 |0.02|
| γ |2^(−1/600) ≈0.998845, 보상 할인 반감기10초|
| GAE λ |2^(−1/60) ≈0.988514, trace 반감기1초|

minibatch 128과 병렬 환경 수는 다른 설정이다. 일반 병렬 진입점의 기본값은 4환경 × rollout 256step = 1,024 transition이다. 완료된 최근 노이즈 smoke는 4환경 × 64step = 256 transition을 사용했다. 이 문서는 현재 실행 중인 프로세스의 설정이나 진행률을 변경·제어하지 않는다.

갱신 전 rollout 전체의 old Gaussian과 갱신 후 new Gaussian의 KL을 81관절에 합하고 관측 표본에 평균한다. 0.02를 넘거나 비유한 값이면 model과 Adam을 복원하고 학습률을 절반씩 낮춰 최대 8개 후보를 검사한다. 승인할 후보가 없으면 해당 update의 나머지 최적화를 중단한다. 관측 정규화 통계는 고정해 갱신 전후 likelihood를 같은 입력 척도로 비교한다. γ·λ는 초 단위 시간 척도에서 정한 값이다.

[현재 guarded PPO](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py:47) · [PPO 기본 설정](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:13) · [병렬 실행에서lr설정](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_training_v1.py:174)

## 9. 발표에서 사용할 표현

“기존 압현·타현 정책을 동결해 기준 관절 목표로 활용하고, 자유 기타의 실제 상태와 음악 목표를 입력받는 512–256 MLP로 전체 상체 81관절의 보정을 학습하고 있습니다. 작은 몸통·머리 보정과 큰 팔·손 보정을 구분하고, 하나의 PD 목표로 합성합니다. 현재는 기타 안정성 비중을 높인 pilot이며, 네트워크·물리·병렬 갱신은 검증했지만 정확한 양손 연주 성공은 아직 확인하지 못했습니다.”

향후 점검은 왼손 지지와 압현의 양립, 실제 음악 판정과 dense 접근 항의 정합성, 기타 범위 판정의 기준점, 초기 분포 확장 효과 순으로 구분해 진행하는 것이 좋겠다.

[수치·출처 및 그림 검증](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/NETWORK_REPORT_VERIFICATION.json)
