# 결과와 원자료 색인

이번 문서는 승인된 최종 분석을 정리한다. 물리 코드·초기값·native 자료를 변경하거나 새 실행을 하지 않았고, 그림 producer도 추가하지 않았다.

## 최종 비교 입력과 검증

- [최종 비교 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final/summary.json:1) · [비교 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final.log)
- base_v2: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/initial_values.json:1), [report/checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/report.json:1), [checkpoint settings](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/checkpoint_connection.json:1), [inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/inputs_before.json:1), [inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/inputs_after.json:1)
- rate: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/initial_values.json:1), [report/checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/report.json:1), [checkpoint settings](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/checkpoint_connection.json:1), [inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/inputs_before.json:1), [inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/inputs_after.json:1)
- gain_v2: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/initial_values.json:1), [report/checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/report.json:1), [checkpoint settings](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/checkpoint_connection.json:1), [inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/inputs_before.json:1), [inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/inputs_after.json:1)
- [조건별 actual native 영상 metadata/ffprobe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/videos.json:1) · [rate](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/videos.json:1) · [gain_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/videos.json:1)
- [README — 수치표·프레임·6개 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/README.md:1)

## 시도 이력

- 첫 [base import 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base.log)와 [실패한 base 실행의 inputs_after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base/inputs_after.json): Ninja 부재로 import 실패, physics 0회. `analysis_base.log`는 실패 분석이 아니라 base_v2의 깨끗한 분석 로그다. 최종 비교는 base_v2다.
- 첫 [gain 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain.log)와 [closure 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_gain_first.log): 5초 native 기록은 있으나 helper log field 변경으로 closure가 불일치해 최종 비교에서 제외했고, raw는 보존했다. 최종 조건은 gain_v2다.
- [rate 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate.log) · [base_v2 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2.log) · [gain_v2 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2.log)

## 구현 및 계획

- [iteration plan](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_ITERATION_PLAN.md:1)
- [runner main](/home/ajou/yigyu/3/stability_adapter_2/run_strike_transfer_iteration.py:24) · [preserved-run entry](/home/ajou/yigyu/3/stability_adapter_2/strike_transfer_preserved_run.py:12) · [analysis entry](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials.py:9)
- [메인 PLAN 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:200) · [메인 README 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1505)
