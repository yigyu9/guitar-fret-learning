# 전체 상체 보상 설계 v4 비교

v4는 음악 결과를 최우선으로 두고 유지·전환·접근·자세 항의 총기여를 고정 예산으로 제한하는 **PROPOSED 설계**다. 전체 상체 81관절과 Actor/Critic 512→256 구조, 행동 범위 후보는 유지한다. 이번 산출물은 동결 설계와 합성 산술 자료를 설명한다. 새 물리 실행 0, 학습 0이며 런타임 환경·체크포인트·자산을 변경하지 않았다.

![v4 보상 수식 비교 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/reward_refinement.png)

## 세 패널 읽기

그래프는 [plot_data.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/plot_data.json)의 값을 그대로 사용한다. 거리를 m에서 mm로 바꾼 것은 축 단위 변환이다. 세 패널은 각각 독립 y축을 가지며, 모두 수학적 설계/합성 산술 비교다.

1. **유지 상한 비교**: v3.1은 초당 최대 `+2`가 유지 시간에 따라 누적되어 `2T`가 된다. v4에서는 한 Fret event의 유지 항이 고정 분모에 정규화되어 최대 `+0.10β`다. 그래프는 v4를 `β=1`로 조건화했다. 초와 event별 β 예산은 정산 단위와 분모가 달라 곡선 간 높이를 같은 성능 단위로 해석하면 안 된다.
2. **β=1 onset 예시**: 최초 초안의 6/6 정음·U=0 점수 `2`보다 5/6 오음·U=1 점수 `2.333`이 커질 수 있었다. 최종 v4의 비교 하한은 정음의 최악 하위항 포함 `1.826`, 실패의 최선 하위항 포함 `1.609`다. 두 최종 하한을 비교할 때 나머지 1차 음악 항과 기타 항은 같다고 둔다. 이것은 한 예시의 조건부 산술이며 일반 성능 보장이 아니다.
3. **접근 함수 후보**: 유효 영역 바깥 거리 `d`에 대한 `clamp(1 − d/0.25m, 0, 1)` 표본이다. 유효 영역 내부는 점수 1 plateau이며, 250 mm 이후는 0이다. toy/source geometry의 실제 검증이 아니고 detector나 실제 기타 좌표에서 측정한 곡선도 아니다.

## 고정되는 정책 범위와 음악 판정

상체 제어권은 torso/spine/chest 9, neck/head 6, 양팔 24, 손가락 42의 총 81관절이다. root와 하체는 고정 상태다. Actor/Critic은 512→256을 유지한다. 몸통 목표는 native 한계와 `q_ref ±5°`의 교집합 후보, head·팔·손가락은 native 범위 후보이며, q_ref/Chest 기준은 reset 때 한 번 정한다. 이 값들은 미적용 행동 범위 후보이며 실제 각도 보장이 아니다.

Fret의 1차 점수는 `F_e = 2(2O_e−1)`이다. `O_e`는 필요한 현의 effective sounding fret, 실제 press depth/cell, 원래 readiness dwell을 만족한 비율이다. 양손 모드에서는 원본이 인정한 실제 crossing 시점에 sounding-state와 readiness dwell을 평가하는 것이 구현 gate다. 뒤늦게 손가락을 고쳐도 이미 잘못된 onset을 정음 성공으로 바꾸지 않는다. 지정 손가락 운지율은 별도 지표로 보존한다.

Strike의 1차 점수는 `S_e = 2(2h_e−1)−w_e`다. `h_e`는 원본 규칙을 통과한 required target hit 비율이고 `w_e`는 고유 invalid crossing 수다. 동일 crossing은 한 번만 세며, 서로 다른 wrong crossing은 event 안에서 각각 반영한다. crossing이 없으면 기하 접근 점수가 높아도 hit 성공이 아니다. F/S는 원래 음악 event를 기준으로 하고 REST/idle의 F/S/A/K는 0이다. harmless extra press는 음악 오음으로 자동 분류하지 않는다. 지속 손바닥/엄지 접촉이나 접촉력 증가를 성공 보상으로 두지 않는다.

음악 event 수와 분모는 시작 전에 고정한다. `N_ref=max(N_F,N_S,1)`, `m_max=max(6, 모든 Fret O 검사점 수, 모든 Strike required target 수)`, `β=6/m_max`다. 음악 clock과 horizon도 사전에 고정하고 실패 때문에 clock을 멈추거나 되감지 않는다.

## 하위 예산과 우선순위

2차 continuity 예산은 다음 계수 후보를 사용한다.

`R_continuity = 0.10Ū + 0.02L̄ − 0.05Ī − 0.05Ē + 0.05f̄ + 0.03τ̄`

이 예산의 β=1 범위는 `[-0.100, +0.200]`이며 총 폭은 `0.300β`다. 유지·해제·간섭·early release·gesture 완료·timing 품질을 포함한다. 해당 기술이 없는 경우 해당 항을 0으로 두고 남은 항에 예산을 재분배하지 않는다.

