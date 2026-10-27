# 어깨 초기각을 유지한 오른손 접근 탐색

2026-10-06. 기존 양팔 C02±0.3rad 초기각 승인 범위의 후속이다.
직전 right_clearance_v3/ty015_sx010은 어깨 native 접촉0이었지만 오른손 간격이
38.250→56.265mm로 벌어졌다. 이번에는 이 조합의 오른쪽 Thorax/Shoulder 초기각을
유지하고 Elbow/Wrist 6개 초기각만 조정한다. 제어권을 제거하는 것이 아니다.

- [ ] 1. C02 기준 ±0.3rad∩모델 한계 안에서 기존 source 검색의 두 좌표 sweep을
  수행한다. 각 축 후보 −0.3/−0.2/−0.1/−0.05/+0.05/+0.1/+0.2/+0.3rad를
  C02 절대각에 더한다. 이미 조정된 시작각에 다시 ±0.3rad를 더하지 않는다.
  기존 전체 humanoid–기타 signed negative-pair 제외, LH 위쪽 반구/국소 넥 아래
  조건과 nominal 3mm unsigned RH/body 거리 soft 순위를 유지한다. 새 거리 gate는 없다.
  proximal 관절 목표와 초기 body pose, 기타/몸통/왼손/손가락/하체/PD/LA를 검사한다.
- [ ] 2. 초기 검사 통과·접근 개선 후보 최대3개와 같은 기준을 각0.1초 native
  hold OFF로 비교한다. 기준 raw4파일은 직전 ty015_sx010과 정확히 재현되어야 한다.
  손과 어깨/상완/손목 접촉 및 기타 p/q·속도·장력·팔 처짐을 분석한다.
- [ ] 3. 개선 후보만 별도 계획으로 연장한다. 그림과 설명을 누적19절에 추가하고
  Luna 산출물과 독립 변경 검수를 마친다. 성공 허용오차를 임의 확정하지 않는다.

왼팔 p08·finger42·torso9·C02 하체/root·기타 +5mm 초기 p/q와 유지 목표·native
gain/solver·절대 LA1.1010801317960974m와 원본 strap 수식을 유지한다.
팔꿈치/손목은 strap guide가 아니므로 route/절대 길이 보존도 대조한다.
고정/강제부착/실행 중 pose 덮어쓰기/새 controller/gain/동적 strap/학습은 추가하지 않는다.
palm-position controller는 사용자 승인 전이며 이번에는 실행하지 않는다.

구현/초기 입력은 stability_adapter_2에, raw search/native 비교와 산출물은
docs/2026-10-12/stability_adapter_2/results/right_distal_v1에 저장한다.
이전 source 파일과 결과는 보존한다. 직전 목표 turn은10개 fresh 검사와4개 native
결과를 만들고 다음 방향을 바꾼 **progress**였다. 최종 기타 유지 성공은 아직 아니다.
