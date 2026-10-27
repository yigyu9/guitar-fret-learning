# 변경 파일 및 결과 경로

## 산출물

- [Read-only saved-trace plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_tensor_effort_api.py:1) — [입력 SHA·6개 trace 검사](/home/ajou/yigyu/3/stability_adapter_2/plot_tensor_effort_api.py:18), [2-panel 그림/manifest](/home/ajou/yigyu/3/stability_adapter_2/plot_tensor_effort_api.py:52).
- [결과 안내와 6행 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/README.md:1); 누적 [VISUAL_REPORT §48, 그림 63](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:912).
- [Canonical figure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.png) 및 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.manifest.json:1).
- [Plot command/environment/exit/hash metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/plot_execution_v4.json:1), [plot log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/plot_run_v4.log:1).

## Read-only inputs and project anchors

- [Six-run comparison with five source hashes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/rollouts/comparison.json:1), [approval record](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/approval.json:1), [native execution record](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/native_execution.json:1), [native log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/native_run.log:1). Six individual run JSONs are in `rollouts/`; they each contain 25 saved states, 24 submissions and 9 true checks. [Analysis-validated source XML range comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/analysis_validated_v2.json:1) is distinct from native `hasLimits` readback.
- [Approved diagnostic contract](/home/ajou/yigyu/3/stability_adapter_2/TENSOR_EFFORT_API_PROPOSAL.md:1), [PLAN §56](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1023), [project README result note](/home/ajou/yigyu/3/stability_adapter_2/README.md:470).

## Verification state

Plotter syntax check and visual inspection passed. First and intermediate images/manifests remain under `artifacts/`, `artifacts_validated/`, and `artifacts_final/`; matching producer copies remain under `source_plot_attempt_v1/`, `source_plot_v2/`, and `source_plot_v3/`. The latest output is `artifacts_final_v2/`. [Independent review](runtime_review.md:7) completed.

## 실행 구현과 후속 분석

- [6조건 실행 구현](/home/ajou/yigyu/3/stability_adapter_2/run_tensor_effort_api.py:44) — 별도 native fixture, 초기 상태·CPU descriptor·실패 기록과 정리.
- [source 범위·속도 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/analysis_validated_v3.json:1) — 기존 v1/v2 자료도 보존.
- [최종 독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/runtime_review.md:7).
- [속도 관측 추가 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/velocity_review.md:7).
