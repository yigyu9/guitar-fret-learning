# 변경 파일 색인 — 준비 팔 목표 유지 + Fret 손가락 제어

## A 구현과 프로젝트 진행 기록

- [native runner](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:30): 초기 audit, 동일 2초 준비, PLAY phase의 native 제어 및 원본 terminal 저장. 실행·제어 경로는 68, 103, 114, 124, 137, 162행에 이어진다.
- [목표 소유권 합성](/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py:5): Fret 손가락 21축, 준비에서 인계한 왼팔 9축, bounded support 및 초기 유지 목표를 하나의 native 명령으로 구성한다.
- [보존 wrapper](/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_arm_hold_preserved_run.py:12): native import 전에 입력 closure를 보존하고 실행한다.
- [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_ARM_HOLD_PLAN.md:1): 범위·단계·검증 조건. 실행에 소비된 계획 원문은 보존했고 완료 기록은 메인 PLAN/README에 추가했다.
- [메인 진행 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:546), [프로젝트 README 진행 요약](/home/ajou/yigyu/3/stability_adapter_2/README.md:1842): 실행 사실, 판정, 다음 왼팔 보정 검토를 기록한다.
- root 분석 진입점 [analyze_fret_arm_hold.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_arm_hold.py:11): 새 실행 trace와 기존 native v3를 비교하고 저장 증거를 독립 확인한다.

## D 원자료·분석·검증

- [이번 결과 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1), [검수 전 실행 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/pre_review.md:1), [소스 보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/source_preservation.json:1).
- Native 원본: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/report.json:1), [terminal info](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/terminal_info.json:1), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/trace.json:1), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/controls.json:1), [handoff values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/handoff_values.json:1).
- 재계산·보존 확인: [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/summary.json:1), [analysis input SHA list](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/inputs.json:1), [recording audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/recording_audit.json:1), [source preservation](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/source_preservation.json:1). 분석 summary는 23개 검사를, recording audit는 31개 검사를 통과했다. Native 입력 1,148개는 실행 전후 동일하다.
- [원본 전체 영상 모음 index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_fret_arm_hold.md:1), [영상 복사·SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_COLLECTION_fret_arm_hold.json:1). 개별 복사본은 [전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/fret_fingers_arm_hold_v1__whole_body.mp4), [양손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/fret_fingers_arm_hold_v1__hands.mp4)이며 각 원본 native 영상과 SHA-256이 같다.
- 이전 native baseline과 그 소비 파일은 [fret_native_connection_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/README.md:1)에 보존했다. 이번 분석은 이전 2.766667초 source terminal을 공통 시각으로 비교한다.
