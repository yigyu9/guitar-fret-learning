# right_wrist_negative_extension_v1 변경·결과 인덱스

이 인덱스는 reference에서 추가 음수 wrist 초기각을 비교한 결과의 경로 모음이다. 이 산출물 작성에서 native 물리·제어 코드나 설정은 수정하지 않았다.

## 계획·설정·문서

- 계획 및 결과 판정: [RIGHT_WRIST_NEGATIVE_EXTENSION.md:32](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_WRIST_NEGATIVE_EXTENSION.md:32)
- 비교기: [compare_arm_initial_trials.py:55](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:55)
- 초기 audit 도구: [audit_arm_initial_inputs.py:1](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:1)
- 기준 설정: [reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_negative_extension_v1/reference.json:1)
- 추가 −0.0025 rad 설정: [wrist_extra_minus0025.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_negative_extension_v1/wrist_extra_minus0025.json:1)
- 추가 −0.005 rad 설정: [wrist_extra_minus0050.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_wrist_negative_extension_v1/wrist_extra_minus0050.json:1)
- PLAN §36: [PLAN.md:770](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:770)
- 프로젝트 안내: [README.md:96](/home/ajou/yigyu/3/stability_adapter_2/README.md:96)
- VISUAL_REPORT §28: [VISUAL_REPORT.md:700](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:700)
- 입력/source 표: [결과 README:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/README.md:5)
- 기타 오차 표: [결과 README:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/README.md:15)
- 그림 및 결과 판정: [결과 README:27](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/README.md:27), [결과 README:29](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/README.md:29)
- 최종 코드·원자료·문서·미디어 검수: [review.md:71](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/review.md:71)

기존 [audit_arm_initial_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py), [compare_arm_initial_trials.py](/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py), [plot_saved_arm_trials.py](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py)는 재사용했으며 이 산출물 작업에서 수정하지 않았다.

## 비교 원자료 및 출력

- Canonical 비교와 판정: [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/comparison.json), [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/decision.json)
- Reference raw는 [reference_links](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/reference_links)에 기존 `negative_pose_late_v1/wrist_minus0050` 저장 run으로 연결되어 원본을 그대로 사용한다.
- 초기 입력 검사와 선택 기록: [initial_audit.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/initial_audit.log), [native_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/native_selection.json), [late_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/late_selection.json), [off_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/off_selection.json)
- 저장 실행 자료: `short/`, `hold_05s/`, `hold_1s/` 아래 `reference/`, `wrist_extra_minus0025/`, `wrist_extra_minus0050/` 각 run의 report·trace·states·contacts·controls·leg_torques JSON, execution/commands 및 관련 로그가 있다. OFF run은 추가하지 않았다.
- 그림·provenance: [right_wrist_negative_extension_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/right_wrist_negative_extension_v1.png), [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/plot_manifest.json)
- 초기3건 원자료: [initial_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/initial_inputs.json:1), [audit 명령](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/initial_audit_command.json:1). 원본 참조 연결은 [link manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/reference_link_manifest.json:1)에 기록했다.
- 최종 보존·검증: [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/source_final_manifest.json:1), [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/verification.json:1), [file_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/file_inventory.json:1). 전체 원자료 파일의 절대 경로와 첫 줄은 inventory에 수록한다.
