# 전체 상체 보상 설계 v3.1

이 문서는 상체 전체 81관절 정책의 부위별 목표 범위와 보상 후보를 설명한다. 전체 상체 81 행동과 Actor/Critic 512→256 구조를 유지한다. 이 작업은 수식/계약용 synthetic 검사와 함수 그래프 작성이며 환경 코드 변경 0, 새 물리 실행 0, 학습 실행 0이다.

![보상 함수 프로파일 설계 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.png)

## 그래프가 보여주는 것

그림은 [reward_profiles.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.json)의 표본 배열을 그대로 표시한 설계 함수 그래프다. 세 패널은 y축 범위가 각각 다르며 보상 크기를 서로 직접 비교하는 그래프가 아니다. 시뮬레이션 궤적이나 실제 학습/물리 결과가 아니다.

- **몸통**: `C_joint`만 표시한다. 실제 몸통 9관절 오차가 모두 같은 크기라고 둔 가상 조건이며 `C_chest` 항은 포함하지 않는다. x축은 초기 기준 대비 실제 q 오차다. 녹색 ±2° 구간은 실제 오차 deadband이고, 주황 점선 ±5°는 PD 요청 목표의 초기 범위 후보다. ±5° 경계를 넘어 요청하지 않도록 제한하는 제안이어도 실제 q는 접촉·동역학으로 벗어날 수 있으므로, 그래프의 비용은 실제 오차가 ±5°를 넘어도 계속 계산한다. 이 곡선은 그런 가상 편차를 보여주며 실제 상황을 뜻하지 않는다.
- **머리 시선**: 정렬 오차에 따른 `G`의 가중 보상률이다. 최대 선호는 +0.01/s로 매우 약하다.
- **기타 범위 이탈**: 허용범위 바깥 위치 거리(cm)에 따른 `−2 C_guitar`의 가중률이다. profile은 회전거리를 0으로 둔 위치 항만 포함한다. 허용범위 내부는 0이고, 원점이나 초기 기타 자세로 돌아가는 비용을 그린 것이 아니다. 회전 허용집합 거리 판정은 구현 전이라 그래프에 포함하지 않았다.

## 행동 범위와 탐색 후보

첫 설계는 Torso·Spine·Chest 9, Neck·Head 6, 양쪽 Thorax~Wrist 24, 양손 손가락 42를 포함한 상체 81관절 단일 정책이다. root/하체는 fixed-lower다. 몸통 요청 목표는 native 한계와 유효 초기 기준 `q_ref ±5°`의 교집합 후보이며, 이는 실제각 고정이나 보장 범위가 아니다. 실제 몸통 관절 오차는 ±2° 이내에서 비용 없이 허용하는 후보이고, 실제 Chest의 Pelvis 상대 회전에는 별도 3° deadband가 있다.

Neck/Head와 팔·손가락은 native 목표 범위를 유지한다. 팔·손가락에는 초기각으로 되돌아가는 비용을 주지 않고, 많이 움직이는 것 자체에도 직접 보상을 주지 않는다. 연주 수행과 기타 범위 유지가 필요한 움직임을 유도한다. 머리는 정면 또는 지정 위치 시선을 아주 약하게 선호한다. 상체 81 제어권을 줄이거나 별도 고정 PD 채널을 추가하지 않는다.

아래 속도와 초기 물리 목표 탐색 표준편차는 최초 시험 후보이며 검증된 한도가 아니다. 실제 물리 목표 탐색 크기를 tanh 이전 `log_std`에 그대로 복사하지 않는다. effective action 범위, tanh 변환과 native 목표 분포를 먼저 계산·검사한다.

| 부위 | 요청 목표 범위 후보 | 목표 변화율 후보 | 초기 물리 목표 탐색 표준편차 후보 |
|---|---|---:|---:|
| Torso·Spine·Chest 9 | native 한계 ∩ `q_ref ±5°` | 0.10 rad/s | 0.002 rad |
| Neck·Head 6 | native 한계 | 0.50 rad/s | 0.010 rad |
| 양쪽 Thorax·Shoulder·Elbow·Wrist 24 | native 한계 | 1.00 rad/s | 0.020 rad |
| 양손 손가락 42 | native 한계 | 1.50 rad/s | 0.030 rad |

[action_bounds_candidate.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/action_bounds_candidate.json)은 저장된 native 초기값으로 계산한 81관절 목표 범위 후보이며 적용되지 않았다. 이 파일은 body 9, head 6, arm 24, finger 42로 나누며, 초기 PD 목표가 후보 범위 안에 드는지 기록한다. 환경이나 실행 목표는 변경하지 않았다.

## 합산 보상 후보

