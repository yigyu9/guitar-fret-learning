# 어깨 초기각을 유지한 오른손 접근 탐색

2026-10-06. 기존 양팔 C02±0.3rad 초기각 승인 범위의 후속이다.
직전 right_clearance_v3/ty015_sx010은 어깨 native 접촉0이었지만 오른손 간격이
38.250→56.265mm로 벌어졌다. 이번에는 이 조합의 오른쪽 Thorax/Shoulder 초기각을
유지하고 Elbow/Wrist 6개 초기각만 조정한다. 제어권을 제거하는 것이 아니다.

- [x] 1. C02 기준 ±0.3rad∩모델 한계 안에서 기존 source 검색의 두 좌표 sweep을
  수행한다. 각 축 후보 −0.3/−0.2/−0.1/−0.05/+0.05/+0.1/+0.2/+0.3rad를
  C02 절대각에 더한다. 이미 조정된 시작각에 다시 ±0.3rad를 더하지 않는다.
  기존 전체 humanoid–기타 signed negative-pair 제외, LH 위쪽 반구/국소 넥 아래
  조건과 nominal 3mm unsigned RH/body 거리 soft 순위를 유지한다. 새 거리 gate는 없다.
  proximal 관절 목표와 초기 body pose, 기타/몸통/왼손/손가락/하체/PD/LA를 검사한다.
- [x] 2. 초기 검사 통과·접근 개선 후보 최대3개와 같은 기준을 각0.1초 native
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

## 초기 검사와 보정 재사용 진단

65개 fresh 초기검사와 기준+3후보의0.1초 hold OFF를 완료했다.
RH/body source 간격을38.250mm에서3.937/4.537/5.797mm로 줄였지만
종료에는21.824/21.562/23.099mm로 벌어졌고 손·어깨 contact0이었다.
기타 최대 오차는 세 후보6.876050/1.519890,6.872301/1.519297,
6.876072mm/1.519909°로 기준6.875701mm/1.519469°와 거의 같았다.
이 수치 차이만으로 채택하지 않는다. 현재 근접각의 실제 지지 전환을 평가한다.

- [ ] 같은 candidate_01 초기각/LA에서 기존 승인된 관절 PI의 OFF/ON을0.1초
  비교한다. 관절오차 actual−target가 개선된 경우0.5/1초로 연장해 진단한다.
  이는 가장 가까운 source 입력의 제어 효과 검사이며 안정화 성공 후보 채택이 아니다.
  구현 run_joint_hold.py 및 JointHoldResidual, ±0.15rad/60Hz/기존gain/C02±0.3
  final bounds를 그대로 재사용한다. 새 손 위치 task/변화율 제한/제어 구조는 추가하지 않는다.
  candidate_01의 오른팔 proximal q_play도 유지하며 PI의24팔 보정은 기존 승인대로 사용한다.
  OFF short raw4는 방금 실행한 candidate_01과 exact, 모든 OFF/ON 초기상태와
  긴 실행 prefix도 일치해야 한다. 원자료는 right_distal_v1/joint_hold에 저장한다.

비교 도구의 명시적 외부 기준 입력은 경로와raw4 SHA를 결과에 기록한다.
최초 comparison.json과 source 보관본은 수정 전 기록으로 유지하며,
수정 후 비교의 현재 기준은 comparison_v2.json이다.
