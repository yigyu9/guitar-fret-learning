# right_elbow_wrist_combo_v1 변경·결과 인덱스

고정한 오른손 손목 자세에서 팔꿈치 X를 조정한 세 입력의 source 및 저장 trace 비교 인덱스다. 이번 산출물 작업은 기존 도구만 읽기 전용으로 재사용했고 설정·제어 코드를 바꾸지 않았다.

## 계획·설정·문서

- 계획 및 판정: [RIGHT_ELBOW_WRIST_COMBO.md:29](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ELBOW_WRIST_COMBO.md:29)
- 기준 입력: [reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_elbow_wrist_combo_v1/reference.json:1)
- 팔꿈치 X −0.0025 rad: [elbow_x_minus0025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_elbow_wrist_combo_v1/elbow_x_minus0025.json:1)
- 팔꿈치 X −0.005 rad: [elbow_x_minus0050.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_elbow_wrist_combo_v1/elbow_x_minus0050.json:1)
- PLAN §38: [PLAN.md:797](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:797)
- 프로젝트 README: [README.md:108](/home/ajou/yigyu/3/stability_adapter_2/README.md:108)
- 누적 VISUAL_REPORT §30: [VISUAL_REPORT.md:720](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:720)
- 초기각/source proxy 표: [결과 README:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md:5)
- 오차 표: [결과 README:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md:13)
- 그림 및 판정: [결과 README:27](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md:27), [결과 README:29](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md:29)
- 재현 CLI와 새 출력 경로: [결과 README:33](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md:33)
- 별도 검수 완료·동결: [review.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/review.md:7), [최종 미디어 검수:45](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/review.md:45).

기존 [audit_arm_initial_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py), [compare_arm_initial_trials.py](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py), [plot_saved_arm_trials.py](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py)는 재사용했고 수정하지 않았다.

## 원자료 및 출력

- Canonical 9-run 비교 및 판정: [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/comparison.json), [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/decision.json)
- 입력 감사 및 선택: [initial_audit.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/initial_audit.log), [native_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/native_selection.json), [late_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/late_selection.json), [off_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/off_selection.json)
- 이전 wrist reference 원본: [reference_links](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/reference_links), [reference_link_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/reference_link_manifest.json)
- 세 기간 run: `short/`, `hold_05s/`, `hold_1s/` 아래 `reference/`, `elbow_x_minus0025/`, `elbow_x_minus0050/`에 report·trace·states·contacts·controls·leg_torques JSON과 commands/execution·로그가 있다. OFF run은 없다.
- 그림과 provenance: [right_elbow_wrist_combo_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/right_elbow_wrist_combo_v1.png), [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/plot_manifest.json)
- 초기3건 검사·명령: [initial_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/initial_inputs.json:1), [initial_audit_command.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/initial_audit_command.json:1).
- 최종 보존·검증 파일: [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/source_final_manifest.json:1), [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/verification.json:1), [file_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/file_inventory.json:1). 전체 원자료 파일의 절대 경로와 첫 줄은 inventory에 수록한다.
