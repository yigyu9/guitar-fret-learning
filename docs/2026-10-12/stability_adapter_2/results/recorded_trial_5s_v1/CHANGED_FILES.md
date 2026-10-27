# 파일 인덱스 — recorded_trial_5s_v1

## 이번 contact sheet 산출물

- [저장 프레임 contact sheet producer](/home/ajou/yigyu/3/stability_adapter_2/make_recorded_trial_contact_sheet.py:20) — 사전 입력 SHA, capture/frame SHA·시각 대조, sheet 생성 및 종료 SHA 확인.
- [연구 결과와 그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/README.md:1).
- [contact sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts/recorded_trial_5s_contact_sheet.png), [입력·producer·출력 해시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts/contact_sheet_manifest.json), [실행 명령·해시 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/contact_sheet_execution.json), [실제 실행 출력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/contact_sheet_execution.log).
- verification 보완 전 producer와 contact sheet/manifest/실행 기록은 [이전 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/producer_before_verification_update/)와 [이전 산출물](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts_before_verification_update/)에 보존했다. 레이아웃 단계 기존 `producer_before_layout_fix/` 사본은 SHA가 manifest와 다르므로 post-fix 작업본으로 보존했다. [원 producer 정확 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/producer_before_layout_fix_exact/make_recorded_trial_contact_sheet.py)은 원 manifest의 기대 SHA `d7408a1c13be55133e4ec95333b2f6f48cbf2d662dc3cff9670d2918a8bff4f2`와 일치한다. [당시 sheet/manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts_before_layout_fix/)는 변경하지 않았다.

## 실제 native 기록과 초기 조건

- [검증 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/verification.json), [저장 자료 검증 보완 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/verification_refinement.json), [baseline 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/report.json), [초기 각도·자세·목표·PD·LA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/initial_values.json), [입력 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/recorded_trial_5s_v1/baseline.json).
- [native camera frame 시각과 해시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/capture.json), [전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/whole_body.mp4), [손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/hands.mp4), [native run log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline.log).
- [상태 JSONL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/states.jsonl), [trace JSONL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/trace.jsonl), [contacts JSONL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/contacts.jsonl), [controls JSONL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/controls.jsonl), [tasks JSONL](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/tasks.jsonl).
- [별도 stop 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/stop_execution.json)과 [`stop_check/` partial 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/stop_check/)는 baseline 1200-step run과 구분해 보존했다.

## 녹화 실행 코드와 계획

- [기록된 trial runner](/home/ajou/yigyu/3/stability_adapter_2/run_recorded_trial.py:18), [Gym camera recorder](/home/ajou/yigyu/3/stability_adapter_2/gym_trial_recording.py:11), [camera 초기화 코드](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:25), [5초 recording 계획](/home/ajou/yigyu/3/stability_adapter_2/FIVE_SECOND_RECORDING_PLAN.md:1), [작업 흐름 안내](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:110).
- [프로젝트 README 사용 안내](/home/ajou/yigyu/3/stability_adapter_2/README.md:651), [메인 체크리스트](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1251).

## 누적 문서 인덱스

- [stability_adapter_2 README 실행 안내](/home/ajou/yigyu/3/stability_adapter_2/README.md:651), [메인 계획 기록 단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1251), [날짜별 결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:411), [누적 시각 보고서 그림 93](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1252).
