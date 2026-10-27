# 변경 파일과 실제 위치

기존 소스는 보존하고 새버전으로 구현했다. main4는 기존 prefix를 유지한 append다. 결과물의 실행 시점 SHA와 최종값은 별도감사에 기록한다.

| 파일 | 내용 |
|---|---|
| [deadline_graphics_v1.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_graphics_v1.py:6) | 학습−1/평가0 그래픽 장치 전달과 렌더 API 차단 |
| [deadline_native_v8.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v8.py:9) | 기존 native 제어를 유지한 그래픽 래퍼 연결 |
| [deadline_graphics_migration_v1.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_graphics_migration_v1.py:15) | 기존 물리·제어 ABI/소스 유지와 수치 불변 이행 |
| [run_deadline_training_v9.py](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v9.py:76) | 학습/영상 분리,5분 복구 저장,30분 공식 평가 |
| [test_deadline_graphics_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_graphics_v1.py:17) | CPU9검사·변경 거절 반례 |
| [run_graphics_reset_probe_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_graphics_reset_probe_v1.py:12) | 원본 실패 진단 보존; 실제 비교는D 진단v2 사용 |
| [GRAPHICS_ISOLATION_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/GRAPHICS_ISOLATION_PLAN_V1.md:1) | 구현 계획과 단계별 검증 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:928) | 기존 prefix 보존 후 검증 결과 추가 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2027) | 기존 prefix 보존 후 검증 결과 추가 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:697) | 기존 prefix 보존 후 검증 결과 추가 |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2477) | 기존 prefix 보존 후 검증 결과 추가 |
| [run_graphics_reset_probe_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/run_graphics_reset_probe_v2.py:12) | 학습 ABI/감사 입력 분리;60회 초기화·전체 물리 비교 |
| [verify_graphics_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verify_graphics_v1.py:18) | checkpoint 수치·제어·영상 실제 검증 |
| [launch_recorded_learning_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/launch_recorded_learning_v1.py:18) | 재개 supervisor와영상 자동 보관 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/README.md:1) | 결과 요약·현재 상태 |
| [PROVENANCE_NOTE_V1.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/PROVENANCE_NOTE_V1.md:1) | 실패·그림정정·동일바이트재기록공개 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/README.md:1) | 최신한글그림·영상설명 |
| [README_ABSOLUTE_V4.md](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V4.md:1) | 영상10개·이전보관색인 |
