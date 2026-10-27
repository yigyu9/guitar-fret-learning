# 변경 파일 색인 — fret_current_guitar_support_v2

이 색인은 v2 구현 및 결과 자료의 위치를 안내한다. 실행 입력·출력과 native 영상은 지정된 phase 디렉터리에 보존되어 있다.

| 파일 | 역할 | 주요 코드 위치 |
|---|---|---|
| [FRET_CURRENT_GUITAR_SUPPORT_V2_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FRET_CURRENT_GUITAR_SUPPORT_V2_PLAN.md:1) | 실험 조건과 절차 | 결과 경로 20행 |
| [fret_current_guitar_support_v2.py](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2.py:7) | 기타 좌표계 손목 상대 위치 추종 및 bounded solve | 준비 마지막 제출 PD 목표 ±0.1 rad, 초기 자세 ±0.3 rad 및 native 범위 14–23행, 현재 기타 pose 기반 목표와 방향 26–47행, 0.3 rad/s 변화율 및 solve 48–59행 |
| [run_fret_current_guitar_support_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:31) | native 실행과 control ownership 검사 | 21손가락·왼팔9·기타 관절 owner 검사 52–62행, 조건 기록 64–72행 |
| [run_fret_current_guitar_support_v2.sh](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.sh:1) | native 실행 wrapper | preserved runner 위임 12행 |
| [fret_current_guitar_support_v2_preserved_run.py](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2_preserved_run.py:1) | 입력 보존 실행 wrapper | 보존 실행 진입점 |
| [analyze_fret_current_guitar_support_v2_verified.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_support_v2_verified.py:1) | 조건 비교, support error 산출, native side-by-side 그림 | support error 76–83행, timeline·native 이미지 84–110행 |
| [fret_arm_analysis_preserved.py](/home/ajou/yigyu/3/stability_adapter_2/fret_arm_analysis_preserved.py:1) | 직접·재사용 분석 입력 보존 wrapper | audit 및 verified 분석 실행 14–42행 |
| [fret_raw_recording.py](/home/ajou/yigyu/3/stability_adapter_2/fret_raw_recording.py:1) | COLOR 전용 native 영상 기록기 | native pixel recorder 연결 1–8행 |
| [live_fret_recording_v2.py](/home/ajou/yigyu/3/stability_adapter_2/live_fret_recording_v2.py:9) | 재사용 native camera pixel capture | RGBA 복사 및 상태불변 검사 14–31행 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/README.md:1) | 결과 해석 및 시각 자료 | 성공 조건과 한계 포함 |
| [analysis_verified/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/summary.json) · [interpretation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/interpretation.json) | 요약 통계 및 공통 구간 해석 | 손목·지지 오차·기타 이동·회전 |
| [ON/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/report.json) · [ON/data/terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/terminal_info.json) | native 검사, 종료 원자료 | 종료 상태·press/sustain 지표 |
| [tests_pre.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/tests_pre.json) · [analysis_verified_audit/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified_audit/inputs_after.json) | 사전 검사 및 분석 입력 보존 감사 | 7개 root 사전 검사, 2,229개 입력 변경 없음 |
| [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/CHANGED_FILES.md:1) | 이번 작업에서 추가한 전체 변경 파일 색인 | 17개 신규 소스와 4개 진행 문서의 절대경로·확인 행 번호 7–27행 |

독립 검수가 완료됐다: [review_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/review_final.md). 보존 감사와 실행 소비 소스 스냅샷·실행 후 진행 갱신본의 구분은 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/final_verification.json)에서, 전체 파일 목록과 SHA는 [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/artifact_inventory.json)에서 확인한다. 보존 최종 소스: [source_final/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/source_final).
