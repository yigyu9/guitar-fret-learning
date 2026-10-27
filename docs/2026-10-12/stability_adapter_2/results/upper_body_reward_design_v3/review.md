# 움직임·보상 설계 v3.1 독립 검수

**요약 판정: 문제없음.** 최종 원문·수식 표본·설명·그림·메인 추가 기록에서 수정이 필요한 오류를 발견하지 않았다. 이 판정은 설계의 정합성과 순수 수식에 대한 것으로, 실제 신호 연결·물리 응답·학습 성능을 인증하지 않는다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 검수 범위

[최종 원문](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:1), [설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1), [함수 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.png), [수식 표본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.json), [최종 합성 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/formula_check_final.json), [행동 한계 후보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/action_bounds_candidate.json), [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/CHANGED_FILES.md:1)과 메인 추가 구간을 검토했다. 메인 구간은 [PLAN:760](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:760), [모듈 README:1917](/home/ajou/yigyu/3/stability_adapter_2/README.md:1917), [결과 README:606](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:606), [VISUAL_REPORT:2368](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2368)이다. 검수자는 이 review.md만 작성했으며 이전 v1/v2/v3·기존 코드·실험을 수정하지 않았다.

## 확인한 수식과 계약

- [원문:14](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:14): 고정 root/하체를 제외한81 전체 제어권과512→256 구조를 유지한다. 몸통9의 요청 한계는 native∩유효 초기 기준±5°이고 actual 각 고정/보장 범위가 아니다. 목/머리6·팔24·손가락42는 native 목표 한계다. 81개 이름의 유일성, 몸통 교집합/나머지 native 한계 및 초기 PD 목표의 포함을 읽기 전용 재계산으로 확인했다.
- [원문:27](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:27): 초기 기준은 에피소드 동안 고정하며 기준 오차·유효 목표 한계·시선 목표/마스크를 정책에 관측시킨다. 움직인 뒤 기준을 갱신해 자세 비용을 없애는 해석을 막는다. 팔/손가락의 초기각 복원 비용과 많이 움직이는 직접 보상은 없다.
- [원문:31](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:31): 무차원 품질/비용에 초당 계수를 적용하고 연속 항에만 Δt를 곱한다. 고유 이벤트는 단발이며 Δt를 곱하지 않는다. 원본 총보상을 중복 합산하지 않는다. 표와 합산식의 항·계수·부호가 일치하며, 샘플링/할인율까지 완전히 불변이라고 주장하지 않는다.
- [원문:51](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:51): H는 현재 활성 PRESS 성공과 필요한 목표·오압현·유효 마스크를 반영한다. 원본 `press_success=physical_press & position_inside` 및 유지 tracker와 맞으며 아치 통과는 별도 평가다. A의 가중 합은0~1의 정렬 신호이며 source의 press-compatible normal_error와 양립한다. K는 현재 phase의 피크 목표 거리 품질이고 인정된 타현 이벤트와 구분한다. 활성 목표가 없을 때 H/A/K의0과 종료 경계 이벤트 처리를 분리한다.
- [원문:55](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:55): Huber 비용은 연속적이며 오차가 커질수록 증가한다. 몸통 관절2°/Chest3°와 속도0.02rad/s의 deadband, 기타 허용집합 내부0, native 한계 접근 및 실제 제출 목표의 정규화 변화율 비용이 일관된다. C_body는 두 자세 비용의 max이므로 작은 개별 관절 변화가 합쳐 만든 큰 Chest 회전도 계산한다. 시선은 같은 world 좌표계의 단위벡터 내적으로 계산하고 최대 가중값0.01/s와 미유효 마스크를 명시한다.
- [원문:73](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:73): 압현 완료는 마지막 eligible 표본 집계 뒤 모든 필수 목표 유지·오압현·원본 tracker 성공 조건을 확인하고 목표ID당1회 처리한다. 시간표 종료나 중간 임시 성공을 완료로 보상하지 않는다. 해제는 이전 PRESS의 실제 전이·원본 창·겹친 PRESS 제외를 확인한다. 오타현은 서로 다른 crossing별로 집계하고 동일 crossing 재집계와 hit/miss 중복을 금지한다. 단순 쉬는 상태나 반복 왕복을 성공 이벤트로 보상하지 않는다.
- [원문:83](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:83): 실패를 임의의 작은 종료 벌점으로만 처리하지 않는다. 고정 음악 horizon의 실패 return/absorbing 처리와 중대한 이탈 문턱을 pilot 전 필수 계약으로 남긴다. 회전 허용집합·detector·시선 축·비허용 접촉 목록이 미검증인 상태를 정상0이나 완성된 보상으로 취급하지 않는다.

## 검증 결과와 한계

동결 원문 SHA-256 `62d847010dd38f6c7d4cc6d393782533a865f3100c31bb833c44e1dddb7e6744` 및 profile SHA를 최종 검사 JSON과 직접 대조했다. JSON의26개 합성 사례 통과 기록과 검사 범위를 확인했고, 별도로 몸통31·시선181·기타81 표본, 총293점을 최종 수식으로 재계산하여 일치를 확인했다. 2267×988 PNG를 직접 열어 표본·부호·축·캡션을 대조했다. 몸통 패널은 동일하다고 가정한9관절 오차의 C_joint만, 기타 패널은 회전거리0의 위치 초과 항만 표시한다. 각 독립 y축과 requested±5°/actual deadband±2°의 구분, 시선 최대0.01/s, 설계 그래프임이 표시돼 있다. 외부 [Isaac Lab 보상 구현](https://github.com/isaac-sim/IsaacLab/blob/main/source/isaaclab/isaaclab/envs/mdp/rewards.py)의 관절 편차·속도·행동 변화 비용도 원문과 대조했으며 이를 프로젝트 수치의 최적성 증거로 쓰지 않는다.

이번 검수에서 환경 보상 구현·native detector/event hook/tracker 실행·네트워크 검사·새 물리·학습은 수행하지 않았다. 관측/기준/범위·시선 축·접촉 목록의 실제 매핑, 탐색 분포·rate 한도·5초 행동 응답, 항별 보상 분포와 종료 return 계약, 작은 PPO pilot이 후속 작업이다. 최종 보존 감사와 봉인은 root 담당이다.
