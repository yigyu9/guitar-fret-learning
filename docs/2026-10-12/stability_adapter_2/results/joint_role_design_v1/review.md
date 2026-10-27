# 전신 관절 역할·제어 원칙 문서 검수

2026-10-15. change-reviewer가 상세 README, joint_role_map.json, build_role_index.py와 문서화 계획을 읽기 전용으로 검수했다. 본 기록만 작성했다. producer 재실행·runtime/native 변경·기존 봉인 수정은 수행하지 않았다.

## 요약 판정

문제없음. Critical 또는 수정이 필요한 Warning은 발견하지 못했다. 현재 구현39정책+66기준 목표와 제안55정책+50기준 목표, 원본105채널/97비영 범위/0범위8축이 구분되어 있다. 역할 색인은 설계 문서이며 native 설정·성능 검증 결과가 아니다.

## 관절 색인 대조

[joint_role_map.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/joint_role_map.json)의105개 이름·XML 순서·각도 범위를 원본 humanoid XML과 독립 대조하여 모두 일치함을 확인했다. 이름은105개 모두 유일하고 root는 포함하지 않는다. producer를 다시 실행하거나 색인을 덮어쓰지 않았다. 기록된 입력4개 SHA도 현재 파일과 일치했다.

| 확인 항목 | 결과 |
|---|---:|
| 전체 scalar 채널 |105|
| 현재 정책 / 기준 목표 |39 /66|
| 제안 정책 / 기준 목표 |55 /50|
| 하체 전체 / 비영 범위 |24 /16|
| 원래0 범위 하체 축 |8|

제안에서 추가되는 policy 이름 집합은 하체의 비영16개뿐이다. 현재 연주39개를 모두 포함하며,0범위8축은 policy로 전환하지 않는다. 몸통·오른쪽 근위부15, 오른손21, 목/머리6과0범위 하체8의 합이 제안의 reference50이다. map의 source_xml_order는 원본 XML 순서이며 native importer 순서나 새55행동 순서로 해석하지 않도록 scope가 명시되어 있다.

## 본문 확인

- [현재/제안 구분:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:13): 현재 native 초기 자세는 과거 fixed-lower 조건이고, 전신105 CPU 계약과55출력 제안은 서로 다른 상태로 표시한다.55출력은 구현·학습되지 않았으며 새 action 순서·입력/제어/체크포인트 계약이 필요하다.
- [목표 권한:53](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:53): ‘지지 조정’이라는 기능 설명이 몸통·오른쪽 Thorax/Shoulder15의 현재 목표 변경 권한을 암묵적으로 만들지 않는다. 현재와55안 모두 해당15개는 기준 목표 유지이며, 능동 보정은 별도 후속 설계다.
- [이름과 해부학:57](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:57): x/y/z suffix를 world축·해부학적 굽힘 방향으로 직접 해석하지 않는다. R_Shoulder 강체의 상완 구간, 손가락별5/4/4/4/4 채널 및 몸 관절63+손42 구성이 맞다. Hip의 허벅지 배치 영향과 Knee/발의 간접 영향도 구분한다.
- [접촉 분담:31](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:31): 가슴·상완·허벅지 모두의 접촉을 매 순간 강제하거나 접촉 수/힘 최대화를 목표로 두지 않는다. 실제 악기 상태와 음악 수행을 함께 본다. 의도한 지면 접촉과 비접촉 구간도 구분한다.
- [왼손과 피크:43](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:43): 압현의 반력 교환을 기타 무게 지지의 필수 역할과 구분한다. 엄지 보조는 조건부이며 입력 운지 변경 학습을 자동 포함하지 않는다. 오른손21 목표 유지와 실제 피크 파지, marker와 물리 충돌 물체도 구분한다.
- [관측과 시간:155](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:155): 실제 관절·기타·접촉·목표/음악 이력과 명령 시점을 요구하고 명령/측정 토크를 분리한다.24개 음악 특징·8개 진행 상태는 출발점이며, 합성 테스트 상태를 실제 전신 관측 ABI로 확정하지 않는다. ±50/100ms 독립 판정, 준비 dwell/audible hold 분리와 고정 음악 시계도 유지한다.

## 보상·학습·비교의 정합성

[하체 자세 비용:193](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:193)의 dead-zone 정규화식은 실제 q와 기준 q_ref의 편차를 사용한다. δ≥0, s>0, w≥0를 명시하고 비영 하체 집합16개에만 적용해0범위 축으로 나누지 않는다. 허용 자세 편차와 목표 범위·rate cap, 물리 실패 종료는 별도다. 구체 계수·gain·승급 문턱을 검증된 값처럼 제시하지 않는다.

공통 음악·기타 성과에 역할별 보조 비용을 더하는 식은 설계 예시이며 실행된 보상으로 설명하지 않는다. 필요한 연주 속도나 지지 토크 자체를 일괄 억제하지 않도록 했고, 가중합·multiplier를 물리 안전 보장으로 해석하지 않는다. 조기 실패·누락·terminal 비용/분모/budget과 simulator 오류를 구분하는 평가 방향도 기존 설계와 일관된다.

[핵심 비교:224](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:224)는 같은 하체 가동 환경에서39출력 기준 유지와55출력 보정을 비교하도록 한다. gain·초기 배치·예산·음악 판정을 맞추고 자세 비용의 효과를 추가 비교한다. fixed-lower와의 차이를 하체 학습만의 효과로 돌리지 않는다. 역할·head 분할 자체를 연구 기여로 확정하지 않으며 복수 seed·실패를 포함한 성과로 검증하도록 했다.

## 주장과 구현 범위

Root만 고정하는 최종 방향은 외부 반력을 갖는 문제이며 자유 보행·부유 root 균형 성과로 확대하지 않는다.105채널 전체 feedback과 모든 목표의 RL 학습, 정지 지지와 연주 중 지지, 기하/접촉 후보와 실제 음향, 자연스러움·사람 동작 유사성을 각각 구분한다.

[논문 표현:254](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_role_design_v1/README.md:254)의 제목과 제안 문장은 현재 설계 설명이다. 실제55출력·native 환경이 완성되기 전에는 달성한 결과로 바꾸지 않도록 명시되어 있다. 기존 코드·결과를 재해석하지 않고 역할 합의와 후속 검증 조건을 상세 기록한 범위에서 최종 보존 감사에 지장이 없다.
