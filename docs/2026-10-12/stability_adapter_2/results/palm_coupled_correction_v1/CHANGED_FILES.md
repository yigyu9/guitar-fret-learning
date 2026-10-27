# 파일 인덱스

그림 생성 단계에서 추가한 파일과 이번 비교를 재현하는 핵심 경로를 정리한다. 기존 실행 raw와 root 소유의 분석·계획 코드는 수정하지 않았다.

|파일|내용|
|---|---|
|[plot_palm_coupled_correction.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_coupled_correction.py:1)|저장된 trace/contact와 검증된 analysis를 읽는 4패널 plot producer; native 실행 없음|
|[palm_coupled_correction.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifacts/palm_coupled_correction.png)|기타 위치·회전, source normal gap, raw palm λ 시계열|
|[plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifacts/plot_manifest.json)|실제 입력·producer·그림 SHA-256|
|[plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifacts/plot_execution.json)|plot 실행 명령, 환경, 종료 코드와 해시 기록|
|[analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/analysis.json:1)|5개 분석 검사와 3조건 비교 결과|
|[fit_palm_coupled_correction.py](/home/ajou/yigyu/3/stability_adapter_2/fit_palm_coupled_correction.py:16)|12축 국소 응답 보정 추정기|
|[analyze_palm_coupled_correction.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_coupled_correction.py:15)|저장 raw와 fit 비교 분석기|
|[run_palm_finite_response.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_finite_response.py:16)|저장된 quarter/half/full 조건 실행기|
|[PALM_COUPLED_CORRECTION_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1)|조건과 범위를 정한 계획|
|[PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1216)|상위 단계 계획 연결|
|[README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:621)|프로젝트 현재 단계 안내|

Native 저장 결과는 이전 기준 실행 [baseline](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/baseline)과 이번 [quarter](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/quarter), [half](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/half), [full](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/full) 자료에 있다. 검증된 재계산 fit은 [fit_verified_v2/fit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/fit_verified_v2/fit.json:1)이며 원래 fit과 실행 자료는 별도 보존되어 있다.

## 구현과 실행 기록

- [목표 보정 원계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1)
- [다음 관절 유지 관측 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_OBSERVATION_PLAN.md:1)
- [분석 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/analysis_execution.json:1)
- [fit/refit 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/fit_execution.json:1)
- [원fit·verified refit 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/fit_verification.json:1)
- [native 명령·종료 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/execution.json:1)
- [관절·접촉 관측 근거](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/hold_observation_seed.json:1)
- [누적 결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:379)
- [그림90 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1189)

### 실제 native trial 입력

- [quarter.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_correction_v1/quarter.json:1)
- [half.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_correction_v1/half.json:1)
- [full.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_correction_v1/full.json:1)
- [manifest.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_coupled_correction_v1/manifest.json:1)

입력소비시점을보완한fit_verified_v2의세trial/manifest는재계산기록용이며native재실행하지않았다. 원native는위quarter/half/full 입력을사용했다.

최종 보존: [source snapshot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/source_final_manifest.json:1), [전체 산출물 절대경로·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifact_inventory.json:1), [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/review.md:7).
