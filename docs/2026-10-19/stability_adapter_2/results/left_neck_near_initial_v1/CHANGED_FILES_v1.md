# 이번 작업의 변경·추가 파일과 실제 줄 번호

기존 파일은 원문 스냅샷을 남기고 메인 문서에 추가만 했다. 소비된 source/실패/이전 출력은 보존했으며 새 실험은 각 버전의 새 파일·폴더를 썼다. 아래 줄은 현재 실제 1기반 줄이다.

## 현재 검토할 입력과 실행

- [현재 실행 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/config_v1/config.json:3)
- [현재81 초기각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/search_v5/station20mm/candidate.json:85)
- [네크 면·초기 후보 진단](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/search_v5/station20mm/candidate.json:1509)
- [현재 녹화 runner](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v5.py:26)
- [양 정책 추론·목표 합성](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v5.py:242)
- [준비용 손목 위치 보정](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:33)
- [24 EFFORT·57 POSITION 설정과 단일 명령](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v2.py:36)
- [최신 원자료 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_near_v3.py:1)

## 구현·계획 원본과 소비 이력

- [LEFT_NECK_NEAR_INITIAL_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_COMPLETION_V1.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V1.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V2.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V2.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V3.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V3.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V4.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V4.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V5.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V5.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V6.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V6.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V7.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V7.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V8.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V8.md:1)
- [LEFT_NECK_NEAR_INITIAL_PLAN_V9.md](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V9.md:1)
- [left_neck_near_geometry_v1.py](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:1)
- [search_left_neck_near_v1.py](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v1.py:1)
- [search_left_neck_near_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v2.py:1)
- [search_left_neck_near_v3.py](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v3.py:1)
- [search_left_neck_near_v4.py](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v4.py:1)
- [search_left_neck_near_v5.py](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v5.py:1)
- [run_left_neck_near_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v1.py:1)
- [run_left_neck_near_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v2.py:1)
- [run_left_neck_near_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v3.py:1)
- [run_left_neck_near_v4.py](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v4.py:1)
- [run_left_neck_near_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v5.py:1)
- [left_near_scene_v1.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_scene_v1.py:1)
- [left_near_scene_v2.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_scene_v2.py:1)
- [left_near_scene_v3.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_scene_v3.py:1)
- [left_near_arm_effort_v1.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:1)
- [left_near_arm_effort_v2.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v2.py:1)
- [left_near_arm_effort_v3.py](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v3.py:1)
- [analyze_left_neck_near_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_near_v1.py:1)
- [analyze_left_neck_near_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_near_v2.py:1)
- [analyze_left_neck_near_v3.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_near_v3.py:1)

## 메인 문서의 원문 보존과 추가

- [추가 문단](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1181) · [추가 전 원문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/A_PLAN_before_append_v1.md:1)
- [추가 문단](/home/ajou/yigyu/3/stability_adapter_2/README.md:2273) · [추가 전 원문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/A_README_before_append_v1.md:1)
- [추가 문단](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/README.md:106) · [추가 전 원문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/D_README_before_append_v1.md:1)

## 이번 결과·산출물·검수

- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/README.md:1)
- [native_analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_analysis_v2.json:1)
- [native_analysis_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_analysis_v3.json:1)
- [ANALYSIS_NOTES_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/ANALYSIS_NOTES_V1.md:1)
- [navigation_update_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/navigation_update_v1.json:1)
- [source_v1_interrupted.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/source_v1_interrupted.json:1)
- [source_v2_interrupted.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/source_v2_interrupted.json:1)
- [runner_source_copy_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/runner_source_copy_v1.json:1)
- [runner_preflight_version_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/runner_preflight_version_v1.json:1)
- [artifacts_v1/README_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/README_V1.md:1)
- [artifacts_v1/README_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/README_V2.md:1)
- [artifacts_v1/build_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/build_archive_v1.py:1)
- [artifacts_v1/build_archive_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/build_archive_v2.py:1)
- [artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/provenance_v1.json:1)
- [artifacts_v1/provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/provenance_v2.json:1)
- [review_native_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_native_v1.md:1)
- [review_preflight_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v1.md:1)
- [review_preflight_v2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v2.md:1)
- [review_preflight_v3.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v3.md:1)
- [review_preflight_v4.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v4.md:1)
- [review_preflight_v5.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v5.md:1)
- [review_preflight_v6.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v6.md:1)
- [review_preflight_v7.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v7.md:1)
- [review_preflight_v8.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v8.md:1)
- [전체10개 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/INDEX_V1.md:1)
- [원본·사본 SHA/실제 길이](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json:1)

최종 검수·보존 감사는 root 봉인 실행 이후 생성한다. 아직 없는 파일의 링크는 만들지 않는다.

- [보존 감사 소스](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/seal_outputs_v1.py:1)
