# 오른팔 초기 어깨 여유 회복 비교

2026-10-06. 기존 양팔 C02±0.3rad 초기각 승인 범위의 후속이다.
right_support_v1 후보의 초기 어깨/body hull gap은0.787mm였고,
손 근접과 함께 어깨가 접근했다. 아래 세 조합을 p08 기준과 비교한다.

1. 기존 candidate_01의 R_Thorax_y 초기각만 p08 기준으로 되돌린다.
2. 같은 조합에서 R_Shoulder_y를 C02 기준 +0.2rad로 둔다.
3. 같은 조합에서 R_Shoulder_y를 +0.3rad, R_Elbow_x를 +0.1rad로 둔다.
나머지 오른팔 초기각은 기존 candidate_01의 값을 쓴다. 모델 한계에 clip하며
전체 오른팔 변화가 C02±0.3rad 안인지 검사한다. 유효 입력 최대3개를 쓴다.
첫 완전 되돌림3개는 팔꿈치/손목/손바닥 source 음수 pair가 있어 실행하지 않았다.
그다음 기존 candidate_01의 나머지 값을 유지하고 R_Thorax_y만
C02 기준 +0.15/+0.175/+0.18rad로 둔 중간값3개를 검사한다.
이 중간값3개도 source 음수 pair가 있어 실행하지 않았다. 다음은 기존 나머지 값을
유지한 (R_Thorax_y, R_Shoulder_x) C02 보정 조합
(+0.175,+0.175), (+0.175,+0.15), (+0.15,+0.1)rad 세 개다.
source unsigned hull 거리와 backend signed query는 서로 다른 proxy이며,
양수가 나왔다고 기존 음수 pair 제외 조건을 완화하지 않는다.

- [ ] 1. fresh 초기화에서 전체 source negative-pair 없음과 기존 LH 방향/국소 넥
  아래 조건을 검사한다. RH palm/body와 shoulder/body unsigned hull 간격을
  함께 관측한다. 어깨 거리의 새 필수 threshold나 runtime gate는 추가하지 않는다.
- [ ] 2. 유효 후보와 p08 기준을0.1초 hold OFF native 비교한다.
  최초 후보의 R_Thorax_y 되돌림은 초기 설정만의 비교이며 해당 관절 제어권을
  제거하는 것이 아니다. 물리 시작 후에는 기존 PD target만 유지한다.
- [ ] 3. 기타 최대 이동/회전·속도·장력·실제 팔/손 상태·접촉을 보고 다음 방향을
  정한다. 개선 후보만 별도 계획으로 연장하며 성공 허용오차를 임의 확정하지 않는다.
  Luna 산출물과 별도 검수를 누적18절에 저장한다.

왼팔 p08·finger42·torso9·C02 하체/root·기타 +5mm 초기 p/q/유지 목표·
native gain/solver·절대 LA1.1010801317960974m와 원본 strap 수식은 유지한다.
고정/강제 부착/실행 중 pose 덮어쓰기/새 제어/gain/동적 strap/학습은 추가하지 않는다.
입력과 구현은 stability_adapter_2, 결과는
docs/2026-10-12/stability_adapter_2/results/right_clearance_v3에 저장한다.
최초 입력 JSON boolean 저장 오류 로그/소스/부분 입력과 그 수정 후4개 초기검사는
right_clearance_v1 및 trials/right_clearance_v1(_verified)에 보존한다.
중간값까지7개 초기검사는 right_clearance_v2와 source 보관본에 유지한다.
