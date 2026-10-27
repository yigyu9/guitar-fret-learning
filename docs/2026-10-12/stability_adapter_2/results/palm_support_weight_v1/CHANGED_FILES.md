# 변경 파일 인덱스 — palm_support_weight_v1

산출물은 검증된 세 조건의 저장 자료만 사용했다. 그림 생성 과정의 native initialization / physics step은 0 / 0이다.

- [plot_palm_support_weight.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_support_weight.py:32) — 네 지표 panel을 생성하고 구조·시간·유한값을 검사한다.
- [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/README.md:1), [VISUAL_REPORT §60](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1074), [dated results index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:347).
- [검증 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/analysis.json) — 6개 검사, 3 native initialization / 72 physics steps.
- 저장 inputs: [scale 0.08 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/scale_0p08/trace.json), [scale 0.02 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/scale_0p02/trace.json), [scale 0 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/scale_0/trace.json). Manifest에는 세 조건의 trace, tasks, contacts, report SHA를 모두 기록했다.
- [비교 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/palm_support_weight.png), [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/plot_manifest.json), [실행 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/plot_execution.json), [실행 요약 log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/plot_execution.log).
- [기존 normal-control 단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_NORMAL_CONTROL_PLAN.md:76)은 읽기 전용 맥락이다.

## 구현·설계 변경

- [방향 가중치 비교 runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_support_weight.py:18) — 기존 scale .08 재현과 .02/0의 target-only 실행.
- [저장 원자료 검증·분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_support_weight.py:12) — 입력 SHA, 실제 task, coverage, 접촉과 기타 상태를 대조한다.
- [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_SUPPORT_WEIGHT_PLAN.md:1), [메인 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:565)·[메인 PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1158)의 비교 기록.
- [후처리 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/analysis_execution.json), [native 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/execution.json).

독립 검수: [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/review.md).
