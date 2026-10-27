# 산출물 파일 인덱스

- [곡선 plotter](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_side_strap.py:123): 저장된 trace/task/contact/report와 기존 camera capture를 읽는다.
- [결과 설명·비교표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/README.md:1)
- [곡선 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_curves.png)
- [기존 native camera frame overlay 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_camera.png)
- [plot 입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/plot_manifest.json)
- [plot 명령·환경·종료 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/plot_execution.json) 및 [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/plot_execution.log)
- [검증된 요약 데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/analysis.json:1), [SHA에 포함된 source overlay helper](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_side_feedback.py:1), [facet 추적점 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_distal_search/search.json:1)
- 기존 입력 예시: [current trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/current/short/trace.json:1), [10 N 초기 camera capture report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/native_initial_10n/report.json:1)
- [누적 시각 결과 §61, 그림 80–81](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1084) 및 [날짜별 결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:351)
- provenance 보완 전 producer/그림/manifest/실행 기록은 [producer_initial](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/producer_initial/plot_palm_side_strap.py)과 [artifacts_initial](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts_initial/plot_manifest.json)에 보존했다. Helper SHA를 포함한 후속 plot attempt는 [artifacts_helper_sha_attempt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts_helper_sha_attempt/plot_manifest.json)에 보존했고, canonical 경로는 위의 `artifacts/`다.

분석값과 원본 run은 수정하지 않았다. 첫 시도에서 `MUJOCO_GL`이 설정되지 않아 plot import가 실패했으며, `MUJOCO_GL=disable`로 저장 데이터 후처리를 다시 실행해 성공했다. 이는 post-processing 실패였고 native 실행이나 physics step 실패가 아니다. 독립 검수는 완료됐으며 남은 지적은 없다.

## 구현·계획 변경

- [실제 Gym·고정 절대 길이 비교 runner](/home/ajou/yigyu/3/stability_adapter_2/run_palm_side_strap.py:17).
- [원자료·수동 장력·접촉 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_side_strap.py:13).
- [소단계 계획·체크리스트](/home/ajou/yigyu/3/stability_adapter_2/PALM_SIDE_STRAP_PLAN.md:1), [메인 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:576), [메인 PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1168).
- [네 후보의 관절각·절대 길이 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_side_strap_v1/candidates.json:1). 각 항목의 settings 경로에 실제 초기각과 LA가 기록돼 있다.
- [분석 보완 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/analysis_execution_v2.json) — 두 보존 inventory를 입력 SHA에 포함했다. 첫 분석·producer는 analysis_initial/에 보존했고 수치·실행 수는 같다.
- [원본 보존 확인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/preservation_check.json).
- [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/review.md).

- [반복 누락 방지를 위한 입력 봉인 지침](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:98).
