# Palm Jacobian–fresh FK artifact index

이번 작업은23 fresh 초기화의 native FK 계측과 저장 JSON의 좌표 보정·정적 그림·설명이다. Physics rollout0이며 기존 controller/PD/solver/기타 목표는 변경하지 않았다. 독립 검수와 최종 figure/document 확인을 완료했다.

## 산출물

- Plotter: [`plot_palm_fk_coordinates.py`](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_fk_coordinates.py:1) — raw/corrected JSON의 검사·입력 SHA·좌표행 대응을 확인하고 위치값을 m/rad에서 mm/rad로 환산해 그래프를 생성한다.
- 결과 설명 및 표: [`README.md`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/README.md:1).
- Canonical figure: [`palm_fk_coordinate_errors.png`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_validated/palm_fk_coordinate_errors.png) — 세 panel, 로그 축.
- Canonical provenance: [`plot_manifest.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_validated/plot_manifest.json).
- 이전 단위 표시 초안: [`artifacts/`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts/palm_fk_coordinate_errors.png) 및 [`artifacts_v1/`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_v1/palm_fk_coordinate_errors.png). 수정 전 producer는 [`source_plot_attempt/plot_palm_fk_coordinates.py`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/source_plot_attempt/plot_palm_fk_coordinates.py:1)에 보존했으며 그 SHA는 앞선 manifest의 producer SHA와 일치한다.
- 누적 그림 및 해석 제한: [`VISUAL_REPORT.md` §36](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:788).

## 입력 및 상위 기록

- Raw native Jacobian–FD comparison: [`measurements_validated/comparison.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/measurements_validated/comparison.json:1) — 6개 global checks, 12개 row checks, 93 embedded input SHA.
- 좌표 보정 비교: [`coordinate_comparison.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/coordinate_comparison.json:1) — 3개 global checks, 98 embedded input SHA.
- 보존된 계측 이력: [`native_execution.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/native_execution.json:1), [`failed_execution.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/failed_execution.json:1), [`native_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/native_run.log:1), [`native_validated_run.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/native_validated_run.log:1), [`source_attempt/`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/source_attempt/stability_adapter_2/check_palm_jacobian_fk.py:1).
- 계측 범위와 결과: [PALM_JACOBIAN_FK_CHECK.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_JACOBIAN_FK_CHECK.md:29), [PLAN.md §44](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:868), [README.md 초기 FK 요약](/home/ajou/yigyu/3/stability_adapter_2/README.md:148).
- 현재 위치 보정 검토 순서: [PALM_POSITION_CURRENT_PROPOSAL.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_CURRENT_PROPOSAL.md:19) — FK 비교 A 완료; runtime 계측 뒤 task 검토 전 확인 필요.
- Native FK 계측 구현: [check_palm_jacobian_fk.py](/home/ajou/yigyu/3/stability_adapter_2/check_palm_jacobian_fk.py:35), [:89 probe/경계 차분](/home/ajou/yigyu/3/stability_adapter_2/check_palm_jacobian_fk.py:89).
- 좌표 변환과 COM 기준 비교: [compare_palm_fk_coordinates.py](/home/ajou/yigyu/3/stability_adapter_2/compare_palm_fk_coordinates.py:10), [:47 블록 변환](/home/ajou/yigyu/3/stability_adapter_2/compare_palm_fk_coordinates.py:47).

## 검증

Plotter 문법 검사를 통과했다. Raw JSON의 global/row checks 6/12, corrected JSON의 checks 3/3, embedded inputs 93/98 SHA를 확인했다. 최종 `artifacts_validated/` PNG와 새 `/tmp` 재생성본은 픽셀 단위 일치하며 크기는 2520×936이다. 기존 초안과 해당 producer snapshot은 보존했다. 다음은 동일 승인 PI 조건에서 runtime Jacobian 조회와 native 관절/body 속도 대응을 읽기 전용으로 계측하는 단계다. 새 position task·gain·rate-limit 적용 승인은 포함하지 않는다.
