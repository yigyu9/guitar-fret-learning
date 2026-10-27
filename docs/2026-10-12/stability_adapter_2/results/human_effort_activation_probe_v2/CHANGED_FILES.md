# 변경 파일 색인

이번 결과 정리는 문서와 연속 진단 현황에만 추가했다. 물리 설정, runner, analyzer, 원시 측정 자료와 기존 결과는 수정하지 않았다.

## 이번 결과 문서

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/README.md) — 실험 범위, OFF/ON 비교, 저장 영상과 한계.
- [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/summary.json) — 저장 상태 비교 결과.
- [analysis log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis.log) — 저장자료 분석 실행 로그.

## 실행 코드와 계획

- [HUMAN_EFFORT_ACTIVATION_PROBE_V2_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_EFFORT_ACTIVATION_PROBE_V2_PLAN.md:1) — 단계 계획.
- [run_human_effort_activation_probe_v2.py:15](/home/ajou/yigyu/3/stability_adapter_2/run_human_effort_activation_probe_v2.py:15) — native trial 진입점; EFFORT 설정과 첫 네 physics step은 26–59행, PD 복원과 저장 종료는 66–85행.
- [human_effort_probe_v2_preserved_run.py:12](/home/ajou/yigyu/3/stability_adapter_2/human_effort_probe_v2_preserved_run.py:12) — 보존 wrapper 진입점; 입력 봉인과 runner 호출은 20행 이후.
- [analyze_human_effort_probe.py:13](/home/ajou/yigyu/3/stability_adapter_2/analyze_human_effort_probe.py:13) — 저장자료 비교 진입점; 상태 비교 및 요약 작성은 18행 이후.

## 원자료

- OFF: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/report.json), [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/initial_values.json), [native EFFORT readback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/native_EFFORT_PD_properties.json), [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/commands.json), [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/states.json), [initial mass matrix](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/mass_matrix_initial.json), [run log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off.log).
- ON: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/report.json), [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/initial_values.json), [native EFFORT readback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/native_EFFORT_PD_properties.json), [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/commands.json), [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/states.json), [initial mass matrix](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/mass_matrix_initial.json), [run log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on.log).
- Analysis input closure: [before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/inputs_after.json).
