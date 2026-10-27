# 변경 파일

| 파일 | 역할 |
|---|---|
| [make_palm_witness_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts.py:1) | 저장된 source/native 레코드만 읽고 비교 그림 및 SHA manifest 생성. native/physics/inference/training 호출 없음. |
| [palm_witness_diagnostics.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/palm_witness_diagnostics.png) | native 두 trace와 16개 source 배치의 이산 finite-patch upper-bound 그림. |
| [recovered_v1/palm_witness_diagnostics.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/recovered_v1/palm_witness_diagnostics.png) · [recovered_v1/producer_source.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/recovered_v1/producer_source.py:1) · [recovered_v1/artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/recovered_v1/artifact_manifest.json:1) | 이전 producer source SHA와 원본 PNG SHA가 일치하는 복구 v1. 원래 실행 manifest/log/metadata byte 복구는 검증되지 않았고, 링크된 manifest는 복구 재생성 실행에서 새로 작성됐다. |
| [make_palm_witness_artifacts_v1_recovered.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts_v1_recovered.py:1) | SHA 검증된 v1 producer source의 영구 복구본. |
| [artifact_revision_preservation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifact_revision_preservation.json:1) | 원본 source/PNG SHA 복구와 revised artifact 보존 이력 및 manifest 복구 범위. |
| [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/artifact_manifest.json:1) · [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/producer_execution.json:1) · [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/producer.log:1) | producer/input/output SHA-256, 실행 명령, exit code와 로그. |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/README.md:1) | 초기각 변경, source/native 결과, 실제 이미지/영상, 제한과 미채택 결론, 학습 방향 기록. |
| [PALM_WITNESS_INITIAL_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:1) | root가 작성한 초기 자세 판정과 후속 순서. |
| [PLAYING_RESIDUAL_EVALUATION.md](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:1) | 현재 기타 G의 fret/strike 목표와 초기 world G 유지 목표를 함께 평가할 residual 계획. |
| [collect_palm_witness_videos.py](/home/ajou/yigyu/3/stability_adapter_2/collect_palm_witness_videos.py:9) · [VIDEO_INDEX_v5.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v5.md:1) | root 생성의 공유 영상 수집기와 128개 영상 인덱스. |
| [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/review.md:1) · [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/ROOT_VERIFICATION_NOTES.md:1) · [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/final_verification.json:1) | review와 root notes는 작성됨. 통합 보존 감사 결과는 봉인 단계에서 별도 생성되는 JSON에 저장. |

첫 산출물 덮어쓰기 및 SHA 검증 복구 경위는 [README의 버전 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/README.md:63)에 기록했다.
