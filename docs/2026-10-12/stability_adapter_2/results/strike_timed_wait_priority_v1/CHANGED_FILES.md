# 산출물 및 변경 파일

| 파일 | 역할 |
|---|---|
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/README.md:1) | 진단 관측, 한계, 저장 native 시각 자료 |
| [analysis/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/summary.json) | 집계와 native sampled metric |
| [native/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/report.json) | 21개 계약 검사 및 native 실행 metadata |
| [native/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/inputs_before.json), [native/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/inputs_after.json) | native 실행 입력 closure: 1,063개 입력 변경 없음 |
| [analysis/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/inputs_before.json), [analysis/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/analysis/inputs_after.json) | 분석기 입력 7개 파일의 SHA 대조: 변경 없음 |
| [native/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/controls.json), [native/data/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/trace.json) | 300 control samples 및 saved native state trace |
| [native/data/PD_phase_properties.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/PD_phase_properties.json) | phase별 damping request/readback 기록 |
| [native/data/initial_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/initial_audit.json), [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/initial_values.json) | native 초기 상태 감사와 값 |
| [native/data/images/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/capture.json), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/videos.json) | 저장 프레임/인코딩 manifest |
| [native/data/images/whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/whole_body.mp4), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/native/data/images/hands.mp4) | Gym native 전신 및 손 영상 |
| [실행기](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_wait_priority.py:123), [다음 단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1) | 닫힌 시간창의 R9 goal ownership 구현과 후속 rebase 검토 계획 |

다음 actual-angle rebase 단계는 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1)의 independent pre-review PASS 후 native 실행 중이다. 본 phase는 그 실행의 완료 증거나 설정 채택, 전체 연주 성공 판정이 아니다. 검수 근거는 [pre_review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/pre_review.md).

## 첫 closed-window command 전 비교 근거

| 파일 | 역할 |
|---|---|
| [this-phase pre_wait_comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/pre_wait_comparison.json), [this-phase compare_before_wait.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/compare_before_wait.py) | 2.5초 전 controls 150개, 2.5초까지 complete native trace 76개, 비교 대상 6 SHA. Selected control keys에 `info`를 포함한 150 controls exact equality 및 76 complete native trace exact equality; 6 SHA unchanged. 첫 hit·clearance/scheduled recovery가 prefix에 포함. 전체 1,200-step state equality 아님 |
