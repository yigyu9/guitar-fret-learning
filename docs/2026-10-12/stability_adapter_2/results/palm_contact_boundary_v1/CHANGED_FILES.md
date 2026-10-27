# 변경 및 입력 파일

그림 생성은 저장 자료를 시각화하는 read-only 단계다. 물리 코드·설정·실험 입력은 수정하지 않았다.

- [plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_contact_boundary.py:1) — 저장 분석·trace·contact를 검증하고 4패널 PNG를 생성한다.
- [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/analysis.json:1) — 7개 검사, 새 실행 4 init/96 step, 여섯 α 조건의 요약·곡선.
- 새 실행 raw: [α=.30](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/alpha_30/trace.json:1), [α=.35](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/alpha_35/trace.json:1), [α=.40](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/alpha_40/trace.json:1), [α=.45](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/alpha_45/trace.json:1). 각 run의 `contacts.json`은 동일 디렉터리에 있다.
- 이전 phase의 saved reference raw: [α=.25 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/validation/corrected_quarter/trace.json:1), [α=.50 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/validation/corrected_half/trace.json:1). 원자료는 수정하지 않았다.
- [Canonical plot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/palm_contact_boundary.png), [입출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/plot_manifest.json:1), [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/plot_execution.json:1), [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/plot_execution.log:1).
- 이전 guard 기준 결과는 `artifacts/`, `artifacts_attempt_v1/`, `artifacts_validated_attempt_v1/`에 보존했고 canonical 링크는 최종 7-check analysis 기준이다.

## 분석·계획 및 누적 기록

- [관측 경계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_CONTACT_BOUNDARY_PLAN.md:1)
- [분석·alpha/실제목표 검증](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_contact_boundary.py:19)
- 새 입력: [alpha30](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_contact_boundary_v1/alpha_30.json:1), [alpha35](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_contact_boundary_v1/alpha_35.json:1), [alpha40](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_contact_boundary_v1/alpha_40.json:1), [alpha45](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_contact_boundary_v1/alpha_45.json:1), [manifest](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_contact_boundary_v1/manifest.json:1)
- [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/execution.json:1), [분석 실행·보완 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/analysis_execution.json:1)
- 누적 기록: [메인 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:609), [메인 계획 진행](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1198), [결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:367), [그림88 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1147).

최종 보존: [source snapshot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/source_final_manifest.json:1), [전체 산출물 절대경로·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifact_inventory.json:1).
