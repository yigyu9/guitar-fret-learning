# 실제 기타 오차에 대한 작은 관절 목표 보정의 응답 식별

seed2_startup_target_v1의 보정 0/.5/1배에서 최대 5초 기타 p/q 오차는
158.088mm/26.355°, 120.157mm/21.524°, 26.773mm/8.323°였다.
기존 full과 LA 1.1018469719600776m를 진단 기준으로 유지한다.
특정 어깨 좌표나 중력만을 악화 원인으로 단정하지 않는다.
full의 thumb/index/middle 양의 rawλ는 마지막 step1200, palm의 마지막 양λ/전체행은
121/134였다. 세 조건의 RH–기타 접촉은 0행이다. 넥 면별 연속 지지는 미검증이다.

## 제어권과 보정의 관계

최종 인터페이스는 양쪽 Thorax→손가락 66축의 연주 목표 q_play를 받는다.
지지용 목표 bias b_support와 기타 오차 보정 δ_stabilize를 합성한다.
`q_target = clip_native(q_play + b_support + δ_stabilize)`이며 기타 p/q나 관절 상태를 덮어쓰지 않는다.
몸통9은 현재 초기 PD 목표 유지로 따로 관리하고 실제 좌표 변화를 측정한다.
이번 정적 진단에서는 q_play=seed2 초기q, b_support=기존 왼팔12 bias다.
δ는 작은 추가 목표 보정이며, 이번 6축은 응답 식별용 입력이다. 최종 제어권을 6/12/33축으로 제한하지 않는다.
연주 입력과 안정화 보정의 충돌 시 우선순위·변화율·잔여 범위는 feedback 검증 단계에서 설계한다.
정책·학습 구조는 아직 결정하지 않는다.

## 다음 작은 실행 단위

1. 같은 초기81q·기타 p/q/속도·LA·PD·solver·self-collision을 유지한다.
   full 기준과 L_Shoulder_xyz/L_Wrist_xyz 각각 +0.002rad의 6probe를 만든다(새7init/8400step).
   초기q는 바꾸지 않고 첫 step부터 상수 PD 목표만 변경한다. 각각 5초·두 뷰151frame를 저장한다.
   합성 offset은 기존 진단 ±.3rad와 native 목표 한계를 확인한다.
   한계로 잘린 probe를 동일한 0.002rad 응답으로 취급하지 않는다.
2. 기타 오차 벡터는 world의 `p_current−p_goal`(m)와
   `Log(R_current R_goal^{-1})`(rad)로 정의한다. raw quaternion은 xyzw다.
   최초0.1초/1초/5초와 마지막1초 평균 응답을 읽고 기준 대비 유한차분 6×6행렬을 만든다.
   joint scalar 변화와 SO3 기타 회전을 구분한다. 접촉 변화·법칙·양손 접촉·몸통 편차도 기록한다.
3. 행렬의 rank·조건수와 단위별 잔차를 확인한 뒤 각 probe축 ±0.001rad 이내의
   한 개 결합 heldout을 고른다. 첫7실행과 별도인 새5초로 검증한다(추가1init/1200step).
   예측과 실제 G응답의 비교 없이 행렬을 runtime feedback이나 학습에 넣지 않는다.
   이 단계는 최대8native/9600step이며 성공 기준을 임의 확정하지 않는다.

기타는 자유 중력·실제 접촉·기존 수동 strap 법칙을 받고 root와 하체는 물리적으로 고정한다.
코드·trial은 stability_adapter_2, 결과는 docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1에 둔다.
이 계획은 아직 실행하지 않았다. 목표각 보정의 효과를 실제 기타 응답으로 확인하는 다음 단계다.
