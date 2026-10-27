# 변경 파일 색인

이번 산출물은 결과 문서와 연속 진단 현황에만 추가했다. 물리 코드, 설정, 원시 실행 자료는 변경하지 않았다.

## 결과와 native 자료

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/README.md) — damping 설정/readback, phase 결과, native 영상과 해석 한계.
- [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/summary.json) — 완료 실행의 phase별 측정값.
- [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/report.json), [PD handoff properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/PD_handoff_properties.json), [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/initial_values.json), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/trace.json).
- Native 영상: [전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/whole_body.mp4), [손 근접](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/hands.mp4). 영상 설정과 검증값은 [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/videos.json) 및 [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/data/images/capture.json)에 기록.
- 입력 보존: [native before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/inputs_before.json), [native after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native/inputs_after.json), [analysis before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/inputs_before.json), [analysis after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis/inputs_after.json).
- [native run log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/native.log), [analysis log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/analysis.log).

## 단계 설계와 코드

- [STRIKE_PLAY_DAMPING_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_PLAY_DAMPING_PLAN.md:1) — 단일 damping 변경의 단계 계획.
- [run_strike_play_damping.py:218](/home/ajou/yigyu/3/stability_adapter_2/run_strike_play_damping.py:218) — PLAY handoff의 9축 native damping 설정/readback.
- [strike_play_damping_preserved_run.py:12](/home/ajou/yigyu/3/stability_adapter_2/strike_play_damping_preserved_run.py:12) — 보존 wrapper 진입점.
