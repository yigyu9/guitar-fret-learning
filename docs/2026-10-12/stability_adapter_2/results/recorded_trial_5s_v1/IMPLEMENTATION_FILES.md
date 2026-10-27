# 초기 값·5초 녹화의 구현 파일

초기 자세를 바꾸려면 trial의 `initial_settings.joint_angles_rad`를 수정한다.
`main_target_offsets_rad`는 초기각 대비 환경 시작 후 PD 목표 보정이며 초기 자세 자체와 다르다.
실제 초기각은 `baseline/initial_values.json`의 named 81관절 지도와 native t0 state를 확인한다.

| 파일 | 역할 |
| --- | --- |
| [실행 runner](/home/ajou/yigyu/3/stability_adapter_2/run_recorded_trial.py:18) | 실제 초기값 저장, 연속5초/1200step, 목표·물리 로그와 중단 보존 |
| [카메라·MP4 helper](/home/ajou/yigyu/3/stability_adapter_2/gym_trial_recording.py:11) | 전신·손30fps/151frame, 렌더 상태 보존, 실제PNG와 영상 저장 |
| [저장 기록 검증](/home/ajou/yigyu/3/stability_adapter_2/verify_recorded_trial.py:16) | 1200step 시간/명령, 영상SHA·길이·처음24step exact·중단 검사 |
| [실제frame 조합](/home/ajou/yigyu/3/stability_adapter_2/make_recorded_trial_contact_sheet.py:73) | 같은 실행의0/2.5/5초 nativePNG를2×3으로 조합 |
| [입력 trial](/home/ajou/yigyu/3/stability_adapter_2/trials/recorded_trial_5s_v1/baseline.json:1) | 절대 초기각/LA/기타 생성 이동과 named 목표offset·왼팔PD배율 |
| [초기 값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/initial_values.json:1) | 실제81q·기타worldp/xyzwq·속도·초기PD·LA·원자료 |
| [녹화 계획](/home/ajou/yigyu/3/stability_adapter_2/FIVE_SECOND_RECORDING_PLAN.md:1) | 사용자 요구와 검증 소단계 |
| [기본 작업 흐름](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:107) | 앞으로 실험별초기값/5초영상, producer 보존즉시SHA검사 |
| [실행 안내](/home/ajou/yigyu/3/stability_adapter_2/README.md:648) | 새 기본 진입점과 산출물 |
| [메인 체크리스트](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1251) | 구현·물리실행·영상·검수 진행 |
| [다음 stiffness 비교](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1) | 사용자 요구에 맞춰3조건각5초/총3600step으로 계획 변경;미실행 |
| [누적 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:403) | 녹화 완료·중단 검증 요약 |
| [그림93·실제영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1246) | 실제Gym frame/MP4와 해석 범위 |
