# 산출물 및 변경 파일

이 진단의 결과 문서와 분석 산출물은 저장 실행을 기술한다. 원본 시뮬레이션 입력은 수정하지 않았다.

| 파일 | 역할 |
|---|---|
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/README.md:1) | 결과 해석과 saved native 시각 자료 |
| [analysis/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/summary.json) | 집계, closure, 제어/정책 표본, 기타 변화량 |
| [native/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/report.json) | 계약 검사와 native 실행 설정 |
| [native/data/PD_phase_properties.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/PD_phase_properties.json) | phase별 native property 요청·readback 및 상태 보존 |
| [native/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/controls.json) | 300개 제어 표본 및 source history |
| [pre_recovery_comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/pre_recovery_comparison.json), [compare_before_recovery.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/compare_before_recovery.py) | 첫 baseline 복원 직전 82 controls 및 복원 시점까지 42 native trace의 prefix 대조; 6 input SHA 불변 |
| [native/data/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/trace.json) | sampled native 상태 trace |
| [native/data/initial_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/initial_audit.json), [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/initial_values.json) | 초기 상태 감사와 값 |
| [native/data/images/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/capture.json), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/videos.json) | 저장 프레임·인코딩 manifest |
| [native/data/images/whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/whole_body.mp4), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/native/data/images/hands.mp4) | Gym native 카메라 영상 |
| [analysis/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/inputs_before.json), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/analysis/inputs_after.json) | 분석 입력 closure 대조: 1,056개 입력 변경 없음 |
| [실행기록 코드](/home/ajou/yigyu/3/stability_adapter_2/run_strike_approach_only_damping.py:141) | phase별 damping 설정과 property 기록 구현 |

다음 timed-ENTRY 비교는 별도 계획인 [STRIKE_TIMED_ENTRY_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1)에서 다룬다. 이번 문서는 해당 후속 native 실행의 완료나 독립 최종 검수 완료를 의미하지 않는다.
