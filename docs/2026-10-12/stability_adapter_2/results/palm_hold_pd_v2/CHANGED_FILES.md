# 파일 인덱스 — palm_hold_pd_v2

## 이번 산출물

- [비교 플로터](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_pd.py:21) — 저장된 analysis/trace/contact 검증과 2×2 그래프 생성.
- [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/README.md:1) 및 [이전 v1 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v1/README.md:1).
- [최종 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts/palm_hold_pd.png), [입력·producer·출력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts/plot_manifest.json), [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/plot_execution.json), [실제 plot stdout/stderr](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/plot_execution.log).
- [v1 producer 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/producer_attempt_v1/plot_palm_hold_pd.py)과 [v1 산출물 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts_attempt_v1/), [v2 producer 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/producer_attempt_v2/plot_palm_hold_pd.py)과 [v2 산출물 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts_attempt_v2/)은 각각 당시 manifest의 producer SHA와 일치한다.
- [분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/analysis.json), [분석 실행 메모](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/EXECUTION_NOTES.md:1), [setter 보완 검증 기록](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_VERIFICATION.md:1).

## 관련 구현·계획·누적 문서

- [검증 runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_hold_pd_verified.py:16), [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_hold_pd.py:15), [PD 비교 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_PLAN.md:1), [다음 강성 분리 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1).
- [프로젝트 README 결과 항목](/home/ajou/yigyu/3/stability_adapter_2/README.md:639), [메인 계획 체크리스트와 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1233), [누적 산출물 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:389), [시각 보고서 그림 92](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1228), [PD 구현 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/IMPLEMENTATION_FILES.md:1).

## 보존된 실행 자료

- v1·v2의 원자료, 실행 stdout/stderr, 분석 이력, 보존 검사 JSON은 각 phase 경로에 유지했다. v2 시뮬레이션 자료는 이번 plot 작업에서 수정하지 않았다.
