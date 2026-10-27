# 변경 파일과 실제 줄 번호

절대 경로와 실제 1-based 줄이다. 이번에는 기존 실행·검사·시각화 코드를 재사용했다.

| 파일·줄 | 역할 |
|---|---|
| [/home/ajou/yigyu/3/stability_adapter_2/NEGATIVE_POSE_LATE_DIAGNOSTIC.md:25](/home/ajou/yigyu/3/stability_adapter_2/NEGATIVE_POSE_LATE_DIAGNOSTIC.md:25) | 계획·실행 결과·다음 진단 기준 |
| [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:726](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:726) | 메인 계획33절 |
| [/home/ajou/yigyu/3/stability_adapter_2/README.md:76](/home/ajou/yigyu/3/stability_adapter_2/README.md:76) | 현재 진단 기준과 다음 조합 |

## 초기 입력과 원본 provenance

- [/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/elbow_y_minus00125.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/elbow_y_minus00125.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/reference.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/wrist_minus0025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/wrist_minus0025.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/wrist_minus0050.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/negative_pose_late_v1/wrist_minus0050.json:1)

## 재사용 코드 (이번에 변경하지 않음)

- [/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:26](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:26)
- [/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:24](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:24)
- [/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py:19](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py:19)
- [/home/ajou/yigyu/3/stability_adapter_2/run_joint_hold.py:57](/home/ajou/yigyu/3/stability_adapter_2/run_joint_hold.py:57)
- [/home/ajou/yigyu/3/stability_adapter_2/joint_hold_residual.py:1](/home/ajou/yigyu/3/stability_adapter_2/joint_hold_residual.py:1)

## 검사·실행·선정 기록

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/input_recipe.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/input_recipe.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/initial_inputs.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/initial_inputs.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/native_selection.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/native_selection.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison_short.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison_short.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/late_selection.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/late_selection.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison_on.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison_on.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off_selection.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off_selection.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/comparison.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/decision.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/decision.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short_commands.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short_commands.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s_commands.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s_commands.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s_commands.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s_commands.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off_commands.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off_commands.json:1)

## 실행별 원자료

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/elbow_y_minus00125/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/elbow_y_minus00125/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/reference/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/reference/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/wrist_minus0025/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/wrist_minus0025/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/short/wrist_minus0050/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/elbow_y_minus00125/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/elbow_y_minus00125/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/reference/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/reference/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/wrist_minus0025/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/wrist_minus0025/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_05s/wrist_minus0050/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/elbow_y_minus00125/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/elbow_y_minus00125/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/reference/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/reference/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/wrist_minus0025/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/wrist_minus0025/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/hold_1s/wrist_minus0050/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/short/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/short/wrist_minus0050/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/hold_05s/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/hold_05s/wrist_minus0050/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/hold_1s/wrist_minus0050/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/off/hold_1s/wrist_minus0050/report.json:1)

각 run의 report/trace/states/contacts/controls/leg_torques JSON과 실행 로그를 보존한다.

## 이미지·설명과 검수

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:670](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:670) — 누적25절 이미지·설명
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/README.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/README.md:7) — 15회 최대 오차 표와 해석 범위
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/review.md:77](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/review.md:77) — 원자료 독립검수

[전체 생성 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/file_inventory.json:1), [검증 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/verification.json:1), [최종 source 보관본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/source_final_manifest.json:1)을 보존한다. PNG에는 줄 번호가 없다.
