# 산출물 및 변경 파일

| 파일 | 역할 |
|---|---|
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/README.md:1) | actual-angle rebase 결과 해석, 한계, native 영상 |
| [analysis/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/summary.json) | 집계, phase samples, closure 및 위치/회전 변화 |
| [native/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/report.json) | 21개 검사와 1,200-step/151-frame 실행 결과 |
| [native/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/inputs_before.json), [native/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/inputs_after.json) | native input closure 1,066개 변경 없음 |
| [analysis/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/inputs_before.json), [analysis/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/analysis/inputs_after.json) | 별도 분석기 입력 7개 파일 SHA 변경 없음 |
| [native/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/controls.json), [native/data/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/trace.json) | saved control 및 native-state samples |
| [native/data/PD_phase_properties.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/PD_phase_properties.json) | phase별 damping native readback |
| [native/data/initial_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/initial_audit.json), [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/initial_values.json) | 시작 상태 검증과 initial values |
| [native/data/images/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/capture.json), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/videos.json) | native frame/video manifests |
| [native/data/images/whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/whole_body.mp4), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/data/images/hands.mp4) | 이번 실행의 Gym native camera videos |
| [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1), [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_wait_rebase.py:182) | 대기 구간 actual-angle rebase 계획과 구현 |

이 phase의 before/after prefix comparison은 완료됐다. 독립 final review 문서 작성은 대기 중이다. 이 문서는 full-song success나 후속 완료를 인증하지 않는다.

## 첫 closed-window command 전 prefix 비교

| 파일 | 역할 |
|---|---|
| [pre_wait_comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/pre_wait_comparison.json), [compare_before_wait.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/compare_before_wait.py) | timed-wait-priority 대비 2.5초 전 controls 150개 및 2.5초까지 complete native trace 76개 exact. Compared control keys include `info`; 비교 입력 6 SHA unchanged. Prefix 범위이며 전체 1,200-step equality 아님 |
