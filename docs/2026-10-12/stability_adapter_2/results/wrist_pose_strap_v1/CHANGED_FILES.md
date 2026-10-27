# wrist_pose_strap_v1 변경·결과 인덱스

이 인덱스는 개선 wrist 자세의 고정 strap rest length 비교에 필요한 계획, 구현, 결과 및 provenance 경로를 묶는다. 설정·물리 코드나 기존 산출물은 여기서 수정하지 않았다.

## 변경된 계획·문서

- 비교 계획/판정: [WRIST_POSE_STRAP_COMPARE.md:29](/home/ajou/yigyu/3/stability_adapter_2/WRIST_POSE_STRAP_COMPARE.md:29)
- 비교기 검증 계약: [compare_strap_initial_trials.py:55](/home/ajou/yigyu/3/stability_adapter_2/compare_strap_initial_trials.py:55)
- raw 파일 및 source-hash 수집: [compare_strap_initial_trials.py:86](/home/ajou/yigyu/3/stability_adapter_2/compare_strap_initial_trials.py:86)
- 입력 설정 5개(각 파일 1행, legacy는 0N 중복): [legacy](/home/ajou/yigyu/3/stability_adapter_2/trials/wrist_pose_strap_v1/legacy.json:1), [0N](/home/ajou/yigyu/3/stability_adapter_2/trials/wrist_pose_strap_v1/load_00n.json:1), [5N](/home/ajou/yigyu/3/stability_adapter_2/trials/wrist_pose_strap_v1/load_05n.json:1), [10N](/home/ajou/yigyu/3/stability_adapter_2/trials/wrist_pose_strap_v1/load_10n.json:1), [20N](/home/ajou/yigyu/3/stability_adapter_2/trials/wrist_pose_strap_v1/load_20n.json:1).
- 프로젝트 계획: [PLAN.md:741](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:741)
- 프로젝트 README: [README.md:83](/home/ajou/yigyu/3/stability_adapter_2/README.md:83)
- 누적 시각 보고 26절: [VISUAL_REPORT.md:680](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:680)
- 결과 표: [결과 README:14](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/README.md:14)
- 결과 그림: [결과 README:29](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/README.md:29)
- 판정/해석: [결과 README:31](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/README.md:31)
- 최종 검수 기록: [review.md:69](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/review.md:69)

## 원자료와 그림

- 최종 12-run 비교와 요약 판정: [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/comparison.json), [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/decision.json)
- 짧은 비교본 및 초기 감사: [comparison_short.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/comparison_short.json), [initial_audit.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/initial_audit.log)
- 선택 기록: [native_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/native_selection.json), [late_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/late_selection.json), [off_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/off_selection.json)
- run별 명령·실행 요약: [short](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/short_commands.json), [0.5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/hold_05s_commands.json), [1초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/hold_1s_commands.json) commands/execution JSON 및 대응 로그가 같은 결과 디렉터리에 보존되어 있다.
- 12개 저장 run: `short/`, `hold_05s/`, `hold_1s/` 아래 각각 `load_00n`, `load_05n`, `load_10n`, `load_20n` 디렉터리에 report, trace, states, contacts, controls, leg_torques JSON이 있다.
- 이미지·provenance: [wrist_pose_strap_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/wrist_pose_strap_v1.png), [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/plot_manifest.json)

## 재사용 파일과 후속 provenance

- [pose_strap_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/pose_strap_inputs.py) 및 [plot_saved_arm_trials.py](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py)는 재사용했으며 변경하지 않았다.
- 초기5개 source 검사: [strap_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/strap_inputs.json:1).
- 검수 후 보존본: [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/source_final_manifest.json:1), [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/verification.json:1), [file_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/file_inventory.json:1). 전체 원자료 파일의 절대 경로와 첫 줄 번호는 inventory에 수록한다.
