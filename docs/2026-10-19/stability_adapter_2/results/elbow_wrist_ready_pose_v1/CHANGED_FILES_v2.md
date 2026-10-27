# 변경 파일과 실제 줄 번호

새 준비 자세 구현과 이번 실행·분석·문서만 기록합니다. 기존stability_adapter/공용자산/실험소비 원본은 유지했습니다. 실패·미실행 버전도 검토 이력으로 보존합니다.

## 계획·구현

- [ELBOW_WRIST_READY_CONTROL_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_CONTROL_PLAN_V2.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V2.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V2.md`, 실제 1줄.
- [ELBOW_WRIST_READY_CONTROL_PLAN_V3.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V3.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V3.md`, 실제 1줄.
- [ELBOW_WRIST_READY_DEPTH_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_DEPTH_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_DEPTH_PLAN_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_PICK_FEEDBACK_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_PICK_FEEDBACK_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_PICK_FEEDBACK_PLAN_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_POSE_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_COMPLETION_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_COMPLETION_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_POSE_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_POSE_PLAN_V2.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V2.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V2.md`, 실제 1줄.
- [ELBOW_WRIST_READY_POSE_PLAN_V3.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V3.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_PLAN_V3.md`, 실제 1줄.
- [ELBOW_WRIST_READY_TIMING_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_TIMING_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_TIMING_PLAN_V1.md`, 실제 1줄.
- [ELBOW_WRIST_READY_VELOCITY_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_VELOCITY_PLAN_V1.md:1) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_VELOCITY_PLAN_V1.md`, 실제 1줄.
- [analyze_elbow_wrist_ready_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v1.py:11) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v1.py`, 실제 11줄.
- [analyze_elbow_wrist_ready_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v2.py:11) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v2.py`, 실제 11줄.
- [audit_elbow_wrist_ready_commands_v1.py](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v1.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v1.py`, 실제 9줄.
- [audit_elbow_wrist_ready_commands_v2.py](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v2.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v2.py`, 실제 9줄.
- [audit_elbow_wrist_ready_depth_v1.py](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_depth_v1.py:13) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_depth_v1.py`, 실제 13줄.
- [audit_elbow_wrist_ready_path_v1.py](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_path_v1.py:13) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_path_v1.py`, 실제 13줄.
- [diagnose_elbow_wrist_tracking_v1.py](/home/ajou/yigyu/3/stability_adapter_2/diagnose_elbow_wrist_tracking_v1.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/diagnose_elbow_wrist_tracking_v1.py`, 실제 9줄.
- [run_elbow_wrist_ready_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v1.py`, 실제 9줄.
- [run_elbow_wrist_ready_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v2.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v2.py`, 실제 9줄.
- [run_elbow_wrist_ready_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v3.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v3.py`, 실제 9줄.
- [run_elbow_wrist_ready_v4.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v4.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v4.py`, 실제 9줄.
- [run_elbow_wrist_ready_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py`, 실제 9줄.
- [run_elbow_wrist_ready_v6.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v6.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v6.py`, 실제 9줄.
- [run_elbow_wrist_ready_v7.py](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:9) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py`, 실제 9줄.
- [search_elbow_wrist_ready_pose_v1.py](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v1.py:30) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v1.py`, 실제 30줄.
- [search_elbow_wrist_ready_pose_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v2.py:31) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v2.py`, 실제 31줄.
- [search_elbow_wrist_ready_pose_v3.py](/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py:31) — 절대경로 `/home/ajou/yigyu/3/stability_adapter_2/search_elbow_wrist_ready_pose_v3.py`, 실제 31줄.

## 메인 안내 갱신

- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1272) — 앞내용 보존 후 추가, 실제 1272줄.
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2362) — 앞내용 보존 후 추가, 실제 2362줄.
- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/README.md:195) — 앞내용 보존 후 추가, 실제 195줄.

## 결과·미디어 생성과 색인

- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/README.md:1) — 실제 1줄.
- [analysis_v4.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/analysis_v4.json:1) — 실제 1줄.
- [command_audit_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/command_audit_v2.json:1) — 실제 1줄.
- [tracking_diagnostic_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/tracking_diagnostic_v1.json:1) — 실제 1줄.
- [build_artifacts_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/build_artifacts_v1.py:1) — 실제 1줄.
- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/README.md:1) — 실제 1줄.
- [build_artifacts_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/build_artifacts_v2.py:1) — 실제 1줄.
- [README_v2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/README_v2.md:1) — 실제 1줄.
- [INDEX_v2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/INDEX_v2.md:1) — 실제 1줄.

검수·전체SHA 봉인 문서는 최종 검사 후 별도 생성합니다. native_initial/원로그/형상정의/PNG/MP4는 각 실행 디렉토리와 전체영상 색인에서 찾을 수 있습니다.

## 최종 보충 문서와 보존 감사

- [repair_links_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v3/repair_links_v1.py:1) — 새 파일, 실제 1줄.
- [repair_links_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v3/repair_links_v2.py:1) — 새 파일, 실제 1줄.
- [README_v3.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v3/README_v3.md:1) — 새 파일, 실제 1줄.
- [FINAL_VERIFICATION_NOTE_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/FINAL_VERIFICATION_NOTE_v1.md:1) — 새 파일, 실제 1줄.
- [FINAL_VERIFICATION_NOTE_v2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/FINAL_VERIFICATION_NOTE_v2.md:1) — 새 파일, 실제 1줄.
- [seal_outputs_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/seal_outputs_v1.py:1) — 새 파일, 실제 1줄.

repair_links_v1의 검사 중단도 원본으로 보존했습니다. 실제 완료 링크 보완은 repair_links_v2의 새 README_v3와 FINAL_VERIFICATION_NOTE_v2를 사용합니다.
