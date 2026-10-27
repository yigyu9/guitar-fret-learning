# 변경 파일·입력 색인

## 조건·계획

- [LOWER_BODY_FIXED_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/LOWER_BODY_FIXED_PLAN.md:1): 사용자 조건과 검증 단계.
- [README.md:10](/home/ajou/yigyu/3/stability_adapter_2/README.md:10), [PLAN.md §58:1049](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1049), [EXPERIMENT_WORKFLOW.md:20](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:20): 현재 하체 고정 조건 및 작업 규칙.
- [build_fixed_lower_asset.py:36](/home/ajou/yigyu/3/stability_adapter_2/build_fixed_lower_asset.py:36), [fixed_lower_environment.py:1](/home/ajou/yigyu/3/stability_adapter_2/fixed_lower_environment.py:1), [run_fixed_lower.py:13](/home/ajou/yigyu/3/stability_adapter_2/run_fixed_lower.py:13): 하체 고정 자산·실행 경로.
- [humanoid_fixed_lower.xml:1](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:1), [humanoid_fixed_lower.json:1](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.json:1): 실행 자산 및 해시 manifest.

## 실행 입력과 검증

- [selection.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/selection.json:1), [full_run_candidates.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_run_candidates.json:1), [selection_inputs_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/selection_inputs_manifest.json:1): 단일 full run 기록 및 원자료 SHA-256.
- 원자료: [report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/report.json:1), [states.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/states.json:1), [trace.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/trace.json:1), [controls.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/controls.json:1), [contacts.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/contacts.json:1), [leg_torques.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/leg_torques.json:1).
- [native_execution_summary.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/native_execution_summary.json:1), [preservation_verification.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/preservation_verification.json:1): native 실행과 보존 검증.
- [short_v4/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/short_v4/report.json:1), [short_v4_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/short_v4_execution.log), [full_1s_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s_execution.log): 단기·전체 실행 기록.
- 실패 기록 보존: [failed_absolute_meshdir/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/failed_absolute_meshdir/), [failed_float32_angle/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/failed_float32_angle/), [short_v3/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/short_v3/).

## 재생과 결과 설명

- [render_fixed_lower_video.py:1](/home/ajou/yigyu/3/stability_adapter_2/render_fixed_lower_video.py:1), [render_best_run_video.py:139](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py:139): 조건에 맞는 footer wrapper와 기존 저장-pose renderer.
- Canonical output [render_v2/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/): [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_manifest.json), [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_execution.json), [로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_execution.log).
- 첫 영상 세트는 [render_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/)에 byte-for-byte 보존했으며 old footer의 `False` 표시는 원 report의 null과 불일치해 canonical이 아니다. [relocation_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/relocation_manifest.json)은 기존 manifest/파일 SHA와 이전·보존 경로를 연결한다.
- [README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/README.md:1), [VISUAL_REPORT.md §50:938](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:938): 영상, 조건, 수치와 해석 범위.

별도 change-reviewer의 최종 검수는 완료했다. [검토 결과](review.md:7)에 남은 finding이 없다.


## 마감·보존 기록

- [결과 메인 색인:286](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:286), [review.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/review.md:7): 현재 조건 안내와 독립 검수.
- [source_final_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/source_final_manifest.json:1), [verification.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/verification.json:1), [inventory.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/inventory.json:1): 실행 producer·계획·문서 사본, 마감 검증과 산출물 목록.