연속 항목은 초당 rate로 계산해 제어 간격 `Δt=1/60s`를 곱한다. 이벤트 항목은 단발 보상이므로 `Δt`를 곱하지 않는다. 따라서 목표 변화율 비용은 부위별 rate 비용이고 압현 완료·해제·타현 hit/miss는 event 보상이다.

`r_t = Δt·(2.00H + 0.50A + 0.25K + 0.01G − 2.00C_guitar − 0.30C_body − 0.05C_body_vel − 1.00W − 0.20C_collision − 0.05C_limit − 0.01C_target_rate) + E_t`

| 항목 | 계수 | 원문 정의의 요점 |
|---|---:|---|
| H 정확 압현 유지 | +2.00/s | 활성 PRESS의 실제 성공, wrong_press가 있으면 0; sustain 유효 마스크 적용 |
| A 압현 접근·정렬 | +0.50/s | 활성 PRESS 목표의 정렬 품질 0~1; 현재 G 좌표·원본 목표 사용 |
| K 타현 준비·경로 | +0.25/s | 유효 타현 event 구간의 피크 경로 품질 0~1; 해당 목표가 없으면 0 |
| G 머리 시선 | +0.01/s | 정면/지정 지점 정렬 품질 0~1; 최대 +0.01/s |
| C_guitar 범위 이탈 | −2.00/s | 허용집합 바깥의 위치·회전 거리; 내부와 범위 내 속도 비용은 0 |
| C_body 몸통 자세 | −0.30/s | 실제 몸통 9관절 초기 기준 오차와 Chest 상대 회전 deadband 초과 |
| C_body_vel 몸통 속도 | −0.05/s | 실제 몸통 9관절의 작은 속도 초과 |
| W 오압현 | −1.00/s | 원본 wrong_press 판정이 활성인 동안 1 |
| C_collision 불필요 접촉 위험 | −0.20/s | 검수된 비허용 body pair 접촉 여부; 정상 지지는 제외 |
| C_limit 관절 한계 접근 | −0.05/s | 실제 native 관절 범위의 양 끝 5% 이내 진입 비용 평균 |
| C_target_rate 목표 변화 | −0.01/s | 실제 제출 목표의 부위별 정규화 변화율 제곱; 네 부위 평균 |

`C_joint = mean_body9 ρ((|q_i−q_ref_i|−2°)_+/5°)`이고 `C_chest = ρ((θ_chest−3°)_+/5°)`다. `C_body=max(C_joint,C_chest)`이므로 그림의 몸통 곡선은 전체 `C_body`가 아니다. `C_body_vel`은 몸통 관절 속도 0.02 rad/s deadband를 쓰는 별도 비용이다.

시선 보상은 head-local 방향과 Pelvis 기준 정면 또는 지정 지점 방향을 world 단위벡터로 비교한다. 정렬 상태가 유효하지 않으면 mask로 미유효 상태를 기록하고 `G=0`으로 둔다. 임의의 Head local 축을 정면으로 가정하거나 더 큰 머리 회전에 보상을 주지 않는다.

## 이벤트와 검사 범위

`E_t = 0.50 N_fret_complete + 0.50 N_release + 1.00 N_strike_hit − 1.00 N_strike_wrong − 1.00 N_strike_miss`다. 각 항은 해당 제어 구간에서 처음 인정된 이벤트만 센다. 압현 완료는 목표 종료 시점의 마지막 eligible 표본과 sustain tracker 증거를 확인하고 목표 ID당 한 번 인정한다. 해제는 원래 release 창에서 실제 press→release 전이를 확인한다. 타현 hit, wrong crossing, miss는 원본 event/현 식별 규칙과 중복 방지 계약을 따른다. 완료 타이머만으로 압현 성공을 보상하지 않고, 쉬는 손가락 상태를 매 step 성공으로 보상하지 않는다.

[formula_check_final.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/formula_check_final.json)은 26개 순수 수식/계약 synthetic 검사가 PASS였음을 기록한다. 이 검사는 native detector, event hook, tracker, network, physics의 실행 검증이 아니며 특정 학습 backend에서의 효과 증거도 아니다. 실제 신호 정확성이나 학습 성능을 증명하지 않는다.

## 원문과 추적성

동결 원문: [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md)

- 전체 상체 81 제어권: 원문 12–14행
- 행동 범위·rate·초기 탐색 후보 및 몸통 ±2° deadband: 원문 16–27행
- 초당 rate와 Δt, 전체 합산식: 원문 29–35행
- 계수 및 항목별 정의: 원문 37–50행
- 세부 정렬·피크·event 기준: 원문 51–52행, 69–83행
- 비용 수식, 회전집합 한계와 시선: 원문 53–67행
- 평가 및 synthetic 검사 한계: 원문 85–91행
- 산출물 경로와 보존 조건: 원문 93행

원문 SHA-256: `62d847010dd38f6c7d4cc6d393782533a865f3100c31bb833c44e1dddb7e6744`
