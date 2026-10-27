# 산출물 및 입력 인덱스

이 인덱스는 probe 생성기·분석기·plotter와 결과 경로를 함께 기록한다. Luna 산출물 제작 단계에서는 원자료, 물리 설정, 분석 JSON을 수정하지 않았다.

- [Plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_coupled_response.py:1) — 입력 SHA 봉인 후 14개 run의 report/trace/tasks/contacts를 검증하고 summary plot을 생성한다.
- [Probe 생성기](/home/ajou/yigyu/3/stability_adapter_2/generate_palm_coupled_probes.py:16) — saved α=.45 기준으로 12축 probe/heldout trial 입력을 생성한 코드.
- [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_coupled_response.py:15) — run 계약과 입력 SHA를 검사하고 결과를 산출한다; [12×12 terminal response 구성](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_coupled_response.py:56).
- [응답 분석 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_RESPONSE_PLAN.md:1), [다음 coupled correction 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1).
- [Analysis](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/analysis.json:1) — 6개 검사, 14 init/336 steps, 12×12 response 및 heldout 비교.
- Baseline: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/baseline/report.json:1), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/baseline/trace.json:1).
- 12개 axis probe: 각 `axis_00`–`axis_11` 디렉터리에 report/trace/tasks/contacts 원자료 저장; 예: [axis_00 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_00/report.json:1), [axis_11 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_11/trace.json:1).
- Heldout: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/heldout/report.json:1), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/heldout/trace.json:1).
- [Figure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/palm_coupled_response.png), [input/output SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/plot_manifest.json:1), [execution metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/plot_execution.json:1), [execution log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/plot_execution.log:1).
- Earlier first-render draft preserved at [artifacts_attempt_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts_attempt_v1/); canonical output is `artifacts/`.

## 입력과 누적 기록

- [14개 trial 입력 manifest](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/manifest.json:1), [baseline 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/baseline.json:1), [heldout 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/heldout.json:1). 단일축 입력은 같은 디렉터리 axis_00.json–axis_11.json이다.
- [native 실행 명령·종료 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/execution.json:1), [분석 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/analysis_execution.json:1).
- 누적 기록: [메인 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:609), [메인 계획 진행](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1198), [결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:367), [그림89 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1164).

### 관절별 입력 절대경로

- [baseline.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/baseline.json:1)
- [axis_00.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_00.json:1)
- [axis_01.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_01.json:1)
- [axis_02.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_02.json:1)
- [axis_03.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_03.json:1)
- [axis_04.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_04.json:1)
- [axis_05.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_05.json:1)
- [axis_06.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_06.json:1)
- [axis_07.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_07.json:1)
- [axis_08.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_08.json:1)
- [axis_09.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_09.json:1)
- [axis_10.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_10.json:1)
- [axis_11.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/axis_11.json:1)
- [heldout.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_response_v1/heldout.json:1)

최종 보존: [source snapshot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/source_final_manifest.json:1), [전체 산출물 절대경로·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifact_inventory.json:1).
