# right_clearance_v2 별도 변경 검수

2026-10-06. 별도 change-reviewer. 이번 기록 범위는 초기 입력 생성기와 현재 저장된 7개 정적 평가다.
구현·원자료는 읽기 전용으로 확인했고 새 native 초기화/physics trial을 실행하지 않았다.
검수자가 수정한 파일은 이 기록뿐이다.

## 요약 판정

**문제없음**. 현재 범위에서 남은 Critical/Warning/Suggestion 없음.
현재 `search/search.json`에서는 reference만 유효하다. 완전 되돌림3개 및 중간값3개는
기존 source 음수 pair gate에 의해 모두 거부됐으므로 이 6개를 native 비교 후보로 사용하지 않는다.
새 후보/실제 native 비교/미디어가 추가되면 해당 변경은 별도로 검수해야 한다.

## 입력 생성기와 보존 계약

- `/home/ajou/yigyu/3/stability_adapter_2/make_right_clearance_inputs.py:39`의
  완전 Thorax_y 되돌림3개와 `:47`의 C02 +0.15/+0.175/+0.18rad 중간값3개를 확인했다.
  중간값에서는 나머지 named 초기각이 기존 candidate_01과 exact 일치한다.
- 같은 파일 `:53`은 각 recipe마다 fresh 초기 환경을 생성한다.
  `:59`의 right-only 초기각·모델/±0.3rad bounds·지정 Thorax_y·root/guitar state와 목표·native PD·
  절대 LA/route·초기 DOF/속도 검사 및 모든 query 이후 state 불변 검사가 목적과 정합한다.
  실행 중 pose 재주입이나 새로운 관절 제어 모드를 도입하지 않는다.
- 저장된7개 설정을 독립 대조해 비right named 각도와 LH metric/L_Wrist 위치 exact,
  오른팔 C02±0.3rad bounds, 중간 Thorax_y 지정값과 나머지 distal 각도 exact를 확인했다.
  finger42/torso9/C02 하체의 초기각과 root/guitar+5mm/절대 LA1.1010801317960974m는 보존된다.
- `:69`의 accepted 판정을 저장 geometry/LH 조건에서 재계산해 전부 일치했다.
  별도 어깨 거리 threshold 없이 기존 source 음수 pair와 LH 조건을 사용한다.
  accepted 입력만 저장하며 현재 trials/right_clearance_v2에는 reference.json만 있다.

## 현재 정적 결과와 검증

- 완전 되돌림3개의 source 음수 pair 수는1/2/6개다.
  중간값 +0.15/+0.175/+0.18rad는2/1/1개이며, RH:palm/G:body backend signed gap은
  각각−3.516569/−1.137145/−0.242039mm다. +0.15rad에는 R_Elbow/G:body 음수 pair도 있다.
- unsigned convex-hull proxy와 backend signed query는 별개다. 양수 unsigned 근접도와
  음수 signed query를 관통 깊이/PhysX clearance/실제 접촉 성공으로 합쳐 해석하지 않는다.
- 프로그램 AST 문법검사와 7개 입력/gate 대조를 통과했고,
  `search/search.json`에 기록된60개 source/input/asset SHA를 현재 파일에서 확인해 모두 일치했다.
  최초 직렬화 실패 및 교정 자료의 별도 보존 경로는 계획서에 명시되어 있으며 삭제/수정하지 않았다.

검수 범위 밖의 다른 작업 트리 변경은 수정하거나 되돌리지 않았다.
