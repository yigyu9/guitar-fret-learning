# right_wrist_local_v1 변경·결과 인덱스

오른손 손목 기준각 주변 ±0.00125 rad의 source 통과 설정 및 저장 ON trace 비교를 가리킨다. 이 산출물 작업에서는 native 실행이나 설정·제어 코드 수정을 하지 않았다.

## 계획·설정·결과 문서

- 비교 계획 및 해석: [RIGHT_WRIST_LOCAL_COMPARE.md:28](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_WRIST_LOCAL_COMPARE.md:28)
- 초기 기준 설정: [reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_local_v1/reference.json:1)
- 손목 −0.00125 rad: [wrist_minus00125.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_local_v1/wrist_minus00125.json:1)
- 손목 +0.00125 rad: [wrist_plus00125.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_local_v1/wrist_plus00125.json:1)
- PLAN §37: [PLAN.md:784](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:784)
- 프로젝트 README: [README.md:102](/home/ajou/yigyu/3/stability_adapter_2/README.md:102)
- 누적 VISUAL_REPORT §29: [VISUAL_REPORT.md:710](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:710)
- 초기각·source proxy 표: [결과 README:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md:5)
- 최대 오차 표: [결과 README:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md:15)
- 그림 및 판정: [결과 README:25](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md:25), [결과 README:27](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md:27)
- 재현 CLI와 새 출력 경로 안내: [결과 README:33](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md:33)
- 최종 원자료·문서·미디어 검수: [review.md:70](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/review.md:70)

세 기존 helper [audit_arm_initial_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py), [compare_arm_initial_trials.py](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py), [plot_saved_arm_trials.py](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py)는 read-only 용도로 재사용했고 변경하지 않았다.

## 원자료 및 출력 경로

- Canonical 9-run 비교와 판정: [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/comparison.json), [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/decision.json)
- 짧은 비교·초기 감사·참조 원본 link manifest: [comparison_short.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/comparison_short.json), [initial_audit.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/initial_audit.log), [reference_link_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/reference_link_manifest.json)
- 선택 기록: [native_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/native_selection.json), [late_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/late_selection.json), [off_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/off_selection.json)
- 기준 raw는 `reference_links/short`, `reference_links/hold_05s`, `reference_links/hold_1s` 아래 ON reference로 연결되어 원본을 변경하지 않는다.
- 세 실행 구간 raw는 `short/`, `hold_05s/`, `hold_1s/` 아래 `reference/`, `wrist_minus00125/`, `wrist_plus00125/`에 있으며, 각 report·trace·states·contacts·controls·leg_torques JSON과 commands/execution·로그가 결과 디렉터리에 있다. OFF run은 없다.
- 그림과 생성 provenance: [right_wrist_local_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/right_wrist_local_v1.png), [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/plot_manifest.json)
- 초기3건 검사 원자료·명령: [initial_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/initial_inputs.json:1), [initial_audit_command.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/initial_audit_command.json:1).
- 최종 보존·검증: [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/source_final_manifest.json:1), [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/verification.json:1), [file_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/file_inventory.json:1). 전체 원자료 파일의 절대 경로와 첫 줄은 inventory에 수록한다.
