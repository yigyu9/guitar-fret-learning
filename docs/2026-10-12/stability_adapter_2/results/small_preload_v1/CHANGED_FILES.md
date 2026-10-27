# small_preload_v1 변경·결과 인덱스

이 인덱스는 개선 wrist 자세의 작은 preload 비교 자료를 가리킨다. native 실행·제어 코드 변경은 이 산출물 작업에서 하지 않았다.

## 계획·입력·구현

- 비교 계획/결과: [SMALL_PRELOAD_COMPARE.md:31](/home/ajou/yigyu/3/stability_adapter_2/SMALL_PRELOAD_COMPARE.md:31)
- 감사기 계약 검사: [audit_strap_initial_inputs.py:45](/home/ajou/yigyu/3/stability_adapter_2/audit_strap_initial_inputs.py:45)
- 설정 0 N (기존 입력과 byte-exact 중복): [load_00n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/small_preload_v1/load_00n.json:1)
- 설정 1 N: [load_01n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/small_preload_v1/load_01n.json:1)
- 설정 2 N: [load_02n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/small_preload_v1/load_02n.json:1)
- 계획 §35: [PLAN.md:756](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:756)
- 프로젝트 안내: [README.md:89](/home/ajou/yigyu/3/stability_adapter_2/README.md:89)
- VISUAL_REPORT §27: [VISUAL_REPORT.md:690](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:690)
- 결과 수치 표: [README.md:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/README.md:13)
- 그림 참조: [README.md:25](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/README.md:25)
- 결과 판정/제한: [README.md:27](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/README.md:27)
- 최종 코드·원자료·문서·미디어 검수: [review.md:71](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/review.md:71)

기존 [compare_strap_initial_trials.py](/home/ajou/yigyu/3/stability_adapter_2/compare_strap_initial_trials.py), [pose_strap_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/pose_strap_inputs.py), [plot_saved_arm_trials.py](/home/ajou/yigyu/3/stability_adapter_2/plot_saved_arm_trials.py)는 재사용했고 수정하지 않았다.

## 원자료와 산출물

- Canonical 9-run 비교/결정: [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/comparison.json), [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/decision.json)
- 짧은 비교와 초기 감사: [comparison_short.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/comparison_short.json), [initial_audit.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/initial_audit.log), [initial_audit_command.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/initial_audit_command.json)
- 선정 기록: [native_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/native_selection.json), [late_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/late_selection.json), [off_selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/off_selection.json)
- 실행 명령·요약: `short/`, `hold_05s/`, `hold_1s/`의 commands/execution JSON과 해당 `load_00n`, `load_01n`, `load_02n` 로그가 결과 디렉터리에 있다.
- Raw run 9개: `short/`, `hold_05s/`, `hold_1s/` 아래 각 `load_00n`, `load_01n`, `load_02n/`에 report, trace, states, contacts, controls, leg_torques JSON이 있다.
- 그림: [small_preload_v1.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/small_preload_v1.png)
- 생성 provenance: [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/plot_manifest.json)
- 초기3건 검사: [strap_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/strap_inputs.json:1).
- 최종 보존·검증 파일: [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/source_final_manifest.json:1), [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/verification.json:1), [file_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/file_inventory.json:1). 전체 원자료 파일의 절대 경로·첫 줄은 inventory에 수록한다.
