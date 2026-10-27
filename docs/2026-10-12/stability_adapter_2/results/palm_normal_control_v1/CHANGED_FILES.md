# 변경 파일 인덱스 — palm_normal_control_v1

그림 생성은 검증된 저장 trace와 실제 native camera frame을 사용하며 물리 실행을 추가하지 않는다. 제어 비교와 camera 검증의 전체 실행은 8회 초기화·123 physics steps다.

- [plot_palm_normal_control.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_normal_control.py:35) — 네 조건의 저장 곡선과 camera 비교 panel을 생성한다.
- 재사용한 [camera overlay helper](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_side_feedback.py:56)는 수정하지 않았다.
- [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/README.md:1), [VISUAL_REPORT §59](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1060), [dated results index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:343).
- [저장 측정·검증 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/analysis.json) — 11 checks, 총 8 native initializations / 123 physics steps.
- 원 trace 예: [Full 0.15 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/short/full/trace.json), [Normal 0.30 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/cap_0p3/short/trace.json); README에는 네 조건 전부 표기했다.
- 재사용 camera inputs: [이전 Full 0.15 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/native_tracking/blue_front_024.png), [Normal 0.30 초기 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/native_cap_0p3/blue_front_000.png), [Normal 0.30 종료 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/native_cap_0p3/blue_front_024.png). overlay가 읽는 [source facet 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_distal_search/search.json).
- [metric plot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_curves.png), [camera comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_camera.png).
- 입력·producer·출력 SHA는 [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/plot_manifest.json), 실제 실행 환경/명령/종료 코드는 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/plot_execution.json)과 [plot_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/plot_execution.log)에 있다.
- 첫 시각화 초안은 [artifacts_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts_v1/)에 보존했다. 현재 `artifacts/`가 최종 표시본이다.
- 읽기 전용 설계 맥락: [PALM_NORMAL_CONTROL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_NORMAL_CONTROL_PLAN.md:1).

## 구현·계획 변경

- [법선 방향 오차 계산](/home/ajou/yigyu/3/stability_adapter_2/palm_normal_task.py:8) — 두 면의 법선이 마주 보도록 하고 법선축 회전을 방향 벌점에서 제외한다.
- [저장 응답 재계산](/home/ajou/yigyu/3/stability_adapter_2/fit_palm_normal_response.py:11), [목표각 범위 진단](/home/ajou/yigyu/3/stability_adapter_2/fit_palm_normal_cap.py:13).
- [실제 Isaac Gym 실행](/home/ajou/yigyu/3/stability_adapter_2/run_palm_normal_control.py:16), [원자료 분석·검증](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_normal_control.py:13).
- [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_NORMAL_CONTROL_PLAN.md:16), [메인 상태](/home/ajou/yigyu/3/stability_adapter_2/README.md:547), [메인 계획 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1148).
- [원본 보존 확인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/preservation_check.json) — 기존 87개 파일의 stat와 8월 19일 자료 49개 SHA가 기준과 일치한다.

독립 검수: [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/review.md:7).
