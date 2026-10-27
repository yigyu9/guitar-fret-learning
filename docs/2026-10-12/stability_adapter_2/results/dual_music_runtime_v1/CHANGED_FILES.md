# 변경 파일과 실제 줄 번호

모든 경로는 절대 경로이며 최신 실행은v5이다. 아래 코드는이번단위에서새로추가했고기존main4는append-only로갱신했다. 원래stability_adapter/와공용원본은수정하지않았다.

| 용도 | 파일·줄 | 변경내용 |
|---|---|---|
| 최신 실행 진입점 | [run_dual_music_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:26) | 준비2초→동결 Fret+Strike→첫 source done까지 native 영상 |
| 공동 물리 장면 | [dual_music_scene_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_scene_v1.py:23) | 기존81제어 owner 재사용, 음악horizon·읽기전용 substep hook |
| 초기 지지 목표 | [dual_music_scene_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_scene_v1.py:11) | median 관절 오차 기반 정적preload, 실제초기상태유지 |
| 공동 음악 판정 | [dual_music_clock_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:34) | 현재기타기준 sounding fret/방향/영역/순서/timing/dwell 진단 |
| 후보 관측 | [dual_music_observation_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_music_observation_v1.py:7) | 548+420+303+28=1299 실제 입력 합성 |
| Strike 평가 분리 | [dual_strike_evaluator_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_strike_evaluator_v1.py:10) | 원본 소스SHA/AST seam으로 추가 물리 진행 제외 |
| Strike 계약 검사 | [dual_strike_contract_guard_v1.py](/home/ajou/yigyu/3/stability_adapter_2/dual_strike_contract_guard_v1.py:5) | document/task/inputSHA 및 action/observation 순서 확인 |
| 음악 반례12개 | [test_dual_music_v2.py](/home/ajou/yigyu/3/stability_adapter_2/tests/test_dual_music_v2.py:1) | 오음/누락/중복/방향/영역/순서/유지·PREP 검사 |
| 입력 반례4개 | [test_dual_strike_contract_guard_v1.py](/home/ajou/yigyu/3/stability_adapter_2/tests/test_dual_strike_contract_guard_v1.py:1) | 실제checkpoint·변경입력/메타데이터·순서 검사 |
| 구현 소단계 계획 | [DUAL_MUSIC_IMPLEMENTATION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_IMPLEMENTATION_V1.md:1) | 실행소비 원본계획 보존, 완료는main추가기록 |
| 메인 계획 결과 | [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:845) | 초기 지지 개선과동시 연주실패/후속학습gate |
| 메인 README | [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1955) | 현재runtime와미완성 학습조건 |
| 결과 색인 | [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:629) | 실제영상·그림·로그 안내 |
| 누적 시각보고 | [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2403) | native5초 비교와첫 종료까지 동시연주영상 |
| 최종 실행 집계 | [execution_summary_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json:1) | native4회/4248물리step/학습0 |
| 보존 예외 기록 | [PROVENANCE_NOTE_V2.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md:1) | failed producer 재구성한계와버전별수정 이력 |

실행소비이력: [run_dual_music_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v1.py:1) · [run_dual_music_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v2.py:1) · [run_dual_music_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v3.py:1) · [run_dual_music_v4.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v4.py:1) · [test_dual_music_v1.py](/home/ajou/yigyu/3/stability_adapter_2/tests/test_dual_music_v1.py:1) · 기존버전을수정하지않고보존한다.

후처리/분석의새파일들은이디렉토리에저장한다. analyze_preload_v1.py 실패본과v2정정본, analyze_pair_v1.py, 두preload producer세트, pair producer성공v1/v2·실패재구성본, 그림/초기값/로그/영상은artifact_inventory.json에서전체색인을제공한다. 실패재구성본을실행시점SHA봉인본으로설명하지않는다.

[결과·그림·영상 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1) · [정지비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_analysis_v2.json:1) · [연주실패 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_analysis_v1.json:1) · [guard 재검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json:1).
