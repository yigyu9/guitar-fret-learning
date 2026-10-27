# 변경 파일 및 입력 인덱스

이번 결과 정리에서 새로 작성한 파일은 이 `README.md`, [그림 생성기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/plot_policy_passive_timeline_v3.py:1), [정책/후속 구간 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/policy_passive_timeline_v3.png), [그림 입력·출력 해시 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/manifest.json), [후처리 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/artifact_execution.json)과 [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/artifact_execution.log), 그리고 [VISUAL_REPORT.md §124](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2218)다. 이전 후처리 시도 및 실패 로그는 덮어쓰지 않고 `figures/attempt_v1/`, `figures/attempt_success_v2/`, `figures/policy_timeline_v2/`에 보존했다.

이번 단계에서 읽은 핵심 원자료:

- [분석 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/analysis/summary.json:1)
- [native_v1 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v1/report.json:1)와 [입력 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v1/attempt.json:1)
- [native_v2 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/report.json:1), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/trace.json:1), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/controls.json:1), [counterfactual](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/counterfactual.json:1)
- 실행 전·후 956개 입력 목록: [inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/inputs_before.json:1), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/inputs_after.json:1)
- 실제 카메라 프레임/동영상 메타데이터: [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/capture.json:1), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/videos.json:1)

관련 구현 및 계획의 실제 파일 위치:

- [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LIVE_GUITAR_PROBE_PLAN.md:1), [수동 기록 연장 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_RECORDING_CONTINUATION.md:1)
- [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_probe_preserved_run.py:1), [v2 실행기](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe_v2.py:69), [native view/capture 경로](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:67), [분석기 진입점](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_live_probe.py:11)
- [stability_adapter_2/PLAN.md 결과 및 제한](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:124), [stability_adapter_2/README.md 결과 및 제한](/home/ajou/yigyu/3/stability_adapter_2/README.md:1429)

기존 native 결과·계획·공유 구현은 수정하지 않았다. 그림 후처리는 native 초기화 0회, 물리 단계 0회다.
