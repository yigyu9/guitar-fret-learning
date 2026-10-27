# 파일 인덱스

이 후처리 단계에서 새로 추가한 그림 producer와 그 산출물, 비교 대상의 핵심 원자료를 가리킨다. 물리 코드, 설정, 분석 결과, 기존 실행 자료는 수정하지 않았다.

|경로|설명|
|---|---|
|[plot_palm_hold_observation.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_hold_observation.py:1)|저장 분석·observer force·native trace/controls를 그리는 plot producer; native 실행 없음|
|[README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/README.md:1)|두 축의 좌표/force 비교 및 관측 범위 설명|
|[palm_hold_observation.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2/palm_hold_observation.png)|2×2; 기준 .45 bias와 전체 목표 보정의 native scalar coordinate/total-DOF-force 시계열|
|[plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2/plot_manifest.json)|입력 10개, producer 및 PNG의 SHA-256|
|[plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2/plot_execution.json)|실행 명령, 환경, Python 및 종료 코드|
|[plot.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2/plot.log)|plot 실행 출력|
|[analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/analysis.json:1)|5개 분석 검사와 2조건 결과|
|[baseline observation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/baseline/observation.json:1), [full observation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/full/observation.json:1)|둘 다 sensor 추가 조건; 기준은 .45 bias, full은 전체 목표 보정이며 각자의 기존 sensor 없는 5 raw 배열과 일치|
|[PALM_HOLD_PD_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_PD_PLAN.md:1)|후속 PD 비교 계획; 별도 소유 문서|
|[artifacts_attempt_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_attempt_v1)|이전 producer, 그림, manifest, 실행 기록, README, 인덱스의 라벨 수정 전 보존본|


[artifacts_attempt_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_attempt_v1)는 이전 producer, 그림, manifest, 실행 기록, README, 파일 인덱스를 보존한 라벨 수정 전 산출물이다. 새 canonical 그림은 [artifacts_v2/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2)에 있다.
