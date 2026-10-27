# 산출물 및 변경 파일

이 phase 문서는 완료된 retry 저장 실행을 중심으로 기술한다. 최초 중단 시도의 프레임은 보존 자료이며 성공 결과에 사용하지 않았다.

| 파일 | 역할 |
|---|---|
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/README.md:1) | timed-ENTRY 진단 결과, 한계, 실제 retry 영상 |
| [analysis_retry_v1/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/summary.json) | retry 집계, phase 표본, closure count 및 변화량 |
| [native_retry_v1/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/report.json) | native retry 검사, 1,200 step·151 frame 완료 상태 |
| [native_retry_v1/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/inputs_before.json), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/inputs_after.json) | native 실행 closure: 1,059개 입력 변경 없음 |
| [analysis_retry_v1/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/inputs_before.json), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/inputs_after.json) | 분석기 입력 7개 파일의 SHA 대조: 변경 없음 |
| [native_retry_v1/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/controls.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/trace.json) | retry control 및 sampled native-state 기록 |
| [native_retry_v1/data/PD_phase_properties.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/PD_phase_properties.json) | phase별 damping 요청 및 native readback |
| [interrupted_run.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/interrupted_run.json) | 최초 run 중단 상태: exit 143, 94 frames, 최종 report 미생성 |
| [native/data/images/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native/data/images/capture.json) | 중단 run의 94-frame partial 저장 목록; 결과 영상 근거 아님 |
| [native_retry_v1/data/images/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/capture.json), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/videos.json) | 완료 retry frames와 영상 manifest |
| [native_retry_v1/data/images/whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/whole_body.mp4), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/hands.mp4) | 완료 retry의 Gym native 카메라 영상 |
| [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1), [실행 코드](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_entry.py:155) | source-open 전 READY geometry 3 대기 규칙 및 실행 구현 |

다음 우선순위 검토는 별도 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1)에 남겨져 있다. 이 phase 문서는 후속 실행이나 독립 최종 검수 완료를 뜻하지 않는다.

## 저장 native trajectory의 authority 분석

| 파일 | 역할 |
|---|---|
| [authority_analysis_v2/goal_authority.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/goal_authority.png) | READY reference, native-measured actual pick, R9 FK predicted goal 비교 그림 |
| [authority_analysis_v2/rows.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/rows.json), [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/summary.json) | saved native sample 8개의 원자료와 요약 |
| [authority_analysis_v2/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/inputs_before.json), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/inputs_after.json) | 분석 입력 6개 SHA가 불변임을 기록 |
| [goal_authority_diagnosis_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/goal_authority_diagnosis_v2.py) | 저장 native sample을 읽어 FK goal 예측 및 그림 생성 |
| [authority_analysis/failed_run.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis/failed_run.json) | 이전 v1 import 실패 기록; 성공 분석 산출물이 아님 |
