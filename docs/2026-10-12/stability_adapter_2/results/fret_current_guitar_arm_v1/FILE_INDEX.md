# 변경 파일 색인 — fret_current_guitar_arm_v1

이 색인은 실험 구현과 결과 열람에 필요한 파일을 찾기 위한 안내다. A 소스와 leaf 계획은 실행 전 스냅샷에 포함되며, 이 결과 문서 작성 중 수정하지 않았다.

| 파일 | 역할 | 주요 위치 |
|---|---|---|
| [FRET_CURRENT_GUITAR_ARM_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FRET_CURRENT_GUITAR_ARM_PLAN.md:1) | 비교 조건과 사전 정의된 절차 | 조건 5–12행, 검증 순서 14–21행 |
| [fret_current_guitar_arm.py](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_arm.py:7) | 왼팔 9관절 bounded target solve | 초기 관절값 ±0.3 rad 목표 허용 범위 14–15행, 목표 변화율 0.8 rad/s 제한 44–48행 |
| [run_fret_current_guitar_arm.py](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.py:1) | native 환경에서 조건 실행 및 기록 | 실행 진입점 |
| [run_fret_current_guitar_arm.sh](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.sh:1) | 실행 wrapper | 런처 인자 전달 |
| [fret_current_guitar_arm_preserved_run.py](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_arm_preserved_run.py:1) | 보존된 실행 조건과 연결 | 재현용 wrapper |
| [analyze_fret_current_guitar_arm.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_arm.py:1) | OFF/ON 결과 및 공통 시점 분석 | 요약·그림 생성 진입점 |
| [analyze_fret_current_guitar_arm_verified.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_arm_verified.py:1) | 입력 해시를 포함한 검증 분석과 side-by-side 그림 생성 | native 프레임 비교·입력 지문 기록 82–98행 |
| [fret_arm_analysis_preserved.py](/home/ajou/yigyu/3/stability_adapter_2/fret_arm_analysis_preserved.py:1) | 재분석 입력 보존 wrapper | snapshot 실행 및 전후 동일성 감사 14–42행 |
| [fret_raw_recording.py](/home/ajou/yigyu/3/stability_adapter_2/fret_raw_recording.py:1) | COLOR 전용 native raw camera 녹화기 | 기록기 연결 1–8행 |
| [live_fret_recording_v2.py](/home/ajou/yigyu/3/stability_adapter_2/live_fret_recording_v2.py:9) | 재사용 native pixel capture helper | RGBA 복사·상태 동일성 검사·PNG 기록 14–31행 |
| [test_fret_current_guitar_arm.py](/home/ajou/yigyu/3/stability_adapter_2/test_fret_current_guitar_arm.py:1) | 사전 범위·속도·FK 검사 | 점검 진입점 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/README.md:1) | 비교 결과, 녹화와 native 그림 설명 | 결론 및 해석 주의 |
| [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/summary.json) | 검증 재분석의 구간 길이, 공통 손목 오차, 종료 및 변위 요약 | 결과 문서에서 인용한 요약 |
| [matched_goals.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/matched_goals.json) | 동일 goal/time의 세부 손목 및 표식 거리 | 매칭 표본 원자료 |
| [interpretation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/interpretation.json) | 공통 구간 이동·회전과 표식 거리 요약 | 해석 한계 포함 |
| [analysis_verified_audit/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified_audit/inputs_after.json) | 검증 재분석 전후 입력 보존 검사 | 1,899개 입력, 변경 0 |
| [tests_pre.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/tests_pre.json) | 실행 전 기구학·속도·범위 검사 | 11개 사전 검사 |
| [OFF/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/report.json) · [ON/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/report.json) | 각 native 실행 조건, 기록, 검사 | 보고서 checks |
| [OFF/data/terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/terminal_info.json) · [ON/data/terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/terminal_info.json) | source의 종료 지표 | 실패·성공 및 프레스 성공률 지표 |
| [analysis_verified/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified) | 입력 보존 감사 후 만든 동일 시점 native 그림 및 최종 사용 분석 | `whole_body_*`, `hands_*`, `timeline.png` |
| [analysis/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis) | 최초 분석 보존본 | 보조 입력 해시 범위가 미흡해 결과 문서 인용에는 사용하지 않음 |
| [OFF/ 및 ON/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1) | 전체 실행 입력·원자료·녹화·보존 스냅샷 | 조건별 `data/`, `source_before/`, 로그 |

독립 검수가 완료됐다: [review_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/review_final.md). 보존 감사와 실행 소비 소스 스냅샷·실행 후 진행 갱신본의 구분은 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/final_verification.json)에서, 전체 파일 목록과 SHA는 [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/artifact_inventory.json)에서 확인한다. 보존 최종 소스: [source_final/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/source_final).
