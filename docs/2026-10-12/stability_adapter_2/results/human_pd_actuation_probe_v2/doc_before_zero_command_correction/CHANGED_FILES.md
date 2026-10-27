# 파일 색인

이번 결과 단계에서는 기존 실행의 원자료를 읽어 README에 정리했다. native 재실행, 분석기 변경, 그림 생성은 하지 않았다.

## 이번 결과와 원자료

- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/README.md:1)
- [저장자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis.log)
- OFF [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/report.json:1) · [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/initial_values.json:1) · [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/commands.json:1) · [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/states.json:1)
- ON [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/report.json:1) · [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/initial_values.json:1) · [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/commands.json:1) · [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/states.json:1)
- [보존된 v1 OFF 실패 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v1/off.log) · [실패 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v1/off/data/report.json:1)
- OFF/ON [전신 영상·프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/whole_body.mp4) · [손 영상·프레임 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/hands.mp4)

## 계획·구현 위치

- [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_PD_ACTUATION_PROBE_V2_PLAN.md:1)
- [runner 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_human_pd_actuation_probe_v2.py:15) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/human_pd_probe_preserved_run_v2.py:12) · [저장자료 비교기](/home/ajou/yigyu/3/stability_adapter_2/analyze_human_pd_probe.py:13)
- [메인 PLAN 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:251) · [메인 README 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:1556)
