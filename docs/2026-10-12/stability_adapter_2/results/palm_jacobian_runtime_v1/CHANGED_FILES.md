# Palm Jacobian runtime artifact index

이번 작업은 동일 승인 PI의1초기화/24 physics steps와 읽기 전용 Jacobian 조회·cache 분석·그림 정리다. 새 controller/PD/물리 설정은 적용하지 않았다. 독립 검수와 이미지 확인을 완료했다.

## 산출물

- Plotter: [`plot_palm_runtime.py`](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_runtime.py:1) — report/cache 검사와 embedded SHA를 확인하고 step 1–24 잔차를 그린다.
- 결과 설명·수치표: [`README.md`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/README.md:1).
- 최종 canonical figure: [`palm_runtime_velocity_residuals.png`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_validated/palm_runtime_velocity_residuals.png) — native body linear velocity point 해석을 구분한 세 panel.
- 최종 provenance: [`plot_manifest.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_validated/plot_manifest.json).
- 이전 panel 해석 초안은 [`artifacts/`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts/palm_runtime_velocity_residuals.png)와 [`artifacts_v1/`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_v1/palm_runtime_velocity_residuals.png)에 보존했다. 수정 전 plotter는 [`source_plot_attempt/plot_palm_runtime.py`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/source_plot_attempt/plot_palm_runtime.py:1)에 보관했다.
- 누적 기록 §37: [`VISUAL_REPORT.md`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:796).

## 원자료 및 다음 기록

- Native report: [`measurements/report.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/measurements/report.json:1) — 9 checks, 71 input SHA.
- 25 query samples: [`measurements/queries.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/measurements/queries.json:1).
- Cache comparison: [`cache_comparison.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/cache_comparison.json:1) — 3 checks, 75 input SHA.
- States/trace/controls: [`states.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/measurements/states.json:1), [`trace.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/measurements/trace.json:1), [`controls.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/measurements/controls.json:1).
- Execution record/log: [`native_execution.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/native_execution.json:1), [`native_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/native_run.log:1).
- Runtime query contract/result: [`PALM_JACOBIAN_RUNTIME_CHECK.md`](/home/ajou/yigyu/3/stability_adapter_2/PALM_JACOBIAN_RUNTIME_CHECK.md:23); [`PLAN.md` §45](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:880); [`README.md` runtime summary](/home/ajou/yigyu/3/stability_adapter_2/README.md:154).
- Next proposal path: [PALM_POSITION_CURRENT_PROPOSAL.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_CURRENT_PROPOSAL.md:3), [PALM_POSITION_COMPARISON.md conditions](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_COMPARISON.md:23), calculation [36행](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_COMPARISON.md:36), and pending checklist [65행](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_COMPARISON.md:65). This proposal still awaits confirmation; no controller is implemented.
- Native 계측 구현: [check_palm_jacobian_runtime.py:24](/home/ajou/yigyu/3/stability_adapter_2/check_palm_jacobian_runtime.py:24), [조회·refresh:73](/home/ajou/yigyu/3/stability_adapter_2/check_palm_jacobian_runtime.py:73).
- 저장 cache 분석: [compare_palm_runtime_cache.py:14](/home/ajou/yigyu/3/stability_adapter_2/compare_palm_runtime_cache.py:14).

## 검증

`py_compile`과 canonical CLI, fresh `/tmp` CLI 재생성을 통과했다. Report 9 checks/71 embedded hashes, cache comparison 3 checks/75 hashes, 25 consecutive queries/24 physics steps 및 sample preservation을 확인했다. 최종 `artifacts_validated/` PNG와 fresh `/tmp` 재생성본은 픽셀 단위로 일치한다. t=0 pre-refresh zero buffer는 curve에서 제외하고 저장된 post-step query만 그렸다.
