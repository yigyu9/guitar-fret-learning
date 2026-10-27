# 변경 파일 인덱스 — `left_distal_initial_v1`

이 인덱스는 2026-10-07 결과 문서와 저장 trace 산출물의 경로를 묶는다. 물리 판단과 trial 실행은 부모가 소유했으며, 이번 산출물 작업은 재생성 가능한 표·그림 문서화에 한정한다.

## 결과와 계획 문서

- 결과 단계 계획: [/home/ajou/yigyu/3/stability_adapter_2/LEFT_DISTAL_INITIAL_COMPARE.md:28](/home/ajou/yigyu/3/stability_adapter_2/LEFT_DISTAL_INITIAL_COMPARE.md:28).
- 프로젝트 진행 기록: [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:810](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:810).
- 프로젝트 안내 연결: [/home/ajou/yigyu/3/stability_adapter_2/README.md:115](/home/ajou/yigyu/3/stability_adapter_2/README.md:115).
- 이 결과의 입력 검사 표와 source 한계: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:5); 18개 저장 ON run 표: [README.md:23](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:23); 판정·제약·다음 승인범위: [README.md:50](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:50); 재생성 명령: [README.md:56](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:56).
- 누적 시각 보고서 §31 / 그림 44: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:730](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:730); [그림 링크: VISUAL_REPORT.md:736](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:736).

## 입력·실행·재사용 도구

- 9개 초기 설정 입력: [l_elbow_x_minus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_elbow_x_minus025.json:1), [l_elbow_x_plus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_elbow_x_plus025.json:1), [l_elbow_y_minus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_elbow_y_minus025.json:1), [l_elbow_y_plus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_elbow_y_plus025.json:1), [l_wrist_x_minus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_wrist_x_minus025.json:1), [l_wrist_x_plus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_wrist_x_plus025.json:1), [l_wrist_y_minus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_wrist_y_minus025.json:1), [l_wrist_y_plus025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/l_wrist_y_plus025.json:1), [reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_distal_initial_v1/reference.json:1).
- 입력 검사 자료: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/initial_inputs.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/initial_inputs.json:1), `initial_audit.log:1`, `initial_audit_command.json:1`.
- 비교·판정 자료: `comparison.json:1` (18개 ON run 및 embedded SHA), `comparison_short.json:1`, `decision.json:1`, `reference_link_manifest.json:1`, `native_selection.json:1`, `late_selection.json:1`, `off_selection.json:1`은 위 결과 디렉터리에 보존한다.
- 실행 기록: `short_commands.json:1` / `short_execution.json:1`, `hold_05s_commands.json:1` / `hold_05s_execution.json:1`, `hold_1s_commands.json:1` / `hold_1s_execution.json:1`, 각 그룹의 `*_reference.log:1` 및 다섯 후보 `*.log:1`은 결과 디렉터리에 보존한다.
- 원 실행자료: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/{short,hold_05s,hold_1s}/{reference,l_elbow_x_minus025,l_elbow_y_plus025,l_wrist_x_plus025,l_wrist_y_minus025,l_wrist_y_plus025}/{report,trace,states,contacts,controls,leg_torques}.json:1`. 각 그룹은 기준 1개와 통과 후보 5개의 저장 자료를 담는다.
- 재사용 도구는 수정하지 않았다: [/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:1](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:1), [/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:1](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:1), [/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py:1](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py:1).

## 이 산출물과 검증 상태

- PNG: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/left_distal_initial_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/left_distal_initial_v1.png).
- provenance manifest: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/plot_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/plot_manifest.json:1). Embedded input 198개 경로의 SHA-256 일치가 확인됐다.
- plot은 이미 저장된 입력만 읽었다. 기존 canonical PNG와 빈 `/tmp/left_distal_initial_luna_reproduction` 출력에서 지원 CLI로 다시 만든 PNG는 크기와 RGBA pixel이 일치했다. 추가 native 실행은 없다.
- 독립 통합 검수 완료·동결: [review.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/review.md:7), [최종 미디어 확인:36](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/review.md:36).
- 최종 보존·검증: [source_final_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/source_final_manifest.json:1), [verification.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/verification.json:1), [file_inventory.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/file_inventory.json:1). 원자료·로그·보존본 각 파일의 절대 경로와 첫 줄은 inventory에 수록한다.
