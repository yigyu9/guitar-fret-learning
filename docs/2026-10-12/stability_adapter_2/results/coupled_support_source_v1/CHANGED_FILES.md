# 변경 파일 — coupled support source v3

| 파일 | 변경 내용 |
|---|---|
| [Phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/README.md:1>) | 검증 범위, 16개 전체 배치 표, 이산 source distance 그림, 저장 pose 기준과 인체 source-only 제안 배치, 거리/교차 검사 구분, 이후 연주 residual 계획을 기록했다. |
| [Artifact producer](</home/ajou/yigyu/3/stability_adapter_2/make_coupled_support_artifacts.py:42>) | v3 입력/검사 결과와 raw dependency SHA를 확인하고 이산 palm patch-distance 그림 및 provenance manifest를 만든다. |
| [Palm patch 거리 그림](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/coupled_support_palm_gap_by_fraction.png>) | 0, 0.1, 0.5, 5초 네 snapshot의 baseline 4개와 proposal 12개 전부 표시. 분수별 표식, only-pass 별표, source-only 설명을 포함한다. |
| [Artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/artifact_manifest.json>) | Producer SHA, 입력 57개 전후 SHA, PNG output SHA, native/physics/inference/training count, 배치·통과 수를 기록한다. |
| [Artifact execution record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/artifact_execution.json>) · [execution log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/artifact_execution.log>) | 정확한 실행 command, exit code 0, 실제 elapsed, log/manifest/producer SHA를 기록한다. |

원본 v3 탐색 입력 및 helper 파일은 변경하지 않았다. v1/v2 실패 결과는 원래 경로에 보존돼 있고 이 산출물은 v3 결과만 읽는다. Root-owned 검증/메인 문서 변경은 [README의 provenance 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/README.md:83>)에서 별도 추적한다.

참조: [v3 model check source](</home/ajou/yigyu/3/stability_adapter_2/check_coupled_support_model.py:16>), [coupled snapshot model](</home/ajou/yigyu/3/stability_adapter_2/coupled_support_source.py:37>), [v3 saved-pose search source](</home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:22>), [playing residual evaluation plan](</home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:17>). 실제 물리 시각 참고는 이전 [LA −2 mm 손목 시험 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/body9_strap_minus2mm_v1__native__hands.mp4>) 하나만 인용한다.
