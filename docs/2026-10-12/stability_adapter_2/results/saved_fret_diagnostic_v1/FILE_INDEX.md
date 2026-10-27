# 변경 파일 색인

이번 문서 작업에서 작성한 파일은 이 색인과 [결과 안내](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md:1>)다. 아래 코드는 이번 저장자료 후처리 및 별도 live 진단의 실제 source 위치이며 수정 대상이 아니다. 줄 번호는 현재 작업 트리 기준이다.

## 진단 source와 계획

- [live_fret_geometry.py](</home/ajou/yigyu/3/stability_adapter_2/live_fret_geometry.py:12>) — pose, 조건부 위치/회전 기하, 목표 할당, 실제 기타 contact 추출 함수.
- [live_fret_recording.py](</home/ajou/yigyu/3/stability_adapter_2/live_fret_recording.py:87>) — live 진단 capture/기록 helper (`LiveFretRecording`).
- [live_fret_recording_v2.py](</home/ajou/yigyu/3/stability_adapter_2/live_fret_recording_v2.py:9>) — v2 native image 배열 저장 recorder helper; 핵심 recorder 구현은 36행.
- [run_live_fret_diagnostic.py](</home/ajou/yigyu/3/stability_adapter_2/run_live_fret_diagnostic.py:5>) 및 [run_live_fret_diagnostic.sh](</home/ajou/yigyu/3/stability_adapter_2/run_live_fret_diagnostic.sh:1>) — v1 live runner와 실행 wrapper.
- [run_live_fret_diagnostic_v2.py](</home/ajou/yigyu/3/stability_adapter_2/run_live_fret_diagnostic_v2.py:5>) 및 [run_live_fret_diagnostic_v2.sh](</home/ajou/yigyu/3/stability_adapter_2/run_live_fret_diagnostic_v2.sh:1>) — native camera image 배열 저장을 쓰는 v2 runner/wrapper.
- [FRET_LIVE_DIAGNOSTIC_PLAN.md](</home/ajou/yigyu/3/stability_adapter_2/FRET_LIVE_DIAGNOSTIC_PLAN.md:1>), [FRET_LIVE_DIAGNOSTIC_V2_PLAN.md](</home/ajou/yigyu/3/stability_adapter_2/FRET_LIVE_DIAGNOSTIC_V2_PLAN.md:1>), [SAVED_FRET_DIAGNOSTIC_PLAN.md](</home/ajou/yigyu/3/stability_adapter_2/SAVED_FRET_DIAGNOSTIC_PLAN.md:1>) — live v1/v2 및 저장자료 후처리 계획.
- [test_live_fret_geometry.py](</home/ajou/yigyu/3/stability_adapter_2/test_live_fret_geometry.py:12>) — geometry/목표 할당/contact 분리 단위 검사의 `GeometryTests`.
- [analyze_live_fret_diagnostic.py](</home/ajou/yigyu/3/stability_adapter_2/analyze_live_fret_diagnostic.py:19>) — live 진단 원자료 분석 진입점.
- [build_saved_fret_diagnostic.py](</home/ajou/yigyu/3/stability_adapter_2/build_saved_fret_diagnostic.py:77>) — 저장 native 기록으로 산출물을 만드는 후처리 진입점. 실행에 사용된 동일 SHA의 source 사본은 [source_pre_revision](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/source_pre_revision/build_saved_fret_diagnostic.py:77>)에 보존돼 있다.

## 결과와 상위 기록

- [이 결과 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md:1>), [summary.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/summary.json>), [capture.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/capture.json>), [metrics.csv](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/metrics.csv>), [interpretation.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/interpretation.json>).
- [메인 계획 기록](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:667>), [결과 인덱스](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:573>), [VISUAL_REPORT 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2313>).
- 독립 검수 결과는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/review.md>)에 기록됐다. 최종 보존 검증 산출물 `final_verification.json`, `source_final/`, `artifact_inventory.json`은 별도 담당의 예정 경로다.
