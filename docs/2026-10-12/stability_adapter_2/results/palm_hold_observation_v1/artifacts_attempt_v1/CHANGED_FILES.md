# 파일 인덱스

이 후처리 단계에서 새로 추가한 그림 producer와 그 산출물, 비교 대상의 핵심 원자료를 가리킨다. 물리 코드, 설정, 분석 결과, 기존 실행 자료는 수정하지 않았다.

|경로|설명|
|---|---|
|[plot_palm_hold_observation.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_observation.py:1)|저장 분석·observer force·native trace/controls를 그리는 plot producer; native 실행 없음|
|[README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/README.md:1)|두 축의 좌표/force 비교 및 관측 범위 설명|
|[palm_hold_observation.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts/palm_hold_observation.png)|2×2 native scalar coordinate/total-DOF-force 시계열 그림|
|[plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts/plot_manifest.json)|입력 10개, producer 및 PNG의 SHA-256|
|[plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts/plot_execution.json)|실행 명령, 환경, Python 및 종료 코드|
|[plot.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts/plot.log)|plot 실행 출력|
|[analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/analysis.json:1)|5개 분석 검사와 2조건 결과|
|[baseline observation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/baseline/observation.json:1), [full observation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/full/observation.json:1)|24 완료-step native total DOF force 표본과 native property readback|
|[PALM_HOLD_PD_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_PLAN.md)|후속 PD 비교 계획 경로; 별도 소유 문서|
