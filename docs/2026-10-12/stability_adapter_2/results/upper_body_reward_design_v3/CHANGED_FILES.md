# 움직임·보상 설계 v3.1 — 변경 파일 색인

새 설계 문서와 함수 그래프·설명·합성 수식 검사를 작성했다. 최초 수식 검사의 v3 초안과 결과를 보존하고, 이벤트 후킹/시선 좌표를 보완한 v3.1을 최신 설계로 삼는다. 기존 v1/v2·코드·실험은 보존하며 네 메인 문서는 끝에만 기록을 추가했다. 환경/네트워크/훈련 코드는 수정하지 않았다.

| 내용 | 절대 경로 및 실제 시작 행 |
|---|---|
| 보상 설계 검수 정정본 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:1) |
| 부위별 범위/속도·탐색 및 기준 관측 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:12) |
| 합산식·초당 가중치 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:29) |
| 비용 및 시선 수식 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:53) |
| 고유 이벤트 후킹 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:69) |
| 평가와 검증 순서 | [UPPER_BODY_REWARD_DESIGN_V3_1.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:85) |
| 최초 수식 검사에 사용한 초안 보존 | [UPPER_BODY_REWARD_DESIGN_V3.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3.md:1) |
| 메인 문서 최신 추가 구간 | [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:760) |
| 메인 문서 최신 추가 구간 | [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1917) |
| 메인 문서 최신 추가 구간 | [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:606) |
| 메인 문서 최신 추가 구간 | [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2368) |
| 함수 그래프 설명 | [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1) |

[함수 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.png) · [함수 표본 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.json) · [26개 최종 수식/합성 계약 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/formula_check_final.json) · [저장된 native 값에서 계산한 목표 한계 후보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/action_bounds_candidate.json).

독립 검수/보존 감사의 예정 경로는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/review.md`, `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/final_verification.json`이다. 문서 단계 마감은 main PLAN에 기록한다.