3차 auxiliary 예산 후보는 다음과 같다.

`R_aux = 0.05Ā + 0.025K̄ + 0.001Ḡ − 0.025B̄ − 0.005V̄ − 0.025X̄ − 0.010J̄ − 0.009D̄`

β=1 범위는 `[-0.074, +0.076]`, 총 폭은 `0.150β`다. `A`는 Fret 접근, `K`는 Strike 경로, `G`는 약한 시선, `B/V`는 몸통 자세/속도, `X`는 검수된 비허용 접촉, `J`는 native 관절 한계, `D`는 실제 제출 목표 변화 비용이다. 세부 창과 고정 분모는 원문 정의를 따른다.

2·3차의 합계 폭은 `0.450β = 2.700/m_max < 4/m_max`다. 따라서 **다른 1차 음악 항과 기타 항이 같다는 조건에서** 모든 하위 항이 가장 유리하게 변해도 required hit/음높이 검사점 하나의 성공과 실패 차이를 상쇄하지 않는다는 undiscounted 비교다. 상위 음악 항끼리, 기타 안전 비용과 음악 점수 사이, 할인된 PPO 목적이나 탐색 전반의 우월성 보장은 아니다.

v3와 v4의 유지 보상 숫자는 단위가 다르다. v3.1은 `+2/초`의 연속 rate로 긴 유지 시간만큼 커진다. v4는 eligible 시간을 원래 고정 분모로 정규화하고 유지의 event별 기여를 `0.10β` 안에 둔다. 따라서 v3의 `2T`와 v4의 `0.10β`는 설계안의 누적 경향을 대비할 뿐, 같은 단위의 보상 개선량을 재는 비교가 아니다.

## 접근 함수와 기타 범위의 검증 한계

접근 후보는 현재 기타 좌표계에서 유효 press cell/깊이 영역까지 거리로 정의한다. `A=clamp(1−d_region/0.25m,0,1)`이며 유효 영역 안에서는 plateau 1이다. 25 cm는 native 초기 거리 분포와 비교해 조정할 척도다. 원본 프렛 영역, press depth, marker와 기타 변환을 검증하기 전에는 학습 신호로 쓰지 않는다.

기타 허용범위 안의 비용은 0이다. 범위 내부 복원, 속도, 정지, 복귀 pulse를 보상하지 않는다. 위치 경계 밖 거리와 허용 SO(3) 회전집합 거리 비용은 별도다. 회전집합 판정은 미구현이며 초기 quaternion 오차나 Euler 단일 분해값으로 대체하지 않는다. 그래프의 250 mm 접근 함수와 JSON의 기타 포화 표본 모두 설계 산술이지 geometry 검증이나 물리 시뮬레이션 결과가 아니다.

## 검사 결과와 학습 전 gate

[formula_checks.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/formula_checks.json)은 42개 검사를 PASS로 기록한다. 범위는 synthetic 설계 산술/계약 사례다. 실제 detector, accepted crossing 시점 대응, geometry, tracker, native 접촉, 회전집합, PPO/network는 검사하지 않았다. 학습 backend 성능 증거가 아니다.

Pilot 전에는 Fret sounding-state와 readiness dwell, crossing snapshot의 timestamp, event/clock/고정 분모, 실제 기타 기준 press 영역, SO(3) 경계·특이점·q와 −q 동치, tracker 및 접촉 목록을 native 환경에서 검증해야 한다. 특히 crossing별 고유 오류 수의 control-bin 상한 `M_cross`, 실제 discount `γ`, 미정산 ledger를 확정하지 않았다. 이 세 항목과 보수적 fatal tail 계산이 봉인되기 전에는 pilot을 시작할 수 없다. 치명 실패 시 물리 실행 종료와 이후 실패 return 계산은 구분하며, 과거 성공 증거를 보존하고 미래 미관측 성공은 0으로 처리하는 별도 runtime gate다.

## 동결 원문 및 추적성

동결 leaf: [UPPER_BODY_REWARD_DESIGN_V4.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md)

- 제안 상태, 범위, v3.1 보존: [원문 1–12행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:1)
- 참고 근거와 음악 판정기 구현 gate: [원문 14–28행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:14)
- 고정 분모·β·시간 단위: [원문 30–42행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:30)
- Fret 점수·유지 의미·검사 시점: [원문 44–62행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:44)
- Strike 점수·고유 crossing: [원문 64–73행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:64)
- 2차 예산과 onset 예시: [원문 75–81행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:75)
- 기타 범위와 회전집합 gate: [원문 83–91행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:83)
- 3차 예산, 시선·접근 정의: [원문 93–107행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:93)
- 종료/미유효 신호 gate: [원문 115–125행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:115)
- 구현 전 검증·채택 순서: [원문 127–136행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:127)

원문 SHA-256: `0d7cff02416874ce98a60697503e1ce79e5fce8be52cdea8d9462617b80e56f1` (plot data의 `plan_sha256`와 일치)
